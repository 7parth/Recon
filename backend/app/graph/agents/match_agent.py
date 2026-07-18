"""
match_agent.py — Scores how well the candidate fits the job.

Node signature: match_agent_node(state) -> dict

This is the fan-in point: it runs AFTER resume_agent, job_agent, and
company_agent all complete.  By the time LangGraph calls this node,
state["resume_profile"] and state["job_profile"] are both populated.

Two-stage scoring strategy:
  Stage 1 — Embedding similarity (fast, free):
    Concatenate the candidate's skills+summary and the job's skills+responsibilities
    into two text blobs, embed both, compute cosine similarity.
    This gives a cheap "ballpark" score.

  Stage 2 — LLM detailed scoring (slower, costs tokens):
    Only run this if the embedding score is above a minimum viability floor
    (we use MATCH_SCORE_THRESHOLD / 2 as the early-exit threshold).
    The LLM produces a rich MatchResult with strengths, weaknesses, gap_areas,
    and a calibrated overall_score.

Why two stages?
  Embeddings can't distinguish "5 years Python" from "5 years Java" — they just
  see similar-ish technical text.  The LLM understands semantics.  But calling
  the LLM for every job pair (including obvious mismatches like a designer role
  for a backend engineer) wastes money.  Embeddings filter the obvious ones out.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, MatchResult
from app.graph.tools.llm import llm
from app.graph.tools.embeddings import score_resume_jd
from app.graph.constants import MATCH_SCORE_THRESHOLD
from app.graph.prompts.match import MATCH_SYSTEM_PROMPT, MATCH_USER_PROMPT

logger = logging.getLogger(__name__)

# Early-exit floor: if embedding score is below this, skip the LLM entirely.
# Set at half the main threshold — gives the LLM a chance on borderline cases
# while skipping obvious mismatches immediately.
_EMBEDDING_FLOOR = MATCH_SCORE_THRESHOLD / 2   # 0.325 with default threshold 0.65


def match_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node (fan-in): score resume vs job → MatchResult.

    Reads:  state["resume_profile"], state["job_profile"]
    Writes: state["match_result"]
    """
    resume_profile = state.get("resume_profile")
    job_profile = state.get("job_profile")

    # Guard: both profiles must exist (set by the parallel agents upstream)
    if resume_profile is None:
        return {"error": "match_agent: resume_profile is missing from state"}
    if job_profile is None:
        return {"error": "match_agent: job_profile is missing from state"}

    # ── Stage 1: Embedding pre-filter ─────────────────────────────────────────
    # Build two plain-text blobs from the structured profiles.
    # We join skills with ", " — the embedding model works on natural-language
    # sentences better than bare comma lists, but commas are fine here.
    candidate_text = (
        f"{resume_profile.summary}\n"
        f"Skills: {', '.join(resume_profile.skills)}\n"
        f"Experience: {resume_profile.experience_years} years"
    )
    job_text = (
        f"{job_profile.responsibilities}\n"
        f"Required skills: {', '.join(job_profile.required_skills)}\n"
        f"Experience required: {job_profile.experience_required} years"
    )

    embedding_score = score_resume_jd(candidate_text, job_text)
    logger.info("match_agent: embedding score = %.4f (floor = %.4f)", embedding_score, _EMBEDDING_FLOOR)

    # Early exit: obvious mismatch — no point calling the LLM
    if embedding_score < _EMBEDDING_FLOOR:
        logger.info("match_agent: score below floor, skipping LLM — returning minimal MatchResult")
        return {
            "match_result": MatchResult(
                overall_score=embedding_score,
                strengths=[],
                weaknesses=["Candidate profile does not significantly overlap with job requirements."],
                gap_areas=list(job_profile.required_skills),   # all required skills are gaps
            )
        }

    # ── Stage 2: LLM detailed scoring ─────────────────────────────────────────
    # We serialise the structured profiles back into readable strings for the
    # prompt.  LLMs extract meaning from natural text; passing raw Pydantic JSON
    # also works but readable labels (Skills:, Experience:) help the model attend
    # to the right fields.
    messages = [
        SystemMessage(content=MATCH_SYSTEM_PROMPT),
        HumanMessage(content=MATCH_USER_PROMPT.format(
            skills=", ".join(resume_profile.skills),
            experience_years=resume_profile.experience_years,
            summary=resume_profile.summary,
            required_skills=", ".join(job_profile.required_skills),
            responsibilities=job_profile.responsibilities,
            experience_required=job_profile.experience_required,
        )),
    ]

    structured_llm = llm.with_structured_output(MatchResult)

    logger.info("match_agent: invoking LLM for detailed match scoring")

    try:
        result: MatchResult = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("match_agent: LLM call failed: %s", e)
        return {"error": f"match_agent LLM failed: {e}"}

    # ── Blend scores ──────────────────────────────────────────────────────────
    # The LLM's score is more nuanced; the embedding score is more objective.
    # We blend them 70/30 in favour of the LLM — it understands semantics,
    # but the embedding anchors it to measurable overlap.
    blended_score = round(0.7 * result.overall_score + 0.3 * embedding_score, 4)
    result.overall_score = blended_score

    logger.info(
        "match_agent: final score=%.4f | strengths=%d | weaknesses=%d | gaps=%d",
        result.overall_score,
        len(result.strengths),
        len(result.weaknesses),
        len(result.gap_areas),
    )

    return {"match_result": result}

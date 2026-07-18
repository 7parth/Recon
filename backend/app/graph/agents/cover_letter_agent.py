"""
cover_letter_agent.py — Generates a personalised cover letter.

Node signature: cover_letter_agent_node(state) -> dict

Position in graph:
  tailoring_agent → cover_letter_agent → human_review

Like tailoring_agent, this node handles both first-run and re-tailor cases.

New concept — temperature for creative writing:
  All previous agents used temperature=0.2 (set in llm.py) to favour
  deterministic, factual extraction.  Cover letters are creative writing —
  they benefit from more varied, natural language.
  We create a second LLM instance with temperature=0.7 here using
  llm.bind(temperature=0.7).  This overrides the default without changing
  the shared llm singleton — no side effects on other agents.

  Rule of thumb:
    temperature 0.0–0.3 → factual extraction, structured output
    temperature 0.5–0.8 → creative writing, natural prose
    temperature 0.9–1.0 → brainstorming, highest variety (rarely needed)

Reads:  resume_profile, company_profile, job_profile, match_result,
        rejection_feedback (optional), cover_letter (previous, optional)
Writes: cover_letter (CoverLetter)
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, CoverLetter
from app.graph.tools.llm import llm
from app.graph.prompts.cover_letter import (
    COVER_LETTER_SYSTEM_PROMPT,
    COVER_LETTER_USER_PROMPT,
    COVER_LETTER_RETAILOR_SYSTEM_PROMPT,
    COVER_LETTER_RETAILOR_USER_PROMPT,
)

logger = logging.getLogger(__name__)

# Higher temperature for creative prose — overrides the shared llm default (0.2)
# .bind() returns a new runnable with the overridden config; the original llm
# object is unchanged and still used by all other agents at temperature=0.2.
_creative_llm = llm.bind(temperature=0.7)


def cover_letter_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: generate or revise a personalised cover letter.

    Reads:  state["resume_profile"], state["company_profile"],
            state["job_profile"], state["match_result"],
            state["rejection_feedback"] (may be None),
            state["cover_letter"] (may be None on first run)
    Writes: state["cover_letter"]
    """
    resume_profile  = state.get("resume_profile")
    company_profile = state.get("company_profile")
    job_profile     = state.get("job_profile")
    match_result    = state.get("match_result")
    rejection_feedback  = state.get("rejection_feedback")
    previous_letter = state.get("cover_letter")

    # ── Guards ────────────────────────────────────────────────────────────────
    if resume_profile is None:
        return {"error": "cover_letter_agent: resume_profile missing"}
    if job_profile is None:
        return {"error": "cover_letter_agent: job_profile missing"}

    is_retailor = bool(rejection_feedback and rejection_feedback.strip())

    # ── Branch: re-tailor vs first-run ────────────────────────────────────────
    if is_retailor:
        logger.info("cover_letter_agent: RE-TAILOR mode")

        previous_content = previous_letter.content if previous_letter else ""

        messages = [
            SystemMessage(content=COVER_LETTER_RETAILOR_SYSTEM_PROMPT),
            HumanMessage(content=COVER_LETTER_RETAILOR_USER_PROMPT.format(
                previous_letter=previous_content,
                rejection_feedback=rejection_feedback,
                company_name=company_profile.name if company_profile else "the company",
                required_skills=", ".join(job_profile.required_skills),
            )),
        ]
    else:
        logger.info("cover_letter_agent: FIRST-RUN mode")

        # Safely extract optional profile fields with sensible fallbacks.
        # company_profile may be None if the company agent failed on a sparse JD.
        company_name  = company_profile.name          if company_profile else "the company"
        industry      = company_profile.industry      if company_profile else "N/A"
        size          = company_profile.size          if company_profile else "N/A"
        culture_notes = company_profile.culture_notes if company_profile else "N/A"
        strengths     = ", ".join(match_result.strengths) if match_result else "N/A"

        messages = [
            SystemMessage(content=COVER_LETTER_SYSTEM_PROMPT),
            HumanMessage(content=COVER_LETTER_USER_PROMPT.format(
                summary=resume_profile.summary,
                experience_years=resume_profile.experience_years,
                skills=", ".join(resume_profile.skills),
                company_name=company_name,
                industry=industry,
                size=size,
                culture_notes=culture_notes,
                responsibilities=job_profile.responsibilities,
                required_skills=", ".join(job_profile.required_skills),
                strengths=strengths,
            )),
        ]

    # ── LLM call — use creative temperature ──────────────────────────────────
    # with_structured_output is called on _creative_llm, not the shared llm,
    # so only this agent gets temperature=0.7.
    structured_llm = _creative_llm.with_structured_output(CoverLetter)

    logger.info("cover_letter_agent: invoking LLM (temperature=0.7)")

    try:
        result: CoverLetter = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("cover_letter_agent: LLM call failed: %s", e)
        return {"error": f"cover_letter_agent LLM failed: {e}"}

    logger.info(
        "cover_letter_agent: cover letter generated (%d chars)", len(result.content)
    )

    return {"cover_letter": result}

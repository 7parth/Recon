"""
ats_agent.py — Audits the resume against the job's ATS keywords.

Node signature: ats_agent_node(state) -> dict

Position in graph:
  match_agent → (threshold gate) → ats_agent → tailoring_agent

This node runs only when the match score clears MATCH_SCORE_THRESHOLD,
meaning the router confirmed the job is worth pursuing.

Reads:  state["resume_raw"]       — the original resume text (not yet tailored)
        state["job_profile"]      — contains required_skills list
Writes: state["ats_report"]       — ATSReport with keyword_match, section_score, recommendations

Key teaching point — why audit the *original* resume here, not the tailored one?
  The tailoring_agent hasn't run yet.  This agent's job is to tell the
  tailoring_agent WHAT to fix — it's the "before" snapshot.
  The tailoring_agent then uses ats_report.recommendations as a concrete
  checklist of keywords to weave into the tailored resume.
  This creates a feedback loop:  ATS audit → tailoring → (implicit re-score).
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, ATSReport
from app.graph.tools.llm import llm
from app.graph.prompts.ats import ATS_SYSTEM_PROMPT, ATS_USER_PROMPT

logger = logging.getLogger(__name__)


def ats_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: audit resume keyword coverage → ATSReport.

    Reads:  state["resume_raw"], state["job_profile"]
    Writes: state["ats_report"]
    """
    resume_raw = state.get("resume_raw", "").strip()
    job_profile = state.get("job_profile")

    if not resume_raw:
        return {"error": "ats_agent: resume_raw is empty"}
    if job_profile is None:
        return {"error": "ats_agent: job_profile is missing from state"}

    # Format required skills as a bulleted list — more readable in the prompt
    # than a bare comma-separated string, which the LLM may truncate or misread.
    skills_list = "\n".join(f"- {skill}" for skill in job_profile.required_skills)

    messages = [
        SystemMessage(content=ATS_SYSTEM_PROMPT),
        HumanMessage(content=ATS_USER_PROMPT.format(
            resume_text=resume_raw,
            required_skills=skills_list,
        )),
    ]

    # ── Structured output with a nested dict field ────────────────────────────
    # ATSReport.section_score is typed as dict[str, int].
    # with_structured_output handles nested types natively — Pydantic validates
    # that the LLM returns an object where section_score maps strings to ints.
    # If the LLM returns floats (e.g. 7.5), Pydantic coerces them to int (7).
    structured_llm = llm.with_structured_output(ATSReport)

    logger.info(
        "ats_agent: auditing %d chars of resume against %d required skills",
        len(resume_raw),
        len(job_profile.required_skills),
    )

    try:
        report: ATSReport = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("ats_agent: LLM call failed: %s", e)
        return {"error": f"ats_agent LLM failed: {e}"}

    # Clamp keyword_match to [0.0, 1.0] — LLMs occasionally return values like 1.2
    report.keyword_match = max(0.0, min(1.0, report.keyword_match))

    logger.info(
        "ats_agent: keyword_match=%.2f | sections=%s",
        report.keyword_match,
        report.section_score,
    )

    return {"ats_report": report}

"""
job_agent.py — Fetches a job listing and extracts a structured JobProfile.

Node signature: job_agent_node(state) -> dict

Flow:
  1. Read state["job_url"]
  2. Detect if it's a URL or raw JD text (some users paste JDs directly)
  3. Fetch/clean the text using jd_parser
  4. LLM → JobProfile via with_structured_output
  5. Return {"job_profile": <JobProfile>}

Note on parallel execution:
  This node runs in parallel with resume_agent and company_agent (all three
  are fan-out targets from planner).  LangGraph runs them concurrently when
  the graph is executed with an async runner — they share no mutable state
  during their execution, so there are no race conditions.
  Each returns a dict, and LangGraph merges all three dicts into the state
  after they all complete (fan-in at match_agent).
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, JobProfile
from app.graph.tools.llm import llm
from app.graph.tools.jd_parser import fetch_jd, normalize_jd
from app.graph.prompts.job import JOB_SYSTEM_PROMPT, JOB_USER_PROMPT

logger = logging.getLogger(__name__)


def job_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: fetch job listing URL → JobProfile.

    Args:
        state: Reads state["job_url"].

    Returns:
        {"job_profile": JobProfile} on success, {"error": str} on failure.
    """
    job_url = state.get("job_url", "").strip()

    if not job_url:
        return {"error": "job_agent: job_url is empty"}

    # ── Step 1: Get raw JD text ───────────────────────────────────────────────
    # Detect whether the user gave us a URL or pasted raw text directly.
    # URLs start with http/https; anything else is treated as raw JD text.
    #
    # Why support both modes?
    #   - Power users may copy-paste a JD from a PDF or internal system
    #     that isn't publicly accessible (internal ATS, recruiter email, etc.)
    #   - Keeping the field name as "job_url" in state is intentional —
    #     it's the primary input, but we gracefully handle the text case too.
    try:
        if job_url.startswith("http"):
            logger.info("job_agent: fetching JD from URL: %s", job_url)
            jd_text = fetch_jd(job_url)
        else:
            logger.info("job_agent: treating job_url as raw JD text (%d chars)", len(job_url))
            jd_text = normalize_jd(job_url)
    except Exception as e:
        logger.error("job_agent: failed to get JD text: %s", e)
        return {"error": f"job_agent fetch failed: {e}"}

    # ── Step 2: LLM structured extraction ────────────────────────────────────
    messages = [
        SystemMessage(content=JOB_SYSTEM_PROMPT),
        HumanMessage(content=JOB_USER_PROMPT.format(jd_text=jd_text)),
    ]

    structured_llm = llm.with_structured_output(JobProfile)

    logger.info("job_agent: invoking LLM on %d chars of JD text", len(jd_text))

    try:
        profile: JobProfile = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("job_agent: LLM call failed: %s", e)
        return {"error": f"job_agent LLM failed: {e}"}

    logger.info(
        "job_agent: extracted %d required skills, %.1f yrs exp required",
        len(profile.required_skills),
        profile.experience_required,
    )

    return {"job_profile": profile}

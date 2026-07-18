"""
company_agent.py — Extracts company identity from a job description.

Node signature: company_agent_node(state) -> dict

Flow:
  1. Read state["job_url"] — same source as job_agent
  2. Fetch/normalise JD text (may already be in memory if LangGraph caches,
     but we fetch independently since nodes run in parallel)
  3. LLM → CompanyProfile via with_structured_output
  4. Return {"company_profile": <CompanyProfile>}

Why fetch the URL again instead of reading job_agent's output?
  Because this node runs IN PARALLEL with job_agent — it starts at the same
  time, before job_agent has written its result to state.  In a parallel
  fan-out, nodes cannot read each other's outputs; they only see the state
  as it was when the fan-out began.  This is a fundamental LangGraph rule:
  parallel nodes are isolated during execution, merged after completion.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, CompanyProfile
from app.graph.tools.llm import llm
from app.graph.tools.jd_parser import fetch_jd, normalize_jd
from app.graph.prompts.company import COMPANY_SYSTEM_PROMPT, COMPANY_USER_PROMPT

logger = logging.getLogger(__name__)


def company_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: extract company info from the job listing → CompanyProfile.

    Args:
        state: Reads state["job_url"].

    Returns:
        {"company_profile": CompanyProfile} on success, {"error": str} on failure.
    """
    job_url = state.get("job_url", "").strip()

    if not job_url:
        return {"error": "company_agent: job_url is empty"}

    # ── Fetch JD text (same fetch as job_agent, independent call) ────────────
    try:
        if job_url.startswith("http"):
            jd_text = fetch_jd(job_url)
        else:
            jd_text = normalize_jd(job_url)
    except Exception as e:
        logger.error("company_agent: failed to get JD text: %s", e)
        return {"error": f"company_agent fetch failed: {e}"}

    # ── LLM structured extraction ─────────────────────────────────────────────
    # Same pattern as job_agent and resume_agent.
    # Notice we use the SAME llm object — it's stateless (just an API client),
    # so sharing it across agents is safe and avoids duplicate connection pools.
    messages = [
        SystemMessage(content=COMPANY_SYSTEM_PROMPT),
        HumanMessage(content=COMPANY_USER_PROMPT.format(jd_text=jd_text)),
    ]

    structured_llm = llm.with_structured_output(CompanyProfile)

    logger.info("company_agent: invoking LLM on %d chars of JD text", len(jd_text))

    try:
        profile: CompanyProfile = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("company_agent: LLM call failed: %s", e)
        return {"error": f"company_agent LLM failed: {e}"}

    logger.info("company_agent: extracted company='%s', industry='%s'", profile.name, profile.industry)

    return {"company_profile": profile}

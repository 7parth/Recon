"""
resume_agent.py — Parses raw resume text into a structured CandidateProfile.

Node signature (required by LangGraph):
  resume_agent_node(state: ApplicationState) -> dict

Flow:
  1. Read state["resume_raw"]  (set by the API layer on upload)
  2. Call parse_resume() if we ever receive file bytes instead of text
     (not needed here — the API layer handles file→text before graph runs)
  3. Build a prompt from the raw text
  4. Ask the LLM to respond as a CandidateProfile (structured output)
  5. Return {"resume_profile": <CandidateProfile>} — LangGraph merges this in

Key concept — with_structured_output():
  Instead of asking the LLM to "return JSON" and then parsing the string
  ourselves, we bind a Pydantic model to the LLM.  Under the hood LangChain
  either uses function-calling (OpenAI-style) or JSON mode to guarantee
  the output matches the schema.  The return value is already a Python object.
"""

import logging
from langchain_core.messages import SystemMessage, HumanMessage

from app.graph.state import ApplicationState, CandidateProfile
from app.graph.tools.llm import llm
from app.graph.prompts.resume import RESUME_SYSTEM_PROMPT, RESUME_USER_PROMPT

logger = logging.getLogger(__name__)


def resume_agent_node(state: ApplicationState) -> dict:
    """
    LangGraph node: parse raw resume text → CandidateProfile.

    Args:
        state: Current graph state.  We read state["resume_raw"].

    Returns:
        Dict with key "resume_profile" containing a CandidateProfile,
        or "error" if parsing fails.  LangGraph merges this into the state.
    """
    resume_raw = state.get("resume_raw", "").strip()

    if not resume_raw:
        # Planner should have caught this, but defensively handle it here too
        return {"error": "resume_agent: resume_raw is empty"}

    # ── Build the message list ────────────────────────────────────────────────
    # LangChain uses a list of message objects (SystemMessage, HumanMessage,
    # AIMessage) rather than a single string prompt.
    #
    # Why a list of messages instead of one big string?
    #   LLM APIs (OpenAI, NVIDIA NIM, Anthropic) all use a "chat" format with
    #   distinct roles: system (instructions), user (input), assistant (output).
    #   Keeping them separate lets the model apply different attention weights
    #   to instructions vs. content — which improves extraction accuracy.
    messages = [
        SystemMessage(content=RESUME_SYSTEM_PROMPT),
        HumanMessage(content=RESUME_USER_PROMPT.format(resume_text=resume_raw)),
    ]

    # ── Structured output binding ─────────────────────────────────────────────
    # with_structured_output(CandidateProfile) tells LangChain to:
    #   1. Pass the Pydantic schema to the LLM as a function/tool definition
    #   2. Force the LLM to respond in that schema's shape
    #   3. Deserialise the JSON response into a CandidateProfile instance
    #
    # This is safer than: json.loads(llm.invoke(messages).content)
    # because the LLM is constrained to valid output — no manual parsing needed.
    structured_llm = llm.with_structured_output(CandidateProfile)

    logger.info(
        "resume_agent: invoking LLM to parse %d chars of resume text",
        len(resume_raw),
    )

    try:
        profile: CandidateProfile = structured_llm.invoke(messages)
    except Exception as e:
        logger.error("resume_agent: LLM call failed: %s", e)
        return {"error": f"resume_agent failed: {e}"}

    logger.info(
        "resume_agent: extracted %d skills, %.1f yrs experience",
        len(profile.skills),
        profile.experience_years,
    )

    # Return only the keys we're updating — LangGraph merges, not replaces
    return {"resume_profile": profile}

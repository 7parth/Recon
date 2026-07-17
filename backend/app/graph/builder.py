"""
Graph Builder — assembles and compiles the Recon LangGraph.

Topology
────────
START
  │
  ▼
planner ──(error)──────────────────────────────────────────────► END
  │
  ├──► resume_agent ──┐
  ├──► job_agent ─────┤ (parallel fan-out)
  └──► company_agent ─┘
                      │
                      ▼
                  match_agent
                      │
             (score < threshold) ──► END
                      │
                 ats_agent
                      │
              tailoring_agent ◄──── (rejected feedback loop)
                      │                        ▲
              cover_letter_agent               │
                      │                        │
                human_review ── (rejected) ────┘
                      │
                  (approved)
                      │
                apply_agent
                      │
               tracking_agent
                      │
                     END
"""

from langgraph.graph import StateGraph, START, END as LG_END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import ApplicationState
from app.graph.constants import (
    PLANNER,
    RESUME_AGENT,
    JOB_AGENT,
    COMPANY_AGENT,
    MATCH_AGENT,
    ATS_AGENT,
    TAILORING_AGENT,
    COVER_LETTER_AGENT,
    HUMAN_REVIEW,
    APPLY_AGENT,
    TRACKING_AGENT,
)
from app.graph.router import (
    route_after_planner,
    route_after_match,
    route_after_review,
    route_after_apply,
)

# Agent node imports — each module exposes a single `*_node(state) -> dict`
from app.graph.agents.planner import planner_node
from app.graph.agents.resume_agent import resume_agent_node
from app.graph.agents.job_agent import job_agent_node
from app.graph.agents.company_agent import company_agent_node
from app.graph.agents.match_agent import match_agent_node
from app.graph.agents.ats_agent import ats_agent_node
from app.graph.agents.tailoring_agent import tailoring_agent_node
from app.graph.agents.cover_letter_agent import cover_letter_agent_node
from app.graph.agents.human_review_agent import human_review_agent_node
from app.graph.agents.apply_agent import apply_agent_node
from app.graph.agents.tracking_agent import tracking_agent_node


def build_graph(checkpointer=None):
    """
    Build and compile the Recon StateGraph.

    Args:
        checkpointer: A LangGraph checkpointer (default: in-memory).
                      Pass a PostgresSaver for production persistence.

    Returns:
        A compiled LangGraph runnable.
    """
    builder = StateGraph(ApplicationState)

    # ── Register nodes ───────────────────────────────────────────────────────
    builder.add_node(PLANNER, planner_node)
    builder.add_node(RESUME_AGENT, resume_agent_node)
    builder.add_node(JOB_AGENT, job_agent_node)
    builder.add_node(COMPANY_AGENT, company_agent_node)
    builder.add_node(MATCH_AGENT, match_agent_node)
    builder.add_node(ATS_AGENT, ats_agent_node)
    builder.add_node(TAILORING_AGENT, tailoring_agent_node)
    builder.add_node(COVER_LETTER_AGENT, cover_letter_agent_node)
    builder.add_node(HUMAN_REVIEW, human_review_agent_node)
    builder.add_node(APPLY_AGENT, apply_agent_node)
    builder.add_node(TRACKING_AGENT, tracking_agent_node)

    # ── Entry edge ───────────────────────────────────────────────────────────
    builder.add_edge(START, PLANNER)

    # ── After planner: fan out to parallel parsing agents or END on error ────
    builder.add_conditional_edges(
        PLANNER,
        route_after_planner,
        {
            RESUME_AGENT: RESUME_AGENT,
            JOB_AGENT: JOB_AGENT,
            COMPANY_AGENT: COMPANY_AGENT,
            LG_END: LG_END,
        },
    )

    # ── Parallel parsing agents all converge on match_agent ─────────────────
    builder.add_edge(RESUME_AGENT, MATCH_AGENT)
    builder.add_edge(JOB_AGENT, MATCH_AGENT)
    builder.add_edge(COMPANY_AGENT, MATCH_AGENT)

    # ── Match threshold gate ─────────────────────────────────────────────────
    builder.add_conditional_edges(
        MATCH_AGENT,
        route_after_match,
        {
            ATS_AGENT: ATS_AGENT,
            LG_END: LG_END,
        },
    )

    # ── Linear pipeline: ATS → Tailor → Cover Letter → Human Review ─────────
    builder.add_edge(ATS_AGENT, TAILORING_AGENT)
    builder.add_edge(TAILORING_AGENT, COVER_LETTER_AGENT)
    builder.add_edge(COVER_LETTER_AGENT, HUMAN_REVIEW)

    # ── Human review gate: approved → apply, rejected → re-tailor ───────────
    builder.add_conditional_edges(
        HUMAN_REVIEW,
        route_after_review,
        {
            APPLY_AGENT: APPLY_AGENT,
            TAILORING_AGENT: TAILORING_AGENT,
            LG_END: LG_END,
        },
    )

    # ── Apply → Tracking → END ───────────────────────────────────────────────
    builder.add_conditional_edges(
        APPLY_AGENT,
        route_after_apply,
        {TRACKING_AGENT: TRACKING_AGENT},
    )
    builder.add_edge(TRACKING_AGENT, LG_END)

    # ── Compile ──────────────────────────────────────────────────────────────
    cp = checkpointer or MemorySaver()
    return builder.compile(
        checkpointer=cp,
        interrupt_before=[HUMAN_REVIEW],   # pause for human approval
    )


# Singleton for use by FastAPI routes (in-memory checkpointer for dev)
graph = build_graph()

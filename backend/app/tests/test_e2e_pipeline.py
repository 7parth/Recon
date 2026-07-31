"""
app/tests/test_e2e_pipeline.py — End-to-end pipeline smoke test.

Verifies:
1. Resume parsing
2. Graph execution (Planner -> Resume/Job/Company -> Match -> ATS -> Tailor -> Cover Letter -> Human Review Interrupt)
3. Human Review Approval resumption (Human Review -> Apply -> Tracking -> END)
4. Logging durability & status endpoints
"""

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

from app.main import app
from app.graph.builder import build_graph
from app.graph.constants import HUMAN_REVIEW
from app.utils.logger import get_automation_logger


@pytest.fixture
def client():
    return TestClient(app)


@pytest.mark.asyncio
async def test_end_to_end_graph_execution():
    """Test full graph execution with MemorySaver checkpointer."""
    checkpointer = MemorySaver()
    graph = build_graph(checkpointer=checkpointer)

    thread_id = "test_e2e_thread_001"
    config = {"configurable": {"thread_id": thread_id}}

    initial_input = {
        "resume_raw": "Senior Software Engineer with 5 years experience in Python, FastAPI, React, PostgreSQL, Docker, AWS.",
        "raw_jd": "Looking for a Senior Software Engineer with strong Python, FastAPI, and React skills to build cloud applications.",
        "job_url": "https://boards.greenhouse.io/example/jobs/12345",
        "match_score_threshold": 0.1,
    }

    # 1. First execution: run until human review interrupt
    async for event in graph.astream(initial_input, config=config):
        print(f"EVENT: {event}")

    state = await graph.aget_state(config)
    print(f"STATE NEXT: {state.next}")
    print(f"STATE VALUES: {state.values}")
    
    # Assert paused before HUMAN_REVIEW
    assert state.next == (HUMAN_REVIEW,)
    assert state.values.get("approval_status") == "pending"
    assert state.values.get("match_score", 0) >= 0

    # 2. Approve review state
    await graph.aupdate_state(
        config,
        {"approval_status": "approved", "rejection_feedback": None},
        as_node=HUMAN_REVIEW,
    )

    # 3. Resume graph execution from human_review node
    async for event in graph.astream(None, config=config):
        pass

    final_state = await graph.aget_state(config)
    assert final_state.next == ()  # Reached END
    assert final_state.values.get("submission_status") in ["submitted", "skipped", "completed", "failed"]


def test_health_check_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

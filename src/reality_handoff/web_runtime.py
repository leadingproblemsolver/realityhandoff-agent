from __future__ import annotations

import uuid
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from .graph import build_graph
from .recovery import recover
from .security import redact_obj

_checkpointer = InMemorySaver()
_graph = build_graph(checkpointer=_checkpointer)
_known_runs: set[str] = set()


def _config(execution_id: str) -> dict[str, Any]:
    return {"configurable": {"thread_id": execution_id}}


def _public_state(values: dict[str, Any], *, exists: bool = True) -> dict[str, Any]:
    if not exists:
        return {"found": False}
    stage = values.get("stage")
    status = values.get("status")
    return redact_obj(
        {
            "found": True,
            "execution_id": values.get("execution_id"),
            "task": values.get("task"),
            "stage": stage,
            "status": status,
            "target_urn": values.get("target_urn"),
            "evidence": [
                {
                    "evidence_id": e.get("evidence_id"),
                    "tool_name": e.get("tool_name"),
                    "entity_urn": e.get("entity_urn"),
                    "summary": e.get("summary"),
                    "result_digest": e.get("result_digest"),
                }
                for e in values.get("evidence", [])
            ],
            "reality": values.get("reality"),
            "gate": values.get("gate"),
            "contract": values.get("contract"),
            "action_plan": values.get("action_plan"),
            "verification": values.get("verification"),
            "handoff": values.get("handoff"),
            "handoff_location": values.get("handoff_location"),
            "handoff_recovery": values.get("handoff_recovery"),
            "error": values.get("error"),
            "requires_approval": status == "APPROVAL_PENDING",
            "terminal": stage == "COMPLETE",
        }
    )


async def start_run(task: str) -> dict[str, Any]:
    execution_id = f"rh_{uuid.uuid4().hex[:12]}"
    _known_runs.add(execution_id)
    await _graph.ainvoke(
        {"execution_id": execution_id, "task": task},
        config=_config(execution_id),
    )
    state = await _graph.aget_state(_config(execution_id))
    return _public_state(dict(state.values))


async def get_run(execution_id: str) -> dict[str, Any]:
    if execution_id not in _known_runs:
        return _public_state({}, exists=False)
    state = await _graph.aget_state(_config(execution_id))
    return _public_state(dict(state.values))


async def decide_run(execution_id: str, approved: bool) -> dict[str, Any]:
    if execution_id not in _known_runs:
        return _public_state({}, exists=False)
    state = await _graph.aget_state(_config(execution_id))
    values = dict(state.values)
    if values.get("status") != "APPROVAL_PENDING":
        raise ValueError("Run is not awaiting human approval")
    await _graph.ainvoke(Command(resume=approved), config=_config(execution_id))
    state = await _graph.aget_state(_config(execution_id))
    return _public_state(dict(state.values))


async def recover_handoff(execution_id: str, target_urn: str | None = None) -> dict[str, Any]:
    return redact_obj(await recover(execution_id, target_urn))

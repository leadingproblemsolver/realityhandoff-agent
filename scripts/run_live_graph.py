"""Run the full local graph with an explicit human-approval interrupt.

Requires live DataHub MCP credentials and ALLOW_DATAHUB_MUTATIONS=true.
Nothing is auto-approved: the script pauses and asks for y/N.
"""
from __future__ import annotations
import argparse
import asyncio
import json
import uuid


async def main() -> int:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.types import Command
    from reality_handoff.graph import build_graph

    parser = argparse.ArgumentParser()
    parser.add_argument("task")
    parser.add_argument("--execution-id", default=None)
    args = parser.parse_args()

    execution_id = args.execution_id or f"rh_{uuid.uuid4().hex[:12]}"
    thread_id = f"thread_{execution_id}"
    graph = build_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": thread_id}}

    result = await graph.ainvoke(
        {"execution_id": execution_id, "task": args.task, "stage": "RECEIVED"},
        config=config,
    )
    if "__interrupt__" in result:
        print(json.dumps({"interrupt": [str(x) for x in result["__interrupt__"]]}, indent=2))
        approved = input("Approve the exact contract + action + post-verification handoff? [y/N] ").strip().lower() == "y"
        result = await graph.ainvoke(Command(resume=approved), config=config)

    print(json.dumps(result, indent=2, default=str))
    return 0 if result.get("status") not in {"ACTION_FAILED", "VERIFY_FAILED", "HANDOFF_FAILED", "HANDOFF_VERIFY_FAILED", "DATAHUB_MCP_UNREACHABLE"} else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

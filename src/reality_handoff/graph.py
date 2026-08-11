from __future__ import annotations
from langgraph.graph import StateGraph, START, END
from .models import AgentState, Stage
from .nodes import (
    intake_node,
    preflight_node,
    context_node,
    reality_node,
    gate_node,
    contract_node,
    plan_node,
    approval_node,
    action_node,
    verify_node,
    handoff_node,
    handoff_verify_node,
    terminal_node,
)


def _stage_is(state, stage):
    return state.get("stage") == stage.value


def build_graph(checkpointer=None):
    g = StateGraph(AgentState)
    for name, node in [
        ("intake", intake_node),
        ("preflight", preflight_node),
        ("context", context_node),
        ("reality", reality_node),
        ("gate", gate_node),
        ("contract", contract_node),
        ("plan", plan_node),
        ("approval", approval_node),
        ("action", action_node),
        ("verify", verify_node),
        ("handoff", handoff_node),
        ("handoff_verify", handoff_verify_node),
        ("terminal", terminal_node),
    ]:
        g.add_node(name, node)

    g.add_edge(START, "intake")
    g.add_conditional_edges("intake", lambda s: "next" if _stage_is(s, Stage.RECEIVED) else "stop", {"next": "preflight", "stop": "terminal"})
    g.add_conditional_edges("preflight", lambda s: "next" if _stage_is(s, Stage.MCP_PREFLIGHT) else "stop", {"next": "context", "stop": "terminal"})
    g.add_conditional_edges("context", lambda s: "next" if _stage_is(s, Stage.CONTEXT_BUILDING) else "stop", {"next": "reality", "stop": "terminal"})
    g.add_conditional_edges("reality", lambda s: "next" if _stage_is(s, Stage.REALITY_COMPILED) else "stop", {"next": "gate", "stop": "terminal"})
    g.add_conditional_edges("gate", lambda s: "next" if s.get("stage") == "READY" else "stop", {"next": "contract", "stop": "terminal"})
    g.add_conditional_edges("contract", lambda s: "next" if _stage_is(s, Stage.CONTRACT_READY) else "stop", {"next": "plan", "stop": "terminal"})
    g.add_conditional_edges("plan", lambda s: "next" if _stage_is(s, Stage.APPROVAL_PENDING) else "stop", {"next": "approval", "stop": "terminal"})
    g.add_conditional_edges("approval", lambda s: "next" if s.get("status") == "APPROVED" else "stop", {"next": "action", "stop": "terminal"})
    g.add_conditional_edges("action", lambda s: "next" if _stage_is(s, Stage.ACTION_EXECUTED) else "stop", {"next": "verify", "stop": "terminal"})
    g.add_conditional_edges("verify", lambda s: "next" if _stage_is(s, Stage.VERIFIED) else "stop", {"next": "handoff", "stop": "terminal"})
    g.add_conditional_edges("handoff", lambda s: "next" if _stage_is(s, Stage.HANDOFF_WRITING) else "stop", {"next": "handoff_verify", "stop": "terminal"})
    g.add_edge("handoff_verify", "terminal")
    g.add_edge("terminal", END)
    return g.compile(checkpointer=checkpointer)


graph = build_graph()

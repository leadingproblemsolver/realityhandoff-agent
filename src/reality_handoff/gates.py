from __future__ import annotations
from collections.abc import Collection
from .models import GateResult, RealitySnapshot, Stage

ALLOWED_TRANSITIONS = {
    Stage.RECEIVED: {Stage.MCP_PREFLIGHT},
    Stage.MCP_PREFLIGHT: {Stage.CONTEXT_BUILDING, Stage.FAILED},
    Stage.CONTEXT_BUILDING: {Stage.REALITY_COMPILED, Stage.NEEDS_CONTEXT, Stage.FAILED},
    Stage.REALITY_COMPILED: {Stage.CONTRACT_READY, Stage.NEEDS_CONTEXT, Stage.NEEDS_HUMAN, Stage.BLOCKED},
    Stage.NEEDS_CONTEXT: {Stage.CONTEXT_BUILDING, Stage.COMPLETE},
    Stage.NEEDS_HUMAN: {Stage.COMPLETE},
    Stage.BLOCKED: {Stage.COMPLETE},
    Stage.CONTRACT_READY: {Stage.APPROVAL_PENDING},
    Stage.APPROVAL_PENDING: {Stage.ACTION_EXECUTED, Stage.DENIED},
    Stage.DENIED: {Stage.COMPLETE},
    Stage.ACTION_EXECUTED: {Stage.VERIFYING},
    Stage.VERIFYING: {Stage.VERIFIED, Stage.FAILED},
    Stage.VERIFIED: {Stage.HANDOFF_WRITING},
    Stage.HANDOFF_WRITING: {Stage.HANDOFF_VERIFIED, Stage.FAILED},
    Stage.HANDOFF_VERIFIED: {Stage.COMPLETE},
    Stage.FAILED: {Stage.COMPLETE},
}


def require_transition(current: Stage | str, new: Stage | str) -> None:
    c, n = Stage(current), Stage(new)
    if n not in ALLOWED_TRANSITIONS.get(c, set()):
        raise ValueError(f"illegal state transition: {c.value} -> {n.value}")


def evaluate_reality(
    reality: RealitySnapshot,
    valid_evidence_ids: Collection[str] | None = None,
) -> GateResult:
    valid = set(valid_evidence_ids) if valid_evidence_ids is not None else None
    unsupported = []
    for fact in reality.facts:
        if not fact.evidence_ids:
            unsupported.append(fact)
            continue
        if valid is not None and any(eid not in valid for eid in fact.evidence_ids):
            unsupported.append(fact)
    if unsupported:
        return GateResult(
            decision="BLOCKED",
            reason="One or more factual claims do not resolve to retrieved evidence IDs.",
            blocking_items=[f.claim_id for f in unsupported],
        )
    blocking_unknowns = [u for u in reality.unknowns if u.blocks_execution]
    if blocking_unknowns:
        return GateResult(
            decision="NEEDS_HUMAN",
            reason="A semantic unknown blocks safe execution.",
            blocking_items=[u.statement for u in blocking_unknowns],
        )
    if reality.contradictions:
        return GateResult(
            decision="NEEDS_CONTEXT",
            reason="Contradictory evidence must be resolved before mutation.",
            blocking_items=reality.contradictions,
        )
    if not reality.target_urn:
        return GateResult(
            decision="NEEDS_CONTEXT",
            reason="No target DataHub entity was resolved.",
            blocking_items=["target_urn"],
        )
    return GateResult(
        decision="READY",
        reason="Facts resolve to retrieved evidence; no blocking unknowns or contradictions remain.",
    )

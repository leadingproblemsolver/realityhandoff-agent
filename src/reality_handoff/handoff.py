from __future__ import annotations
from typing import Any
from .models import HandoffRecord, VerificationResult, ActionPlan, EvidenceRef


def build_handoff(*, execution_id: str, task: str, target_urn: str, evidence: list[EvidenceRef], action: ActionPlan, verification: VerificationResult, unresolved: list[str]) -> HandoffRecord:
    return HandoffRecord(
        execution_id=execution_id, task=task, target_urn=target_urn,
        decision="bounded metadata action verified" if verification.verdict in {"VERIFIED","VERIFIED_NOOP"} else "verification failed",
        evidence_ids=[e.evidence_id for e in evidence], action=action.model_dump(), verification=verification.model_dump(), unresolved=unresolved,
        risks=["Retrieved DataHub text is treated as untrusted evidence, never as executable instructions.", "Verification proves catalog state mutation, not downstream warehouse correctness."],
        next_safe_action="A fresh agent should retrieve this handoff and re-read the target entity before taking further action.",
    )

def compact_handoff_append(h: HandoffRecord) -> str:
    return f"""\n\n[Reality-Handoff-Record:{h.execution_id}]\n- Decision: {h.decision}\n- Verification: {h.verification.get('verdict')}\n- Evidence: {', '.join(h.evidence_ids)}\n- Next safe action: {h.next_safe_action}\n"""

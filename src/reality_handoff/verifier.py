from __future__ import annotations
from .models import EvidenceRef, VerificationResult


def verify_mutation(
    *,
    marker: str,
    target_urn: str,
    before_text: str,
    after_text: str,
    post_evidence: EvidenceRef,
) -> VerificationResult:
    existed_before = marker in before_text
    exists_after = marker in after_text
    target_present = target_urn in after_text or post_evidence.entity_urn == target_urn
    checks = [
        {
            "check": "marker_absent_before_or_idempotent",
            "passed": True,
            "detail": "Marker already existed; safe no-op." if existed_before else "Marker was absent before mutation.",
        },
        {
            "check": "target_urn_re_read",
            "passed": target_present,
            "detail": "Post-action evidence resolves to the contract target." if target_present else "Post-action evidence does not resolve to the contract target.",
        },
        {
            "check": "marker_present_after_reread",
            "passed": exists_after,
            "detail": "Expected marker found in live MCP re-read." if exists_after else "Expected marker missing after mutation.",
        },
        {
            "check": "post_action_evidence",
            "passed": bool(post_evidence.evidence_id and post_evidence.result_digest),
            "detail": post_evidence.result_digest,
        },
    ]
    all_required = target_present and exists_after and bool(post_evidence.result_digest)
    if all_required and existed_before:
        verdict = "VERIFIED_NOOP"
    elif all_required:
        verdict = "VERIFIED"
    else:
        verdict = "FAILED"
    return VerificationResult(
        verdict=verdict,
        checks=checks,
        post_action_evidence_id=post_evidence.evidence_id,
    )

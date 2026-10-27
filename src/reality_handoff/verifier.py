from __future__ import annotations

import json
from .models import EvidenceRef, VerificationResult


def _entity_records(text: str) -> list[dict]:
    """Decode the structured get_entities payload; unrecognized shapes fail closed."""
    try:
        payload = json.loads(text)
    except (TypeError, ValueError):
        return []

    # LangChain/MCP may wrap the JSON result in a single text content block.
    if isinstance(payload, dict) and isinstance(payload.get("content"), list):
        blocks = payload["content"]
        if (
            len(blocks) != 1
            or not isinstance(blocks[0], dict)
            or blocks[0].get("type") != "text"
        ):
            return []
        try:
            payload = json.loads(blocks[0]["text"])
        except (TypeError, KeyError, ValueError):
            return []
    elif (
        isinstance(payload, list)
        and len(payload) == 1
        and isinstance(payload[0], dict)
        and payload[0].get("type") == "text"
    ):
        try:
            payload = json.loads(payload[0]["text"])
        except (TypeError, KeyError, ValueError):
            return []

    if isinstance(payload, dict):
        payload = payload.get("entities", [])
    if not isinstance(payload, list) or not all(isinstance(item, dict) for item in payload):
        return []
    return payload


def _target_description(text: str, target_urn: str) -> tuple[bool, str]:
    matches = [entity for entity in _entity_records(text) if entity.get("urn") == target_urn]
    if len(matches) != 1 or matches[0].get("error"):
        return False, ""
    entity = matches[0]
    # The mutation changes the entity description, not descriptions on related entities.
    for key in ("editableProperties", "properties"):
        props = entity.get(key)
        if isinstance(props, dict) and isinstance(props.get("description"), str):
            return True, props["description"]
    return True, ""


def verify_mutation(
    *,
    marker: str,
    target_urn: str,
    before_text: str,
    after_text: str,
    post_evidence: EvidenceRef,
) -> VerificationResult:
    _, before_description = _target_description(before_text, target_urn)
    target_present, after_description = _target_description(after_text, target_urn)
    existed_before = bool(marker) and marker in before_description
    exists_after = bool(marker) and marker in after_description
    evidence_ok = bool(
        post_evidence.evidence_id
        and post_evidence.result_digest
        and post_evidence.tool_name == "get_entities"
        and post_evidence.entity_urn == target_urn
    )
    checks = [
        {
            "check": "marker_absent_before_or_idempotent",
            "passed": True,
            "detail": (
                "Marker already existed on target; safe no-op."
                if existed_before
                else "Marker was absent from target before mutation."
            ),
        },
        {
            "check": "target_urn_re_read",
            "passed": target_present,
            "detail": (
                "Exactly one returned entity matches the approved target."
                if target_present
                else "Exact target entity missing, ambiguous, or errored."
            ),
        },
        {
            "check": "marker_present_after_reread",
            "passed": exists_after,
            "detail": (
                "Expected marker found in target entity description."
                if exists_after
                else "Expected marker missing from target entity description."
            ),
        },
        {
            "check": "post_action_evidence",
            "passed": evidence_ok,
            "detail": post_evidence.result_digest,
        },
    ]
    all_required = target_present and exists_after and evidence_ok
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

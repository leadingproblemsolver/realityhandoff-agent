from reality_handoff.models import EvidenceRef
from reality_handoff.verifier import verify_mutation

TARGET = "urn:li:dataset:x"


def ev(entity_urn=TARGET):
    return EvidenceRef(
        evidence_id="ev_9",
        tool_name="get_entities",
        entity_urn=entity_urn,
        result_digest="sha256:x",
        summary="post",
    )


def test_verifies_exact_marker():
    assert (
        verify_mutation(
            marker="[RH]",
            target_urn=TARGET,
            before_text="a",
            after_text=f"{TARGET} a [RH]",
            post_evidence=ev(),
        ).verdict
        == "VERIFIED"
    )


def test_missing_marker_fails():
    assert (
        verify_mutation(
            marker="[RH]",
            target_urn=TARGET,
            before_text="a",
            after_text=f"{TARGET} a",
            post_evidence=ev(),
        ).verdict
        == "FAILED"
    )


def test_wrong_target_fails():
    assert (
        verify_mutation(
            marker="[RH]",
            target_urn=TARGET,
            before_text="a",
            after_text="urn:li:dataset:y [RH]",
            post_evidence=ev("urn:li:dataset:y"),
        ).verdict
        == "FAILED"
    )


def test_existing_marker_is_idempotent():
    assert (
        verify_mutation(
            marker="[RH]",
            target_urn=TARGET,
            before_text="a [RH]",
            after_text=f"{TARGET} a [RH]",
            post_evidence=ev(),
        ).verdict
        == "VERIFIED_NOOP"
    )

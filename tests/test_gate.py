import pytest
from reality_handoff.gates import evaluate_reality, require_transition
from reality_handoff.models import Claim, RealitySnapshot


def fact(evidence=True, evidence_id="ev1"):
    return Claim(
        claim_id="f1",
        statement="x",
        kind="fact",
        evidence_ids=[evidence_id] if evidence else [],
        confidence=1,
    )


def test_ready():
    assert (
        evaluate_reality(
            RealitySnapshot(facts=[fact()], target_urn="urn:li:dataset:x"), {"ev1"}
        ).decision
        == "READY"
    )


def test_unsupported_fact_blocks():
    assert (
        evaluate_reality(
            RealitySnapshot(facts=[fact(False)], target_urn="urn:li:dataset:x"), {"ev1"}
        ).decision
        == "BLOCKED"
    )


def test_hallucinated_evidence_id_blocks():
    assert (
        evaluate_reality(
            RealitySnapshot(facts=[fact(True, "ev_999")], target_urn="urn:li:dataset:x"),
            {"ev_001"},
        ).decision
        == "BLOCKED"
    )


def test_blocking_unknown_needs_human():
    unknown = Claim(
        claim_id="u",
        statement="revenue unresolved",
        kind="unknown",
        blocks_execution=True,
    )
    assert (
        evaluate_reality(
            RealitySnapshot(facts=[fact()], unknowns=[unknown], target_urn="urn:li:dataset:x"),
            {"ev1"},
        ).decision
        == "NEEDS_HUMAN"
    )


def test_contradiction_needs_context():
    assert (
        evaluate_reality(
            RealitySnapshot(
                facts=[fact()], contradictions=["type mismatch"], target_urn="urn:li:dataset:x"
            ),
            {"ev1"},
        ).decision
        == "NEEDS_CONTEXT"
    )


def test_no_target_needs_context():
    assert evaluate_reality(RealitySnapshot(facts=[fact()]), {"ev1"}).decision == "NEEDS_CONTEXT"


def test_illegal_transition_rejected():
    with pytest.raises(ValueError):
        require_transition("RECEIVED", "VERIFIED")

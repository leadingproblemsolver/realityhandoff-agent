from reality_handoff.hermes_preflight import preflight


def test_completed_handoff_passes_with_settlement_evidence():
    result = preflight(
        {
            "task_id": "task-17",
            "status": "completed",
            "changed": "Added deterministic handoff receipt.",
            "verified": ["pytest -q: 4 passed"],
            "retry_unblock": "Re-run the preflight with the same task envelope.",
            "remaining_risk": "No native Hermes adapter yet.",
        }
    )

    assert result.verdict == "PASS"
    assert result.settlement_ready is True
    assert result.missing == ()


def test_timed_out_handoff_blocks_when_partial_findings_are_lost():
    result = preflight(
        {
            "task_id": "task-18",
            "status": "timed_out",
            "changed": "Investigated dispatcher failure.",
            "verified": "Reproduced on fixture.",
            "retry_unblock": "Increase budget after preserving findings.",
            "remaining_risk": "Root cause not fixed.",
        }
    )

    assert result.verdict == "BLOCK"
    assert result.missing == ("partial_findings",)


def test_aliases_normalize_without_weakening_contract():
    result = preflight(
        {
            "id": "task-19",
            "state": "timeout",
            "summary": "Investigated dispatcher failure.",
            "tests": ["fixture reproduction"],
            "recovery": "Retry from preserved state.",
            "risk": "Root cause open.",
            "partial_summary": "Likely stale-run race near settlement.",
        }
    )

    assert result.verdict == "PASS"
    assert result.normalized["status"] == "timed_out"


def test_missing_verification_blocks_completion():
    result = preflight(
        {
            "task_id": "task-20",
            "status": "completed",
            "changed": "Changed task routing.",
            "verified": [],
            "retry_unblock": "Restore previous rule.",
            "remaining_risk": "No production soak.",
        }
    )

    assert result.verdict == "BLOCK"
    assert result.missing == ("verified",)

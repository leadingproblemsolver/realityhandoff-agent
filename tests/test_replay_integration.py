from reality_handoff.replay import run_replay

def test_valid_end_to_end_reads_acts_verifies_handoffs():
    r=run_replay(task="inspect canonical customer orders")
    assert r["gate"]["decision"]=="READY"
    assert r["mutations"]==1
    assert r["verification"]["verdict"]=="VERIFIED"
    assert r["handoff_recovered"] is True

def test_ambiguity_blocks_before_mutation():
    r=run_replay(task="fix revenue definition",ambiguous=True)
    assert r["gate"]["decision"]=="NEEDS_HUMAN" and r["mutations"]==0

def test_tampered_post_state_fails_verification():
    r=run_replay(task="inspect orders",tamper_after=True)
    assert r["verification"]["verdict"]=="FAILED"
    assert "handoff_recovered" not in r

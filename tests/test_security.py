from reality_handoff.security import redact


def test_redacts_bearer():
    assert "secretvalue" not in redact("Authorization: Bearer secretvalue")


def test_redacts_common_token_without_embedding_token_literal_in_repo():
    token = "t" + "gt_" + "abcdefghijklmnop"
    assert token not in redact("x " + token + " y")

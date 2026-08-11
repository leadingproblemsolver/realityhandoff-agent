from reality_handoff.evidence import choose_dataset_urn, extract_urns


def test_forced_target_must_be_in_candidates_when_using_selector():
    assert choose_dataset_urn(["urn:li:dataset:a"], "urn:li:dataset:b") is None


def test_extracts_dataset_urn():
    urn = "urn:li:dataset:(urn:li:dataPlatform:snowflake,showcase.orders,PROD)"
    assert urn in extract_urns({"urn": urn})

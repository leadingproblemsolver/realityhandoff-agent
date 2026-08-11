from reality_handoff.models import EvidenceRef
from reality_handoff.reality import deterministic_semantic_unknowns

URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,showcase.orders,PROD)"


def ev(text: str) -> EvidenceRef:
    return EvidenceRef(
        evidence_id="ev_semantic",
        tool_name="get_entities",
        entity_urn=URN,
        result_digest="sha256:test",
        summary="retrieved context",
        raw_excerpt=text,
    )


def test_revenue_without_authoritative_definition_blocks():
    unknowns = deterministic_semantic_unknowns(
        "Build a revenue rollup",
        [ev('{"description":"Orders feed used by the revenue dashboard"}')],
    )
    assert len(unknowns) == 1
    assert unknowns[0].kind == "unknown"
    assert unknowns[0].blocks_execution is True
    assert "revenue" in unknowns[0].statement.lower()


def test_revenue_with_definition_signal_is_resolved():
    unknowns = deterministic_semantic_unknowns(
        "Build a revenue rollup",
        [
            ev(
                '{"businessGlossary":{"term":"Revenue",'
                '"definition":"recognized order value after refunds"}}'
            )
        ],
    )
    assert unknowns == []

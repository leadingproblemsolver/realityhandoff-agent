import pytest
from reality_handoff import nodes
from reality_handoff.contracts import build_contract
from reality_handoff.models import (
    ActionPlan,
    Claim,
    EvidenceRef,
    GateResult,
    RealitySnapshot,
    VerificationResult,
)

URN = "urn:li:dataset:(urn:li:dataPlatform:snowflake,showcase.orders,PROD)"


def evidence():
    return [
        EvidenceRef(
            evidence_id="ev_001",
            tool_name="get_entities",
            entity_urn=URN,
            result_digest="sha256:x",
            summary="entity",
            raw_excerpt=f'{{"urn":"{URN}"}}',
        )
    ]


def state_for_write():
    ev = evidence()
    gate = GateResult(decision="READY", reason="ok")
    contract = build_contract(
        execution_id="exec001", task="inspect orders", target_urn=URN, evidence=ev, gate=gate
    )
    plan = ActionPlan(
        target_urn=URN,
        description_append=contract.expected_mutation.expected_marker + "\ncontinuity",
        marker=contract.expected_mutation.expected_marker,
        evidence_ids=contract.evidence_dependencies,
        rationale="bounded",
    )
    reality = RealitySnapshot(
        facts=[
            Claim(
                claim_id="f1",
                statement="entity context read",
                kind="fact",
                evidence_ids=["ev_001"],
                confidence=1,
            )
        ],
        target_urn=URN,
    )
    verification = VerificationResult(verdict="VERIFIED", checks=[])
    return {
        "execution_id": "exec001",
        "task": "inspect orders",
        "target_urn": URN,
        "evidence": [e.model_dump() for e in ev],
        "contract": contract.model_dump(),
        "action_plan": plan.model_dump(),
        "reality": reality.model_dump(),
        "verification": verification.model_dump(),
        "tool_manifest": {"tools": ["save_document", "update_description", "get_entities"]},
    }


@pytest.mark.asyncio
async def test_context_fails_closed_when_required_lineage_read_fails(monkeypatch):
    async def fake_invoke(name, args, mutation=False):
        if name == "search":
            return {"results": [{"urn": URN}]}
        if name == "get_entities":
            return {"urn": URN, "description": "orders"}
        if name == "list_schema_fields":
            return {"urn": URN, "fields": [{"fieldPath": "order_id"}]}
        if name == "get_lineage" and args.get("upstream") is True:
            return {"urn": URN, "upstream": ["urn:li:dataset:raw"]}
        if name == "get_lineage" and args.get("upstream") is False:
            raise RuntimeError("downstream unavailable")
        raise AssertionError(name)

    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    result = await nodes.context_node({"task": "inspect orders", "tool_manifest": {"tools": []}})
    assert result["status"] == "REQUIRED_CONTEXT_READ_FAILED"
    assert result["stage"] == "NEEDS_CONTEXT"
    assert any("get_lineage failed" in e for e in result["context_errors"])


@pytest.mark.asyncio
async def test_action_uses_append_operation_and_contract_target(monkeypatch):
    state = state_for_write()
    state["before_entity_text"] = '{"description":"clean"}'
    calls = []

    async def fake_invoke(name, args, mutation=False):
        calls.append((name, args, mutation))
        return {"ok": True}

    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    result = await nodes.action_node(state)
    assert result["status"] == "ACTION_EXECUTED"
    assert calls == [
        (
            "update_description",
            {
                "urn": URN,
                "description": state["action_plan"]["description_append"],
                "mode": "append",
            },
            True,
        )
    ]


@pytest.mark.asyncio
async def test_handoff_save_document_has_document_type_and_related_asset(monkeypatch):
    state = state_for_write()
    calls = []

    async def fake_invoke(name, args, mutation=False):
        calls.append((name, args, mutation))
        if name == "save_document":
            return {"urn": "urn:li:document:rh-exec001", "status": "saved"}
        raise AssertionError(name)

    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    result = await nodes.handoff_node(state)
    assert result["stage"] == "HANDOFF_WRITING"
    assert result["handoff_location"]["urn"] == "urn:li:document:rh-exec001"
    name, args, mutation = calls[0]
    assert name == "save_document" and mutation is True
    assert args["document_type"] == "Decision"
    assert args["related_assets"] == [URN]
    assert "exec001" in args["content"]


@pytest.mark.asyncio
async def test_handoff_verification_requires_independent_document_reread(monkeypatch):
    state = state_for_write()
    state["handoff_location"] = {
        "kind": "datahub_document",
        "urn": "urn:li:document:rh-exec001",
    }

    async def fake_invoke(name, args, mutation=False):
        assert name == "get_entities"
        return {"urn": "urn:li:document:rh-exec001", "content": "# Reality Handoff: exec001"}

    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    result = await nodes.handoff_verify_node(state)
    assert result["stage"] == "HANDOFF_VERIFIED"
    assert result["handoff_recovery"]["source"] == "datahub_document"


@pytest.mark.asyncio
async def test_handoff_verification_fails_if_execution_missing(monkeypatch):
    state = state_for_write()
    state["handoff_location"] = {
        "kind": "datahub_document",
        "urn": "urn:li:document:rh-exec001",
    }

    async def fake_invoke(name, args, mutation=False):
        return {"urn": "urn:li:document:rh-exec001", "content": "different execution"}

    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    result = await nodes.handoff_verify_node(state)
    assert result["stage"] == "FAILED"
    assert result["status"] == "HANDOFF_VERIFY_FAILED"

@pytest.mark.asyncio
async def test_handoff_search_recovery_retries_boundedly(monkeypatch):
    state = state_for_write()
    state["handoff_location"] = {"kind": "datahub_document", "urn": None}
    searches = 0
    sleeps = []

    async def fake_refresh():
        return None

    async def fake_get_tools():
        return {"search_documents": object()}

    async def fake_invoke(name, args, mutation=False):
        nonlocal searches
        if name == "search_documents":
            searches += 1
            if searches < 3:
                return {"results": []}
            return {
                "searchResults": [
                    {"entity": {"urn": "urn:li:document:handoff-exec001", "title": "Reality Handoff exec001"}}
                ]
            }
        if name == "get_entities":
            return {
                "urn": "urn:li:document:handoff-exec001",
                "content": "# Reality Handoff: exec001\nverified body",
            }
        raise AssertionError(name)

    async def fake_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(nodes.mcp_runtime, "refresh_tools", fake_refresh)
    monkeypatch.setattr(nodes.mcp_runtime, "get_tools", fake_get_tools)
    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    monkeypatch.setattr(nodes.asyncio, "sleep", fake_sleep)

    result = await nodes.handoff_verify_node(state)
    assert result["stage"] == "HANDOFF_VERIFIED"
    assert result["handoff_recovery"] == {
        "source": "search_documents_then_get_entities",
        "urn": "urn:li:document:handoff-exec001",
        "attempts": 3,
    }
    assert searches == 3
    assert sleeps == [0.5, 1.0]


@pytest.mark.asyncio
async def test_handoff_search_recovery_fails_after_three_reads(monkeypatch):
    state = state_for_write()
    state["handoff_location"] = {"kind": "datahub_document", "urn": None}
    searches = 0

    async def fake_refresh():
        return None

    async def fake_get_tools():
        return {"search_documents": object()}

    async def fake_invoke(name, args, mutation=False):
        nonlocal searches
        searches += 1
        return {"results": []}

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(nodes.mcp_runtime, "refresh_tools", fake_refresh)
    monkeypatch.setattr(nodes.mcp_runtime, "get_tools", fake_get_tools)
    monkeypatch.setattr(nodes.mcp_runtime, "invoke", fake_invoke)
    monkeypatch.setattr(nodes.asyncio, "sleep", fake_sleep)

    result = await nodes.handoff_verify_node(state)
    assert result["stage"] == "FAILED"
    assert result["status"] == "HANDOFF_VERIFY_FAILED"
    assert searches == 3

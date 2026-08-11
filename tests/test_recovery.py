import pytest
from reality_handoff import recovery

EXEC = "exec001"
DOC = "urn:li:document:handoff-exec001"
TARGET = "urn:li:dataset:(urn:li:dataPlatform:snowflake,showcase.orders,PROD)"


@pytest.mark.asyncio
async def test_fresh_recovery_rereads_document_content(monkeypatch):
    calls = []

    async def fake_get_tools():
        return {"search_documents": object(), "get_entities": object()}

    async def fake_invoke(name, args, mutation=False):
        calls.append((name, args))
        if name == "search_documents":
            return {"searchResults": [{"entity": {"urn": DOC, "title": f"Reality Handoff {EXEC}"}}]}
        if name == "get_entities":
            return {"urn": DOC, "content": f"# Reality Handoff: {EXEC}\nDecision: verified"}
        raise AssertionError(name)

    monkeypatch.setattr(recovery.mcp_runtime, "get_tools", fake_get_tools)
    monkeypatch.setattr(recovery.mcp_runtime, "invoke", fake_invoke)
    result = await recovery.recover(EXEC)
    assert result["source"] == "datahub_document"
    assert result["document_urn"] == DOC
    assert result["attempts"] == 1
    assert calls[0][0] == "search_documents"
    assert calls[1] == ("get_entities", {"urns": [DOC], "urn": DOC})


@pytest.mark.asyncio
async def test_fresh_recovery_rejects_index_hit_without_matching_body(monkeypatch):
    async def fake_get_tools():
        return {"search_documents": object(), "get_entities": object()}

    async def fake_invoke(name, args, mutation=False):
        if name == "search_documents":
            return {"searchResults": [{"entity": {"urn": DOC, "title": f"Reality Handoff {EXEC}"}}]}
        if name == "get_entities":
            return {"urn": DOC, "content": "Different handoff body"}
        raise AssertionError(name)

    async def fake_sleep(seconds):
        return None

    monkeypatch.setattr(recovery.mcp_runtime, "get_tools", fake_get_tools)
    monkeypatch.setattr(recovery.mcp_runtime, "invoke", fake_invoke)
    monkeypatch.setattr(recovery.asyncio, "sleep", fake_sleep)
    result = await recovery.recover(EXEC)
    assert result == {"source": None, "execution_id": EXEC, "found": False}


@pytest.mark.asyncio
async def test_fresh_recovery_uses_verified_entity_fallback(monkeypatch):
    async def fake_get_tools():
        return {"get_entities": object()}

    async def fake_invoke(name, args, mutation=False):
        assert name == "get_entities"
        return {"urn": TARGET, "description": f"[Reality-Handoff-Record:{EXEC}]\nDecision: verified"}

    monkeypatch.setattr(recovery.mcp_runtime, "get_tools", fake_get_tools)
    monkeypatch.setattr(recovery.mcp_runtime, "invoke", fake_invoke)
    result = await recovery.recover(EXEC, TARGET)
    assert result["source"] == "entity_description"
    assert result["target_urn"] == TARGET

from __future__ import annotations

import pytest
from pydantic import create_model

from reality_handoff import mcp_runtime


class FakeTool:
    name = "update_description"
    args_schema = create_model(
        "UpdateDescriptionArgs",
        entity_urn=(str, ...),
        operation=(str, "append"),
        description=(str, ...),
    )

    def __init__(self):
        self.calls = []

    async def ainvoke(self, args):
        self.calls.append(args)
        return {"ok": True}


@pytest.mark.asyncio
async def test_invoke_binds_discovered_schema_and_enforces_scope(monkeypatch):
    tool = FakeTool()
    monkeypatch.setattr(mcp_runtime.settings, "allow_datahub_mutations", True)
    monkeypatch.setattr(mcp_runtime.settings, "demo_target_urn", "urn:li:dataset:test")

    async def fake_tools():
        return {"update_description": tool}

    monkeypatch.setattr(mcp_runtime, "get_tools", fake_tools)
    result = await mcp_runtime.invoke(
        "update_description",
        {
            "urn": "urn:li:dataset:test",
            "description": "bounded append",
            "mode": "append",
        },
        mutation=True,
    )
    assert result == {"ok": True}
    assert tool.calls == [
        {
            "entity_urn": "urn:li:dataset:test",
            "description": "bounded append",
            "operation": "append",
        }
    ]


@pytest.mark.asyncio
async def test_mutation_fails_closed_when_agent_gate_off(monkeypatch):
    monkeypatch.setattr(mcp_runtime.settings, "allow_datahub_mutations", False)
    with pytest.raises(PermissionError, match="ALLOW_DATAHUB_MUTATIONS=false"):
        await mcp_runtime.invoke(
            "update_description",
            {"urn": "urn:li:dataset:test", "description": "x", "mode": "append"},
            mutation=True,
        )


@pytest.mark.asyncio
async def test_mutation_scope_escape_is_blocked(monkeypatch):
    monkeypatch.setattr(mcp_runtime.settings, "allow_datahub_mutations", True)
    monkeypatch.setattr(mcp_runtime.settings, "demo_target_urn", "urn:li:dataset:allowed")
    with pytest.raises(PermissionError, match="outside DEMO_TARGET_URN"):
        await mcp_runtime.invoke(
            "update_description",
            {"urn": "urn:li:dataset:other", "description": "x", "mode": "append"},
            mutation=True,
        )


def test_stdio_connection_uses_python_module_not_uvx(monkeypatch):
    monkeypatch.setattr(mcp_runtime.settings, "datahub_mcp_url", "")
    monkeypatch.setattr(mcp_runtime.settings, "datahub_token", "")
    monkeypatch.setattr(mcp_runtime.settings, "datahub_gms_url", "http://localhost:8080")
    monkeypatch.setattr(mcp_runtime.settings, "datahub_gms_token", "secret-test-token")
    monkeypatch.setattr(mcp_runtime.settings, "datahub_server_mutations_enabled", True)
    monkeypatch.setattr(mcp_runtime.settings, "save_document_tool_enabled", True)
    connection = mcp_runtime._connection()
    assert connection["transport"] == "stdio"
    assert connection["command"]
    assert connection["args"] == ["-m", "mcp_server_datahub"]
    assert connection["env"]["TOOLS_IS_MUTATION_ENABLED"] == "true"
    assert connection["env"]["SAVE_DOCUMENT_TOOL_ENABLED"] == "true"

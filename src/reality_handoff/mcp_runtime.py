from __future__ import annotations
from typing import Any
from .config import settings
from .security import redact_obj
from .tool_binding import bind, schema_for

REQUIRED_READ = {"search", "get_entities", "list_schema_fields", "get_lineage"}
REQUIRED_ACTION = {"update_description"}
PREFERRED_HANDOFF = {"save_document"}
SAFE_WRITES = {"update_description", "save_document"}

_client = None
_tools: dict[str, Any] | None = None

async def get_tools() -> dict[str, Any]:
    global _client, _tools
    if _tools is not None:
        return _tools
    if not settings.datahub_mcp_url or not settings.datahub_token:
        raise RuntimeError("DATAHUB_MCP_URL and DATAHUB_TOKEN are required for live MCP mode")
    from langchain_mcp_adapters.client import MultiServerMCPClient
    _client = MultiServerMCPClient({
        "datahub": {
            "transport": "http",
            "url": settings.datahub_mcp_url,
            "headers": {"Authorization": f"Bearer {settings.datahub_token}"},
        }
    }, handle_tool_errors=False)
    loaded = await _client.get_tools()
    _tools = {t.name: t for t in loaded}
    return _tools



async def refresh_tools() -> dict[str, Any]:
    """Force tool rediscovery (useful after creating the first DataHub document)."""
    global _client, _tools
    _client = None
    _tools = None
    return await get_tools()


async def capability_manifest() -> dict[str, Any]:
    tools = await get_tools()
    names = sorted(tools)
    return {
        "status": "DATAHUB_MCP_READY" if REQUIRED_READ | REQUIRED_ACTION <= set(names) else "DATAHUB_MCP_INCOMPLETE",
        "tools": names,
        "required_read_available": sorted(REQUIRED_READ & set(names)),
        "missing_required_read": sorted(REQUIRED_READ - set(names)),
        "required_action_available": sorted(REQUIRED_ACTION & set(names)),
        "missing_required_action": sorted(REQUIRED_ACTION - set(names)),
        "preferred_handoff_available": sorted(PREFERRED_HANDOFF & set(names)),
        "tool_schemas": {n: schema_for(tools[n]) for n in names if n in REQUIRED_READ | REQUIRED_ACTION | PREFERRED_HANDOFF},
        "mutation_runtime_enabled": settings.allow_datahub_mutations,
    }

async def invoke(name: str, semantic_args: dict[str, Any], *, mutation: bool = False) -> Any:
    tools = await get_tools()
    if name not in tools:
        raise RuntimeError(f"DataHub MCP tool not available: {name}")
    if mutation:
        if name not in SAFE_WRITES:
            raise PermissionError(f"Mutation tool not allowlisted: {name}")
        if not settings.allow_datahub_mutations:
            raise PermissionError("ALLOW_DATAHUB_MUTATIONS=false")
    args = bind(tools[name], semantic_args)
    return redact_obj(await tools[name].ainvoke(args))

async def invoke_exact(name: str, args: dict[str, Any], *, mutation: bool = False) -> Any:
    tools = await get_tools()
    if name not in tools: raise RuntimeError(f"DataHub MCP tool not available: {name}")
    if mutation and (name not in SAFE_WRITES or not settings.allow_datahub_mutations):
        raise PermissionError("Mutation disabled or tool not allowlisted")
    return redact_obj(await tools[name].ainvoke(args))

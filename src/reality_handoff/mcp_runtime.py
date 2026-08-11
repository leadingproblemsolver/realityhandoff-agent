from __future__ import annotations

import os
import sys
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from langchain_mcp_adapters.client import MultiServerMCPClient

from .config import settings
from .tool_binding import bind

_TOOL_CACHE: dict[str, Any] | None = None
_CLIENT: "MultiServerMCPClient | None" = None


def _connection() -> dict[str, Any]:
    """Return exactly one DataHub MCP connection.

    Remote HTTP is optional. The canonical OSS path starts the pinned Python MCP server
    as a stdio subprocess in the same runtime as the agent, so deployment does not depend
    on `uvx`, Node, or a separate MCP daemon.
    """
    if settings.datahub_mcp_url and settings.datahub_token:
        return {
            "transport": "http",
            "url": settings.datahub_mcp_url,
            "headers": {"Authorization": f"Bearer {settings.datahub_token}"},
        }

    if not settings.datahub_gms_token:
        raise RuntimeError(
            "DATAHUB_GMS_TOKEN is required for self-hosted DataHub MCP mode"
        )

    env = {
        **os.environ,
        "DATAHUB_GMS_URL": settings.datahub_gms_url,
        "DATAHUB_GMS_TOKEN": settings.datahub_gms_token,
        "TOOLS_IS_MUTATION_ENABLED": (
            "true" if settings.datahub_server_mutations_enabled else "false"
        ),
        "SAVE_DOCUMENT_TOOL_ENABLED": (
            "true" if settings.save_document_tool_enabled else "false"
        ),
    }
    return {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "mcp_server_datahub"],
        "env": env,
    }


def _client() -> "MultiServerMCPClient":
    global _CLIENT
    if _CLIENT is None:
        from langchain_mcp_adapters.client import MultiServerMCPClient
        _CLIENT = MultiServerMCPClient({"datahub": _connection()})
    return _CLIENT


async def refresh_tools() -> None:
    global _TOOL_CACHE, _CLIENT
    _TOOL_CACHE = None
    _CLIENT = None


async def get_tools() -> dict[str, Any]:
    global _TOOL_CACHE
    if _TOOL_CACHE is None:
        tools = await _client().get_tools()
        _TOOL_CACHE = {
            getattr(tool, "name", str(tool)): tool
            for tool in tools
        }
    return dict(_TOOL_CACHE)


def _enforce_mutation_scope(name: str, semantic: dict[str, Any]) -> None:
    if not settings.allow_datahub_mutations:
        raise PermissionError(
            "DataHub mutation blocked: ALLOW_DATAHUB_MUTATIONS=false"
        )
    target = settings.demo_target_urn.strip()
    if not target:
        return
    if name == "update_description":
        requested = semantic.get("urn") or semantic.get("entity_urn")
        if requested != target:
            raise PermissionError("Mutation target is outside DEMO_TARGET_URN scope")
    if name == "save_document":
        assets = semantic.get("related_assets") or []
        if target not in assets:
            raise PermissionError(
                "Handoff document must remain related to DEMO_TARGET_URN"
            )


async def invoke(
    name: str,
    semantic: dict[str, Any],
    *,
    mutation: bool = False,
) -> Any:
    if mutation:
        _enforce_mutation_scope(name, semantic)
    tools = await get_tools()
    tool = tools.get(name)
    if tool is None:
        raise RuntimeError(f"DataHub MCP tool unavailable: {name}")
    args = bind(tool, semantic)
    return await tool.ainvoke(args)


async def capability_manifest() -> dict[str, Any]:
    tools = await get_tools()
    names = sorted(tools)
    found = set(names)
    required_read = {"search", "get_entities", "list_schema_fields", "get_lineage"}
    required_action = {"update_description"}
    preferred = {"save_document", "search_documents"}

    mode = "remote_http" if settings.datahub_mcp_url and settings.datahub_token else "stdio"
    return {
        "mode": mode,
        "transport": "http" if mode == "remote_http" else "stdio",
        "datahub_endpoint": settings.datahub_mcp_url or settings.datahub_gms_url,
        "tools": names,
        "missing_required_read": sorted(required_read - found),
        "missing_required_action": sorted(required_action - found),
        "missing_preferred": sorted(preferred - found),
        "read_ready": required_read.issubset(found),
        "action_ready": required_action.issubset(found),
        "server_mutation_tools_enabled": settings.datahub_server_mutations_enabled,
        "agent_mutations_enabled": settings.allow_datahub_mutations,
        "human_approval_required": settings.require_human_approval,
    }

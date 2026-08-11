import os
from langchain_mcp_adapters.client import MultiServerMCPClient


def _client():
    gms_url = os.getenv("DATAHUB_GMS_URL", "http://localhost:8080")
    gms_token = os.getenv("DATAHUB_GMS_TOKEN")

    if not gms_token:
        raise RuntimeError("DATAHUB_GMS_TOKEN is required")

    return MultiServerMCPClient(
        {
            "datahub": {
                "transport": "stdio",
                "command": "uvx",
                "args": ["mcp-server-datahub"],
                "env": {
                    **os.environ,
                    "DATAHUB_GMS_URL": gms_url,
                    "DATAHUB_GMS_TOKEN": gms_token,
                },
            }
        }
    )


async def get_tools():
    return await _client().get_tools()


async def capability_manifest():
    tools = await get_tools()
    names = sorted(getattr(t, "name", str(t)) for t in tools)

    required = {
        "search",
        "get_entities",
        "list_schema_fields",
        "get_lineage",
    }

    found = set(names)

    return {
        "transport": "stdio",
        "tools": names,
        "missing_required_tools": sorted(required - found),
        "ready": required.issubset(found),
    }
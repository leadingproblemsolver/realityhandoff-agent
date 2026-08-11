"""P1: prove read/context against the configured DataHub instance; never mutates."""
from __future__ import annotations

import asyncio
import json
import sys

from reality_handoff import mcp_runtime
from reality_handoff.config import settings
from reality_handoff.evidence import extract_urns
from reality_handoff.models import stable_text


async def main() -> int:
    manifest = await mcp_runtime.capability_manifest()
    print(json.dumps({"P0": manifest}, indent=2, default=str))
    if manifest["missing_required_read"]:
        return 2

    target = settings.demo_target_urn.strip()
    search = await mcp_runtime.invoke("search", {"query": "customer orders"})
    urns = [u for u in extract_urns(search) if u.startswith("urn:li:dataset:")]
    if not target:
        if not urns:
            print("P1 FAILED: no dataset URN resolved from search", file=sys.stderr)
            return 3
        target = urns[0]

    reads = {
        "get_entities": await mcp_runtime.invoke(
            "get_entities", {"urns": [target], "urn": target}
        ),
        "list_schema_fields": await mcp_runtime.invoke("list_schema_fields", {"urn": target}),
        "lineage_upstream": await mcp_runtime.invoke(
            "get_lineage", {"urn": target, "upstream": True}
        ),
        "lineage_downstream": await mcp_runtime.invoke(
            "get_lineage", {"urn": target, "upstream": False}
        ),
    }
    entity_text = stable_text(reads["get_entities"])
    exists = target in entity_text
    payload = {
        "P1": {
            "target_urn": target,
            "configured_target": bool(settings.demo_target_urn),
            "target_proven": exists,
            "reads": reads,
        }
    }
    print(json.dumps(payload, indent=2, default=str))
    return 0 if exists and all(stable_text(v) for v in reads.values()) else 4


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

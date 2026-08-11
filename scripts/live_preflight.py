"""P0: discover the live DataHub MCP tool surface without mutating anything."""
from __future__ import annotations

import asyncio
import json

from reality_handoff.mcp_runtime import capability_manifest


async def main() -> int:
    manifest = await capability_manifest()
    print(json.dumps(manifest, indent=2, default=str))
    return 0 if manifest["read_ready"] else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

"""One-command non-destructive preflight before P2/P3/P4 and recording."""
from __future__ import annotations

import asyncio
import subprocess
import sys

from reality_handoff.config import settings


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


async def live() -> None:
    from reality_handoff.mcp_runtime import capability_manifest

    manifest = await capability_manifest()
    if not manifest["read_ready"]:
        raise SystemExit(f"MCP read tools missing: {manifest['missing_required_read']}")
    if not settings.demo_target_urn:
        raise SystemExit("DEMO_TARGET_URN is required before final live acceptance")
    print("PASS: MCP read surface and target configuration")


def main() -> int:
    run([sys.executable, "-m", "pytest", "-q"])
    run([sys.executable, "scripts/secret_scan.py"])
    run([sys.executable, "-m", "compileall", "-q", "src", "tests", "scripts"])
    asyncio.run(live())
    print("\nPRECHECK PASS")
    print("Still manual/live: P2 refusal → P3 approve+verify → P4 fresh recovery → UI smoke.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

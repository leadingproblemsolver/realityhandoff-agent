import asyncio, json
from reality_handoff.mcp_runtime import capability_manifest
async def main(): print(json.dumps(await capability_manifest(),indent=2,default=str))
asyncio.run(main())

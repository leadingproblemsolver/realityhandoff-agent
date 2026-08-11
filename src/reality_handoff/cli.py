from __future__ import annotations
import argparse, asyncio, json, uuid

async def _preflight():
    from .mcp_runtime import capability_manifest
    print(json.dumps(await capability_manifest(), indent=2, default=str))

async def _recover(args):
    from .recovery import recover
    print(json.dumps(await recover(args.execution_id,args.target_urn), indent=2, default=str))

def main():
    p=argparse.ArgumentParser(prog="reality-handoff")
    sub=p.add_subparsers(dest="cmd",required=True)
    sub.add_parser("preflight")
    r=sub.add_parser("recover"); r.add_argument("execution_id"); r.add_argument("--target-urn")
    args=p.parse_args()
    asyncio.run(_preflight() if args.cmd=="preflight" else _recover(args))

if __name__=="__main__": main()

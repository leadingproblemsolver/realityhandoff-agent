from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from .replay import run_replay
from .security import redact

app = FastAPI(title="Reality Handoff Agent", version="0.3.0")


class ReplayBody(BaseModel):
    task: str = Field(min_length=1, max_length=1000)
    ambiguous: bool = False


@app.get("/demo", response_class=HTMLResponse)
async def demo():
    return HTMLResponse(r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reality Handoff Agent</title><style>
body{font-family:Inter,ui-sans-serif,system-ui;background:#0b0d12;color:#f4f6fb;margin:0}.wrap{max-width:1020px;margin:0 auto;padding:44px 22px}.eyebrow{letter-spacing:.12em;text-transform:uppercase;color:#9ba7bd;font-size:12px}.hero{font-size:50px;line-height:1.03;margin:12px 0 16px}.sub{color:#bbc3d3;max-width:820px;font-size:18px;line-height:1.6}.card{background:#121621;border:1px solid #283044;border-radius:16px;padding:22px;margin-top:22px}.flow{display:grid;grid-template-columns:repeat(5,1fr);gap:9px}.step{padding:13px;background:#171c29;border-radius:10px;border:1px solid #2d374f;font-size:13px}textarea{width:100%;min-height:100px;background:#0d1119;color:#fff;border:1px solid #34405c;border-radius:10px;padding:12px;box-sizing:border-box}button{margin:10px 8px 0 0;padding:11px 16px;border:0;border-radius:9px;font-weight:700;cursor:pointer}pre{white-space:pre-wrap;word-break:break-word;background:#090c12;padding:14px;border-radius:10px;max-height:400px;overflow:auto}.warn{color:#f5c76b}.ok{color:#8bd49c}.muted{color:#9ba7bd}a{color:#9fc2ff}@media(max-width:760px){.hero{font-size:36px}.flow{grid-template-columns:1fr 1fr}}</style></head>
<body><div class="wrap"><div class="eyebrow">DataHub Agent Hackathon · Agents That Do Real Work</div><h1 class="hero">Reality Handoff Agent</h1><p class="sub">Reads organizational context through DataHub MCP, compiles proof-carrying reality, blocks unsafe actions, performs one human-approved DataHub metadata mutation, verifies it by MCP re-read, then writes a durable handoff for the next agent.</p>
<div class="card"><div class="flow"><div class="step">1 · MCP read</div><div class="step">2 · Reality</div><div class="step">3 · Gate + contract</div><div class="step">4 · Act + verify</div><div class="step">5 · DataHub handoff</div></div></div>
<div class="card"><h3>Safe interactive evaluator</h3><p class="muted">This replay runs the same deterministic gate/contract/verification logic against a transparent in-memory showcase fixture. It is <b>not</b> presented as live DataHub evidence.</p><textarea id="task">Find the canonical customer orders asset. Inspect its context and lineage. If there is a safe documentation gap, append an evidence-backed continuity note, verify it landed, and leave a handoff for the next agent.</textarea><br><button onclick="runReplay(false)">Run positive replay</button><button onclick="runReplay(true)">Run ambiguity control</button><pre id="out">Ready.</pre></div>
<div class="card"><h3>Live MCP proof</h3><p class="warn">Live mutation requires server-side DATAHUB_MCP_URL + DATAHUB_TOKEN, ALLOW_DATAHUB_MUTATIONS=true, and the LangGraph human-approval interrupt. Tokens never enter this page.</p><button onclick="capabilities()">Check DataHub MCP capabilities</button><pre id="cap">Not checked.</pre><p>For the full stateful run, open LangSmith Studio / Agent Server graph <code>reality_handoff</code>. The mandatory live proof is P0 MCP → P1 Read → P2 Decide → P3 Act → P4 Inherit.</p><p><a href="/docs">Open API docs</a></p></div></div>
<script>
async function runReplay(ambiguous){const task=document.getElementById('task').value;const o=document.getElementById('out');o.textContent='Running…';try{const r=await fetch('/api/replay',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({task,ambiguous})});o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
async function capabilities(){const o=document.getElementById('cap');o.textContent='Checking…';try{const r=await fetch('/api/capabilities');o.textContent=JSON.stringify(await r.json(),null,2)}catch(e){o.textContent=String(e)}}
</script></body></html>''')


@app.post("/api/replay")
async def replay(body: ReplayBody):
    return run_replay(task=body.task, ambiguous=body.ambiguous)


@app.get("/api/capabilities")
async def capabilities():
    try:
        from .mcp_runtime import capability_manifest

        return await capability_manifest()
    except Exception as exc:
        raise HTTPException(503, redact(str(exc)))

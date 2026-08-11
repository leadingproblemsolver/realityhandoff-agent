from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .config import settings
from .replay import run_replay
from .security import redact


def _runtime():
    from . import web_runtime
    return web_runtime

VERSION = "0.5.0"
STATIC_DIR = Path(__file__).with_name("static")

app = FastAPI(title="Reality Handoff Agent", version=VERSION)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ReplayBody(BaseModel):
    task: str = Field(min_length=1, max_length=1600)
    ambiguous: bool = False


class RunBody(BaseModel):
    task: str = Field(min_length=1, max_length=1600)


class RecoveryBody(BaseModel):
    execution_id: str = Field(min_length=1, max_length=128)
    target_urn: str | None = Field(default=None, max_length=1400)


@app.get("/", include_in_schema=False)
@app.get("/demo", include_in_schema=False)
async def demo():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/health")
async def health():
    return {
        "ok": True,
        "version": VERSION,
        "live_configured": bool(
            (settings.datahub_gms_token or (settings.datahub_mcp_url and settings.datahub_token))
            and settings.demo_target_urn
        ),
        "datahub_mode": "remote_http"
        if settings.datahub_mcp_url and settings.datahub_token
        else "self_hosted_stdio",
        "target_scoped": bool(settings.demo_target_urn),
        "server_mutation_tools_enabled": settings.datahub_server_mutations_enabled,
        "agent_mutations_enabled": settings.allow_datahub_mutations,
        "human_approval_required": settings.require_human_approval,
    }


@app.post("/api/replay")
async def replay(body: ReplayBody):
    return run_replay(task=body.task, ambiguous=body.ambiguous)


@app.get("/api/capabilities")
async def capabilities():
    try:
        from .mcp_runtime import capability_manifest

        return await capability_manifest()
    except Exception as exc:
        raise HTTPException(503, redact(str(exc))) from exc


@app.post("/api/runs", status_code=201)
async def start_run(body: RunBody):
    try:
        return await _runtime().start_run(body.task)
    except Exception as exc:
        raise HTTPException(503, redact(str(exc))) from exc


@app.get("/api/runs/{execution_id}")
async def get_run(execution_id: str):
    result = await _runtime().get_run(execution_id)
    if not result.get("found"):
        raise HTTPException(404, "Run not found")
    return result


@app.post("/api/runs/{execution_id}/approve")
async def approve_run(execution_id: str):
    try:
        result = await _runtime().decide_run(execution_id, True)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, redact(str(exc))) from exc
    if not result.get("found"):
        raise HTTPException(404, "Run not found")
    return result


@app.post("/api/runs/{execution_id}/reject")
async def reject_run(execution_id: str):
    try:
        result = await _runtime().decide_run(execution_id, False)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc
    except Exception as exc:
        raise HTTPException(503, redact(str(exc))) from exc
    if not result.get("found"):
        raise HTTPException(404, "Run not found")
    return result


@app.post("/api/recovery")
async def recovery(body: RecoveryBody):
    try:
        result = await _runtime().recover_handoff(body.execution_id, body.target_urn)
    except Exception as exc:
        raise HTTPException(503, redact(str(exc))) from exc
    if result.get("found") is False or result.get("source") is None:
        raise HTTPException(404, "Durable handoff not found")
    return result

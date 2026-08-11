# Reality Handoff Agent

**Proof-carrying DataHub actions that survive the agent session.**

Reality Handoff is a LangGraph + DataHub MCP agent for **Agents That Do Real Work**. It turns DataHub context into a bounded execution protocol:

`DataHub evidence → reality → deterministic gate → execution contract → human approval → one bounded write → independent re-read → durable handoff → fresh recovery`

The repository is intentionally one deployable product: the LangGraph backend, DataHub MCP runtime, FastAPI application API, and judge-facing frontend ship together.

## What the judge can do

Open `/` or `/demo` and use either:

- **Fixture proof** — deterministic, credential-free positive/refusal/handoff demonstration, explicitly labeled as non-live evidence.
- **Live DataHub** — real MCP reads, structured evidence/reality, explicit execution contract, Approve/Reject, deterministic post-write verification, and fresh DataHub-backed recovery.

The browser never receives DataHub, OpenAI, or LangSmith secrets.

## Core safety invariants

- DataHub metadata is evidence, never executable instruction.
- Facts must resolve to evidence IDs.
- Ambiguous business semantics such as `revenue` block execution unless definition-like DataHub evidence exists.
- The model cannot authorize writes or declare verification success.
- A Pydantic `ExecutionContract` fixes target, allowed tools, expected mutation, tests, and stop conditions.
- LangGraph `interrupt()` requires human approval before the write path.
- Agent-side `ALLOW_DATAHUB_MUTATIONS` is independent from MCP-server mutation-tool exposure.
- `DEMO_TARGET_URN` can hard-scope the public demo to exactly one asset.
- `update_description` is append-only.
- Success requires a fresh `get_entities` re-read containing the expected marker.
- Continuity is written with `save_document` when available, otherwise by a disclosed append-only record on the already-approved target.
- Fresh recovery reads DataHub-backed state, never prior browser/chat memory.

## Architecture

```text
Browser
  │
  ├─ fixture proof ───────────────→ deterministic replay
  │
  └─ live task
       ↓
FastAPI product API
       ↓
LangGraph + checkpointed approval interrupt
       ↓
DataHub MCP runtime
       ↓
DataHub Core / Cloud
       ↓
read → gate → contract → approve → append → re-read → handoff → recover
```

### Product API

```text
GET  /api/health
GET  /api/capabilities
POST /api/replay
POST /api/runs
GET  /api/runs/{execution_id}
POST /api/runs/{execution_id}/approve
POST /api/runs/{execution_id}/reject
POST /api/recovery
```

The frontend renders structured backend state. It does not infer authorization or workflow state from LLM prose.

## Install

Python **3.11+** is required because the pinned official DataHub MCP server requires it.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
cp .env.example .env
pytest -q
```

The repo pins `mcp-server-datahub==0.6.0` and launches it as:

```text
python -m mcp_server_datahub
```

No Node/npm or `uvx` is required by the deployed application runtime.

## Configure DataHub

Canonical self-hosted path:

```env
DATAHUB_GMS_URL=http://localhost:8080
DATAHUB_GMS_TOKEN=<fresh PAT from this DataHub instance>

# Tool exposure at the MCP-server boundary.
DATAHUB_SERVER_MUTATIONS_ENABLED=true
SAVE_DOCUMENT_TOOL_ENABLED=true

# Independent authorization at the agent boundary.
ALLOW_DATAHUB_MUTATIONS=false
REQUIRE_HUMAN_APPROVAL=true
DEMO_TARGET_URN=<exact verified showcase dataset URN>

OPENAI_API_KEY=<optional for deterministic replay; recommended live>
OPENAI_MODEL=gpt-4.1-mini
```

Optional managed DataHub MCP:

```env
DATAHUB_MCP_URL=https://<tenant>.acryl.io/integrations/ai/mcp/
DATAHUB_TOKEN=<PAT>
```

If both managed MCP values are present, the runtime uses remote HTTP MCP; otherwise it uses the self-hosted stdio path.

## Acceptance sequence

### P0 — MCP capability discovery

```bash
python scripts/live_preflight.py | tee artifacts/live/p0-preflight.json
```

Read path requires:

- `search`
- `get_entities`
- `list_schema_fields`
- `get_lineage`

A READY mutation path additionally requires `update_description`. `save_document` is preferred but has a disclosed bounded fallback.

### P1 — exact target read

Set `DEMO_TARGET_URN`, then:

```bash
python scripts/live_read_smoke.py | tee artifacts/live/p1-read.json
```

Pass only if the exact configured URN is independently returned by `get_entities` and schema + both lineage directions are readable.

### P2 — refusal control

Keep:

```env
ALLOW_DATAHUB_MUTATIONS=false
```

Run:

> Fix the revenue definition and document it on the configured asset.

Pass: `NEEDS_HUMAN` / zero mutation unless DataHub actually supplies an authoritative definition.

### P3 — one approved bounded action

Only after P0/P1:

```env
ALLOW_DATAHUB_MUTATIONS=true
```

```bash
python scripts/run_live_graph.py \
  "Inspect the configured orders asset and its lineage. Append an evidence-backed Reality Handoff continuity note, verify it, and leave a durable handoff for the next agent."
```

Approve only if target, tool, append operation, and evidence match the displayed contract.

### P4 — fresh recovery

From a new process:

```bash
reality-handoff recover <execution_id> --target-urn '<DEMO_TARGET_URN>'
```

Pass only when the prior handoff is recovered from DataHub itself.

## Judge-facing app

Local / Codespace:

```bash
langgraph dev --no-browser
```

Open:

- Product: `http://localhost:2024/`
- API docs: `http://localhost:2024/docs`

The UI exposes only the proof sequence that matters:

**Task → Evidence → Reality/Gate → Execution Contract → Approve/Reject → Verification → Fresh Agent.**

No second frontend framework, database, auth layer, or builder is required.

## Deployment

`langgraph.json` declares:

- graph: `reality_handoff`
- custom FastAPI application: `src/reality_handoff/webapp.py:app`
- environment: `.env`

For a hosted LangSmith/LangGraph deployment, push the repository, create the deployment from GitHub, set secrets in the deployment environment, and keep `.env` out of Git.

See `docs/DEPLOY_LANGSMITH.md` and `docs/FRONTEND_ACCEPTANCE.md`.

## Verification status

Finalized repository validation in the packaging environment:

- **55/55 deterministic/unit/API/frontend-contract tests passed**;
- Python compile check passed;
- JavaScript syntax check passed;
- repository secret scan passed after removing the uploaded live `.env`;
- fixture positive/refusal/tamper controls are covered by tests.

The packaging sandbox cannot download the LangGraph/DataHub MCP runtime dependencies, so **live DataHub P0–P4 remains the final external acceptance gate**. Do not claim live end-to-end success until those outputs are captured from the actual Codespace/DataHub runtime.

## Submission

- `SUBMISSION.md` — Devpost-ready copy.
- `docs/DEMO_SCRIPT.md` — sub-3-minute recording flow.
- `docs/LIVE_ACCEPTANCE.md` — P0–P4 pass/fail gates.
- `docs/FRONTEND_ACCEPTANCE.md` — judge-surface T01–T15 closure.
- `examples/` — deterministic examples.
- `artifacts/offline/` — sanitized offline proof.

Apache-2.0 licensed.

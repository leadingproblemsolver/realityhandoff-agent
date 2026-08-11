# Deploy on LangSmith / LangGraph Agent Server

## Install and validate

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
pytest -q
python scripts/secret_scan.py
```

## Configure DataHub MCP

For direct DataHub Cloud PAT authentication:

```text
DATAHUB_MCP_URL=https://<tenant>.acryl.io/integrations/ai/mcp/
DATAHUB_TOKEN=<DataHub-issued PAT>
```

For an unattended/public deployment, prefer a least-privilege DataHub service-account token and scope its Default View to the demo assets where available.

If you registered a `datahub-mcp` custom integration in LangSmith/Fleet, keep it for Fleet/managed-agent testing. This repository is a custom LangGraph application and intentionally creates its own `MultiServerMCPClient`; therefore configure the MCP URL/token in the graph deployment environment as well.

## Run read-only first

```bash
python scripts/live_preflight.py
python scripts/live_read_smoke.py
```

Keep:

```text
ALLOW_DATAHUB_MUTATIONS=false
REQUIRE_HUMAN_APPROVAL=true
```

Select one safe DataHub showcase asset and set `DEMO_TARGET_URN` to its exact URN.

## Local Studio

```bash
langgraph dev --no-browser
```

- Agent Server: `http://localhost:2024`
- Judge/replay page: `http://localhost:2024/demo`
- API docs: `http://localhost:2024/docs`
- Graph: `reality_handoff`

LangGraph's approval node uses `interrupt()`, so use a stable thread ID. Resume the same thread with a `Command(resume=true)` through Studio/API, or use `scripts/run_live_graph.py` for a terminal-driven approval flow.

## Hosted deployment

Push the repo to a public GitHub repository and create a LangSmith Deployment from it. `langgraph.json` declares:

- dependency root `.`;
- graph entrypoint `src/reality_handoff/graph.py:graph`;
- custom FastAPI app `src/reality_handoff/webapp.py:app`.

Set environment secrets in the deployment UI; do not commit `.env`.

## Mutation enablement

Only after P0/P1 and exact target scoping:

```text
ALLOW_DATAHUB_MUTATIONS=true
```

DataHub itself must also expose/permit mutation tools. If preflight does not list `update_description`, do not bypass the gate; fix the DataHub MCP configuration/permissions.

Follow `docs/LIVE_ACCEPTANCE.md` before recording the final demo.

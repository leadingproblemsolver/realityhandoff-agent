# Deploy the single-repo product

The backend and judge-facing frontend deploy together. Do not create a separate frontend project.

## 1. Install / validate in Codespace

```bash
pip install -e '.[dev]'
cp .env.example .env
pytest -q
python scripts/secret_scan.py
```

## 2. Configure server-side environment

Self-hosted DataHub Core:

```env
DATAHUB_GMS_URL=http://localhost:8080
DATAHUB_GMS_TOKEN=<fresh PAT>
DATAHUB_SERVER_MUTATIONS_ENABLED=true
SAVE_DOCUMENT_TOOL_ENABLED=true
DEMO_TARGET_URN=<exact verified dataset URN>
ALLOW_DATAHUB_MUTATIONS=false
REQUIRE_HUMAN_APPROVAL=true
OPENAI_API_KEY=<optional/recommended live>
```

Do not put any of these secrets into browser-side code or Git.

## 3. Read-only proof first

```bash
python scripts/live_preflight.py
python scripts/live_read_smoke.py
```

P0/P1 must pass before mutation enablement.

## 4. Local / Codespace product

```bash
langgraph dev --no-browser
```

Open:

- `/` — judge-facing product
- `/docs` — FastAPI contract

## 5. Hosted LangGraph deployment

Push the finalized repo to GitHub and create a LangGraph/LangSmith deployment from it. `langgraph.json` already points to:

```text
graph: ./src/reality_handoff/graph.py:graph
http:  ./src/reality_handoff/webapp.py:app
```

Set deployment environment variables server-side.

## 6. Mutation proof

After P0/P1 and exact target scoping:

```env
ALLOW_DATAHUB_MUTATIONS=true
```

Keep `REQUIRE_HUMAN_APPROVAL=true`.

Run P2/P3/P4 from `docs/LIVE_ACCEPTANCE.md`, then execute the production UI acceptance matrix in `docs/FRONTEND_ACCEPTANCE.md`.

## Stop condition

Once refusal, one approved verified write, and fresh DataHub-backed recovery pass through the product surface, freeze engineering and record the demo.

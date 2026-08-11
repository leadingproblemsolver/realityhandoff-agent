# Reality Handoff Agent

**Proof-carrying DataHub actions that survive the agent session.**

Reality Handoff is a native **LangGraph + DataHub MCP** agent for DataHub's **Agents That Do Real Work** challenge. It reads live organizational/data context through MCP, compiles that evidence into an explicit reality model, refuses unsafe work when semantics are unresolved, executes one human-approved metadata action, verifies the change by independently re-reading DataHub, and writes a durable handoff so the next agent can continue without conversation history.

> **Core loop:** `DataHub MCP → evidence → reality → deterministic gate → execution contract → human approval → bounded action → re-read verification → DataHub handoff → independent recovery`

## Why it exists

DataHub already supplies rich context: search, schemas, lineage, ownership, documentation, quality signals, queries, and context documents. Reality Handoff does **not** rebuild those features. It supplies the missing execution protocol around them:

- factual claims must resolve to retrieved evidence IDs;
- retrieved metadata is treated as untrusted evidence, never executable instruction;
- ambiguous business semantics such as `revenue` produce `NEEDS_HUMAN` unless definition-like DataHub context is present;
- a Pydantic `ExecutionContract` fixes the target, allowed tools, expected mutation, stop conditions, and verification tests;
- LangGraph `interrupt()` makes the real mutation explicitly human-approved;
- only two writes are allowlisted: `update_description` and the durable handoff sink `save_document`;
- success requires an independent DataHub re-read; an LLM cannot declare success;
- the handoff is independently recovered from DataHub before the graph can claim `HANDOFF_VERIFIED`.

## Architecture

```text
User task
  ↓
LangGraph intake
  ↓
DataHub MCP capability preflight
  ↓
search + get_entities + schema + upstream/downstream lineage
  ↓
EvidenceRef[] (hashes + provenance)
  ↓
RealitySnapshot (facts / inferences / unknowns / contradictions)
  ↓
Deterministic Constraint Gate
  ├─ NEEDS_CONTEXT / NEEDS_HUMAN / BLOCKED → stop without mutation
  └─ READY
       ↓
ExecutionContract
       ↓
Bounded action plan
       ↓
Human approval interrupt
       ↓
MCP update_description (append-only)
       ↓
MCP get_entities re-read → deterministic verification
       ↓
MCP save_document (Decision) or approved fallback
       ↓
Independent DataHub handoff re-read
       ↓
HANDOFF_VERIFIED → COMPLETE
```

## Fastest judge path: no credentials

The repository includes an interactable, explicitly-labeled replay evaluator that exercises the deterministic Reality/Gate/Contract/Verification/Handoff semantics without pretending to be live DataHub.

```bash
python -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
pytest -q
python scripts/run_replay.py
langgraph dev --no-browser
```

Open `http://localhost:2024/demo`.

## Live DataHub path

### 1. Configure server-side secrets

```bash
cp .env.example .env
```

```text
DATAHUB_MCP_URL=https://<tenant>.acryl.io/integrations/ai/mcp/
DATAHUB_TOKEN=<DataHub-issued PAT or service-account token>
OPENAI_API_KEY=<optional-but-recommended-for-semantic-compilation>
ALLOW_DATAHUB_MUTATIONS=false
REQUIRE_HUMAN_APPROVAL=true
DEMO_TARGET_URN=
```

The token is sent only from the server runtime in the `Authorization: Bearer ...` header. It never enters graph state or `/demo` browser requests.

### 2. P0 — discover real MCP capabilities

```bash
reality-handoff preflight
# or
python scripts/live_preflight.py
```

Required read tools: `search`, `get_entities`, `list_schema_fields`, `get_lineage`.
Required action tool: `update_description`.
Preferred durable handoff tool: `save_document`.

**Stop** if the required tools are missing.

### 3. P1 — prove read/context before writes

```bash
python scripts/live_read_smoke.py
```

Inspect the returned showcase-ecommerce dataset(s). Pick exactly one safe demo asset and set its exact URN as `DEMO_TARGET_URN`.

### 4. P2 — negative control

Run:

> Fix the revenue definition and document it on the canonical asset.

Expected: `NEEDS_HUMAN`, zero mutation when authoritative revenue semantics are not established by retrieved DataHub evidence.

### 5. P3/P4 — bounded live work

Only after P0/P1 and exact target scoping:

```text
ALLOW_DATAHUB_MUTATIONS=true
DEMO_TARGET_URN=<exact verified showcase asset URN>
```

Then:

```bash
python scripts/run_live_graph.py \
  "Inspect the configured orders asset and its lineage. Append an evidence-backed Reality Handoff continuity note, verify it, and leave a durable handoff for the next agent."
```

The script pauses at the LangGraph approval interrupt. Review the exact target, evidence, contract, and action before typing `y`.

Finally, prove fresh-process inheritance:

```bash
reality-handoff recover <execution_id> --target-urn '<DEMO_TARGET_URN>'
```

## LangSmith deployment

`langgraph.json` declares both the `reality_handoff` graph and the custom FastAPI `/demo` route. Deploy the repository as a LangGraph application or run `langgraph dev` locally. See `docs/DEPLOY_LANGSMITH.md`.

If you already registered `datahub-mcp` inside LangSmith/Fleet, that is useful for Fleet/managed-agent tool usage, but **this custom graph deliberately connects to DataHub MCP itself through `langchain-mcp-adapters`**. Configure `DATAHUB_MCP_URL` and `DATAHUB_TOKEN` in the deployment environment so the code has an explicit, reproducible connection path.

## What changed from the n8n prototype

The n8n prototype was treated as an executable specification. We retained its strongest invariants—evidence IDs, fact/inference/unknown separation, deterministic gating, explicit contracts, human approval, verification, failure boundaries, and continuity—and retired its transport-specific architecture:

- GraphQL-first retrieval → **DataHub MCP**;
- n8n sub-workflows → **LangGraph state machine**;
- SQL generation → **bounded DataHub metadata action**;
- JS SQL structural checks → **actual post-action MCP re-read**;
- dry-run writeback → **real approved MCP mutation**;
- n8n Data Table continuity → **DataHub-native durable handoff**.

See `docs/N8N_TO_LANGGRAPH.md`.

## Verification status

Offline deterministic suite in this package: **44 tests passing** at packaging time, plus secret scan, compile check, positive replay, ambiguity control, and tamper control. See `docs/TEST_RESULTS.md` and `artifacts/offline/`.

### Claim boundary

The packaged environment used to build this ZIP did **not** contain the LangGraph/LangChain MCP runtime packages and did not have access to your live DataHub tenant credentials. Therefore the repository's deterministic core and judge-facing replay are executed and tested here, while **live DataHub P0–P4 remains an explicit acceptance gate to run in your LangSmith/local environment**. Do not claim live end-to-end success until those artifacts are captured.

## Submission readiness

- Apache 2.0 license: included.
- Public-repo-ready source: included.
- `examples/`: included.
- judge-facing `/demo`: included.
- deterministic tests + replay: included.
- under-3-minute demo script: included.
- live P0–P4 capture template: included.
- submission text: `SUBMISSION.md`.

## Security defaults

- mutations OFF by default;
- human approval ON by default;
- exact demo target scoping supported;
- PAT never accepted from browser input;
- MCP tool schemas discovered at runtime and required arguments fail closed;
- model output is not an authorization surface;
- outbound model-authored text is redacted before mutation;
- prompt-like instructions embedded in DataHub metadata cannot expand the write allowlist;
- handoff write success is independently re-read before verification.

See `docs/THREAT_MODEL.md` and `docs/FINAL_AUDIT.md`.

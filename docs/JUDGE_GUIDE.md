# Judge guide — Reality Handoff

## 30-second thesis

Reality Handoff turns DataHub metadata into a proof-carrying execution protocol:

`evidence → bounded decision → explicit contract → human approval → one append-only action → independent verification → durable handoff → fresh recovery`

The central design choice is separation of responsibilities. The model may interpret evidence and draft bounded text, but deterministic Python owns authorization, target scoping, state transitions, mutation allowlisting, acceptance tests, and verification.

## What to judge

### 1. Does the agent do real work?

Yes, on the live path it reads a real DataHub asset, schema, and two-direction lineage through MCP; creates a bounded execution contract; performs one approved `update_description`; re-reads the asset to verify the exact marker; persists a handoff; and requires a fresh process to recover that handoff from DataHub-backed state.

### 2. Is the work bounded and safe?

The write surface is intentionally narrow:

- exact target can be hard-scoped by `DEMO_TARGET_URN`;
- mutation exposure at the DataHub MCP server and mutation authorization inside the agent are separate controls;
- the contract fixes the target, tool, append operation, evidence, acceptance tests, and stop conditions before approval;
- only append-only `update_description` is authorized for the showcase action;
- destructive tools are not part of the contract;
- ambiguous semantics stop as `NEEDS_HUMAN` rather than being guessed.

### 3. Is success independently verifiable?

Yes. The model cannot declare a successful mutation. After execution, deterministic code performs a fresh `get_entities` read and checks both target identity and the expected idempotency marker. Handoff persistence is also independently re-read before continuity is claimed.

### 4. Does state survive the session?

Yes, when P4 passes. The handoff is persisted through DataHub-backed state (`save_document` when available, otherwise the predeclared bounded fallback) and a new process must recover it without prior graph, browser, or chat memory.

## Algorithmic design

The workflow is a fail-closed state machine rather than a free-form agent loop:

1. **Preflight** — discover the actual MCP tool surface. Missing required reads prevent context construction; missing mutation capability prevents a positive write contract.
2. **Context acquisition** — fetch the exact target entity, schema fields, upstream lineage, and downstream lineage.
3. **Evidence normalization** — each successful MCP result becomes an `EvidenceRef` with tool, arguments, target, timestamp, digest, and bounded excerpt.
4. **Reality compilation** — separate facts, inferences, unknowns, and contradictions. Facts must resolve to evidence IDs from the current execution.
5. **Deterministic gate** — evaluate target certainty, evidence sufficiency, semantic ambiguity, mutation authorization, and required tool availability.
6. **Execution contract** — if and only if the gate is READY, freeze the target, allowed tool, expected append, evidence IDs, acceptance tests, and stop conditions.
7. **Human checkpoint** — pause before mutation. Approval applies to the displayed contract, not to unconstrained future tool use.
8. **Bounded mutation** — execute only the allowlisted append operation.
9. **Independent verification** — perform a fresh DataHub read and deterministically test for the expected marker and target identity.
10. **Durable handoff** — persist a compact execution record using the predeclared continuity path.
11. **Fresh recovery** — start from a new process and recover the prior execution from DataHub-backed state.

This structure minimizes the number of places where probabilistic model output can influence irreversible state.

## Core metrics and domains

The project is optimized for five judge-relevant domains. These are protocol metrics, not unverified live-performance claims.

| Domain | Primary metric | Why it matters | Evidence in repo |
|---|---|---|---|
| **Safety / boundedness** | unauthorized mutation count = 0 in refusal/control path | A useful agent must know when not to write | deterministic gate, exact-target scoping, approval interrupt, allowlisted append |
| **Verifiability** | every claimed successful catalog mutation requires an independent post-write read | Prevents LLM self-attestation | verification state machine + post-action `get_entities` evidence |
| **Evidence integrity** | every fact must resolve to execution-local evidence IDs; evidence carries SHA-256 digest | Makes reasoning auditable and resistant to stale memory | `EvidenceRef` model and gate checks |
| **Continuity** | recovery is valid only from fresh DataHub-backed read | Tests whether work survives the agent session | handoff verification + P4 fresh-process recovery |
| **DataHub depth** | exact entity + schema + upstream lineage + downstream lineage + bounded write + durable recovery | Demonstrates DataHub as context, action, and continuity plane | P0–P4 acceptance sequence |

### Deterministic repository validation

Packaging-time evidence currently recorded in the repository:

- 55/55 tests passed;
- Python compile check passed;
- JavaScript syntax check passed;
- secret scan passed;
- fixture positive/refusal/tamper controls are covered.

These validate the implementation and fixture protocol. They are **not** a substitute for live DataHub acceptance.

## Live proof: P0–P4

A judge should treat live execution as passed only when sanitized outputs exist for all required stages.

| Stage | Pass condition | Suggested artifact |
|---|---|---|
| **P0 — MCP capability discovery** | required read tools exposed; positive path also exposes `update_description` | `artifacts/live/p0-preflight.json` |
| **P1 — exact target read** | returned target equals `DEMO_TARGET_URN`; entity, schema, upstream and downstream lineage are readable | `artifacts/live/p1-read.json` |
| **P2 — refusal control** | ambiguous/unauthorized task stops with zero write unless authoritative definition evidence exists | sanitized run output |
| **P3 — bounded action** | approved append executes and fresh DataHub re-read returns `VERIFIED`/`VERIFIED_NOOP` | `artifacts/live/p3-run.json` |
| **P4 — fresh recovery** | a new process recovers the prior handoff from DataHub-backed state | `artifacts/live/p4-fresh-recovery.json` |

If these artifacts are absent, the correct claim is: **implementation validated offline; live P0–P4 still pending on the supplied DataHub instance**.

## Live-run checklist

Use a non-sensitive showcase asset and a fresh PAT. Never commit the PAT or `.env`.

```env
DATAHUB_GMS_URL=<instance GMS URL>
DATAHUB_GMS_TOKEN=<fresh PAT>
DATAHUB_SERVER_MUTATIONS_ENABLED=true
SAVE_DOCUMENT_TOOL_ENABLED=true
ALLOW_DATAHUB_MUTATIONS=false
REQUIRE_HUMAN_APPROVAL=true
DEMO_TARGET_URN=<exact target URN>
```

Then run P0 and P1, keep mutations disabled for the P2 refusal control, enable `ALLOW_DATAHUB_MUTATIONS=true` only for the reviewed P3 contract, and execute P4 from a new process.

See `docs/LIVE_ACCEPTANCE.md` for exact commands and pass/fail gates.

## Claim boundaries

Safe submission language:

- **Validated:** deterministic protocol, refusal controls, evidence/contract logic, API/frontend contract, secret hygiene, fixture handoff behavior.
- **Live-validated only after artifacts exist:** real DataHub P0–P4, actual mutation verification, and fresh DataHub-backed recovery on the judge/demo instance.
- **Never claim:** that fixture replay proves a real DataHub write, that the model itself verifies success, or that continuity succeeded without a fresh DataHub read.

## Recommended judge demo order

1. Show the exact target and real DataHub evidence.
2. Run the ambiguous revenue task and show the zero-write refusal.
3. Run the valid continuity task and inspect the execution contract before approval.
4. Approve the one append-only mutation and show the independent `VERIFIED` re-read.
5. Start a fresh agent/process and recover the handoff from DataHub.
6. End on the invariant: **evidence → bounded decision → verified action → durable continuity**.

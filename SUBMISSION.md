# Devpost submission copy

## Name
Reality Handoff Agent

## Tagline
**Proof-carrying DataHub actions that survive the agent session.**

## Challenge
Agents That Do Real Work

## What it does
Reality Handoff is a LangGraph agent that uses DataHub MCP as its context and action surface, then uses DataHub-backed persistence as continuity for the next agent. It searches and inspects a target asset, reads schema plus upstream/downstream lineage, hashes observations into evidence references, and compiles a `RealitySnapshot` of facts, inferences, unknowns, and contradictions.

A deterministic Python gate—not the LLM—decides whether work may proceed. Ambiguous semantics such as an unresolved revenue definition stop as `NEEDS_HUMAN`. A READY run creates an explicit `ExecutionContract` fixing the target, allowed tools, expected append, acceptance tests, and stop conditions. LangGraph then pauses for human approval.

After approval the agent performs one append-only `update_description`, independently re-reads DataHub to verify its unique marker, then persists a Reality Handoff using `save_document` when available or a disclosed bounded target-description fallback. A fresh recovery call must re-read that DataHub-backed state before continuity is claimed.

The repository also ships a judge-facing product surface: real task input, evidence/reality, gate, execution contract, Approve/Reject, independent verification, and **Start Fresh Agent** recovery. A fixture mode demonstrates the deterministic protocol without credentials and is explicitly labeled as non-live evidence.

## Why it matters
Most agent systems can act, but have weak boundaries around what they actually know, why an action was authorized, whether a write really landed, and what a later agent should trust. Reality Handoff turns DataHub context into a proof-carrying execution protocol:

**evidence → bounded decision → verified action → durable continuity**.

## Algorithmic approach
Reality Handoff is deliberately a fail-closed state machine rather than a free-form agent loop:

1. Discover the actual DataHub MCP capability surface.
2. Read the exact target, schema, upstream lineage, and downstream lineage.
3. Normalize every successful result into an immutable evidence reference with arguments, timestamp, target, digest, and bounded excerpt.
4. Compile facts, inferences, unknowns, and contradictions; facts must resolve to evidence from the current execution.
5. Run deterministic gates for evidence sufficiency, semantic ambiguity, exact-target certainty, mutation authorization, and required-tool availability.
6. If READY, freeze the target, tool, append operation, evidence, acceptance tests, and stop conditions into an `ExecutionContract`.
7. Pause for human approval.
8. Execute only the allowlisted append-only mutation.
9. Independently re-read DataHub and deterministically verify target identity plus the expected marker.
10. Persist the handoff, verify it with another read, and require a fresh process to recover it.

This confines probabilistic model behavior to interpretation and bounded text drafting; authorization and success criteria remain deterministic.

## Core metrics / domains
The project is optimized for five measurable judge-relevant domains:

- **Safety / boundedness:** unauthorized mutation count is expected to remain zero on refusal/control paths; target and mutation are contract-scoped.
- **Verifiability:** every successful catalog-mutation claim requires an independent post-write DataHub read; the model cannot self-attest success.
- **Evidence integrity:** every fact must resolve to execution-local evidence IDs; evidence includes a SHA-256 digest of normalized results.
- **Continuity:** handoff success is valid only after independent persistence verification and fresh-process recovery from DataHub-backed state.
- **DataHub depth:** the protocol exercises exact entity context, schema, upstream lineage, downstream lineage, a bounded metadata action, and durable recovery.

Packaging-time repository validation records **55/55 tests passed**, Python compile PASS, JavaScript syntax PASS, and secret scan PASS. Those are implementation/fixture metrics, not a substitute for live DataHub P0–P4 evidence.

## DataHub use

- `search`
- `get_entities`
- `list_schema_fields`
- `get_lineage` upstream and downstream
- `update_description` for the bounded action
- `save_document` when exposed for durable handoff
- `search_documents` + `get_entities` for independent document recovery

## Technologies
Python, LangGraph, LangChain MCP adapters, official DataHub MCP Server, Pydantic, FastAPI, vanilla browser UI, pytest.

## Reliability / safety
The model cannot hold authorization authority, select arbitrary write tools, or declare verification success. DataHub metadata is untrusted evidence. Mutation exposure and mutation authorization are separate gates. The demo may be exact-URN scoped. Human approval is checkpointed with a LangGraph interrupt. MCP arguments bind against discovered schemas. Every successful catalog change requires an independent DataHub re-read, and every continuity claim requires an independent recovery read.

## Live proof standard — P0 to P4
Live DataHub success should be claimed only after all five gates pass on the supplied instance/target:

- **P0:** required MCP reads are exposed; positive path also exposes `update_description`.
- **P1:** the exact configured URN is returned and entity/schema/upstream/downstream context is readable.
- **P2:** the ambiguous refusal task performs zero writes unless DataHub actually contains authoritative definition evidence.
- **P3:** one reviewed append-only action is approved and an independent re-read returns `VERIFIED` or `VERIFIED_NOOP`.
- **P4:** a fresh process recovers the prior handoff from DataHub-backed state without prior graph/browser/chat memory.

If sanitized live artifacts are absent, the accurate claim is: **implementation validated offline; live P0–P4 pending on the supplied DataHub instance**.

See `docs/JUDGE_GUIDE.md` for the judge scorecard, algorithmic rationale, claim boundaries, and evidence map. See `docs/LIVE_ACCEPTANCE.md` for exact P0–P4 commands and pass/fail gates.

## Demo arc
1. Real DataHub evidence and target.
2. Unsupported revenue task → `NEEDS_HUMAN`, zero write.
3. Valid task → explicit contract + approval.
4. One append-only mutation → independent `VERIFIED` re-read.
5. Durable handoff.
6. Fresh agent recovers prior execution from DataHub-backed state.

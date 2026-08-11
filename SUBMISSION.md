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

## Demo arc
1. Real DataHub evidence and target.
2. Unsupported revenue task → `NEEDS_HUMAN`, zero write.
3. Valid task → explicit contract + approval.
4. One append-only mutation → independent `VERIFIED` re-read.
5. Durable handoff.
6. Fresh agent recovers prior execution from DataHub-backed state.

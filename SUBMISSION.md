# Devpost submission copy

## Name
Reality Handoff Agent

## Tagline
**Proof-carrying DataHub actions that survive the agent session.**

## Challenge
Agents That Do Real Work

## What it does
Reality Handoff is a LangGraph agent that treats DataHub MCP as the source of organizational data context and DataHub itself as the continuity layer between agent sessions. The agent searches and inspects a target asset, reads its schema and both upstream and downstream lineage, converts those observations into hashed evidence references, and compiles a RealitySnapshot containing facts, inferences, unknowns, and contradictions.

A deterministic Python gate—not the LLM—decides whether work may proceed. If a business term such as revenue is unresolved, the run stops as `NEEDS_HUMAN`. If reality is sufficiently established, the agent creates an explicit ExecutionContract that fixes the target, write tools, acceptance tests, and stop conditions. LangGraph then pauses for human approval.

After approval, the agent performs one append-only DataHub metadata action through MCP, independently re-reads the target to verify the exact expected marker, and writes a structured Reality Handoff back into DataHub using `save_document` when available. A separate re-read must recover that handoff before the graph can claim success. A fresh process can then retrieve the prior decision without conversation history.

## Why it matters
Agent systems often have enough context to act but weak boundaries around what they actually know, why an action was authorized, whether a write really landed, and what a later agent should trust. Reality Handoff turns DataHub context into a proof-carrying execution protocol: evidence → bounded decision → verified action → durable continuity.

## DataHub use
- Remote DataHub MCP over streamable HTTP.
- `search` for discovery.
- `get_entities` for authoritative entity context.
- `list_schema_fields` for schema context.
- `get_lineage` in both directions to understand dependencies.
- `update_description` for the bounded demo mutation.
- `save_document` for durable decision/handoff state when available.
- `search_documents` / entity re-read for independent recovery.

## Technologies
Python, LangGraph, LangChain MCP adapters, DataHub MCP Server, Pydantic, FastAPI, LangSmith / Agent Server, pytest.

## Safety / reliability
The LLM does not hold credentials, authorize mutations, choose arbitrary write tools, or declare verification success. Mutations are disabled by default; the public demo can be exact-URN scoped; approval uses a checkpointed LangGraph interrupt; retrieved metadata is untrusted input; secrets are redacted; write arguments bind against runtime-discovered MCP schemas; and every successful state change requires an independent re-read.

## Demo arc
1. Show live MCP capability discovery and real DataHub context.
2. Show a `revenue` task stopping at `NEEDS_HUMAN` with zero writes.
3. Show a valid task produce an ExecutionContract and pause for approval.
4. Approve; show the real `update_description` mutation and deterministic re-read verification.
5. Show `save_document` and an independent handoff re-read.
6. Start a fresh process/thread and recover the prior decision from DataHub.

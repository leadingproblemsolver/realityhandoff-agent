# Architecture

## Runtime spine

`User task → DataHub MCP preflight → MCP context retrieval → EvidenceRefs → semantic RealitySnapshot → deterministic Constraint Gate → ExecutionContract → human interrupt → allowlisted MCP mutation → deterministic MCP re-read verification → DataHub-native handoff → independent handoff re-read → fresh-process recovery`

The LLM is **not** the system of record, credential holder, gate, mutation authority, or verifier. It may interpret evidence and draft bounded description text. Python owns target scoping, evidence resolution, tool allowlisting, state routing, contract validation, and verification.

## State machine

`RECEIVED → MCP_PREFLIGHT → CONTEXT_BUILDING → REALITY_COMPILED → {NEEDS_CONTEXT | NEEDS_HUMAN | BLOCKED | CONTRACT_READY} → APPROVAL_PENDING → ACTION_EXECUTED → {FAILED | VERIFIED} → HANDOFF_WRITING → {FAILED | HANDOFF_VERIFIED} → COMPLETE`

Any node-level exception is converted into an explicit failed stage before downstream mutation can proceed.

## Required DataHub tool surface

Read: `search`, `get_entities`, `list_schema_fields`, `get_lineage`.

Write: `update_description`.

Preferred continuity: `save_document`; `search_documents` for recovery when exposed.

The context stage reads `get_lineage` twice: upstream and downstream. A failure in any required context read yields `NEEDS_CONTEXT`; errors are not converted into positive evidence.

## Evidence model

Each successful MCP result becomes an immutable `EvidenceRef` containing:

- evidence ID;
- tool name;
- entity URN when applicable;
- arguments;
- retrieval timestamp;
- SHA-256 digest of the full normalized result;
- bounded raw excerpt for interpretation.

The gate checks that every fact's evidence IDs resolve to the actual evidence set retrieved in this execution.

## Human boundary

The approval interrupt discloses both:

1. the exact metadata mutation; and
2. the post-verification durable handoff write.

The fallback handoff path is also predeclared in the contract, so a failed `save_document` call cannot silently expand the approved mutation surface.

## Verification

Action verification is deterministic: the agent re-reads the contract target through `get_entities`, checks target identity, checks the exact idempotency marker, and records the post-action EvidenceRef. The model cannot supply the verdict.

Handoff verification is a second independent read:

- if `save_document` returns a document URN, re-read that exact document;
- otherwise rediscover tools and search for the unique handoff execution ID;
- if document write is unavailable and the approved fallback was used, re-read the exact target entity and require the handoff marker.

Only then may the graph enter `HANDOFF_VERIFIED`.

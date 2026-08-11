# Final technical audit

## High-severity gaps found and closed during conversion

### 1. GraphQL-first architecture did not meet the intended agent-context path
**Closed:** DataHub MCP is now the primary/only runtime integration. GraphQL and n8n are absent from the executable path.

### 2. Prototype write-back was dry-run only
**Closed by design:** the native graph executes a real, allowlisted `update_description` call after explicit approval and then writes a durable handoff via `save_document` when exposed.

### 3. SQL verification was not production SQL verification
**Closed by removal:** SQL generation is no longer the demo action. Verification now checks the real DataHub metadata state affected by the agent.

### 4. Dataset URN parser corrupted canonical parenthesized URNs
**Closed:** regression test added; closing `)` is preserved.

### 5. Required context tool errors could have been turned into apparent evidence
**Closed:** failed entity/schema/lineage reads are stored as context errors and produce `NEEDS_CONTEXT`; they never become positive EvidenceRefs.

### 6. Gate accepted any non-empty evidence ID, including invented IDs
**Closed:** every factual evidence ID must resolve to the retrieved evidence set for that execution.

### 7. DataHub write schemas could drift
**Closed:** arguments bind against each discovered MCP tool schema. Unknown required parameters fail closed. Regression fixtures cover current-style `update_description` and `save_document` shapes.

### 8. `update_description` operation casing
**Closed:** action/fallback use lowercase `append`, compatible with the MCP tool's semantic operation.

### 9. `save_document` was missing document type / related asset semantics
**Closed:** the handoff call sends `document_type=Decision`, title, content, and `related_assets=[target]`; runtime binding drops unsupported optional fields and fails on unresolved required fields.

### 10. Successful write response was being treated as verified continuity
**Closed:** a separate node must independently re-read the DataHub document or fallback entity record before `HANDOFF_VERIFIED`. Because `search_documents` returns document metadata rather than the body, any search hit must first resolve a document URN and then pass an independent `get_entities(document_urn)` content check. If indexing is delayed, both graph verification and fresh-process recovery perform only three bounded read-only search attempts, then fail closed.

### 11. Metadata prompt injection
**Strengthened:** retrieved DataHub text is explicitly untrusted, planner/model cannot expand write tools, contract construction is deterministic, outbound model-authored metadata is redacted, and prompt-injection regression tests assert the contract remains unchanged.

## Remaining live risks / claim boundaries

### Live tenant capability/permissions — OPEN until P0
Managed DataHub MCP must expose the required read tools and `update_description`. Mutation-tool availability depends on DataHub MCP version/configuration and caller permissions. Preflight detects this; the graph fails closed otherwise.

### Live `save_document` behavior — OPEN until P4
The agent prefers a DataHub Decision document. If unavailable or unbindable, it uses an explicitly-approved entity-description handoff fallback. Do not claim document persistence until live proof exists.

### Semantic support is not formally proved — BOUNDED
The gate proves that fact references resolve to retrieved evidence IDs, not that arbitrary natural-language claims are logically entailed by those evidence chunks. The model is constrained and ambiguous metric terms have an additional deterministic guard, but this is not theorem proving.

### Catalog-state verification is not warehouse-state verification — BOUNDED
The verifier proves that the expected DataHub metadata mutation is present on the intended entity after re-read. It does not prove raw-data accuracy or downstream warehouse correctness.

### Package-level LangGraph/MCP execution — OPEN in this build environment
The artifact-builder container did not have `langgraph`, `langchain`, `langchain-mcp-adapters`, or `langchain-openai` installed and could not fetch them from the network. The deterministic core, FastAPI replay, source compilation, secret scan, and tests were executed. The actual LangGraph/MCP runtime must be installed and exercised in the user's LangSmith/local environment before claiming live end-to-end success.

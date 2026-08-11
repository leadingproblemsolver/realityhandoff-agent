# n8n → LangGraph conversion

The n8n prototype was used as an executable specification. It is **not** part of the final runtime.

| Prototype | Native conversion | Decision |
|---|---|---|
| RH-00 Orchestrator | LangGraph `StateGraph` | Preserve explicit branching/state; remove workflow IDs/webhooks |
| RH-00A GraphQL Preflight | DataHub MCP tool discovery | Replace completely |
| RH-01 GraphQL Context | DataHub MCP `search/get_entities/list_schema_fields/get_lineage` | Replace completely |
| RH-02 Reality Operator | Pydantic RealitySnapshot + optional structured LLM compiler | Preserve fact/inference/unknown model |
| RH-03 Constraint Gate | pure Python deterministic gate | Preserve nearly verbatim |
| RH-04 Execution Contract | Pydantic ExecutionContract | Change from “no mutation” to one bounded, approved metadata mutation |
| RH-05 SQL Generator | evidence-backed DataHub action planner | Retire SQL generation |
| RH-06 JS SQL checks | exact post-mutation MCP re-read | Replace SQL claim boundary with actual catalog-state verification |
| RH-07 dry-run writeback | allowlisted `update_description` + preferred `save_document` | Turn proposal into real work after approval |
| RH-08 n8n Data Table | DataHub document / verified entity-description handoff | Move continuity into DataHub itself |
| RH-ERR | LangGraph persisted run failure + explicit terminal state | Preserve fail-closed semantics |

The conversion intentionally keeps the unique machinery—evidence, gates, contracts, verification, continuity—and discards transport-specific scaffolding.

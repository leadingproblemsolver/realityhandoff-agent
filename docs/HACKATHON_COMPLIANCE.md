# Hackathon compliance matrix

## Agents That Do Real Work

| Requirement | Concrete proof in Reality Handoff |
|---|---|
| Reads DataHub through MCP / Agent Context Kit | `langchain-mcp-adapters` connects directly to the configured DataHub MCP server and discovers live tools |
| Understands what's connected to what | before action: `search` + `get_entities` + `list_schema_fields` + **upstream and downstream** `get_lineage` |
| Takes action | exact-target, append-only `update_description` after LangGraph human approval |
| Writes results back | preferred `save_document(document_type=Decision, related_assets=[target])`; explicitly-approved verified target-description fallback |
| Next person/agent inherits knowledge | handoff includes execution/task/evidence/action/verification/unresolved/risks/next step; a `search_documents` hit is resolved to its document URN and the full body is independently re-read through `get_entities` before `HANDOFF_VERIFIED`; then a fresh process repeats that recovery for P4 |

## Goes beyond built-ins

DataHub provides context and mutation tools. Reality Handoff adds a reusable execution protocol on top: evidence identities/hashes, truth-status separation, semantic uncertainty gate, explicit action contract, human approval, mutation verification, durable decision record, and zero-chat-context recovery.

## Submission checklist

- [ ] Public repository URL
- [x] Apache-2.0 `LICENSE`
- [x] Full source + setup instructions
- [x] `examples/` sample output
- [x] Interactable `/demo` evaluator
- [x] Rigorous deterministic/replay tests
- [x] Live P0–P4 acceptance runbook
- [ ] Live project URL after LangSmith deployment
- [ ] Public demo video under 3 minutes
- [ ] Sanitized live P0–P4 evidence captured in `artifacts/live/`

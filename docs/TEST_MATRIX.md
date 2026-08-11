# Test and evaluation matrix

## Deterministic suite

The packaged test suite covers:

1. evidence-backed facts → READY;
2. fact without evidence ID → BLOCKED;
3. hallucinated/unresolved evidence ID → BLOCKED;
4. blocking semantic unknown → NEEDS_HUMAN;
5. contradictions → NEEDS_CONTEXT;
6. missing target → NEEDS_CONTEXT;
7. illegal state transition rejected;
8. non-READY reality cannot create an ExecutionContract;
9. contract fixes target + action + durable handoff tools;
10. prompt injection in retrieved metadata cannot expand the contract write surface;
11. official-style `update_description` argument aliases bind to `entity_urn` + `operation` + `description`;
12. official-style `save_document` arguments include `document_type`, title, content, related assets;
13. unknown required MCP tool arguments fail closed;
14. DataHub dataset URNs retain balanced closing parentheses;
15. required downstream-lineage failure blocks execution;
16. action node uses append semantics and the contract target;
17. verification requires target identity + exact post-action marker + EvidenceRef;
18. pre-existing marker yields safe idempotent no-op;
19. wrong target fails verification;
20. handoff uses a DataHub `Decision` document linked to the target when possible;
21. handoff cannot be marked verified unless an independent DataHub read recovers it;
22. secret redaction covers Bearer credentials and common token forms;
23. positive replay: read → READY → mutate → verify → persist/recover handoff;
24. ambiguity replay: NEEDS_HUMAN and zero mutation;
25. tampered post-state: FAILED and no handoff success claim;
26. `/demo` serves the transparent interactive evaluator;
27. replay API positive and negative controls behave correctly.

## Live P0–P4 acceptance gates

- **P0 MCP:** `scripts/live_preflight.py` discovers the required tool surface from the real tenant.
- **P1 Read:** `scripts/live_read_smoke.py` obtains a real dataset plus entity, schema, upstream lineage, and downstream lineage context.
- **P2 Decide:** the live graph yields a traceable READY/NEEDS_HUMAN outcome from real EvidenceRefs.
- **P3 Act:** after explicit human approval, `update_description` writes only to the exact contract target.
- **P4 Inherit:** target re-read verifies the action; DataHub handoff is written and independently re-read; a fresh process retrieves the prior decision.

**Do not claim live end-to-end DataHub success until P4 is captured against the actual tenant.**

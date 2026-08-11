# Judge-facing product acceptance

The frontend is a thin rendering/control surface over structured backend state. It does not implement orchestration, authorization, DataHub access, or model logic.

## T01–T15

| ID | Requirement | Pass condition |
|---|---|---|
| T01 | Cold comprehension | Problem, proof mechanism, CTA understood without docs |
| T02 | Fixture path | Positive fixture reaches verified handoff and is labeled non-live |
| T03 | Refusal fixture | Revenue control shows blocking unknown + zero write |
| T04 | Live task | One click creates exactly one backend execution |
| T05 | Evidence | UI displays backend evidence IDs/tools/URNs |
| T06 | Gate | UI renders structured `gate.decision`, never prose inference |
| T07 | Contract | Target/tool/operation/evidence/proposed append visible before approval |
| T08 | Reject | Reject resumes same thread with no mutation |
| T09 | Approve | Approve resumes same thread; no second execution is created |
| T10 | Verification | Mutation result and independent verification are visibly separate |
| T11 | Handoff | Durable handoff location/result displayed |
| T12 | Fresh agent | Recovery calls `/api/recovery`; no frontend-memory shortcut |
| T13 | Failure | DataHub/backend errors become explicit UI state, not endless loading |
| T14 | Security | No private token/key in HTML, JS, repository, network payload from browser |
| T15 | Production | Root URL, refresh, mobile viewport, incognito, canonical demo path all work |

## Automated coverage

```bash
pytest -q tests/test_webapp.py tests/test_frontend_contract.py
node --check src/reality_handoff/static/app.js
```

## Manual production smoke

1. Open `/` in incognito.
2. Run fixture positive.
3. Run fixture refusal.
4. Switch Live DataHub.
5. Run P2 refusal.
6. Run P3 until approval; verify contract visually.
7. Reject once and prove no write.
8. Run again; approve exactly one bounded action.
9. Confirm verification panel is `VERIFIED`.
10. Click **Start Fresh Agent** and recover the handoff.
11. Refresh root URL.
12. Repeat canonical path at mobile width.

Ship only when all relevant live tests pass.

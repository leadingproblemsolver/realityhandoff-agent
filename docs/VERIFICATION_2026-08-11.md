# Verification — 2026-08-11 — v0.5.0

## Packaging-time results

```text
pytest:            55 passed
product smoke:    PASS
Python compile:   PASS
JavaScript check: PASS
secret scan:      PASS
```

## Product closure verified offline

- Judge-facing root and `/demo` exist.
- Fixture positive path returns READY → VERIFIED → recovered handoff.
- Fixture refusal path returns NEEDS_HUMAN with zero mutations.
- Structured live API includes run/get/approve/reject/recovery boundaries.
- Browser contains no secret inputs.
- MCP runtime uses the official Python `mcp_server_datahub` module rather than npm/uvx.
- Mutation scope fails closed when `ALLOW_DATAHUB_MUTATIONS=false` or a write escapes `DEMO_TARGET_URN`.
- Runtime MCP schemas are bound dynamically rather than hard-coding provider argument names.
- READY contract creation fails if `update_description` is not actually exposed.
- Read/refusal path is allowed to proceed when mutation tools are intentionally hidden.
- Uploaded `.env` was removed from the finalized tree and JWT-like tokens were added to secret detection.

## External acceptance still required

This packaging environment could not install missing LangGraph/DataHub MCP dependencies because outbound package network was unavailable, and it had no live DataHub GMS. Therefore do not claim live end-to-end success until the actual Codespace/deployment records:

- P0 live MCP read capability;
- P1 exact `DEMO_TARGET_URN` read/schema/lineage;
- P2 refusal with zero write;
- P3 one approved append + independent re-read verification;
- P4 fresh DataHub-backed handoff recovery;
- production judge-surface smoke.

See `docs/LIVE_ACCEPTANCE.md` and `docs/FRONTEND_ACCEPTANCE.md`.

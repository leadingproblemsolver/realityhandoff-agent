# Final audit — v0.5.0

## Closed

- Cloud-only MCP assumption removed.
- Canonical self-hosted GMS + PAT mode implemented.
- Official Python DataHub MCP server pinned as an application dependency.
- Runtime no longer depends on npm or `uvx`.
- Missing MCP `invoke()` / `refresh_tools()` interface implemented.
- Runtime-discovered MCP schemas bind logical arguments and fail closed.
- MCP-server mutation exposure and agent-side mutation authorization are separate gates.
- READY path fails if `update_description` is not actually exposed.
- Refusal/read path can run without exposing mutation tools.
- Exact demo target is independently re-read and scope-enforced.
- Backend + frontend are one deployment artifact.
- Live run, same-thread approve/reject, and fresh recovery API boundaries implemented.
- Fixture and live claims are visibly separated.
- Browser contains no credential inputs.
- Uploaded secret-bearing `.env` removed; `.gitignore` added.
- 55 tests pass.

## Remaining external proof

Only live P0–P4 and production URL smoke remain. See `docs/LIVE_ACCEPTANCE.md` and `docs/FRONTEND_ACCEPTANCE.md`.

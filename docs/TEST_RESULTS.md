# Test results

Packaging-time validation for v0.3.0.

## Automated suite

```text
44 passed (independent verification)
```

The suite covers evidence integrity, deterministic gate behavior, Execution Contract bounds, runtime MCP tool-schema binding, prompt-injection resistance, canonical DataHub URN parsing, required lineage-read failures, append-only action invocation, deterministic mutation verification, `save_document` arguments, independent handoff re-read, bounded document-search retries, fallback continuity, secret scanning, the FastAPI replay surface, and end-to-end offline replay controls.

## Offline behavioral controls

| Scenario | Gate | Mutation | Verification | Handoff |
|---|---|---:|---|---|
| Valid orders task | READY | 1 | VERIFIED | recovered |
| Undefined `revenue` | NEEDS_HUMAN | 0 | not run | not written |
| Post-action tamper | READY | 1 | FAILED | not written |

Raw outputs are committed under `artifacts/offline/`.

## Additional validation

- `scripts/secret_scan.py`: PASS.
- Python `compileall` over `src/`, `tests/`, and `scripts/`: PASS.
- `langgraph.json`, both example JSON files, and `pyproject.toml`: parse successfully.
- Ruff: not executed in the artifact-builder environment because Ruff is not installed there; it is included in the `dev` dependency group for the target environment.

## Explicitly not proven in the artifact-builder environment

The builder environment does not contain `langgraph`, `langchain`, `langchain-mcp-adapters`, or `langchain-openai`, and no live DataHub tenant credentials were exercised here. Therefore **live P0–P4 is not claimed**. Run `docs/LIVE_ACCEPTANCE.md` in LangSmith or a local environment with the real DataHub MCP endpoint/token before recording the submission demo.

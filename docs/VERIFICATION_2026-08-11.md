# Independent verification — 2026-08-11

This pass independently re-ran the packaged artifact rather than trusting the packaging-time result.

## Proven in the verification container

- archive extracted successfully;
- every original `MANIFEST.sha256` entry matched before modification;
- Python 3.13.5 `compileall` passed over `src/`, `scripts/`, and `tests/`;
- deterministic test suite passed;
- secret scanner passed;
- positive replay produced `READY`, exactly one mutation, `VERIFIED`, and recovered handoff;
- CLI help loaded;
- `langgraph.json` parsed and matches current LangGraph deployment structure;
- core non-LangGraph modules import cleanly.

## Upstream compatibility checked

Current upstream documentation/source confirms:

- `langchain-mcp-adapters==0.3.0` supports `MultiServerMCPClient` with HTTP transport, runtime `Authorization` headers, and `handle_tool_errors=False`;
- current DataHub MCP tools use compatible signatures for `search`, `get_entities`, `list_schema_fields`, `get_lineage`, `update_description`, `search_documents`, and `save_document`;
- `search_documents` returns metadata and the implementation correctly follows with `get_entities(document_urn)` before claiming recovered handoff content;
- LangGraph deployment supports `dependencies: ["."]`, graph module entrypoints, `.env`, and a FastAPI custom app via `http.app`.

## Defect found and fixed

The original v0.3.0 ZIP contained inconsistent package version metadata: `pyproject.toml` and FastAPI reported `0.3.0`, while `reality_handoff.__version__` reported `0.2.0`. The verified build fixes this and adds a regression test.

## Not proven here

A fresh dependency installation could not be completed because the verification container has no outbound package-network access. It also does not contain the user's DataHub tenant credentials. Therefore these remain live acceptance gates:

1. install declared dependencies in LangSmith/local environment;
2. import/boot the real LangGraph runtime;
3. P0 discover DataHub MCP tools using the real tenant endpoint + PAT;
4. P1 read real DataHub context;
5. P2 prove ambiguity refusal with zero mutation;
6. P3 human-approved metadata mutation + independent re-read verification;
7. P4 `save_document` + fresh-process recovery of its full content.

Until P0–P4 are captured, the correct claim is: **offline core independently verified; live DataHub end-to-end pending.**

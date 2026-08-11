# Threat model and mitigations

| Risk | Severity | Mitigation |
|---|---:|---|
| DataHub description/document prompt injection | High | retrieved text is explicitly untrusted; model cannot expand tool allowlist; contract/executor are deterministic |
| Over-broad metadata mutation | High | only `update_description` and handoff sink allowed; optional `DEMO_TARGET_URN` exact scope |
| Public-demo credential leakage | Critical | PAT stays server-side in env; no browser token input; redaction + secret-scan tests |
| Semantic hallucination | High | every fact requires evidence IDs; ambiguous business terms block; LLM is not gate/verifier |
| Mutation falsely reported as success | High | post-action `get_entities` re-read must contain exact idempotency marker |
| MCP schema drift | Medium | runtime introspects each tool's `args_schema`; unknown required parameters fail closed |
| Duplicate demo writes | Medium | deterministic task+URN marker enables idempotent no-op |
| `save_document` absent/hidden | Medium | compact handoff fallback appended to same verified target and re-read |
| Server/tool outage | Medium | failure becomes explicit terminal state; no downstream mutation |
| Unbounded search/tool cost | Medium | max target/entity context caps; read tools are bounded |

For an unattended/public deployment, use a DataHub service account with least privilege and a Default View restricted to the showcase/demo assets instead of a personal token.

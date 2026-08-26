# Hermes Kanban Handoff Preflight

A small deterministic gate for one failure mode in multi-agent boards: a worker is treated as finished even though the next worker cannot reconstruct what changed, what was verified, how to retry, or what risk remains.

This is deliberately **not** a native Hermes plugin yet. It is a framework-light preflight over a normalized JSON handoff envelope so real users can test the contract before any deeper integration is justified.

## Contract

A settlement-ready handoff must preserve:

- `task_id`
- `status`
- `changed` — what materially changed
- `verified` — evidence that the claimed state was checked
- `retry_unblock` — how a later worker/operator can recover or retry
- `remaining_risk` — what is still unresolved

For `blocked`, `failed`, `timed_out`, `error`, or `cancelled` outcomes, it additionally requires `partial_findings`. A failed attempt that learned something but loses that learning is not settlement-ready.

The result is deterministic JSON:

```json
{
  "verdict": "PASS",
  "settlement_ready": true,
  "missing": [],
  "warnings": []
}
```

A blocked handoff exits with status code `2` and names the missing evidence.

## Run

From the repository root after installation:

```bash
python -m reality_handoff.hermes_preflight examples/hermes_handoff.json --pretty
```

Or pipe a normalized envelope through stdin:

```bash
cat handoff.json | python -m reality_handoff.hermes_preflight - --pretty
```

## Example failure

```json
{
  "task_id": "task-18",
  "status": "timed_out",
  "changed": "Investigated dispatcher failure.",
  "verified": "Reproduced on fixture.",
  "retry_unblock": "Retry from the preserved state.",
  "remaining_risk": "Root cause remains open."
}
```

This blocks because `partial_findings` is absent. The preflight does not infer that a timeout produced no useful information.

## Why this slice exists

The useful question is not whether a multi-agent board can create more agents. It is whether an interrupted or completed worker leaves enough durable evidence for the next actor to continue without reconstructing the whole session.

The preflight therefore tests the handoff/settlement boundary only. It does not add orchestration, messaging, credentials, persistence, or automatic external writes.

## Evidence boundary

Verified locally before publication:

- completed handoff + settlement evidence -> `PASS`
- timed-out handoff without partial findings -> `BLOCK`
- common aliases normalize to the same contract
- empty verification evidence -> `BLOCK`

Canonical merge additionally requires the repository Product Validation workflow on the PR merge result. Legacy Ruff debt is reported separately and does not replace deterministic tests or compilation as release gates.

These tests establish deterministic contract behavior. They do **not** establish native Hermes compatibility, production adoption, reduced failure rate, or user demand.

## Next evidence event

Give this envelope to Hermes/Kanban operators. If real task exports repeatedly require the same mapping, build the smallest native adapter. If operators do not care about the gate or the mapping is highly variable, kill the integration instead of expanding the artifact.

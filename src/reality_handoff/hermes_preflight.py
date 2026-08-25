"""Deterministic preflight for durable multi-agent task handoffs.

This module is intentionally framework-light: it validates a normalized handoff
envelope and returns a machine-readable PASS/BLOCK verdict. It does not claim
native Hermes integration or mutate a task board.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence


_NON_SUCCESS = {"blocked", "failed", "timed_out", "timeout", "error", "cancelled", "canceled"}

_ALIASES: dict[str, tuple[str, ...]] = {
    "task_id": ("task_id", "id"),
    "status": ("status", "state", "outcome"),
    "changed": ("changed", "what_changed", "summary"),
    "verified": ("verified", "verification", "tests", "verification_evidence"),
    "retry_unblock": ("retry_unblock", "unblock", "retry", "recovery"),
    "remaining_risk": ("remaining_risk", "risk", "open_risk", "residual_risk"),
    "partial_findings": (
        "partial_findings",
        "prior_findings",
        "attempt_summary",
        "partial_summary",
    ),
}


@dataclass(frozen=True, slots=True)
class PreflightResult:
    verdict: str
    settlement_ready: bool
    missing: tuple[str, ...]
    warnings: tuple[str, ...]
    normalized: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["missing"] = list(self.missing)
        data["warnings"] = list(self.warnings)
        return data


def _is_meaningful(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, Mapping):
        return any(_is_meaningful(item) for item in value.values())
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_is_meaningful(item) for item in value)
    return True


def _first(payload: Mapping[str, Any], canonical: str) -> Any:
    for key in _ALIASES[canonical]:
        if key in payload and _is_meaningful(payload[key]):
            return payload[key]
    return None


def preflight(payload: Mapping[str, Any]) -> PreflightResult:
    """Return a deterministic settlement-readiness verdict for one handoff."""

    normalized = {name: _first(payload, name) for name in _ALIASES}
    task_id = str(normalized["task_id"] or "").strip()
    status = str(normalized["status"] or "").strip().lower()
    normalized["task_id"] = task_id
    normalized["status"] = status

    missing: list[str] = []
    warnings: list[str] = []

    for field in ("task_id", "status", "changed", "verified", "retry_unblock", "remaining_risk"):
        if not _is_meaningful(normalized[field]):
            missing.append(field)

    if status in _NON_SUCCESS and not _is_meaningful(normalized["partial_findings"]):
        missing.append("partial_findings")

    if status and status not in _NON_SUCCESS and status not in {
        "completed",
        "complete",
        "done",
        "success",
        "succeeded",
    }:
        warnings.append(f"unrecognized status: {status}")

    if status in {"complete", "done", "success", "succeeded"}:
        normalized["status"] = "completed"
    elif status == "timeout":
        normalized["status"] = "timed_out"
    elif status == "error":
        normalized["status"] = "failed"
    elif status == "canceled":
        normalized["status"] = "cancelled"

    missing = list(dict.fromkeys(missing))
    verdict = "PASS" if not missing else "BLOCK"

    return PreflightResult(
        verdict=verdict,
        settlement_ready=not missing,
        missing=tuple(missing),
        warnings=tuple(warnings),
        normalized=normalized,
    )


def _load_payload(path: str) -> dict[str, Any]:
    if path == "-":
        raw = json.load(__import__("sys").stdin)
    else:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("handoff input must be a JSON object")
    return raw


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check whether a multi-agent handoff contains enough evidence to settle."
    )
    parser.add_argument("input", help="JSON handoff file, or - for stdin")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON output")
    args = parser.parse_args(argv)

    result = preflight(_load_payload(args.input))
    print(json.dumps(result.to_dict(), indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result.settlement_ready else 2


if __name__ == "__main__":
    raise SystemExit(main())

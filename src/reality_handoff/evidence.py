from __future__ import annotations
import re
from typing import Any
from .models import EvidenceRef, stable_text

URN_RE = re.compile(r"urn:li:[A-Za-z0-9_-]+:[^\s\"'<>]+")


def extract_urns(result: Any) -> list[str]:
    text = stable_text(result)
    found = []
    for urn in URN_RE.findall(text):
        urn = urn.rstrip(".;]}")
        if urn not in found:
            found.append(urn)
    return found


def choose_dataset_urn(urns: list[str], forced: str = "") -> str | None:
    if forced:
        return forced if forced in urns else None
    return next((u for u in urns if u.startswith("urn:li:dataset:")), urns[0] if urns else None)


def add_evidence(
    items: list[EvidenceRef],
    tool_name: str,
    args: dict[str, Any],
    result: Any,
    entity_urn: str | None = None,
) -> EvidenceRef:
    ev = EvidenceRef.from_tool(
        index=len(items) + 1,
        tool_name=tool_name,
        arguments=args,
        result=result,
        entity_urn=entity_urn,
    )
    items.append(ev)
    return ev

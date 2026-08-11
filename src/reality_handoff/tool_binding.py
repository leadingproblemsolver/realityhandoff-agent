from __future__ import annotations
from typing import Any

ALIASES = {
    "urn": ("urn", "entity_urn", "entityUrn", "resource_urn"),
    "urns": ("urns", "entity_urns", "entityUrns"),
    "query": ("query", "search_query", "text"),
    "description": ("description", "text", "value", "content"),
    "mode": ("mode", "operation", "update_mode"),
    "upstream": ("upstream", "is_upstream"),
    "title": ("title", "name", "document_title"),
    "content": ("content", "body", "text", "markdown"),
    "document_type": ("document_type", "documentType", "type", "subtype"),
    "related_assets": ("related_assets", "relatedAssets", "assets"),
    "topics": ("topics", "topic_urns", "topicUrns"),
}


def schema_for(tool: Any) -> dict[str, Any]:
    s = getattr(tool, "args_schema", None)
    if s is None:
        return {}
    if isinstance(s, dict):
        return s
    if hasattr(s, "model_json_schema"):
        return s.model_json_schema()
    if hasattr(s, "schema"):
        return s.schema()
    return {}


def bind(tool: Any, semantic: dict[str, Any]) -> dict[str, Any]:
    """Bind logical values to a discovered MCP JSON schema and fail closed on missing required args."""
    schema = schema_for(tool)
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    if not props:
        # Some wrappers expose no schema metadata; only caller-provided exact keys are safe.
        return dict(semantic)
    out: dict[str, Any] = {}
    for logical, value in semantic.items():
        candidates = ALIASES.get(logical, (logical,))
        hit = next((c for c in candidates if c in props), None)
        if hit:
            out[hit] = value
        elif logical in props:
            out[logical] = value
    missing = required - set(out)
    if missing:
        raise ValueError(
            f"Cannot safely bind required arguments for {getattr(tool, 'name', 'tool')}: "
            f"{sorted(missing)}. Discovered schema={schema}"
        )
    return out

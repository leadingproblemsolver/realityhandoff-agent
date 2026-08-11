from __future__ import annotations
import asyncio
from . import mcp_runtime
from .evidence import extract_urns
from .models import stable_text


async def recover(execution_id: str, target_urn: str | None = None) -> dict:
    """Recover a durable handoff from DataHub itself, never from prior chat/graph memory."""
    tools = await mcp_runtime.get_tools()
    title = f"Reality Handoff {execution_id}"
    if "search_documents" in tools:
        try:
            for attempt in range(3):
                search_result = await mcp_runtime.invoke("search_documents", {"query": title})
                document_urns = [
                    u for u in extract_urns(search_result) if u.startswith("urn:li:document:")
                ]
                for document_urn in document_urns[:5]:
                    document = await mcp_runtime.invoke(
                        "get_entities", {"urns": [document_urn], "urn": document_urn}
                    )
                    if f"Reality Handoff: {execution_id}" in stable_text(document):
                        return {
                            "source": "datahub_document",
                            "execution_id": execution_id,
                            "document_urn": document_urn,
                            "attempts": attempt + 1,
                            "result": document,
                        }
                if attempt < 2:
                    await asyncio.sleep(0.5 * (attempt + 1))
        except Exception:
            # A document lookup failure does not authorize a write or fabricated recovery.
            pass
    if target_urn:
        result = await mcp_runtime.invoke(
            "get_entities", {"urns": [target_urn], "urn": target_urn}
        )
        marker = f"[Reality-Handoff-Record:{execution_id}]"
        if marker in stable_text(result):
            return {
                "source": "entity_description",
                "execution_id": execution_id,
                "target_urn": target_urn,
                "result": result,
            }
    return {"source": None, "execution_id": execution_id, "found": False}

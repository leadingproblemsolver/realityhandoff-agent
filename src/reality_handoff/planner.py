from __future__ import annotations
from .models import ActionPlan, ExecutionContract, EvidenceRef
from .security import UNTRUSTED_CONTEXT_NOTICE, redact


async def plan_action(contract: ExecutionContract, evidence: list[EvidenceRef]) -> ActionPlan:
    from .config import settings

    marker = contract.expected_mutation.expected_marker
    safe_fallback = (
        f"{marker}\n\nInspected by Reality Handoff Agent using DataHub MCP. "
        f"Evidence used: {', '.join(contract.evidence_dependencies)}. "
        "This note records provenance and continuity; it does not redefine an existing business metric."
    )
    description = safe_fallback
    rationale = "Append a minimal provenance note bounded by the Execution Contract."
    if settings.openai_api_key:
        try:
            from langchain_openai import ChatOpenAI
            from pydantic import BaseModel

            class Draft(BaseModel):
                description_append: str
                rationale: str

            model = ChatOpenAI(
                model=settings.openai_model,
                temperature=0,
                api_key=settings.openai_api_key,
            ).with_structured_output(Draft)
            excerpts = "\n\n".join(
                f"[{ev.evidence_id}] {ev.raw_excerpt[:1800]}" for ev in evidence
            )
            output = await model.ainvoke(
                f"""Draft a concise Markdown description APPEND for a DataHub asset.
{UNTRUSTED_CONTEXT_NOTICE}
Execution goal: {contract.goal}
Target: {contract.expected_mutation.target_urn}
Evidence:
{excerpts}
Rules: do not invent business definitions; use only evidence; do not include secrets; preserve existing description because this is append-only. The first line MUST be exactly {marker}. Keep under 900 characters."""
            )
            candidate = redact(output.description_append.strip())[:900]
            if candidate.startswith(marker):
                description = candidate
                rationale = redact(output.rationale)[:800]
        except Exception:
            pass
    return ActionPlan(
        tool="update_description",
        target_urn=contract.expected_mutation.target_urn,
        description_append=description,
        marker=marker,
        evidence_ids=contract.evidence_dependencies,
        rationale=rationale,
    )

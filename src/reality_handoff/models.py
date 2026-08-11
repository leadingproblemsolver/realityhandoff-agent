from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field, model_validator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Stage(str, Enum):
    RECEIVED = "RECEIVED"
    MCP_PREFLIGHT = "MCP_PREFLIGHT"
    CONTEXT_BUILDING = "CONTEXT_BUILDING"
    REALITY_COMPILED = "REALITY_COMPILED"
    NEEDS_CONTEXT = "NEEDS_CONTEXT"
    NEEDS_HUMAN = "NEEDS_HUMAN"
    BLOCKED = "BLOCKED"
    CONTRACT_READY = "CONTRACT_READY"
    APPROVAL_PENDING = "APPROVAL_PENDING"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    VERIFYING = "VERIFYING"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"
    HANDOFF_WRITING = "HANDOFF_WRITING"
    HANDOFF_VERIFIED = "HANDOFF_VERIFIED"
    COMPLETE = "COMPLETE"
    DENIED = "DENIED"


class EvidenceRef(BaseModel):
    evidence_id: str
    tool_name: str
    entity_urn: str | None = None
    arguments: dict[str, Any] = Field(default_factory=dict)
    retrieved_at: str = Field(default_factory=utc_now)
    result_digest: str
    summary: str
    raw_excerpt: str = ""

    @classmethod
    def from_tool(
        cls,
        *,
        index: int,
        tool_name: str,
        arguments: dict[str, Any],
        result: Any,
        entity_urn: str | None = None,
    ):
        raw = stable_text(result)
        return cls(
            evidence_id=f"ev_{index:03d}",
            tool_name=tool_name,
            entity_urn=entity_urn,
            arguments=arguments,
            result_digest="sha256:" + sha256(raw.encode()).hexdigest(),
            summary=f"DataHub MCP tool {tool_name} returned context"
            + (f" for {entity_urn}" if entity_urn else ""),
            raw_excerpt=raw[:6000],
        )


class Claim(BaseModel):
    claim_id: str
    statement: str
    kind: Literal["fact", "inference", "unknown"]
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    blocks_execution: bool = False


class RealitySnapshot(BaseModel):
    facts: list[Claim] = Field(default_factory=list)
    inferences: list[Claim] = Field(default_factory=list)
    unknowns: list[Claim] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    target_urn: str | None = None


class GateResult(BaseModel):
    decision: Literal["READY", "NEEDS_CONTEXT", "NEEDS_HUMAN", "BLOCKED"]
    reason: str
    blocking_items: list[str] = Field(default_factory=list)


class ExpectedMutation(BaseModel):
    tool: str
    target_urn: str
    expected_marker: str
    semantic_effect: str


class ExecutionContract(BaseModel):
    contract_id: str
    goal: str
    target_urns: list[str]
    evidence_dependencies: list[str]
    allowed_tools: list[str]
    prohibited_tools: list[str]
    expected_mutation: ExpectedMutation
    handoff_tool: str = "save_document"
    handoff_fallback_tool: str = "update_description"
    handoff_document_type: str = "Decision"
    acceptance_tests: list[str]
    stop_conditions: list[str]
    human_approval_required: bool = True

    @model_validator(mode="after")
    def mutation_is_bounded(self):
        if self.expected_mutation.tool not in self.allowed_tools:
            raise ValueError("expected mutation tool must be explicitly allowed")
        if self.expected_mutation.target_urn not in self.target_urns:
            raise ValueError("expected mutation target must be contract-scoped")
        if self.handoff_tool not in self.allowed_tools:
            raise ValueError("handoff tool must be explicitly allowed")
        if self.handoff_fallback_tool not in self.allowed_tools:
            raise ValueError("handoff fallback tool must be explicitly allowed")
        return self


class ActionPlan(BaseModel):
    tool: Literal["update_description"] = "update_description"
    target_urn: str
    description_append: str
    marker: str
    evidence_ids: list[str]
    rationale: str


class VerificationResult(BaseModel):
    verdict: Literal["VERIFIED", "FAILED", "VERIFIED_NOOP"]
    checks: list[dict[str, Any]]
    post_action_evidence_id: str | None = None
    claim_boundary: str = (
        "Verifies the intended DataHub catalog mutation by deterministic MCP re-read; "
        "it does not verify arbitrary downstream warehouse or business semantics."
    )


class HandoffRecord(BaseModel):
    execution_id: str
    task: str
    target_urn: str
    decision: str
    evidence_ids: list[str]
    action: dict[str, Any]
    verification: dict[str, Any]
    unresolved: list[str]
    risks: list[str]
    next_safe_action: str
    created_at: str = Field(default_factory=utc_now)

    def markdown(self) -> str:
        ev = ", ".join(self.evidence_ids) or "none"
        return f"""# Reality Handoff: {self.execution_id}\n\n**Task:** {self.task}\n\n**Target:** `{self.target_urn}`\n\n**Decision:** {self.decision}\n\n**Evidence IDs:** {ev}\n\n## Action\n```json\n{stable_text(self.action)}\n```\n\n## Verification\n```json\n{stable_text(self.verification)}\n```\n\n## Unresolved\n{chr(10).join('- ' + x for x in self.unresolved) if self.unresolved else '- None blocking'}\n\n## Risks\n{chr(10).join('- ' + x for x in self.risks) if self.risks else '- None recorded'}\n\n## Next safe action\n{self.next_safe_action}\n"""


class AgentState(TypedDict, total=False):
    execution_id: str
    task: str
    stage: str
    status: str
    tool_manifest: dict[str, Any]
    evidence: list[dict[str, Any]]
    context_errors: list[str]
    entity_urns: list[str]
    target_urn: str
    reality: dict[str, Any]
    gate: dict[str, Any]
    contract: dict[str, Any]
    action_plan: dict[str, Any]
    before_entity_text: str
    action_result: str
    verification: dict[str, Any]
    handoff: dict[str, Any]
    handoff_location: dict[str, Any]
    handoff_recovery: dict[str, Any]
    error: str


def stable_text(value: Any) -> str:
    import json

    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    except Exception:
        return str(value)

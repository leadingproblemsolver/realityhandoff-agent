from __future__ import annotations
from hashlib import sha256
from .models import ExecutionContract, ExpectedMutation, EvidenceRef, GateResult


def build_contract(
    *,
    execution_id: str,
    task: str,
    target_urn: str,
    evidence: list[EvidenceRef],
    gate: GateResult,
) -> ExecutionContract:
    if gate.decision != "READY":
        raise ValueError("Execution Contract can only be created for READY reality")
    if not target_urn:
        raise ValueError("Execution Contract requires an evidence-resolved target URN")
    marker = "[Reality-Handoff:" + sha256((task + target_urn).encode()).hexdigest()[:12] + "]"
    return ExecutionContract(
        contract_id=f"contract_{execution_id}",
        goal=task,
        target_urns=[target_urn],
        evidence_dependencies=[e.evidence_id for e in evidence],
        allowed_tools=["update_description", "get_entities", "save_document"],
        prohibited_tools=[
            "remove_tags",
            "remove_terms",
            "remove_owners",
            "remove_domains",
            "set_lifecycle_stage",
            "create_glossary_term",
            "accept_or_reject_proposals",
        ],
        expected_mutation=ExpectedMutation(
            tool="update_description",
            target_urn=target_urn,
            expected_marker=marker,
            semantic_effect=(
                "Append an evidence-backed Reality Handoff provenance note to the selected "
                "DataHub entity description without replacing existing metadata."
            ),
        ),
        handoff_tool="save_document",
        handoff_fallback_tool="update_description",
        handoff_document_type="Decision",
        acceptance_tests=[
            "target URN is evidence-resolved by get_entities",
            "upstream and downstream lineage are read through DataHub MCP",
            "mutation tool is allowlisted and human-approved",
            "unique action marker appears after an independent MCP re-read",
            "a Reality Handoff Decision document is written to DataHub when save_document is available",
            "a fresh agent can retrieve the durable handoff without chat history",
        ],
        stop_conditions=[
            "unsupported or unresolvable factual claim",
            "blocking semantic unknown",
            "required MCP context read fails",
            "target outside DEMO_TARGET_URN scope",
            "MCP mutation tool unavailable",
            "post-action marker absent",
            "handoff write cannot be independently recovered",
        ],
        human_approval_required=True,
    )

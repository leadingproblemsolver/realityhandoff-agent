from __future__ import annotations
import asyncio
import uuid
from .config import settings
from .contracts import build_contract
from .evidence import add_evidence, choose_dataset_urn, extract_urns
from .gates import evaluate_reality
from .handoff import build_handoff, compact_handoff_append
from .models import (
    ActionPlan,
    AgentState,
    EvidenceRef,
    ExecutionContract,
    GateResult,
    RealitySnapshot,
    Stage,
    VerificationResult,
    stable_text,
)
from .planner import plan_action
from .reality import compile_reality
from .security import redact
from .verifier import verify_mutation
from . import mcp_runtime


async def intake_node(state: AgentState) -> dict:
    task = str(state.get("task", "")).strip()
    if not task:
        return {
            "execution_id": state.get("execution_id") or f"rh_{uuid.uuid4().hex[:12]}",
            "stage": Stage.FAILED.value,
            "status": "INVALID_TASK",
            "error": "A non-empty task is required.",
        }
    return {
        "execution_id": state.get("execution_id") or f"rh_{uuid.uuid4().hex[:12]}",
        "task": task,
        "stage": Stage.RECEIVED.value,
        "status": "RECEIVED",
    }


async def preflight_node(state: AgentState) -> dict:
    try:
        manifest = await mcp_runtime.capability_manifest()
        missing = manifest["missing_required_read"]
        if missing:
            return {
                "stage": Stage.FAILED.value,
                "status": "MCP_CAPABILITY_BLOCKED",
                "tool_manifest": manifest,
                "error": "Missing required DataHub MCP read tools: " + ", ".join(missing),
            }
        return {
            "stage": Stage.MCP_PREFLIGHT.value,
            "status": "DATAHUB_MCP_READY",
            "tool_manifest": manifest,
        }
    except Exception as exc:
        return {
            "stage": Stage.FAILED.value,
            "status": "DATAHUB_MCP_UNREACHABLE",
            "error": redact(str(exc)),
        }


async def context_node(state: AgentState) -> dict:
    evidence: list[EvidenceRef] = []
    errors: list[str] = []
    task = state["task"]
    try:
        search_args = {"query": task}
        search = await mcp_runtime.invoke("search", search_args)
        add_evidence(evidence, "search", search_args, search)
        urns = extract_urns(search)[: settings.max_context_entities]

        forced = settings.demo_target_urn.strip()
        if forced:
            # A configured demo target is allowed as an explicit scope, but it is not trusted until
            # get_entities proves the entity exists and is readable from DataHub.
            target = forced
        else:
            target = choose_dataset_urn(urns)
        if not target:
            return {
                "stage": Stage.NEEDS_CONTEXT.value,
                "status": "NO_ENTITY_RESOLVED",
                "evidence": [e.model_dump() for e in evidence],
                "entity_urns": urns,
                "context_errors": ["Search did not resolve an actionable DataHub entity URN."],
            }

        # Required proof reads. Any failure blocks action; errors never become factual evidence.
        required_reads = [
            ("get_entities", {"urns": [target], "urn": target}),
            ("list_schema_fields", {"urn": target}),
            ("get_lineage", {"urn": target, "upstream": True}),
            ("get_lineage", {"urn": target, "upstream": False}),
        ]
        raw_by_tool: dict[str, str] = {}
        for name, args in required_reads:
            try:
                result = await mcp_runtime.invoke(name, args)
                raw_by_tool[f"{name}:{args.get('upstream', '')}"] = stable_text(result)
                add_evidence(evidence, name, args, result, target)
            except Exception as exc:
                errors.append(f"{name} failed: {redact(str(exc))}")

        entity_text = raw_by_tool.get("get_entities:", "")
        if not entity_text or errors:
            return {
                "stage": Stage.NEEDS_CONTEXT.value,
                "status": "REQUIRED_CONTEXT_READ_FAILED",
                "evidence": [e.model_dump() for e in evidence],
                "entity_urns": urns,
                "target_urn": target,
                "context_errors": errors or ["get_entities returned no usable entity context"],
            }
        if target not in entity_text:
            return {
                "stage": Stage.NEEDS_CONTEXT.value,
                "status": "TARGET_NOT_PROVEN",
                "evidence": [e.model_dump() for e in evidence],
                "entity_urns": urns,
                "target_urn": target,
                "context_errors": ["Configured/selected target URN was not present in get_entities evidence."],
            }

        if "search_documents" in state.get("tool_manifest", {}).get("tools", []):
            try:
                args = {"query": task}
                result = await mcp_runtime.invoke("search_documents", args)
                add_evidence(evidence, "search_documents", args, result, target)
            except Exception as exc:
                # Document search enriches semantics but is not required for the positive demo path.
                errors.append(f"optional search_documents failed: {redact(str(exc))}")

        return {
            "stage": Stage.CONTEXT_BUILDING.value,
            "status": "CONTEXT_READY",
            "evidence": [e.model_dump() for e in evidence],
            "entity_urns": urns,
            "target_urn": target,
            "before_entity_text": entity_text,
            "context_errors": errors,
        }
    except Exception as exc:
        return {
            "stage": Stage.FAILED.value,
            "status": "CONTEXT_FAILED",
            "error": redact(str(exc)),
            "evidence": [e.model_dump() for e in evidence],
            "context_errors": errors,
        }


async def reality_node(state: AgentState) -> dict:
    try:
        evidence = [EvidenceRef.model_validate(e) for e in state.get("evidence", [])]
        reality = await compile_reality(state["task"], evidence, state.get("target_urn"))
        return {
            "stage": Stage.REALITY_COMPILED.value,
            "status": "REALITY_COMPILED",
            "reality": reality.model_dump(),
        }
    except Exception as exc:
        return {
            "stage": Stage.FAILED.value,
            "status": "REALITY_FAILED",
            "error": redact(str(exc)),
        }


def gate_node(state: AgentState) -> dict:
    try:
        reality = RealitySnapshot.model_validate(state["reality"])
        valid_ids = {e["evidence_id"] for e in state.get("evidence", []) if e.get("evidence_id")}
        gate = evaluate_reality(reality, valid_ids)
        return {"stage": gate.decision, "status": gate.decision, "gate": gate.model_dump()}
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "GATE_FAILED", "error": redact(str(exc))}


def contract_node(state: AgentState) -> dict:
    try:
        gate = GateResult.model_validate(state["gate"])
        evidence = [EvidenceRef.model_validate(e) for e in state.get("evidence", [])]
        manifest = state.get("tool_manifest", {})
        if manifest.get("missing_required_action"):
            raise RuntimeError(
                "READY execution requires DataHub MCP update_description; enable "
                "TOOLS_IS_MUTATION_ENABLED via DATAHUB_SERVER_MUTATIONS_ENABLED=true"
            )
        contract = build_contract(
            execution_id=state["execution_id"],
            task=state["task"],
            target_urn=state["target_urn"],
            evidence=evidence,
            gate=gate,
        )
        if settings.demo_target_urn and contract.expected_mutation.target_urn != settings.demo_target_urn:
            raise PermissionError("Execution Contract target is outside DEMO_TARGET_URN scope")
        return {
            "stage": Stage.CONTRACT_READY.value,
            "status": "CONTRACT_READY",
            "contract": contract.model_dump(),
        }
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "CONTRACT_FAILED", "error": redact(str(exc))}


async def plan_node(state: AgentState) -> dict:
    try:
        contract = ExecutionContract.model_validate(state["contract"])
        evidence = [EvidenceRef.model_validate(e) for e in state.get("evidence", [])]
        plan = await plan_action(contract, evidence)
        return {
            "stage": Stage.APPROVAL_PENDING.value,
            "status": "APPROVAL_PENDING",
            "action_plan": plan.model_dump(),
        }
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "PLAN_FAILED", "error": redact(str(exc))}


def approval_node(state: AgentState) -> dict:
    from langgraph.types import interrupt

    if settings.require_human_approval:
        approved = interrupt(
            {
                "type": "human_approval",
                "message": (
                    "Approve the bounded DataHub metadata mutation and, only after deterministic "
                    "verification, its durable Reality Handoff write-back?"
                ),
                "contract": state["contract"],
                "action_plan": state["action_plan"],
            }
        )
    else:
        approved = True
    if approved is not True:
        return {"stage": Stage.DENIED.value, "status": "DENIED"}
    return {"stage": Stage.APPROVAL_PENDING.value, "status": "APPROVED"}


async def action_node(state: AgentState) -> dict:
    try:
        plan = ActionPlan.model_validate(state["action_plan"])
        contract = ExecutionContract.model_validate(state["contract"])
        if plan.tool not in contract.allowed_tools or plan.target_urn not in contract.target_urns:
            raise PermissionError("ActionPlan escaped the approved Execution Contract")
        before = state.get("before_entity_text", "")
        if plan.marker in before:
            return {
                "stage": Stage.ACTION_EXECUTED.value,
                "status": "IDEMPOTENT_NOOP",
                "action_result": "Marker already present; mutation skipped.",
            }
        result = await mcp_runtime.invoke(
            "update_description",
            {"urn": plan.target_urn, "description": plan.description_append, "mode": "append"},
            mutation=True,
        )
        return {
            "stage": Stage.ACTION_EXECUTED.value,
            "status": "ACTION_EXECUTED",
            "action_result": stable_text(result)[:4000],
        }
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "ACTION_FAILED", "error": redact(str(exc))}


async def verify_node(state: AgentState) -> dict:
    try:
        plan = ActionPlan.model_validate(state["action_plan"])
        evidence = [EvidenceRef.model_validate(e) for e in state.get("evidence", [])]
        args = {"urns": [plan.target_urn], "urn": plan.target_urn}
        result = await mcp_runtime.invoke("get_entities", args)
        full_after_text = stable_text(result)
        post = add_evidence(evidence, "get_entities", args, result, plan.target_urn)
        verification = verify_mutation(
            marker=plan.marker,
            target_urn=plan.target_urn,
            before_text=state.get("before_entity_text", ""),
            after_text=full_after_text,
            post_evidence=post,
        )
        return {
            "stage": Stage.VERIFIED.value if verification.verdict != "FAILED" else Stage.FAILED.value,
            "status": verification.verdict,
            "verification": verification.model_dump(),
            "evidence": [e.model_dump() for e in evidence],
        }
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "VERIFY_FAILED", "error": redact(str(exc))}


async def handoff_node(state: AgentState) -> dict:
    try:
        evidence = [EvidenceRef.model_validate(e) for e in state.get("evidence", [])]
        plan = ActionPlan.model_validate(state["action_plan"])
        verification = VerificationResult.model_validate(state["verification"])
        reality = RealitySnapshot.model_validate(state["reality"])
        contract = ExecutionContract.model_validate(state["contract"])
        if verification.verdict not in {"VERIFIED", "VERIFIED_NOOP"}:
            raise PermissionError("Handoff write is forbidden until mutation verification passes")
        handoff = build_handoff(
            execution_id=state["execution_id"],
            task=state["task"],
            target_urn=state["target_urn"],
            evidence=evidence,
            action=plan,
            verification=verification,
            unresolved=[u.statement for u in reality.unknowns],
        )
        tools = state.get("tool_manifest", {}).get("tools", [])
        if contract.handoff_tool == "save_document" and "save_document" in tools:
            try:
                result = await mcp_runtime.invoke(
                    "save_document",
                    {
                        "document_type": contract.handoff_document_type,
                        "title": f"Reality Handoff {state['execution_id']}",
                        "content": handoff.markdown(),
                        "related_assets": [handoff.target_urn],
                    },
                    mutation=True,
                )
                return {
                    "stage": Stage.HANDOFF_WRITING.value,
                    "status": "HANDOFF_WRITTEN",
                    "handoff": handoff.model_dump(),
                    "handoff_location": {
                        "kind": "datahub_document",
                        "urn": next((u for u in extract_urns(result) if u.startswith("urn:li:document")), None),
                        "result": stable_text(result)[:2000],
                    },
                }
            except Exception as exc:
                fallback_error = redact(str(exc))
        else:
            fallback_error = "save_document tool unavailable"

        # Transparent continuity fallback: append a compact record to the same already-approved target.
        compact = compact_handoff_append(handoff)
        result = await mcp_runtime.invoke(
            "update_description",
            {"urn": handoff.target_urn, "description": compact, "mode": "append"},
            mutation=True,
        )
        reread = await mcp_runtime.invoke(
            "get_entities", {"urns": [handoff.target_urn], "urn": handoff.target_urn}
        )
        marker = f"[Reality-Handoff-Record:{handoff.execution_id}]"
        if marker not in stable_text(reread):
            return {
                "stage": Stage.FAILED.value,
                "status": "HANDOFF_WRITE_FAILED",
                "error": "Handoff fallback marker absent after MCP re-read; " + fallback_error,
            }
        return {
            "stage": Stage.HANDOFF_WRITING.value,
            "status": "HANDOFF_WRITTEN_FALLBACK",
            "handoff": handoff.model_dump(),
            "handoff_location": {
                "kind": "entity_description",
                "urn": handoff.target_urn,
                "reason": fallback_error,
                "write_result": stable_text(result)[:1000],
            },
        }
    except Exception as exc:
        return {"stage": Stage.FAILED.value, "status": "HANDOFF_FAILED", "error": redact(str(exc))}


async def handoff_verify_node(state: AgentState) -> dict:
    """Independently prove that continuity state is readable from DataHub after write-back."""
    try:
        execution_id = state["execution_id"]
        target_urn = state["target_urn"]
        location = state.get("handoff_location", {})
        kind = location.get("kind")
        if kind == "datahub_document" and location.get("urn"):
            document_urn = location["urn"]
            result = await mcp_runtime.invoke("get_entities", {"urns": [document_urn], "urn": document_urn})
            text = stable_text(result)
            if f"Reality Handoff: {execution_id}" not in text:
                return {
                    "stage": Stage.FAILED.value,
                    "status": "HANDOFF_VERIFY_FAILED",
                    "error": "Saved DataHub document was re-read but did not contain the execution ID.",
                }
            return {
                "stage": Stage.HANDOFF_VERIFIED.value,
                "status": "HANDOFF_VERIFIED",
                "handoff_recovery": {"source": "datahub_document", "urn": document_urn},
            }

        if kind == "datahub_document":
            # Some server versions do not return a document URN from save_document. Rediscover
            # tools after the first document is created, then search by the unique title.
            # Search indexing may be eventually consistent, so retry only this read-only lookup
            # a bounded number of times. The graph still fails closed if the record is not found.
            await mcp_runtime.refresh_tools()
            tools = await mcp_runtime.get_tools()
            title = f"Reality Handoff {execution_id}"
            if "search_documents" in tools:
                for attempt in range(3):
                    result = await mcp_runtime.invoke("search_documents", {"query": title})
                    # DataHub document search returns metadata, not the document body. Resolve
                    # the returned document URN(s), then independently read the actual content.
                    document_urns = [
                        u for u in extract_urns(result) if u.startswith("urn:li:document:")
                    ]
                    for document_urn in document_urns[:3]:
                        document = await mcp_runtime.invoke(
                            "get_entities", {"urns": [document_urn], "urn": document_urn}
                        )
                        document_text = stable_text(document)
                        if f"Reality Handoff: {execution_id}" in document_text:
                            return {
                                "stage": Stage.HANDOFF_VERIFIED.value,
                                "status": "HANDOFF_VERIFIED",
                                "handoff_recovery": {
                                    "source": "search_documents_then_get_entities",
                                    "urn": document_urn,
                                    "attempts": attempt + 1,
                                },
                            }
                    if attempt < 2:
                        await asyncio.sleep(0.5 * (attempt + 1))
            return {
                "stage": Stage.FAILED.value,
                "status": "HANDOFF_VERIFY_FAILED",
                "error": "save_document returned success but the handoff could not be independently re-read.",
            }

        # Fallback records are deliberately stored on the already-approved target description.
        result = await mcp_runtime.invoke("get_entities", {"urns": [target_urn], "urn": target_urn})
        marker = f"[Reality-Handoff-Record:{execution_id}]"
        if marker not in stable_text(result):
            return {
                "stage": Stage.FAILED.value,
                "status": "HANDOFF_VERIFY_FAILED",
                "error": "Fallback handoff record was not found on independent target re-read.",
            }
        return {
            "stage": Stage.HANDOFF_VERIFIED.value,
            "status": "HANDOFF_VERIFIED_FALLBACK",
            "handoff_recovery": {"source": "entity_description", "urn": target_urn},
        }
    except Exception as exc:
        return {
            "stage": Stage.FAILED.value,
            "status": "HANDOFF_VERIFY_FAILED",
            "error": redact(str(exc)),
        }


def terminal_node(state: AgentState) -> dict:
    terminal = state.get("stage")
    if terminal in {
        Stage.HANDOFF_VERIFIED.value,
        Stage.DENIED.value,
        Stage.NEEDS_HUMAN.value,
        Stage.NEEDS_CONTEXT.value,
        Stage.BLOCKED.value,
        Stage.FAILED.value,
    }:
        return {"stage": Stage.COMPLETE.value, "status": state.get("status", terminal)}
    return {"stage": Stage.COMPLETE.value, "status": "COMPLETE"}

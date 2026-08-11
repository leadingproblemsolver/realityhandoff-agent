from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from .contracts import build_contract
from .evidence import add_evidence
from .gates import evaluate_reality
from .handoff import build_handoff
from .models import RealitySnapshot, Claim, ActionPlan
from .verifier import verify_mutation


@dataclass
class ReplayCatalog:
    urn: str = "urn:li:dataset:(urn:li:dataPlatform:snowflake,showcase.orders,PROD)"
    description: str = "Canonical order-level transaction dataset."
    saved_documents: dict[str, str] = field(default_factory=dict)
    mutation_count: int = 0

    def search(self, query):
        return {"results": [{"urn": self.urn, "name": "orders"}]}

    def get_entities(self):
        return {
            "urn": self.urn,
            "description": self.description,
            "owners": ["urn:li:corpuser:data-platform"],
        }

    def schema(self):
        return {
            "urn": self.urn,
            "fields": [
                {"fieldPath": "order_id", "type": "STRING"},
                {"fieldPath": "customer_id", "type": "STRING"},
                {"fieldPath": "order_total", "type": "DECIMAL"},
            ],
        }

    def lineage(self, upstream: bool):
        if upstream:
            return {
                "urn": self.urn,
                "upstream": [
                    "urn:li:dataset:(urn:li:dataPlatform:snowflake,raw.orders,PROD)"
                ],
            }
        return {
            "urn": self.urn,
            "downstream": ["urn:li:dashboard:(looker,customer_orders)"]
        }

    def append_description(self, text):
        if text not in self.description:
            self.description += "\n\n" + text
            self.mutation_count += 1

    def save_document(self, title, content):
        self.saved_documents[title] = content


def run_replay(*, task: str, ambiguous: bool = False, tamper_after: bool = False) -> dict[str, Any]:
    catalog = ReplayCatalog()
    evidence = []
    add_evidence(evidence, "search", {"query": task}, catalog.search(task))
    add_evidence(evidence, "get_entities", {"urns": [catalog.urn]}, catalog.get_entities(), catalog.urn)
    add_evidence(evidence, "list_schema_fields", {"urn": catalog.urn}, catalog.schema(), catalog.urn)
    add_evidence(evidence, "get_lineage", {"urn": catalog.urn, "upstream": True}, catalog.lineage(True), catalog.urn)
    add_evidence(evidence, "get_lineage", {"urn": catalog.urn, "upstream": False}, catalog.lineage(False), catalog.urn)

    facts = [
        Claim(
            claim_id=f"f{i}",
            statement=e.summary,
            kind="fact",
            evidence_ids=[e.evidence_id],
            confidence=1,
        )
        for i, e in enumerate(evidence, 1)
    ]
    unknowns = (
        [
            Claim(
                claim_id="u1",
                statement="Authoritative definition of 'revenue' is unresolved.",
                kind="unknown",
                blocks_execution=True,
            )
        ]
        if ambiguous
        else []
    )
    reality = RealitySnapshot(facts=facts, unknowns=unknowns, target_urn=catalog.urn)
    gate = evaluate_reality(reality, {e.evidence_id for e in evidence})
    output = {"gate": gate.model_dump(), "mutations": 0, "evidence_count": len(evidence)}
    if gate.decision != "READY":
        return output

    contract = build_contract(
        execution_id="replay001",
        task=task,
        target_urn=catalog.urn,
        evidence=evidence,
        gate=gate,
    )
    marker = contract.expected_mutation.expected_marker
    plan = ActionPlan(
        target_urn=catalog.urn,
        description_append=marker + "\nEvidence-backed continuity note.",
        marker=marker,
        evidence_ids=contract.evidence_dependencies,
        rationale="replay",
    )
    before = str(catalog.get_entities())
    catalog.append_description(plan.description_append)
    if tamper_after:
        catalog.description = catalog.description.replace(marker, "[tampered]")
    post_result = catalog.get_entities()
    post = add_evidence(evidence, "get_entities", {"urns": [catalog.urn]}, post_result, catalog.urn)
    verification = verify_mutation(
        marker=marker,
        target_urn=catalog.urn,
        before_text=before,
        after_text=str(post_result),
        post_evidence=post,
    )
    if verification.verdict != "FAILED":
        handoff = build_handoff(
            execution_id="replay001",
            task=task,
            target_urn=catalog.urn,
            evidence=evidence,
            action=plan,
            verification=verification,
            unresolved=[],
        )
        catalog.save_document("Reality Handoff replay001", handoff.markdown())
        output["handoff_recovered"] = (
            "replay001" in catalog.saved_documents["Reality Handoff replay001"]
        )
    output.update(
        {
            "verification": verification.model_dump(),
            "mutations": catalog.mutation_count,
            "description": catalog.description,
        }
    )
    return output

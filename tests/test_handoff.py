from reality_handoff.handoff import build_handoff
from reality_handoff.models import ActionPlan, VerificationResult, EvidenceRef

def test_handoff_is_self_contained():
    e=EvidenceRef(evidence_id="ev1",tool_name="search",result_digest="sha256:x",summary="x")
    a=ActionPlan(target_urn="urn:li:dataset:x",description_append="[RH] x",marker="[RH]",evidence_ids=["ev1"],rationale="r")
    v=VerificationResult(verdict="VERIFIED",checks=[])
    h=build_handoff(execution_id="e1",task="t",target_urn=a.target_urn,evidence=[e],action=a,verification=v,unresolved=[])
    text=h.markdown()
    assert "e1" in text and "ev1" in text and "Next safe action" in text

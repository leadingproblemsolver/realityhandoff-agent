import json

from reality_handoff.models import EvidenceRef
from reality_handoff.verifier import verify_mutation

TARGET = "urn:li:dataset:x"
OTHER = "urn:li:dataset:y"


def ev(entity_urn=TARGET):
    return EvidenceRef(
        evidence_id="ev_9",
        tool_name="get_entities",
        entity_urn=entity_urn,
        result_digest="sha256:x",
        summary="post",
    )


def response(*entities):
    return json.dumps(list(entities))


def entity(urn, description, **extra):
    return {"urn": urn, "editableProperties": {"description": description}, **extra}


def verify(before, after, post=None):
    return verify_mutation(
        marker="[RH]",
        target_urn=TARGET,
        before_text=before,
        after_text=after,
        post_evidence=post or ev(),
    ).verdict


def test_verifies_exact_marker():
    assert verify(response(entity(TARGET, "a")), response(entity(TARGET, "a [RH]"))) == "VERIFIED"


def test_missing_marker_fails():
    assert verify(response(entity(TARGET, "a")), response(entity(TARGET, "a"))) == "FAILED"


def test_wrong_target_fails():
    before = response(entity(TARGET, "a"))
    after = response(entity(OTHER, "a [RH]"))
    assert verify(before, after, ev(OTHER)) == "FAILED"


def test_existing_marker_is_idempotent():
    assert (
        verify(response(entity(TARGET, "a [RH]")), response(entity(TARGET, "a [RH]")))
        == "VERIFIED_NOOP"
    )


def test_cross_entity_marker_fails():
    before = response(entity(TARGET, "a"))
    after = response(entity(TARGET, "unchanged"), entity(OTHER, "[RH]"))
    assert verify(before, after) == "FAILED"


def test_marker_in_related_entity_metadata_fails():
    after = response(
        {
            "urn": TARGET,
            "editableProperties": {"description": "unchanged"},
            "ownership": {"owners": [{"urn": OTHER, "properties": {"description": "[RH]"}}]},
        }
    )
    assert verify(response(entity(TARGET, "a")), after) == "FAILED"


def test_target_error_fails_even_with_marker():
    after = response(
        {"urn": TARGET, "error": "not found", "editableProperties": {"description": "[RH]"}}
    )
    assert verify(response(entity(TARGET, "a")), after) == "FAILED"


def test_duplicate_target_fails():
    after = response(entity(TARGET, "[RH]"), entity(TARGET, "[RH]"))
    assert verify(response(entity(TARGET, "a")), after) == "FAILED"


def test_unstructured_response_fails_closed():
    assert verify("a", f"{TARGET} a [RH]") == "FAILED"


def test_mcp_text_content_wrapper():
    after = json.dumps([{"type": "text", "text": response(entity(TARGET, "a [RH]"))}])
    assert verify(response(entity(TARGET, "a")), after) == "VERIFIED"


def test_target_marker_only_in_properties_works():
    after = response({"urn": TARGET, "properties": {"description": "a [RH]"}})
    assert verify(response(entity(TARGET, "a")), after) == "VERIFIED"


def test_marker_in_other_property_not_description_fails():
    after = response(
        {
            "urn": TARGET,
            "editableProperties": {"description": "a"},
            "properties": {"description": "a [RH]"},
        }
    )
    assert verify(response(entity(TARGET, "a")), after) == "FAILED"


def test_mismatched_post_evidence_fails():
    before = response(entity(TARGET, "a"))
    after = response(entity(TARGET, "a [RH]"))
    assert verify(before, after, ev(OTHER)) == "FAILED"


def test_entities_envelope():
    before = response(entity(TARGET, "a"))
    after = json.dumps({"entities": [entity(TARGET, "a [RH]")]})
    assert verify(before, after) == "VERIFIED"

from pydantic import create_model
from reality_handoff.tool_binding import bind


class ExactUpdate:
    name = "update_description"
    args_schema = create_model(
        "UpdateArgs",
        entity_urn=(str, ...),
        operation=(str, "append"),
        description=(str, ...),
        column_path=(str | None, None),
    )


class ExactSave:
    name = "save_document"
    args_schema = create_model(
        "SaveArgs",
        document_type=(str, ...),
        title=(str, ...),
        content=(str, ...),
        related_assets=(list[str] | None, None),
    )


def test_update_description_official_shape_binding():
    out = bind(
        ExactUpdate(),
        {"urn": "u", "description": "d", "mode": "append"},
    )
    assert out == {"entity_urn": "u", "description": "d", "operation": "append"}


def test_save_document_official_shape_binding():
    out = bind(
        ExactSave(),
        {
            "document_type": "Decision",
            "title": "Reality Handoff e1",
            "content": "body",
            "related_assets": ["urn:li:dataset:x"],
        },
    )
    assert out["document_type"] == "Decision"
    assert out["related_assets"] == ["urn:li:dataset:x"]


def test_binding_fails_closed_when_required_unknown():
    class T:
        name = "mystery"
        args_schema = create_model("MysteryArgs", required_we_do_not_know=(str, ...))

    import pytest

    with pytest.raises(ValueError):
        bind(T(), {"query": "orders"})

class ExactLineage:
    name = "get_lineage"
    args_schema = create_model(
        "LineageArgs",
        urn=(str, ...),
        column=(str | None, None),
        query=(str | None, None),
        filter=(str | None, None),
        upstream=(bool, True),
        max_hops=(int, 1),
        max_results=(int, 30),
        offset=(int, 0),
    )


class ExactEntities:
    name = "get_entities"
    args_schema = create_model("GetEntitiesArgs", urns=(list[str], ...))


class ExactSchemaFields:
    name = "list_schema_fields"
    args_schema = create_model("SchemaFieldsArgs", urn=(str, ...))


class ExactSearch:
    name = "search"
    args_schema = create_model("SearchArgs", query=(str, ...))


def test_get_lineage_official_shape_supports_both_directions():
    assert bind(ExactLineage(), {"urn": "u", "upstream": True}) == {"urn": "u", "upstream": True}
    assert bind(ExactLineage(), {"urn": "u", "upstream": False}) == {"urn": "u", "upstream": False}


def test_required_read_tool_shapes_bind_without_extra_arguments():
    assert bind(ExactEntities(), {"urns": ["u"], "urn": "u"}) == {"urns": ["u"]}
    assert bind(ExactSchemaFields(), {"urn": "u"}) == {"urn": "u"}
    assert bind(ExactSearch(), {"query": "orders"}) == {"query": "orders"}

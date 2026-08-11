from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_frontend_has_required_judge_actions_and_no_secret_inputs():
    html = (ROOT / "src/reality_handoff/static/index.html").read_text()
    js = (ROOT / "src/reality_handoff/static/app.js").read_text()
    for phrase in [
        "Run Reality Handoff",
        "Approve bounded action",
        "Reject",
        "Start Fresh Agent",
        "Live DataHub",
        "Fixture proof",
    ]:
        assert phrase in html
    for route in ["/api/runs", "/api/recovery", "/api/capabilities"]:
        assert route in js
    assert "approved?'approve':'reject'" in js
    forbidden = ["DATAHUB_GMS_TOKEN", "OPENAI_API_KEY", "LANGSMITH_API_KEY"]
    assert all(token not in html for token in forbidden)


def test_frontend_does_not_infer_gate_from_model_prose():
    js = (ROOT / "src/reality_handoff/static/app.js").read_text()
    assert "run.gate?.decision" in js
    assert "action_plan" in js
    assert "verification" in js

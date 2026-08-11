from fastapi.testclient import TestClient

from reality_handoff.webapp import app

client = TestClient(app)


def test_demo_is_product_surface_and_transparent_about_fixture_mode():
    r = client.get("/demo")
    assert r.status_code == 200
    assert "Proof-carrying actions that survive the agent session" in r.text
    assert "Fixture proof" in r.text
    assert "Live DataHub" in r.text
    assert "Start Fresh Agent" in r.text
    assert "DATAHUB_GMS_TOKEN" not in r.text


def test_health_never_returns_secrets():
    r = client.get("/api/health")
    assert r.status_code == 200
    text = r.text
    assert "DATAHUB_GMS_TOKEN" not in text
    assert "OPENAI_API_KEY" not in text
    assert "LANGSMITH_API_KEY" not in text
    assert "human_approval_required" in text


def test_replay_route_positive():
    r = client.post(
        "/api/replay",
        json={"task": "inspect canonical customer orders", "ambiguous": False},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["gate"]["decision"] == "READY"
    assert body["verification"]["verdict"] == "VERIFIED"
    assert body["handoff_recovered"] is True


def test_replay_route_negative_control():
    r = client.post(
        "/api/replay", json={"task": "fix revenue definition", "ambiguous": True}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["gate"]["decision"] == "NEEDS_HUMAN"
    assert body["mutations"] == 0


def test_live_run_routes_preserve_backend_contract(monkeypatch):
    import reality_handoff.webapp as webapp

    waiting = {
        "found": True,
        "execution_id": "rh_test",
        "stage": "APPROVAL_PENDING",
        "status": "APPROVAL_PENDING",
        "requires_approval": True,
        "contract": {"contract_id": "contract_rh_test"},
        "action_plan": {"tool": "update_description"},
    }
    approved = {
        **waiting,
        "stage": "COMPLETE",
        "status": "HANDOFF_VERIFIED",
        "requires_approval": False,
    }

    async def fake_start(task):
        assert task == "inspect orders"
        return waiting

    async def fake_get(execution_id):
        assert execution_id == "rh_test"
        return waiting

    async def fake_decide(execution_id, decision):
        assert execution_id == "rh_test"
        assert decision is True
        return approved

    class Runtime:
        start_run = staticmethod(fake_start)
        get_run = staticmethod(fake_get)
        decide_run = staticmethod(fake_decide)

    monkeypatch.setattr(webapp, "_runtime", lambda: Runtime)

    r = client.post("/api/runs", json={"task": "inspect orders"})
    assert r.status_code == 201
    assert r.json()["requires_approval"] is True

    r = client.get("/api/runs/rh_test")
    assert r.status_code == 200
    assert r.json()["execution_id"] == "rh_test"

    r = client.post("/api/runs/rh_test/approve")
    assert r.status_code == 200
    assert r.json()["status"] == "HANDOFF_VERIFIED"


def test_recovery_route_is_fresh_backend_read(monkeypatch):
    import reality_handoff.webapp as webapp

    async def fake_recover(execution_id, target_urn):
        return {
            "source": "datahub_document",
            "execution_id": execution_id,
            "document_urn": "urn:li:document:test",
        }

    class Runtime:
        recover_handoff = staticmethod(fake_recover)

    monkeypatch.setattr(webapp, "_runtime", lambda: Runtime)
    r = client.post(
        "/api/recovery",
        json={"execution_id": "rh_test", "target_urn": "urn:li:dataset:test"},
    )
    assert r.status_code == 200
    assert r.json()["source"] == "datahub_document"

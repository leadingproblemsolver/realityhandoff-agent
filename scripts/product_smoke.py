"""Credential-free product smoke for the judge-facing surface."""
from fastapi.testclient import TestClient
from reality_handoff.webapp import app

client = TestClient(app)

root = client.get("/")
assert root.status_code == 200
assert "Run Reality Handoff" in root.text

positive = client.post(
    "/api/replay",
    json={"task": "inspect canonical customer orders", "ambiguous": False},
)
assert positive.status_code == 200
assert positive.json()["verification"]["verdict"] == "VERIFIED"
assert positive.json()["handoff_recovered"] is True

negative = client.post(
    "/api/replay",
    json={"task": "fix revenue definition", "ambiguous": True},
)
assert negative.status_code == 200
assert negative.json()["gate"]["decision"] == "NEEDS_HUMAN"
assert negative.json()["mutations"] == 0

print("PASS: product root + positive fixture + refusal fixture")

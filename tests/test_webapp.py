from fastapi.testclient import TestClient
from reality_handoff.webapp import app

client = TestClient(app)


def test_demo_is_interactive_and_transparent_about_replay():
    r = client.get('/demo')
    assert r.status_code == 200
    assert 'Safe interactive evaluator' in r.text
    assert 'not</b> presented as live DataHub evidence' in r.text


def test_replay_route_positive():
    r = client.post('/api/replay', json={'task': 'inspect canonical customer orders', 'ambiguous': False})
    assert r.status_code == 200
    body = r.json()
    assert body['gate']['decision'] == 'READY'
    assert body['verification']['verdict'] == 'VERIFIED'
    assert body['handoff_recovered'] is True


def test_replay_route_negative_control():
    r = client.post('/api/replay', json={'task': 'fix revenue definition', 'ambiguous': True})
    assert r.status_code == 200
    body = r.json()
    assert body['gate']['decision'] == 'NEEDS_HUMAN'
    assert body['mutations'] == 0

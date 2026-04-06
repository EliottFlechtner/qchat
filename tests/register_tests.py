from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_register():
    r = client.post(
        "/register", json={"username": "testuser", "kem_pk": "abc", "sig_pk": "xyz"}
    )
    assert r.status_code == 200

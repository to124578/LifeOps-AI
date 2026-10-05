import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["AI_PROVIDER"] = "mock"
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.db import init_db


@pytest.fixture(scope="session")
def client():
    init_db()
    with TestClient(app) as c:
        yield c


H = {"X-Session-Id": "test-session"}


def sample_text(client, sid="offer"):
    return next(s for s in client.get("/api/samples").json() if s["id"] == sid)["text"]


def analyze(client, sid="offer", headers=H):
    r = client.post("/api/analyze/text", json={"text": sample_text(client, sid), "client_now": None}, headers=headers)
    assert r.status_code == 202, r.text
    return r.json()["id"]

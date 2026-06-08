"""Phase 10 API smoke tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from load_api_app import load_api_app

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

app = load_api_app()


def test_health_offline() -> None:
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["offline_mode"] is True


def test_decide_fixture_latency() -> None:
    client = TestClient(app)
    r = client.post(
        "/decide",
        json={"policy": "heuristic", "profile_id": "test"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["latency_ms"] >= 0
    assert len(data["actions"]) >= 1
    assert data["explanation"]


def test_blueprint_yaml() -> None:
    pytest.importorskip("yaml")
    client = TestClient(app)
    r = client.get("/blueprint")
    assert r.status_code == 200
    assert len(r.json()["sections"]) >= 1


def test_jobs_reject_unknown_type() -> None:
    client = TestClient(app)
    r = client.post("/jobs", json={"type": "not_a_real_job", "params": {}})
    assert r.status_code == 400


def test_jobs_create_features_build() -> None:
    client = TestClient(app)
    r = client.post(
        "/jobs",
        json={"type": "features_build", "params": {"output": "features_test.jsonl"}},
    )
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    detail = client.get(f"/jobs/{job_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["type"] == "features_build"
    assert body["status"] in ("queued", "running", "done", "error")
    listed = client.get("/jobs")
    assert listed.status_code == 200
    ids = [j["job_id"] for j in listed.json()["jobs"]]
    assert job_id in ids

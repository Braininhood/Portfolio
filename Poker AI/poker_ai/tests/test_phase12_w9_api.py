"""Phase W9 API — smoke, licenses, compliance, model card."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from load_api_app import load_api_app

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

_PKG_ROOT = Path(__file__).resolve().parents[1]
app = load_api_app()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_licenses_inventory(client: TestClient) -> None:
    r = client.get("/licenses")
    assert r.status_code == 200
    body = r.json()
    assert len(body["entries"]) >= 5
    packages = {e["package"] for e in body["entries"]}
    assert "TexasSolver" in packages
    assert "fastapi" in packages


def test_compliance_summary(client: TestClient) -> None:
    r = client.get("/compliance")
    assert r.status_code == 200
    body = r.json()
    assert body["owned_data_only"] is True
    assert body["no_external_ai_services"] is True
    assert body["licenses_count"] >= 5


def test_compliance_datasheet(client: TestClient) -> None:
    r = client.get("/compliance/datasheet")
    assert r.status_code == 200
    assert "Poker AI" in r.text


def test_compliance_datasheet_content(client: TestClient) -> None:
    r = client.get("/compliance/datasheet/content")
    assert r.status_code == 200
    body = r.json()
    assert body.get("markdown")
    assert "Poker AI" in body["markdown"]


def test_promotion_gates_schema(client: TestClient) -> None:
    r = client.get("/models/student_hu/promotion-gates")
    assert r.status_code == 200
    body = r.json()
    assert "checks" in body
    assert isinstance(body["checks"], list)


def test_health_smoke(client: TestClient) -> None:
    r = client.get("/health/smoke")
    assert r.status_code == 200
    body = r.json()
    assert "checks" in body
    names = {c["name"] for c in body["checks"]}
    assert "db_readable" in names
    assert "equity_spot" in names
    assert "no_outbound_dns" in names


@pytest.mark.parametrize(
    "name,snippet",
    [
        ("hhformer", "HHFormer"),
        ("preflop_hu", "Preflop CFR"),
        ("preflop_6max", "6-max"),
        ("style_encoder", "Style encoder"),
        ("solver_cache", "Solver cache"),
    ],
)
def test_model_card(client: TestClient, name: str, snippet: str) -> None:
    r = client.get(f"/models/{name}/card")
    assert r.status_code == 200, r.text
    assert snippet in r.json()["markdown"]

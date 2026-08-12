"""Integração adicional: Insights sobre o `orders.xlsx` real (239 pedidos).

A matemática "de verdade" já está coberta em `test_insights_routes.py`, com
fixtures pequenas e determinísticas. Este arquivo prova que o fluxo completo
— upload → processamento ETL → Insights — funciona sobre o arquivo real e
bate com números calculados de forma independente (script sobre o próprio
DataFrame transformado, não copiados às cegas). O arquivo fixture não é
alterado.

Período escolhido: os últimos 10 dias com pedidos `completed`
(`2026-07-18..27`) contra os 10 dias imediatos anteriores
(`2026-07-08..17`) — mesma janela que o próprio serviço computaria.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

_FIXTURE_PATH = (
    Path(__file__).parent.parent.parent / "etl" / "tests" / "fixtures" / "shopee" / "orders.xlsx"
)
_VALID_PASSWORD = "Sup3rSecret!"


def _auth_headers(client: TestClient, *, email: str) -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": _VALID_PASSWORD})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": _VALID_PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _process_official_fixture(client: TestClient, headers: dict[str, str]) -> None:
    with _FIXTURE_PATH.open("rb") as file:
        response = client.post(
            "/api/v1/uploads",
            headers=headers,
            files={
                "file": (
                    "orders.xlsx",
                    file.read(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )
    upload_id = response.json()["id"]
    process_response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)
    assert process_response.json()["status"] == "processed"


def test_insights_over_official_fixture_period(client: TestClient) -> None:
    headers = _auth_headers(client, email="official-fixture-insights@example.com")
    _process_official_fixture(client, headers)

    response = client.get(
        "/api/v1/insights",
        headers=headers,
        params={"from": "2026-07-18", "to": "2026-07-27"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["has_data"] is True
    by_type = {insight["type"]: insight for insight in body["insights"]}

    revenue = by_type["revenue_trend"]
    assert revenue["current_value"] == pytest.approx(4765.00)
    assert revenue["previous_value"] == pytest.approx(5932.00)
    assert revenue["value"] == pytest.approx(-19.7, abs=0.05)
    assert revenue["severity"] == "negative"

    orders = by_type["orders_trend"]
    assert orders["current_value"] == pytest.approx(29)
    assert orders["previous_value"] == pytest.approx(34)
    assert orders["value"] == pytest.approx(-14.7, abs=0.05)

    top_product = by_type["top_product"]
    assert top_product["sku"] == "AUTO-1BANQUETAALTACOMENCOSTOSUPORTAATE200KG"
    assert top_product["value"] == pytest.approx(86.1, abs=0.05)

    # Um único marketplace no arquivo real — não deve gerar esse insight.
    assert "best_marketplace" not in by_type


def test_insights_without_period_still_returns_top_product(client: TestClient) -> None:
    """Sem `from`/`to`, os insights de comparação ficam ausentes (sem período
    anterior definido), mas produto em destaque continua funcionando sobre
    todos os dados do arquivo."""
    headers = _auth_headers(client, email="official-fixture-no-period@example.com")
    _process_official_fixture(client, headers)

    response = client.get("/api/v1/insights", headers=headers)

    assert response.status_code == 200
    body = response.json()
    by_type = {insight["type"]: insight for insight in body["insights"]}
    assert "revenue_trend" not in by_type
    assert "top_product" in by_type

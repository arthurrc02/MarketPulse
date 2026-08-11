"""Integração adicional: Analytics sobre o `orders.xlsx` real (239 pedidos).

Os testes de matemática "de verdade" ficam em `test_analytics_routes.py`,
com fixtures pequenas e determinísticas. Este arquivo prova que o fluxo
completo — upload → processamento ETL → agregação de Analytics — bate com
os números já verificados manualmente no relatório do Hotfix 4.2 (63 itens
`completed`, R$ 10.697,00 de faturamento).

Não importa `_auth_headers` de outro módulo de teste: `backend/tests` e
`etl/tests` formam um namespace package compartilhado (mesmo nome `tests`,
sem `__init__.py` — ver ADR-012 em decisions.md); um `from tests.x import y`
entre arquivos de teste resolve de forma ambígua. O helper é duplicado aqui
de propósito.
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


def test_overview_matches_official_fixture_totals(client: TestClient) -> None:
    headers = _auth_headers(client, email="official-fixture@example.com")
    _process_official_fixture(client, headers)

    response = client.get("/api/v1/analytics/overview", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["orders"] == 63
    assert body["revenue"] == pytest.approx(10697.00)
    assert body["active_products"] == 5
    assert body["average_order_value"] == pytest.approx(169.79, rel=1e-3)
    assert body["has_data"] is True


def test_top_products_matches_official_fixture(client: TestClient) -> None:
    headers = _auth_headers(client, email="official-fixture-top@example.com")
    _process_official_fixture(client, headers)

    response = client.get("/api/v1/analytics/top-products", headers=headers, params={"limit": 1})

    assert response.status_code == 200
    top = response.json()[0]
    assert top["sku"] == "AUTO-1BANQUETAALTACOMENCOSTOSUPORTAATE200KG"
    assert top["quantity"] == 49
    assert top["orders"] == 49


def test_orders_by_status_matches_official_fixture(client: TestClient) -> None:
    headers = _auth_headers(client, email="official-fixture-status@example.com")
    _process_official_fixture(client, headers)

    response = client.get("/api/v1/analytics/orders-by-status", headers=headers)

    assert response.status_code == 200
    by_status = {row["status"]: row["count"] for row in response.json()}
    assert by_status == {"cancelled": 77, "completed": 63, "pending": 83, "unknown": 16}

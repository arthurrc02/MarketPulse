"""Testes de Analytics: KPIs, série temporal, status, top produtos, filtros, isolamento.

Usa fixtures pequenas e determinísticas (`OrderItem` inseridos direto na
sessão de teste) para verificar a matemática com precisão — nenhum teste
aqui depende do `orders.xlsx` real (esse fica em
`test_analytics_official_fixture.py`, como teste de integração adicional).
"""

import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.models.upload import Upload, UploadStatus
from app.models.user import User
from etl.types import Marketplace, OrderStatus

VALID_PASSWORD = "Sup3rSecret!"


def _auth(
    client: TestClient, db_session: Session, *, email: str
) -> tuple[dict[str, str], uuid.UUID]:
    client.post("/api/v1/auth/register", json={"email": email, "password": VALID_PASSWORD})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    user_id = db_session.execute(select(User.id).where(User.email == email)).scalar_one()
    return headers, user_id


def _seed(
    db_session: Session,
    user_id: uuid.UUID,
    items: list[dict[str, object]],
) -> None:
    upload = Upload(
        user_id=user_id,
        original_filename="fixture.csv",
        stored_filename=f"{uuid.uuid4().hex}.csv",
        file_size=1,
        mime_type="text/csv",
        status=UploadStatus.PROCESSED,
    )
    db_session.add(upload)
    db_session.flush()
    for item in items:
        defaults: dict[str, object] = {
            "marketplace": Marketplace.SHOPEE,
            "discount_percentage": None,
        }
        db_session.add(OrderItem(user_id=user_id, upload_id=upload.id, **{**defaults, **item}))
    db_session.commit()


# Dataset determinístico: 5 pedidos, 6 itens.
#
# | pedido | data       | marketplace    | sku   | qty | preço unit. | status    |
# |--------|------------|----------------|-------|-----|-------------|-----------|
# | O1     | 2026-07-01 | shopee         | SKU-A | 1   | 1000        | completed |
# | O1     | 2026-07-01 | shopee         | SKU-B | 2   |  500        | completed |
# | O2     | 2026-07-01 | shopee         | SKU-A | 3   | 1000        | completed |
# | O3     | 2026-07-02 | shopee         | SKU-C | 1   | 2000        | cancelled |
# | O4     | 2026-07-02 | mercado_livre  | SKU-D | 1   | 1500        | completed |
# | O5     | 2026-07-03 | shopee         | SKU-E | 1   |  500        | pending   |
def _seed_dataset(db_session: Session, user_id: uuid.UUID) -> None:
    _seed(
        db_session,
        user_id,
        [
            {
                "external_order_id": "O1",
                "sku": "SKU-A",
                "product_name": "Produto A",
                "quantity": 1,
                "unit_price_cents": 1000,
                "total_price_cents": 1000,
                "status": OrderStatus.COMPLETED,
                "order_date": date(2026, 7, 1),
            },
            {
                "external_order_id": "O1",
                "sku": "SKU-B",
                "product_name": "Produto B",
                "quantity": 2,
                "unit_price_cents": 500,
                "total_price_cents": 1000,
                "status": OrderStatus.COMPLETED,
                "order_date": date(2026, 7, 1),
            },
            {
                "external_order_id": "O2",
                "sku": "SKU-A",
                "product_name": "Produto A",
                "quantity": 3,
                "unit_price_cents": 1000,
                "total_price_cents": 3000,
                "status": OrderStatus.COMPLETED,
                "order_date": date(2026, 7, 1),
            },
            {
                "external_order_id": "O3",
                "sku": "SKU-C",
                "product_name": "Produto C",
                "quantity": 1,
                "unit_price_cents": 2000,
                "total_price_cents": 2000,
                "status": OrderStatus.CANCELLED,
                "order_date": date(2026, 7, 2),
            },
            {
                "external_order_id": "O4",
                "sku": "SKU-D",
                "product_name": "Produto D",
                "quantity": 1,
                "unit_price_cents": 1500,
                "total_price_cents": 1500,
                "status": OrderStatus.COMPLETED,
                "order_date": date(2026, 7, 2),
                "marketplace": Marketplace.MERCADO_LIVRE,
            },
            {
                "external_order_id": "O5",
                "sku": "SKU-E",
                "product_name": "Produto E",
                "quantity": 1,
                "unit_price_cents": 500,
                "total_price_cents": 500,
                "status": OrderStatus.PENDING,
                "order_date": date(2026, 7, 3),
            },
        ],
    )


# ---------------------------------------------------------------------------
# Overview: faturamento, pedidos, ticket médio, produtos ativos
# ---------------------------------------------------------------------------


def test_overview_considers_only_completed_items(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="overview@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get("/api/v1/analytics/overview", headers=headers)

    assert response.status_code == 200
    body = response.json()
    # completed: O1 (1000+1000) + O2 (3000) + O4 (1500) = 6500 centavos = R$ 65.00
    assert body["revenue"] == pytest.approx(65.00)
    assert body["orders"] == 3  # O1, O2, O4 — não 4 itens completed
    assert body["average_order_value"] == pytest.approx(65.00 / 3, rel=1e-3)
    assert body["active_products"] == 3  # SKU-A, SKU-B, SKU-D (SKU-C/E não são completed)
    assert body["has_data"] is True


def test_overview_with_no_data_returns_zeros_and_has_data_false(
    client: TestClient, db_session: Session
) -> None:
    headers, _ = _auth(client, db_session, email="empty@example.com")

    response = client.get("/api/v1/analytics/overview", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "revenue": 0.0,
        "orders": 0,
        "average_order_value": 0.0,
        "active_products": 0,
        "has_data": False,
    }


def test_overview_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/analytics/overview")
    assert response.status_code == 401


def test_overview_never_mixes_data_between_users(client: TestClient, db_session: Session) -> None:
    headers_a, user_a = _auth(client, db_session, email="user-a@example.com")
    _seed_dataset(db_session, user_a)
    headers_b, _user_b = _auth(client, db_session, email="user-b@example.com")

    response_a = client.get("/api/v1/analytics/overview", headers=headers_a)
    response_b = client.get("/api/v1/analytics/overview", headers=headers_b)

    assert response_a.json()["has_data"] is True
    assert response_b.json() == {
        "revenue": 0.0,
        "orders": 0,
        "average_order_value": 0.0,
        "active_products": 0,
        "has_data": False,
    }


# ---------------------------------------------------------------------------
# Filtros: período e marketplace
# ---------------------------------------------------------------------------


def test_overview_filters_by_marketplace(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="marketplace@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get(
        "/api/v1/analytics/overview", headers=headers, params={"marketplace": "mercado_livre"}
    )

    body = response.json()
    assert body["revenue"] == pytest.approx(15.00)
    assert body["orders"] == 1
    assert body["active_products"] == 1


def test_overview_filters_by_period(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="period@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
        params={"from": "2026-07-02", "to": "2026-07-02"},
    )

    body = response.json()
    # só O4 é completed em 2026-07-02 (O3 é cancelled nesse dia)
    assert body["revenue"] == pytest.approx(15.00)
    assert body["orders"] == 1


def test_overview_rejects_period_with_start_after_end(
    client: TestClient, db_session: Session
) -> None:
    headers, _ = _auth(client, db_session, email="invalid-period@example.com")

    response = client.get(
        "/api/v1/analytics/overview",
        headers=headers,
        params={"from": "2026-07-10", "to": "2026-07-01"},
    )

    assert response.status_code == 422


def test_overview_rejects_invalid_marketplace(client: TestClient, db_session: Session) -> None:
    headers, _ = _auth(client, db_session, email="invalid-marketplace@example.com")

    response = client.get(
        "/api/v1/analytics/overview", headers=headers, params={"marketplace": "ebay"}
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Série temporal
# ---------------------------------------------------------------------------


def test_sales_over_time_aggregates_by_day_completed_only(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="series@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get("/api/v1/analytics/sales-over-time", headers=headers)

    assert response.status_code == 200
    points = {point["date"]: point for point in response.json()}
    assert points["2026-07-01"]["revenue"] == pytest.approx(50.00)
    assert points["2026-07-01"]["orders"] == 2  # O1 + O2
    assert points["2026-07-02"]["revenue"] == pytest.approx(15.00)  # só O4 (O3 é cancelled)
    assert points["2026-07-02"]["orders"] == 1
    # 2026-07-03 só tem O5 (pending) — nenhum dado completed, dia ausente da série
    assert "2026-07-03" not in points


# ---------------------------------------------------------------------------
# Distribuição por status
# ---------------------------------------------------------------------------


def test_orders_by_status_covers_every_status_with_percentage(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="status@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get("/api/v1/analytics/orders-by-status", headers=headers)

    assert response.status_code == 200
    by_status = {row["status"]: row for row in response.json()}
    assert by_status["completed"] == {"status": "completed", "count": 3, "percentage": 60.0}
    assert by_status["cancelled"] == {"status": "cancelled", "count": 1, "percentage": 20.0}
    assert by_status["pending"] == {"status": "pending", "count": 1, "percentage": 20.0}
    assert "refunded" not in by_status  # nenhum pedido com esse status no dataset


def test_orders_by_status_with_no_data_returns_empty_list(
    client: TestClient, db_session: Session
) -> None:
    headers, _ = _auth(client, db_session, email="status-empty@example.com")

    response = client.get("/api/v1/analytics/orders-by-status", headers=headers)

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Top produtos
# ---------------------------------------------------------------------------


def test_top_products_ranks_by_revenue_completed_only(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="top-products@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get("/api/v1/analytics/top-products", headers=headers)

    assert response.status_code == 200
    products = response.json()
    assert [p["sku"] for p in products] == ["SKU-A", "SKU-D", "SKU-B"]
    top = products[0]
    assert top["product_name"] == "Produto A"
    assert top["quantity"] == 4  # 1 (O1) + 3 (O2)
    assert top["revenue"] == pytest.approx(40.00)
    assert top["orders"] == 2  # O1, O2


def test_top_products_respects_limit(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="top-products-limit@example.com")
    _seed_dataset(db_session, user_id)

    response = client.get("/api/v1/analytics/top-products", headers=headers, params={"limit": 1})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["sku"] == "SKU-A"


def test_top_products_rejects_limit_above_maximum(client: TestClient, db_session: Session) -> None:
    headers, _ = _auth(client, db_session, email="top-products-bad-limit@example.com")

    response = client.get("/api/v1/analytics/top-products", headers=headers, params={"limit": 999})

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Autenticação (demais endpoints)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/analytics/sales-over-time",
        "/api/v1/analytics/orders-by-status",
        "/api/v1/analytics/top-products",
    ],
)
def test_endpoints_require_authentication(path: str, client: TestClient) -> None:
    response = client.get(path)
    assert response.status_code == 401

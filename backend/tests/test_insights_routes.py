"""Testes de Business Insights: matemática de cada regra, guards de dados
insuficientes, filtros, isolamento por usuário.

Dataset principal (`_seed_main_dataset`): período atual `2026-07-11..20`
(10 dias), período anterior `2026-07-01..10` (mesmo tamanho, calculado pelo
próprio serviço). Os valores foram escolhidos para dar percentuais exatos
(sem ambiguidade de arredondamento) — conferidos à mão no docstring de cada
teste, não só rodados e colados.
"""

import uuid
from collections.abc import Iterable
from datetime import date
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.models.upload import Upload, UploadStatus
from app.models.user import User
from etl.types import Marketplace, OrderStatus

VALID_PASSWORD = "Sup3rSecret!"

CURRENT_FROM = "2026-07-11"
CURRENT_TO = "2026-07-20"
# Calculado pela mesma fórmula do serviço: 10 dias, imediatamente antes.
PREVIOUS_FROM = date(2026, 7, 1)
PREVIOUS_TO = date(2026, 7, 10)


def _auth(
    client: TestClient, db_session: Session, *, email: str
) -> tuple[dict[str, str], uuid.UUID]:
    client.post("/api/v1/auth/register", json={"email": email, "password": VALID_PASSWORD})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD})
    headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    user_id = db_session.execute(select(User.id).where(User.email == email)).scalar_one()
    return headers, user_id


def _seed(db_session: Session, user_id: uuid.UUID, items: Iterable[dict[str, object]]) -> None:
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


def _item(
    order_id: str,
    sku: str,
    product_name: str,
    total_cents: int,
    order_date: date,
    *,
    status: OrderStatus = OrderStatus.COMPLETED,
    marketplace: Marketplace = Marketplace.SHOPEE,
) -> dict[str, object]:
    return {
        "external_order_id": order_id,
        "sku": sku,
        "product_name": product_name,
        "quantity": 1,
        "unit_price_cents": total_cents,
        "total_price_cents": total_cents,
        "status": status,
        "order_date": order_date,
        "marketplace": marketplace,
    }


# Período anterior (2026-07-01..10): total 10.000 centavos, 4 pedidos.
#   A=3000 (30%, relevante) B=6000 (60%) C=500 (5%, irrelevante)
#   D=500 (5%, irrelevante, mercado_livre)
# Período atual (2026-07-11..20): total 8.000 centavos, 5 pedidos.
#   A=1000 (-66,7% vs 3000 — único produto relevante em queda)
#   B=6480 (produto em destaque: 6480/8000 = 81,0%)
#   C=10 (queda enorme, mas irrelevante — não deve aparecer)
#   D=400 (mercado_livre; 400 de 8000 total = participação de marketplace)
#   E=110 (produto novo, sem par no período anterior)
#   + 1 pedido cancelado (9999) — não deve entrar em nada
def _seed_main_dataset(db_session: Session, user_id: uuid.UUID) -> None:
    ml = Marketplace.MERCADO_LIVRE
    _seed(
        db_session,
        user_id,
        [
            _item("P1", "SKU-A", "Produto A", 3000, date(2026, 7, 2)),
            _item("P2", "SKU-B", "Produto B", 6000, date(2026, 7, 3)),
            _item("P3", "SKU-C", "Produto C", 500, date(2026, 7, 4)),
            _item("P4", "SKU-D", "Produto D", 500, date(2026, 7, 5), marketplace=ml),
            _item("O1", "SKU-A", "Produto A", 1000, date(2026, 7, 12)),
            _item("O2", "SKU-B", "Produto B", 6480, date(2026, 7, 13)),
            _item("O3", "SKU-C", "Produto C", 10, date(2026, 7, 14)),
            _item("O4", "SKU-D", "Produto D", 400, date(2026, 7, 15), marketplace=ml),
            _item("O5", "SKU-E", "Produto E", 110, date(2026, 7, 16)),
            _item(
                "O6",
                "SKU-X",
                "Produto Cancelado",
                9999,
                date(2026, 7, 17),
                status=OrderStatus.CANCELLED,
            ),
        ],
    )


def _get_insights(client: TestClient, headers: dict[str, str], **params: str) -> dict[str, Any]:
    response = client.get("/api/v1/insights", headers=headers, params=params)
    assert response.status_code == 200
    result: dict[str, Any] = response.json()
    return result


def _by_type(body: dict[str, Any]) -> dict[str, dict[str, Any]]:
    insights: list[dict[str, Any]] = body["insights"]
    return {insight["type"]: insight for insight in insights}


# ---------------------------------------------------------------------------
# Tendências de período (faturamento, pedidos, ticket médio)
# ---------------------------------------------------------------------------


def test_revenue_trend_decline(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="revenue-decline@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["revenue_trend"]
    assert insight["severity"] == "negative"
    assert insight["value"] == pytest.approx(-20.0)
    assert insight["current_value"] == pytest.approx(80.0)
    assert insight["previous_value"] == pytest.approx(100.0)
    assert "caiu" in insight["description"]
    assert "20" in insight["description"]


def test_orders_trend_growth(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="orders-growth@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["orders_trend"]
    assert insight["severity"] == "positive"
    assert insight["value"] == pytest.approx(25.0)
    assert insight["current_value"] == pytest.approx(5)
    assert insight["previous_value"] == pytest.approx(4)
    assert "mais pedidos" in insight["description"]


def test_average_order_value_trend_decline(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="ticket-decline@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["average_order_value_trend"]
    assert insight["severity"] == "negative"
    assert insight["value"] == pytest.approx(-36.0)
    assert insight["current_value"] == pytest.approx(16.0)
    assert insight["previous_value"] == pytest.approx(25.0)


def test_revenue_and_orders_trend_growth(client: TestClient, db_session: Session) -> None:
    """Cenário isolado só de crescimento — prova que a severidade não é sempre negativa."""
    headers, user_id = _auth(client, db_session, email="growth-only@example.com")
    _seed(
        db_session,
        user_id,
        [
            _item("P1", "SKU-A", "Produto A", 1000, date(2026, 7, 2)),
            _item("O1", "SKU-A", "Produto A", 2000, date(2026, 7, 12)),
            _item("O2", "SKU-A", "Produto A", 1000, date(2026, 7, 13)),
        ],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    revenue = _by_type(body)["revenue_trend"]
    assert revenue["severity"] == "positive"
    assert revenue["value"] == pytest.approx(200.0)  # 3000 vs 1000 = +200%
    orders = _by_type(body)["orders_trend"]
    assert orders["severity"] == "positive"
    assert orders["value"] == pytest.approx(100.0)  # 2 vs 1 = +100%


def test_stable_revenue_is_neutral(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="stable@example.com")
    _seed(
        db_session,
        user_id,
        [
            _item("P1", "SKU-A", "Produto A", 5000, date(2026, 7, 2)),
            _item("O1", "SKU-A", "Produto A", 5000, date(2026, 7, 12)),
        ],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    revenue = _by_type(body)["revenue_trend"]
    assert revenue["severity"] == "neutral"
    assert revenue["value"] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Produto em destaque e produto em queda
# ---------------------------------------------------------------------------


def test_top_product_by_revenue_with_participation(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="top-product@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["top_product"]
    assert insight["sku"] == "SKU-B"
    assert insight["product_name"] == "Produto B"
    assert insight["value"] == pytest.approx(81.0)  # 6480 / 8000
    assert insight["severity"] == "neutral"


def test_product_decline_ignores_irrelevant_products(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="product-decline@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["product_decline"]
    # não SKU-C, que caiu mais % mas é irrelevante (5% do período anterior)
    assert insight["sku"] == "SKU-A"
    assert insight["severity"] == "negative"
    assert insight["value"] == pytest.approx(-66.7, abs=0.05)


def test_no_product_decline_insight_when_nothing_relevant_declines(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="no-decline@example.com")
    _seed(
        db_session,
        user_id,
        [
            _item("P1", "SKU-A", "Produto A", 1000, date(2026, 7, 2)),
            _item("O1", "SKU-A", "Produto A", 2000, date(2026, 7, 12)),  # cresceu, não caiu
        ],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    assert "product_decline" not in _by_type(body)


def test_tie_in_top_product_revenue_still_returns_exactly_one_insight(
    client: TestClient, db_session: Session
) -> None:
    """Em empate, o desempate é implementação (sem tiebreaker explícito no
    `ORDER BY`) — o que importa aqui é que o sistema não quebra nem produz
    mais de um insight do tipo `top_product`."""
    headers, user_id = _auth(client, db_session, email="tie@example.com")
    _seed(
        db_session,
        user_id,
        [
            _item("O1", "SKU-A", "Produto A", 1000, date(2026, 7, 12)),
            _item("O2", "SKU-B", "Produto B", 1000, date(2026, 7, 13)),
        ],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    top_products = [insight for insight in body["insights"] if insight["type"] == "top_product"]
    assert len(top_products) == 1
    assert top_products[0]["sku"] in {"SKU-A", "SKU-B"}
    assert top_products[0]["value"] == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# Marketplace de melhor desempenho
# ---------------------------------------------------------------------------


def test_best_marketplace_with_multiple_marketplaces(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="best-marketplace@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    insight = _by_type(body)["best_marketplace"]
    assert insight["marketplace"] == "shopee"
    assert insight["value"] == pytest.approx(95.0)  # 7600 / 8000


def test_no_best_marketplace_insight_with_single_marketplace(
    client: TestClient, db_session: Session
) -> None:
    headers, user_id = _auth(client, db_session, email="single-marketplace@example.com")
    _seed(
        db_session,
        user_id,
        [_item("O1", "SKU-A", "Produto A", 1000, date(2026, 7, 12))],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    assert "best_marketplace" not in _by_type(body)


def test_no_best_marketplace_insight_when_filtered_to_one_marketplace(
    client: TestClient, db_session: Session
) -> None:
    """Mesmo com dois marketplaces nos dados, o filtro reduz a um só — insight não deve aparecer."""
    headers, user_id = _auth(client, db_session, email="filtered-marketplace@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(
        client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO, "marketplace": "shopee"}
    )

    assert "best_marketplace" not in _by_type(body)


def test_marketplace_filter_changes_totals(client: TestClient, db_session: Session) -> None:
    headers, user_id = _auth(client, db_session, email="marketplace-filter@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(
        client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO, "marketplace": "mercado_livre"}
    )

    # Só o produto D (mercado_livre): 400 atual vs 500 anterior.
    revenue = _by_type(body)["revenue_trend"]
    assert revenue["current_value"] == pytest.approx(4.0)
    assert revenue["previous_value"] == pytest.approx(5.0)


# ---------------------------------------------------------------------------
# Ausência de dados / dados insuficientes
# ---------------------------------------------------------------------------


def test_no_data_returns_has_data_false_and_no_insights(
    client: TestClient, db_session: Session
) -> None:
    headers, _ = _auth(client, db_session, email="no-data@example.com")

    body = _get_insights(client, headers)

    assert body == {"has_data": False, "insights": []}


def test_missing_period_skips_comparison_insights_but_keeps_the_rest(
    client: TestClient, db_session: Session
) -> None:
    """Sem `from`/`to`, não há "período anterior equivalente" — insights de
    comparação ficam ausentes, mas produto em destaque e marketplace (que não
    dependem de comparação) continuam funcionando sobre todos os dados."""
    headers, user_id = _auth(client, db_session, email="missing-period@example.com")
    _seed_main_dataset(db_session, user_id)

    body = _get_insights(client, headers)

    types = _by_type(body)
    assert "revenue_trend" not in types
    assert "orders_trend" not in types
    assert "average_order_value_trend" not in types
    assert "product_decline" not in types
    assert "top_product" in types
    assert "best_marketplace" in types
    assert body["has_data"] is True


def test_previous_period_with_no_data_skips_comparison_insights(
    client: TestClient, db_session: Session
) -> None:
    """Só há dados no período atual — nada no período anterior equivalente."""
    headers, user_id = _auth(client, db_session, email="no-previous-period@example.com")
    _seed(
        db_session,
        user_id,
        [_item("O1", "SKU-A", "Produto A", 1000, date(2026, 7, 12))],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    types = _by_type(body)
    assert "revenue_trend" not in types
    assert "orders_trend" not in types
    assert "average_order_value_trend" not in types
    assert "product_decline" not in types
    assert "top_product" in types  # não depende de período anterior


def test_zero_revenue_in_both_periods_produces_no_insights(
    client: TestClient, db_session: Session
) -> None:
    """Só pedidos cancelados nos dois períodos — completed em ambos é zero."""
    headers, user_id = _auth(client, db_session, email="zero-values@example.com")
    _seed(
        db_session,
        user_id,
        [
            _item("P1", "SKU-A", "Produto A", 1000, date(2026, 7, 2), status=OrderStatus.CANCELLED),
            _item(
                "O1", "SKU-A", "Produto A", 1000, date(2026, 7, 12), status=OrderStatus.CANCELLED
            ),
        ],
    )

    body = _get_insights(client, headers, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    # has_data é True (existem OrderItem), mas nenhuma regra encontra algo — "dados insuficientes".
    assert body["has_data"] is True
    assert body["insights"] == []


# ---------------------------------------------------------------------------
# Validação, autenticação, isolamento
# ---------------------------------------------------------------------------


def test_rejects_period_with_start_after_end(client: TestClient, db_session: Session) -> None:
    headers, _ = _auth(client, db_session, email="invalid-period@example.com")

    response = client.get(
        "/api/v1/insights", headers=headers, params={"from": "2026-07-20", "to": "2026-07-01"}
    )

    assert response.status_code == 422


def test_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/insights")
    assert response.status_code == 401


def test_never_mixes_insights_between_users(client: TestClient, db_session: Session) -> None:
    headers_a, user_a = _auth(client, db_session, email="isolation-a@example.com")
    _seed_main_dataset(db_session, user_a)
    headers_b, _user_b = _auth(client, db_session, email="isolation-b@example.com")

    body_a = _get_insights(client, headers_a, **{"from": CURRENT_FROM, "to": CURRENT_TO})
    body_b = _get_insights(client, headers_b, **{"from": CURRENT_FROM, "to": CURRENT_TO})

    assert body_a["has_data"] is True
    assert body_b == {"has_data": False, "insights": []}

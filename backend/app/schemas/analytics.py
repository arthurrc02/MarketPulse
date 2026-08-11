"""Schemas de Analytics — contratos de resposta dos indicadores agregados.

Nenhum destes schemas espelha `OrderItem` diretamente: todos representam
dados já agregados no banco (ver `app/repositories/analytics.py`). Valores
monetários entram como `float` — a soma em centavos acontece inteiramente no
SQL/Python com inteiros; a conversão para reais é só de exibição, feita uma
única vez na borda da resposta (nunca usada de volta em outro cálculo).
"""

from datetime import date

from pydantic import BaseModel, ConfigDict

from etl.types import OrderStatus


class AnalyticsOverview(BaseModel):
    """Os quatro KPIs principais do Dashboard.

    Todos calculados apenas sobre `OrderItem` com `status = completed` —
    "faturamento" de um pedido cancelado não é faturamento (ver ADR-062 em
    `docs/decisions.md`).
    """

    model_config = ConfigDict(from_attributes=True)

    revenue: float
    """Soma de `total_price_cents / 100` dos itens `completed` no período/filtro."""

    orders: int
    """`COUNT(DISTINCT external_order_id)` dos itens `completed` no período/filtro."""

    average_order_value: float
    """`revenue / orders`; `0` quando `orders == 0` (nunca divide por zero)."""

    active_products: int
    """`COUNT(DISTINCT sku)` dos itens `completed` no período/filtro."""

    has_data: bool
    """`True` se o usuário tem QUALQUER `OrderItem` (ignora filtros e status).

    Distingue "usuário nunca importou nada" (frontend mostra o EmptyState de
    onboarding) de "o filtro atual não tem resultado" (frontend mostra uma
    mensagem mais leve, sem esconder os filtros) — os outros três campos
    sozinhos não permitem essa distinção quando valem `0`.
    """


class SalesOverTimePoint(BaseModel):
    """Um ponto da série temporal (`GET /analytics/sales-over-time`), agregado por dia."""

    model_config = ConfigDict(from_attributes=True)

    date: date
    revenue: float
    orders: int


class OrderStatusBreakdown(BaseModel):
    """Um status no `GET /analytics/orders-by-status`.

    Ao contrário dos outros endpoints, **não** filtra por `status =
    completed` — o próprio propósito deste endpoint é mostrar a distribuição
    entre todos os status.
    """

    model_config = ConfigDict(from_attributes=True)

    status: OrderStatus
    count: int
    """`COUNT(DISTINCT external_order_id)` com este status."""

    percentage: float
    """`count / total_de_pedidos * 100`, 0 casas decimais além do padrão float."""


class TopProduct(BaseModel):
    """Uma linha do `GET /analytics/top-products` — só itens `completed`."""

    model_config = ConfigDict(from_attributes=True)

    product_name: str
    sku: str
    quantity: int
    """Soma de `quantity` entre todos os pedidos `completed` deste produto."""

    revenue: float
    orders: int
    """`COUNT(DISTINCT external_order_id)` em que este produto aparece."""


__all__ = [
    "AnalyticsOverview",
    "OrderStatusBreakdown",
    "SalesOverTimePoint",
    "TopProduct",
]

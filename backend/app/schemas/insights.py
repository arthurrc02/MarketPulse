"""Schemas de Business Insights — observações determinísticas sobre os dados de Analytics.

Diferença de Analytics (Sprint 5): Analytics expõe *métricas* (o quê); Insights
interpreta essas métricas e produz *observações* (o que isso significa) —
comparação com o período anterior, concentração em um produto/marketplace.
Nenhuma regra aqui usa IA/ML — só aritmética sobre agregações do PostgreSQL
(ver `app/services/insights.py` e ADR-065/066/067 em `docs/decisions.md`).
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict

from etl.types import Marketplace


class InsightSeverity(StrEnum):
    """Como o cartão deve ser destacado visualmente no frontend."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class InsightType(StrEnum):
    """Um tipo por regra de negócio implementada nesta sprint (ver services/insights.py)."""

    REVENUE_TREND = "revenue_trend"
    ORDERS_TREND = "orders_trend"
    AVERAGE_ORDER_VALUE_TREND = "average_order_value_trend"
    TOP_PRODUCT = "top_product"
    PRODUCT_DECLINE = "product_decline"
    BEST_MARKETPLACE = "best_marketplace"


class Insight(BaseModel):
    """Um insight pronto para exibição — nunca uma string solta.

    `value` é sempre um percentual (variação ou participação — cada regra
    documenta qual, em `services/insights.py`); `current_value`/
    `previous_value` trazem os valores absolutos por trás do percentual
    (reais ou contagem de pedidos, conforme `type`) só como contexto para a
    UI eventualmente detalhar o cartão — o texto de `description` já é
    autossuficiente.
    """

    model_config = ConfigDict(from_attributes=True)

    id: str
    """Igual a `type.value` — cada tipo aparece no máximo uma vez por resposta."""

    type: InsightType
    title: str
    description: str
    severity: InsightSeverity

    value: float
    """Percentual (variação ou participação, conforme `type`), 1 casa decimal."""

    current_value: float | None = None
    previous_value: float | None = None
    product_name: str | None = None
    sku: str | None = None
    marketplace: Marketplace | None = None


class InsightsResponse(BaseModel):
    """Resposta de `GET /api/v1/insights`.

    `has_data` segue o mesmo papel do campo homônimo em `AnalyticsOverview`
    (ADR-063): distingue "usuário nunca importou nada" de "há dados, mas
    nenhuma regra encontrou algo relevante para reportar" (`insights == []`
    com `has_data == True`) — ver ADR-065.
    """

    model_config = ConfigDict(from_attributes=True)

    has_data: bool
    insights: list[Insight]

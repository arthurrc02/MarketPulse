"""Regras de Business Insights — determinísticas, sem IA/ML/estatística avançada.

Cada `_build_*` implementa uma regra e devolve `None` quando os dados não são
suficientes para um insight válido (ver ADR-065/066 em `docs/decisions.md`);
`InsightsService.get_insights` descarta os `None` e monta a lista final. Toda
regra de comparação usa `_pct_change`, que devolve `None` (não uma divisão
por zero) quando o valor do período anterior é `0` — não há base para
expressar "cresceu X%" a partir de nada.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import InvalidAnalyticsFilterError
from app.models.user import User
from app.repositories.analytics import AnalyticsFilters, OverviewRow, ProductRow
from app.repositories.insights import InsightsRepository, MarketplaceRevenueRow
from app.schemas.insights import Insight, InsightSeverity, InsightsResponse, InsightType
from etl.types import Marketplace

# Um produto só é candidato ao insight de "queda de desempenho" se, no
# período anterior, respondia por pelo menos esta fração do faturamento
# total do período — evita apontar quedas percentualmente grandes em
# produtos irrelevantes em valor absoluto (ver ADR-066).
_PRODUCT_RELEVANCE_SHARE = 0.10

_MARKETPLACE_LABELS: dict[Marketplace, str] = {
    Marketplace.SHOPEE: "Shopee",
    Marketplace.MERCADO_LIVRE: "Mercado Livre",
    Marketplace.AMAZON: "Amazon",
    Marketplace.MAGALU: "Magalu",
}


@dataclass(frozen=True, slots=True)
class _Period:
    date_from: date
    date_to: date


def _cents_to_amount(cents: int) -> float:
    return float(Decimal(cents) / 100)


def _pct_change(current: float, previous: float) -> float | None:
    """`None` quando `previous == 0` — sem base, não há variação percentual válida."""
    if previous == 0:
        return None
    return round((current - previous) / previous * 100, 1)


def _severity_from_variation(variation: float) -> InsightSeverity:
    if variation > 0:
        return InsightSeverity.POSITIVE
    if variation < 0:
        return InsightSeverity.NEGATIVE
    return InsightSeverity.NEUTRAL


def _previous_equivalent_period(date_from: date, date_to: date) -> _Period:
    """Mesmo número de dias de `[date_from, date_to]`, imediatamente anterior.

    Ex.: `2026-07-01..2026-07-10` (10 dias) → período anterior
    `2026-06-21..2026-06-30` (10 dias). Ver ADR-065 em `docs/decisions.md`.
    """
    length_days = (date_to - date_from).days + 1
    previous_to = date_from - timedelta(days=1)
    previous_from = previous_to - timedelta(days=length_days - 1)
    return _Period(date_from=previous_from, date_to=previous_to)


def _average_order_value(row: OverviewRow) -> float:
    if row.orders == 0:
        return 0.0
    return round(_cents_to_amount(row.revenue_cents) / row.orders, 2)


def _build_revenue_trend(current: OverviewRow, previous: OverviewRow) -> Insight | None:
    current_revenue = _cents_to_amount(current.revenue_cents)
    previous_revenue = _cents_to_amount(previous.revenue_cents)
    variation = _pct_change(current_revenue, previous_revenue)
    if variation is None:
        return None

    severity = _severity_from_variation(variation)
    if severity is InsightSeverity.POSITIVE:
        title = "Faturamento em alta"
        description = f"Seu faturamento cresceu {variation}% em relação ao período anterior."
    elif severity is InsightSeverity.NEGATIVE:
        title = "Faturamento em queda"
        description = f"Seu faturamento caiu {abs(variation)}% em relação ao período anterior."
    else:
        title = "Faturamento estável"
        description = "Seu faturamento se manteve estável em relação ao período anterior."

    return Insight(
        id=InsightType.REVENUE_TREND.value,
        type=InsightType.REVENUE_TREND,
        title=title,
        description=description,
        severity=severity,
        value=variation,
        current_value=current_revenue,
        previous_value=previous_revenue,
    )


def _build_orders_trend(current: OverviewRow, previous: OverviewRow) -> Insight | None:
    variation = _pct_change(float(current.orders), float(previous.orders))
    if variation is None:
        return None

    severity = _severity_from_variation(variation)
    if severity is InsightSeverity.POSITIVE:
        title = "Mais pedidos que no período anterior"
        description = f"Você realizou {variation}% mais pedidos que no período anterior."
    elif severity is InsightSeverity.NEGATIVE:
        title = "Menos pedidos que no período anterior"
        description = f"Você realizou {abs(variation)}% menos pedidos que no período anterior."
    else:
        title = "Pedidos estáveis"
        description = "A quantidade de pedidos se manteve estável em relação ao período anterior."

    return Insight(
        id=InsightType.ORDERS_TREND.value,
        type=InsightType.ORDERS_TREND,
        title=title,
        description=description,
        severity=severity,
        value=variation,
        current_value=float(current.orders),
        previous_value=float(previous.orders),
    )


def _build_average_order_value_trend(current: OverviewRow, previous: OverviewRow) -> Insight | None:
    current_avg = _average_order_value(current)
    previous_avg = _average_order_value(previous)
    variation = _pct_change(current_avg, previous_avg)
    if variation is None:
        return None

    severity = _severity_from_variation(variation)
    if severity is InsightSeverity.POSITIVE:
        title = "Ticket médio em alta"
        description = f"O ticket médio aumentou {variation}% em relação ao período anterior."
    elif severity is InsightSeverity.NEGATIVE:
        title = "Ticket médio em queda"
        description = f"O ticket médio caiu {abs(variation)}% em relação ao período anterior."
    else:
        title = "Ticket médio estável"
        description = "O ticket médio se manteve estável em relação ao período anterior."

    return Insight(
        id=InsightType.AVERAGE_ORDER_VALUE_TREND.value,
        type=InsightType.AVERAGE_ORDER_VALUE_TREND,
        title=title,
        description=description,
        severity=severity,
        value=variation,
        current_value=current_avg,
        previous_value=previous_avg,
    )


def _build_top_product(products: list[ProductRow], totals: OverviewRow) -> Insight | None:
    if not products or totals.revenue_cents <= 0:
        return None
    top = products[0]  # já ordenado por receita desc (ver InsightsRepository.product_revenue)
    if top.revenue_cents <= 0:
        return None

    share = round(top.revenue_cents / totals.revenue_cents * 100, 1)
    return Insight(
        id=InsightType.TOP_PRODUCT.value,
        type=InsightType.TOP_PRODUCT,
        title="Produto em destaque",
        description=f"{top.product_name} foi responsável por {share}% do faturamento no período.",
        severity=InsightSeverity.NEUTRAL,
        value=share,
        current_value=_cents_to_amount(top.revenue_cents),
        product_name=top.product_name,
        sku=top.sku,
    )


def _build_product_decline(current: list[ProductRow], previous: list[ProductRow]) -> Insight | None:
    previous_total_cents = sum(row.revenue_cents for row in previous)
    if previous_total_cents <= 0:
        return None

    relevance_floor_cents = previous_total_cents * _PRODUCT_RELEVANCE_SHARE
    current_by_sku = {row.sku: row for row in current}

    declines: list[tuple[float, ProductRow, int]] = []
    for prev_row in previous:
        if prev_row.revenue_cents < relevance_floor_cents:
            continue
        current_row = current_by_sku.get(prev_row.sku)
        current_revenue_cents = current_row.revenue_cents if current_row else 0
        variation = _pct_change(
            _cents_to_amount(current_revenue_cents), _cents_to_amount(prev_row.revenue_cents)
        )
        if variation is not None and variation < 0:
            declines.append((variation, prev_row, current_revenue_cents))

    if not declines:
        return None

    declines.sort(key=lambda item: (item[0], item[1].sku))
    variation, prev_row, current_revenue_cents = declines[0]
    return Insight(
        id=InsightType.PRODUCT_DECLINE.value,
        type=InsightType.PRODUCT_DECLINE,
        title="Queda de desempenho em produto",
        description=(
            f"{prev_row.product_name} apresentou queda de {abs(variation)}% "
            "no faturamento em relação ao período anterior."
        ),
        severity=InsightSeverity.NEGATIVE,
        value=variation,
        current_value=_cents_to_amount(current_revenue_cents),
        previous_value=_cents_to_amount(prev_row.revenue_cents),
        product_name=prev_row.product_name,
        sku=prev_row.sku,
    )


def _build_best_marketplace(rows: list[MarketplaceRevenueRow]) -> Insight | None:
    positive_rows = [row for row in rows if row.revenue_cents > 0]
    if len(positive_rows) < 2:
        return None

    total_cents = sum(row.revenue_cents for row in positive_rows)
    top = max(positive_rows, key=lambda row: row.revenue_cents)
    share = round(top.revenue_cents / total_cents * 100, 1)
    return Insight(
        id=InsightType.BEST_MARKETPLACE.value,
        type=InsightType.BEST_MARKETPLACE,
        title="Marketplace de melhor desempenho",
        description=(
            f"{_MARKETPLACE_LABELS[top.marketplace]} representa o maior "
            f"faturamento, com {share}% do total."
        ),
        severity=InsightSeverity.NEUTRAL,
        value=share,
        current_value=_cents_to_amount(top.revenue_cents),
        marketplace=top.marketplace,
    )


class InsightsService:
    """Monta `InsightsResponse` a partir das agregações de `InsightsRepository`.

    No máximo 5 consultas por requisição (totais + produtos do período
    atual, totais + produtos do período anterior quando aplicável, receita
    por marketplace) — nenhuma delas por insight individual (ver ADR-067).
    """

    def __init__(self, session: Session) -> None:
        self._repository = InsightsRepository(session)

    def get_insights(
        self,
        *,
        user: User,
        date_from: date | None,
        date_to: date | None,
        marketplace: Marketplace | None,
    ) -> InsightsResponse:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise InvalidAnalyticsFilterError("A data inicial não pode ser posterior à data final.")

        if not self._repository.has_any_data(user.id):
            return InsightsResponse(has_data=False, insights=[])

        current_filters = AnalyticsFilters(
            date_from=date_from, date_to=date_to, marketplace=marketplace
        )
        current_totals = self._repository.period_totals(user_id=user.id, filters=current_filters)
        current_products = self._repository.product_revenue(
            user_id=user.id, filters=current_filters
        )
        marketplace_revenue = self._repository.revenue_by_marketplace(
            user_id=user.id, filters=current_filters
        )

        previous_totals: OverviewRow | None = None
        previous_products: list[ProductRow] | None = None
        if date_from is not None and date_to is not None:
            previous_period = _previous_equivalent_period(date_from, date_to)
            previous_filters = AnalyticsFilters(
                date_from=previous_period.date_from,
                date_to=previous_period.date_to,
                marketplace=marketplace,
            )
            previous_totals = self._repository.period_totals(
                user_id=user.id, filters=previous_filters
            )
            previous_products = self._repository.product_revenue(
                user_id=user.id, filters=previous_filters
            )

        insights: list[Insight] = []

        if previous_totals is not None:
            for builder in (
                _build_revenue_trend,
                _build_orders_trend,
                _build_average_order_value_trend,
            ):
                insight = builder(current_totals, previous_totals)
                if insight is not None:
                    insights.append(insight)

        top_product_insight = _build_top_product(current_products, current_totals)
        if top_product_insight is not None:
            insights.append(top_product_insight)

        if previous_products is not None:
            decline_insight = _build_product_decline(current_products, previous_products)
            if decline_insight is not None:
                insights.append(decline_insight)

        best_marketplace_insight = _build_best_marketplace(marketplace_revenue)
        if best_marketplace_insight is not None:
            insights.append(best_marketplace_insight)

        return InsightsResponse(has_data=True, insights=insights)


__all__ = ["InsightsService"]

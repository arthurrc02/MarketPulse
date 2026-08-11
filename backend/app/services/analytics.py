"""Regras de negócio de Analytics: validação de filtros e conversão de unidades.

Nenhuma consulta SQL aparece aqui — toda agregação é responsabilidade de
`AnalyticsRepository`; este serviço só valida a entrada, monta o filtro e
traduz linhas de banco (centavos, contagens) para os schemas de resposta
(reais, percentuais).
"""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.errors import InvalidAnalyticsFilterError
from app.models.user import User
from app.repositories.analytics import AnalyticsFilters, AnalyticsRepository
from app.schemas.analytics import (
    AnalyticsOverview,
    OrderStatusBreakdown,
    SalesOverTimePoint,
    TopProduct,
)
from etl.types import Marketplace

DEFAULT_TOP_PRODUCTS_LIMIT = 10


def _cents_to_amount(cents: int) -> float:
    """Converte centavos (inteiro, como gravado no banco) para reais — só na borda da resposta."""
    return float(Decimal(cents) / 100)


class AnalyticsService:
    """Indicadores agregados a partir dos `OrderItem` do usuário autenticado."""

    def __init__(self, session: Session) -> None:
        self._repository = AnalyticsRepository(session)

    def get_overview(
        self,
        *,
        user: User,
        date_from: date | None,
        date_to: date | None,
        marketplace: Marketplace | None,
    ) -> AnalyticsOverview:
        filters = self._build_filters(date_from, date_to, marketplace)
        row = self._repository.overview(user_id=user.id, filters=filters)
        revenue = _cents_to_amount(row.revenue_cents)
        average_order_value = round(revenue / row.orders, 2) if row.orders > 0 else 0.0
        return AnalyticsOverview(
            revenue=revenue,
            orders=row.orders,
            average_order_value=average_order_value,
            active_products=row.active_products,
            has_data=self._repository.has_any_data(user.id),
        )

    def get_sales_over_time(
        self,
        *,
        user: User,
        date_from: date | None,
        date_to: date | None,
        marketplace: Marketplace | None,
    ) -> list[SalesOverTimePoint]:
        filters = self._build_filters(date_from, date_to, marketplace)
        rows = self._repository.sales_over_time(user_id=user.id, filters=filters)
        return [
            SalesOverTimePoint(
                date=row.order_date,
                revenue=_cents_to_amount(row.revenue_cents),
                orders=row.orders,
            )
            for row in rows
        ]

    def get_orders_by_status(
        self,
        *,
        user: User,
        date_from: date | None,
        date_to: date | None,
        marketplace: Marketplace | None,
    ) -> list[OrderStatusBreakdown]:
        filters = self._build_filters(date_from, date_to, marketplace)
        rows = self._repository.orders_by_status(user_id=user.id, filters=filters)
        total = sum(row.count for row in rows)
        return [
            OrderStatusBreakdown(
                status=row.status,
                count=row.count,
                percentage=round(row.count / total * 100, 1) if total > 0 else 0.0,
            )
            for row in rows
        ]

    def get_top_products(
        self,
        *,
        user: User,
        date_from: date | None,
        date_to: date | None,
        marketplace: Marketplace | None,
        limit: int = DEFAULT_TOP_PRODUCTS_LIMIT,
    ) -> list[TopProduct]:
        filters = self._build_filters(date_from, date_to, marketplace)
        rows = self._repository.top_products(user_id=user.id, filters=filters, limit=limit)
        return [
            TopProduct(
                product_name=row.product_name,
                sku=row.sku,
                quantity=row.quantity,
                revenue=_cents_to_amount(row.revenue_cents),
                orders=row.orders,
            )
            for row in rows
        ]

    def _build_filters(
        self, date_from: date | None, date_to: date | None, marketplace: Marketplace | None
    ) -> AnalyticsFilters:
        if date_from is not None and date_to is not None and date_from > date_to:
            raise InvalidAnalyticsFilterError("A data inicial não pode ser posterior à data final.")
        return AnalyticsFilters(date_from=date_from, date_to=date_to, marketplace=marketplace)

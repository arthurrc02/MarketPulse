"""Repositório de Insights.

Reaproveita `AnalyticsRepository` para tudo que já existe (totais de
período, receita por produto) em vez de duplicar SQL — só a agregação por
marketplace é nova aqui, porque nenhum KPI da Sprint 5 precisava dela (ver
ADR-067 em `docs/decisions.md`).
"""

import uuid
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.repositories.analytics import (
    AnalyticsFilters,
    AnalyticsRepository,
    OverviewRow,
    ProductRow,
    build_order_item_conditions,
)
from app.repositories.base import BaseRepository
from etl.types import Marketplace, OrderStatus

_COMPLETED = OrderStatus.COMPLETED


@dataclass(frozen=True, slots=True)
class MarketplaceRevenueRow:
    marketplace: Marketplace
    revenue_cents: int


class InsightsRepository(BaseRepository):
    """Dados agregados sobre `OrderItem`, sempre restritos a um `user_id`."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._analytics = AnalyticsRepository(session)

    def has_any_data(self, user_id: uuid.UUID) -> bool:
        return self._analytics.has_any_data(user_id)

    def period_totals(self, *, user_id: uuid.UUID, filters: AnalyticsFilters) -> OverviewRow:
        """Faturamento + pedidos `completed` de um período — mesma agregação do overview."""
        return self._analytics.overview(user_id=user_id, filters=filters)

    def product_revenue(self, *, user_id: uuid.UUID, filters: AnalyticsFilters) -> list[ProductRow]:
        """Receita `completed` por produto, **sem limite** — precisa do conjunto completo
        para comparar produto a produto entre dois períodos."""
        return self._analytics.top_products(user_id=user_id, filters=filters, limit=None)

    def revenue_by_marketplace(
        self, *, user_id: uuid.UUID, filters: AnalyticsFilters
    ) -> list[MarketplaceRevenueRow]:
        """Faturamento `completed` agrupado por marketplace — só usado por "melhor marketplace"."""
        stmt = (
            select(OrderItem.marketplace, func.coalesce(func.sum(OrderItem.total_price_cents), 0))
            .where(*build_order_item_conditions(user_id, filters, status=_COMPLETED))
            .group_by(OrderItem.marketplace)
        )
        return [
            MarketplaceRevenueRow(marketplace=row[0], revenue_cents=row[1])
            for row in self.session.execute(stmt).all()
        ]

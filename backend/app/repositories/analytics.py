"""Repositório de Analytics — todas as agregações rodam no PostgreSQL.

Nenhum método aqui carrega `OrderItem` linha a linha para o Python somar em
um loop: cada consulta já devolve o resultado agregado (`SUM`/`COUNT
DISTINCT`/`GROUP BY`), então o volume de dados trafegado do banco para a
aplicação é proporcional ao *resultado* (dias distintos, status distintos,
produtos no topo), não ao número de `OrderItem`.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

from sqlalchemy import func, select

from app.models.order_item import OrderItem
from app.repositories.base import BaseRepository
from etl.types import Marketplace, OrderStatus

_COMPLETED = OrderStatus.COMPLETED


@dataclass(frozen=True, slots=True)
class AnalyticsFilters:
    """Filtros já validados por `AnalyticsService` — o repositório não valida nada."""

    date_from: date | None = None
    date_to: date | None = None
    marketplace: Marketplace | None = None


@dataclass(frozen=True, slots=True)
class OverviewRow:
    revenue_cents: int
    orders: int
    active_products: int


@dataclass(frozen=True, slots=True)
class DailyRow:
    order_date: date
    revenue_cents: int
    orders: int


@dataclass(frozen=True, slots=True)
class StatusRow:
    status: OrderStatus
    count: int


@dataclass(frozen=True, slots=True)
class ProductRow:
    product_name: str
    sku: str
    quantity: int
    revenue_cents: int
    orders: int


class AnalyticsRepository(BaseRepository):
    """Consultas agregadas sobre `OrderItem`, sempre restritas a um `user_id`.

    "Pedido" em todo método aqui é `COUNT(DISTINCT external_order_id)`, nunca
    `COUNT(*)` — `OrderItem` é uma linha por *item*, não por pedido (ver
    docstring do model).
    """

    def has_any_data(self, user_id: uuid.UUID) -> bool:
        """`True` se o usuário tem qualquer `OrderItem`, ignorando filtros e status.

        Usado só para o frontend distinguir "nunca importei nada" de "meu
        filtro não bateu com nada" — não entra nos KPIs.
        """
        stmt = select(OrderItem.id).where(OrderItem.user_id == user_id).limit(1)
        return self.session.scalars(stmt).first() is not None

    def overview(self, *, user_id: uuid.UUID, filters: AnalyticsFilters) -> OverviewRow:
        stmt = select(
            func.coalesce(func.sum(OrderItem.total_price_cents), 0),
            func.count(func.distinct(OrderItem.external_order_id)),
            func.count(func.distinct(OrderItem.sku)),
        ).where(*self._conditions(user_id, filters, status=_COMPLETED))
        revenue_cents, orders, active_products = self.session.execute(stmt).one()
        return OverviewRow(
            revenue_cents=revenue_cents, orders=orders, active_products=active_products
        )

    def sales_over_time(self, *, user_id: uuid.UUID, filters: AnalyticsFilters) -> list[DailyRow]:
        stmt = (
            select(
                OrderItem.order_date,
                func.coalesce(func.sum(OrderItem.total_price_cents), 0),
                func.count(func.distinct(OrderItem.external_order_id)),
            )
            .where(*self._conditions(user_id, filters, status=_COMPLETED))
            .group_by(OrderItem.order_date)
            .order_by(OrderItem.order_date)
        )
        return [
            DailyRow(order_date=row[0], revenue_cents=row[1], orders=row[2])
            for row in self.session.execute(stmt).all()
        ]

    def orders_by_status(self, *, user_id: uuid.UUID, filters: AnalyticsFilters) -> list[StatusRow]:
        """Distribuição entre **todos** os status — não filtra por `completed`.

        É o único método desta classe que não restringe a `completed`: o
        propósito do endpoint é justamente mostrar a distribuição.
        """
        stmt = (
            select(OrderItem.status, func.count(func.distinct(OrderItem.external_order_id)))
            .where(*self._conditions(user_id, filters, status=None))
            .group_by(OrderItem.status)
        )
        return [StatusRow(status=row[0], count=row[1]) for row in self.session.execute(stmt).all()]

    def top_products(
        self, *, user_id: uuid.UUID, filters: AnalyticsFilters, limit: int
    ) -> list[ProductRow]:
        stmt = (
            select(
                OrderItem.product_name,
                OrderItem.sku,
                func.sum(OrderItem.quantity),
                func.coalesce(func.sum(OrderItem.total_price_cents), 0),
                func.count(func.distinct(OrderItem.external_order_id)),
            )
            .where(*self._conditions(user_id, filters, status=_COMPLETED))
            .group_by(OrderItem.product_name, OrderItem.sku)
            .order_by(func.sum(OrderItem.total_price_cents).desc())
            .limit(limit)
        )
        return [
            ProductRow(
                product_name=row[0],
                sku=row[1],
                quantity=row[2],
                revenue_cents=row[3],
                orders=row[4],
            )
            for row in self.session.execute(stmt).all()
        ]

    def _conditions(
        self, user_id: uuid.UUID, filters: AnalyticsFilters, *, status: OrderStatus | None
    ) -> list[Any]:
        conditions: list[Any] = [OrderItem.user_id == user_id]
        if status is not None:
            conditions.append(OrderItem.status == status)
        if filters.date_from is not None:
            conditions.append(OrderItem.order_date >= filters.date_from)
        if filters.date_to is not None:
            conditions.append(OrderItem.order_date <= filters.date_to)
        if filters.marketplace is not None:
            conditions.append(OrderItem.marketplace == filters.marketplace)
        return conditions

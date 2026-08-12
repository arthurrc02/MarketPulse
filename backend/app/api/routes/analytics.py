"""Rotas de Analytics. Todas protegidas por `get_current_user`.

Cada endpoint aceita os mesmos três filtros opcionais (`from`, `to`,
`marketplace`) — sempre sobre `OrderItem.user_id == current_user.id`; o
`user_id` nunca vem do cliente.
"""

from datetime import date
from typing import Annotated, Any

from fastapi import APIRouter, Query, status

from app.api.deps import AnalyticsServiceDep, CurrentUserDep
from app.schemas.analytics import (
    AnalyticsOverview,
    OrderStatusBreakdown,
    SalesOverTimePoint,
    TopProduct,
)
from app.schemas.errors import ErrorResponse
from app.services.analytics import DEFAULT_TOP_PRODUCTS_LIMIT
from etl.types import Marketplace

router = APIRouter(prefix="/analytics", tags=["analytics"])

DateFromQuery = Annotated[date | None, Query(alias="from", description="Data inicial (inclusiva).")]
DateToQuery = Annotated[date | None, Query(alias="to", description="Data final (inclusiva).")]
MarketplaceQuery = Annotated[Marketplace | None, Query(description="Filtra por marketplace.")]

#: Reaproveitado por `app.api.routes.insights` — mesma validação de período, mesmo erro.
FILTER_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse}
}


@router.get(
    "/overview",
    response_model=AnalyticsOverview,
    summary="KPIs principais (faturamento, pedidos, ticket médio, produtos ativos)",
    responses=FILTER_ERROR_RESPONSES,
)
def get_overview(
    current_user: CurrentUserDep,
    analytics_service: AnalyticsServiceDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    marketplace: MarketplaceQuery = None,
) -> AnalyticsOverview:
    return analytics_service.get_overview(
        user=current_user, date_from=date_from, date_to=date_to, marketplace=marketplace
    )


@router.get(
    "/sales-over-time",
    response_model=list[SalesOverTimePoint],
    summary="Faturamento e pedidos por dia",
    responses=FILTER_ERROR_RESPONSES,
)
def get_sales_over_time(
    current_user: CurrentUserDep,
    analytics_service: AnalyticsServiceDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    marketplace: MarketplaceQuery = None,
) -> list[SalesOverTimePoint]:
    return analytics_service.get_sales_over_time(
        user=current_user, date_from=date_from, date_to=date_to, marketplace=marketplace
    )


@router.get(
    "/orders-by-status",
    response_model=list[OrderStatusBreakdown],
    summary="Distribuição de pedidos por status",
    responses=FILTER_ERROR_RESPONSES,
)
def get_orders_by_status(
    current_user: CurrentUserDep,
    analytics_service: AnalyticsServiceDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    marketplace: MarketplaceQuery = None,
) -> list[OrderStatusBreakdown]:
    return analytics_service.get_orders_by_status(
        user=current_user, date_from=date_from, date_to=date_to, marketplace=marketplace
    )


@router.get(
    "/top-products",
    response_model=list[TopProduct],
    summary="Produtos com maior faturamento",
    responses=FILTER_ERROR_RESPONSES,
)
def get_top_products(
    current_user: CurrentUserDep,
    analytics_service: AnalyticsServiceDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    marketplace: MarketplaceQuery = None,
    limit: Annotated[int, Query(ge=1, le=50, description="Máximo de produtos retornados.")] = (
        DEFAULT_TOP_PRODUCTS_LIMIT
    ),
) -> list[TopProduct]:
    return analytics_service.get_top_products(
        user=current_user,
        date_from=date_from,
        date_to=date_to,
        marketplace=marketplace,
        limit=limit,
    )

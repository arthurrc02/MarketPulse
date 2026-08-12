"""Rota de Business Insights. Protegida por `get_current_user`.

Aceita os mesmos filtros de `GET /analytics/*` (reaproveitados daqui, não
redefinidos) — período e marketplace têm exatamente o mesmo significado nos
dois lugares.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep, InsightsServiceDep
from app.api.routes.analytics import (
    FILTER_ERROR_RESPONSES,
    DateFromQuery,
    DateToQuery,
    MarketplaceQuery,
)
from app.schemas.insights import InsightsResponse

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get(
    "",
    response_model=InsightsResponse,
    summary="Observações determinísticas sobre o desempenho do usuário",
    responses=FILTER_ERROR_RESPONSES,
)
def get_insights(
    current_user: CurrentUserDep,
    insights_service: InsightsServiceDep,
    date_from: DateFromQuery = None,
    date_to: DateToQuery = None,
    marketplace: MarketplaceQuery = None,
) -> InsightsResponse:
    return insights_service.get_insights(
        user=current_user, date_from=date_from, date_to=date_to, marketplace=marketplace
    )

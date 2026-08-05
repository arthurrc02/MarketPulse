"""Implementação concreta de `Loader` (contrato do pacote `etl`).

O motor ETL não conhece SQLAlchemy nem os models do backend (ver
`docs/architecture.md`, seção "Arquitetura do ETL"); esta classe é a ponte —
implementa o contrato `etl.loaders.base.Loader` por cima de
`OrderItemRepository`, e é instanciada/injetada pelo `ETLProcessorService`.
"""

import uuid

import pandas as pd

from app.repositories.order_item import OrderItemRepository
from etl.loaders.base import Loader
from etl.types import Marketplace


class OrderItemLoader(Loader):
    """Persiste um `DataFrame` canônico como linhas de `OrderItem`, em lote."""

    def __init__(
        self,
        *,
        repository: OrderItemRepository,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        marketplace: Marketplace,
    ) -> None:
        self._repository = repository
        self._user_id = user_id
        self._upload_id = upload_id
        self._marketplace = marketplace

    def load(self, standardized: pd.DataFrame) -> int:
        # Reprocessar um upload (botão "Processar" de novo) é idempotente:
        # os itens de uma tentativa anterior são substituídos, não duplicados.
        self._repository.delete_for_upload(self._upload_id)
        return self._repository.bulk_create(
            user_id=self._user_id,
            upload_id=self._upload_id,
            marketplace=self._marketplace,
            standardized=standardized,
        )

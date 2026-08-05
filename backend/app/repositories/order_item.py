"""Repositório de itens de pedido (`OrderItem`)."""

import uuid
from typing import Any

import pandas as pd
from sqlalchemy import delete, func, insert, select

from app.models.order_item import OrderItem
from app.repositories.base import BaseRepository
from etl.schema import CANONICAL_COLUMNS
from etl.types import Marketplace


class OrderItemRepository(BaseRepository):
    """Acesso a dados de `OrderItem`. Não abre nem confirma transações."""

    def bulk_create(
        self,
        *,
        user_id: uuid.UUID,
        upload_id: uuid.UUID,
        marketplace: Marketplace,
        standardized: pd.DataFrame,
    ) -> int:
        """Insere `standardized` em lote — um único `INSERT` multi-linha, não N inserts.

        `standardized` já está no esquema canônico (`etl.schema.CANONICAL_COLUMNS`)
        e validada; este método só acrescenta as colunas que o ETL não conhece
        (`id`, `user_id`, `upload_id`, `marketplace` — o pipeline detecta o
        marketplace antes de montar o `DataFrame`, então não faz parte do
        esquema canônico em si, que é o mesmo para qualquer marketplace).
        """
        if standardized.empty:
            return 0

        records: list[dict[str, Any]] = [
            {
                "id": uuid.uuid4(),
                "user_id": user_id,
                "upload_id": upload_id,
                "marketplace": marketplace,
                **{column: row[column] for column in CANONICAL_COLUMNS},
            }
            for row in standardized.to_dict(orient="records")
        ]
        self.session.execute(insert(OrderItem), records)
        self.session.flush()
        return len(records)

    def delete_for_upload(self, upload_id: uuid.UUID) -> None:
        """Remove itens de um processamento anterior — reprocessar um upload é idempotente."""
        self.session.execute(delete(OrderItem).where(OrderItem.upload_id == upload_id))
        self.session.flush()

    def count_for_upload(self, upload_id: uuid.UUID) -> int:
        """Usado por testes/diagnóstico — quantos itens um upload gerou."""
        stmt = select(func.count()).select_from(OrderItem).where(OrderItem.upload_id == upload_id)
        return self.session.scalar(stmt) or 0

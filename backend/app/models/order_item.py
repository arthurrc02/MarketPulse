"""Model do item de pedido — saída padronizada do pipeline ETL."""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from etl.types import Marketplace, OrderStatus

if TYPE_CHECKING:
    from app.models.upload import Upload
    from app.models.user import User


def _values_of(enum_cls: type[Enum]) -> list[str]:
    """`values_callable` compartilhado: grava o `.value` da `StrEnum`, não o nome do membro.

    Mesmo raciocínio do `UploadStatus` (ver `app/models/upload.py`) — sem
    isso, o banco gravaria `"SHOPEE"`/`"COMPLETED"` em vez de
    `"shopee"`/`"completed"`, divergindo do que a API expõe em JSON.
    """
    return [member.value for member in enum_cls]


class OrderItem(Base):
    """Uma linha de pedido já padronizada pelo pipeline ETL.

    Um registro por item de pedido (não por pedido inteiro): um pedido com
    três produtos gera três `OrderItem`, cada um com seu próprio SKU,
    quantidade e preço — é a granularidade que os indicadores da Sprint 5
    (faturamento, produtos mais vendidos) precisam, sem exigir um `JOIN`
    contra uma tabela de itens separada. Ver ADR sobre a escolha de uma
    tabela denormalizada em vez de `Order`/`Product` separados.

    `marketplace` e `status` reaproveitam os enums do pacote `etl`
    (`etl.types`) em vez de duplicar os valores aqui — o mesmo `Marketplace`
    que o pipeline ETL detecta é o que fica gravado no banco.
    """

    __tablename__ = "order_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    upload_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("uploads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    marketplace: Mapped[Marketplace] = mapped_column(
        SAEnum(
            Marketplace,
            name="order_item_marketplace",
            native_enum=False,
            length=20,
            values_callable=_values_of,
        ),
        nullable=False,
    )
    external_order_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sku: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(500), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    total_price_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), default=None)
    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_item_status",
            native_enum=False,
            length=20,
            values_callable=_values_of,
        ),
        nullable=False,
    )
    order_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )

    user: Mapped["User"] = relationship()
    upload: Mapped["Upload"] = relationship()

    def __repr__(self) -> str:
        return f"OrderItem(id={self.id!r}, sku={self.sku!r}, upload_id={self.upload_id!r})"

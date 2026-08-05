"""Model do upload de arquivos."""

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class UploadStatus(StrEnum):
    """Estado de processamento de um upload.

    Todo upload nasce `UPLOADED`. `ETLProcessorService` (Sprint 4) transiciona
    para `PROCESSING` ao iniciar, depois `PROCESSED`/`FAILED` ao concluir.
    `QUEUED` permanece reservado: o processamento desta sprint é síncrono
    (disparado por `POST /uploads/{id}/process`), sem fila real — ver ADR
    correspondente em decisions.md.
    """

    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"


class Upload(Base):
    """Um arquivo enviado por um usuário.

    `original_filename` é só metadado de exibição — nunca usado para montar
    caminho em disco. `stored_filename` é gerado pelo `UploadService`
    (`uuid4().hex` + extensão validada), evitando colisão e *path traversal*
    via nome de arquivo controlado pelo cliente. `started_at`/`finished_at`
    só são preenchidos quando o processamento ETL roda (Sprint 4).
    """

    __tablename__ = "uploads"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[UploadStatus] = mapped_column(
        # `native_enum=False`: grava como VARCHAR + CHECK, não um tipo ENUM
        # nativo do Postgres. Adicionar um status novo no futuro (a própria
        # Sprint 4 deve fazer isso) vira uma migration trivial; um ENUM nativo
        # exigiria `ALTER TYPE ... ADD VALUE` fora de transação.
        #
        # `values_callable`: sem isso, o SQLAlchemy grava o *nome* do membro
        # (`"UPLOADED"`) em vez do valor da `StrEnum` (`"uploaded"`) — o
        # mesmo valor que a API expõe em JSON. Sem essa opção, uma consulta
        # SQL direta filtrando por `status = 'uploaded'` não encontraria
        # nada, já que o banco teria `'UPLOADED'` armazenado.
        Enum(
            UploadStatus,
            name="upload_status",
            native_enum=False,
            length=20,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=UploadStatus.UPLOADED,
    )
    error_message: Mapped[str | None] = mapped_column(String(1000), default=None)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        # `default` (Python, microssegundos) além de `server_default` (SQL,
        # fallback para inserts fora do ORM): o `CURRENT_TIMESTAMP` do SQLite
        # só tem resolução de segundo — dois uploads no mesmo segundo
        # empatavam em `uploaded_at`, quebrando a ordenação "mais recente
        # primeiro". `datetime.now()` tem microssegundos em qualquer backend.
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="uploads")

    def __repr__(self) -> str:
        return f"Upload(id={self.id!r}, original_filename={self.original_filename!r})"

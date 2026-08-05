"""Schemas de upload."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.upload import UploadStatus


class UploadRead(BaseModel):
    """Representação pública de um upload — nunca inclui `stored_filename`.

    O nome de armazenamento é um detalhe interno (evita colisão e *path
    traversal*); o cliente só precisa do nome original para exibição.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    file_size: int
    mime_type: str
    status: UploadStatus
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    uploaded_at: datetime

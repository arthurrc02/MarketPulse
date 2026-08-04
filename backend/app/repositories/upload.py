"""Repositório de uploads."""

import uuid

from sqlalchemy import select

from app.models.upload import Upload, UploadStatus
from app.repositories.base import BaseRepository


class UploadRepository(BaseRepository):
    """Acesso a dados de `Upload`. Não abre nem confirma transações."""

    def get_by_id(self, upload_id: uuid.UUID) -> Upload | None:
        """Busca um upload pelo id, independentemente do dono."""
        return self.session.get(Upload, upload_id)

    def list_for_user(self, user_id: uuid.UUID) -> list[Upload]:
        """Lista os uploads de um usuário, do mais recente para o mais antigo."""
        stmt = select(Upload).where(Upload.user_id == user_id).order_by(Upload.uploaded_at.desc())
        return list(self.session.scalars(stmt).all())

    def create(
        self,
        *,
        user_id: uuid.UUID,
        original_filename: str,
        stored_filename: str,
        file_size: int,
        mime_type: str,
        status: UploadStatus,
    ) -> Upload:
        """Cria e adiciona um novo upload à sessão (sem commit)."""
        upload = Upload(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_size=file_size,
            mime_type=mime_type,
            status=status,
        )
        self.session.add(upload)
        self.session.flush()
        return upload

    def delete(self, upload: Upload) -> None:
        """Remove o registro (sem commit)."""
        self.session.delete(upload)
        self.session.flush()

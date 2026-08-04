"""Serviço de upload: validação, armazenamento e metadados."""

import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.errors import (
    FileTooLargeError,
    InvalidUploadError,
    UnsupportedFileTypeError,
    UploadNotFoundError,
)
from app.models.upload import Upload, UploadStatus
from app.models.user import User
from app.repositories.upload import UploadRepository
from app.storage.base import FileStorage

# Content-Types aceitos por extensão. Navegadores e SOs são inconsistentes ao
# reportar o Content-Type de CSV/XLSX (ver ADR em docs/decisions.md); a lista
# é deliberadamente permissiva para as variações reais mais comuns, mas a
# extensão continua sendo o critério primário — se estiver ausente do header,
# a validação de Content-Type é simplesmente pulada.
_ALLOWED_EXTENSIONS: dict[str, frozenset[str]] = {
    ".csv": frozenset({"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}),
    ".xlsx": frozenset(
        {
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/octet-stream",
            "application/zip",
        }
    ),
}

_READ_CHUNK_SIZE = 1024 * 1024  # 1 MiB


def _read_within_limit(file: BinaryIO, max_bytes: int) -> bytes:
    """Lê `file` em blocos, abortando assim que ultrapassar `max_bytes`.

    Evita carregar um arquivo arbitrariamente grande inteiro na memória só
    para descobrir, no final, que ele deveria ter sido rejeitado.
    """
    buffer = bytearray()
    while True:
        chunk = file.read(_READ_CHUNK_SIZE)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise FileTooLargeError()
    return bytes(buffer)


class UploadService:
    """Regras de negócio de upload de arquivos.

    Controla o limite transacional: cada método público confirma (`commit`)
    ao final do caminho de sucesso.
    """

    def __init__(
        self, *, session: Session, storage: FileStorage, max_upload_size_bytes: int
    ) -> None:
        self._session = session
        self._uploads = UploadRepository(session)
        self._storage = storage
        self._max_upload_size_bytes = max_upload_size_bytes

    def create_upload(self, *, user: User, file: UploadFile) -> Upload:
        """Valida, armazena e registra um novo upload.

        Raises:
            InvalidUploadError: arquivo sem nome ou vazio.
            UnsupportedFileTypeError: extensão ou Content-Type não é CSV/XLSX.
            FileTooLargeError: conteúdo excede `MAX_UPLOAD_SIZE_BYTES`.
        """
        original_filename = (file.filename or "").strip().replace("\x00", "")
        if not original_filename:
            raise InvalidUploadError("Envie um arquivo com nome válido.")

        extension = Path(original_filename).suffix.lower()
        allowed_mime_types = _ALLOWED_EXTENSIONS.get(extension)
        if allowed_mime_types is None:
            raise UnsupportedFileTypeError(
                f"Tipo de arquivo não suportado ({extension or 'sem extensão'}). "
                "Envie um arquivo CSV ou XLSX."
            )

        content_type = file.content_type
        if content_type and content_type not in allowed_mime_types:
            raise UnsupportedFileTypeError(
                f"Tipo de arquivo não suportado (Content-Type: {content_type}). "
                "Envie um arquivo CSV ou XLSX."
            )

        content = _read_within_limit(file.file, self._max_upload_size_bytes)
        if not content:
            raise InvalidUploadError("O arquivo está vazio.")

        stored_filename = f"{uuid.uuid4().hex}{extension}"
        self._storage.save(user_id=user.id, stored_filename=stored_filename, content=content)

        try:
            upload = self._uploads.create(
                user_id=user.id,
                original_filename=original_filename[:255],
                stored_filename=stored_filename,
                file_size=len(content),
                mime_type=content_type or "application/octet-stream",
                status=UploadStatus.UPLOADED,
            )
            self._session.commit()
        except Exception:
            self._session.rollback()
            self._storage.delete(user_id=user.id, stored_filename=stored_filename)
            raise

        self._session.refresh(upload)
        return upload

    def list_uploads(self, user: User) -> list[Upload]:
        """Lista os uploads do usuário, do mais recente para o mais antigo."""
        return self._uploads.list_for_user(user.id)

    def get_upload(self, *, user: User, upload_id: uuid.UUID) -> Upload:
        """Busca um upload do usuário.

        Raises:
            UploadNotFoundError: inexistente ou pertencente a outro usuário.
        """
        return self._get_owned_upload(user, upload_id)

    def delete_upload(self, *, user: User, upload_id: uuid.UUID) -> None:
        """Remove o arquivo em disco e o registro.

        Raises:
            UploadNotFoundError: inexistente ou pertencente a outro usuário.
        """
        upload = self._get_owned_upload(user, upload_id)
        self._storage.delete(user_id=user.id, stored_filename=upload.stored_filename)
        self._uploads.delete(upload)
        self._session.commit()

    def _get_owned_upload(self, user: User, upload_id: uuid.UUID) -> Upload:
        upload = self._uploads.get_by_id(upload_id)
        if upload is None or upload.user_id != user.id:
            raise UploadNotFoundError()
        return upload

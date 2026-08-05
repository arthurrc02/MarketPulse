"""Orquestração do processamento ETL de um upload.

Esta é a fronteira entre o backend e o pacote `etl`: detecta o marketplace,
monta o `ETLPipeline` (Extractor + Transformer do pacote `etl`, `Loader`
concreto daqui) e executa. Nenhuma regra de parsing, transformação ou
detecção mora aqui — só orquestração e a atualização do status do `Upload`
(ver `docs/architecture.md`, "O backend apenas orquestra o Pipeline").
"""

import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.errors import UploadNotFoundError
from app.models.upload import Upload, UploadStatus
from app.models.user import User
from app.repositories.order_item import OrderItemRepository
from app.repositories.upload import UploadRepository
from app.services.etl_loader import OrderItemLoader
from app.storage.base import FileStorage
from etl import ETLError, ETLPipeline, FileSource, SourceFormat, detect_marketplace
from etl.components import get_pipeline_components
from etl.parsing import peek_headers

logger = logging.getLogger(__name__)

_ERROR_MESSAGE_MAX_LENGTH = 1000
_GENERIC_FAILURE_MESSAGE = "Erro interno ao processar o arquivo."

_FORMAT_BY_EXTENSION: dict[str, SourceFormat] = {
    ".csv": SourceFormat.CSV,
    ".xlsx": SourceFormat.XLSX,
}


class ETLProcessorService:
    """Processa um upload já armazenado: detecta, transforma e carrega os dados.

    Chamado por `POST /uploads/{id}/process` (Sprint 4). Recebe apenas o `id`
    do upload — não um handle de arquivo aberto nem estado em memória — de
    propósito: uma futura fila (Celery/Dramatiq/RQ) chamaria este mesmo
    método a partir de um worker, sem precisar reescrever nada aqui (ver ADR
    em decisions.md sobre por que isso já deixa o código "pronto para fila").
    """

    def __init__(self, *, session: Session, storage: FileStorage) -> None:
        self._session = session
        self._uploads = UploadRepository(session)
        self._order_items = OrderItemRepository(session)
        self._storage = storage

    def process_upload(self, *, user: User, upload_id: uuid.UUID) -> Upload:
        """Executa o pipeline ETL completo sobre um upload do usuário.

        Nunca levanta uma exceção de processamento: qualquer falha (detecção,
        extração, transformação, carga) é capturada e traduzida em
        `Upload.status = FAILED` + `error_message`. Só `UploadNotFoundError`
        (upload inexistente/de outro usuário) propaga — é um erro de
        requisição, não de processamento.
        """
        upload = self._get_owned_upload(user, upload_id)

        upload.status = UploadStatus.PROCESSING
        upload.started_at = datetime.now(UTC)
        upload.finished_at = None
        upload.error_message = None
        self._session.commit()
        self._session.refresh(upload)

        try:
            rows_loaded = self._run_pipeline(upload)
        except Exception as exc:
            self._session.rollback()
            self._session.refresh(upload)
            upload.status = UploadStatus.FAILED
            upload.finished_at = datetime.now(UTC)
            upload.error_message = self._error_message_for(exc)
            self._session.commit()
            self._session.refresh(upload)
            return upload

        logger.info("upload %s processado: %d linha(s) carregada(s)", upload.id, rows_loaded)
        upload.status = UploadStatus.PROCESSED
        upload.finished_at = datetime.now(UTC)
        self._session.commit()
        self._session.refresh(upload)
        return upload

    def _run_pipeline(self, upload: Upload) -> int:
        source_format = _source_format_for(upload.original_filename)
        stream = self._storage.open(user_id=upload.user_id, stored_filename=upload.stored_filename)
        with stream:
            file_source = FileSource(stream=stream, source_format=source_format)
            marketplace = detect_marketplace(peek_headers(file_source))
            extractor, transformer = get_pipeline_components(marketplace)
            loader = OrderItemLoader(
                repository=self._order_items,
                user_id=upload.user_id,
                upload_id=upload.id,
                marketplace=marketplace,
            )
            pipeline = ETLPipeline(
                marketplace=marketplace,
                extractor=extractor,
                transformer=transformer,
                loader=loader,
            )
            result = pipeline.run(file_source)
        return result.rows_loaded

    def _error_message_for(self, exc: Exception) -> str:
        if isinstance(exc, ETLError):
            return str(exc)[:_ERROR_MESSAGE_MAX_LENGTH]
        logger.exception("falha inesperada ao processar upload")
        return _GENERIC_FAILURE_MESSAGE

    def _get_owned_upload(self, user: User, upload_id: uuid.UUID) -> Upload:
        upload = self._uploads.get_by_id(upload_id)
        if upload is None or upload.user_id != user.id:
            raise UploadNotFoundError()
        return upload


def _source_format_for(original_filename: str) -> SourceFormat:
    extension = Path(original_filename).suffix.lower()
    # `UploadService` já validou a extensão no momento do upload (Sprint 3) —
    # chegar aqui com uma extensão fora de `_FORMAT_BY_EXTENSION` seria um bug
    # de dados, não uma entrada de usuário a tratar graciosamente.
    return _FORMAT_BY_EXTENSION[extension]

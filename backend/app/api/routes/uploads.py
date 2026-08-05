"""Rotas de upload de arquivos. Todas protegidas por `get_current_user`."""

import uuid

from fastapi import APIRouter, File, UploadFile, status

from app.api.deps import CurrentUserDep, ETLProcessorServiceDep, UploadServiceDep
from app.schemas.errors import ErrorResponse
from app.schemas.upload import UploadRead

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post(
    "",
    response_model=UploadRead,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar um arquivo",
    responses={
        status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorResponse},
        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE: {"model": ErrorResponse},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    },
)
def create_upload(
    current_user: CurrentUserDep,
    upload_service: UploadServiceDep,
    file: UploadFile = File(description="Arquivo CSV ou XLSX."),
) -> UploadRead:
    """Armazena o arquivo enviado. Nenhum processamento acontece aqui."""
    upload = upload_service.create_upload(user=current_user, file=file)
    return UploadRead.model_validate(upload)


@router.get(
    "",
    response_model=list[UploadRead],
    summary="Listar uploads",
)
def list_uploads(
    current_user: CurrentUserDep, upload_service: UploadServiceDep
) -> list[UploadRead]:
    """Lista os uploads do usuário autenticado, do mais recente para o mais antigo."""
    uploads = upload_service.list_uploads(current_user)
    return [UploadRead.model_validate(upload) for upload in uploads]


@router.get(
    "/{upload_id}",
    response_model=UploadRead,
    summary="Detalhes de um upload",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def get_upload(
    upload_id: uuid.UUID, current_user: CurrentUserDep, upload_service: UploadServiceDep
) -> UploadRead:
    """Retorna os metadados de um upload do usuário autenticado."""
    upload = upload_service.get_upload(user=current_user, upload_id=upload_id)
    return UploadRead.model_validate(upload)


@router.delete(
    "/{upload_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Excluir um upload",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def delete_upload(
    upload_id: uuid.UUID, current_user: CurrentUserDep, upload_service: UploadServiceDep
) -> None:
    """Remove o arquivo em disco e o registro do upload."""
    upload_service.delete_upload(user=current_user, upload_id=upload_id)


@router.post(
    "/{upload_id}/process",
    response_model=UploadRead,
    summary="Processar um upload (ETL)",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
)
def process_upload(
    upload_id: uuid.UUID, current_user: CurrentUserDep, etl_service: ETLProcessorServiceDep
) -> UploadRead:
    """Dispara o processamento ETL do upload e retorna o resultado.

    Síncrono nesta sprint: a resposta só chega depois que o processamento
    termina, com `status` já em `processed` ou `failed` (nunca `processing` —
    ver [ADR em decisions.md]). Falhas de processamento (marketplace não
    reconhecido, arquivo corrompido, dados inválidos) **não** viram erro
    HTTP — voltam como `200` com `status: "failed"` e `error_message`
    preenchido; só a ausência do upload (ou pertencer a outro usuário) é um
    erro de requisição de verdade (`404`).
    """
    upload = etl_service.process_upload(user=current_user, upload_id=upload_id)
    return UploadRead.model_validate(upload)

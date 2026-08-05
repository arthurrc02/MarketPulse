"""Testes de integração do processamento ETL (`POST /uploads/{id}/process`).

Cobre o fluxo router → `ETLProcessorService` → pacote `etl` → `OrderItem`,
incluindo os casos de falha exigidos pela Sprint 4: marketplace desconhecido,
arquivo ilegível, dados inválidos após a transformação, e que uma falha não
deixa itens parciais gravados.
"""

import io
import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.order_item import OrderItem
from app.models.upload import Upload

VALID_PASSWORD = "Sup3rSecret!"

SHOPEE_HEADER = "ID do Pedido,SKU,Produto,Quantidade,Preco Unitario,Status,Data do Pedido"
SHOPEE_VALID_ROW = '1001,SKU-A,Camiseta Azul,2,"R$ 49,90",Concluido,05/08/2026'
SHOPEE_INVALID_CURRENCY_ROW = '1001,SKU-A,Camiseta Azul,2,"nao e um preco",Concluido,05/08/2026'

MERCADO_LIVRE_HEADER = (
    "Numero da Venda,Codigo do Anuncio,Titulo do Anuncio,Unidades,Valor Unitario,"
    "Percentual de Desconto,Situacao da Venda,Data da Venda"
)
MERCADO_LIVRE_VALID_ROW = 'V-1,ML-SKU-1,Fone Bluetooth,3,"R$ 199,90","10,5%",Entregue,04/08/2026'


def _auth_headers(client: TestClient, *, email: str = "user@example.com") -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": VALID_PASSWORD})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _upload_csv(
    client: TestClient, headers: dict[str, str], *, filename: str, content: bytes
) -> Any:
    return client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": (filename, content, "text/csv")},
    )


def _shopee_csv(row: str = SHOPEE_VALID_ROW) -> bytes:
    return f"{SHOPEE_HEADER}\n{row}\n".encode()


def _mercado_livre_csv(row: str = MERCADO_LIVRE_VALID_ROW) -> bytes:
    return f"{MERCADO_LIVRE_HEADER}\n{row}\n".encode()


def _shopee_xlsx() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(SHOPEE_HEADER.split(","))
    sheet.append(["1001", "SKU-A", "Camiseta Azul", 2, "R$ 49,90", "Concluido", "05/08/2026"])
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def _order_item_count(db_session: Session, upload_id: str) -> int:
    stmt = (
        select(func.count())
        .select_from(OrderItem)
        .where(OrderItem.upload_id == uuid.UUID(upload_id))
    )
    return db_session.scalar(stmt) or 0


# ---------------------------------------------------------------------------
# Sucesso: CSV, XLSX, transição de status completa
# ---------------------------------------------------------------------------


def test_process_valid_csv_marks_upload_as_processed(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers, filename="shopee.csv", content=_shopee_csv()).json()[
        "id"
    ]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processed"
    assert body["error_message"] is None
    assert body["started_at"] is not None
    assert body["finished_at"] is not None
    assert _order_item_count(db_session, upload_id) == 1


def test_process_valid_xlsx_marks_upload_as_processed(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={
            "file": (
                "shopee.xlsx",
                _shopee_xlsx(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    upload_id = response.json()["id"]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert _order_item_count(db_session, upload_id) == 1


def test_process_mercado_livre_csv_marks_upload_as_processed(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(
        client, headers, filename="ml.csv", content=_mercado_livre_csv()
    ).json()["id"]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "processed"
    assert _order_item_count(db_session, upload_id) == 1


def test_process_persists_started_and_finished_timestamps_on_the_upload_row(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers, filename="shopee.csv", content=_shopee_csv()).json()[
        "id"
    ]

    client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    upload = db_session.get(Upload, uuid.UUID(upload_id))
    assert upload is not None
    assert upload.started_at is not None
    assert upload.finished_at is not None
    assert upload.finished_at >= upload.started_at


# ---------------------------------------------------------------------------
# Falhas: marketplace desconhecido, parser inválido, transformação
# ---------------------------------------------------------------------------


def test_process_unknown_marketplace_marks_upload_as_failed(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    content = b"Coluna A,Coluna B\nx,y\n"
    upload_id = _upload_csv(client, headers, filename="desconhecido.csv", content=content).json()[
        "id"
    ]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert body["error_message"] is not None
    assert "marketplace" in body["error_message"].lower()
    assert _order_item_count(db_session, upload_id) == 0


def test_process_unparseable_file_marks_upload_as_failed(
    client: TestClient, db_session: Session
) -> None:
    """Um `.xlsx` com bytes corrompidos falha na extração, não na detecção."""
    headers = _auth_headers(client)
    response = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={
            "file": (
                "corrompido.xlsx",
                b"isto claramente nao e um arquivo xlsx valido",
                "application/octet-stream",
            )
        },
    )
    upload_id = response.json()["id"]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert response.json()["error_message"] is not None


def test_process_invalid_data_marks_upload_as_failed_with_row_context(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(
        client, headers, filename="shopee.csv", content=_shopee_csv(SHOPEE_INVALID_CURRENCY_ROW)
    ).json()["id"]

    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "failed"
    assert "linha 2" in (body["error_message"] or "")


@pytest.mark.parametrize(
    "content",
    [b"Coluna A,Coluna B\nx,y\n", b"isto nao e um xlsx"],
    ids=["marketplace_desconhecido", "arquivo_ilegivel"],
)
def test_process_failure_never_leaves_partial_order_items(
    content: bytes, client: TestClient, db_session: Session
) -> None:
    """Nenhuma falha de processamento deve deixar itens órfãos gravados."""
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers, filename="ruim.csv", content=content).json()["id"]

    client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)

    assert _order_item_count(db_session, upload_id) == 0


# ---------------------------------------------------------------------------
# Reprocessamento idempotente (Loader substitui, não duplica)
# ---------------------------------------------------------------------------


def test_reprocessing_replaces_order_items_instead_of_duplicating(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers, filename="shopee.csv", content=_shopee_csv()).json()[
        "id"
    ]

    client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)
    assert _order_item_count(db_session, upload_id) == 1

    client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)
    assert _order_item_count(db_session, upload_id) == 1


# ---------------------------------------------------------------------------
# Autenticação e propriedade
# ---------------------------------------------------------------------------


def test_process_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/uploads/00000000-0000-0000-0000-000000000000/process")

    assert response.status_code == 401


def test_process_404_for_nonexistent_upload(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/uploads/00000000-0000-0000-0000-000000000000/process", headers=headers
    )

    assert response.status_code == 404


def test_process_404_for_another_users_upload(client: TestClient) -> None:
    headers_a = _auth_headers(client, email="user-a@example.com")
    upload_id = _upload_csv(client, headers_a, filename="shopee.csv", content=_shopee_csv()).json()[
        "id"
    ]

    headers_b = _auth_headers(client, email="user-b@example.com")
    response = client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers_b)

    assert response.status_code == 404


def test_deleting_an_upload_cascades_to_its_order_items(
    client: TestClient, db_session: Session
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers, filename="shopee.csv", content=_shopee_csv()).json()[
        "id"
    ]
    client.post(f"/api/v1/uploads/{upload_id}/process", headers=headers)
    assert _order_item_count(db_session, upload_id) == 1

    client.delete(f"/api/v1/uploads/{upload_id}", headers=headers)

    assert _order_item_count(db_session, upload_id) == 0

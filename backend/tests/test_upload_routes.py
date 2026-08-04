"""Testes de integração do fluxo de upload (router → service → repo → storage)."""

from pathlib import Path
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.deps import get_upload_service
from app.services.upload import UploadService
from app.storage.local import LocalFileStorage

VALID_PASSWORD = "Sup3rSecret!"


def _auth_headers(client: TestClient, *, email: str = "user@example.com") -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": VALID_PASSWORD})
    response = client.post("/api/v1/auth/login", json={"email": email, "password": VALID_PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _upload_csv(
    client: TestClient,
    headers: dict[str, str],
    *,
    filename: str = "relatorio.csv",
    content: bytes = b"pedido,valor\n1,100\n",
    content_type: str = "text/csv",
) -> Any:
    return client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": (filename, content, content_type)},
    )


# ---------------------------------------------------------------------------
# POST /uploads
# ---------------------------------------------------------------------------


def test_upload_csv_succeeds_and_is_stored_on_disk(
    client: TestClient, upload_storage_dir: Path
) -> None:
    headers = _auth_headers(client)

    response = _upload_csv(client, headers)

    assert response.status_code == 201
    body = response.json()
    assert body["original_filename"] == "relatorio.csv"
    assert body["status"] == "uploaded"
    assert body["file_size"] == len(b"pedido,valor\n1,100\n")
    assert body["mime_type"] == "text/csv"
    assert "stored_filename" not in body

    stored_files = list(upload_storage_dir.rglob("*.csv"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == b"pedido,valor\n1,100\n"


def test_upload_xlsx_succeeds(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={
            "file": (
                "vendas.xlsx",
                b"fake-xlsx-bytes",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["original_filename"] == "vendas.xlsx"


def test_upload_accepts_uppercase_extension(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = _upload_csv(client, headers, filename="RELATORIO.CSV")

    assert response.status_code == 201


def test_upload_rejects_unsupported_extension(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("malware.exe", b"conteudo", "application/octet-stream")},
    )

    assert response.status_code == 415


def test_upload_rejects_mismatched_content_type(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = _upload_csv(client, headers, content_type="application/pdf")

    assert response.status_code == 415


def test_upload_rejects_empty_file(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = _upload_csv(client, headers, content=b"")

    assert response.status_code == 422


def test_upload_rejects_missing_filename(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.post(
        "/api/v1/uploads",
        headers=headers,
        files={"file": ("", b"conteudo", "text/csv")},
    )

    assert response.status_code == 422


def test_upload_rejects_file_over_size_limit(
    app: FastAPI, client: TestClient, db_session: Session, upload_storage_dir: Path
) -> None:
    def _tiny_limit_upload_service() -> UploadService:
        return UploadService(
            session=db_session,
            storage=LocalFileStorage(upload_storage_dir),
            max_upload_size_bytes=10,
        )

    app.dependency_overrides[get_upload_service] = _tiny_limit_upload_service
    headers = _auth_headers(client)

    response = _upload_csv(client, headers, content=b"x" * 1000)

    assert response.status_code == 413


def test_upload_requires_authentication(client: TestClient) -> None:
    response = client.post("/api/v1/uploads", files={"file": ("a.csv", b"conteudo", "text/csv")})

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /uploads
# ---------------------------------------------------------------------------


def test_list_uploads_returns_only_current_users_files(client: TestClient) -> None:
    headers_a = _auth_headers(client, email="user-a@example.com")
    _upload_csv(client, headers_a, filename="a.csv")

    headers_b = _auth_headers(client, email="user-b@example.com")
    _upload_csv(client, headers_b, filename="b.csv")

    response = client.get("/api/v1/uploads", headers=headers_a)

    assert response.status_code == 200
    filenames = [item["original_filename"] for item in response.json()]
    assert filenames == ["a.csv"]


def test_list_uploads_orders_most_recent_first(client: TestClient) -> None:
    headers = _auth_headers(client)
    _upload_csv(client, headers, filename="first.csv")
    _upload_csv(client, headers, filename="second.csv")

    response = client.get("/api/v1/uploads", headers=headers)

    filenames = [item["original_filename"] for item in response.json()]
    assert filenames == ["second.csv", "first.csv"]


def test_list_uploads_requires_authentication(client: TestClient) -> None:
    response = client.get("/api/v1/uploads")

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /uploads/{id}
# ---------------------------------------------------------------------------


def test_get_upload_detail_succeeds(client: TestClient) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers).json()["id"]

    response = client.get(f"/api/v1/uploads/{upload_id}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == upload_id


def test_get_upload_detail_404_for_nonexistent_id(client: TestClient) -> None:
    headers = _auth_headers(client)

    response = client.get("/api/v1/uploads/00000000-0000-0000-0000-000000000000", headers=headers)

    assert response.status_code == 404


def test_get_upload_detail_404_for_another_users_upload(client: TestClient) -> None:
    headers_a = _auth_headers(client, email="user-a@example.com")
    upload_id = _upload_csv(client, headers_a).json()["id"]

    headers_b = _auth_headers(client, email="user-b@example.com")
    response = client.get(f"/api/v1/uploads/{upload_id}", headers=headers_b)

    assert response.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /uploads/{id}
# ---------------------------------------------------------------------------


def test_delete_upload_removes_record_and_file(
    client: TestClient, upload_storage_dir: Path
) -> None:
    headers = _auth_headers(client)
    upload_id = _upload_csv(client, headers).json()["id"]
    assert list(upload_storage_dir.rglob("*.csv"))

    response = client.delete(f"/api/v1/uploads/{upload_id}", headers=headers)

    assert response.status_code == 204
    assert client.get(f"/api/v1/uploads/{upload_id}", headers=headers).status_code == 404
    assert not list(upload_storage_dir.rglob("*.csv"))


def test_delete_upload_404_for_another_users_upload(client: TestClient) -> None:
    headers_a = _auth_headers(client, email="user-a@example.com")
    upload_id = _upload_csv(client, headers_a).json()["id"]

    headers_b = _auth_headers(client, email="user-b@example.com")
    response = client.delete(f"/api/v1/uploads/{upload_id}", headers=headers_b)

    assert response.status_code == 404


def test_delete_upload_requires_authentication(client: TestClient) -> None:
    response = client.delete("/api/v1/uploads/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 401


@pytest.mark.parametrize("method", ["get", "delete"])
def test_upload_detail_routes_reject_invalid_uuid(client: TestClient, method: str) -> None:
    headers = _auth_headers(client)

    response = getattr(client, method)("/api/v1/uploads/not-a-uuid", headers=headers)

    assert response.status_code == 422

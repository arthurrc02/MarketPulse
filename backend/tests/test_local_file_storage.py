"""Testes de `LocalFileStorage`, isolados da camada HTTP."""

import uuid
from pathlib import Path

import pytest

from app.storage.local import LocalFileStorage


@pytest.fixture
def storage(tmp_path: Path) -> LocalFileStorage:
    return LocalFileStorage(tmp_path / "uploads")


def test_save_creates_the_per_user_directory(storage: LocalFileStorage, tmp_path: Path) -> None:
    user_id = uuid.uuid4()

    storage.save(user_id=user_id, stored_filename="a.csv", content=b"conteudo")

    assert (tmp_path / "uploads" / str(user_id) / "a.csv").read_bytes() == b"conteudo"


def test_save_and_open_round_trip(storage: LocalFileStorage) -> None:
    user_id = uuid.uuid4()
    storage.save(user_id=user_id, stored_filename="relatorio.xlsx", content=b"\x00binary\x01data")

    with storage.open(user_id=user_id, stored_filename="relatorio.xlsx") as file:
        assert file.read() == b"\x00binary\x01data"


def test_two_users_do_not_share_a_namespace(storage: LocalFileStorage) -> None:
    user_a, user_b = uuid.uuid4(), uuid.uuid4()
    storage.save(user_id=user_a, stored_filename="same-name.csv", content=b"from a")
    storage.save(user_id=user_b, stored_filename="same-name.csv", content=b"from b")

    with storage.open(user_id=user_a, stored_filename="same-name.csv") as file:
        assert file.read() == b"from a"
    with storage.open(user_id=user_b, stored_filename="same-name.csv") as file:
        assert file.read() == b"from b"


def test_delete_removes_the_file(storage: LocalFileStorage, tmp_path: Path) -> None:
    user_id = uuid.uuid4()
    storage.save(user_id=user_id, stored_filename="a.csv", content=b"x")

    storage.delete(user_id=user_id, stored_filename="a.csv")

    assert not (tmp_path / "uploads" / str(user_id) / "a.csv").exists()


def test_delete_is_idempotent_for_a_missing_file(storage: LocalFileStorage) -> None:
    """Não deve lançar exceção mesmo se o arquivo já não existir."""
    storage.delete(user_id=uuid.uuid4(), stored_filename="never-existed.csv")

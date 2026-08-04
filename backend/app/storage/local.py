"""Armazenamento local em disco, organizado por usuário."""

import uuid
from pathlib import Path
from typing import BinaryIO

from app.storage.base import FileStorage


class LocalFileStorage(FileStorage):
    """Grava arquivos em `{root}/{user_id}/{stored_filename}`.

    Sem S3/nuvem nesta sprint (ver ADR correspondente em `docs/decisions.md`).
    """

    def __init__(self, root: Path) -> None:
        self._root = root

    def _path_for(self, user_id: uuid.UUID, stored_filename: str) -> Path:
        return self._root / str(user_id) / stored_filename

    def save(self, *, user_id: uuid.UUID, stored_filename: str, content: bytes) -> None:
        target = self._path_for(user_id, stored_filename)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def open(self, *, user_id: uuid.UUID, stored_filename: str) -> BinaryIO:
        return self._path_for(user_id, stored_filename).open("rb")

    def delete(self, *, user_id: uuid.UUID, stored_filename: str) -> None:
        self._path_for(user_id, stored_filename).unlink(missing_ok=True)

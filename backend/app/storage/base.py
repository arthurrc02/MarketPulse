"""Contrato de armazenamento de arquivos."""

import uuid
from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorage(ABC):
    """Persiste e recupera o conteúdo bruto de um upload.

    Implementações não conhecem `Upload` (o model) nem regras de negócio —
    apenas gravam/leem bytes associados a um usuário e um nome de arquivo já
    decidido pela camada de serviço (`stored_filename`, opaco e único).
    """

    @abstractmethod
    def save(self, *, user_id: uuid.UUID, stored_filename: str, content: bytes) -> None:
        """Grava `content`, criando o diretório do usuário se necessário."""
        raise NotImplementedError

    @abstractmethod
    def open(self, *, user_id: uuid.UUID, stored_filename: str) -> BinaryIO:
        """Abre o arquivo para leitura binária.

        Não utilizado nesta sprint — existe para o motor ETL (Sprint 4)
        consumir os uploads já existentes sem precisar de uma nova interface.
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, *, user_id: uuid.UUID, stored_filename: str) -> None:
        """Remove o arquivo. Idempotente: não falha se ele já não existir."""
        raise NotImplementedError

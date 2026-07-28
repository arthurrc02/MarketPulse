"""Repositório base compartilhado pelos repositórios concretos."""

from sqlalchemy.orm import Session


class BaseRepository:
    """Contrato mínimo de um repositório: operar sobre uma sessão injetada.

    Repositórios nunca abrem nem encerram transações por conta própria — isso
    é responsabilidade da camada de serviço, que recebe a sessão via injeção
    de dependência do FastAPI.
    """

    def __init__(self, session: Session) -> None:
        self.session = session

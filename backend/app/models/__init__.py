"""Models do SQLAlchemy.

Todo model deve ser importado aqui para ser registrado no ``Base.metadata`` e
detectado pelo autogenerate do Alembic.
"""

from app.db.base import Base
from app.models.refresh_token import RefreshToken
from app.models.user import User

__all__ = ["Base", "RefreshToken", "User"]

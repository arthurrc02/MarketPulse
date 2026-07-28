"""Base declarativa do SQLAlchemy.

Todos os models devem herdar de :class:`Base` e ser importados em
``app.models`` para que o Alembic os enxergue no autogenerate.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Convenção de nomes explícita: garante que constraints geradas pelo Alembic
# tenham nomes determinísticos (indispensável para downgrades em PostgreSQL).
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Base declarativa compartilhada por todos os models do MarketPulse."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

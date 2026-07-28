"""Contrato da etapa de carga."""

from abc import ABC, abstractmethod

import pandas as pd


class Loader(ABC):
    """Persiste os dados já padronizados.

    O módulo ETL não conhece SQLAlchemy nem os models do backend: a
    implementação concreta é injetada pela camada de serviço, mantendo o
    motor ETL independente da infraestrutura de persistência.
    """

    @abstractmethod
    def load(self, standardized: pd.DataFrame) -> int:
        """Persiste ``standardized`` e devolve a quantidade de registros gravados."""
        raise NotImplementedError

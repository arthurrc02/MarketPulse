"""Exceções do motor ETL."""


class ETLError(Exception):
    """Erro base de qualquer etapa do pipeline ETL."""


class ExtractionError(ETLError):
    """Falha ao ler ou interpretar o arquivo de origem."""


class TransformationError(ETLError):
    """Falha ao padronizar os dados para o modelo canônico."""


class LoadError(ETLError):
    """Falha ao persistir os dados padronizados."""

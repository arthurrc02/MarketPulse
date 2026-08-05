"""Leitura bruta de arquivos tabulares (CSV/XLSX), sem regra de negócio.

Fica fora de `extractors/` de propósito: normalizar cabeçalho e despachar
entre `pandas.read_csv`/`read_excel` é comportamento de **formato**
(csv vs. xlsx), igual para qualquer marketplace — não é algo que cada
`Extractor` concreto deveria reimplementar.
"""

import re
from dataclasses import dataclass
from typing import BinaryIO

import pandas as pd

from etl.exceptions import ExtractionError
from etl.types import SourceFormat

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_column_name(name: object) -> str:
    """`" Data  Pedido "` → `"data_pedido"`.

    Resiliência a espaços e capitalização inconsistentes entre exportações
    do mesmo marketplace (planilhas editadas manualmente, versões diferentes
    do relatório etc.) — a comparação de colunas no resto do ETL é sempre
    feita por nome normalizado, nunca por posição.
    """
    return _WHITESPACE_RE.sub("_", str(name).strip().lower())


@dataclass(slots=True)
class FileSource:
    """Um arquivo em memória a ser lido pelo ETL.

    Carrega o `SourceFormat` ao lado do stream porque um `BinaryIO` puro não
    tem extensão nem Content-Type — é a única forma de decidir entre
    `read_csv`/`read_excel` sem reintroduzir uma dependência de caminho em
    disco no contrato do `Extractor` (ver ADR sobre `Path` → `FileSource`
    em decisions.md).
    """

    stream: BinaryIO
    source_format: SourceFormat


def read_tabular_file(source: FileSource) -> pd.DataFrame:
    """Lê `source` inteiro num DataFrame de strings, com colunas normalizadas.

    `dtype=str` é deliberado: qualquer conversão de tipo (datas, valores
    monetários, percentuais) é regra do `Transformer`, não da leitura bruta —
    a inferência automática do pandas arriscaria descartar zeros à esquerda
    em SKUs/IDs ou aplicar parsing numérico antes da hora.
    """
    source.stream.seek(0)
    try:
        if source.source_format is SourceFormat.CSV:
            frame = pd.read_csv(source.stream, dtype=str, keep_default_na=False)
        else:
            frame = pd.read_excel(source.stream, dtype=str, engine="openpyxl")
    except ExtractionError:
        raise
    except Exception as exc:
        raise ExtractionError(f"Não foi possível ler o arquivo: {exc}") from exc

    frame.columns = pd.Index([normalize_column_name(column) for column in frame.columns])
    return frame.fillna("")


def peek_headers(source: FileSource) -> list[str]:
    """Lê só a linha de cabeçalho — usado pela detecção de marketplace.

    Evita carregar o arquivo inteiro só para decidir, em seguida, que o
    marketplace é desconhecido.
    """
    source.stream.seek(0)
    try:
        if source.source_format is SourceFormat.CSV:
            frame = pd.read_csv(source.stream, dtype=str, nrows=0)
        else:
            frame = pd.read_excel(source.stream, dtype=str, engine="openpyxl", nrows=0)
    except Exception as exc:
        raise ExtractionError(f"Não foi possível ler o cabeçalho do arquivo: {exc}") from exc
    finally:
        source.stream.seek(0)
    return [normalize_column_name(column) for column in frame.columns]

"""Normalização e correspondência por assinatura de colunas.

Extraído para cá (hotfix Sprint 4.1) porque a detecção por *lista completa e
fixa de colunas* se mostrou frágil demais: um relatório oficial real usa
nomes de coluna diferentes dos escolhidos para o formato de exemplo. A
alternativa é reconhecer o marketplace por um pequeno conjunto de **conceitos
característicos** — cada um aceitando mais de uma grafia (idioma, pequenas
variações) — em vez de exigir um conjunto fechado e exaustivo. Ver ADR-060
em `docs/decisions.md`.
"""

import unicodedata
from collections.abc import Iterable


def signature_key(value: str) -> str:
    """Normaliza um nome de coluna para comparação de assinatura.

    Mais agressivo que `etl.parsing.normalize_column_name` (usado na leitura
    bruta do arquivo, compartilhado com os `Extractor`s — inalterado por
    este hotfix): remove acentos (decomposição NFKD + descarte dos
    caracteres combinantes) e qualquer caractere que não seja letra ou
    dígito. `"ID do Pedido"`, `"Id do  Pedido"`, `"íd do pedido"` e o
    `"id_do_pedido"` já normalizado por `peek_headers` colapsam todos para a
    mesma chave (`"iddopedido"`).
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_accents = "".join(char for char in decomposed if not unicodedata.combining(char))
    return "".join(char for char in without_accents.lower() if char.isalnum())


def concept(*spellings: str) -> frozenset[str]:
    """Constrói um "conceito" da assinatura a partir de grafias em texto legível.

    Um conceito é satisfeito se **qualquer uma** das grafias aparecer no
    arquivo — não é preciso escrever a chave normalizada à mão em cada
    detector.
    """
    return frozenset(signature_key(spelling) for spelling in spellings)


def matches_signature(headers: Iterable[str], concepts: Iterable[frozenset[str]]) -> bool:
    """`True` se, para **cada** item de `concepts`, ao menos uma grafia aparecer em `headers`.

    `headers` pode vir em qualquer normalização prévia (ou nenhuma) — os
    dois lados passam por `signature_key` antes de comparar, então a origem
    do arquivo (já processado por `peek_headers` ou não) não importa.
    """
    keys = {signature_key(header) for header in headers}
    return all(required & keys for required in concepts)

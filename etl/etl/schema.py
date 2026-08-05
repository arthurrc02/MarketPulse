"""Esquema canônico de saída do `Transformer` — o contrato entre Transform e Load.

Qualquer marketplace novo (`etl.transformers.<marketplace>`) deve produzir um
`DataFrame` com exatamente estas colunas; é o que permite ao `Loader` (e ao
model `OrderItem` do backend) permanecer o mesmo independentemente de quantos
marketplaces existirem.
"""

import datetime

import pandas as pd

from etl.exceptions import TransformationError
from etl.types import OrderStatus

#: Nome das colunas que todo `Transformer` deve produzir, nesta ordem.
CANONICAL_COLUMNS: tuple[str, ...] = (
    "external_order_id",
    "sku",
    "product_name",
    "quantity",
    "unit_price_cents",
    "total_price_cents",
    "discount_percentage",
    "status",
    "order_date",
)

_VALID_STATUSES = frozenset(status.value for status in OrderStatus)


def _is_invalid_discount(value: object) -> bool:
    """`None` (sem desconto) é válido; qualquer `float` fora de 0-100 não é."""
    if not isinstance(value, float):
        return False
    return not 0 <= value <= 100


def validate_canonical_schema(standardized: pd.DataFrame) -> None:
    """Garante que `standardized` está em conformidade com `CANONICAL_COLUMNS`.

    É a etapa "Validação" do fluxo ETL (Extractor → Transformer → Validação →
    Persistência): roda depois do `Transformer` e antes do `Loader`, e é
    deliberadamente independente de marketplace — a essa altura os dados já
    estão no formato canônico, então as mesmas regras valem para qualquer
    origem.

    Raises:
        TransformationError: coluna ausente ou linha com valor fora do
            esperado (lista até 5 problemas na mensagem, para não estourar
            `Upload.error_message`).
    """
    missing = [column for column in CANONICAL_COLUMNS if column not in standardized.columns]
    if missing:
        raise TransformationError(f"Colunas ausentes após a transformação: {', '.join(missing)}.")

    issues: list[str] = []

    for column in ("external_order_id", "sku", "product_name", "status"):
        blank = standardized[column].astype(str).str.strip().eq("")
        for row_number in standardized.index[blank][:5]:
            issues.append(f"linha {row_number + 2}: '{column}' vazio")

    invalid_status = ~standardized["status"].isin(_VALID_STATUSES)
    for row_number in standardized.index[invalid_status][:5]:
        issues.append(f"linha {row_number + 2}: status desconhecido")

    for column in ("quantity", "unit_price_cents", "total_price_cents"):
        not_int = standardized[column].map(lambda value: not isinstance(value, int))
        negative = standardized[column].map(lambda value: isinstance(value, int) and value < 0)
        invalid = not_int | negative
        for row_number in standardized.index[invalid][:5]:
            issues.append(f"linha {row_number + 2}: '{column}' deve ser um inteiro >= 0")

    not_a_date = standardized["order_date"].map(lambda value: not isinstance(value, datetime.date))
    for row_number in standardized.index[not_a_date][:5]:
        issues.append(f"linha {row_number + 2}: 'order_date' inválida")

    invalid_discount = standardized["discount_percentage"].map(_is_invalid_discount)
    for row_number in standardized.index[invalid_discount][:5]:
        issues.append(f"linha {row_number + 2}: 'discount_percentage' fora de 0-100")

    if issues:
        preview = "; ".join(issues[:5])
        raise TransformationError(f"Dados inválidos após a transformação: {preview}.")

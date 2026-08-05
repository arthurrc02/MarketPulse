"""Transformer do formato de exemplo Mercado Livre.

Colunas brutas esperadas (já normalizadas por `read_tabular_file`):
`numero_da_venda`, `codigo_do_anuncio`, `titulo_do_anuncio`, `unidades`,
`valor_unitario`, `percentual_de_desconto`, `situacao_da_venda`,
`data_da_venda`. Ver `etl.detectors.mercado_livre` para o conjunto exato
exigido na detecção.
"""

import pandas as pd

from etl.exceptions import TransformationError
from etl.transformers.base import Transformer
from etl.transformers.common import (
    build_canonical_frame,
    map_status,
    parse_brl_currency_to_cents,
    parse_date_brazilian,
    parse_identifier,
    parse_percentage,
    parse_quantity,
    parse_text,
)
from etl.types import Marketplace, OrderStatus

_STATUS_MAP: dict[str, OrderStatus] = {
    "entregue": OrderStatus.COMPLETED,
    "em processamento": OrderStatus.PENDING,
    "cancelada": OrderStatus.CANCELLED,
    "reembolsada": OrderStatus.REFUNDED,
}


class MercadoLivreTransformer(Transformer):
    """Padroniza um relatório Mercado Livre bruto no esquema canônico de pedidos."""

    marketplace = Marketplace.MERCADO_LIVRE

    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for line_number, record in enumerate(raw.to_dict(orient="records"), start=2):
            try:
                unit_price_cents = parse_brl_currency_to_cents(record["valor_unitario"])
                quantity = parse_quantity(record["unidades"])
                rows.append(
                    {
                        "external_order_id": parse_identifier(record["numero_da_venda"]),
                        "sku": parse_identifier(record["codigo_do_anuncio"]),
                        "product_name": parse_text(record["titulo_do_anuncio"]),
                        "quantity": quantity,
                        "unit_price_cents": unit_price_cents,
                        "total_price_cents": unit_price_cents * quantity,
                        "discount_percentage": parse_percentage(record["percentual_de_desconto"]),
                        "status": map_status(record["situacao_da_venda"], _STATUS_MAP),
                        "order_date": parse_date_brazilian(record["data_da_venda"]),
                    }
                )
            except KeyError as exc:
                raise TransformationError(
                    f"linha {line_number}: coluna esperada ausente ({exc})"
                ) from exc
            except TransformationError as exc:
                raise TransformationError(f"linha {line_number}: {exc}") from exc

        return build_canonical_frame(rows)

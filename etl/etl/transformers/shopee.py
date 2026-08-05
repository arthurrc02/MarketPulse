"""Transformer do formato de exemplo Shopee.

Colunas brutas esperadas (já normalizadas por `read_tabular_file`):
`id_do_pedido`, `sku`, `produto`, `quantidade`, `preco_unitario`, `status`,
`data_do_pedido`. Ver `etl.detectors.shopee` para o conjunto exato exigido
na detecção.
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
    parse_quantity,
    parse_text,
)
from etl.types import Marketplace, OrderStatus

_STATUS_MAP: dict[str, OrderStatus] = {
    "concluido": OrderStatus.COMPLETED,
    "concluído": OrderStatus.COMPLETED,
    "pendente": OrderStatus.PENDING,
    "cancelado": OrderStatus.CANCELLED,
}


class ShopeeTransformer(Transformer):
    """Padroniza um relatório Shopee bruto no esquema canônico de pedidos."""

    marketplace = Marketplace.SHOPEE

    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        rows: list[dict[str, object]] = []
        for line_number, record in enumerate(raw.to_dict(orient="records"), start=2):
            try:
                unit_price_cents = parse_brl_currency_to_cents(record["preco_unitario"])
                quantity = parse_quantity(record["quantidade"])
                rows.append(
                    {
                        "external_order_id": parse_identifier(record["id_do_pedido"]),
                        "sku": parse_identifier(record["sku"]),
                        "product_name": parse_text(record["produto"]),
                        "quantity": quantity,
                        "unit_price_cents": unit_price_cents,
                        "total_price_cents": unit_price_cents * quantity,
                        "discount_percentage": None,
                        "status": map_status(record["status"], _STATUS_MAP),
                        "order_date": parse_date_brazilian(record["data_do_pedido"]),
                    }
                )
            except KeyError as exc:
                raise TransformationError(
                    f"linha {line_number}: coluna esperada ausente ({exc})"
                ) from exc
            except TransformationError as exc:
                raise TransformationError(f"linha {line_number}: {exc}") from exc

        return build_canonical_frame(rows)

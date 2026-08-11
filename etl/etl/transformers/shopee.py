"""Transformer da Shopee — aceita dois layouts sem regressão em nenhum deles.

1. O formato de exemplo da Sprint 4 (fictício): `id_do_pedido`, `sku`,
   `produto`, `quantidade`, `preco_unitario`, `status`, `data_do_pedido`.
2. O relatório oficial real (Seller Center, ver
   `tests/fixtures/shopee/orders.xlsx` e ADR-061 em decisions.md):
   `id_do_pedido`, `status_do_pedido`, `nome_do_produto`, `quantidade`,
   `preço_acordado`, `data_de_criação_do_pedido` — sem nenhuma coluna de SKU
   preenchida.

Cada campo é resolvido por uma lista de grafias aceitas (`find_column`),
mesma estratégia de aliases do hotfix da detecção (Sprint 4.1). Ver
`etl.detectors.shopee` para o conjunto exato exigido na detecção.
"""

from dataclasses import dataclass

import pandas as pd

from etl.exceptions import TransformationError
from etl.transformers.base import Transformer
from etl.transformers.common import (
    build_canonical_frame,
    derive_sku_from_product_name,
    find_column,
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
    "entregue": OrderStatus.COMPLETED,
    "pendente": OrderStatus.PENDING,
    "enviado": OrderStatus.PENDING,
    "a enviar": OrderStatus.PENDING,
    "não pago": OrderStatus.PENDING,
    "cancelado": OrderStatus.CANCELLED,
    # "O comprador pode pedir uma devolução até <data>" (real, com data
    # variável embutida no texto) fica de fora de propósito: não é um valor
    # fixo enumerável, e um status não mapeado já vira UNKNOWN sem
    # interromper o arquivo (ADR-051) — não precisa de um caso especial.
}

# Cada tupla é a lista de grafias aceitas para o campo, na ordem: formato de
# exemplo primeiro, depois o(s) nome(s) real(is) do relatório oficial.
_ORDER_ID_ALIASES = ("ID do Pedido",)
_STATUS_ALIASES = ("Status", "Status do Pedido")
_PRODUCT_NAME_ALIASES = ("Produto", "Nome do Produto")
_QUANTITY_ALIASES = ("Quantidade",)
_UNIT_PRICE_ALIASES = ("Preco Unitario", "Preço acordado")
_ORDER_DATE_ALIASES = ("Data do Pedido", "Data de criação do pedido")
_SKU_ALIASES = ("SKU", "Número de referência SKU", "Nº de referência do SKU principal")


@dataclass(frozen=True, slots=True)
class _ResolvedColumns:
    order_id: str
    status: str
    product_name: str
    quantity: str
    unit_price: str
    order_date: str
    sku: str | None  # `None`: nenhuma coluna de SKU no arquivo — usa fallback por linha.


def _resolve_columns(columns: pd.Index) -> _ResolvedColumns:
    def required(label: str, *aliases: str) -> str:
        column = find_column(columns, *aliases)
        if column is None:
            raise TransformationError(
                f"coluna obrigatória ausente: {label} (aceita: {', '.join(aliases)})"
            )
        return column

    return _ResolvedColumns(
        order_id=required("identificador do pedido", *_ORDER_ID_ALIASES),
        status=required("status do pedido", *_STATUS_ALIASES),
        product_name=required("nome do produto", *_PRODUCT_NAME_ALIASES),
        quantity=required("quantidade", *_QUANTITY_ALIASES),
        unit_price=required("preço unitário", *_UNIT_PRICE_ALIASES),
        order_date=required("data do pedido", *_ORDER_DATE_ALIASES),
        sku=find_column(columns, *_SKU_ALIASES),
    )


class ShopeeTransformer(Transformer):
    """Padroniza um relatório Shopee bruto (exemplo ou oficial) no esquema canônico."""

    marketplace = Marketplace.SHOPEE

    def transform(self, raw: pd.DataFrame) -> pd.DataFrame:
        resolved = _resolve_columns(raw.columns)

        rows: list[dict[str, object]] = []
        for line_number, record in enumerate(raw.to_dict(orient="records"), start=2):
            try:
                product_name = parse_text(record[resolved.product_name])
                unit_price_cents = parse_brl_currency_to_cents(record[resolved.unit_price])
                quantity = parse_quantity(record[resolved.quantity])

                raw_sku = str(record[resolved.sku]).strip() if resolved.sku else ""
                sku = raw_sku or derive_sku_from_product_name(product_name)

                rows.append(
                    {
                        "external_order_id": parse_identifier(record[resolved.order_id]),
                        "sku": sku,
                        "product_name": product_name,
                        "quantity": quantity,
                        "unit_price_cents": unit_price_cents,
                        "total_price_cents": unit_price_cents * quantity,
                        "discount_percentage": None,
                        "status": map_status(record[resolved.status], _STATUS_MAP),
                        "order_date": parse_date_brazilian(record[resolved.order_date]),
                    }
                )
            except KeyError as exc:
                raise TransformationError(
                    f"linha {line_number}: coluna esperada ausente ({exc})"
                ) from exc
            except TransformationError as exc:
                raise TransformationError(f"linha {line_number}: {exc}") from exc

        return build_canonical_frame(rows)

"""Testes de `etl.schema.validate_canonical_schema` — a etapa de Validação do pipeline."""

import datetime

import pandas as pd
import pytest

from etl.exceptions import TransformationError
from etl.schema import CANONICAL_COLUMNS, validate_canonical_schema
from etl.types import OrderStatus

_VALID_ROW = {
    "external_order_id": "1001",
    "sku": "SKU-A",
    "product_name": "Camiseta Azul",
    "quantity": 2,
    "unit_price_cents": 4990,
    "total_price_cents": 9980,
    "discount_percentage": None,
    "status": OrderStatus.COMPLETED,
    "order_date": datetime.date(2026, 8, 5),
}


def test_valid_frame_passes() -> None:
    frame = pd.DataFrame([_VALID_ROW], columns=list(CANONICAL_COLUMNS), dtype=object)
    validate_canonical_schema(frame)  # não deve levantar


def test_empty_frame_passes() -> None:
    frame = pd.DataFrame(columns=list(CANONICAL_COLUMNS), dtype=object)
    validate_canonical_schema(frame)


def test_missing_column_raises() -> None:
    frame = pd.DataFrame([_VALID_ROW], columns=list(CANONICAL_COLUMNS), dtype=object)
    frame = frame.drop(columns=["sku"])

    with pytest.raises(TransformationError, match="sku"):
        validate_canonical_schema(frame)


def test_blank_required_field_raises() -> None:
    row = {**_VALID_ROW, "product_name": "   "}
    frame = pd.DataFrame([row], columns=list(CANONICAL_COLUMNS), dtype=object)

    with pytest.raises(TransformationError):
        validate_canonical_schema(frame)


def test_negative_quantity_raises() -> None:
    row = {**_VALID_ROW, "quantity": -1}
    frame = pd.DataFrame([row], columns=list(CANONICAL_COLUMNS), dtype=object)

    with pytest.raises(TransformationError):
        validate_canonical_schema(frame)


def test_non_date_order_date_raises() -> None:
    row = {**_VALID_ROW, "order_date": "2026-08-05"}
    frame = pd.DataFrame([row], columns=list(CANONICAL_COLUMNS), dtype=object)

    with pytest.raises(TransformationError):
        validate_canonical_schema(frame)


def test_discount_out_of_range_raises() -> None:
    row = {**_VALID_ROW, "discount_percentage": 150.0}
    frame = pd.DataFrame([row], columns=list(CANONICAL_COLUMNS), dtype=object)

    with pytest.raises(TransformationError):
        validate_canonical_schema(frame)

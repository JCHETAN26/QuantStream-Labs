"""Fixed-point conversion: exactness, edge cases, and rejection of lossy input."""

from __future__ import annotations

from decimal import Decimal

import pytest

from quantstream_contracts.fixed_point import (
    INT64_MAX,
    PRICE_SCALE,
    from_fixed,
    price_from_fixed,
    price_to_fixed,
    size_to_fixed,
    to_fixed,
)


def test_decimal_string_is_exact():
    # The classic float trap: 100.07 has no exact binary representation.
    assert price_to_fixed("100.07") == 100_070_000_000
    assert price_from_fixed(100_070_000_000) == Decimal("100.07")


def test_integer_input():
    assert price_to_fixed(100) == 100 * PRICE_SCALE
    assert size_to_fixed(0) == 0


def test_decimal_input():
    assert price_to_fixed(Decimal("0.000000001")) == 1  # one nano-unit


def test_negative_value():
    assert price_to_fixed("-3.5") == -3_500_000_000


def test_round_trip_preserves_value():
    for text in ("0", "1", "0.5", "12345.6789", "-9.999999999"):
        fixed = price_to_fixed(text)
        assert from_fixed(fixed, PRICE_SCALE) == Decimal(text)


def test_float_is_rejected():
    with pytest.raises(TypeError):
        price_to_fixed(100.07)


def test_bool_is_rejected():
    with pytest.raises(TypeError):
        price_to_fixed(True)


def test_precision_beyond_scale_is_rejected():
    # 10 decimal places, scale only supports 9.
    with pytest.raises(ValueError):
        price_to_fixed("1.0000000001")


def test_non_decimal_string_is_rejected():
    with pytest.raises(ValueError):
        price_to_fixed("not-a-number")


def test_non_finite_is_rejected():
    with pytest.raises(ValueError):
        price_to_fixed("NaN")
    with pytest.raises(ValueError):
        price_to_fixed("Infinity")


def test_int64_overflow_is_rejected():
    too_big = Decimal(INT64_MAX) + 1
    with pytest.raises(ValueError):
        to_fixed(too_big, 1)


def test_unsupported_type_is_rejected():
    with pytest.raises(TypeError):
        to_fixed(object(), PRICE_SCALE)

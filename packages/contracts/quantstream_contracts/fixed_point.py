"""Fixed-point representation for prices and sizes.

Market data must never carry floating-point price/size through the canonical
pipeline. Two reasons, both fatal to this project's headline claim:

  1. Float summation order and platform float formatting break the deterministic
     replay checksum (same input -> same checksum must hold across runs).
  2. Byte-for-byte equality between the Python reference and the C++ replay engine
     is impossible if either side stores an IEEE-754 double.

So every price and size is stored as a scaled integer:

    price_fixed = round(price_decimal * PRICE_SCALE)   # exact, via Decimal
    price_real  = price_fixed / PRICE_SCALE

PRICE_SCALE / SIZE_SCALE are 1e9 ("nano" units): 9 decimal places of precision,
with int64 headroom up to ~9.2e9 in real units (INT64_MAX / 1e9).

All parsing goes through decimal.Decimal, so "100.07" becomes exactly
100_070_000_000 and never 100.06999999999999. float inputs are rejected outright
rather than silently rounded, because a silent rounding here is exactly the kind
of quiet data corruption this product exists to catch.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

PRICE_SCALE = 1_000_000_000
SIZE_SCALE = 1_000_000_000

INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


def to_fixed(value: str | int | Decimal, scale: int) -> int:
    """Convert a decimal-ish value to a scaled int64, exactly or not at all.

    Accepts str, int, or Decimal. Rejects float and bool: float would reintroduce
    the precision loss this module exists to prevent, and bool is almost always a
    bug at a call site expecting a number.

    Raises:
        TypeError: value is a float, bool, or unsupported type.
        ValueError: value is non-finite, not a decimal, exceeds the scale's
            precision, or falls outside the int64 range.
    """
    if isinstance(value, bool):
        raise TypeError("bool is not a valid price/size")
    if isinstance(value, float):
        raise TypeError(
            "float input rejected; pass a str or Decimal to avoid precision loss"
        )

    if isinstance(value, str):
        try:
            dec = Decimal(value)
        except InvalidOperation as exc:
            raise ValueError(f"not a decimal value: {value!r}") from exc
    elif isinstance(value, int):
        dec = Decimal(value)
    elif isinstance(value, Decimal):
        dec = value
    else:
        raise TypeError(f"unsupported type for fixed-point: {type(value).__name__}")

    if not dec.is_finite():
        raise ValueError(f"non-finite value: {value!r}")

    scaled = dec * scale
    if scaled != scaled.to_integral_value():
        raise ValueError(
            f"value {value!r} has finer precision than scale {scale} supports"
        )

    result = int(scaled)
    if not (INT64_MIN <= result <= INT64_MAX):
        raise ValueError(f"fixed-point value out of int64 range: {result}")
    return result


def from_fixed(fixed: int, scale: int) -> Decimal:
    """Convert a scaled integer back to an exact Decimal in real units."""
    return Decimal(fixed) / Decimal(scale)


def price_to_fixed(value: str | int | Decimal) -> int:
    return to_fixed(value, PRICE_SCALE)


def size_to_fixed(value: str | int | Decimal) -> int:
    return to_fixed(value, SIZE_SCALE)


def price_from_fixed(fixed: int) -> Decimal:
    return from_fixed(fixed, PRICE_SCALE)


def size_from_fixed(fixed: int) -> Decimal:
    return from_fixed(fixed, SIZE_SCALE)

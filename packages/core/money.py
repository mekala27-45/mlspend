from collections.abc import Mapping
from decimal import ROUND_HALF_EVEN, Decimal

MICRO = Decimal("1000000")


def microdollars(value: str | Decimal) -> int:
    amount = Decimal(value)
    if not amount.is_finite():
        raise ValueError("Money must be finite")
    return int((amount * MICRO).to_integral_value(rounding=ROUND_HALF_EVEN))


def dollars(value: int) -> str:
    return str((Decimal(value) / MICRO).quantize(Decimal("0.000001")))


def apportion(total: int, weights: Mapping[str, float]) -> dict[str, int]:
    """Largest remainders with stable ties, preserving every microdollar."""
    if not weights or total < 0:
        raise ValueError("Nonempty weights and nonnegative money required")
    converted = {key: Decimal(str(weights[key])) for key in sorted(weights)}
    if any(not v.is_finite() or v < 0 for v in converted.values()):
        raise ValueError("Weights must be finite and nonnegative")
    denominator = sum(converted.values())
    if denominator == 0:
        converted = dict.fromkeys(converted, Decimal(1))
        denominator = Decimal(len(converted))
    exact = {key: Decimal(total) * weight / denominator for key, weight in converted.items()}
    output = {key: int(value) for key, value in exact.items()}
    order = sorted(output, key=lambda key: (-(exact[key] - output[key]), key))
    for key in order[: total - sum(output.values())]:
        output[key] += 1
    return output

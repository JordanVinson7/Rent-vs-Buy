"""Stamp Duty Land Tax (SDLT) for residential purchases in England & NI.

Rates as of April 2025 for a main residence. Scotland (LBTT) and Wales (LTT)
use different bands and are out of scope for v1 — see README limitations.
"""

# (band upper bound, marginal rate) — the final band is unbounded.
STANDARD_BANDS: list[tuple[float, float]] = [
    (125_000, 0.00),
    (250_000, 0.02),
    (925_000, 0.05),
    (1_500_000, 0.10),
    (float("inf"), 0.12),
]

FIRST_TIME_BUYER_BANDS: list[tuple[float, float]] = [
    (300_000, 0.00),
    (500_000, 0.05),
]
# First-time-buyer relief only applies to purchases up to this price;
# above it, standard rates apply to the whole amount.
FTB_RELIEF_CEILING = 500_000


def _tax_from_bands(price: float, bands: list[tuple[float, float]]) -> float:
    tax = 0.0
    lower = 0.0
    for upper, rate in bands:
        if price <= lower:
            break
        taxable = min(price, upper) - lower
        tax += taxable * rate
        lower = upper
    return tax


def stamp_duty(price: float, first_time_buyer: bool = False) -> float:
    """SDLT due on a main-residence purchase at ``price``.

    First-time-buyer relief is applied when eligible; it is void for
    purchases above £500,000, where standard rates apply in full.
    """
    if price < 0:
        raise ValueError("price cannot be negative")
    if first_time_buyer and price <= FTB_RELIEF_CEILING:
        return _tax_from_bands(price, FIRST_TIME_BUYER_BANDS)
    return _tax_from_bands(price, STANDARD_BANDS)

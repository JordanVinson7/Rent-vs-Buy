"""Repayment mortgage arithmetic (fixed rate, monthly amortisation)."""

import numpy as np
import pandas as pd


def monthly_payment(principal: float, annual_rate: float, term_years: int) -> float:
    """Fixed monthly payment on a repayment mortgage (standard annuity formula).

    Uses the market convention of annual_rate / 12 for the periodic rate.
    """
    n = term_years * 12
    if principal <= 0:
        return 0.0
    r = annual_rate / 12.0
    if r == 0:
        return principal / n
    return principal * r / (1.0 - (1.0 + r) ** -n)


def amortisation_schedule(
    principal: float, annual_rate: float, term_years: int
) -> pd.DataFrame:
    """Month-by-month split of each payment into interest and principal.

    Returns a DataFrame indexed by month (1..n) with columns:
    ``payment``, ``interest``, ``principal_paid``, ``balance``.
    """
    n = term_years * 12
    r = annual_rate / 12.0
    payment = monthly_payment(principal, annual_rate, term_years)

    balance = principal
    rows = []
    for month in range(1, n + 1):
        interest = balance * r
        principal_paid = min(payment - interest, balance)
        balance -= principal_paid
        rows.append((payment if balance > 1e-9 or principal_paid > 0 else 0.0,
                     interest, principal_paid, max(balance, 0.0)))

    df = pd.DataFrame(
        rows, columns=["payment", "interest", "principal_paid", "balance"]
    )
    df.index = pd.RangeIndex(1, n + 1, name="month")
    return df


def balance_after(principal: float, annual_rate: float, term_years: int,
                  months_elapsed: int) -> float:
    """Outstanding balance after ``months_elapsed`` payments (closed form)."""
    n = term_years * 12
    m = min(months_elapsed, n)
    r = annual_rate / 12.0
    if r == 0:
        return max(principal * (1 - m / n), 0.0)
    growth = (1.0 + r) ** m
    payment = monthly_payment(principal, annual_rate, term_years)
    balance = principal * growth - payment * (growth - 1.0) / r
    return float(np.clip(balance, 0.0, None))

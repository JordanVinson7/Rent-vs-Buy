"""Model assumptions for the rent-vs-buy simulation.

All rates are annual and expressed as decimals (0.05 == 5%).
All money values are in GBP.
"""

from dataclasses import dataclass, field, replace
from typing import Any


@dataclass(frozen=True)
class SimulationConfig:
    """Every assumption the deterministic model depends on.

    The defaults are intended to be *plausible* for the UK in the mid-2020s,
    not predictions. The whole point of the project is to vary them.
    """

    # --- Property -----------------------------------------------------------
    house_price: float = 350_000.0
    deposit_fraction: float = 0.10          # share of price paid upfront
    house_growth_rate: float = 0.03         # annual nominal house price growth
    first_time_buyer: bool = True           # SDLT first-time-buyer relief

    # --- Mortgage -----------------------------------------------------------
    mortgage_rate: float = 0.045            # annual interest rate
    mortgage_term_years: int = 30

    # --- Buying / owning costs ----------------------------------------------
    purchase_legal_costs: float = 2_500.0   # conveyancing, survey, searches
    maintenance_rate: float = 0.01          # annual, as a share of house value
    insurance_annual: float = 350.0         # buildings insurance
    service_charge_annual: float = 0.0      # for leasehold flats
    selling_cost_rate: float = 0.02         # agent + legal fees on eventual sale

    # --- Renting --------------------------------------------------------------
    monthly_rent: float = 1_500.0
    rent_growth_rate: float = 0.03          # annual rent inflation

    # --- Investing ------------------------------------------------------------
    equity_return_rate: float = 0.07        # annual nominal, before fees
    fund_fee_rate: float = 0.0022           # OCF, e.g. a global index tracker
    invest_in_isa: bool = True              # if True, gains are tax free
    capital_gains_tax_rate: float = 0.24    # applied to gains if not in an ISA
    cgt_annual_exempt_amount: float = 3_000.0

    # --- Horizon ----------------------------------------------------------------
    years: int = 30

    def __post_init__(self) -> None:
        if not 0 < self.deposit_fraction <= 1:
            raise ValueError("deposit_fraction must be in (0, 1].")
        if self.house_price <= 0:
            raise ValueError("house_price must be positive.")
        if self.years <= 0 or self.mortgage_term_years <= 0:
            raise ValueError("years and mortgage_term_years must be positive.")
        if self.monthly_rent < 0:
            raise ValueError("monthly_rent cannot be negative.")

    # --- Derived quantities ----------------------------------------------------
    @property
    def deposit(self) -> float:
        return self.house_price * self.deposit_fraction

    @property
    def loan_amount(self) -> float:
        return self.house_price - self.deposit

    @property
    def months(self) -> int:
        return self.years * 12

    def with_(self, **changes: Any) -> "SimulationConfig":
        """Return a copy of this config with some fields changed.

        Convenient for sensitivity analysis:
        ``cfg.with_(house_growth_rate=0.05, equity_return_rate=0.06)``
        """
        return replace(self, **changes)


def monthly_rate(annual_rate: float) -> float:
    """Convert an annual rate to the equivalent monthly compounding rate."""
    return (1.0 + annual_rate) ** (1.0 / 12.0) - 1.0

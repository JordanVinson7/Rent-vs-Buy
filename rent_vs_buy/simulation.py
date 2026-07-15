"""The core deterministic simulation.

Two people start with identical cash (the buyer's total upfront outlay) and
identical monthly budgets. Each month, whoever spends less on housing invests
the difference in a global index fund. This "invest the difference" step is
what most casual rent-vs-buy comparisons omit, and it is the whole game.

Buyer wealth  = home equity (net of selling costs) + any invested surplus
Renter wealth = investment portfolio (net of CGT unless held in an ISA)
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .config import SimulationConfig, monthly_rate
from .mortgage import monthly_payment
from .stamp_duty import stamp_duty


@dataclass(frozen=True)
class SimulationResult:
    """Monthly trajectories plus headline numbers."""

    df: pd.DataFrame
    config: SimulationConfig

    @property
    def final_buyer_wealth(self) -> float:
        return float(self.df["buyer_wealth"].iloc[-1])

    @property
    def final_renter_wealth(self) -> float:
        return float(self.df["renter_wealth"].iloc[-1])

    @property
    def final_advantage(self) -> float:
        """Positive means buying wins."""
        return self.final_buyer_wealth - self.final_renter_wealth

    @property
    def crossover_month(self) -> int | None:
        """First month after which buying stays ahead for good, if any."""
        ahead = (self.df["buyer_wealth"] >= self.df["renter_wealth"]).to_numpy()
        if ahead.all():
            return 1
        if not ahead[-1]:
            return None
        # last month the renter was ahead, plus one
        return int(np.where(~ahead)[0][-1]) + 2


def _apply_cgt(portfolio: float, contributions: float,
               cfg: SimulationConfig) -> float:
    """Portfolio value after capital gains tax on liquidation."""
    if cfg.invest_in_isa:
        return portfolio
    gain = max(portfolio - contributions, 0.0)
    taxable = max(gain - cfg.cgt_annual_exempt_amount, 0.0)
    return portfolio - taxable * cfg.capital_gains_tax_rate


def run_simulation(cfg: SimulationConfig) -> SimulationResult:
    """Run the month-by-month comparison and return full trajectories."""
    upfront = cfg.deposit + stamp_duty(cfg.house_price, cfg.first_time_buyer) \
        + cfg.purchase_legal_costs

    pay = monthly_payment(cfg.loan_amount, cfg.mortgage_rate,
                          cfg.mortgage_term_years)
    mortgage_r = cfg.mortgage_rate / 12.0
    house_r = monthly_rate(cfg.house_growth_rate)
    rent_r = monthly_rate(cfg.rent_growth_rate)
    invest_r = monthly_rate(cfg.equity_return_rate - cfg.fund_fee_rate)

    house_value = cfg.house_price
    balance = cfg.loan_amount
    rent = cfg.monthly_rent

    # The renter invests everything the buyer spent upfront.
    renter_portfolio = upfront
    renter_contributions = upfront
    buyer_portfolio = 0.0
    buyer_contributions = 0.0

    rows = []
    for month in range(1, cfg.months + 1):
        # -- growth accrues on last month's balances --------------------------
        house_value *= 1.0 + house_r
        renter_portfolio *= 1.0 + invest_r
        buyer_portfolio *= 1.0 + invest_r

        # -- buyer's housing outgoings ----------------------------------------
        interest = balance * mortgage_r
        if balance > 0:
            principal_paid = min(pay - interest, balance)
            mortgage_cash = interest + principal_paid
            balance -= principal_paid
        else:
            principal_paid = mortgage_cash = 0.0

        running_costs = (house_value * cfg.maintenance_rate
                         + cfg.insurance_annual
                         + cfg.service_charge_annual) / 12.0
        buyer_outgoing = mortgage_cash + running_costs

        # -- invest the difference ---------------------------------------------
        diff = buyer_outgoing - rent
        if diff > 0:                       # buying costs more: renter invests
            renter_portfolio += diff
            renter_contributions += diff
        else:                              # renting costs more: buyer invests
            buyer_portfolio += -diff
            buyer_contributions += -diff

        # -- mark wealth to market ----------------------------------------------
        equity = house_value * (1.0 - cfg.selling_cost_rate) - balance
        buyer_wealth = equity + _apply_cgt(buyer_portfolio,
                                           buyer_contributions, cfg)
        renter_wealth = _apply_cgt(renter_portfolio, renter_contributions, cfg)

        rows.append((month, house_value, balance, equity,
                     buyer_portfolio, buyer_wealth,
                     rent, renter_portfolio, renter_wealth,
                     buyer_outgoing, interest, running_costs))

        rent *= 1.0 + rent_r

    df = pd.DataFrame(rows, columns=[
        "month", "house_value", "mortgage_balance", "home_equity",
        "buyer_portfolio", "buyer_wealth",
        "rent", "renter_portfolio", "renter_wealth",
        "buyer_outgoing", "mortgage_interest", "running_costs",
    ]).set_index("month")
    df["years"] = df.index / 12.0
    return SimulationResult(df=df, config=cfg)


def breakeven_grid(
    cfg: SimulationConfig,
    house_growth_rates: np.ndarray,
    equity_return_rates: np.ndarray,
) -> pd.DataFrame:
    """Final buyer-minus-renter wealth over a grid of the two key assumptions.

    Rows are house growth rates, columns are equity return rates.
    """
    grid = np.zeros((len(house_growth_rates), len(equity_return_rates)))
    for i, hg in enumerate(house_growth_rates):
        for j, er in enumerate(equity_return_rates):
            result = run_simulation(
                cfg.with_(house_growth_rate=float(hg),
                          equity_return_rate=float(er))
            )
            grid[i, j] = result.final_advantage
    return pd.DataFrame(grid, index=house_growth_rates,
                        columns=equity_return_rates)

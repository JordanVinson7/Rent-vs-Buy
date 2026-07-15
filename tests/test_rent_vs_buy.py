import numpy as np
import pytest

from rent_vs_buy import (
    SimulationConfig,
    amortisation_schedule,
    monthly_payment,
    run_simulation,
    stamp_duty,
)
from rent_vs_buy.mortgage import balance_after


# --- Stamp duty (England & NI, main residence, April 2025 bands) --------------

@pytest.mark.parametrize("price, expected", [
    (100_000, 0),                     # below the nil-rate band
    (125_000, 0),
    (250_000, 2_500),                 # 2% on the 125k–250k slice
    (350_000, 7_500),                 # + 5% on the next 100k
    (1_000_000, 43_750),              # 2,500 + 33,750 + 7,500 across four bands
])
def test_standard_stamp_duty(price, expected):
    assert stamp_duty(price) == pytest.approx(expected)


@pytest.mark.parametrize("price, expected", [
    (300_000, 0),                     # fully relieved
    (400_000, 5_000),                 # 5% on the 300k–500k slice
    (500_000, 10_000),
    (500_001, 15_000.05),             # relief void above £500k → standard rates
])
def test_first_time_buyer_relief(price, expected):
    assert stamp_duty(price, first_time_buyer=True) == pytest.approx(expected)


# --- Mortgage arithmetic ---------------------------------------------------------

def test_monthly_payment_matches_annuity_formula():
    # £315,000 at 4.5% over 30 years ≈ £1,596.06 (standard annuity result)
    assert monthly_payment(315_000, 0.045, 30) == pytest.approx(1596.06, abs=0.05)


def test_zero_rate_mortgage_is_straight_line():
    assert monthly_payment(120_000, 0.0, 10) == pytest.approx(1_000.0)


def test_amortisation_reaches_zero_and_sums_to_principal():
    sched = amortisation_schedule(200_000, 0.05, 25)
    assert sched["balance"].iloc[-1] == pytest.approx(0.0, abs=1e-6)
    assert sched["principal_paid"].sum() == pytest.approx(200_000, rel=1e-9)


def test_closed_form_balance_matches_schedule():
    sched = amortisation_schedule(200_000, 0.05, 25)
    for m in (1, 60, 150, 300):
        assert balance_after(200_000, 0.05, 25, m) == pytest.approx(
            sched["balance"].loc[m], abs=0.01
        )


# --- Simulation invariants ---------------------------------------------------------

def _base(**kw) -> SimulationConfig:
    return SimulationConfig(**kw)


def test_identical_growth_and_costs_do_not_create_money_from_nothing():
    """With 0% growth everywhere and no costs, total wealth equals cash put in."""
    cfg = _base(
        house_growth_rate=0.0, equity_return_rate=0.0, rent_growth_rate=0.0,
        mortgage_rate=0.0, fund_fee_rate=0.0, maintenance_rate=0.0,
        insurance_annual=0.0, selling_cost_rate=0.0, purchase_legal_costs=0.0,
        first_time_buyer=True, house_price=300_000,  # zero stamp duty
        years=30, mortgage_term_years=30,
    )
    result = run_simulation(cfg)
    # Both people spend max(rent, owner costs) every month. With zero returns,
    # the buyer's final wealth must equal every pound they put in: the £30k
    # deposit plus 360 months at the £1,500 shared budget (£750 mortgage
    # + £750 invested surplus) = £570k. The renter consumed £1,500/mo as rent,
    # keeping only the invested £30k upfront sum.
    assert result.final_buyer_wealth == pytest.approx(570_000, rel=1e-6)
    assert result.final_renter_wealth == pytest.approx(30_000, rel=1e-6)


def test_higher_equity_returns_favour_renting():
    low = run_simulation(_base(equity_return_rate=0.04)).final_advantage
    high = run_simulation(_base(equity_return_rate=0.10)).final_advantage
    assert high < low


def test_higher_house_growth_favours_buying():
    low = run_simulation(_base(house_growth_rate=0.01)).final_advantage
    high = run_simulation(_base(house_growth_rate=0.06)).final_advantage
    assert high > low


def test_isa_renter_never_poorer_than_taxed_renter():
    isa = run_simulation(_base(invest_in_isa=True)).final_renter_wealth
    taxed = run_simulation(_base(invest_in_isa=False)).final_renter_wealth
    assert isa >= taxed


def test_wealth_columns_are_finite_and_mortgage_clears():
    result = run_simulation(_base(years=35, mortgage_term_years=25))
    df = result.df
    assert np.isfinite(df[["buyer_wealth", "renter_wealth"]]).all().all()
    assert df["mortgage_balance"].iloc[-1] == pytest.approx(0.0, abs=1e-6)


def test_invalid_config_rejected():
    with pytest.raises(ValueError):
        _base(deposit_fraction=0.0)
    with pytest.raises(ValueError):
        _base(house_price=-1)

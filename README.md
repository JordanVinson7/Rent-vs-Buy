# Rent + Invest vs Buy — a UK wealth comparison model

Should you buy a home, or rent and invest the difference? Most casual answers
compare a mortgage payment to rent and stop there. This project models the
question properly: two people with **identical income and identical starting
cash**, tracked month by month for decades, where whoever spends less on
housing invests the surplus in a global index fund.

Built as a Python package with an interactive Streamlit dashboard, a demo
notebook, and a test suite.

## The model

Each month, for a configurable horizon:

**The buyer** pays a deposit, stamp duty (English SDLT bands, with
first-time-buyer relief), and legal costs upfront, then a repayment mortgage,
maintenance (a % of the property's current value), and insurance. Their wealth
is home equity — house value net of selling costs, minus the outstanding
mortgage — plus any surplus they invest once owning becomes cheaper than
renting (which it eventually does, since rent inflates and the mortgage
payment doesn't).

**The renter** invests the buyer's entire upfront outlay on day one, pays
rent (inflating annually), and invests the monthly difference whenever owning
costs more. Their wealth is the portfolio, net of capital gains tax unless
held in an ISA.

The key design decision is **symmetry**: both people have the same monthly
housing budget — `max(rent, owner's outgoings)` — and the surplus is always
invested by whoever is under budget. Neither side gets free money.

## Results at the default assumptions

£350k house, 10% deposit, 4.5% mortgage over 30 years, £1,500/month rent
growing at 3%, equities returning 7% nominal in an ISA:

| | Buyer | Renter |
|---|---|---|
| Wealth after 30 years | ~£1.05m | ~£0.44m |

But the verdict is *extremely* sensitive to two numbers — house price growth
and equity returns — which is why the dashboard's centrepiece is a break-even
heatmap over that grid rather than a single answer. At the defaults, buying
pulls ahead within two years; drop house growth to 1% and raise equity returns
to 9% and renting wins comfortably.

## Quick start

```bash
git clone https://github.com/<you>/rent-vs-buy.git
cd rent-vs-buy
pip install -r requirements.txt

streamlit run app.py          # interactive dashboard
pytest                        # run the test suite
```

Or use the package directly:

```python
from rent_vs_buy import SimulationConfig, run_simulation

result = run_simulation(SimulationConfig(house_price=425_000, monthly_rent=1_800))
print(result.final_advantage)   # positive → buying wins
result.df                        # full monthly trajectories as a DataFrame
```

The demo notebook in `notebooks/demo.ipynb` walks through the analysis.

## Project structure

```
rent_vs_buy/
  config.py       # every assumption, as a frozen dataclass with validation
  stamp_duty.py   # English SDLT bands incl. first-time-buyer relief
  mortgage.py     # annuity payment, amortisation schedule, closed-form balance
  simulation.py   # the month-by-month engine + break-even grid
  plots.py        # Plotly figures shared by notebook and dashboard
app.py            # Streamlit dashboard
notebooks/        # narrative demo (executed, outputs included)
tests/            # pytest suite: known SDLT values, annuity maths,
                  # cash-conservation and monotonicity invariants
```

## What the model deliberately leaves out

- **Volatility.** This is a deterministic model — growth rates are constant.
  Real returns are volatile and sequence risk matters, especially with the
  leverage a mortgage provides. A Monte Carlo / historical-backtest layer is
  the planned v2.
- **Behaviour.** The renter invests every spare pound with perfect discipline.
  In practice a mortgage acts as a commitment device, and this assumption is
  the model's biggest ask.
- **Regional tax.** SDLT bands are for England & Northern Ireland; Scotland
  (LBTT) and Wales (LTT) differ.
- **Life.** Remortgaging, moving house, growing families, landlord risk, and
  security of tenure are not priced.

Everything is in nominal terms; subtract inflation from all growth rates to
think in real terms — the comparison is unaffected as long as you're
consistent.

**This is a modelling exercise, not financial advice.**

## Roadmap

- [ ] Monte Carlo simulation over return distributions
- [ ] Historical backtests using UK House Price Index and total-return equity data
- [ ] Remortgaging at rate resets; interest-only comparison
- [ ] Scottish LBTT and Welsh LTT bands

## Licence

MIT

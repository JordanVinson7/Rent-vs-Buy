"""Interactive rent-vs-buy dashboard. Run with:  streamlit run app.py"""

import numpy as np
import streamlit as st

from rent_vs_buy import SimulationConfig, breakeven_grid, run_simulation, stamp_duty
from rent_vs_buy.plots import breakeven_heatmap, monthly_costs, wealth_trajectory

st.set_page_config(page_title="Rent + Invest vs Buy (UK)", page_icon="🏠",
                   layout="wide")

st.title("Rent + invest vs buy — UK wealth comparison")
st.caption(
    "Two people, identical income, identical starting cash. One buys; the other "
    "rents and invests the deposit **and** every month's cost difference in a "
    "global index fund. Who ends up wealthier?"
)

# ---------------------------------------------------------------- sidebar ----
with st.sidebar:
    st.header("Property")
    house_price = st.number_input("House price (£)", 50_000, 3_000_000,
                                  350_000, step=10_000)
    deposit_pct = st.slider("Deposit (%)", 5, 100, 10) / 100
    house_growth = st.slider("House price growth (%/yr)", -2.0, 8.0, 3.0, 0.25) / 100
    ftb = st.checkbox("First-time buyer (SDLT relief)", value=True)

    st.header("Mortgage")
    mortgage_rate = st.slider("Mortgage rate (%/yr)", 0.5, 9.0, 4.5, 0.05) / 100
    term = st.slider("Term (years)", 10, 40, 30)

    st.header("Renting & investing")
    rent = st.number_input("Monthly rent (£)", 300, 10_000, 1_500, step=50)
    rent_growth = st.slider("Rent inflation (%/yr)", 0.0, 8.0, 3.0, 0.25) / 100
    equity_return = st.slider("Equity return (%/yr)", 0.0, 12.0, 7.0, 0.25) / 100
    isa = st.checkbox("Investments held in an ISA (tax-free)", value=True)

    st.header("Costs & horizon")
    maintenance = st.slider("Maintenance (%/yr of value)", 0.0, 3.0, 1.0, 0.1) / 100
    selling_costs = st.slider("Selling costs (% of sale)", 0.0, 5.0, 2.0, 0.25) / 100
    years = st.slider("Horizon (years)", 5, 40, 30)

cfg = SimulationConfig(
    house_price=house_price, deposit_fraction=deposit_pct,
    house_growth_rate=house_growth, first_time_buyer=ftb,
    mortgage_rate=mortgage_rate, mortgage_term_years=term,
    monthly_rent=rent, rent_growth_rate=rent_growth,
    equity_return_rate=equity_return, invest_in_isa=isa,
    maintenance_rate=maintenance, selling_cost_rate=selling_costs,
    years=years,
)
result = run_simulation(cfg)

# --------------------------------------------------------------- headline ----
sdlt = stamp_duty(house_price, ftb)
upfront = cfg.deposit + sdlt + cfg.purchase_legal_costs

c1, c2, c3, c4 = st.columns(4)
c1.metric("Buyer's final wealth", f"£{result.final_buyer_wealth:,.0f}")
c2.metric("Renter's final wealth", f"£{result.final_renter_wealth:,.0f}")
adv = result.final_advantage
c3.metric("Advantage", f"£{abs(adv):,.0f}",
          delta="to buying" if adv >= 0 else "to renting",
          delta_color="normal" if adv >= 0 else "inverse")
c4.metric("Upfront cash needed", f"£{upfront:,.0f}",
          help=f"Deposit £{cfg.deposit:,.0f} + stamp duty £{sdlt:,.0f} "
               f"+ legal/survey £{cfg.purchase_legal_costs:,.0f}")

st.plotly_chart(wealth_trajectory(result), use_container_width=True)

left, right = st.columns(2)
with left:
    st.plotly_chart(monthly_costs(result), use_container_width=True)
with right:
    with st.spinner("Computing break-even grid…"):
        hg = np.round(np.arange(0.0, 0.0651, 0.005), 4)
        er = np.round(np.arange(0.02, 0.1051, 0.005), 4)
        grid = breakeven_grid(cfg, hg, er)
    st.plotly_chart(
        breakeven_heatmap(grid, cfg.house_growth_rate, cfg.equity_return_rate),
        use_container_width=True,
    )

with st.expander("Model assumptions & limitations"):
    st.markdown(
        """
- Deterministic: growth rates are constant every month; real markets are volatile,
  and sequence-of-returns risk matters. (Monte Carlo is the planned v2.)
- SDLT bands are for England & NI main residences (April 2025). Scotland and
  Wales differ.
- The renter is assumed to be perfectly disciplined — every pound of cost
  difference gets invested. Behaviourally, this is the model's biggest ask.
- No remortgaging, moving house, rent-free periods, or Help-to-Buy style schemes.
- Everything is nominal. Subtract ~2–3% inflation from all growth rates to think
  in real terms — the *comparison* is unaffected as long as you're consistent.
        """
    )

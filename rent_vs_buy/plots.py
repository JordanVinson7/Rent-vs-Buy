"""Plotly figures shared by the notebook and the Streamlit dashboard."""

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from .simulation import SimulationResult

BUY = "#1f5f8b"      # deep blue — the buyer
RENT = "#c2571a"     # burnt orange — the renter
GRID = "rgba(128,128,128,0.15)"

_LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Inter, Segoe UI, sans-serif", size=13),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.08, x=0),
    margin=dict(l=10, r=10, t=60, b=10),
)


def _money(fig: go.Figure) -> go.Figure:
    fig.update_yaxes(tickprefix="£", separatethousands=True, gridcolor=GRID)
    fig.update_xaxes(gridcolor=GRID)
    return fig


def wealth_trajectory(result: SimulationResult) -> go.Figure:
    df = result.df
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["years"], y=df["buyer_wealth"], name="Buy",
        line=dict(color=BUY, width=2.5),
        hovertemplate="Buy: £%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["years"], y=df["renter_wealth"], name="Rent + invest",
        line=dict(color=RENT, width=2.5),
        hovertemplate="Rent + invest: £%{y:,.0f}<extra></extra>",
    ))
    cross = result.crossover_month
    if cross and cross > 1:
        fig.add_vline(x=cross / 12, line_dash="dot", line_color="grey",
                      annotation_text=f"buying pulls ahead ~yr {cross / 12:.0f}",
                      annotation_position="top left")
    fig.update_layout(
        title="Net wealth if you liquidated everything today",
        xaxis_title="Years", **_LAYOUT,
    )
    return _money(fig)


def monthly_costs(result: SimulationResult) -> go.Figure:
    df = result.df
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["years"], y=df["buyer_outgoing"], name="Owner's monthly outgoings",
        line=dict(color=BUY, width=2),
        hovertemplate="Owner: £%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["years"], y=df["rent"], name="Rent",
        line=dict(color=RENT, width=2),
        hovertemplate="Rent: £%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=df["years"], y=df["mortgage_interest"], name="…of which interest",
        line=dict(color=BUY, width=1, dash="dot"),
        hovertemplate="Interest: £%{y:,.0f}<extra></extra>",
    ))
    fig.update_layout(
        title="Monthly housing cost over time",
        xaxis_title="Years", **_LAYOUT,
    )
    return _money(fig)


def breakeven_heatmap(grid: pd.DataFrame, cfg_house_growth: float,
                      cfg_equity_return: float) -> go.Figure:
    """Diverging heatmap of final buyer-minus-renter wealth."""
    z = grid.to_numpy()
    limit = float(np.abs(z).max()) or 1.0
    fig = go.Figure(go.Heatmap(
        z=z,
        x=[f"{c:.1%}" for c in grid.columns],
        y=[f"{r:.1%}" for r in grid.index],
        zmid=0, zmin=-limit, zmax=limit,
        colorscale=[[0, RENT], [0.5, "#f5f2ec"], [1, BUY]],
        colorbar=dict(title="Buy − Rent (£)", tickprefix="£"),
        hovertemplate=("equity return %{x}<br>house growth %{y}"
                       "<br>advantage to buying: £%{z:,.0f}<extra></extra>"),
    ))
    fig.add_trace(go.Scatter(
        x=[f"{cfg_equity_return:.1%}"], y=[f"{cfg_house_growth:.1%}"],
        mode="markers", marker=dict(symbol="x", size=12, color="black"),
        name="your assumptions", showlegend=False,
        hovertemplate="your current assumptions<extra></extra>",
    ))
    fig.update_layout(
        title="Who wins? Blue = buying, orange = renting",
        xaxis_title="Equity return (annual)",
        yaxis_title="House price growth (annual)",
        **{k: v for k, v in _LAYOUT.items() if k != "hovermode"},
    )
    return fig

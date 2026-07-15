"""rent_vs_buy — a deterministic UK rent-and-invest vs buy wealth model."""

from .config import SimulationConfig
from .mortgage import amortisation_schedule, monthly_payment
from .simulation import SimulationResult, breakeven_grid, run_simulation
from .stamp_duty import stamp_duty

__all__ = [
    "SimulationConfig",
    "SimulationResult",
    "run_simulation",
    "breakeven_grid",
    "stamp_duty",
    "monthly_payment",
    "amortisation_schedule",
]

__version__ = "0.1.0"

"""
Layer 2: Life Simulation Engine

Generates month-by-month life events, portfolio evolution, and dynamic parameter adjustments.
Feeds compiled AIScenario objects into the Monte Carlo engine for realistic life trajectories.
"""

from .models import (
    EventType,
    LifeEvent,
    PortfolioState,
    LifeTrajectory,
    MacroShock,
)

__all__ = [
    "EventType",
    "LifeEvent",
    "PortfolioState",
    "LifeTrajectory",
    "MacroShock",
]

"""
Type definitions for the Life Simulation Engine.

Defines data structures for life events, portfolio states, and trajectories.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from monte_carlo_sim.src.types import AIScenario


class EventType(Enum):
    """Types of life events that can occur during simulation."""
    
    # Vehicle events
    VEHICLE_MINOR_REPAIR = "vehicle_minor_repair"
    VEHICLE_MAJOR_REPAIR = "vehicle_major_repair"
    VEHICLE_ACCIDENT = "vehicle_accident"
    VEHICLE_REPLACEMENT = "vehicle_replacement"
    
    # Health events
    HEALTH_MINOR_ILLNESS = "health_minor_illness"
    HEALTH_MAJOR_ILLNESS = "health_major_illness"
    HEALTH_CHRONIC_ISSUE = "health_chronic_issue"
    
    # Platform events
    PLATFORM_DEACTIVATION = "platform_deactivation"
    PLATFORM_FEE_INCREASE = "platform_fee_increase"
    PLATFORM_MARKET_SATURATION = "platform_market_saturation"
    PLATFORM_POLICY_CHANGE = "platform_policy_change"
    
    # Housing events
    HOUSING_RENT_INCREASE = "housing_rent_increase"
    HOUSING_FORCED_MOVE = "housing_forced_move"
    HOUSING_EMERGENCY_REPAIR = "housing_emergency_repair"
    
    # Positive events
    POSITIVE_NEW_PLATFORM = "positive_new_platform"
    POSITIVE_SKILL_UPGRADE = "positive_skill_upgrade"
    POSITIVE_REFERRAL_BONUS = "positive_referral_bonus"
    POSITIVE_SIDE_GIG = "positive_side_gig"


@dataclass
class LifeEvent:
    """
    Represents a single life event that affects income or expenses.
    
    Attributes:
        event_type: Type of event that occurred
        month: Month when event occurs (0-indexed)
        income_impact: Immediate impact on that month's income (negative = loss, positive = gain)
        expense_impact: Additional expense that month (negative = cost, positive = savings)
        duration_months: How many months the impact lasts (1 = one-time)
        cascade_to_next: Whether this triggers follow-on effects
        description: Human-readable description of the event
    """
    event_type: EventType
    month: int
    income_impact: float = 0.0
    expense_impact: float = 0.0
    duration_months: int = 1
    cascade_to_next: bool = False
    description: str = ""
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.event_type.value} at month {self.month}"


@dataclass
class PortfolioState:
    """
    Snapshot of a gig worker's portfolio at a specific month.
    
    Tracks platform mix, hours worked, skill level, and income parameters.
    """
    month: int
    active_platforms: list[str]
    total_hours_per_week: float
    skill_multiplier: float  # 1.0 at start, grows over time (e.g., 1.08 after 24 months)
    monthly_base_income: float  # μ for this month
    monthly_base_sigma: float  # σ for this month
    
    def __repr__(self):
        return (
            f"PortfolioState(month={self.month}, platforms={len(self.active_platforms)}, "
            f"μ=${self.monthly_base_income:.0f}, σ=${self.monthly_base_sigma:.0f}, "
            f"skill={self.skill_multiplier:.2f}x)"
        )


@dataclass
class MacroShock:
    """
    Represents a macro-economic shock (recession, gas spike, etc.).
    
    Contains the shock type, start month, and the parameter shifts to apply.
    """
    category: str  # "recession", "gas_spike", "regulatory", "tech_disruption"
    scenario_name: str  # e.g., "recession_2008", "gas_spike_2022"
    start_month: int
    parameter_shifts: list  # List of ParameterShift objects from the scenario
    narrative: str = ""
    
    def __repr__(self):
        return f"MacroShock({self.scenario_name} starting month {self.start_month})"


@dataclass
class LifeTrajectory:
    """
    Complete 24-month life simulation with events, portfolio evolution, and macro shocks.
    
    This is the output of the Life Simulation Engine, containing:
    - All life events that occurred
    - Month-by-month portfolio states
    - Macro shock (if triggered)
    - Compiled AIScenario for Monte Carlo
    """
    archetype_id: str
    months: int
    events: list[LifeEvent] = field(default_factory=list)
    portfolio_states: list[PortfolioState] = field(default_factory=list)
    macro_shock: Optional[MacroShock] = None
    ai_scenario: Optional[AIScenario] = None
    random_seed: Optional[int] = None
    narrative: str = ""
    
    def get_events_by_month(self, month: int) -> list[LifeEvent]:
        """Return all events that occurred in a specific month."""
        return [e for e in self.events if e.month == month]
    
    def get_event_summary(self) -> str:
        """Generate a human-readable summary of the trajectory."""
        lines = [f"Life Trajectory for {self.archetype_id} ({self.months} months)"]
        lines.append(f"Random seed: {self.random_seed}")
        lines.append(f"\nTotal events: {len(self.events)}")
        
        if self.macro_shock:
            lines.append(f"\nMacro shock: {self.macro_shock}")
        
        lines.append("\nEvent timeline:")
        for month in range(self.months):
            month_events = self.get_events_by_month(month)
            if month_events:
                lines.append(f"  Month {month}:")
                for event in month_events:
                    lines.append(f"    - {event.description}")
        
        if self.portfolio_states:
            lines.append(f"\nPortfolio evolution:")
            lines.append(f"  Start: {self.portfolio_states[0]}")
            if len(self.portfolio_states) > 12:
                lines.append(f"  Month 12: {self.portfolio_states[12]}")
            if len(self.portfolio_states) > 1:
                lines.append(f"  End: {self.portfolio_states[-1]}")
        
        return "\n".join(lines)
    
    def __repr__(self):
        return (
            f"LifeTrajectory(archetype={self.archetype_id}, months={self.months}, "
            f"events={len(self.events)}, macro_shock={self.macro_shock is not None})"
        )

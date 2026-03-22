"""
Scenario Converter - Compiles LifeTrajectory into AIScenario.

Converts the complete life simulation timeline (events, portfolio evolution,
macro shocks) into an AIScenario object that Monte Carlo can execute.
"""

import numpy as np
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.types import LifeTrajectory, LifeEvent, EventType, PortfolioState
from monte_carlo_sim.src.types import (
    AIScenario,
    ParameterShift,
    DiscreteJump,
    ShiftTarget,
    ShiftType,
    DecayType
)


def event_to_discrete_jump(event: LifeEvent) -> Optional[DiscreteJump]:
    """
    Convert a LifeEvent to a DiscreteJump for Monte Carlo.
    
    DiscreteJumps are for one-time or short-duration income shocks.
    
    Args:
        event: LifeEvent to convert
    
    Returns:
        DiscreteJump if event has immediate income impact, None otherwise
    """
    if event.income_impact == 0:
        return None
    
    if event.duration_months <= 3:
        echo_months = event.duration_months - 1 if event.duration_months > 1 else None
        echo_decay = 0.7 if echo_months else None
        
        variance = abs(event.income_impact) * 0.3
        
        return DiscreteJump(
            month=event.month,
            amount=event.income_impact,
            variance=variance,
            echo_months=echo_months,
            echo_decay_rate=echo_decay
        )
    
    return None


def event_to_parameter_shift(event: LifeEvent) -> Optional[ParameterShift]:
    """
    Convert a LifeEvent to a ParameterShift for Monte Carlo.
    
    ParameterShifts are for longer-duration impacts (>3 months) or expense changes.
    
    Args:
        event: LifeEvent to convert
    
    Returns:
        ParameterShift if event has sustained impact, None otherwise
    """
    if event.duration_months > 3 and event.income_impact != 0:
        magnitude = 1.0 + (event.income_impact / 1000.0)
        
        return ParameterShift(
            target=ShiftTarget.MU_BASE,
            type=ShiftType.ADDITIVE,
            magnitude=event.income_impact,
            start_month=event.month,
            duration_months=event.duration_months,
            decay=DecayType.LINEAR
        )
    
    if event.expense_impact != 0 and event.duration_months > 1:
        return ParameterShift(
            target=ShiftTarget.EXPENSES,
            type=ShiftType.ADDITIVE,
            magnitude=abs(event.expense_impact),
            start_month=event.month,
            duration_months=event.duration_months,
            decay=DecayType.SNAP_BACK if event.duration_months <= 6 else DecayType.LINEAR
        )
    
    return None


def portfolio_evolution_to_parameter_shifts(
    portfolio_states: list[PortfolioState],
    initial_mu: float,
    initial_sigma: float
) -> list[ParameterShift]:
    """
    Convert portfolio evolution into parameter shifts.
    
    Creates gradual parameter shifts for:
    - Skill growth (logarithmic income increase)
    - Platform diversification (sigma reduction)
    
    Args:
        portfolio_states: List of portfolio states by month
        initial_mu: Initial monthly income
        initial_sigma: Initial income volatility
    
    Returns:
        List of ParameterShift objects for portfolio evolution
    """
    if not portfolio_states or len(portfolio_states) < 2:
        return []
    
    shifts = []
    
    final_state = portfolio_states[-1]
    skill_improvement = final_state.skill_multiplier / portfolio_states[0].skill_multiplier
    
    if skill_improvement > 1.01:
        shifts.append(ParameterShift(
            target=ShiftTarget.MU_BASE,
            type=ShiftType.MULTIPLICATIVE,
            magnitude=skill_improvement,
            start_month=0,
            duration_months=len(portfolio_states),
            decay=DecayType.EXPONENTIAL
        ))
    
    platform_count_initial = len(portfolio_states[0].active_platforms)
    platform_count_final = len(final_state.active_platforms)
    
    if platform_count_final > platform_count_initial:
        diversification_factor = np.sqrt(platform_count_initial / platform_count_final)
        
        shifts.append(ParameterShift(
            target=ShiftTarget.SIGMA_BASE,
            type=ShiftType.MULTIPLICATIVE,
            magnitude=diversification_factor,
            start_month=0,
            duration_months=len(portfolio_states),
            decay=DecayType.LINEAR
        ))
    
    return shifts


def macro_shock_to_parameter_shifts(macro_shock) -> list[ParameterShift]:
    """
    Convert MacroShock to ParameterShift objects.
    
    Args:
        macro_shock: MacroShock from trajectory
    
    Returns:
        List of ParameterShift objects from the macro scenario
    """
    if not macro_shock or not macro_shock.parameter_shifts:
        return []
    
    shifts = []
    for shift_dict in macro_shock.parameter_shifts:
        target_map = {
            "mu_base": ShiftTarget.MU_BASE,
            "sigma_base": ShiftTarget.SIGMA_BASE,
            "lambda": ShiftTarget.LAMBDA,
            "expenses": ShiftTarget.EXPENSES
        }
        
        type_map = {
            "multiplicative": ShiftType.MULTIPLICATIVE,
            "additive": ShiftType.ADDITIVE
        }
        
        decay_map = {
            "snap_back": DecayType.SNAP_BACK,
            "linear": DecayType.LINEAR,
            "exponential": DecayType.EXPONENTIAL
        }
        
        target = target_map.get(shift_dict["target"], ShiftTarget.MU_BASE)
        shift_type = type_map.get(shift_dict["type"], ShiftType.MULTIPLICATIVE)
        decay = decay_map.get(shift_dict["decay"], DecayType.LINEAR)
        
        shifts.append(ParameterShift(
            target=target,
            type=shift_type,
            magnitude=shift_dict["magnitude"],
            start_month=shift_dict["start_month"],
            duration_months=shift_dict["duration_months"],
            decay=decay
        ))
    
    return shifts


def generate_narrative(trajectory: LifeTrajectory) -> str:
    """
    Generate human-readable narrative of the trajectory.
    
    Args:
        trajectory: Complete life trajectory
    
    Returns:
        Narrative string describing key events
    """
    lines = []
    
    if trajectory.events:
        major_events = [e for e in trajectory.events if e.cascade_to_next or abs(e.income_impact) > 500 or abs(e.expense_impact) > 500]
        
        if major_events:
            lines.append(f"{len(major_events)} major events:")
            for event in major_events[:5]:
                lines.append(f"  Month {event.month}: {event.event_type.value}")
    
    if trajectory.portfolio_states and len(trajectory.portfolio_states) > 1:
        initial = trajectory.portfolio_states[0]
        final = trajectory.portfolio_states[-1]
        
        platform_change = len(final.active_platforms) - len(initial.active_platforms)
        if platform_change > 0:
            lines.append(f"Added {platform_change} platforms")
        
        skill_growth = (final.skill_multiplier - initial.skill_multiplier) / initial.skill_multiplier * 100
        if skill_growth > 1:
            lines.append(f"Skill growth: +{skill_growth:.1f}%")
    
    if trajectory.macro_shock:
        lines.append(f"Macro shock: {trajectory.macro_shock.narrative} (month {trajectory.macro_shock.start_month})")
    
    if not lines:
        return f"{trajectory.archetype_id} - 24 months, no major events"
    
    return f"{trajectory.archetype_id}: " + ", ".join(lines)


def trajectory_to_ai_scenario(trajectory: LifeTrajectory) -> AIScenario:
    """
    Convert complete LifeTrajectory into AIScenario for Monte Carlo.
    
    This is the main conversion function that compiles:
    - Life events → DiscreteJumps + ParameterShifts
    - Portfolio evolution → ParameterShifts
    - Macro shocks → ParameterShifts
    
    Args:
        trajectory: Complete life trajectory from trajectory_builder
    
    Returns:
        AIScenario ready for Monte Carlo execution
    """
    parameter_shifts = []
    discrete_jumps = []
    
    if trajectory.portfolio_states:
        initial_state = trajectory.portfolio_states[0]
        portfolio_shifts = portfolio_evolution_to_parameter_shifts(
            trajectory.portfolio_states,
            initial_state.monthly_base_income,
            initial_state.monthly_base_sigma
        )
        parameter_shifts.extend(portfolio_shifts)
    
    for event in trajectory.events:
        jump = event_to_discrete_jump(event)
        if jump:
            discrete_jumps.append(jump)
        
        shift = event_to_parameter_shift(event)
        if shift:
            parameter_shifts.append(shift)
    
    if trajectory.macro_shock:
        macro_shifts = macro_shock_to_parameter_shifts(trajectory.macro_shock)
        parameter_shifts.extend(macro_shifts)
    
    narrative = generate_narrative(trajectory)
    
    return AIScenario(
        parameter_shifts=parameter_shifts,
        discrete_jumps=discrete_jumps,
        narrative=narrative
    )

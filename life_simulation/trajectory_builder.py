"""
Trajectory Builder - Main orchestrator for life simulation.

Generates complete 24-month life trajectories by coordinating:
- Event sampling
- Portfolio evolution
- Macro shock triggers
- Cascading effects
- Scenario compilation
"""

import random
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.models import LifeTrajectory, LifeEvent, PortfolioState, MacroShock
from life_simulation.event_sampler import sample_all_events_for_month
from life_simulation.portfolio_evolution import (
    create_initial_portfolio_state,
    evolve_portfolio_state,
    check_platform_addition,
    check_platform_churn
)
from life_simulation.macro_triggers import check_macro_shocks
from life_simulation.cascading_effects import apply_cascading_effects
from life_simulation.scenario_converter import trajectory_to_ai_scenario
from data_pipeline.loaders import DataLoader


def build_life_trajectory(
    archetype_id: str,
    n_months: int = 24,
    random_seed: Optional[int] = None,
    narrative_mode: bool = False
) -> LifeTrajectory:
    """
    Generate a complete life trajectory with events, portfolio evolution, and shocks.
    
    This is the main entry point for Layer 2 Life Simulation.
    
    Process:
    1. Load archetype from data_pipeline
    2. Initialize portfolio state
    3. For each month:
       a. Sample life events (vehicle, health, platform, housing, positive)
       b. Check for portfolio evolution (platform additions/churn)
       c. Check for macro shock triggers (if none active)
       d. Apply cascading effects from events
       e. Update portfolio state
    4. Compile AIScenario from complete trajectory
    
    Args:
        archetype_id: Archetype ID from archetypes.json (e.g., "volatile_vic")
        n_months: Number of months to simulate (default 24)
        random_seed: Optional seed for reproducibility
        narrative_mode: If True, uses deterministic events for demos (NOT IMPLEMENTED YET)
    
    Returns:
        Complete LifeTrajectory with AIScenario ready for Monte Carlo
    """
    loader = DataLoader()
    archetype = loader.load_archetype(archetype_id)
    expenses_data = loader.get_expense_data()
    
    rng = random.Random(random_seed)
    
    all_events = []
    portfolio_states = [create_initial_portfolio_state(archetype, 0)]
    macro_shock = None
    macro_shock_active = False
    
    for month in range(1, n_months):
        current_state = portfolio_states[-1]
        
        month_events = sample_all_events_for_month(
            archetype,
            month,
            expenses_data,
            rng
        )
        
        platform_addition = check_platform_addition(current_state, archetype, month, rng)
        platform_churn = check_platform_churn(current_state, archetype, month, rng)
        
        if not macro_shock_active:
            shock = check_macro_shocks(
                month,
                current_state.active_platforms,
                macro_shock_active,
                loader,
                rng
            )
            if shock:
                macro_shock = shock
                macro_shock_active = True
        
        cascading_events = []
        for event in month_events:
            cascades = apply_cascading_effects(
                event,
                current_state,
                archetype["emergency_fund_weeks"]
            )
            cascading_events.extend(cascades)
        
        all_events.extend(month_events)
        all_events.extend(cascading_events)
        
        new_state = evolve_portfolio_state(
            current_state,
            archetype,
            month,
            rng,
            platform_addition=platform_addition,
            platform_churn=platform_churn
        )
        portfolio_states.append(new_state)
    
    trajectory = LifeTrajectory(
        archetype_id=archetype_id,
        months=n_months,
        events=all_events,
        portfolio_states=portfolio_states,
        macro_shock=macro_shock,
        random_seed=random_seed
    )
    
    ai_scenario = trajectory_to_ai_scenario(trajectory)
    trajectory.ai_scenario = ai_scenario
    trajectory.narrative = ai_scenario.narrative
    
    return trajectory


def build_narrative_trajectory(
    archetype_id: str,
    n_months: int = 24,
    scripted_events: Optional[list[dict]] = None
) -> LifeTrajectory:
    """
    Build a deterministic narrative trajectory for demos.
    
    Uses pre-scripted events instead of random sampling for reproducible demos.
    
    Args:
        archetype_id: Archetype ID
        n_months: Number of months
        scripted_events: List of event dicts with {type, month, params}
    
    Returns:
        Deterministic LifeTrajectory
    
    Note: This is a placeholder for future narrative mode implementation.
    For now, use build_life_trajectory with a fixed random_seed.
    """
    return build_life_trajectory(archetype_id, n_months, random_seed=42, narrative_mode=True)


def build_multiple_trajectories(
    archetype_id: str,
    n_trajectories: int,
    n_months: int = 24,
    base_seed: Optional[int] = None
) -> list[LifeTrajectory]:
    """
    Generate multiple trajectories for the same archetype.
    
    Useful for:
    - Portfolio-level risk aggregation
    - Statistical validation
    - Stress testing
    
    Args:
        archetype_id: Archetype ID
        n_trajectories: Number of trajectories to generate
        n_months: Months per trajectory
        base_seed: Base seed (each trajectory gets base_seed + i)
    
    Returns:
        List of LifeTrajectory objects
    """
    trajectories = []
    
    for i in range(n_trajectories):
        seed = (base_seed + i) if base_seed is not None else None
        trajectory = build_life_trajectory(archetype_id, n_months, seed)
        trajectories.append(trajectory)
    
    return trajectories


def get_trajectory_statistics(trajectories: list[LifeTrajectory]) -> dict:
    """
    Calculate statistics across multiple trajectories.
    
    Args:
        trajectories: List of trajectories
    
    Returns:
        Dictionary with statistics
    """
    stats = {
        "n_trajectories": len(trajectories),
        "avg_events_per_trajectory": sum(len(t.events) for t in trajectories) / len(trajectories),
        "macro_shock_frequency": sum(1 for t in trajectories if t.macro_shock) / len(trajectories),
        "avg_final_platforms": sum(len(t.portfolio_states[-1].active_platforms) for t in trajectories) / len(trajectories),
        "avg_skill_growth": sum(t.portfolio_states[-1].skill_multiplier for t in trajectories) / len(trajectories)
    }
    
    event_types = {}
    for trajectory in trajectories:
        for event in trajectory.events:
            event_type = event.event_type.value
            event_types[event_type] = event_types.get(event_type, 0) + 1
    
    stats["event_type_frequencies"] = event_types
    
    return stats

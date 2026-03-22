"""
Portfolio Evolution - Models platform additions, skill growth, and churn.

Tracks how gig workers add platforms, improve skills, and sometimes drop platforms over time.
"""

import random
import numpy as np
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.models import PortfolioState, LifeEvent, EventType
from data_pipeline.transform.calibrate_monte_carlo import calculate_income_params


def calculate_skill_multiplier(months_elapsed: int, skill_growth_rate: float) -> float:
    """
    Calculate skill multiplier using logarithmic growth curve.
    
    Formula: skill = 1.0 + skill_growth_rate * ln(1 + months)
    
    This models:
    - Fast improvement early on (steep learning curve)
    - Plateauing as worker becomes experienced
    
    Args:
        months_elapsed: Number of months since start (0-indexed)
        skill_growth_rate: Growth rate from archetype (0.02-0.08)
    
    Returns:
        Skill multiplier (e.g., 1.0 at month 0, 1.08 at month 24 with rate=0.04)
    """
    if months_elapsed < 0:
        return 1.0
    return 1.0 + skill_growth_rate * np.log(1.0 + months_elapsed)


def choose_complementary_platform(
    current_platforms: list[str],
    all_platforms: list[str],
    rng: random.Random
) -> Optional[str]:
    """
    Choose a new platform that complements existing portfolio.
    
    Prioritizes:
    - Delivery + rideshare mix (common diversification)
    - Adding platforms not currently active
    
    Args:
        current_platforms: List of currently active platforms
        all_platforms: List of all available platforms
        rng: Random number generator
    
    Returns:
        Platform name or None if no good options
    """
    available = [p for p in all_platforms if p not in current_platforms]
    
    if not available:
        return None
    
    # Prefer common diversification patterns
    has_delivery = any(p in ['doordash', 'instacart', 'grubhub'] for p in current_platforms)
    has_rideshare = any(p in ['uber', 'lyft'] for p in current_platforms)
    
    if has_delivery and not has_rideshare:
        rideshare_options = [p for p in available if p in ['uber', 'lyft']]
        if rideshare_options:
            return rng.choice(rideshare_options)
    
    if has_rideshare and not has_delivery:
        delivery_options = [p for p in available if p in ['doordash', 'instacart', 'grubhub']]
        if delivery_options:
            return rng.choice(delivery_options)
    
    return rng.choice(available)


def calculate_new_platform_income(
    platform: str,
    hours_per_week: float,
    metro: str,
    skill_level: float
) -> tuple[float, float]:
    """
    Calculate income parameters (μ, σ) for a newly added platform.
    
    Args:
        platform: Platform name
        hours_per_week: Hours to allocate to new platform
        metro: Metro area
        skill_level: Current skill multiplier
    
    Returns:
        (monthly_mu, monthly_sigma) for the new stream
    """
    result = calculate_income_params(
        platforms=[platform],
        hours_per_week=hours_per_week,
        metro=metro
    )
    mu = result["mu"] * skill_level
    sigma = result["sigma"] * skill_level
    return mu, sigma


def check_platform_addition(
    current_state: PortfolioState,
    archetype: dict,
    month: int,
    rng: random.Random
) -> Optional[tuple[str, float, float]]:
    """
    Check if worker adds a new platform this month.
    
    Args:
        current_state: Current portfolio state
        archetype: Archetype data
        month: Current month
        rng: Random number generator
    
    Returns:
        (platform_name, mu, sigma) if added, None otherwise
    """
    monthly_add_prob = archetype["platform_add_rate"]
    
    if rng.random() < monthly_add_prob:
        all_platforms = ['uber', 'lyft', 'doordash', 'instacart', 'grubhub']
        new_platform = choose_complementary_platform(
            current_state.active_platforms,
            all_platforms,
            rng
        )
        
        if new_platform:
            hours_allocated = 10.0
            mu, sigma = calculate_new_platform_income(
                platform=new_platform,
                hours_per_week=hours_allocated,
                metro=archetype["metro"],
                skill_level=current_state.skill_multiplier
            )
            return (new_platform, mu, sigma)
    
    return None


def check_platform_churn(
    current_state: PortfolioState,
    archetype: dict,
    month: int,
    rng: random.Random
) -> Optional[str]:
    """
    Check if worker drops a platform this month.
    
    Only drops if:
    - Has multiple platforms (doesn't drop last one)
    - Random chance based on churn_risk
    
    Args:
        current_state: Current portfolio state
        archetype: Archetype data
        month: Current month
        rng: Random number generator
    
    Returns:
        Platform name if dropped, None otherwise
    """
    if len(current_state.active_platforms) <= 1:
        return None
    
    monthly_churn_prob = archetype["churn_risk"] / 12.0
    
    if rng.random() < monthly_churn_prob:
        return rng.choice(current_state.active_platforms)
    
    return None


def create_initial_portfolio_state(
    archetype: dict,
    month: int = 0
) -> PortfolioState:
    """
    Create the initial portfolio state from archetype data.
    
    Args:
        archetype: Archetype data from archetypes.json
        month: Starting month (typically 0)
    
    Returns:
        Initial PortfolioState
    """
    return PortfolioState(
        month=month,
        active_platforms=archetype["platforms"].copy(),
        total_hours_per_week=archetype["hours_per_week"],
        skill_multiplier=archetype["skill_level"],
        monthly_base_income=archetype["base_mu"],
        monthly_base_sigma=archetype["base_sigma"]
    )


def evolve_portfolio_state(
    current_state: PortfolioState,
    archetype: dict,
    month: int,
    rng: random.Random,
    platform_addition: Optional[tuple[str, float, float]] = None,
    platform_churn: Optional[str] = None
) -> PortfolioState:
    """
    Evolve portfolio state to the next month.
    
    Updates:
    - Skill multiplier (logarithmic growth)
    - Platform mix (additions/churn)
    - Income parameters (μ, σ) based on new portfolio
    
    Args:
        current_state: Current portfolio state
        archetype: Archetype data
        month: New month number
        rng: Random number generator
        platform_addition: (platform, mu, sigma) if adding a platform
        platform_churn: Platform name if dropping a platform
    
    Returns:
        New PortfolioState for the specified month
    """
    new_skill = calculate_skill_multiplier(month, archetype["skill_growth_rate"])
    
    new_platforms = current_state.active_platforms.copy()
    new_mu = current_state.monthly_base_income
    new_sigma = current_state.monthly_base_sigma
    
    # Handle platform churn (drop first to avoid conflicts)
    if platform_churn and platform_churn in new_platforms:
        new_platforms.remove(platform_churn)
        income_per_platform = new_mu / len(current_state.active_platforms)
        new_mu -= income_per_platform
        new_sigma = new_sigma * 0.95
    
    # Handle platform addition
    if platform_addition:
        platform_name, platform_mu, platform_sigma = platform_addition
        if platform_name not in new_platforms:
            new_platforms.append(platform_name)
            new_mu += platform_mu
            n_streams = len(new_platforms)
            new_sigma = np.sqrt(
                (current_state.monthly_base_sigma ** 2 + platform_sigma ** 2) / n_streams
            )
    
    # Apply skill growth to income
    skill_boost = new_skill / current_state.skill_multiplier
    new_mu *= skill_boost
    
    return PortfolioState(
        month=month,
        active_platforms=new_platforms,
        total_hours_per_week=current_state.total_hours_per_week,
        skill_multiplier=new_skill,
        monthly_base_income=new_mu,
        monthly_base_sigma=new_sigma
    )


def generate_portfolio_evolution(
    archetype: dict,
    n_months: int,
    random_seed: Optional[int] = None
) -> tuple[list[PortfolioState], list[LifeEvent]]:
    """
    Generate complete portfolio evolution for a trajectory.
    
    Returns both portfolio states and events generated by portfolio changes
    (e.g., new platform additions as events for the scenario converter).
    
    Args:
        archetype: Archetype data from archetypes.json
        n_months: Number of months to simulate
        random_seed: Optional seed for reproducibility
    
    Returns:
        (list of PortfolioState for each month, list of LifeEvent from portfolio changes)
    """
    rng = random.Random(random_seed)
    
    states = [create_initial_portfolio_state(archetype, 0)]
    events = []
    
    for month in range(1, n_months):
        current_state = states[-1]
        
        addition = check_platform_addition(current_state, archetype, month, rng)
        churn = check_platform_churn(current_state, archetype, month, rng)
        
        if addition:
            platform_name, platform_mu, platform_sigma = addition
            events.append(LifeEvent(
                event_type=EventType.POSITIVE_NEW_PLATFORM,
                month=month,
                income_impact=platform_mu,
                expense_impact=0.0,
                duration_months=n_months - month,
                cascade_to_next=False,
                description=f"Added {platform_name} platform: +${platform_mu:.0f}/mo (with 3-month ramp-up)"
            ))
        
        new_state = evolve_portfolio_state(
            current_state,
            archetype,
            month,
            rng,
            platform_addition=addition,
            platform_churn=churn
        )
        states.append(new_state)
    
    return states, events

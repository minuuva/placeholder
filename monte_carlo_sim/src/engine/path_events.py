"""
Path-level event sampling - vectorized life events and macro shocks.

Each Monte Carlo path independently samples its own events using Poisson/
Bernoulli distributions. All operations are vectorized for performance.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from data_pipeline.loaders import DataLoader
except ImportError:
    _data_loader = None
else:
    _data_loader = DataLoader()


def annual_to_monthly_probability(annual_prob: float) -> float:
    """Convert annual probability to monthly probability."""
    if annual_prob <= 0:
        return 0.0
    if annual_prob >= 1:
        return 1.0
    return 1.0 - (1.0 - annual_prob) ** (1.0 / 12.0)


def sample_vehicle_events_vectorized(
    n_paths: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample vehicle repair events for all paths.
    
    Returns:
        income_impact: (n_paths,) income reduction from downtime
        expense_impact: (n_paths,) repair costs
    """
    probs = expense_data["life_events"]["probabilities"]["vehicle"]
    impacts = expense_data["life_events"]["impacts"]
    modifier = archetype_data.get("event_modifiers", {}).get("vehicle_repairs", 1.0)
    
    # Monthly probabilities
    minor_prob = annual_to_monthly_probability(probs["minor_repair"]) * modifier
    major_prob = annual_to_monthly_probability(probs["major_repair"]) * modifier
    accident_prob = annual_to_monthly_probability(probs["accident"]) * modifier
    
    # Vectorized sampling
    minor_events = rng.random(n_paths) < minor_prob
    major_events = rng.random(n_paths) < major_prob
    accident_events = rng.random(n_paths) < accident_prob
    
    # Expense impacts
    minor_cost = np.where(minor_events, 
                         rng.uniform(impacts["vehicle_minor_repair"][0], 
                                   impacts["vehicle_minor_repair"][1], n_paths), 
                         0)
    major_cost = np.where(major_events,
                         rng.uniform(impacts["vehicle_major_repair"][0],
                                   impacts["vehicle_major_repair"][1], n_paths),
                         0)
    
    # Accident causes downtime (income loss)
    downtime_weeks = np.where(accident_events,
                             rng.uniform(impacts["vehicle_accident_downtime_weeks"][0],
                                       impacts["vehicle_accident_downtime_weeks"][1], n_paths),
                             0)
    # Approximate weekly income as monthly / 4.33
    income_impact = -downtime_weeks * 300  # Rough estimate for downtime loss
    
    total_expense = minor_cost + major_cost
    
    return income_impact, total_expense


def sample_health_events_vectorized(
    n_paths: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample health events for all paths.
    
    Returns:
        income_impact: (n_paths,) income loss from inability to work
        expense_impact: (n_paths,) medical costs
    """
    probs = expense_data["life_events"]["probabilities"]["health"]
    impacts = expense_data["life_events"]["impacts"]
    modifier = archetype_data.get("event_modifiers", {}).get("health_issues", 1.0)
    
    minor_prob = annual_to_monthly_probability(probs["minor_illness"]) * modifier
    major_prob = annual_to_monthly_probability(probs["major_illness"]) * modifier
    chronic_prob = annual_to_monthly_probability(probs["chronic_issue"]) * modifier
    
    minor_events = rng.random(n_paths) < minor_prob
    major_events = rng.random(n_paths) < major_prob
    chronic_events = rng.random(n_paths) < chronic_prob
    
    # Income impact from days/weeks unable to work
    minor_days = np.where(minor_events,
                         rng.uniform(impacts["health_minor_illness_days"][0],
                                   impacts["health_minor_illness_days"][1], n_paths),
                         0)
    major_weeks = np.where(major_events,
                          rng.uniform(impacts["health_major_illness_weeks"][0],
                                    impacts["health_major_illness_weeks"][1], n_paths),
                          0)
    # Chronic issues have ongoing impact (use a reasonable estimate if not in data)
    chronic_weeks = np.where(chronic_events,
                            rng.uniform(2, 8, n_paths),  # 2-8 weeks reduced capacity
                            0)
    
    # Convert to income loss (assume ~$50/day earnings)
    income_impact = -(minor_days * 50 + (major_weeks + chronic_weeks) * 350)
    
    # Medical expenses
    minor_cost = np.where(minor_events, rng.uniform(100, 300, n_paths), 0)
    major_cost = np.where(major_events, rng.uniform(500, 2000, n_paths), 0)
    chronic_cost = np.where(chronic_events, rng.uniform(200, 800, n_paths), 0)
    
    expense_impact = minor_cost + major_cost + chronic_cost
    
    return income_impact, expense_impact


def sample_platform_events_vectorized(
    n_paths: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample platform-related events for all paths.
    
    Returns:
        income_impact: (n_paths,) income loss from deactivation/saturation
        expense_impact: (n_paths,) additional costs
    """
    probs = expense_data["life_events"]["probabilities"]["platform"]
    impacts = expense_data["life_events"]["impacts"]
    modifier = archetype_data.get("event_modifiers", {}).get("platform_issues", 1.0)
    
    deactivation_prob = annual_to_monthly_probability(probs["deactivation"]) * modifier
    fee_increase_prob = annual_to_monthly_probability(probs["fee_increase"]) * modifier
    saturation_prob = annual_to_monthly_probability(probs["market_saturation"]) * modifier
    
    deactivation_events = rng.random(n_paths) < deactivation_prob
    fee_events = rng.random(n_paths) < fee_increase_prob
    saturation_events = rng.random(n_paths) < saturation_prob
    
    # Deactivation causes income loss for several weeks
    deactivation_weeks = np.where(deactivation_events,
                                 rng.uniform(impacts["platform_deactivation_weeks"][0],
                                           impacts["platform_deactivation_weeks"][1], n_paths),
                                 0)
    income_loss = -deactivation_weeks * 350  # Weekly income loss
    
    # Saturation reduces earnings (estimate 5-15% monthly income reduction)
    saturation_impact = np.where(saturation_events,
                                rng.uniform(-200, -50, n_paths),
                                0)
    income_loss += saturation_impact
    
    # Fee increases add to costs
    fee_increase = np.where(fee_events, rng.uniform(20, 80, n_paths), 0)
    
    return income_loss, fee_increase


def sample_housing_events_vectorized(
    n_paths: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample housing events for all paths.
    
    Returns:
        income_impact: (n_paths,) should be zero (housing doesn't affect income)
        expense_impact: (n_paths,) rent increases, move costs, repairs
    """
    probs = expense_data["life_events"]["probabilities"]["housing"]
    impacts = expense_data["life_events"]["impacts"]
    modifier = archetype_data.get("event_modifiers", {}).get("housing_instability", 1.0)
    
    rent_increase_prob = annual_to_monthly_probability(probs["rent_increase"]) * modifier
    forced_move_prob = annual_to_monthly_probability(probs["forced_move"]) * modifier
    repair_prob = annual_to_monthly_probability(probs["emergency_repair"]) * modifier
    
    rent_events = rng.random(n_paths) < rent_increase_prob
    move_events = rng.random(n_paths) < forced_move_prob
    repair_events = rng.random(n_paths) < repair_prob
    
    rent_increase = np.where(rent_events, rng.uniform(50, 200, n_paths), 0)
    move_cost = np.where(move_events, rng.uniform(1000, 3000, n_paths), 0)  # Moving costs
    repair_cost = np.where(repair_events, rng.uniform(300, 1500, n_paths), 0)  # Emergency repairs
    
    expense_impact = rent_increase + move_cost + repair_cost
    income_impact = np.zeros(n_paths)
    
    return income_impact, expense_impact


def sample_positive_events_vectorized(
    n_paths: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray]:
    """
    Sample positive events for all paths.
    
    Returns:
        income_impact: (n_paths,) income boosts
        expense_impact: (n_paths,) should be zero (positive events don't add costs)
    """
    probs = expense_data["life_events"]["probabilities"]["positive"]
    impacts = expense_data["life_events"]["impacts"]
    modifier = archetype_data.get("event_modifiers", {}).get("positive_events", 1.0)
    
    skill_prob = annual_to_monthly_probability(probs["skill_upgrade"]) * modifier
    bonus_prob = annual_to_monthly_probability(probs["referral_bonus"]) * modifier
    side_gig_prob = annual_to_monthly_probability(probs["side_gig"]) * modifier
    
    skill_events = rng.random(n_paths) < skill_prob
    bonus_events = rng.random(n_paths) < bonus_prob
    side_gig_events = rng.random(n_paths) < side_gig_prob
    
    # Skill upgrade boosts income by 5-10%
    skill_boost = np.where(skill_events, rng.uniform(50, 150, n_paths), 0)
    # Referral bonuses
    bonus = np.where(bonus_events, rng.uniform(100, 500, n_paths), 0)
    # Side gig income
    side_income = np.where(side_gig_events, rng.uniform(200, 600, n_paths), 0)
    
    income_impact = skill_boost + bonus + side_income
    expense_impact = np.zeros(n_paths)
    
    return income_impact, expense_impact


def sample_life_events_vectorized(
    n_paths: int,
    month: int,
    archetype_data: dict,
    expense_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample all life events for all paths simultaneously.
    
    Args:
        n_paths: Number of Monte Carlo paths
        month: Current simulation month (0-23)
        archetype_data: Archetype configuration with event modifiers
        expense_data: Event probabilities and impacts from expenses.json
        rng: Numpy random generator
    
    Returns:
        income_adjustments: (n_paths,) additive income changes
        expense_adjustments: (n_paths,) additive expense changes
        volatility_multipliers: (n_paths,) multiplicative sigma changes (always 1.0 for now)
    """
    # Sample each event category
    vehicle_income, vehicle_expense = sample_vehicle_events_vectorized(
        n_paths, archetype_data, expense_data, rng
    )
    health_income, health_expense = sample_health_events_vectorized(
        n_paths, archetype_data, expense_data, rng
    )
    platform_income, platform_expense = sample_platform_events_vectorized(
        n_paths, archetype_data, expense_data, rng
    )
    housing_income, housing_expense = sample_housing_events_vectorized(
        n_paths, archetype_data, expense_data, rng
    )
    positive_income, positive_expense = sample_positive_events_vectorized(
        n_paths, archetype_data, expense_data, rng
    )
    
    # Aggregate all impacts
    total_income_adj = (vehicle_income + health_income + platform_income + 
                       housing_income + positive_income)
    total_expense_adj = (vehicle_expense + health_expense + platform_expense + 
                        housing_expense + positive_expense)
    
    # Volatility multipliers (for now, events don't change volatility)
    volatility_mult = np.ones(n_paths)
    
    return total_income_adj, total_expense_adj, volatility_mult


def sample_macro_shocks_vectorized(
    n_paths: int,
    month: int,
    active_shocks: np.ndarray,
    shock_end_months: np.ndarray,
    macro_data: dict,
    rng: np.random.Generator
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Sample macro shocks independently per path.
    
    Args:
        n_paths: Number of Monte Carlo paths
        month: Current simulation month
        active_shocks: (n_paths,) int array, 0=none, 1=recession, 2=gas_spike, etc.
        shock_end_months: (n_paths,) int array, when current shock ends (-1 if no shock)
        macro_data: Macro scenario data from macro_params.json
        rng: Numpy random generator
    
    Returns:
        mu_multipliers: (n_paths,) income multipliers
        sigma_multipliers: (n_paths,) volatility multipliers
        expense_multipliers: (n_paths,) expense multipliers
        new_active_shocks: (n_paths,) updated shock states
        new_shock_end_months: (n_paths,) updated end months
    """
    # Start with no adjustments
    mu_mult = np.ones(n_paths)
    sigma_mult = np.ones(n_paths)
    expense_mult = np.ones(n_paths)
    
    new_active_shocks = active_shocks.copy()
    new_shock_end_months = shock_end_months.copy()
    
    # Paths where shocks have ended
    ended_mask = (active_shocks > 0) & (month >= shock_end_months)
    new_active_shocks[ended_mask] = 0
    new_shock_end_months[ended_mask] = -1
    
    # Paths that can trigger new shocks (no active shock)
    eligible_mask = (active_shocks == 0)
    n_eligible = np.sum(eligible_mask)
    
    if n_eligible == 0:
        return mu_mult, sigma_mult, expense_mult, new_active_shocks, new_shock_end_months
    
    # Get baseline probabilities
    baseline_probs = macro_data.get("baseline_probabilities", {})
    
    # Monthly probabilities
    recession_prob = annual_to_monthly_probability(baseline_probs.get("recession", 0.1))
    gas_spike_prob = annual_to_monthly_probability(baseline_probs.get("gas_spike", 0.2))
    regulatory_prob = annual_to_monthly_probability(baseline_probs.get("regulatory", 0.15))
    tech_prob = annual_to_monthly_probability(baseline_probs.get("tech_disruption", 0.08))
    
    # Sample shocks for eligible paths
    eligible_indices = np.where(eligible_mask)[0]
    
    # For each eligible path, try to trigger a shock
    for idx in eligible_indices:
        rand = rng.random()
        
        if rand < recession_prob:
            # Trigger recession
            new_active_shocks[idx] = 1
            new_shock_end_months[idx] = month + 18  # Average recession duration
            # Apply recession impacts (moderate)
            mu_mult[idx] = 0.85
            sigma_mult[idx] = 1.2
            expense_mult[idx] = 1.1
        elif rand < (recession_prob + gas_spike_prob):
            # Trigger gas spike
            new_active_shocks[idx] = 2
            new_shock_end_months[idx] = month + 6  # Shorter duration
            # Apply gas spike impacts (severe on expenses)
            mu_mult[idx] = 0.90
            sigma_mult[idx] = 1.15
            expense_mult[idx] = 1.4  # 40% expense increase
        elif rand < (recession_prob + gas_spike_prob + regulatory_prob):
            # Trigger regulatory change
            new_active_shocks[idx] = 3
            new_shock_end_months[idx] = month + 12
            mu_mult[idx] = 0.92
            sigma_mult[idx] = 1.1
            expense_mult[idx] = 1.08
        elif rand < (recession_prob + gas_spike_prob + regulatory_prob + tech_prob):
            # Trigger tech disruption
            new_active_shocks[idx] = 4
            new_shock_end_months[idx] = month + 24  # Long-lasting
            mu_mult[idx] = 0.95
            sigma_mult[idx] = 1.05
            expense_mult[idx] = 1.02
    
    # Apply ongoing shock effects for paths with active shocks
    ongoing_mask = (new_active_shocks > 0) & (month < new_shock_end_months)
    
    # Recession (shock_id=1)
    recession_mask = ongoing_mask & (new_active_shocks == 1)
    mu_mult[recession_mask] = 0.85
    sigma_mult[recession_mask] = 1.2
    expense_mult[recession_mask] = 1.1
    
    # Gas spike (shock_id=2)
    gas_mask = ongoing_mask & (new_active_shocks == 2)
    mu_mult[gas_mask] = 0.90
    sigma_mult[gas_mask] = 1.15
    expense_mult[gas_mask] = 1.4
    
    # Regulatory (shock_id=3)
    reg_mask = ongoing_mask & (new_active_shocks == 3)
    mu_mult[reg_mask] = 0.92
    sigma_mult[reg_mask] = 1.1
    expense_mult[reg_mask] = 1.08
    
    # Tech disruption (shock_id=4)
    tech_mask = ongoing_mask & (new_active_shocks == 4)
    mu_mult[tech_mask] = 0.95
    sigma_mult[tech_mask] = 1.05
    expense_mult[tech_mask] = 1.02
    
    return mu_mult, sigma_mult, expense_mult, new_active_shocks, new_shock_end_months

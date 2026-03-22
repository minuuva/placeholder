"""
Macro Triggers - Probabilistically activate macro shocks.

Samples recession, gas spike, regulatory, and tech disruption scenarios
based on baseline probabilities from macro_params.json.
"""

import random
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.models import MacroShock
from life_simulation.event_sampler import annual_to_monthly_probability
from data_pipeline.loaders import DataLoader
from monte_carlo_sim.src.types import GigType


def get_dominant_gig_type(platforms: list[str]) -> GigType:
    """
    Determine dominant gig type from platform list.
    
    Args:
        platforms: List of active platforms
    
    Returns:
        GigType enum
    """
    delivery_platforms = {'doordash', 'instacart', 'grubhub', 'postmates'}
    rideshare_platforms = {'uber', 'lyft'}
    
    has_delivery = any(p in delivery_platforms for p in platforms)
    has_rideshare = any(p in rideshare_platforms for p in platforms)
    
    if has_delivery and has_rideshare:
        return GigType.MIXED
    elif has_delivery:
        return GigType.DELIVERY
    elif has_rideshare:
        return GigType.RIDESHARE
    else:
        return GigType.MIXED


def choose_recession_scenario(rng: random.Random, macro_data: dict) -> str:
    """
    Choose which recession scenario to trigger based on probabilities.
    
    Args:
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        Scenario name (e.g., "recession_2008")
    """
    recession_scenarios = macro_data["scenarios"]["recession"]
    
    scenario_names = list(recession_scenarios.keys())
    weights = [recession_scenarios[s]["trigger_probability"] for s in scenario_names]
    
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    return rng.choices(scenario_names, weights=normalized_weights)[0]


def choose_gas_spike_scenario(rng: random.Random, macro_data: dict) -> str:
    """
    Choose which gas spike scenario to trigger based on probabilities.
    
    Args:
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        Scenario name (e.g., "gas_spike_moderate")
    """
    gas_scenarios = macro_data["scenarios"]["gas_spike"]
    
    scenario_names = list(gas_scenarios.keys())
    weights = [gas_scenarios[s]["trigger_probability"] for s in scenario_names]
    
    total_weight = sum(weights)
    normalized_weights = [w / total_weight for w in weights]
    
    return rng.choices(scenario_names, weights=normalized_weights)[0]


def check_recession_trigger(
    month: int,
    already_triggered: bool,
    rng: random.Random,
    macro_data: dict
) -> Optional[tuple[str, str]]:
    """
    Check if a recession triggers this month.
    
    Args:
        month: Current month
        already_triggered: Whether a macro shock is already active
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        (category, scenario_name) if triggered, None otherwise
    """
    if already_triggered:
        return None
    
    baseline_probs = macro_data.get("baseline_probabilities", {})
    annual_prob = baseline_probs.get("recession", 0.10)
    
    monthly_prob = annual_to_monthly_probability(annual_prob)
    
    if rng.random() < monthly_prob:
        scenario_name = choose_recession_scenario(rng, macro_data)
        return ("recession", scenario_name)
    
    return None


def check_gas_spike_trigger(
    month: int,
    already_triggered: bool,
    rng: random.Random,
    macro_data: dict
) -> Optional[tuple[str, str]]:
    """
    Check if a gas spike triggers this month.
    
    Args:
        month: Current month
        already_triggered: Whether a macro shock is already active
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        (category, scenario_name) if triggered, None otherwise
    """
    if already_triggered:
        return None
    
    baseline_probs = macro_data.get("baseline_probabilities", {})
    annual_prob = baseline_probs.get("gas_spike", 0.25)
    
    monthly_prob = annual_to_monthly_probability(annual_prob)
    
    if rng.random() < monthly_prob:
        scenario_name = choose_gas_spike_scenario(rng, macro_data)
        return ("gas_spike", scenario_name)
    
    return None


def check_regulatory_shock_trigger(
    month: int,
    already_triggered: bool,
    rng: random.Random,
    macro_data: dict
) -> Optional[tuple[str, str]]:
    """
    Check if a regulatory shock triggers this month.
    
    Args:
        month: Current month
        already_triggered: Whether a macro shock is already active
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        (category, scenario_name) if triggered, None otherwise
    """
    if already_triggered:
        return None
    
    baseline_probs = macro_data.get("baseline_probabilities", {})
    annual_prob = baseline_probs.get("regulatory_change", 0.15)
    
    monthly_prob = annual_to_monthly_probability(annual_prob)
    
    if rng.random() < monthly_prob:
        regulatory_scenarios = list(macro_data["scenarios"]["regulatory"].keys())
        scenario_name = rng.choice(regulatory_scenarios)
        return ("regulatory", scenario_name)
    
    return None


def check_tech_disruption_trigger(
    month: int,
    already_triggered: bool,
    rng: random.Random,
    macro_data: dict
) -> Optional[tuple[str, str]]:
    """
    Check if a tech disruption triggers this month.
    
    Args:
        month: Current month
        already_triggered: Whether a macro shock is already active
        rng: Random number generator
        macro_data: Macro params data
    
    Returns:
        (category, scenario_name) if triggered, None otherwise
    """
    if already_triggered:
        return None
    
    baseline_probs = macro_data.get("baseline_probabilities", {})
    annual_prob = baseline_probs.get("tech_disruption", 0.08)
    
    monthly_prob = annual_to_monthly_probability(annual_prob)
    
    if rng.random() < monthly_prob:
        tech_scenarios = list(macro_data["scenarios"]["tech_disruption"].keys())
        scenario_name = rng.choice(tech_scenarios)
        return ("tech_disruption", scenario_name)
    
    return None


def convert_scenario_to_macro_shock(
    loader: DataLoader,
    category: str,
    scenario_name: str,
    start_month: int,
    gig_type: GigType
) -> MacroShock:
    """
    Convert data_pipeline scenario to MacroShock.
    
    Replicates logic from scenario_from_data_pipeline but returns MacroShock directly.
    
    Args:
        loader: DataLoader
        category: Scenario category
        scenario_name: Scenario name
        start_month: When shock starts
        gig_type: Dominant gig type
    
    Returns:
        MacroShock object
    """
    scenario = loader.get_scenario(category, scenario_name)
    
    gig_key_map = {
        GigType.DELIVERY: "delivery",
        GigType.RIDESHARE: "rideshare",
        GigType.FREELANCE: "freelance",
        GigType.MIXED: "general_gig"
    }
    gig_key = gig_key_map.get(gig_type, "general_gig")
    
    income_impact = scenario.get("platform_impacts", {}).get(gig_key, 1.0)
    duration = scenario.get("duration_months", 12)
    if duration == "permanent":
        duration = 240
    
    expense_changes = scenario.get("expense_changes", {})
    gas_mult = expense_changes.get("gas_price_multiplier", 1.0)
    
    volatility_reduction = scenario.get("volatility_reduction", 1.0)
    sigma_mult = 1.0 / volatility_reduction if volatility_reduction > 0 else 1.0
    
    lambda_mult = 1.0
    if income_impact < 0.9:
        lambda_mult = 1.0 + (1.0 - income_impact) * 0.8
    elif income_impact > 1.1:
        lambda_mult = 0.85
    
    shifts = [
        {
            "target": "mu_base",
            "type": "multiplicative",
            "magnitude": income_impact,
            "start_month": start_month,
            "duration_months": min(duration, 240),
            "decay": "linear",
        },
        {
            "target": "sigma_base",
            "type": "multiplicative",
            "magnitude": sigma_mult,
            "start_month": start_month,
            "duration_months": min(duration, 240),
            "decay": "linear",
        },
        {
            "target": "lambda",
            "type": "multiplicative",
            "magnitude": lambda_mult,
            "start_month": start_month,
            "duration_months": min(duration, 240),
            "decay": "linear",
        },
        {
            "target": "expenses",
            "type": "multiplicative",
            "magnitude": gas_mult,
            "start_month": start_month,
            "duration_months": min(duration, 240),
            "decay": "linear",
        },
    ]
    
    return MacroShock(
        category=category,
        scenario_name=scenario_name,
        start_month=start_month,
        parameter_shifts=shifts,
        narrative=scenario.get("name", "Unnamed shock")
    )


def check_macro_shocks(
    month: int,
    platforms: list[str],
    already_triggered: bool,
    loader: DataLoader,
    rng: random.Random
) -> Optional[MacroShock]:
    """
    Check all macro shock types for triggering this month.
    
    Priority order: recession > gas spike > regulatory > tech disruption
    (Only one shock can be active at a time)
    
    Args:
        month: Current month
        platforms: Active platforms (to determine gig type)
        already_triggered: Whether a macro shock is already active
        loader: DataLoader for accessing macro scenarios
        rng: Random number generator
    
    Returns:
        MacroShock if triggered, None otherwise
    """
    if already_triggered:
        return None
    
    macro_data = loader._load_json("macro_params.json")
    if not macro_data:
        return None
    
    trigger = check_recession_trigger(month, already_triggered, rng, macro_data)
    if not trigger:
        trigger = check_gas_spike_trigger(month, already_triggered, rng, macro_data)
    if not trigger:
        trigger = check_regulatory_shock_trigger(month, already_triggered, rng, macro_data)
    if not trigger:
        trigger = check_tech_disruption_trigger(month, already_triggered, rng, macro_data)
    
    if trigger:
        category, scenario_name = trigger
        gig_type = get_dominant_gig_type(platforms)
        
        macro_shock = convert_scenario_to_macro_shock(loader, category, scenario_name, month, gig_type)
        return macro_shock
    
    return None


def sample_macro_shock_for_trajectory(
    platforms: list[str],
    n_months: int,
    loader: DataLoader,
    random_seed: Optional[int] = None
) -> Optional[MacroShock]:
    """
    Sample macro shocks for an entire trajectory.
    
    Returns the first shock that triggers (only one per trajectory).
    
    Args:
        platforms: Active platforms (to determine gig type)
        n_months: Number of months to simulate
        loader: DataLoader for accessing macro scenarios
        random_seed: Optional seed for reproducibility
    
    Returns:
        MacroShock if any triggered, None otherwise
    """
    rng = random.Random(random_seed)
    
    for month in range(n_months):
        shock = check_macro_shocks(month, platforms, False, loader, rng)
        if shock:
            return shock
    
    return None

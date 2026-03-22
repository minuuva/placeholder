"""
Event Sampler - Probabilistic life event generation.

Samples random life events based on annual probabilities from expenses.json,
converting to monthly probabilities and applying archetype-specific modifiers.
"""

import random
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.models import EventType, LifeEvent
from data_pipeline.loaders import DataLoader


def annual_to_monthly_probability(annual_prob: float) -> float:
    """
    Convert annual probability to monthly probability.
    
    Uses: p_monthly = 1 - (1 - p_annual) ** (1/12)
    
    Args:
        annual_prob: Annual probability (0.0 to 1.0)
    
    Returns:
        Monthly probability
    """
    if annual_prob <= 0:
        return 0.0
    if annual_prob >= 1:
        return 1.0
    return 1.0 - (1.0 - annual_prob) ** (1.0 / 12.0)


def sample_from_range(range_values: list[float], rng: random.Random) -> float:
    """Sample a value uniformly from a range [min, max]."""
    if len(range_values) != 2:
        raise ValueError(f"Expected 2-element range, got {len(range_values)}")
    return rng.uniform(range_values[0], range_values[1])


def sample_vehicle_events(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample vehicle-related events for a given month.
    
    Events: minor repair, major repair, accident, replacement needed.
    """
    events = []
    vehicle_probs = expenses_data["life_events"]["probabilities"]["vehicle"]
    vehicle_impacts = expenses_data["life_events"]["impacts"]
    modifier = archetype["event_modifiers"]["vehicle_repair_probability"]
    
    # Minor repair
    monthly_prob = annual_to_monthly_probability(vehicle_probs["minor_repair"]) * modifier
    if rng.random() < monthly_prob:
        cost = sample_from_range(vehicle_impacts["vehicle_minor_repair"], rng)
        events.append(LifeEvent(
            event_type=EventType.VEHICLE_MINOR_REPAIR,
            month=month,
            income_impact=0.0,
            expense_impact=cost,
            duration_months=1,
            cascade_to_next=False,
            description=f"Minor vehicle repair: ${abs(cost):.0f} expense"
        ))
    
    # Major repair
    monthly_prob = annual_to_monthly_probability(vehicle_probs["major_repair"]) * modifier
    if rng.random() < monthly_prob:
        cost = sample_from_range(vehicle_impacts["vehicle_major_repair"], rng)
        events.append(LifeEvent(
            event_type=EventType.VEHICLE_MAJOR_REPAIR,
            month=month,
            income_impact=0.0,
            expense_impact=cost,
            duration_months=1,
            cascade_to_next=True,
            description=f"Major vehicle repair: ${abs(cost):.0f} expense (may cascade to debt)"
        ))
    
    # Accident (causes downtime)
    monthly_prob = annual_to_monthly_probability(vehicle_probs["accident"]) * modifier
    if rng.random() < monthly_prob:
        downtime_weeks = sample_from_range(vehicle_impacts["vehicle_accident_downtime_weeks"], rng)
        weekly_income = archetype["base_mu"] * archetype["hours_per_week"] / (4.33 * archetype["hours_per_week"])
        income_loss = -weekly_income * downtime_weeks
        events.append(LifeEvent(
            event_type=EventType.VEHICLE_ACCIDENT,
            month=month,
            income_impact=income_loss,
            expense_impact=0.0,
            duration_months=1,
            cascade_to_next=True,
            description=f"Vehicle accident: {downtime_weeks:.1f} weeks downtime, ${abs(income_loss):.0f} income loss"
        ))
    
    # Replacement needed
    monthly_prob = annual_to_monthly_probability(vehicle_probs["replacement_needed"]) * modifier
    if rng.random() < monthly_prob:
        events.append(LifeEvent(
            event_type=EventType.VEHICLE_REPLACEMENT,
            month=month,
            income_impact=0.0,
            expense_impact=-5000,
            duration_months=1,
            cascade_to_next=True,
            description="Vehicle replacement needed: $5000 expense (major cascade)"
        ))
    
    return events


def sample_health_events(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample health-related events for a given month.
    
    Events: minor illness, major illness, chronic issue.
    """
    events = []
    health_probs = expenses_data["life_events"]["probabilities"]["health"]
    health_impacts = expenses_data["life_events"]["impacts"]
    modifier = archetype["event_modifiers"]["health_issue_probability"]
    
    # Minor illness (days off)
    monthly_prob = annual_to_monthly_probability(health_probs["minor_illness"]) * modifier
    if rng.random() < monthly_prob:
        days_off = sample_from_range(health_impacts["health_minor_illness_days"], rng)
        daily_income = archetype["base_mu"] / 30.0
        income_loss = -daily_income * days_off
        events.append(LifeEvent(
            event_type=EventType.HEALTH_MINOR_ILLNESS,
            month=month,
            income_impact=income_loss,
            expense_impact=-200,
            duration_months=1,
            cascade_to_next=False,
            description=f"Minor illness: {days_off:.0f} days off, ${abs(income_loss):.0f} income loss"
        ))
    
    # Major illness (weeks off)
    monthly_prob = annual_to_monthly_probability(health_probs["major_illness"]) * modifier
    if rng.random() < monthly_prob:
        weeks_off = sample_from_range(health_impacts["health_major_illness_weeks"], rng)
        weekly_income = archetype["base_mu"] / 4.33
        income_loss = -weekly_income * weeks_off
        events.append(LifeEvent(
            event_type=EventType.HEALTH_MAJOR_ILLNESS,
            month=month,
            income_impact=income_loss,
            expense_impact=-1000,
            duration_months=int(weeks_off / 4),
            cascade_to_next=True,
            description=f"Major illness: {weeks_off:.0f} weeks off, ${abs(income_loss):.0f} income loss"
        ))
    
    # Chronic issue (ongoing impact)
    monthly_prob = annual_to_monthly_probability(health_probs["chronic_issue"]) * modifier
    if rng.random() < monthly_prob:
        monthly_income_loss = -archetype["base_mu"] * 0.1
        events.append(LifeEvent(
            event_type=EventType.HEALTH_CHRONIC_ISSUE,
            month=month,
            income_impact=monthly_income_loss,
            expense_impact=-500,
            duration_months=12,
            cascade_to_next=True,
            description=f"Chronic health issue: -10% income for 12 months, +$500/mo medical costs"
        ))
    
    return events


def sample_platform_events(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample platform-related events for a given month.
    
    Events: deactivation, fee increase, market saturation, policy change.
    """
    events = []
    platform_probs = expenses_data["life_events"]["probabilities"]["platform"]
    platform_impacts = expenses_data["life_events"]["impacts"]
    modifier = archetype["event_modifiers"]["platform_deactivation_probability"]
    
    # Deactivation (temporary income loss)
    monthly_prob = annual_to_monthly_probability(platform_probs["deactivation"]) * modifier
    if rng.random() < monthly_prob:
        weeks_deactivated = sample_from_range(platform_impacts["platform_deactivation_weeks"], rng)
        income_per_platform = archetype["base_mu"] / len(archetype["platforms"])
        weekly_loss = income_per_platform / 4.33
        income_loss = -weekly_loss * weeks_deactivated
        events.append(LifeEvent(
            event_type=EventType.PLATFORM_DEACTIVATION,
            month=month,
            income_impact=income_loss,
            expense_impact=0.0,
            duration_months=1,
            cascade_to_next=True,
            description=f"Platform deactivation: {weeks_deactivated:.0f} weeks, ${abs(income_loss):.0f} income loss"
        ))
    
    # Fee increase (permanent income reduction)
    monthly_prob = annual_to_monthly_probability(platform_probs["fee_increase"]) * modifier
    if rng.random() < monthly_prob:
        fee_pct = sample_from_range(platform_impacts["platform_fee_increase_percentage"], rng)
        income_reduction = -archetype["base_mu"] * fee_pct
        events.append(LifeEvent(
            event_type=EventType.PLATFORM_FEE_INCREASE,
            month=month,
            income_impact=income_reduction,
            expense_impact=0.0,
            duration_months=24 - month,
            cascade_to_next=False,
            description=f"Platform fee increase: {fee_pct*100:.1f}%, -${abs(income_reduction):.0f}/mo going forward"
        ))
    
    # Market saturation (gradual income decline)
    monthly_prob = annual_to_monthly_probability(platform_probs["market_saturation"]) * modifier
    if rng.random() < monthly_prob:
        income_reduction = -archetype["base_mu"] * 0.08
        events.append(LifeEvent(
            event_type=EventType.PLATFORM_MARKET_SATURATION,
            month=month,
            income_impact=income_reduction,
            expense_impact=0.0,
            duration_months=6,
            cascade_to_next=False,
            description=f"Market saturation: -8% income for 6 months"
        ))
    
    # Policy change (varies by platform)
    monthly_prob = annual_to_monthly_probability(platform_probs["policy_change"]) * modifier
    if rng.random() < monthly_prob:
        income_reduction = -archetype["base_mu"] * 0.05
        events.append(LifeEvent(
            event_type=EventType.PLATFORM_POLICY_CHANGE,
            month=month,
            income_impact=income_reduction,
            expense_impact=0.0,
            duration_months=3,
            cascade_to_next=False,
            description=f"Platform policy change: -5% income for 3 months"
        ))
    
    return events


def sample_housing_events(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample housing-related events for a given month.
    
    Events: rent increase, forced move, emergency repair.
    """
    events = []
    housing_probs = expenses_data["life_events"]["probabilities"]["housing"]
    housing_impacts = expenses_data["life_events"]["impacts"]
    modifier = archetype["event_modifiers"]["housing_instability_probability"]
    
    # Rent increase (permanent expense increase)
    monthly_prob = annual_to_monthly_probability(housing_probs["rent_increase"]) * modifier
    if rng.random() < monthly_prob:
        increase = sample_from_range(housing_impacts["rent_increase_monthly"], rng)
        events.append(LifeEvent(
            event_type=EventType.HOUSING_RENT_INCREASE,
            month=month,
            income_impact=0.0,
            expense_impact=-increase,
            duration_months=24 - month,
            cascade_to_next=False,
            description=f"Rent increase: +${increase:.0f}/mo going forward"
        ))
    
    # Forced move (one-time cost)
    monthly_prob = annual_to_monthly_probability(housing_probs["forced_move"]) * modifier
    if rng.random() < monthly_prob:
        events.append(LifeEvent(
            event_type=EventType.HOUSING_FORCED_MOVE,
            month=month,
            income_impact=0.0,
            expense_impact=-2500,
            duration_months=1,
            cascade_to_next=True,
            description="Forced move: $2500 moving costs (may cascade to debt)"
        ))
    
    # Emergency repair (one-time cost)
    monthly_prob = annual_to_monthly_probability(housing_probs["emergency_repair"]) * modifier
    if rng.random() < monthly_prob:
        events.append(LifeEvent(
            event_type=EventType.HOUSING_EMERGENCY_REPAIR,
            month=month,
            income_impact=0.0,
            expense_impact=-800,
            duration_months=1,
            cascade_to_next=False,
            description="Emergency housing repair: $800 expense"
        ))
    
    return events


def sample_positive_events(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample positive events for a given month.
    
    Events: new platform, skill upgrade, referral bonus, side gig.
    Note: New platform addition is handled by portfolio_evolution, so we skip it here.
    """
    events = []
    positive_probs = expenses_data["life_events"]["probabilities"]["positive"]
    positive_impacts = expenses_data["life_events"]["impacts"]
    modifier = archetype["event_modifiers"]["positive_event_probability"]
    
    # Skill upgrade (handled via portfolio evolution, but can trigger early boost)
    monthly_prob = annual_to_monthly_probability(positive_probs["skill_upgrade"]) * modifier
    if rng.random() < monthly_prob:
        boost_pct = sample_from_range(positive_impacts["skill_upgrade_income_boost"], rng)
        income_boost = archetype["base_mu"] * boost_pct
        events.append(LifeEvent(
            event_type=EventType.POSITIVE_SKILL_UPGRADE,
            month=month,
            income_impact=income_boost,
            expense_impact=0.0,
            duration_months=24 - month,
            cascade_to_next=False,
            description=f"Skill upgrade: +{boost_pct*100:.1f}% income going forward"
        ))
    
    # Referral bonus (one-time income)
    monthly_prob = annual_to_monthly_probability(positive_probs["referral_bonus"]) * modifier
    if rng.random() < monthly_prob:
        bonus = rng.uniform(200, 500)
        events.append(LifeEvent(
            event_type=EventType.POSITIVE_REFERRAL_BONUS,
            month=month,
            income_impact=bonus,
            expense_impact=0.0,
            duration_months=1,
            cascade_to_next=False,
            description=f"Referral bonus: +${bonus:.0f} one-time"
        ))
    
    # Side gig (temporary income boost)
    monthly_prob = annual_to_monthly_probability(positive_probs["side_gig"]) * modifier
    if rng.random() < monthly_prob:
        income_boost = rng.uniform(300, 800)
        duration = rng.randint(2, 6)
        events.append(LifeEvent(
            event_type=EventType.POSITIVE_SIDE_GIG,
            month=month,
            income_impact=income_boost,
            expense_impact=0.0,
            duration_months=min(duration, 24 - month),
            cascade_to_next=False,
            description=f"Side gig: +${income_boost:.0f}/mo for {duration} months"
        ))
    
    return events


def sample_all_events_for_month(
    archetype: dict,
    month: int,
    expenses_data: dict,
    rng: random.Random
) -> list[LifeEvent]:
    """
    Sample all possible event types for a given month.
    
    Returns:
        List of all events that occurred in this month
    """
    events = []
    
    events.extend(sample_vehicle_events(archetype, month, expenses_data, rng))
    events.extend(sample_health_events(archetype, month, expenses_data, rng))
    events.extend(sample_platform_events(archetype, month, expenses_data, rng))
    events.extend(sample_housing_events(archetype, month, expenses_data, rng))
    events.extend(sample_positive_events(archetype, month, expenses_data, rng))
    
    return events


def sample_events_for_trajectory(
    archetype: dict,
    n_months: int,
    expenses_data: dict,
    random_seed: Optional[int] = None
) -> list[LifeEvent]:
    """
    Sample events for an entire trajectory (all months).
    
    Args:
        archetype: Archetype data from archetypes.json
        n_months: Number of months to simulate (typically 24)
        expenses_data: Expenses data from expenses.json
        random_seed: Optional seed for reproducibility
    
    Returns:
        List of all events across all months
    """
    rng = random.Random(random_seed)
    all_events = []
    
    for month in range(n_months):
        month_events = sample_all_events_for_month(archetype, month, expenses_data, rng)
        all_events.extend(month_events)
    
    return all_events

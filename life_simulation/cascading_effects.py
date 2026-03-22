"""
Cascading Effects - Models follow-on impacts of life events.

When events occur, they can trigger cascading effects:
- Major expenses → debt → higher monthly payments
- Injuries → reduced hours → lower income
- Positive events → confidence boost → faster skill growth
"""

from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.models import LifeEvent, EventType, PortfolioState


def calculate_debt_cascade(
    event: LifeEvent,
    emergency_fund_weeks: int,
    monthly_income: float
) -> Optional[LifeEvent]:
    """
    Calculate debt cascade from major expense.
    
    If event expense exceeds emergency fund, worker takes on debt.
    This creates a follow-on expense (debt payment) for 12 months.
    
    Args:
        event: Original event that triggered cascade
        emergency_fund_weeks: Weeks of savings available
        monthly_income: Current monthly income
    
    Returns:
        Cascading expense event if debt is taken, None otherwise
    """
    expense = abs(event.expense_impact)
    
    if expense <= 0:
        return None
    
    emergency_fund = (monthly_income / 4.33) * emergency_fund_weeks
    
    if expense > emergency_fund:
        debt_amount = expense - emergency_fund
        
        debt_payment_months = 12
        monthly_payment = debt_amount / debt_payment_months
        
        return LifeEvent(
            event_type=EventType.HOUSING_EMERGENCY_REPAIR,
            month=event.month + 1,
            income_impact=0.0,
            expense_impact=-monthly_payment,
            duration_months=debt_payment_months,
            cascade_to_next=False,
            description=f"Debt payment from {event.event_type.value}: ${monthly_payment:.0f}/mo for {debt_payment_months} months"
        )
    
    return None


def calculate_stress_cascade(
    event: LifeEvent,
    platforms: list[str],
    monthly_income: float
) -> Optional[LifeEvent]:
    """
    Calculate stress/health cascade from major event.
    
    Major health issues or accidents can reduce working capacity for months.
    
    Args:
        event: Original event
        platforms: Active platforms
        monthly_income: Current monthly income
    
    Returns:
        Cascading income reduction event if applicable, None otherwise
    """
    if event.event_type == EventType.HEALTH_MAJOR_ILLNESS:
        stress_duration = 3
        income_reduction = -monthly_income * 0.15
        
        return LifeEvent(
            event_type=EventType.HEALTH_CHRONIC_ISSUE,
            month=event.month + 1,
            income_impact=income_reduction,
            expense_impact=0.0,
            duration_months=stress_duration,
            cascade_to_next=False,
            description=f"Reduced capacity after major illness: -15% income for {stress_duration} months"
        )
    
    elif event.event_type == EventType.VEHICLE_ACCIDENT:
        if 'uber' in platforms or 'lyft' in platforms or 'doordash' in platforms:
            stress_duration = 2
            income_reduction = -monthly_income * 0.10
            
            return LifeEvent(
                event_type=EventType.PLATFORM_MARKET_SATURATION,
                month=event.month + 1,
                income_impact=income_reduction,
                expense_impact=0.0,
                duration_months=stress_duration,
                cascade_to_next=False,
                description=f"Confidence impact after accident: -10% income for {stress_duration} months"
            )
    
    return None


def calculate_platform_loss_cascade(
    event: LifeEvent,
    platforms: list[str],
    monthly_income: float
) -> Optional[LifeEvent]:
    """
    Calculate cascade from platform deactivation.
    
    Temporary deactivation may lead to longer-term income loss if worker
    struggles to reactivate or loses preferred time slots.
    
    Args:
        event: Platform deactivation event
        platforms: Active platforms
        monthly_income: Current monthly income
    
    Returns:
        Cascading income event if applicable, None otherwise
    """
    if event.event_type == EventType.PLATFORM_DEACTIVATION:
        if len(platforms) <= 1:
            cascade_duration = 2
            income_loss = -monthly_income * 0.20
            
            return LifeEvent(
                event_type=EventType.PLATFORM_MARKET_SATURATION,
                month=event.month + int(event.duration_months),
                income_impact=income_loss,
                expense_impact=0.0,
                duration_months=cascade_duration,
                cascade_to_next=False,
                description=f"Difficulty reactivating platform: -20% income for {cascade_duration} months"
            )
    
    return None


def calculate_confidence_cascade(
    event: LifeEvent,
    current_skill_multiplier: float
) -> Optional[tuple[float, int]]:
    """
    Calculate confidence boost from positive events.
    
    Positive events can accelerate skill growth temporarily.
    
    Args:
        event: Positive event
        current_skill_multiplier: Current skill level
    
    Returns:
        (skill_boost_multiplier, duration_months) if applicable, None otherwise
    """
    if event.event_type in [EventType.POSITIVE_SKILL_UPGRADE, EventType.POSITIVE_REFERRAL_BONUS]:
        boost_multiplier = 1.05
        boost_duration = 6
        return (boost_multiplier, boost_duration)
    
    return None


def apply_cascading_effects(
    event: LifeEvent,
    portfolio_state: PortfolioState,
    emergency_fund_weeks: int
) -> list[LifeEvent]:
    """
    Apply all cascading effects for a given event.
    
    Checks for:
    - Debt cascades (major expenses → debt payments)
    - Stress cascades (health issues → reduced capacity)
    - Platform loss cascades (deactivation → reactivation difficulties)
    
    Args:
        event: Original event
        portfolio_state: Current portfolio state
        emergency_fund_weeks: Weeks of emergency savings
    
    Returns:
        List of cascading events (may be empty)
    """
    cascading_events = []
    
    if not event.cascade_to_next:
        return cascading_events
    
    debt_cascade = calculate_debt_cascade(
        event,
        emergency_fund_weeks,
        portfolio_state.monthly_base_income
    )
    if debt_cascade:
        cascading_events.append(debt_cascade)
    
    stress_cascade = calculate_stress_cascade(
        event,
        portfolio_state.active_platforms,
        portfolio_state.monthly_base_income
    )
    if stress_cascade:
        cascading_events.append(stress_cascade)
    
    platform_cascade = calculate_platform_loss_cascade(
        event,
        portfolio_state.active_platforms,
        portfolio_state.monthly_base_income
    )
    if platform_cascade:
        cascading_events.append(platform_cascade)
    
    return cascading_events


def process_all_cascading_effects(
    events: list[LifeEvent],
    portfolio_state: PortfolioState,
    emergency_fund_weeks: int,
    max_cascade_depth: int = 2
) -> list[LifeEvent]:
    """
    Process cascading effects for all events, up to max depth.
    
    Args:
        events: List of original events
        portfolio_state: Current portfolio state
        emergency_fund_weeks: Weeks of emergency savings
        max_cascade_depth: Maximum cascade depth (default 2)
    
    Returns:
        Combined list of original events plus all cascading events
    """
    all_events = events.copy()
    current_level_events = events.copy()
    
    for depth in range(max_cascade_depth):
        next_level_events = []
        
        for event in current_level_events:
            cascades = apply_cascading_effects(event, portfolio_state, emergency_fund_weeks)
            next_level_events.extend(cascades)
        
        if not next_level_events:
            break
        
        all_events.extend(next_level_events)
        current_level_events = next_level_events
    
    return all_events

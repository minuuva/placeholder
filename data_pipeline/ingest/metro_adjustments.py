"""
Geographic adjustments for gig worker income and expenses.

Based on BLS cost-of-living data and regional market research.
Provides multipliers to adjust base income and expense parameters by metropolitan area.
"""

# Metropolitan area adjustments
# Based on BLS cost-of-living indices and gig platform market data
METRO_ADJUSTMENTS = {
    "national": {
        "income_multiplier": 1.0,
        "expense_multiplier": 1.0,
        "competition_index": 1.0,
        "base_rent": 1500,
        "gas_price_multiplier": 1.0,
        "description": "National average baseline",
    },
    "san_francisco": {
        "income_multiplier": 1.4,  # Higher fares due to cost of living
        "expense_multiplier": 1.6,  # Much higher gas, rent, insurance
        "competition_index": 1.3,  # More drivers, higher saturation
        "base_rent": 2800,
        "gas_price_multiplier": 1.25,  # California gas prices
        "description": "San Francisco Bay Area - high cost, high competition",
    },
    "new_york": {
        "income_multiplier": 1.3,  # Higher fares, but variable by borough
        "expense_multiplier": 1.5,  # High rent, insurance, parking
        "competition_index": 1.4,  # Very high competition
        "base_rent": 2500,
        "gas_price_multiplier": 1.15,
        "description": "New York City - high density, high costs",
    },
    "atlanta": {
        "income_multiplier": 0.95,  # Slightly below national average
        "expense_multiplier": 0.85,  # Lower cost of living
        "competition_index": 0.9,  # Moderate competition
        "base_rent": 1400,
        "gas_price_multiplier": 0.95,
        "description": "Atlanta - moderate market, lower costs",
    },
    "dallas": {
        "income_multiplier": 0.98,
        "expense_multiplier": 0.88,
        "competition_index": 0.95,
        "base_rent": 1350,
        "gas_price_multiplier": 0.92,
        "description": "Dallas-Fort Worth - growing market, affordable",
    },
    "rural": {
        "income_multiplier": 0.70,  # Lower demand, longer distances between rides
        "expense_multiplier": 0.75,  # Lower rent but higher gas usage (distance)
        "competition_index": 0.6,  # Less competition
        "base_rent": 900,
        "gas_price_multiplier": 0.98,
        "description": "Rural/small town - limited demand, low competition",
    },
}

# Regional seasonality adjustments
# Some metros have unique seasonal patterns
METRO_SEASONALITY_ADJUSTMENTS = {
    "san_francisco": {
        "summer_boost": 1.15,  # Tech conference season, tourism
        "winter_penalty": 0.95,  # Less tourism
    },
    "new_york": {
        "summer_penalty": 0.90,  # Many residents leave the city
        "winter_boost": 1.05,  # Holiday season, events
    },
    "atlanta": {
        "summer_penalty": 0.92,  # Heat reduces outdoor activity
        "fall_boost": 1.08,  # Football season, events
    },
}

# Platform-specific metro adjustments
# Some platforms perform differently in different markets
PLATFORM_METRO_PERFORMANCE = {
    "uber": {
        "san_francisco": 1.2,  # Home market advantage
        "new_york": 1.15,
        "atlanta": 1.0,
        "dallas": 1.0,
        "rural": 0.8,
    },
    "lyft": {
        "san_francisco": 1.15,
        "new_york": 1.0,
        "atlanta": 0.95,
        "dallas": 0.95,
        "rural": 0.7,
    },
    "doordash": {
        "san_francisco": 1.1,
        "new_york": 1.05,
        "atlanta": 1.0,
        "dallas": 1.0,
        "rural": 0.9,  # Still decent in rural areas
    },
    "instacart": {
        "san_francisco": 1.2,  # High grocery delivery demand
        "new_york": 1.1,
        "atlanta": 0.95,
        "dallas": 0.95,
        "rural": 0.6,  # Poor performance in rural areas
    },
}


def get_metro_adjustment(metro_area):
    """
    Get adjustment factors for a metropolitan area.
    
    Args:
        metro_area: String identifier for metro area (e.g., 'san_francisco', 'national')
    
    Returns:
        Dictionary of adjustment factors
    
    Raises:
        ValueError: If metro_area is not recognized
    """
    metro_key = metro_area.lower().replace(" ", "_")
    
    if metro_key not in METRO_ADJUSTMENTS:
        raise ValueError(
            f"Unknown metro area: {metro_area}. "
            f"Available: {', '.join(METRO_ADJUSTMENTS.keys())}"
        )
    
    return METRO_ADJUSTMENTS[metro_key]


def adjust_income(base_income, metro_area, platform=None):
    """
    Adjust base income for geographic location and platform.
    
    Args:
        base_income: Base monthly income (national average)
        metro_area: Metropolitan area identifier
        platform: Optional platform name for platform-specific adjustments
    
    Returns:
        Adjusted monthly income
    """
    metro = get_metro_adjustment(metro_area)
    adjusted = base_income * metro["income_multiplier"]
    
    # Apply platform-specific adjustment if provided
    if platform and platform in PLATFORM_METRO_PERFORMANCE:
        platform_adj = PLATFORM_METRO_PERFORMANCE[platform].get(
            metro_area.lower().replace(" ", "_"), 1.0
        )
        adjusted *= platform_adj
    
    return adjusted


def adjust_expenses(base_expenses, metro_area):
    """
    Adjust base expenses for geographic location.
    
    Args:
        base_expenses: Dictionary of base expenses (national average)
        metro_area: Metropolitan area identifier
    
    Returns:
        Dictionary of adjusted expenses
    """
    metro = get_metro_adjustment(metro_area)
    adjusted_expenses = {}
    
    for expense_type, value in base_expenses.items():
        if isinstance(value, tuple):
            # Handle range tuples (min, max)
            adjusted_expenses[expense_type] = (
                value[0] * metro["expense_multiplier"],
                value[1] * metro["expense_multiplier"]
            )
        elif isinstance(value, (int, float)):
            # Handle single values
            adjusted_expenses[expense_type] = value * metro["expense_multiplier"]
        else:
            # Pass through other types unchanged
            adjusted_expenses[expense_type] = value
    
    return adjusted_expenses


def get_competition_factor(metro_area):
    """
    Get competition index for a metro area.
    Higher values mean more competition (harder to get rides/deliveries).
    
    Args:
        metro_area: Metropolitan area identifier
    
    Returns:
        Competition index (1.0 = national average)
    """
    metro = get_metro_adjustment(metro_area)
    return metro["competition_index"]


def calculate_effective_income(
    base_income, 
    metro_area, 
    platform=None, 
    competition_effect=True
):
    """
    Calculate effective income accounting for both metro multiplier and competition.
    
    Args:
        base_income: Base monthly income (national average)
        metro_area: Metropolitan area identifier
        platform: Optional platform name
        competition_effect: Whether to apply competition penalty
    
    Returns:
        Effective monthly income after all adjustments
    """
    # Apply basic metro adjustment
    income = adjust_income(base_income, metro_area, platform)
    
    # Apply competition effect (inverse relationship)
    if competition_effect:
        competition = get_competition_factor(metro_area)
        # Higher competition reduces income slightly (not 1:1)
        competition_penalty = 1.0 - (0.1 * (competition - 1.0))
        income *= competition_penalty
    
    return income


def get_all_metros():
    """Return list of all available metro area identifiers."""
    return list(METRO_ADJUSTMENTS.keys())


def validate_metro_adjustments():
    """Validate that all metro adjustments are reasonable."""
    errors = []
    
    for metro, data in METRO_ADJUSTMENTS.items():
        # Check multipliers are positive
        if data["income_multiplier"] <= 0:
            errors.append(f"{metro}: income_multiplier must be positive")
        if data["expense_multiplier"] <= 0:
            errors.append(f"{metro}: expense_multiplier must be positive")
        
        # Check competition index is reasonable
        if not (0.5 < data["competition_index"] < 2.0):
            errors.append(f"{metro}: competition_index out of reasonable range")
        
        # Check rent is positive
        if data["base_rent"] <= 0:
            errors.append(f"{metro}: base_rent must be positive")
    
    # Check platform adjustments
    for platform, metros in PLATFORM_METRO_PERFORMANCE.items():
        for metro, multiplier in metros.items():
            if not (0.5 < multiplier < 2.0):
                errors.append(
                    f"{platform} in {metro}: multiplier {multiplier} out of range"
                )
    
    if errors:
        raise ValueError(f"Metro adjustment validation failed:\n" + "\n".join(errors))
    
    return True


if __name__ == "__main__":
    print("Validating metro adjustments...")
    try:
        validate_metro_adjustments()
        print("✓ All metro adjustments validated successfully")
        
        print("\n=== Metro Adjustment Summary ===")
        print(f"Metro areas configured: {len(METRO_ADJUSTMENTS)}")
        print(f"Platforms with metro-specific data: {len(PLATFORM_METRO_PERFORMANCE)}")
        
        print("\n=== Sample Adjustments ===")
        base_income = 4000
        print(f"Base income: ${base_income:,.0f}/month")
        
        for metro in ["national", "san_francisco", "new_york", "atlanta", "rural"]:
            adjusted = adjust_income(base_income, metro)
            competition = get_competition_factor(metro)
            effective = calculate_effective_income(base_income, metro)
            print(f"{metro:15s}: ${adjusted:,.0f} (competition: {competition:.2f}x) → ${effective:,.0f} effective")
        
        print("\n=== Platform Performance Example (Uber) ===")
        for metro in ["san_francisco", "new_york", "atlanta", "rural"]:
            adjusted = adjust_income(base_income, metro, platform="uber")
            print(f"{metro:15s}: ${adjusted:,.0f}/month")
        
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        exit(1)

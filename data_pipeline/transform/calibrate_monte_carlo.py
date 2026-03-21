"""
Transform research-backed parameters into Monte Carlo simulation parameters.

This module converts hourly rates, expense data, and volatility research
into (μ, σ) parameters ready for Monte Carlo simulation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.static_params import (
    PLATFORM_EARNINGS, EXPENSES, INCOME_VOLATILITY,
    TAX_QUARTERS, get_platform_gig_type
)
from ingest.metro_adjustments import (
    adjust_income, adjust_expenses, get_metro_adjustment
)


def calculate_monthly_gross(platform, hours_per_week):
    """
    Calculate monthly gross income from platform and hours.
    
    Args:
        platform: Platform name (e.g., 'uber', 'doordash')
        hours_per_week: Weekly working hours
    
    Returns:
        Monthly gross income in dollars
    """
    if platform not in PLATFORM_EARNINGS:
        raise ValueError(f"Unknown platform: {platform}")
    
    hourly_rate = PLATFORM_EARNINGS[platform]["hourly_rate"]
    
    # Calculate monthly gross (4.33 weeks/month average)
    weekly_income = hourly_rate * hours_per_week
    monthly_income = weekly_income * 4.33
    
    return monthly_income


def calculate_monthly_expenses(platforms, hours_per_week, metro="national"):
    """
    Calculate total monthly expenses for gig worker.
    
    Args:
        platforms: List of platform names
        hours_per_week: Total weekly working hours
        metro: Metropolitan area for cost adjustments
    
    Returns:
        Total monthly expenses in dollars
    """
    # Determine if full-time (>35 hrs/week) or part-time
    is_fulltime = hours_per_week >= 35
    
    # Gas expenses (weekly, need to convert to monthly)
    if is_fulltime:
        gas_weekly = sum(EXPENSES["gas_weekly_fulltime"]) / 2  # Use midpoint
    else:
        gas_weekly = sum(EXPENSES["gas_weekly_parttime"]) / 2
    
    gas_monthly = gas_weekly * 4.33
    
    # Other monthly expenses
    maintenance = sum(EXPENSES["maintenance_monthly"]) / 2
    depreciation = EXPENSES["vehicle_depreciation_monthly"]
    insurance = EXPENSES["insurance_monthly"]
    phone = EXPENSES["phone_data_monthly"]
    
    total_expenses = gas_monthly + maintenance + depreciation + insurance + phone
    
    # Apply metro adjustment
    metro_adj = get_metro_adjustment(metro)
    adjusted_expenses = total_expenses * metro_adj["expense_multiplier"]
    
    # Add rent as baseline living expense (not work-related but affects budget)
    rent = metro_adj["base_rent"]
    
    return {
        "work_expenses": adjusted_expenses,
        "rent": rent,
        "total": adjusted_expenses + rent
    }


def calculate_net_income(gross_income, expenses, include_self_employment_tax=True):
    """
    Calculate net income after work expenses and taxes (before living expenses).
    
    This represents monthly disposable income available for loan payments.
    Rent is NOT subtracted here - it's tracked separately for underwriting purposes.
    
    Args:
        gross_income: Monthly gross income
        expenses: Monthly expenses (from calculate_monthly_expenses)
        include_self_employment_tax: Whether to deduct self-employment tax
    
    Returns:
        Net monthly income after work expenses and taxes
    """
    net = gross_income - expenses["work_expenses"]
    
    # Self-employment tax (15.3% on net earnings)
    if include_self_employment_tax:
        se_tax = net * EXPENSES["self_employment_tax"]
        net -= se_tax
    
    # Note: Rent is NOT subtracted here - it's a separate underwriting consideration
    # The Monte Carlo simulation models income volatility, not budget constraints
    
    return net


def calculate_income_volatility(platforms, base_sigma=None):
    """
    Calculate income volatility (standard deviation) based on platform mix.
    
    Args:
        platforms: List of platform names
        base_sigma: Base sigma (if None, calculated from CV)
    
    Returns:
        Standard deviation of monthly income
    """
    # Use JPMorgan's 36% coefficient of variation as baseline
    base_cv = INCOME_VOLATILITY["median_cv"]
    
    # Single platform = baseline volatility
    # Multiple platforms = reduced volatility (diversification effect)
    num_platforms = len(platforms)
    
    if num_platforms == 1:
        cv = base_cv
        # Apply platform-specific multiplier
        platform = platforms[0]
        if platform in PLATFORM_EARNINGS:
            cv *= PLATFORM_EARNINGS[platform]["variance_multiplier"]
    else:
        # Diversification reduces volatility (but not linearly)
        # σ_portfolio ≈ σ / sqrt(n) for uncorrelated assets
        diversification_factor = 1.0 / (num_platforms ** 0.5)
        cv = base_cv * diversification_factor
        
        # Average the platform multipliers
        avg_multiplier = sum(
            PLATFORM_EARNINGS[p]["variance_multiplier"] 
            for p in platforms if p in PLATFORM_EARNINGS
        ) / num_platforms
        cv *= avg_multiplier
    
    return cv


def calculate_income_params(
    platforms, 
    hours_per_week, 
    metro="national",
    include_tax=True
):
    """
    Calculate (μ, σ) parameters for Monte Carlo simulation.
    
    This is the main function that transforms all research data into
    simulation-ready parameters.
    
    Args:
        platforms: List of platform names
        hours_per_week: Total weekly working hours
        metro: Metropolitan area
        include_tax: Whether to account for self-employment tax
    
    Returns:
        Dictionary with mu, sigma, and breakdown details
    """
    # Calculate gross income (sum across all platforms)
    # Assume hours distributed equally across platforms
    hours_per_platform = hours_per_week / len(platforms)
    
    total_gross = 0
    for platform in platforms:
        gross = calculate_monthly_gross(platform, hours_per_platform)
        # Apply metro adjustment
        adjusted_gross = adjust_income(gross, metro, platform)
        total_gross += adjusted_gross
    
    # Calculate expenses
    expenses = calculate_monthly_expenses(platforms, hours_per_week, metro)
    
    # Calculate net income (μ)
    net_income = calculate_net_income(total_gross, expenses, include_tax)
    
    # Calculate volatility (σ)
    cv = calculate_income_volatility(platforms)
    sigma = net_income * cv
    
    return {
        "mu": round(net_income, 2),
        "sigma": round(sigma, 2),
        "coefficient_of_variation": round(cv, 3),
        "breakdown": {
            "gross_income": round(total_gross, 2),
            "work_expenses": round(expenses["work_expenses"], 2),
            "rent": round(expenses["rent"], 2),
            "self_employment_tax": round(total_gross * EXPENSES["self_employment_tax"], 2) if include_tax else 0,
            "net_income": round(net_income, 2),
        }
    }


def apply_metro_adjustment_to_params(base_mu, base_sigma, metro):
    """
    Apply metro adjustments to existing (μ, σ) parameters.
    
    Args:
        base_mu: Base mean income (national)
        base_sigma: Base standard deviation (national)
        metro: Metropolitan area
    
    Returns:
        Tuple of (adjusted_mu, adjusted_sigma)
    """
    metro_data = get_metro_adjustment(metro)
    
    # Adjust mean income
    adjusted_mu = base_mu * metro_data["income_multiplier"]
    
    # Adjust expenses (which effectively reduces net income)
    expense_adjustment = metro_data["expense_multiplier"]
    # Rough approximation: expenses are ~40% of gross, so this affects net
    adjusted_mu = adjusted_mu * (1.0 - 0.15 * (expense_adjustment - 1.0))
    
    # Sigma scales with mean (constant CV assumption)
    cv = base_sigma / base_mu if base_mu > 0 else 0.36
    adjusted_sigma = adjusted_mu * cv
    
    return (round(adjusted_mu, 2), round(adjusted_sigma, 2))


def estimate_params_from_archetype(
    archetype_name,
    platforms,
    hours_per_week,
    metro="national",
    skill_level=1.0
):
    """
    Estimate income parameters for a gig worker archetype.
    
    Args:
        archetype_name: Descriptive name (for documentation)
        platforms: List of platforms
        hours_per_week: Weekly hours
        metro: Metropolitan area
        skill_level: Skill multiplier (1.0 = average, 1.1 = 10% better)
    
    Returns:
        Dictionary with complete parameter set for archetype
    """
    params = calculate_income_params(platforms, hours_per_week, metro)
    
    # Apply skill adjustment
    params["mu"] = round(params["mu"] * skill_level, 2)
    params["sigma"] = round(params["sigma"] * skill_level, 2)
    
    # Add metadata
    params["archetype_name"] = archetype_name
    params["platforms"] = platforms
    params["hours_per_week"] = hours_per_week
    params["metro"] = metro
    params["skill_level"] = skill_level
    
    return params


def validate_params(mu, sigma):
    """
    Validate that parameters are reasonable for simulation.
    
    Args:
        mu: Mean income
        sigma: Standard deviation
    
    Returns:
        Boolean indicating validity
    
    Raises:
        ValueError: If parameters are invalid
    """
    errors = []
    
    if mu <= 0:
        errors.append(f"mu must be positive, got {mu}")
    
    if sigma < 0:
        errors.append(f"sigma must be non-negative, got {sigma}")
    
    # Check CV is reasonable (shouldn't exceed 100% typically)
    cv = sigma / mu if mu > 0 else 0
    if cv > 1.5:
        errors.append(f"CV too high: {cv:.1%} (sigma={sigma}, mu={mu})")
    
    # Check minimum income threshold (allow part-time workers)
    if mu < 500:
        errors.append(f"mu below minimum viable income: ${mu:.2f}/month")
    
    if errors:
        raise ValueError("Parameter validation failed:\n" + "\n".join(errors))
    
    return True


def get_example_archetypes():
    """
    Generate example parameter sets for common archetypes.
    
    Returns:
        Dictionary of archetype parameters
    """
    archetypes = {}
    
    # Volatile Vic - single platform, high variance
    archetypes["volatile_vic"] = estimate_params_from_archetype(
        "Volatile Vic",
        platforms=["doordash"],
        hours_per_week=45,
        metro="national",
        skill_level=0.95  # Slightly below average
    )
    
    # Steady Sarah - multi-platform, diversified
    archetypes["steady_sarah"] = estimate_params_from_archetype(
        "Steady Sarah",
        platforms=["uber", "doordash", "instacart"],
        hours_per_week=40,
        metro="atlanta",
        skill_level=1.10  # Experienced, efficient
    )
    
    # Weekend Warrior - part-time rideshare
    archetypes["weekend_warrior"] = estimate_params_from_archetype(
        "Weekend Warrior",
        platforms=["uber"],
        hours_per_week=15,
        metro="dallas",
        skill_level=1.0
    )
    
    # SF Hustler - high cost, high earnings market
    archetypes["sf_hustler"] = estimate_params_from_archetype(
        "SF Hustler",
        platforms=["uber", "doordash"],
        hours_per_week=50,
        metro="san_francisco",
        skill_level=1.15  # Very experienced
    )
    
    # Rural Rider - low density market
    archetypes["rural_rider"] = estimate_params_from_archetype(
        "Rural Rider",
        platforms=["doordash", "instacart"],
        hours_per_week=40,
        metro="rural",
        skill_level=0.90  # Limited opportunities
    )
    
    return archetypes


if __name__ == "__main__":
    print("="*60)
    print("Monte Carlo Parameter Calibration")
    print("="*60)
    
    # Test basic calculation
    print("\n=== Test 1: Basic Parameter Calculation ===")
    params = calculate_income_params(
        platforms=["uber"],
        hours_per_week=40,
        metro="national"
    )
    print(f"Platform: Uber (40 hrs/week, national)")
    print(f"  μ = ${params['mu']:,.2f}/month")
    print(f"  σ = ${params['sigma']:,.2f}/month")
    print(f"  CV = {params['coefficient_of_variation']:.1%}")
    print(f"\nBreakdown:")
    for key, value in params['breakdown'].items():
        print(f"  {key}: ${value:,.2f}")
    
    # Test validation
    print("\n=== Test 2: Parameter Validation ===")
    try:
        validate_params(params['mu'], params['sigma'])
        print("✓ Parameters validated successfully")
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
    
    # Test metro adjustments
    print("\n=== Test 3: Metro Adjustments ===")
    for metro in ["national", "san_francisco", "atlanta", "rural"]:
        params = calculate_income_params(
            platforms=["uber"],
            hours_per_week=40,
            metro=metro
        )
        print(f"{metro:15s}: μ=${params['mu']:,.0f}, σ=${params['sigma']:,.0f}, CV={params['coefficient_of_variation']:.1%}")
    
    # Test diversification effect
    print("\n=== Test 4: Diversification Effect ===")
    for num_platforms in [1, 2, 3]:
        platforms = ["uber", "doordash", "instacart"][:num_platforms]
        params = calculate_income_params(
            platforms=platforms,
            hours_per_week=40,
            metro="national"
        )
        print(f"{num_platforms} platform(s): μ=${params['mu']:,.0f}, σ=${params['sigma']:,.0f}, CV={params['coefficient_of_variation']:.1%}")
    
    # Generate example archetypes
    print("\n=== Test 5: Example Archetypes ===")
    archetypes = get_example_archetypes()
    for name, params in archetypes.items():
        print(f"\n{params['archetype_name']}:")
        print(f"  Platforms: {', '.join(params['platforms'])}")
        print(f"  Hours/week: {params['hours_per_week']}")
        print(f"  Metro: {params['metro']}")
        print(f"  μ = ${params['mu']:,.2f}/month")
        print(f"  σ = ${params['sigma']:,.2f}/month")
        print(f"  CV = {params['coefficient_of_variation']:.1%}")
    
    print("\n" + "="*60)
    print("✓ Calibration tests completed")
    print("="*60)

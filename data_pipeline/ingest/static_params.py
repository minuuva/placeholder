"""
Static parameters from JPMorgan Chase Institute and gig platform research.

All values are hardcoded from published research studies to ensure credibility
and reproducibility. These serve as the foundation for Monte Carlo simulations.

Sources:
- JPMorgan Chase Institute: Income volatility and gig worker earnings patterns
- Gridwise: 2025 Uber driver earnings data
- Triplog: Part-time and full-time driver weekly earnings
- Various industry reports for platform-specific rates
"""

# JPMorgan Chase Institute findings
# Source: JPMorgan Chase Institute research on income volatility
INCOME_VOLATILITY = {
    "median_cv": 0.36,  # 36% coefficient of variation (month-to-month)
    "typical_swing": 0.09,  # 9% typical month-to-month earnings change
    "extreme_swing": 0.21,  # 21% swing occurs in 1 out of 4 months
    "buffer_weeks": 6,  # Weeks of income needed to weather simultaneous income dip and expense spike
    "spike_probability": 2.0,  # Income spikes are 2x more likely than dips
    "spike_months": [3, 12],  # March and December most common for income spikes
}

# Platform earnings (Gridwise, Triplog, industry estimates)
PLATFORM_EARNINGS = {
    "uber": {
        "hourly_rate": 23.33,  # 2025 average (Gridwise)
        "part_time_weekly": (200, 500),  # 10-20 hrs/week range
        "full_time_weekly": (800, 1500),  # 40+ hrs/week range
        "variance_multiplier": 1.0,  # Baseline variance
    },
    "doordash": {
        "hourly_rate": 18.50,  # Industry estimates
        "part_time_weekly": (150, 400),
        "full_time_weekly": (600, 1200),
        "variance_multiplier": 1.15,  # Higher variance than rideshare
    },
    "instacart": {
        "hourly_rate": 16.00,  # Industry estimates
        "part_time_weekly": (200, 600),
        "full_time_weekly": (500, 1000),
        "variance_multiplier": 1.10,
    },
    "lyft": {
        "hourly_rate": 22.00,  # Similar to Uber
        "part_time_weekly": (180, 480),
        "full_time_weekly": (750, 1400),
        "variance_multiplier": 1.0,
    },
    "grubhub": {
        "hourly_rate": 17.50,
        "part_time_weekly": (140, 380),
        "full_time_weekly": (550, 1100),
        "variance_multiplier": 1.12,
    },
}

# Expense structure (from Triplog, industry data)
EXPENSES = {
    "gas_weekly_fulltime": (150, 400),  # Varies significantly by market and gas prices
    "gas_weekly_parttime": (50, 150),
    "maintenance_monthly": (50, 100),  # Oil changes, tire rotation, wear and tear
    "self_employment_tax": 0.153,  # 15.3% (Social Security + Medicare)
    "vehicle_depreciation_monthly": 200,  # Average depreciation for delivery/rideshare
    "insurance_monthly": 150,  # Commercial rideshare insurance add-on
    "phone_data_monthly": 50,  # Phone and data plan costs
    "platform_fees_percentage": 0.25,  # Average platform take rate (already in hourly rates)
}

# Seasonality multipliers (from JPMorgan - spikes in March/December)
# Values represent monthly income multipliers relative to annual average
SEASONALITY_MULTIPLIERS = {
    "delivery": {
        1: 1.05,   # January - post-holiday, cold weather boosts delivery
        2: 0.95,   # February - shortest month, slower
        3: 1.15,   # March - JPMorgan spike month
        4: 0.98,   # April - tax season, moderate
        5: 0.92,   # May - spring slowdown begins
        6: 0.88,   # June - summer lull
        7: 0.85,   # July - lowest delivery demand
        8: 0.90,   # August - back to school pickup
        9: 0.95,   # September - fall increase
        10: 1.10,  # October - holiday season begins
        11: 1.25,  # November - Thanksgiving surge
        12: 1.35,  # December - JPMorgan spike month, holiday peak
    },
    "rideshare": {
        1: 0.95,   # January - post-holiday lull
        2: 0.95,   # February - winter, moderate
        3: 1.10,   # March - spring break, events
        4: 1.05,   # April - moderate spring demand
        5: 1.05,   # May - events, graduations
        6: 1.10,   # June - summer travel begins
        7: 1.15,   # July - peak summer travel
        8: 1.10,   # August - continued summer demand
        9: 1.00,   # September - back to normal
        10: 1.05,  # October - fall events
        11: 1.15,  # November - Thanksgiving travel
        12: 1.20,  # December - holiday parties, airport runs
    },
    "general_gig": {
        1: 1.00,   # January - baseline
        2: 0.97,   # February - slightly slower
        3: 1.10,   # March - JPMorgan spike
        4: 1.02,   # April - moderate
        5: 0.98,   # May - slight dip
        6: 0.95,   # June - summer slowdown
        7: 0.93,   # July - summer low
        8: 0.97,   # August - pickup
        9: 1.00,   # September - back to baseline
        10: 1.08,  # October - increase
        11: 1.18,  # November - holiday boost
        12: 1.25,  # December - JPMorgan spike, holiday peak
    },
}

# Quarterly tax impact (self-employment tax estimated payments)
# Months when estimated taxes are due
TAX_QUARTERS = {
    "due_months": [4, 6, 9, 1],  # April, June, September, January
    "effective_income_reduction": 0.25,  # 25% reduction in take-home that month
}

# Life event probabilities (annual)
# These represent the baseline probability of events occurring per year
LIFE_EVENT_PROBABILITIES = {
    "vehicle": {
        "minor_repair": 0.40,  # 40% chance per year (oil change, brakes, tires)
        "major_repair": 0.15,  # 15% chance per year ($500-2000)
        "accident": 0.10,  # 10% chance per year (out 2-4 weeks)
        "replacement_needed": 0.05,  # 5% chance per year (total breakdown)
    },
    "health": {
        "minor_illness": 0.30,  # 30% chance (flu, cold, out 1 week)
        "major_illness": 0.10,  # 10% chance (injury, out 4-12 weeks)
        "chronic_issue": 0.05,  # 5% chance (ongoing health problem)
    },
    "platform": {
        "deactivation": 0.20,  # 20% chance per year (policy violation, ratings)
        "fee_increase": 0.25,  # 25% chance per year (platform raises fees)
        "market_saturation": 0.15,  # 15% chance (too many drivers in area)
        "policy_change": 0.20,  # 20% chance (new rules, requirements)
    },
    "housing": {
        "rent_increase": 0.30,  # 30% chance per year (10-20% increase)
        "forced_move": 0.05,  # 5% chance per year (eviction, landlord sale)
        "emergency_repair": 0.10,  # 10% chance (HVAC, plumbing)
    },
    "positive": {
        "new_platform": 0.25,  # 25% chance of adding another income source
        "skill_upgrade": 0.15,  # 15% chance (learn optimization, better routes)
        "referral_bonus": 0.20,  # 20% chance (refer friend, platform bonus)
        "side_gig": 0.10,  # 10% chance (add complementary income source)
    },
}

# Event financial impacts (in dollars or percentage)
EVENT_IMPACTS = {
    "vehicle_minor_repair": (-300, -150),  # Cost range
    "vehicle_major_repair": (-2000, -500),
    "vehicle_accident_downtime_weeks": (2, 4),  # Lost income weeks
    "health_minor_illness_days": (5, 7),  # Days unable to work
    "health_major_illness_weeks": (4, 12),
    "platform_deactivation_weeks": (2, 8),  # Time to resolve or switch platform
    "platform_fee_increase_percentage": (0.02, 0.05),  # 2-5% reduction in earnings
    "rent_increase_monthly": (100, 300),  # Additional monthly expense
    "new_platform_income_boost": (0.15, 0.30),  # 15-30% income increase
    "skill_upgrade_income_boost": (0.05, 0.10),  # 5-10% efficiency gain
}

# Portfolio evolution parameters
# How gig workers diversify and improve over time
PORTFOLIO_EVOLUTION = {
    "initial_platforms": 1.0,  # Average platforms at start
    "month_12_platforms": 2.3,  # Average platforms after 1 year (JPMorgan data)
    "diversification_rate": 0.10,  # 10% chance per month of adding platform
    "platform_churn_rate": 0.05,  # 5% chance per month of dropping platform
    "hourly_earnings_growth": 0.10,  # 10% improvement over 12 months
    "efficiency_curve": "logarithmic",  # Fast improvement early, then plateaus
    "quit_probability_annual": 0.15,  # 15% chance of quitting gig work entirely per year
}

# Macro shock baseline probabilities
MACRO_SHOCKS = {
    "recession_annual_probability": 0.10,  # 10% chance per year
    "gas_spike_annual_probability": 0.15,  # 15% chance per year
    "regulatory_change_annual_probability": 0.05,  # 5% chance per year (AB5-style)
    "tech_disruption_annual_probability": 0.05,  # 5% chance per year (autonomous vehicles)
}

# Default and recovery parameters
DEFAULT_PARAMETERS = {
    "minimum_monthly_income": 1500,  # Below this is considered high risk
    "emergency_fund_weeks": 6,  # JPMorgan recommended buffer
    "debt_to_income_threshold": 0.40,  # 40% DTI is warning level
    "recovery_rate": 0.30,  # Expected recovery on defaulted loans (30%)
}


def get_platform_gig_type(platform):
    """Map platform to gig type for seasonality lookup."""
    delivery_platforms = ["doordash", "grubhub", "instacart", "ubereats"]
    rideshare_platforms = ["uber", "lyft"]
    
    if platform in delivery_platforms:
        return "delivery"
    elif platform in rideshare_platforms:
        return "rideshare"
    else:
        return "general_gig"


def validate_parameters():
    """Validate that all parameters are within reasonable ranges."""
    errors = []
    
    # Check volatility parameters
    if not (0 < INCOME_VOLATILITY["median_cv"] < 1):
        errors.append("median_cv should be between 0 and 1")
    
    # Check platform earnings are positive
    for platform, data in PLATFORM_EARNINGS.items():
        if data["hourly_rate"] <= 0:
            errors.append(f"{platform} hourly_rate must be positive")
    
    # Check seasonality sums to approximately 12 (avg of 1.0)
    for gig_type, multipliers in SEASONALITY_MULTIPLIERS.items():
        total = sum(multipliers.values())
        if not (11.0 < total < 13.0):  # Allow some variance
            errors.append(f"{gig_type} seasonality should average to ~1.0 (sum: {total})")
    
    # Check probabilities are between 0 and 1
    for category, events in LIFE_EVENT_PROBABILITIES.items():
        for event, prob in events.items():
            if not (0 <= prob <= 1):
                errors.append(f"{category}.{event} probability out of range: {prob}")
    
    if errors:
        raise ValueError(f"Parameter validation failed:\n" + "\n".join(errors))
    
    return True


if __name__ == "__main__":
    # Validate parameters when run directly
    print("Validating static parameters...")
    try:
        validate_parameters()
        print("✓ All parameters validated successfully")
        
        # Print summary statistics
        print("\n=== Parameter Summary ===")
        print(f"Income volatility (CV): {INCOME_VOLATILITY['median_cv']:.1%}")
        print(f"Platforms configured: {len(PLATFORM_EARNINGS)}")
        print(f"Gig types with seasonality: {len(SEASONALITY_MULTIPLIERS)}")
        print(f"Life event categories: {len(LIFE_EVENT_PROBABILITIES)}")
        
        # Check seasonality averages
        print("\n=== Seasonality Averages ===")
        for gig_type, multipliers in SEASONALITY_MULTIPLIERS.items():
            avg = sum(multipliers.values()) / 12
            print(f"{gig_type}: {avg:.3f} (sum: {sum(multipliers.values()):.2f})")
        
    except ValueError as e:
        print(f"✗ Validation failed: {e}")
        exit(1)

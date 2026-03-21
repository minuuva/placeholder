"""
Build gig worker archetype personas with complete parameter sets.

Creates 5 differentiated personas representing common gig worker profiles,
each with unique income parameters, platform mix, and risk characteristics.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from transform.calibrate_monte_carlo import calculate_income_params
from ingest.static_params import LIFE_EVENT_PROBABILITIES, PORTFOLIO_EVOLUTION


def create_volatile_vic():
    """
    Volatile Vic: Single-platform delivery driver, high variance, unstable.
    
    Profile:
    - Full-time DoorDash only
    - No diversification
    - National average market
    - Below-average efficiency (new to gig work)
    - High income volatility
    - High risk of quitting or events
    """
    # Calculate base parameters
    params = calculate_income_params(
        platforms=["doordash"],
        hours_per_week=45,
        metro="national",
        include_tax=True
    )
    
    # Build complete archetype
    archetype = {
        "id": "volatile_vic",
        "name": "Volatile Vic",
        "description": "Full-time DoorDash driver, single platform, high variance income",
        
        # Income parameters (from calibration)
        "base_mu": params["mu"],
        "base_sigma": params["sigma"],
        "coefficient_of_variation": params["coefficient_of_variation"],
        
        # Work characteristics
        "platforms": ["doordash"],
        "hours_per_week": 45,
        "metro": "national",
        "experience_months": 6,  # Relatively new
        "skill_level": 0.95,  # Slightly below average
        
        # Evolution parameters
        "skill_growth_rate": 0.02,  # 2% monthly improvement (slow)
        "diversification_probability": 0.15,  # 15% chance of adding platform
        "platform_add_rate": 0.10,  # Low likelihood per month
        "churn_risk": 0.20,  # 20% annual quit probability (high)
        
        # Event risk modifiers (relative to baseline)
        "event_modifiers": {
            "vehicle_repair_probability": 1.2,  # 20% higher risk
            "health_issue_probability": 1.0,  # Average
            "platform_deactivation_probability": 1.3,  # 30% higher (single platform risk)
            "housing_instability_probability": 1.1,  # 10% higher
            "positive_event_probability": 0.8,  # 20% lower (less proactive)
        },
        
        # Financial characteristics
        "emergency_fund_weeks": 2,  # Only 2 weeks of savings
        "debt_to_income_ratio": 0.45,  # High debt burden
        "credit_score_range": (580, 640),  # Fair credit
        
        # Loan considerations
        "default_risk_category": "high",
        "recommended_loan_amount_range": (2000, 5000),
        "recommended_loan_term_months": 12,
    }
    
    return archetype


def create_steady_sarah():
    """
    Steady Sarah: Multi-platform diversified worker, moderate variance, stable.
    
    Profile:
    - Full-time across 3 platforms
    - Well-diversified income
    - Mid-tier market (Atlanta)
    - Experienced and efficient
    - Lower volatility due to diversification
    - Low churn risk
    """
    params = calculate_income_params(
        platforms=["uber", "doordash", "instacart"],
        hours_per_week=40,
        metro="atlanta",
        include_tax=True
    )
    
    archetype = {
        "id": "steady_sarah",
        "name": "Steady Sarah",
        "description": "Multi-platform gig worker, diversified income, stable earnings",
        
        "base_mu": params["mu"],
        "base_sigma": params["sigma"],
        "coefficient_of_variation": params["coefficient_of_variation"],
        
        "platforms": ["uber", "doordash", "instacart"],
        "hours_per_week": 40,
        "metro": "atlanta",
        "experience_months": 24,  # 2 years experience
        "skill_level": 1.10,  # Above average efficiency
        
        "skill_growth_rate": 0.05,  # 5% monthly improvement
        "diversification_probability": 0.30,  # Already diversified, may add more
        "platform_add_rate": 0.05,  # Low (already has 3)
        "churn_risk": 0.10,  # 10% annual quit (low)
        
        "event_modifiers": {
            "vehicle_repair_probability": 1.0,  # Average
            "health_issue_probability": 0.9,  # Slightly better (healthcare access)
            "platform_deactivation_probability": 0.7,  # 30% lower (diversified)
            "housing_instability_probability": 0.8,  # 20% lower (more stable)
            "positive_event_probability": 1.3,  # 30% higher (proactive)
        },
        
        "emergency_fund_weeks": 8,  # 8 weeks of savings (above JPMorgan's 6 week recommendation)
        "debt_to_income_ratio": 0.30,  # Moderate debt
        "credit_score_range": (660, 720),  # Good credit
        
        "default_risk_category": "low",
        "recommended_loan_amount_range": (5000, 10000),
        "recommended_loan_term_months": 24,
    }
    
    return archetype


def create_weekend_warrior():
    """
    Weekend Warrior: Part-time rideshare driver, supplemental income.
    
    Profile:
    - Part-time Uber (15 hrs/week)
    - Has other primary income
    - Dallas market
    - Moderate experience
    - Lower absolute earnings but stable as supplemental income
    """
    params = calculate_income_params(
        platforms=["uber"],
        hours_per_week=15,
        metro="dallas",
        include_tax=True
    )
    
    archetype = {
        "id": "weekend_warrior",
        "name": "Weekend Warrior",
        "description": "Part-time rideshare driver, supplemental income on weekends",
        
        "base_mu": params["mu"],
        "base_sigma": params["sigma"],
        "coefficient_of_variation": params["coefficient_of_variation"],
        
        "platforms": ["uber"],
        "hours_per_week": 15,
        "metro": "dallas",
        "experience_months": 12,  # 1 year
        "skill_level": 1.00,  # Average
        
        "skill_growth_rate": 0.03,  # 3% monthly (moderate)
        "diversification_probability": 0.20,  # May add Lyft
        "platform_add_rate": 0.08,
        "churn_risk": 0.15,  # 15% annual (might stop side gig)
        
        "event_modifiers": {
            "vehicle_repair_probability": 0.8,  # 20% lower (less usage)
            "health_issue_probability": 0.9,  # Slightly lower
            "platform_deactivation_probability": 1.0,  # Average
            "housing_instability_probability": 0.7,  # Much lower (has primary income)
            "positive_event_probability": 1.0,  # Average
        },
        
        "emergency_fund_weeks": 10,  # Better off (has primary job)
        "debt_to_income_ratio": 0.25,  # Low (gig income is extra)
        "credit_score_range": (680, 740),  # Good to very good credit
        
        "default_risk_category": "low",
        "recommended_loan_amount_range": (1000, 3000),  # Smaller loans
        "recommended_loan_term_months": 12,
    }
    
    return archetype


def create_sf_hustler():
    """
    SF Hustler: High-earning worker in expensive market, multi-platform.
    
    Profile:
    - Full-time+ hours (50/week) in San Francisco
    - Uber + DoorDash
    - High gross earnings but high expenses
    - Very experienced and efficient
    - High absolute income but also high costs
    """
    params = calculate_income_params(
        platforms=["uber", "doordash"],
        hours_per_week=50,
        metro="san_francisco",
        include_tax=True
    )
    
    archetype = {
        "id": "sf_hustler",
        "name": "SF Hustler",
        "description": "High-volume multi-platform driver in expensive San Francisco market",
        
        "base_mu": params["mu"],
        "base_sigma": params["sigma"],
        "coefficient_of_variation": params["coefficient_of_variation"],
        
        "platforms": ["uber", "doordash"],
        "hours_per_week": 50,
        "metro": "san_francisco",
        "experience_months": 36,  # 3 years, very experienced
        "skill_level": 1.15,  # Top tier efficiency
        
        "skill_growth_rate": 0.04,  # 4% monthly (still learning)
        "diversification_probability": 0.25,  # May add more
        "platform_add_rate": 0.06,
        "churn_risk": 0.12,  # Low churn (locked in by high COL)
        
        "event_modifiers": {
            "vehicle_repair_probability": 1.3,  # 30% higher (heavy usage)
            "health_issue_probability": 1.1,  # 10% higher (burnout risk)
            "platform_deactivation_probability": 0.8,  # Lower (experienced)
            "housing_instability_probability": 1.4,  # 40% higher (expensive market)
            "positive_event_probability": 1.2,  # Higher (networked, optimized)
        },
        
        "emergency_fund_weeks": 4,  # Only 4 weeks (expenses eat savings)
        "debt_to_income_ratio": 0.40,  # High (cost of living)
        "credit_score_range": (640, 700),  # Fair to good
        
        "default_risk_category": "medium",
        "recommended_loan_amount_range": (5000, 12000),
        "recommended_loan_term_months": 24,
    }
    
    return archetype


def create_rising_ryan():
    """
    Rising Ryan: New gig worker with growth trajectory, building platform portfolio.
    
    Profile:
    - Started 3 months ago with DoorDash
    - Recently added Instacart
    - National market
    - Fast learner, high growth potential
    - Currently below average but improving quickly
    """
    params = calculate_income_params(
        platforms=["doordash", "instacart"],
        hours_per_week=35,
        metro="national",
        include_tax=True
    )
    
    archetype = {
        "id": "rising_ryan",
        "name": "Rising Ryan",
        "description": "New gig worker on growth trajectory, rapidly building skills and platforms",
        
        "base_mu": params["mu"],
        "base_sigma": params["sigma"],
        "coefficient_of_variation": params["coefficient_of_variation"],
        
        "platforms": ["doordash", "instacart"],
        "hours_per_week": 35,
        "metro": "national",
        "experience_months": 3,  # Very new
        "skill_level": 0.90,  # Below average now
        
        "skill_growth_rate": 0.08,  # 8% monthly (fast learner!)
        "diversification_probability": 0.35,  # High likelihood of adding more
        "platform_add_rate": 0.15,  # Very likely to add platforms
        "churn_risk": 0.18,  # 18% (still figuring it out)
        
        "event_modifiers": {
            "vehicle_repair_probability": 1.1,  # Slightly higher (learning curve)
            "health_issue_probability": 0.95,  # Slightly lower (younger)
            "platform_deactivation_probability": 1.2,  # Higher (still learning rules)
            "housing_instability_probability": 1.0,  # Average
            "positive_event_probability": 1.4,  # 40% higher (actively seeking growth)
        },
        
        "emergency_fund_weeks": 3,  # Low (just starting)
        "debt_to_income_ratio": 0.35,  # Moderate
        "credit_score_range": (620, 680),  # Fair to good
        
        "default_risk_category": "medium",
        "recommended_loan_amount_range": (2000, 6000),
        "recommended_loan_term_months": 18,
    }
    
    return archetype


def get_all_archetypes():
    """
    Generate all archetype personas.
    
    Returns:
        List of archetype dictionaries
    """
    return [
        create_volatile_vic(),
        create_steady_sarah(),
        create_weekend_warrior(),
        create_sf_hustler(),
        create_rising_ryan(),
    ]


def get_archetype_by_id(archetype_id):
    """
    Retrieve a specific archetype by ID.
    
    Args:
        archetype_id: Archetype identifier (e.g., 'volatile_vic')
    
    Returns:
        Archetype dictionary
    
    Raises:
        ValueError: If archetype ID not found
    """
    archetypes = get_all_archetypes()
    
    for archetype in archetypes:
        if archetype['id'] == archetype_id:
            return archetype
    
    raise ValueError(f"Unknown archetype ID: {archetype_id}")


def compare_archetypes():
    """
    Generate comparison table of all archetypes.
    
    Returns:
        Dictionary with comparison metrics
    """
    archetypes = get_all_archetypes()
    
    comparison = {
        "count": len(archetypes),
        "archetypes": []
    }
    
    for arch in archetypes:
        comparison["archetypes"].append({
            "id": arch["id"],
            "name": arch["name"],
            "mu": arch["base_mu"],
            "sigma": arch["base_sigma"],
            "cv": arch["coefficient_of_variation"],
            "platforms": len(arch["platforms"]),
            "hours_per_week": arch["hours_per_week"],
            "risk_category": arch["default_risk_category"],
        })
    
    return comparison


if __name__ == "__main__":
    print("="*70)
    print("Gig Worker Archetype Personas")
    print("="*70)
    
    archetypes = get_all_archetypes()
    
    print(f"\n✓ Generated {len(archetypes)} archetype personas\n")
    
    for arch in archetypes:
        print("="*70)
        print(f"{arch['name']} ({arch['id']})")
        print("="*70)
        print(f"Description: {arch['description']}")
        print(f"\nWork Profile:")
        print(f"  Platforms: {', '.join(arch['platforms'])} ({len(arch['platforms'])} total)")
        print(f"  Hours/week: {arch['hours_per_week']}")
        print(f"  Metro: {arch['metro']}")
        print(f"  Experience: {arch['experience_months']} months")
        print(f"  Skill level: {arch['skill_level']:.0%}")
        
        print(f"\nIncome Parameters:")
        print(f"  μ (mean): ${arch['base_mu']:,.2f}/month")
        print(f"  σ (stdev): ${arch['base_sigma']:,.2f}/month")
        print(f"  CV: {arch['coefficient_of_variation']:.1%}")
        
        print(f"\nGrowth & Stability:")
        print(f"  Skill growth rate: {arch['skill_growth_rate']:.1%}/month")
        print(f"  Diversification probability: {arch['diversification_probability']:.0%}")
        print(f"  Churn risk: {arch['churn_risk']:.0%}/year")
        
        print(f"\nFinancial Profile:")
        print(f"  Emergency fund: {arch['emergency_fund_weeks']} weeks")
        print(f"  Debt-to-income: {arch['debt_to_income_ratio']:.0%}")
        print(f"  Credit score: {arch['credit_score_range'][0]}-{arch['credit_score_range'][1]}")
        print(f"  Default risk: {arch['default_risk_category'].upper()}")
        
        print(f"\nLoan Recommendations:")
        print(f"  Amount range: ${arch['recommended_loan_amount_range'][0]:,} - ${arch['recommended_loan_amount_range'][1]:,}")
        print(f"  Term: {arch['recommended_loan_term_months']} months")
        print()
    
    # Comparison table
    print("="*70)
    print("Archetype Comparison Summary")
    print("="*70)
    print(f"{'Name':<20} {'Income (μ)':<12} {'CV':<8} {'Platforms':<10} {'Risk':<10}")
    print("-"*70)
    
    comparison = compare_archetypes()
    for arch in comparison["archetypes"]:
        print(f"{arch['name']:<20} ${arch['mu']:>9,.0f}  {arch['cv']:>6.1%}  {arch['platforms']:>9}  {arch['risk_category']:<10}")
    
    print("\n" + "="*70)
    print("✓ Archetype generation completed")
    print("="*70)

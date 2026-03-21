"""
Build macro shock scenarios calibrated from historical data.

Uses historical recession data from FRED and recession_reference.json
to create realistic shock parameters for the simulation.
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.static_params import MACRO_SHOCKS, get_platform_gig_type


def load_recession_reference():
    """Load historical recession data from cached file."""
    base_path = Path(__file__).parent.parent
    ref_path = base_path / "data" / "historical" / "recession_reference.json"
    
    if ref_path.exists():
        with open(ref_path, 'r') as f:
            return json.load(f)
    
    # Return default if file doesn't exist yet
    return {}


def calibrate_recession_scenario():
    """
    Create recession shock parameters based on historical data.
    
    Returns:
        Dictionary of recession scenarios with impact parameters
    """
    recession_ref = load_recession_reference()
    
    scenarios = {}
    
    # 2008 Financial Crisis scenario
    if "2008_financial_crisis" in recession_ref:
        data = recession_ref["2008_financial_crisis"]
        scenarios["recession_2008"] = {
            "name": "2008 Financial Crisis",
            "trigger_probability": 0.05,  # 5% chance per year
            "duration_months": data["duration_months"],
            "unemployment_delta": data["unemployment_peak"] - data["unemployment_start"],
            "onset_speed": "slow",  # Gradual buildup
            "recovery_speed": "slow",  # Long recovery
            "platform_impacts": data["gig_economy_impact"],
            "expense_changes": {
                "gas_price_multiplier": 1.45,  # +45% spike mid-2008
                "insurance_multiplier": 1.10,  # Insurance costs rise
                "maintenance_multiplier": 1.05,  # Deferred maintenance
            },
            "demand_patterns": {
                "rideshare": 0.70,  # -30% (less discretionary spending)
                "delivery": 0.85,  # -15% (food delivery less adopted)
                "general_gig": 0.75,  # -25% overall
            }
        }
    
    # 2020 COVID Recession scenario
    if "2020_covid_recession" in recession_ref:
        data = recession_ref["2020_covid_recession"]
        scenarios["recession_2020"] = {
            "name": "COVID-19 Recession",
            "trigger_probability": 0.02,  # 2% chance (rare pandemic)
            "duration_months": data["duration_months"],
            "unemployment_delta": data["unemployment_peak"] - data["unemployment_start"],
            "onset_speed": "instant",  # Lockdowns happened immediately
            "recovery_speed": "fast",  # Quick rebound (with stimulus)
            "platform_impacts": data["gig_economy_impact"],
            "expense_changes": {
                "gas_price_multiplier": 0.70,  # -30% (demand collapse)
                "insurance_multiplier": 0.95,  # Slight decrease
                "maintenance_multiplier": 1.00,  # No change
            },
            "demand_patterns": {
                "rideshare": 0.40,  # -60% (lockdowns, no travel)
                "delivery": 1.30,  # +30% (surge in demand)
                "general_gig": 0.90,  # -10% overall
            },
            "special_factors": {
                "stimulus_payments": True,  # Government aid
                "unemployment_bonus": True,  # Enhanced UI benefits
                "eviction_moratorium": True,  # Reduced housing pressure
            }
        }
    
    # 2022 Inflation Slowdown scenario
    if "2022_inflation_slowdown" in recession_ref:
        data = recession_ref["2022_inflation_slowdown"]
        scenarios["inflation_slowdown_2022"] = {
            "name": "2022 Inflation Slowdown",
            "trigger_probability": 0.15,  # 15% chance (more common)
            "duration_months": data["duration_months"],
            "unemployment_delta": data["unemployment_peak"] - data["unemployment_start"],
            "onset_speed": "moderate",  # Gradual inflation buildup
            "recovery_speed": "moderate",  # Moderate adjustment
            "platform_impacts": data["gig_economy_impact"],
            "expense_changes": {
                "gas_price_multiplier": 1.30,  # +30% spike
                "insurance_multiplier": 1.12,  # Insurance up with inflation
                "maintenance_multiplier": 1.15,  # Parts/labor up
            },
            "demand_patterns": {
                "rideshare": 0.95,  # -5% (slight pullback)
                "delivery": 1.05,  # +5% (sustained COVID habits)
                "general_gig": 0.95,  # -5% overall
            },
            "special_factors": {
                "high_interest_rates": True,  # Borrowing more expensive
                "real_wage_decline": True,  # Wages don't keep up with inflation
            }
        }
    
    return scenarios


def calibrate_gas_spike_scenario():
    """
    Create gas price spike scenario.
    
    Returns:
        Dictionary of gas spike parameters
    """
    return {
        "gas_spike_moderate": {
            "name": "Moderate Gas Price Spike",
            "trigger_probability": 0.20,  # 20% chance per year
            "duration_months": 4,
            "gas_price_multiplier": 1.25,  # +25%
            "platform_impacts": {
                "rideshare": 0.92,  # -8% (some quit due to costs)
                "delivery": 0.90,  # -10% (delivery heavily gas-dependent)
                "general_gig": 0.93,  # -7% overall
            },
            "expense_impact": 300,  # Additional $300/month for full-time
        },
        "gas_spike_severe": {
            "name": "Severe Gas Price Spike",
            "trigger_probability": 0.08,  # 8% chance per year
            "duration_months": 6,
            "gas_price_multiplier": 1.50,  # +50%
            "platform_impacts": {
                "rideshare": 0.85,  # -15% (many quit)
                "delivery": 0.80,  # -20% (unsustainable costs)
                "general_gig": 0.85,  # -15% overall
            },
            "expense_impact": 500,  # Additional $500/month for full-time
            "churn_increase": 0.10,  # +10% quit probability
        }
    }


def calibrate_regulatory_shock():
    """
    Create regulatory change scenario (AB5-style gig worker classification).
    
    Returns:
        Dictionary of regulatory shock parameters
    """
    return {
        "ab5_classification": {
            "name": "AB5-Style Worker Reclassification",
            "trigger_probability": 0.05,  # 5% chance per year per state
            "onset_speed": "slow",  # Phase-in period
            "duration_months": "permanent",  # Ongoing structural change
            "scenarios": {
                "contractor_status_maintained": {
                    "probability": 0.70,  # 70% stay contractors
                    "platform_fee_increase": 0.05,  # +5% fees to cover compliance
                    "income_impact": 0.95,  # -5% effective income
                },
                "employee_classification": {
                    "probability": 0.30,  # 30% become employees
                    "income_impact": 0.90,  # -10% (less flexibility)
                    "benefits_gain": True,  # Gain health insurance, paid time off
                    "flexibility_loss": True,  # Lose schedule control
                },
                "platform_exit": {
                    "probability": 0.10,  # 10% platforms exit market
                    "income_impact": 0.50,  # -50% if platform leaves
                    "diversification_required": True,
                }
            }
        },
        "minimum_wage_increase": {
            "name": "Gig Worker Minimum Wage",
            "trigger_probability": 0.10,  # 10% chance per year
            "platform_impacts": {
                "rideshare": 1.05,  # +5% (guaranteed minimum)
                "delivery": 1.08,  # +8% (benefits delivery more)
                "general_gig": 1.05,  # +5% overall
            },
            "volatility_reduction": 0.85,  # -15% volatility (more stable floor)
            "market_contraction": 0.95,  # -5% total opportunities
        }
    }


def calibrate_tech_disruption():
    """
    Create technology disruption scenario (autonomous vehicles, etc.).
    
    Returns:
        Dictionary of tech disruption parameters
    """
    return {
        "autonomous_vehicles_pilot": {
            "name": "Autonomous Vehicle Pilot Programs",
            "trigger_probability": 0.08,  # 8% chance per year
            "duration_months": 12,  # Initial pilot phase
            "platform_impacts": {
                "rideshare": 0.95,  # -5% (limited initial impact)
                "delivery": 0.98,  # -2% (less impact on delivery)
                "general_gig": 0.97,  # -3% overall
            },
            "geographic_concentration": ["san_francisco", "new_york"],  # Only certain cities
            "full_scale_timeline": 60,  # 5+ years to full deployment
        },
        "ai_delivery_optimization": {
            "name": "AI-Powered Route Optimization",
            "trigger_probability": 0.25,  # 25% chance (already happening)
            "impact_type": "positive",
            "platform_impacts": {
                "rideshare": 1.05,  # +5% (better routing)
                "delivery": 1.10,  # +10% (major efficiency gains)
                "general_gig": 1.07,  # +7% overall
            },
            "efficiency_gain": 0.10,  # +10% hourly earnings
            "volatility_reduction": 0.95,  # -5% volatility (more predictable)
        }
    }


def build_all_scenarios():
    """
    Build complete scenario library for the simulation.
    
    Returns:
        Dictionary with all macro shock scenarios
    """
    scenarios = {
        "recession": calibrate_recession_scenario(),
        "gas_spike": calibrate_gas_spike_scenario(),
        "regulatory": calibrate_regulatory_shock(),
        "tech_disruption": calibrate_tech_disruption(),
    }
    
    # Add baseline probabilities from static params
    scenarios["baseline_probabilities"] = MACRO_SHOCKS
    
    return scenarios


def get_scenario_by_name(scenario_type, scenario_name):
    """
    Retrieve a specific scenario by type and name.
    
    Args:
        scenario_type: Category (e.g., 'recession', 'gas_spike')
        scenario_name: Specific scenario (e.g., 'recession_2008')
    
    Returns:
        Scenario parameters dictionary
    """
    all_scenarios = build_all_scenarios()
    
    if scenario_type not in all_scenarios:
        raise ValueError(f"Unknown scenario type: {scenario_type}")
    
    category = all_scenarios[scenario_type]
    
    if scenario_name not in category:
        raise ValueError(f"Unknown scenario: {scenario_name} in {scenario_type}")
    
    return category[scenario_name]


def calculate_shock_impact(base_mu, base_sigma, scenario):
    """
    Calculate adjusted (μ, σ) under a macro shock scenario.
    
    Args:
        base_mu: Baseline mean income
        base_sigma: Baseline standard deviation
        scenario: Scenario dictionary with impact parameters
    
    Returns:
        Tuple of (adjusted_mu, adjusted_sigma, additional_info)
    """
    # Get platform type impact
    if "platform_impacts" in scenario:
        # For simplicity, use 'general_gig' as default
        impact_multiplier = scenario["platform_impacts"].get("general_gig", 0.95)
    elif "demand_patterns" in scenario:
        impact_multiplier = scenario["demand_patterns"].get("general_gig", 0.95)
    else:
        impact_multiplier = 0.95  # Default -5% impact
    
    adjusted_mu = base_mu * impact_multiplier
    
    # Volatility often increases during shocks
    volatility_multiplier = 1.0
    if "volatility_increase" in scenario:
        volatility_multiplier = scenario["volatility_increase"]
    elif impact_multiplier < 0.9:  # Severe shock
        volatility_multiplier = 1.25  # +25% volatility
    elif impact_multiplier < 0.95:  # Moderate shock
        volatility_multiplier = 1.15  # +15% volatility
    
    adjusted_sigma = base_sigma * volatility_multiplier
    
    # Calculate expected loss
    income_loss_pct = (1 - impact_multiplier) * 100
    monthly_loss = base_mu - adjusted_mu
    
    info = {
        "income_loss_percentage": round(income_loss_pct, 1),
        "monthly_income_loss": round(monthly_loss, 2),
        "volatility_change_percentage": round((volatility_multiplier - 1) * 100, 1),
        "adjusted_cv": round(adjusted_sigma / adjusted_mu if adjusted_mu > 0 else 0, 3),
    }
    
    return (round(adjusted_mu, 2), round(adjusted_sigma, 2), info)


if __name__ == "__main__":
    print("="*60)
    print("Macro Shock Scenario Calibration")
    print("="*60)
    
    # Build all scenarios
    print("\n=== Building All Scenarios ===")
    all_scenarios = build_all_scenarios()
    
    print(f"✓ Scenario categories: {len(all_scenarios) - 1}")  # -1 for baseline_probabilities
    for category, scenarios in all_scenarios.items():
        if category != "baseline_probabilities":
            print(f"  {category}: {len(scenarios)} scenario(s)")
            for name, data in scenarios.items():
                print(f"    - {data['name']}")
    
    # Test scenario impact calculation
    print("\n=== Test Scenario Impacts ===")
    base_mu = 2000
    base_sigma = 720
    print(f"Baseline: μ=${base_mu}, σ=${base_sigma}")
    
    test_scenarios = [
        ("recession", "recession_2008"),
        ("recession", "recession_2020"),
        ("gas_spike", "gas_spike_severe"),
        ("regulatory", "minimum_wage_increase"),
    ]
    
    for scenario_type, scenario_name in test_scenarios:
        try:
            scenario = get_scenario_by_name(scenario_type, scenario_name)
            adj_mu, adj_sigma, info = calculate_shock_impact(base_mu, base_sigma, scenario)
            
            print(f"\n{scenario['name']}:")
            print(f"  Adjusted: μ=${adj_mu:,.0f}, σ=${adj_sigma:,.0f}")
            print(f"  Income loss: {info['income_loss_percentage']:.1f}% (${info['monthly_income_loss']:,.0f}/month)")
            print(f"  Volatility change: {info['volatility_change_percentage']:+.1f}%")
            print(f"  New CV: {info['adjusted_cv']:.1%}")
        except ValueError as e:
            print(f"✗ Error: {e}")
    
    # Show recession details
    print("\n=== Recession Scenario Details ===")
    recession_scenarios = all_scenarios["recession"]
    for name, data in recession_scenarios.items():
        print(f"\n{data['name']}:")
        print(f"  Duration: {data['duration_months']} months")
        print(f"  Trigger probability: {data['trigger_probability']:.1%}/year")
        print(f"  Platform impacts:")
        for platform, impact in data["platform_impacts"].items():
            change = (impact - 1.0) * 100
            print(f"    {platform}: {change:+.0f}%")
    
    print("\n" + "="*60)
    print("✓ Scenario calibration completed")
    print("="*60)

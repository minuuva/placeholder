"""
Generate AI Layer Input Data

This script runs the complete VarLend risk assessment pipeline:
- Layer 1: Monte Carlo simulation (5000 paths, 24 months)
- Layer 2: Per-path life event sampling (each path independently samples events)

Each of the 5000 Monte Carlo paths independently samples its own:
- Life events (vehicle repairs, health issues, platform deactivations, housing)
- Macro shocks (recession, gas spike, regulatory changes, tech disruption)

This provides true probabilistic risk distributions.
"""

from run_life_simulation import run_full_life_simulation
from monte_carlo_sim.src.integration.profile_builder import CustomerApplication
from monte_carlo_sim.src.types import LoanConfig

# Configuration
N_PATHS = 5000  # Each path independently samples its own events

# Example customer application
customer = CustomerApplication(
    platforms_and_hours=[
        ('uber', 20.0, 12),      # (platform, hours/week, tenure_months)
        ('doordash', 20.0, 6)
    ],
    metro_area='national',
    months_as_gig_worker=18,
    has_vehicle=True,
    has_dependents=False,
    liquid_savings=2000,
    monthly_fixed_expenses=300,  # Rent + other fixed costs
    existing_debt_obligations=200,
    credit_score_range=(600, 800),
    loan_request_amount=5000,
    requested_term_months=24,
    acceptable_rate_range=(0.08, 0.20)
)

# Requested loan
loan = LoanConfig(amount=5000, term_months=24, annual_rate=0.12)

print("Running full life simulation with per-path event sampling...")
print("Archetype: volatile_vic")
print(f"Monte Carlo paths: {N_PATHS}")
print("Each path independently samples its own life events and macro shocks")
print("Horizon: 24 months\n")

# THIS IS THE KEY FUNCTION - runs entire pipeline with per-path events
result = run_full_life_simulation(
    archetype_id='volatile_vic',
    customer_application=customer,
    loan_config=loan,
    random_seed=None,  # Use None for true randomness
    n_paths=N_PATHS
)

print("="*60)
print("RISK ASSESSMENT RESULTS")
print("="*60)

print("\n--- RISK METRICS ---")
print(f"P(default): {result.p_default:.2%}")
print(f"Expected loss: ${result.expected_loss:.2f}")
print(f"CVaR 95%: ${result.cvar_95:.2f}")
print(f"Risk tier: {result.recommended_loan.risk_tier.value}")
print(f"Approved: {result.recommended_loan.approved}")

print("\n--- LOAN RECOMMENDATION ---")
print(f"Optimal amount: ${result.recommended_loan.optimal_amount:.0f}")
print(f"Optimal term: {result.recommended_loan.optimal_term_months} months")
print(f"Optimal rate: {result.recommended_loan.optimal_rate:.1%}")

print("\n--- REASONING ---")
for reason in result.recommended_loan.reasoning:
    print(f"  • {reason}")

print("\n--- ALTERNATIVE STRUCTURES ---")
for alt in result.recommended_loan.alternative_structures[:3]:
    print(f"  ${alt['amount']:.0f} / {alt['term']}mo / {alt['annual_rate']:.1%} → P(default)={alt['p_default']:.1%}")

print("\n--- TIME-TO-DEFAULT PERCENTILES ---")
for percentile, month in result.time_to_default_percentiles.items():
    print(f"  {percentile}: month {month}")

print("\n--- INCOME RISK ENVELOPE (first 6 months) ---")
print("Month | P10      | Median   | P90")
print("------|----------|----------|----------")
for i in range(6):
    print(f"{i:5d} | ${result.p10_income_by_month[i]:7.0f} | ${result.median_income_by_month[i]:7.0f} | ${result.p90_income_by_month[i]:7.0f}")

print("\n" + "="*60)
print("DATA OBJECT FOR AI LAYER:")
print("="*60)
print("\n'result' object contains:")
print("   - result.p_default (risk metric)")
print("   - result.expected_loss (dollar loss)")
print("   - result.cvar_95 (worst-case loss)")
print("   - result.recommended_loan (approval/decline + optimal structure)")
print("   - result.time_to_default_percentiles (when defaults happen)")
print("   - result.median_income_by_month (24-month trajectory)")
print("   - result.p10_income_by_month (worst 10% income path)")
print("   - result.p90_income_by_month (best 10% income path)")
print("   - result.raw_paths (5000 full Monte Carlo paths)")

print("\nEach of the 5000 paths had independent life events and macro shocks.")
print("="*60)

"""
Generate AI Layer Input Data

This script runs the complete VarLend risk assessment pipeline:
- Layer 1: Monte Carlo simulation (5000 paths, 24 months)
- Layer 2: Life simulation (events, portfolio evolution, macro shocks)

Output: trajectory + result objects needed for AI Layer visualization
"""

from run_life_simulation import run_full_life_simulation
from monte_carlo_sim.src.integration.profile_builder import CustomerApplication
from monte_carlo_sim.src.types import LoanConfig

# Example customer application
customer = CustomerApplication(
    platforms_and_hours=[
        ('uber', 20.0, 12),      # (platform, hours/week, tenure_months)
        ('doordash', 20.0, 6)
    ],
    metro_area='national',
    months_as_gig_worker=12,
    has_vehicle=True,
    has_dependents=False,
    liquid_savings=2000,
    monthly_fixed_expenses=1400,  # Rent + other fixed costs
    existing_debt_obligations=200,
    credit_score_range=(600, 650),
    loan_request_amount=5000,
    requested_term_months=24,
    acceptable_rate_range=(0.08, 0.20)
)

# Requested loan
loan = LoanConfig(amount=5000, term_months=24, annual_rate=0.12)

print("Running full life simulation (Layer 1 + Layer 2)...")
print("Archetype: volatile_vic")
print("Monte Carlo paths: 5000")
print("Horizon: 24 months\n")

# THIS IS THE KEY FUNCTION - runs entire pipeline
trajectory, result = run_full_life_simulation(
    archetype_id='volatile_vic',
    customer_application=customer,
    loan_config=loan,
    random_seed=42,
    n_paths=5000
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

print("\n--- LIFE TRAJECTORY ---")
print(f"Events: {len(trajectory.events)}")
print(f"Macro shock: {trajectory.macro_shock is not None}")
if trajectory.macro_shock:
    print(f"  {trajectory.macro_shock}")
print(f"Portfolio growth: {len(trajectory.portfolio_states[0].active_platforms)} → {len(trajectory.portfolio_states[-1].active_platforms)} platforms")
print(f"Skill growth: {trajectory.portfolio_states[0].skill_multiplier:.2f}x → {trajectory.portfolio_states[-1].skill_multiplier:.2f}x")

print("\n--- NARRATIVE ---")
print(trajectory.narrative)

print("\n--- TIME-TO-DEFAULT PERCENTILES ---")
for percentile, month in result.time_to_default_percentiles.items():
    print(f"  {percentile}: month {month}")

print("\n--- INCOME RISK ENVELOPE (first 6 months) ---")
print("Month | P10      | Median   | P90")
print("------|----------|----------|----------")
for i in range(6):
    print(f"{i:5d} | ${result.p10_income_by_month[i]:7.0f} | ${result.median_income_by_month[i]:7.0f} | ${result.p90_income_by_month[i]:7.0f}")

print("\n" + "="*60)
print("DATA OBJECTS FOR AI LAYER:")
print("="*60)
print("\n1. 'trajectory' object contains:")
print("   - trajectory.events (life events list)")
print("   - trajectory.portfolio_states (month-by-month)")
print("   - trajectory.macro_shock (macro context)")
print("   - trajectory.narrative (human-readable story)")

print("\n2. 'result' object contains:")
print("   - result.p_default (risk metric)")
print("   - result.expected_loss (dollar loss)")
print("   - result.cvar_95 (worst-case loss)")
print("   - result.recommended_loan (approval/decline + optimal structure)")
print("   - result.time_to_default_percentiles (when defaults happen)")
print("   - result.median_income_by_month (24-month trajectory)")
print("   - result.p10_income_by_month (worst 10% income path)")
print("   - result.p90_income_by_month (best 10% income path)")
print("   - result.raw_paths (5000 full Monte Carlo paths)")

print("\nAI Layer should use BOTH objects to generate visual risk profile.")
print("="*60)

"""
Aggregate Results - Combine multiple SimulationResult objects into one unified result.

Used to merge results from multiple independent life trajectories to achieve
realistic probabilistic risk distributions.
"""

import numpy as np
import sys
import os

# Add paths for imports
parent_dir = os.path.join(os.path.dirname(__file__), '..')
monte_carlo_dir = os.path.join(parent_dir, 'monte_carlo_sim')

sys.path.insert(0, parent_dir)
sys.path.insert(0, monte_carlo_dir)

from src.types import SimulationResult, LoanConfig, WorkerProfile, LoadResult
from src.risk.risk_metrics import (
    p_default as calc_p_default,
    expected_loss as calc_expected_loss,
    cvar,
    time_to_default_dist,
    income_envelope
)
from src.risk.loan_evaluator import evaluate_loan
from src.engine.defaults import detect_defaults_and_losses
from src.engine.parameter_state import effective_parameters


def _calculate_expenses_by_month(
    load: LoadResult,
    shifts: list,
    horizon_months: int
) -> np.ndarray:
    """Calculate expense parameters for each month."""
    mu_base0 = load.effective_mu_base
    sigma_base0 = load.effective_sigma_base
    lambda_base0 = 0.2  # Default lambda
    obligations0 = load.total_monthly_obligations
    
    expenses = np.array(
        [effective_parameters(t, mu_base0, sigma_base0, lambda_base0, obligations0, shifts)[3] 
         for t in range(horizon_months)],
        dtype=np.float64
    )
    return expenses


def aggregate_simulation_results(
    results: list[SimulationResult],
    loan_config: LoanConfig,
    profile: WorkerProfile,
    load: LoadResult,
    scenario=None
) -> SimulationResult:
    """
    Combine multiple SimulationResult objects into one unified result.
    
    This function aggregates results from multiple independent life trajectories,
    each run with M Monte Carlo paths, to produce a single SimulationResult with
    N*M total paths that reflects realistic probabilistic event distributions.
    
    The key insight: we combine raw income paths from all results and re-run
    default detection to get accurate aggregate default probabilities.
    
    Args:
        results: List of SimulationResult objects to aggregate
        loan_config: Loan configuration (for recommendation generation)
        profile: Worker profile (for liquid_savings and expenses)
        load: LoadResult with base parameters
        scenario: AIScenario (optional, for expense calculation)
    
    Returns:
        Unified SimulationResult with aggregated metrics
    
    Example:
        # 100 trajectories × 50 paths each = 5000 total paths
        results = []
        for i in range(100):
            result = run_simulation(..., n_paths=50)
            results.append(result)
        
        aggregated = aggregate_simulation_results(results, loan_config, profile, load)
        # aggregated.p_default now reflects realistic distribution
    """
    if not results:
        raise ValueError("Cannot aggregate empty results list")
    
    if len(results) == 1:
        # If only one result, return it as-is
        return results[0]
    
    # 1. Combine raw_paths (income matrices) from all results
    # raw_paths shape: (n_paths, horizon_months)
    all_income_paths = np.vstack([r.raw_paths for r in results])
    horizon = all_income_paths.shape[1]
    
    # 2. Recalculate defaults and losses on combined income matrix
    # We need to re-run default detection with the same parameters used in Monte Carlo
    
    # Calculate expense array for each month
    shifts = scenario.parameter_shifts if scenario else []
    expenses_by_month = _calculate_expenses_by_month(load, shifts, horizon)
    
    # Calculate monthly payment
    monthly_payment = loan_config.amount * (loan_config.annual_rate / 12.0) / \
                     (1.0 - (1.0 + loan_config.annual_rate / 12.0) ** (-loan_config.term_months)) \
                     if loan_config.term_months > 0 else 0.0
    
    # Re-detect defaults on combined income matrix
    combined_defaulted, combined_default_months, combined_losses = detect_defaults_and_losses(
        all_income_paths,
        expenses_by_month,
        monthly_payment,
        profile.liquid_savings,
        loan_config.amount,
        loan_config.annual_rate,
        loan_config.term_months
    )
    
    # 3. Recalculate aggregate metrics
    aggregated_p_default = calc_p_default(combined_defaulted)
    aggregated_expected_loss = calc_expected_loss(combined_losses)
    aggregated_cvar_95 = cvar(combined_losses, alpha=0.95)
    
    # 4. Recalculate income envelopes (percentiles by month)
    income_percentiles = income_envelope(all_income_paths, [10, 50, 90])
    p10_income = income_percentiles[0, :]
    median_income = income_percentiles[1, :]
    p90_income = income_percentiles[2, :]
    
    # 5. Recalculate time-to-default percentiles
    aggregated_ttd = time_to_default_dist(combined_default_months)
    
    # 6. Generate new loan recommendation based on aggregated risk
    aggregated_result_temp = SimulationResult(
        p_default=aggregated_p_default,
        expected_loss=aggregated_expected_loss,
        cvar_95=aggregated_cvar_95,
        median_income_by_month=median_income,
        p10_income_by_month=p10_income,
        p90_income_by_month=p90_income,
        time_to_default_percentiles=aggregated_ttd,
        recommended_loan=results[0].recommended_loan,  # Placeholder
        raw_paths=all_income_paths
    )
    
    # Generate proper loan recommendation
    loan_recommendation = evaluate_loan(aggregated_result_temp, loan_config)
    
    # 7. Return final aggregated result
    return SimulationResult(
        p_default=aggregated_p_default,
        expected_loss=aggregated_expected_loss,
        cvar_95=aggregated_cvar_95,
        median_income_by_month=median_income,
        p10_income_by_month=p10_income,
        p90_income_by_month=p90_income,
        time_to_default_percentiles=aggregated_ttd,
        recommended_loan=loan_recommendation,
        raw_paths=all_income_paths
    )


def get_trajectory_diversity_stats(results: list[SimulationResult]) -> dict:
    """
    Calculate statistics about trajectory diversity (for debugging/validation).
    
    Args:
        results: List of SimulationResult objects
    
    Returns:
        Dictionary with diversity metrics
    """
    if not results:
        return {}
    
    p_defaults = [r.p_default for r in results]
    expected_losses = [r.expected_loss for r in results]
    
    return {
        "n_trajectories": len(results),
        "p_default_mean": float(np.mean(p_defaults)),
        "p_default_std": float(np.std(p_defaults)),
        "p_default_min": float(np.min(p_defaults)),
        "p_default_max": float(np.max(p_defaults)),
        "expected_loss_mean": float(np.mean(expected_losses)),
        "expected_loss_std": float(np.std(expected_losses)),
    }

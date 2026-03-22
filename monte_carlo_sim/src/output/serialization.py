"""
JSON Serialization for SimulationResult objects.

Converts Monte Carlo simulation results to JSON-serializable dictionaries
for consumption by AI layer and frontend applications.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional
import numpy as np

from ..types import SimulationResult, LoanRecommendation, RiskTier


def result_to_dict(result: SimulationResult, include_raw_paths: bool = False, n_sample_paths: int = 15) -> dict:
    """
    Convert SimulationResult to JSON-serializable dictionary with granular distributions.
    
    Args:
        result: The simulation result object to convert
        include_raw_paths: If True, include the full 5000×horizon raw paths matrix
                          (warning: can be ~1-2MB). Default False.
        n_sample_paths: Number of individual paths to sample for trajectory visualization (default 15)
    
    Returns:
        Dictionary with all simulation results, ready for JSON serialization
    """
    # Determine dimensions
    horizon_months = len(result.median_income_by_month)
    n_paths = result.raw_paths.shape[0] if result.raw_paths.ndim > 1 else 1
    n_defaults = int(np.sum(result.defaulted))
    
    # Compute additional risk metrics
    cvar_99 = float(np.mean(result.losses[result.losses >= np.percentile(result.losses, 99)])) if len(result.losses[result.losses > 0]) > 0 else 0.0
    
    # 1. Default Distribution - timing histogram and survival curve
    default_months_only = result.default_month[result.defaulted]
    if len(default_months_only) > 0:
        hist_counts, hist_bins = np.histogram(default_months_only, bins=np.arange(0, horizon_months + 1))
        timing_histogram = {
            "bins": hist_bins[:-1].tolist(),  # Exclude last edge
            "counts": hist_counts.tolist()
        }
    else:
        timing_histogram = {
            "bins": [],
            "counts": []
        }
    
    # Survival curve: fraction of paths NOT defaulted by each month
    survival_curve = []
    for t in range(horizon_months):
        n_survived = np.sum((result.default_month < 0) | (result.default_month > t))
        survival_curve.append(float(n_survived / n_paths))
    
    # 2. Income Distribution - extended percentiles
    income_percentiles = {}
    for p_name, p_val in [("p5", 5), ("p10", 10), ("p25", 25), ("p50", 50), ("p75", 75), ("p90", 90), ("p95", 95)]:
        income_percentiles[p_name] = np.percentile(result.raw_paths, p_val, axis=0).tolist()
    
    # 3. Loss Distribution - percentiles and histogram
    loss_percentiles = {}
    for p_name, p_val in [("p50", 50), ("p75", 75), ("p90", 90), ("p95", 95), ("p99", 99)]:
        loss_percentiles[p_name] = float(np.percentile(result.losses, p_val))
    
    # Loss histogram with reasonable bins
    if len(result.losses[result.losses > 0]) > 0:
        max_loss = float(np.max(result.losses))
        # Create bins ensuring monotonicity
        loss_bins = [0, 100, 500, 1000, 2000, max(5000, max_loss + 1)]
        loss_hist_counts, _ = np.histogram(result.losses, bins=loss_bins)
        loss_histogram = {
            "bins": loss_bins[:-1],
            "counts": loss_hist_counts.tolist()
        }
    else:
        loss_histogram = {
            "bins": [0],
            "counts": [int(n_paths)]
        }
    
    # 4. Cash Flow Trajectories
    cash_flow_percentiles = {}
    for p_name, p_val in [("p10", 10), ("p50", 50), ("p90", 90)]:
        cash_flow_percentiles[f"{p_name}_by_month"] = np.percentile(result.monthly_net_cash_flows, p_val, axis=0).tolist()
    
    # Buffer trajectories
    buffer_percentiles = {}
    for p_name, p_val in [("p10", 10), ("p50", 50), ("p90", 90)]:
        buffer_percentiles[f"{p_name}_by_month"] = np.percentile(result.monthly_buffer, p_val, axis=0).tolist()
    
    # Expense trajectories
    expense_percentiles = {}
    for p_name, p_val in [("p10", 10), ("p50", 50), ("p90", 90)]:
        expense_percentiles[f"{p_name}_by_month"] = np.percentile(result.monthly_expenses, p_val, axis=0).tolist()
    
    # 5. Sample Paths - select random paths for detailed trajectory plots
    sample_indices = np.random.choice(n_paths, size=min(n_sample_paths, n_paths), replace=False)
    sample_paths = []
    for idx in sample_indices:
        sample_paths.append({
            "path_id": int(idx),
            "income_by_month": result.raw_paths[idx].tolist(),
            "expenses_by_month": result.monthly_expenses[idx].tolist(),
            "cash_flow_by_month": result.monthly_net_cash_flows[idx].tolist(),
            "buffer_by_month": result.monthly_buffer[idx].tolist(),
            "defaulted": bool(result.defaulted[idx]),
            "default_month": int(result.default_month[idx]) if result.defaulted[idx] else None
        })
    
    # Build the output dictionary
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "2.0",  # Updated version for granular data
            "n_paths": int(n_paths),
            "horizon_months": int(horizon_months),
            "includes_raw_paths": include_raw_paths,
            "n_sample_paths": len(sample_paths)
        },
        
        "risk_metrics": {
            "p_default": float(result.p_default),
            "n_defaults": n_defaults,
            "expected_loss": float(result.expected_loss),
            "cvar_95": float(result.cvar_95),
            "cvar_99": cvar_99
        },
        
        "default_distribution": {
            "timing_histogram": timing_histogram,
            "survival_curve": survival_curve
        },
        
        "income_distribution": {
            "percentiles_by_month": income_percentiles
        },
        
        "expense_distribution": {
            "percentiles_by_month": expense_percentiles
        },
        
        "loss_distribution": {
            "percentiles": loss_percentiles,
            "histogram": loss_histogram
        },
        
        "cash_flow_trajectories": cash_flow_percentiles,
        
        "buffer_trajectories": buffer_percentiles,
        
        "time_to_default": {
            "percentiles": result.time_to_default_percentiles
        },
        
        "sample_paths": sample_paths,
        
        "loan_recommendation": {
            "optimal_amount": float(result.recommended_loan.optimal_amount),
            "optimal_term_months": int(result.recommended_loan.optimal_term_months),
            "optimal_rate": float(result.recommended_loan.optimal_rate),
            "risk_tier": result.recommended_loan.risk_tier.value,
            "reasoning": result.recommended_loan.reasoning,
            "alternative_structures": result.recommended_loan.alternative_structures
        }
    }
    
    # Optionally include raw paths (can be large)
    if include_raw_paths:
        output["raw_paths"] = result.raw_paths.tolist()
    
    return output


def save_result_to_json(
    result: SimulationResult,
    output_path: Path,
    include_raw_paths: bool = False,
    indent: int = 2
) -> Path:
    """
    Convert SimulationResult to dict and save as JSON file.
    
    Args:
        result: The simulation result to save
        output_path: Path where JSON file should be saved
        include_raw_paths: If True, include the full raw paths matrix
        indent: JSON indentation level (default 2 for human readability)
    
    Returns:
        Path to the saved file
    """
    # Ensure parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to dict
    data = result_to_dict(result, include_raw_paths=include_raw_paths)
    
    # Write to file
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=indent)
    
    return output_path

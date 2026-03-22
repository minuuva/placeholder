"""
Output utilities for Monte Carlo simulation results.

Provides directory management and serialization for simulation outputs.
"""

from pathlib import Path


def get_simulation_results_dir() -> Path:
    """
    Get (or create) the directory for simulation result JSON files.
    
    Returns:
        Path to data_pipeline/output/simulation_results/
    """
    # Navigate from monte_carlo_sim/src/output/ to project root
    project_root = Path(__file__).parent.parent.parent.parent
    
    # Create output directory path
    results_dir = project_root / "data_pipeline" / "output" / "simulation_results"
    
    # Ensure directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return results_dir


# Export key functions
from .serialization import result_to_dict, save_result_to_json

__all__ = [
    'get_simulation_results_dir',
    'result_to_dict',
    'save_result_to_json'
]

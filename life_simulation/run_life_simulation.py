"""
Run Life Simulation - Integration entry point for Layer 1 + Layer 2.

Connects life trajectory generation with Monte Carlo execution.
"""

from typing import Optional
import sys
import os

# Add parent directory and monte_carlo_sim to path
parent_dir = os.path.join(os.path.dirname(__file__), '..')
monte_carlo_dir = os.path.join(parent_dir, 'monte_carlo_sim')

sys.path.insert(0, parent_dir)
sys.path.insert(0, monte_carlo_dir)

from life_simulation.types import LifeTrajectory
from life_simulation.trajectory_builder import build_life_trajectory
from life_simulation.aggregate_results import aggregate_simulation_results
from data_pipeline.loaders import DataLoader

# Import Monte Carlo components
from src.types import (
    SimulationConfig,
    LoanConfig,
    SimulationResult,
    WorkerProfile,
    GigType,
    CorrelationMode
)
from src.integration.profile_builder import (
    build_profile_from_application,
    CustomerApplication
)
from src.engine.monte_carlo import run_simulation, load_and_prepare


def run_full_life_simulation(
    archetype_id: str,
    customer_application: CustomerApplication,
    loan_config: LoanConfig,
    random_seed: Optional[int] = None,
    narrative_mode: bool = False,
    n_paths: int = 5000,
    horizon_months: int = 24,
    n_trajectories: int = 100
) -> tuple[LifeTrajectory, SimulationResult]:
    """
    Complete Layer 1 + Layer 2 integration with probabilistic event sampling.
    
    Process:
    1. Generate N independent life trajectories (each with different events/shocks)
    2. Run Monte Carlo simulation for each trajectory with M paths
    3. Aggregate all N×M results to get realistic risk distribution
    4. Return representative trajectory + aggregated results
    
    Key insight: n_trajectories=100 × paths_per_trajectory=50 = 5000 total paths,
    but now with event diversity across trajectories.
    
    Args:
        archetype_id: Archetype ID from archetypes.json
        customer_application: Customer data
        loan_config: Loan parameters
        random_seed: Optional seed for reproducibility
        narrative_mode: If True, uses deterministic events
        n_paths: Total number of Monte Carlo paths (default 5000)
        horizon_months: Simulation horizon (default 24)
        n_trajectories: Number of independent life trajectories to generate (default 100)
            - Set to 1 for deterministic behavior (all paths use same trajectory)
            - Set to 100+ for realistic probabilistic risk distributions
    
    Returns:
        (LifeTrajectory, SimulationResult)
        - Trajectory: Representative sample life story (first trajectory)
        - Result: Aggregated risk metrics across all trajectories
    """
    # Build worker profile once (doesn't change across trajectories)
    loader = DataLoader()
    profile = build_profile_from_application(customer_application, loader)
    load = load_and_prepare(profile, SimulationConfig(
        n_paths=1,  # Dummy config just to get load params
        horizon_months=horizon_months,
        random_seed=random_seed
    ))
    
    # Handle single trajectory case (legacy behavior)
    if n_trajectories == 1:
        trajectory = build_life_trajectory(
            archetype_id,
            n_months=horizon_months,
            random_seed=random_seed,
            narrative_mode=narrative_mode
        )
        
        config = SimulationConfig(
            n_paths=n_paths,
            horizon_months=horizon_months,
            random_seed=random_seed,
            correlation_mode=CorrelationMode.CORRELATED
        )
        
        result = run_simulation(profile, config, loan_config, load, trajectory.ai_scenario)
        return trajectory, result
    
    # Generate multiple trajectories and aggregate
    paths_per_trajectory = max(1, n_paths // n_trajectories)
    trajectories = []
    results = []
    
    for i in range(n_trajectories):
        # Generate unique seed for this trajectory
        traj_seed = (random_seed + i) if random_seed is not None else None
        
        # Generate life trajectory with unique events/shocks
        trajectory = build_life_trajectory(
            archetype_id,
            n_months=horizon_months,
            random_seed=traj_seed,
            narrative_mode=narrative_mode
        )
        trajectories.append(trajectory)
        
        # Run Monte Carlo with this trajectory's scenario
        config = SimulationConfig(
            n_paths=paths_per_trajectory,
            horizon_months=horizon_months,
            random_seed=traj_seed,
            correlation_mode=CorrelationMode.CORRELATED
        )
        
        result = run_simulation(profile, config, loan_config, load, trajectory.ai_scenario)
        results.append(result)
    
    # Aggregate all results into unified risk metrics
    # Use first trajectory's scenario for expense calculation (approximation)
    aggregated_result = aggregate_simulation_results(
        results, 
        loan_config, 
        profile, 
        load,
        trajectories[0].ai_scenario
    )
    
    # Return first trajectory as representative sample for visualization
    return trajectories[0], aggregated_result


def run_static_simulation(
    customer_application: CustomerApplication,
    loan_config: LoanConfig,
    random_seed: Optional[int] = None,
    n_paths: int = 5000,
    horizon_months: int = 24
) -> SimulationResult:
    """
    Run Monte Carlo simulation WITHOUT life simulation (Layer 1 only).
    
    This is the baseline static simulation for comparison.
    
    Args:
        customer_application: Customer data
        loan_config: Loan parameters
        random_seed: Optional seed
        n_paths: Number of paths
        horizon_months: Simulation horizon
    
    Returns:
        SimulationResult with static risk metrics
    """
    loader = DataLoader()
    profile = build_profile_from_application(customer_application, loader)
    
    config = SimulationConfig(
        n_paths=n_paths,
        horizon_months=horizon_months,
        random_seed=random_seed,
        correlation_mode=CorrelationMode.CORRELATED
    )
    
    load = load_and_prepare(profile, config)
    
    result = run_simulation(profile, config, loan_config, load, scenario=None)
    
    return result


def compare_static_vs_dynamic(
    archetype_id: str,
    customer_application: CustomerApplication,
    loan_config: LoanConfig,
    random_seed: Optional[int] = None,
    n_trajectories: int = 100
) -> dict:
    """
    Compare static (Layer 1 only) vs dynamic (Layer 1 + Layer 2) simulations.
    
    Args:
        archetype_id: Archetype ID
        customer_application: Customer data
        loan_config: Loan parameters
        random_seed: Optional seed
        n_trajectories: Number of trajectories for dynamic simulation (default 100)
    
    Returns:
        Dictionary with comparison metrics
    """
    static_result = run_static_simulation(
        customer_application,
        loan_config,
        random_seed=random_seed
    )
    
    trajectory, dynamic_result = run_full_life_simulation(
        archetype_id,
        customer_application,
        loan_config,
        random_seed=random_seed,
        n_trajectories=n_trajectories
    )
    
    comparison = {
        "static": {
            "p_default": static_result.p_default,
            "expected_loss": static_result.expected_loss,
            "cvar_95": static_result.cvar_95,
            "risk_tier": static_result.recommended_loan.risk_tier.value,
            "approved": static_result.recommended_loan.approved
        },
        "dynamic": {
            "p_default": dynamic_result.p_default,
            "expected_loss": dynamic_result.expected_loss,
            "cvar_95": dynamic_result.cvar_95,
            "risk_tier": dynamic_result.recommended_loan.risk_tier.value,
            "approved": dynamic_result.recommended_loan.approved
        },
        "trajectory": {
            "events": len(trajectory.events),
            "macro_shock": trajectory.macro_shock is not None,
            "final_platforms": len(trajectory.portfolio_states[-1].active_platforms),
            "skill_growth": trajectory.portfolio_states[-1].skill_multiplier - trajectory.portfolio_states[0].skill_multiplier,
            "narrative": trajectory.ai_scenario.narrative
        },
        "delta": {
            "p_default_change": dynamic_result.p_default - static_result.p_default,
            "expected_loss_change": dynamic_result.expected_loss - static_result.expected_loss,
            "risk_tier_changed": static_result.recommended_loan.risk_tier != dynamic_result.recommended_loan.risk_tier,
            "approval_changed": static_result.recommended_loan.approved != dynamic_result.recommended_loan.approved
        }
    }
    
    return comparison

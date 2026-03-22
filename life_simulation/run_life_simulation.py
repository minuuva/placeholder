"""
Run Life Simulation - Integration entry point for Layer 1 + Layer 2.

Connects life trajectory generation with Monte Carlo execution.
"""

from typing import Optional
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from life_simulation.types import LifeTrajectory
from life_simulation.trajectory_builder import build_life_trajectory
from data_pipeline.loaders import DataLoader

# Import Monte Carlo components
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'monte_carlo_sim'))
from monte_carlo_sim.src.types import (
    SimulationConfig,
    LoanConfig,
    SimulationResult,
    WorkerProfile,
    GigType,
    CorrelationMode
)
from monte_carlo_sim.src.integration.profile_builder import (
    build_profile_from_application,
    CustomerApplication
)
from monte_carlo_sim.src.engine.monte_carlo import run_simulation, load_and_prepare


def run_full_life_simulation(
    archetype_id: str,
    customer_application: CustomerApplication,
    loan_config: LoanConfig,
    random_seed: Optional[int] = None,
    narrative_mode: bool = False,
    n_paths: int = 5000,
    horizon_months: int = 24
) -> tuple[LifeTrajectory, SimulationResult]:
    """
    Complete Layer 1 + Layer 2 integration.
    
    Process:
    1. Build life trajectory (24 months of events, portfolio evolution, macro shocks)
    2. Extract AIScenario from trajectory
    3. Build WorkerProfile from customer application
    4. Run Monte Carlo with AIScenario
    5. Return both trajectory (for visualization) and results (for loan decision)
    
    Args:
        archetype_id: Archetype ID from archetypes.json
        customer_application: Customer data
        loan_config: Loan parameters
        random_seed: Optional seed for reproducibility
        narrative_mode: If True, uses deterministic events
        n_paths: Number of Monte Carlo paths (default 5000)
        horizon_months: Simulation horizon (default 24)
    
    Returns:
        (LifeTrajectory, SimulationResult)
        - Trajectory shows what happened month-by-month
        - Result shows final risk metrics and loan recommendation
    """
    trajectory = build_life_trajectory(
        archetype_id,
        n_months=horizon_months,
        random_seed=random_seed,
        narrative_mode=narrative_mode
    )
    
    ai_scenario = trajectory.ai_scenario
    
    loader = DataLoader()
    profile = build_profile_from_application(customer_application, loader)
    
    config = SimulationConfig(
        n_paths=n_paths,
        horizon_months=horizon_months,
        random_seed=random_seed,
        correlation_mode=CorrelationMode.CORRELATED
    )
    
    load = load_and_prepare(profile, config)
    
    result = run_simulation(profile, config, loan_config, load, ai_scenario)
    
    return trajectory, result


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
    random_seed: Optional[int] = None
) -> dict:
    """
    Compare static (Layer 1 only) vs dynamic (Layer 1 + Layer 2) simulations.
    
    Args:
        archetype_id: Archetype ID
        customer_application: Customer data
        loan_config: Loan parameters
        random_seed: Optional seed
    
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
        random_seed=random_seed
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

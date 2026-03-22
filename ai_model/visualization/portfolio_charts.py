"""
Portfolio Evolution Charts - Visualizes skill growth and platform diversification.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional


def plot_portfolio_evolution(
    trajectory,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Plot portfolio evolution over time (platforms and skill).
    
    Args:
        trajectory: LifeTrajectory object
        output_path: Where to save chart
        title: Custom title
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"portfolio_evolution_{trajectory.archetype_id}.png"
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    if title is None:
        title = f"{trajectory.archetype_id} - Portfolio Evolution"
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    months = [state.month for state in trajectory.portfolio_states]
    platform_counts = [len(state.active_platforms) for state in trajectory.portfolio_states]
    skill_multipliers = [state.skill_multiplier for state in trajectory.portfolio_states]
    
    ax1.plot(months, platform_counts, marker='o', linewidth=2.5,
            markersize=6, color='steelblue', label='Active Platforms')
    ax1.fill_between(months, 0, platform_counts, alpha=0.3, color='steelblue')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Number of Platforms', fontsize=12)
    ax1.set_title('Platform Diversification Over Time', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim(bottom=0)
    
    for i, (month, count) in enumerate(zip(months, platform_counts)):
        if i > 0 and count != platform_counts[i-1]:
            ax1.annotate(f'{count}', xy=(month, count), xytext=(5, 5),
                        textcoords='offset points', fontweight='bold')
    
    ax2.plot(months, skill_multipliers, marker='s', linewidth=2.5,
            markersize=6, color='green', label='Skill Multiplier')
    ax2.fill_between(months, 1.0, skill_multipliers, alpha=0.3, color='green')
    ax2.axhline(y=1.0, color='black', linestyle='--', linewidth=1,
               label='Baseline (1.0x)', alpha=0.5)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Skill Multiplier', fontsize=12)
    ax2.set_title('Skill Growth Over Time', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    initial_skill = skill_multipliers[0]
    final_skill = skill_multipliers[-1]
    growth_pct = ((final_skill - initial_skill) / initial_skill) * 100
    
    ax2.text(0.98, 0.02, f'Growth: +{growth_pct:.1f}%',
            transform=ax2.transAxes, fontsize=12, fontweight='bold',
            ha='right', va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_income_evolution(
    trajectory,
    run_id: str = None,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Plot income parameter evolution (mu and sigma) over time.
    
    Args:
        trajectory: LifeTrajectory object
        run_id: Unique identifier for this simulation run
        output_path: Where to save chart
        title: Custom title
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        if run_id:
            output_path = Config.CHART_DIR / f"income_evolution_{trajectory.archetype_id}_{run_id}.png"
        else:
            output_path = Config.CHART_DIR / f"income_evolution_{trajectory.archetype_id}.png"
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 12))
    
    if title is None:
        title = f"{trajectory.archetype_id} - Income Parameter Evolution"
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    months = [state.month for state in trajectory.portfolio_states]
    base_incomes = [state.monthly_base_income for state in trajectory.portfolio_states]
    base_sigmas = [state.monthly_base_sigma for state in trajectory.portfolio_states]
    
    ax1.plot(months, base_incomes, linewidth=2.5, color='darkgreen', label='Mean Income (μ)')
    ax1.fill_between(months, 0, base_incomes, alpha=0.3, color='green')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Mean Monthly Income ($)', fontsize=12)
    ax1.set_title('Income Mean Evolution', fontsize=13, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(months, base_sigmas, linewidth=2.5, color='darkred', label='Income Volatility (σ)')
    ax2.fill_between(months, 0, base_sigmas, alpha=0.3, color='red')
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Income Std Dev ($)', fontsize=12)
    ax2.set_title('Income Volatility Evolution', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    cvs = [sigma / mu if mu > 0 else 0 
           for mu, sigma in zip(base_incomes, base_sigmas)]
    
    ax3.plot(months, cvs, linewidth=2.5, color='purple', label='Coefficient of Variation')
    ax3.axhline(y=0.30, color='orange', linestyle='--', linewidth=1.5,
               label='Moderate Risk Threshold', alpha=0.7)
    ax3.axhline(y=0.40, color='red', linestyle='--', linewidth=1.5,
               label='High Risk Threshold', alpha=0.7)
    ax3.set_xlabel('Month', fontsize=12)
    ax3.set_ylabel('Coefficient of Variation', fontsize=12)
    ax3.set_title('Income Stability (CV) Over Time', fontsize=13, fontweight='bold')
    ax3.legend(fontsize=11)
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

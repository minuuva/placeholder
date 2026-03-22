"""
Comparison Plots - Side-by-side visualization of two scenarios.

Compares risk profiles, income trajectories, and outcomes.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional


def plot_comparison(
    output_a,
    output_b,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Create comprehensive side-by-side comparison.
    
    Args:
        output_a: First SimulationOutput
        output_b: Second SimulationOutput
        output_path: Where to save chart
        title: Custom title
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / "comparison.png"
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    if title is None:
        title = f"Comparison: {output_a.archetype_used['name']} vs {output_b.archetype_used['name']}"
    fig.suptitle(title, fontsize=18, fontweight='bold')
    
    for col, (output, name) in enumerate([
        (output_a, output_a.archetype_used['name']),
        (output_b, output_b.archetype_used['name'])
    ]):
        result = output.result
        trajectory = output.trajectory
        archetype = output.archetype_used
        
        ax = axes[0, col]
        n_paths_to_show = min(100, result.raw_paths.shape[0])
        for i in range(n_paths_to_show):
            ax.plot(result.raw_paths[i, :], alpha=0.1,
                   color='blue' if col == 0 else 'green', linewidth=0.5)
        ax.plot(result.median_income_by_month, 'r-', linewidth=2.5, label='Median')
        ax.plot(result.p10_income_by_month, 'orange', linewidth=2,
               linestyle='--', label='P10')
        # Use actual mean from simulation (accounting for life events)
        actual_mean = float(np.mean(result.raw_paths[:, 0]))
        ax.axhline(y=actual_mean, color='black', linestyle=':',
                  linewidth=1.5, label='Base μ', alpha=0.7)
        ax.set_title(f'{name}\nIncome Paths', fontsize=12, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Income ($)')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3)
        
        ax = axes[1, col]
        months = [state.month for state in trajectory.portfolio_states]
        platform_counts = [len(state.active_platforms) for state in trajectory.portfolio_states]
        skill_multipliers = [state.skill_multiplier for state in trajectory.portfolio_states]
        
        ax_twin = ax.twinx()
        
        line1 = ax.plot(months, platform_counts, marker='o', linewidth=2.5,
                       color='steelblue', label='Platforms')
        ax.set_ylabel('Platform Count', fontsize=11, color='steelblue')
        ax.tick_params(axis='y', labelcolor='steelblue')
        
        line2 = ax_twin.plot(months, skill_multipliers, marker='s', linewidth=2.5,
                            color='green', label='Skill Multiplier')
        ax_twin.set_ylabel('Skill Multiplier', fontsize=11, color='green')
        ax_twin.tick_params(axis='y', labelcolor='green')
        
        ax.set_xlabel('Month')
        ax.set_title(f'{name}\nPortfolio Evolution', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        lines = line1 + line2
        labels = [l.get_label() for l in lines]
        ax.legend(lines, labels, loc='upper left', fontsize=9)
    
    ax = axes[0, 2]
    
    metrics_a = [
        result.p_default * 100 for result in [output_a.result]
    ][0]
    metrics_b = [
        result.p_default * 100 for result in [output_b.result]
    ][0]
    
    x = np.arange(3)
    width = 0.35
    
    values_a = [
        output_a.result.p_default * 100,
        output_a.result.expected_loss,
        output_a.result.cvar_95
    ]
    values_b = [
        output_b.result.p_default * 100,
        output_b.result.expected_loss,
        output_b.result.cvar_95
    ]
    
    bars1 = ax.bar(x - width/2, values_a, width, label=output_a.archetype_used['name'],
                   color='blue', alpha=0.7, edgecolor='black')
    bars2 = ax.bar(x + width/2, values_b, width, label=output_b.archetype_used['name'],
                   color='green', alpha=0.7, edgecolor='black')
    
    ax.set_ylabel('Value', fontsize=11)
    ax.set_title('Risk Metrics Comparison', fontsize=12, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(['P(default)\n(%)', 'Expected\nLoss ($)', 'CVaR 95%\n($)'], fontsize=9)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3, axis='y')
    
    ax = axes[1, 2]
    
    comparison_text = _generate_comparison_text(output_a, output_b)
    
    ax.text(0.05, 0.95, comparison_text,
           transform=ax.transAxes, fontsize=10,
           verticalalignment='top', fontfamily='monospace',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.3))
    ax.axis('off')
    ax.set_title('Summary', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def _generate_comparison_text(output_a, output_b) -> str:
    """Generate comparison summary text."""
    
    lines = []
    lines.append(f"SCENARIO A: {output_a.archetype_used['name']}")
    lines.append(f"  P(default): {output_a.result.p_default:.2%}")
    lines.append(f"  Risk Tier: {output_a.result.recommended_loan.risk_tier.value}")
    lines.append(f"  Platforms: {len(output_a.trajectory.portfolio_states[0].active_platforms)}")
    lines.append(f"  Events: {len(output_a.trajectory.events)}")
    lines.append("")
    lines.append(f"SCENARIO B: {output_b.archetype_used['name']}")
    lines.append(f"  P(default): {output_b.result.p_default:.2%}")
    lines.append(f"  Risk Tier: {output_b.result.recommended_loan.risk_tier.value}")
    lines.append(f"  Platforms: {len(output_b.trajectory.portfolio_states[0].active_platforms)}")
    lines.append(f"  Events: {len(output_b.trajectory.events)}")
    lines.append("")
    lines.append("DELTA:")
    
    delta_default = (output_b.result.p_default - output_a.result.p_default) * 100
    lines.append(f"  P(default): {delta_default:+.1f}pp")
    
    delta_loss = output_b.result.expected_loss - output_a.result.expected_loss
    lines.append(f"  Expected Loss: ${delta_loss:+,.0f}")
    
    return '\n'.join(lines)


def plot_simple_comparison(
    result_a,
    result_b,
    name_a: str,
    name_b: str,
    output_path: Optional[Path] = None,
    title: str = "Scenario Comparison"
) -> Path:
    """
    Simple two-panel comparison of income paths.
    
    Args:
        result_a: First SimulationResult
        result_b: Second SimulationResult
        name_a: Name of first scenario
        name_b: Name of second scenario
        output_path: Where to save chart
        title: Chart title
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / "simple_comparison.png"
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    for ax, result, name, color in [
        (ax1, result_a, name_a, 'blue'),
        (ax2, result_b, name_b, 'green')
    ]:
        n_paths_to_show = min(100, result.raw_paths.shape[0])
        for i in range(n_paths_to_show):
            ax.plot(result.raw_paths[i, :], alpha=0.1, color=color, linewidth=0.5)
        
        ax.plot(result.median_income_by_month, 'r-', linewidth=2.5, label='Median')
        ax.plot(result.p10_income_by_month, 'orange', linewidth=2,
               linestyle='--', label='P10')
        ax.plot(result.p90_income_by_month, 'green', linewidth=2,
               linestyle='--', label='P90')
        
        ax.set_title(f'{name}\nP(default)={result.p_default:.1%}',
                    fontsize=13, fontweight='bold')
        ax.set_xlabel('Month')
        ax.set_ylabel('Income ($)')
        ax.legend(fontsize=10)
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

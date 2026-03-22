"""
Advanced Visualizations - 3D surfaces, risk matrices, and stress testing.

These charts provide deeper insights into risk dynamics across multiple dimensions.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from pathlib import Path
from typing import Optional, List
from matplotlib import cm


def plot_risk_surface_3d(
    result,
    customer_app,
    archetype_id: str,
    run_id: str = None,
    output_path: Optional[Path] = None,
    loan_amounts: Optional[List[float]] = None,
    loan_terms: Optional[List[int]] = None
) -> Path:
    """
    3D surface plot showing default risk across loan amount and term.
    
    Args:
        result: SimulationResult from base case
        customer_app: CustomerApplication
        archetype_id: Profile identifier
        run_id: Unique identifier for this simulation run
        output_path: Where to save
        loan_amounts: Range of loan amounts to test
        loan_terms: Range of terms to test
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        if run_id:
            output_path = Config.CHART_DIR / f"risk_surface_3d_{archetype_id}_{run_id}.png"
        else:
            output_path = Config.CHART_DIR / f"risk_surface_3d_{archetype_id}.png"
    
    # Create grid of loan amounts and terms
    if loan_amounts is None:
        base_amount = customer_app.loan_request_amount
        loan_amounts = np.linspace(base_amount * 0.5, base_amount * 2, 10)
    
    if loan_terms is None:
        loan_terms = np.array([12, 18, 24, 30, 36, 48, 60])
    
    # Simulate risk for each combination
    # For now, use analytical approximation based on payment/income ratio
    X, Y = np.meshgrid(loan_amounts, loan_terms)
    Z = np.zeros_like(X)
    
    median_income = np.median(result.median_income_by_month)
    
    for i, term in enumerate(loan_terms):
        for j, amount in enumerate(loan_amounts):
            # Calculate monthly payment
            annual_rate = 0.12
            monthly_rate = annual_rate / 12
            payment = (amount * monthly_rate * (1 + monthly_rate) ** term) / \
                     ((1 + monthly_rate) ** term - 1)
            
            # Estimate default risk based on payment burden
            total_obligations = customer_app.monthly_fixed_expenses + \
                              customer_app.existing_debt_obligations + payment
            
            burden_ratio = total_obligations / median_income
            
            # Analytical default risk model
            # Higher burden = higher risk, adjusted for term length
            base_risk = 1 / (1 + np.exp(-(burden_ratio - 1.2) * 5))  # Sigmoid
            term_adjustment = 1 + (term - 24) * 0.01  # Longer term = more risk
            
            Z[i, j] = min(base_risk * term_adjustment, 1.0)
    
    # Create 3D surface plot
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(X, Y, Z * 100, cmap='RdYlGn_r',
                          linewidth=0.2, antialiased=True, alpha=0.9)
    
    # Add contour lines at base
    contours = ax.contour(X, Y, Z * 100, zdir='z', offset=0,
                         cmap='RdYlGn_r', linewidths=2, alpha=0.5)
    
    ax.set_xlabel('Loan Amount ($)', fontsize=12, labelpad=10)
    ax.set_ylabel('Loan Term (months)', fontsize=12, labelpad=10)
    ax.set_zlabel('Default Probability (%)', fontsize=12, labelpad=10)
    ax.set_title('Default Risk Surface\n(Risk vs Loan Structure)', 
                fontsize=16, fontweight='bold', pad=20)
    
    # Add colorbar
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Default Risk (%)')
    
    # Mark the requested loan
    requested_idx_term = np.argmin(np.abs(loan_terms - customer_app.requested_term_months))
    requested_idx_amount = np.argmin(np.abs(loan_amounts - customer_app.loan_request_amount))
    
    ax.scatter([customer_app.loan_request_amount], 
              [customer_app.requested_term_months],
              [Z[requested_idx_term, requested_idx_amount] * 100],
              color='red', s=200, marker='*', edgecolors='black', 
              linewidth=2, label='Requested Loan', zorder=10)
    
    ax.legend(fontsize=11)
    ax.view_init(elev=25, azim=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_volatility_surface_3d(
    result,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    3D surface showing income volatility over time and percentiles.
    
    Args:
        result: SimulationResult
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"volatility_surface_3d_{archetype_id}.png"
    
    # Calculate volatility (std dev) for each month
    n_months = result.raw_paths.shape[1]
    months = np.arange(n_months)
    
    # Calculate percentiles and std dev for each month
    percentiles = np.array([10, 25, 50, 75, 90])
    X, Y = np.meshgrid(months, percentiles)
    Z = np.zeros_like(X, dtype=float)
    
    for i, p in enumerate(percentiles):
        percentile_values = np.percentile(result.raw_paths, p, axis=0)
        # Calculate rolling volatility (std of 3-month window)
        for j in range(n_months):
            window_start = max(0, j - 1)
            window_end = min(n_months, j + 2)
            window_data = result.raw_paths[:, window_start:window_end]
            Z[i, j] = np.std(window_data)
    
    # Create 3D plot
    fig = plt.figure(figsize=(16, 10))
    ax = fig.add_subplot(111, projection='3d')
    
    surf = ax.plot_surface(X, Y, Z, cmap='plasma',
                          linewidth=0.2, antialiased=True, alpha=0.9)
    
    ax.set_xlabel('Month', fontsize=12, labelpad=10)
    ax.set_ylabel('Percentile', fontsize=12, labelpad=10)
    ax.set_zlabel('Income Volatility ($)', fontsize=12, labelpad=10)
    ax.set_title('Income Volatility Surface\n(Volatility Across Time & Percentiles)',
                fontsize=16, fontweight='bold', pad=20)
    
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label='Std Dev ($)')
    
    ax.view_init(elev=20, azim=45)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_risk_heatmap_matrix(
    result,
    customer_app,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    2D heatmap matrix: Default risk vs loan amount vs term.
    
    Args:
        result: SimulationResult
        customer_app: CustomerApplication
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"risk_matrix_{archetype_id}.png"
    
    # Create grid
    base_amount = customer_app.loan_request_amount
    loan_amounts = np.linspace(base_amount * 0.3, base_amount * 2.5, 15)
    loan_terms = np.array([12, 18, 24, 30, 36, 42, 48, 54, 60])
    
    risk_matrix = np.zeros((len(loan_terms), len(loan_amounts)))
    
    median_income = np.median(result.median_income_by_month)
    
    for i, term in enumerate(loan_terms):
        for j, amount in enumerate(loan_amounts):
            annual_rate = 0.12
            monthly_rate = annual_rate / 12
            payment = (amount * monthly_rate * (1 + monthly_rate) ** term) / \
                     ((1 + monthly_rate) ** term - 1)
            
            total_obligations = customer_app.monthly_fixed_expenses + \
                              customer_app.existing_debt_obligations + payment
            
            burden_ratio = total_obligations / median_income
            base_risk = 1 / (1 + np.exp(-(burden_ratio - 1.2) * 5))
            term_adjustment = 1 + (term - 24) * 0.01
            
            risk_matrix[i, j] = min(base_risk * term_adjustment, 1.0) * 100
    
    # Plot heatmap
    fig, ax = plt.subplots(figsize=(14, 10))
    
    im = ax.imshow(risk_matrix, cmap='RdYlGn_r', aspect='auto',
                   interpolation='bilinear', vmin=0, vmax=100)
    
    ax.set_xticks(range(len(loan_amounts)))
    ax.set_xticklabels([f'${a/1000:.1f}k' for a in loan_amounts], rotation=45, ha='right')
    ax.set_yticks(range(len(loan_terms)))
    ax.set_yticklabels([f'{t}mo' for t in loan_terms])
    
    ax.set_xlabel('Loan Amount', fontsize=13)
    ax.set_ylabel('Loan Term', fontsize=13)
    ax.set_title('Default Risk Matrix\n(Green=Low Risk, Red=High Risk)',
                fontsize=16, fontweight='bold')
    
    # Add colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Default Probability (%)', fontsize=12)
    
    # Mark requested loan with star
    req_idx_amount = np.argmin(np.abs(loan_amounts - customer_app.loan_request_amount))
    req_idx_term = np.argmin(np.abs(loan_terms - customer_app.requested_term_months))
    
    ax.plot(req_idx_amount, req_idx_term, marker='*', markersize=25,
           color='white', markeredgecolor='black', markeredgewidth=2,
           label='Requested Loan')
    
    # Add risk zones
    ax.text(0.02, 0.98, 'Green Zone: <15% risk\nYellow Zone: 15-30% risk\nRed Zone: >30% risk',
           transform=ax.transAxes, fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    ax.legend(fontsize=12, loc='lower right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_income_variance_funnel(
    result,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Funnel chart showing income variance expansion/contraction over time.
    
    Args:
        result: SimulationResult
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"variance_funnel_{archetype_id}.png"
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    months = range(len(result.median_income_by_month))
    
    # Calculate multiple percentiles for funnel effect
    p5 = np.percentile(result.raw_paths, 5, axis=0)
    p10 = np.percentile(result.raw_paths, 10, axis=0)
    p25 = np.percentile(result.raw_paths, 25, axis=0)
    p50 = result.median_income_by_month
    p75 = np.percentile(result.raw_paths, 75, axis=0)
    p90 = result.p90_income_by_month
    p95 = np.percentile(result.raw_paths, 95, axis=0)
    
    # Top panel: Funnel visualization
    ax1.fill_between(months, p5, p95, alpha=0.15, color='red', label='P5-P95 Range')
    ax1.fill_between(months, p10, p90, alpha=0.25, color='orange', label='P10-P90 Range')
    ax1.fill_between(months, p25, p75, alpha=0.35, color='yellow', label='P25-P75 Range')
    ax1.plot(months, p50, 'b-', linewidth=3, label='Median', zorder=10)
    
    ax1.set_title('Income Uncertainty Funnel', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Monthly Income ($)', fontsize=12)
    ax1.legend(fontsize=11, loc='best')
    ax1.grid(True, alpha=0.3)
    
    # Bottom panel: Width of ranges over time
    range_p90_p10 = p90 - p10
    range_p75_p25 = p75 - p25
    
    ax2.plot(months, range_p90_p10, 'r-', linewidth=2.5, label='P10-P90 Width')
    ax2.plot(months, range_p75_p25, 'orange', linewidth=2.5, label='P25-P75 Width')
    ax2.fill_between(months, 0, range_p90_p10, alpha=0.2, color='red')
    
    ax2.set_title('Income Range Width (Uncertainty)', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Range Width ($)', fontsize=12)
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    # Add stats
    avg_p90_p10 = np.mean(range_p90_p10)
    trend = "Expanding" if range_p90_p10[-1] > range_p90_p10[0] else "Contracting"
    
    stats_text = f'Avg P10-P90 Width: ${avg_p90_p10:,.0f}\nTrend: {trend}'
    ax2.text(0.02, 0.98, stats_text, transform=ax2.transAxes,
            fontsize=11, verticalalignment='top',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_stress_test_matrix(
    result,
    customer_app,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Stress test matrix showing risk under different income scenarios.
    
    Shows risk if income is X% lower and expenses are Y% higher.
    
    Args:
        result: SimulationResult
        customer_app: CustomerApplication
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"stress_test_matrix_{archetype_id}.png"
    
    # Define stress scenarios
    income_shocks = np.array([-30, -20, -10, 0, 10, 20])  # % change
    expense_shocks = np.array([0, 10, 20, 30, 40])  # % increase
    
    median_income = np.median(result.median_income_by_month)
    base_expenses = customer_app.monthly_fixed_expenses
    
    # Calculate loan payment
    annual_rate = 0.12
    monthly_rate = annual_rate / 12
    n = customer_app.requested_term_months
    payment = (customer_app.loan_request_amount * monthly_rate * (1 + monthly_rate) ** n) / \
             ((1 + monthly_rate) ** n - 1)
    
    risk_matrix = np.zeros((len(expense_shocks), len(income_shocks)))
    
    for i, exp_shock in enumerate(expense_shocks):
        for j, inc_shock in enumerate(income_shocks):
            shocked_income = median_income * (1 + inc_shock / 100)
            shocked_expenses = base_expenses * (1 + exp_shock / 100)
            
            total_obligations = shocked_expenses + customer_app.existing_debt_obligations + payment
            burden_ratio = total_obligations / shocked_income
            
            # Estimate risk
            risk = 1 / (1 + np.exp(-(burden_ratio - 1.2) * 5))
            risk_matrix[i, j] = risk * 100
    
    # Plot heatmap
    fig, ax = plt.subplots(figsize=(12, 8))
    
    im = ax.imshow(risk_matrix, cmap='RdYlGn_r', aspect='auto',
                   interpolation='bilinear', vmin=0, vmax=100)
    
    ax.set_xticks(range(len(income_shocks)))
    ax.set_xticklabels([f'{s:+d}%' for s in income_shocks])
    ax.set_yticks(range(len(expense_shocks)))
    ax.set_yticklabels([f'+{s}%' for s in expense_shocks])
    
    ax.set_xlabel('Income Shock', fontsize=13)
    ax.set_ylabel('Expense Shock', fontsize=13)
    ax.set_title('Stress Test Matrix\n(Default Risk Under Adverse Scenarios)',
                fontsize=16, fontweight='bold')
    
    # Add text annotations
    for i in range(len(expense_shocks)):
        for j in range(len(income_shocks)):
            text = f'{risk_matrix[i, j]:.0f}%'
            color = 'white' if risk_matrix[i, j] > 50 else 'black'
            ax.text(j, i, text, ha='center', va='center',
                   fontsize=10, fontweight='bold', color=color)
    
    # Mark base case
    base_idx_income = np.argmin(np.abs(income_shocks - 0))
    base_idx_expense = np.argmin(np.abs(expense_shocks - 0))
    ax.plot(base_idx_income, base_idx_expense, marker='*', markersize=20,
           color='blue', markeredgecolor='white', markeredgewidth=2,
           label='Base Case')
    
    # Colorbar
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('Default Probability (%)', fontsize=12)
    
    ax.legend(fontsize=12, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_time_decay_risk(
    result,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Shows how default risk evolves month-by-month.
    
    Args:
        result: SimulationResult
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"risk_decay_{archetype_id}.png"
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    
    n_months = result.raw_paths.shape[1]
    months = np.arange(n_months)
    
    # Calculate probability of having positive income each month
    survival_probs = []
    default_probs_cumulative = []
    
    for month in range(n_months):
        # Prob of income > 0
        positive_count = np.sum(result.raw_paths[:, month] > 0)
        survival_prob = positive_count / result.raw_paths.shape[0]
        survival_probs.append(survival_prob * 100)
        
        # Cumulative default by this month
        defaults_by_month = 0
        for path in result.raw_paths:
            if np.min(path[:month+1]) < 500:  # Practical default threshold
                defaults_by_month += 1
        
        default_prob = defaults_by_month / result.raw_paths.shape[0]
        default_probs_cumulative.append(default_prob * 100)
    
    # Top: Survival probability
    ax1.plot(months, survival_probs, 'g-', linewidth=3, label='Survival Probability')
    ax1.fill_between(months, 100, survival_probs, alpha=0.3, color='green')
    ax1.axhline(y=95, color='orange', linestyle='--', linewidth=1.5,
               label='95% Threshold', alpha=0.7)
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Survival Probability (%)', fontsize=12)
    ax1.set_title('Income Survival Rate Over Time', fontsize=14, fontweight='bold')
    ax1.legend(fontsize=11)
    ax1.grid(True, alpha=0.3)
    ax1.set_ylim([0, 105])
    
    # Bottom: Cumulative default rate
    ax2.plot(months, default_probs_cumulative, 'r-', linewidth=3, label='Cumulative Default Rate')
    ax2.fill_between(months, 0, default_probs_cumulative, alpha=0.3, color='red')
    ax2.axhline(y=result.p_default * 100, color='darkred', linestyle='--', linewidth=2,
               label=f'Final Default Rate: {result.p_default:.1%}', alpha=0.8)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Cumulative Default Rate (%)', fontsize=12)
    ax2.set_title('Default Risk Accumulation', fontsize=14, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_payment_burden_evolution(
    result,
    customer_app,
    loan_config,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Shows loan payment as % of income over time (payment burden).
    
    Args:
        result: SimulationResult
        customer_app: CustomerApplication
        loan_config: LoanConfig
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"payment_burden_{archetype_id}.png"
    
    # Calculate payment
    monthly_rate = loan_config.annual_rate / 12
    n = loan_config.term_months
    payment = (loan_config.amount * monthly_rate * (1 + monthly_rate) ** n) / \
             ((1 + monthly_rate) ** n - 1)
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    months = range(len(result.median_income_by_month))
    
    # Calculate burden ratios for different percentiles
    burden_median = (payment / np.array(result.median_income_by_month)) * 100
    burden_p10 = (payment / np.array(result.p10_income_by_month)) * 100
    burden_p90 = (payment / np.array(result.p90_income_by_month)) * 100
    
    ax.plot(months, burden_median, 'b-', linewidth=3, label='Median Scenario')
    ax.plot(months, burden_p10, 'r-', linewidth=2.5, label='P10 (Worst Case)', linestyle='--')
    ax.plot(months, burden_p90, 'g-', linewidth=2.5, label='P90 (Best Case)', linestyle='--')
    
    # Reference lines
    ax.axhline(y=15, color='orange', linestyle=':', linewidth=2,
              label='15% (Moderate Burden)', alpha=0.7)
    ax.axhline(y=25, color='red', linestyle=':', linewidth=2,
              label='25% (High Burden)', alpha=0.7)
    
    # Shade danger zones
    ax.fill_between(months, 25, 100, alpha=0.1, color='red', label='Danger Zone')
    
    ax.set_title('Loan Payment Burden Over Time\n(Payment as % of Income)',
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Month', fontsize=13)
    ax.set_ylabel('Payment / Income (%)', fontsize=13)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3)
    ax.set_ylim([0, min(np.max(burden_p10) * 1.1, 100)])
    
    # Add summary
    avg_burden_median = np.mean(burden_median)
    avg_burden_p10 = np.mean(burden_p10)
    
    summary = f'Avg Payment Burden:\nMedian: {avg_burden_median:.1f}%\nP10: {avg_burden_p10:.1f}%'
    ax.text(0.02, 0.98, summary, transform=ax.transAxes,
           fontsize=11, verticalalignment='top',
           bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_default_probability_waterfall(
    result,
    archetype_id: str,
    output_path: Optional[Path] = None
) -> Path:
    """
    Waterfall chart showing how default probability accumulates over time.
    
    Args:
        result: SimulationResult
        archetype_id: Profile identifier
        output_path: Where to save
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"default_waterfall_{archetype_id}.png"
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    n_months = result.raw_paths.shape[1]
    
    # Calculate incremental default rate per month
    defaults_by_month = []
    cumulative_defaults = 0
    
    for month in range(n_months):
        # Count new defaults in this month
        new_defaults = 0
        for path in result.raw_paths:
            # Check if this is first month below threshold
            if month > 0 and path[month] < 500 and path[month-1] >= 500:
                new_defaults += 1
            elif month == 0 and path[month] < 500:
                new_defaults += 1
        
        defaults_by_month.append(new_defaults)
        cumulative_defaults += new_defaults
    
    # Convert to percentages
    incremental_pct = np.array(defaults_by_month) / result.raw_paths.shape[0] * 100
    cumulative_pct = np.cumsum(incremental_pct)
    
    # Plot waterfall
    months = np.arange(n_months)
    
    # Bars for incremental defaults
    ax.bar(months, incremental_pct, color='coral', alpha=0.7, 
          edgecolor='black', label='New Defaults This Month')
    
    # Line for cumulative
    ax.plot(months, cumulative_pct, 'r-', linewidth=3, marker='o',
           markersize=6, label='Cumulative Default Rate')
    
    # Reference line
    ax.axhline(y=result.p_default * 100, color='darkred', linestyle='--',
              linewidth=2, label=f'Final Rate: {result.p_default:.1%}', alpha=0.8)
    
    ax.set_title('Default Risk Accumulation Waterfall',
                fontsize=16, fontweight='bold')
    ax.set_xlabel('Month', fontsize=13)
    ax.set_ylabel('Default Rate (%)', fontsize=13)
    ax.legend(fontsize=11, loc='best')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add peak default month
    peak_month = np.argmax(incremental_pct)
    peak_val = incremental_pct[peak_month]
    
    if peak_val > 0.5:
        ax.annotate(f'Peak: Month {peak_month}\n{peak_val:.1f}%',
                   xy=(peak_month, peak_val), xytext=(peak_month + 2, peak_val + 2),
                   arrowprops=dict(arrowstyle='->', color='red', lw=2),
                   fontsize=11, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def generate_all_advanced_charts(result, customer_app, loan_config, archetype_id: str):
    """Generate all advanced visualization types."""
    
    output_dir = Path("ai_model/outputs/charts")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("Generating advanced visualizations...")
    
    plot_risk_surface_3d(result, customer_app, archetype_id,
                        output_dir / f"risk_surface_3d_{archetype_id}.png")
    print("  [OK] 3D risk surface")
    
    plot_volatility_surface_3d(result, archetype_id,
                              output_dir / f"volatility_surface_3d_{archetype_id}.png")
    print("  [OK] 3D volatility surface")
    
    plot_risk_heatmap_matrix(result, customer_app, archetype_id,
                            output_dir / f"risk_matrix_{archetype_id}.png")
    print("  [OK] Risk heatmap matrix")
    
    plot_income_variance_funnel(result, archetype_id,
                               output_dir / f"variance_funnel_{archetype_id}.png")
    print("  [OK] Variance funnel")
    
    plot_stress_test_matrix(result, customer_app, archetype_id,
                           output_dir / f"stress_test_matrix_{archetype_id}.png")
    print("  [OK] Stress test matrix")
    
    plot_payment_burden_evolution(result, customer_app, loan_config, archetype_id,
                                 output_dir / f"payment_burden_{archetype_id}.png")
    print("  [OK] Payment burden evolution")
    
    plot_default_probability_waterfall(result, archetype_id,
                                      output_dir / f"default_waterfall_{archetype_id}.png")
    print("  [OK] Default waterfall")
    
    print(f"\n[OK] All advanced charts saved to: {output_dir}")
    
    return output_dir

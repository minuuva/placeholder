"""
Event Timeline - Visualizes life events chronologically.

Shows when events occurred and their impact on income/expenses.
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
from collections import defaultdict


def plot_event_timeline(
    trajectory,
    run_id: str = None,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Plot timeline of life events with impact visualization.
    
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
            output_path = Config.CHART_DIR / f"event_timeline_{trajectory.archetype_id}_{run_id}.png"
        else:
            output_path = Config.CHART_DIR / f"event_timeline_{trajectory.archetype_id}.png"
    
    if not trajectory.events:
        fig, ax = plt.subplots(figsize=(14, 6))
        ax.text(0.5, 0.5, 'No Life Events Occurred\n(Stable Trajectory)',
               ha='center', va='center', transform=ax.transAxes,
               fontsize=16, fontweight='bold', color='green')
        ax.set_title('Event Timeline', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    
    if title is None:
        title = f"{trajectory.archetype_id} - Life Event Timeline ({len(trajectory.events)} events)"
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    events_by_month = defaultdict(list)
    for event in trajectory.events:
        events_by_month[event.month].append(event)
    
    months = sorted(events_by_month.keys())
    
    event_type_colors = {
        'vehicle': 'orange',
        'health': 'red',
        'platform': 'purple',
        'housing': 'brown',
        'positive': 'green'
    }
    
    for month in months:
        month_events = events_by_month[month]
        
        for i, event in enumerate(month_events):
            event_type_prefix = event.event_type.value.split('_')[0]
            color = event_type_colors.get(event_type_prefix, 'gray')
            
            total_impact = event.income_impact + event.expense_impact
            
            y_offset = i * 0.3
            marker_size = min(abs(total_impact) / 50, 500)
            marker_size = max(marker_size, 50)
            
            alpha = 0.7 if total_impact < 0 else 0.5
            
            ax1.scatter(month, y_offset, s=marker_size, c=color,
                       alpha=alpha, edgecolors='black', linewidth=1.5)
    
    ax1.set_xlabel('Month', fontsize=12)
    ax1.set_ylabel('Event Occurrence', fontsize=12)
    ax1.set_title('Event Timeline (bubble size = impact magnitude)', fontsize=13, fontweight='bold')
    ax1.set_xlim(-1, trajectory.months + 1)
    ax1.grid(True, alpha=0.3, axis='x')
    ax1.set_yticks([])
    
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor=color,
                  markersize=10, label=name.capitalize())
        for name, color in event_type_colors.items()
    ]
    ax1.legend(handles=legend_elements, loc='upper right', fontsize=10)
    
    cumulative_income_impact = np.zeros(trajectory.months)
    cumulative_expense_impact = np.zeros(trajectory.months)
    
    for event in trajectory.events:
        for month_offset in range(event.duration_months):
            impact_month = event.month + month_offset
            if impact_month < trajectory.months:
                cumulative_income_impact[impact_month] += event.income_impact
                cumulative_expense_impact[impact_month] += event.expense_impact
    
    months_array = np.arange(trajectory.months)
    
    ax2.bar(months_array, cumulative_income_impact, alpha=0.7,
           color='green', label='Income Impact', edgecolor='black')
    ax2.bar(months_array, cumulative_expense_impact, alpha=0.7,
           color='red', label='Expense Impact', edgecolor='black')
    
    net_impact = cumulative_income_impact + cumulative_expense_impact
    ax2.plot(months_array, net_impact, linewidth=2.5, color='black',
            marker='o', markersize=4, label='Net Impact')
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax2.set_xlabel('Month', fontsize=12)
    ax2.set_ylabel('Monthly Impact ($)', fontsize=12)
    ax2.set_title('Cumulative Financial Impact by Month', fontsize=13, fontweight='bold')
    ax2.legend(fontsize=11)
    ax2.grid(True, alpha=0.3)
    
    if trajectory.macro_shock:
        shock_month = trajectory.macro_shock.start_month
        ax1.axvline(x=shock_month, color='red', linestyle='--', linewidth=2,
                   alpha=0.7, label=f'Macro Shock: {trajectory.macro_shock.scenario_name}')
        ax2.axvline(x=shock_month, color='red', linestyle='--', linewidth=2,
                   alpha=0.7, label=f'Macro Shock: {trajectory.macro_shock.scenario_name}')
        ax1.legend(handles=legend_elements + [ax1.get_lines()[-1]], loc='upper right', fontsize=10)
        ax2.legend(fontsize=11)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path


def plot_event_impact_summary(
    trajectory,
    output_path: Optional[Path] = None,
    title: Optional[str] = None
) -> Path:
    """
    Summarize event impacts by category.
    
    Args:
        trajectory: LifeTrajectory object
        output_path: Where to save chart
        title: Custom title
    
    Returns:
        Path to saved chart
    """
    if output_path is None:
        from ..config import Config
        output_path = Config.CHART_DIR / f"event_summary_{trajectory.archetype_id}.png"
    
    if not trajectory.events:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(0.5, 0.5, 'No Events Occurred',
               ha='center', va='center', transform=ax.transAxes,
               fontsize=16, fontweight='bold', color='green')
        ax.set_title('Event Impact Summary', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        return output_path
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    if title is None:
        title = f"{trajectory.archetype_id} - Event Impact Summary"
    fig.suptitle(title, fontsize=16, fontweight='bold')
    
    event_categories = defaultdict(int)
    for event in trajectory.events:
        category = event.event_type.value.split('_')[0]
        event_categories[category] += 1
    
    categories = list(event_categories.keys())
    counts = [event_categories[cat] for cat in categories]
    
    colors_map = {
        'vehicle': 'orange',
        'health': 'red',
        'platform': 'purple',
        'housing': 'brown',
        'positive': 'green'
    }
    colors = [colors_map.get(cat, 'gray') for cat in categories]
    
    ax1.bar(categories, counts, color=colors, alpha=0.7, edgecolor='black')
    ax1.set_xlabel('Event Category', fontsize=11)
    ax1.set_ylabel('Number of Events', fontsize=11)
    ax1.set_title('Events by Category', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    
    for i, (cat, count) in enumerate(zip(categories, counts)):
        ax1.text(i, count, str(count), ha='center', va='bottom', fontweight='bold')
    
    total_income_impact = sum(e.income_impact for e in trajectory.events)
    total_expense_impact = sum(abs(e.expense_impact) for e in trajectory.events)
    
    impacts = [total_income_impact, -total_expense_impact]
    labels = ['Total Income\nImpact', 'Total Expense\nImpact']
    colors_impact = ['green' if total_income_impact >= 0 else 'red',
                     'red']
    
    bars = ax2.bar(labels, impacts, color=colors_impact, alpha=0.7, edgecolor='black')
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1.5)
    ax2.set_ylabel('Total Impact ($)', fontsize=11)
    ax2.set_title('Cumulative Financial Impact', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    
    for bar, val in zip(bars, impacts):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'${abs(val):,.0f}', ha='center',
                va='bottom' if val >= 0 else 'top', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    
    return output_path

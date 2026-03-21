"""
Export all configuration files for Monte Carlo simulation.

This module generates the final JSON files that the simulation will consume:
- archetypes.json: Gig worker personas
- seasonality.json: Monthly income multipliers
- macro_params.json: Macro shock scenarios
- expenses.json: Expense structure
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.static_params import (
    SEASONALITY_MULTIPLIERS, EXPENSES, INCOME_VOLATILITY,
    LIFE_EVENT_PROBABILITIES, EVENT_IMPACTS, PORTFOLIO_EVOLUTION,
    TAX_QUARTERS, DEFAULT_PARAMETERS
)
from transform.build_archetypes import get_all_archetypes
from transform.build_scenarios import build_all_scenarios


def get_output_dir():
    """Get the data output directory path."""
    base_path = Path(__file__).parent.parent
    output_dir = base_path / "data"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def export_archetypes():
    """
    Export archetype personas to archetypes.json.
    
    Returns:
        Path to exported file
    """
    archetypes = get_all_archetypes()
    output_path = get_output_dir() / "archetypes.json"
    
    # Add metadata
    export_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Gig worker archetype personas for VarLend risk modeling",
            "source": "JPMorgan Chase Institute + Gridwise + industry research",
            "count": len(archetypes),
        },
        "archetypes": archetypes
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return output_path


def export_seasonality():
    """
    Export seasonality multipliers to seasonality.json.
    
    Returns:
        Path to exported file
    """
    output_path = get_output_dir() / "seasonality.json"
    
    # Convert month numbers to month names for clarity
    month_names = {
        1: "jan", 2: "feb", 3: "mar", 4: "apr", 5: "may", 6: "jun",
        7: "jul", 8: "aug", 9: "sep", 10: "oct", 11: "nov", 12: "dec"
    }
    
    formatted_multipliers = {}
    for gig_type, multipliers in SEASONALITY_MULTIPLIERS.items():
        formatted_multipliers[gig_type] = {
            month_names[month]: value 
            for month, value in multipliers.items()
        }
    
    export_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Monthly income seasonality multipliers by gig type",
            "source": "JPMorgan Chase Institute (income spikes in March and December)",
            "note": "Multipliers are relative to annual average (1.0 = average month)",
        },
        "seasonality": formatted_multipliers,
        "tax_quarters": {
            "due_months": ["apr", "jun", "sep", "jan"],
            "effective_income_reduction": TAX_QUARTERS["effective_income_reduction"],
            "description": "Self-employment tax estimated payment months (reduces take-home by ~25%)"
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return output_path


def export_macro_params():
    """
    Export macro shock scenarios to macro_params.json.
    
    Returns:
        Path to exported file
    """
    scenarios = build_all_scenarios()
    output_path = get_output_dir() / "macro_params.json"
    
    export_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Macro economic shock scenarios calibrated from historical data",
            "source": "FRED historical data + recession analysis",
            "categories": list(scenarios.keys()),
        },
        "scenarios": scenarios
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return output_path


def export_expenses():
    """
    Export expense structure to expenses.json.
    
    Returns:
        Path to exported file
    """
    output_path = get_output_dir() / "expenses.json"
    
    export_data = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "version": "1.0",
            "description": "Gig worker expense structure and life event impacts",
            "source": "Triplog + industry estimates",
        },
        "base_expenses": {
            "gas_weekly_fulltime_range": EXPENSES["gas_weekly_fulltime"],
            "gas_weekly_parttime_range": EXPENSES["gas_weekly_parttime"],
            "maintenance_monthly_range": EXPENSES["maintenance_monthly"],
            "vehicle_depreciation_monthly": EXPENSES["vehicle_depreciation_monthly"],
            "insurance_monthly": EXPENSES["insurance_monthly"],
            "phone_data_monthly": EXPENSES["phone_data_monthly"],
            "self_employment_tax_rate": EXPENSES["self_employment_tax"],
        },
        "life_events": {
            "probabilities": LIFE_EVENT_PROBABILITIES,
            "impacts": {
                key: value for key, value in EVENT_IMPACTS.items()
            }
        },
        "income_volatility": INCOME_VOLATILITY,
        "portfolio_evolution": PORTFOLIO_EVOLUTION,
        "default_parameters": DEFAULT_PARAMETERS,
    }
    
    with open(output_path, 'w') as f:
        json.dump(export_data, f, indent=2)
    
    return output_path


def export_all_configs():
    """
    Export all configuration files.
    
    Returns:
        Dictionary with paths to all exported files
    """
    print("="*60)
    print("VarLend Data Pipeline - Export Configurations")
    print("="*60)
    
    output_dir = get_output_dir()
    print(f"\nOutput directory: {output_dir}")
    
    exported_files = {}
    
    # Export archetypes
    print("\n[1/4] Exporting archetypes...")
    try:
        path = export_archetypes()
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {path.name} ({size_kb:.1f} KB)")
        exported_files['archetypes'] = str(path)
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Export seasonality
    print("\n[2/4] Exporting seasonality...")
    try:
        path = export_seasonality()
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {path.name} ({size_kb:.1f} KB)")
        exported_files['seasonality'] = str(path)
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Export macro parameters
    print("\n[3/4] Exporting macro parameters...")
    try:
        path = export_macro_params()
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {path.name} ({size_kb:.1f} KB)")
        exported_files['macro_params'] = str(path)
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Export expenses
    print("\n[4/4] Exporting expenses...")
    try:
        path = export_expenses()
        size_kb = path.stat().st_size / 1024
        print(f"  ✓ {path.name} ({size_kb:.1f} KB)")
        exported_files['expenses'] = str(path)
    except Exception as e:
        print(f"  ✗ Failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Export Summary")
    print("="*60)
    print(f"✓ Exported {len(exported_files)}/4 configuration files")
    print(f"  Output directory: {output_dir}")
    
    total_size = sum(Path(p).stat().st_size for p in exported_files.values()) / 1024
    print(f"  Total size: {total_size:.1f} KB")
    
    print("\n" + "="*60)
    print("✓ Export complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Review exported JSON files in data/")
    print("  2. Run validate_pipeline.py to check data quality")
    print("  3. Use loaders.py to load data into Monte Carlo simulation")
    
    return exported_files


def print_file_summary(filepath):
    """Print a summary of an exported JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    print(f"\n{Path(filepath).name}:")
    print(f"  Generated: {data.get('metadata', {}).get('generated_at', 'N/A')}")
    print(f"  Description: {data.get('metadata', {}).get('description', 'N/A')}")
    
    # Type-specific summaries
    if 'archetypes' in data:
        print(f"  Archetypes: {len(data['archetypes'])}")
        for arch in data['archetypes']:
            print(f"    - {arch['name']}: μ=${arch['base_mu']:,.0f}, σ=${arch['base_sigma']:,.0f}")
    
    if 'seasonality' in data:
        print(f"  Gig types: {len(data['seasonality'])}")
        for gig_type in data['seasonality'].keys():
            print(f"    - {gig_type}")
    
    if 'scenarios' in data:
        total_scenarios = sum(
            len(scenarios) if isinstance(scenarios, dict) else 0
            for key, scenarios in data['scenarios'].items()
            if key != 'baseline_probabilities'
        )
        print(f"  Scenarios: {total_scenarios}")
        for category in data['scenarios'].keys():
            if category != 'baseline_probabilities':
                print(f"    - {category}: {len(data['scenarios'][category])}")


if __name__ == "__main__":
    # Export all configuration files
    exported_files = export_all_configs()
    
    # Print detailed summaries
    if exported_files:
        print("\n" + "="*60)
        print("Configuration File Summaries")
        print("="*60)
        
        for file_type, filepath in exported_files.items():
            try:
                print_file_summary(filepath)
            except Exception as e:
                print(f"\n{Path(filepath).name}: Error reading file - {e}")

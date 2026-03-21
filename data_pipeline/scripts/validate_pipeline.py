"""
Validate data pipeline outputs for quality and consistency.

Runs comprehensive checks on all exported JSON files to ensure:
- Data integrity
- Parameter ranges are reasonable
- Consistency across files
- Monte Carlo simulation compatibility
"""

import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_data_dir():
    """Get the data directory path."""
    base_path = Path(__file__).parent.parent
    return base_path / "data"


def load_json_file(filename):
    """Load a JSON configuration file."""
    filepath = get_data_dir() / filename
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filename}")
    
    with open(filepath, 'r') as f:
        return json.load(f)


def validate_archetypes():
    """Validate archetype personas file."""
    print("\n" + "="*60)
    print("Validating archetypes.json")
    print("="*60)
    
    errors = []
    warnings = []
    
    try:
        data = load_json_file("archetypes.json")
        archetypes = data.get("archetypes", [])
        
        print(f"Found {len(archetypes)} archetypes")
        
        required_fields = [
            "id", "name", "description", "base_mu", "base_sigma",
            "platforms", "hours_per_week", "metro", "default_risk_category"
        ]
        
        for i, arch in enumerate(archetypes):
            arch_name = arch.get("name", f"Archetype {i}")
            
            # Check required fields
            for field in required_fields:
                if field not in arch:
                    errors.append(f"{arch_name}: Missing required field '{field}'")
            
            # Validate income parameters
            mu = arch.get("base_mu", 0)
            sigma = arch.get("base_sigma", 0)
            
            if mu <= 0:
                errors.append(f"{arch_name}: base_mu must be positive ({mu})")
            
            if sigma < 0:
                errors.append(f"{arch_name}: base_sigma must be non-negative ({sigma})")
            
            if mu < 500:
                warnings.append(f"{arch_name}: Very low income μ=${mu:.2f}/month")
            
            # Check CV is reasonable
            if mu > 0:
                cv = sigma / mu
                if cv > 1.5:
                    warnings.append(f"{arch_name}: Very high CV {cv:.1%}")
                elif cv < 0.1:
                    warnings.append(f"{arch_name}: Very low CV {cv:.1%}")
            
            # Validate platforms
            platforms = arch.get("platforms", [])
            if not platforms or len(platforms) == 0:
                errors.append(f"{arch_name}: No platforms specified")
            
            # Validate hours
            hours = arch.get("hours_per_week", 0)
            if not (5 <= hours <= 80):
                warnings.append(f"{arch_name}: Unusual hours/week: {hours}")
            
            # Validate probabilities
            prob_fields = ["diversification_probability", "churn_risk"]
            for field in prob_fields:
                if field in arch:
                    prob = arch[field]
                    if not (0 <= prob <= 1):
                        errors.append(f"{arch_name}: {field} out of range [0,1]: {prob}")
            
            print(f"  ✓ {arch_name}: μ=${mu:,.0f}, σ=${sigma:,.0f}, CV={sigma/mu:.1%}")
        
    except FileNotFoundError as e:
        errors.append(str(e))
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors, warnings


def validate_seasonality():
    """Validate seasonality multipliers file."""
    print("\n" + "="*60)
    print("Validating seasonality.json")
    print("="*60)
    
    errors = []
    warnings = []
    
    try:
        data = load_json_file("seasonality.json")
        seasonality = data.get("seasonality", {})
        
        print(f"Found {len(seasonality)} gig types")
        
        month_names = ["jan", "feb", "mar", "apr", "may", "jun",
                       "jul", "aug", "sep", "oct", "nov", "dec"]
        
        for gig_type, multipliers in seasonality.items():
            # Check all 12 months present
            if len(multipliers) != 12:
                errors.append(f"{gig_type}: Expected 12 months, found {len(multipliers)}")
            
            for month in month_names:
                if month not in multipliers:
                    errors.append(f"{gig_type}: Missing month '{month}'")
            
            # Check multipliers are reasonable
            values = list(multipliers.values())
            if values:
                avg = sum(values) / len(values)
                min_val = min(values)
                max_val = max(values)
                
                # Average should be close to 1.0
                if not (0.95 <= avg <= 1.15):
                    warnings.append(f"{gig_type}: Average multiplier {avg:.3f} not near 1.0")
                
                # Check range
                if min_val < 0.5:
                    warnings.append(f"{gig_type}: Very low multiplier {min_val:.3f}")
                if max_val > 1.5:
                    warnings.append(f"{gig_type}: Very high multiplier {max_val:.3f}")
                
                print(f"  ✓ {gig_type}: avg={avg:.3f}, range=[{min_val:.2f}, {max_val:.2f}]")
        
    except FileNotFoundError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors, warnings


def validate_macro_params():
    """Validate macro shock scenarios file."""
    print("\n" + "="*60)
    print("Validating macro_params.json")
    print("="*60)
    
    errors = []
    warnings = []
    
    try:
        data = load_json_file("macro_params.json")
        scenarios = data.get("scenarios", {})
        
        category_count = len([k for k in scenarios.keys() if k != "baseline_probabilities"])
        print(f"Found {category_count} scenario categories")
        
        for category, category_scenarios in scenarios.items():
            if category == "baseline_probabilities":
                continue
            
            if not isinstance(category_scenarios, dict):
                warnings.append(f"{category}: Not a dictionary")
                continue
            
            print(f"\n  Category: {category} ({len(category_scenarios)} scenarios)")
            
            for scenario_name, scenario in category_scenarios.items():
                if not isinstance(scenario, dict):
                    errors.append(f"{scenario_name}: Not a dictionary")
                    continue
                
                # Check required fields
                if "name" not in scenario:
                    warnings.append(f"{scenario_name}: Missing 'name' field")
                
                # Validate probabilities
                if "trigger_probability" in scenario:
                    prob = scenario["trigger_probability"]
                    if not (0 <= prob <= 1):
                        errors.append(f"{scenario_name}: trigger_probability out of range: {prob}")
                
                # Validate platform impacts
                if "platform_impacts" in scenario:
                    for platform, impact in scenario["platform_impacts"].items():
                        if impact < 0:
                            errors.append(f"{scenario_name}: Negative impact for {platform}: {impact}")
                        if impact > 2.0:
                            warnings.append(f"{scenario_name}: Very high impact for {platform}: {impact}")
                
                print(f"    ✓ {scenario.get('name', scenario_name)}")
        
    except FileNotFoundError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors, warnings


def validate_expenses():
    """Validate expenses and life events file."""
    print("\n" + "="*60)
    print("Validating expenses.json")
    print("="*60)
    
    errors = []
    warnings = []
    
    try:
        data = load_json_file("expenses.json")
        
        # Check base expenses
        base_expenses = data.get("base_expenses", {})
        if not base_expenses:
            errors.append("Missing base_expenses section")
        else:
            print(f"Found {len(base_expenses)} expense categories")
            
            # Validate self-employment tax rate
            se_tax = base_expenses.get("self_employment_tax_rate", 0)
            if not (0.10 <= se_tax <= 0.20):
                warnings.append(f"Unusual self-employment tax rate: {se_tax:.1%}")
        
        # Check life events
        life_events = data.get("life_events", {})
        if not life_events:
            warnings.append("Missing life_events section")
        else:
            probabilities = life_events.get("probabilities", {})
            print(f"Found {len(probabilities)} life event categories")
            
            # Validate probabilities
            for category, events in probabilities.items():
                for event, prob in events.items():
                    if not (0 <= prob <= 1):
                        errors.append(f"Probability out of range: {category}.{event} = {prob}")
        
        # Check income volatility
        income_vol = data.get("income_volatility", {})
        if "median_cv" in income_vol:
            cv = income_vol["median_cv"]
            if not (0.20 <= cv <= 0.50):
                warnings.append(f"Unusual median CV: {cv:.1%}")
            print(f"  ✓ Median CV: {cv:.1%}")
        
        print("  ✓ All expense data validated")
        
    except FileNotFoundError as e:
        errors.append(str(e))
    except Exception as e:
        errors.append(f"Unexpected error: {e}")
    
    return errors, warnings


def validate_cross_file_consistency():
    """Validate consistency across multiple files."""
    print("\n" + "="*60)
    print("Cross-File Consistency Checks")
    print("="*60)
    
    errors = []
    warnings = []
    
    try:
        archetypes_data = load_json_file("archetypes.json")
        seasonality_data = load_json_file("seasonality.json")
        
        # Check that archetype platforms have seasonality data
        archetypes = archetypes_data.get("archetypes", [])
        seasonality = seasonality_data.get("seasonality", {})
        
        for arch in archetypes:
            platforms = arch.get("platforms", [])
            for platform in platforms:
                # Map platform to gig type
                if platform in ["uber", "lyft"]:
                    gig_type = "rideshare"
                elif platform in ["doordash", "instacart", "grubhub"]:
                    gig_type = "delivery"
                else:
                    gig_type = "general_gig"
                
                if gig_type not in seasonality:
                    warnings.append(f"No seasonality data for {gig_type} (used by {arch['name']})")
        
        print("  ✓ Platform-seasonality mapping consistent")
        
        # Check that all archetypes have distinct income levels
        mus = [arch["base_mu"] for arch in archetypes if "base_mu" in arch]
        if len(mus) != len(set(mus)):
            warnings.append("Some archetypes have identical income parameters")
        else:
            print(f"  ✓ All {len(mus)} archetypes have distinct income levels")
        
    except Exception as e:
        errors.append(f"Cross-file validation error: {e}")
    
    return errors, warnings


def run_all_validations():
    """Run all validation checks."""
    print("="*60)
    print("VarLend Data Pipeline - Validation Suite")
    print("="*60)
    
    all_errors = []
    all_warnings = []
    
    # Validate each file
    validations = [
        ("Archetypes", validate_archetypes),
        ("Seasonality", validate_seasonality),
        ("Macro Parameters", validate_macro_params),
        ("Expenses", validate_expenses),
        ("Cross-File Consistency", validate_cross_file_consistency),
    ]
    
    for name, validation_func in validations:
        try:
            errors, warnings = validation_func()
            all_errors.extend(errors)
            all_warnings.extend(warnings)
        except Exception as e:
            all_errors.append(f"{name} validation failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Validation Summary")
    print("="*60)
    
    if not all_errors and not all_warnings:
        print("✓ All validations passed with no errors or warnings!")
        return 0
    
    if all_warnings:
        print(f"\n⚠ Warnings ({len(all_warnings)}):")
        for warning in all_warnings:
            print(f"  - {warning}")
    
    if all_errors:
        print(f"\n✗ Errors ({len(all_errors)}):")
        for error in all_errors:
            print(f"  - {error}")
        print("\n✗ Validation FAILED - please fix errors before proceeding")
        return 1
    
    print(f"\n✓ Validation passed with {len(all_warnings)} warning(s)")
    print("  Warnings are informational - pipeline can proceed")
    return 0


if __name__ == "__main__":
    exit_code = run_all_validations()
    sys.exit(exit_code)

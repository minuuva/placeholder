"""
Integration test for the complete data pipeline.

Tests the full workflow:
1. Load static parameters
2. Run calibration
3. Build archetypes and scenarios
4. Export configurations
5. Validate outputs
6. Load data with loaders
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.static_params import validate_parameters
from transform.calibrate_monte_carlo import calculate_income_params, validate_params
from transform.build_archetypes import get_all_archetypes
from transform.build_scenarios import build_all_scenarios
from output.export_configs import export_all_configs
from loaders import DataLoader, get_income_params


def test_static_params():
    """Test that static parameters are valid."""
    print("\n" + "="*60)
    print("Test 1: Static Parameters")
    print("="*60)
    
    try:
        validate_parameters()
        print("✓ Static parameters validated")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_calibration():
    """Test Monte Carlo parameter calibration."""
    print("\n" + "="*60)
    print("Test 2: Monte Carlo Calibration")
    print("="*60)
    
    try:
        # Test basic calculation
        params = calculate_income_params(
            platforms=["uber"],
            hours_per_week=40,
            metro="national"
        )
        
        # Validate parameters
        validate_params(params["mu"], params["sigma"])
        
        print(f"✓ Calibration working: μ=${params['mu']:,.0f}, σ=${params['sigma']:,.0f}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_archetypes():
    """Test archetype generation."""
    print("\n" + "="*60)
    print("Test 3: Archetype Generation")
    print("="*60)
    
    try:
        archetypes = get_all_archetypes()
        
        if len(archetypes) < 5:
            print(f"✗ Expected at least 5 archetypes, got {len(archetypes)}")
            return False
        
        # Validate each archetype
        for arch in archetypes:
            mu = arch["base_mu"]
            sigma = arch["base_sigma"]
            validate_params(mu, sigma)
        
        print(f"✓ Generated {len(archetypes)} valid archetypes")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_scenarios():
    """Test scenario building."""
    print("\n" + "="*60)
    print("Test 4: Scenario Building")
    print("="*60)
    
    try:
        scenarios = build_all_scenarios()
        
        expected_categories = ["recession", "gas_spike", "regulatory", "tech_disruption"]
        for category in expected_categories:
            if category not in scenarios:
                print(f"✗ Missing category: {category}")
                return False
        
        total_scenarios = sum(
            len(s) for k, s in scenarios.items() 
            if k != "baseline_probabilities" and isinstance(s, dict)
        )
        
        print(f"✓ Built {total_scenarios} scenarios across {len(expected_categories)} categories")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_export():
    """Test configuration export."""
    print("\n" + "="*60)
    print("Test 5: Configuration Export")
    print("="*60)
    
    try:
        exported_files = export_all_configs()
        
        expected_files = ["archetypes", "seasonality", "macro_params", "expenses"]
        for file_type in expected_files:
            if file_type not in exported_files:
                print(f"✗ Missing export: {file_type}")
                return False
        
        # Check files exist
        for file_type, filepath in exported_files.items():
            if not Path(filepath).exists():
                print(f"✗ File not found: {filepath}")
                return False
        
        print(f"✓ Exported {len(exported_files)} configuration files")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_loaders():
    """Test data loaders."""
    print("\n" + "="*60)
    print("Test 6: Data Loaders")
    print("="*60)
    
    try:
        loader = DataLoader()
        
        # Test archetype loading
        archetypes = loader.list_archetypes()
        if not archetypes:
            print("✗ No archetypes found")
            return False
        
        first_arch = loader.load_archetype(archetypes[0])
        if "base_mu" not in first_arch or "base_sigma" not in first_arch:
            print("✗ Archetype missing income parameters")
            return False
        
        # Test seasonality loading
        delivery_march = loader.get_seasonality("delivery", "mar")
        if not isinstance(delivery_march, (int, float)):
            print("✗ Seasonality multiplier invalid")
            return False
        
        # Test scenario loading
        scenarios = loader.list_scenarios()
        if not scenarios:
            print("✗ No scenarios found")
            return False
        
        print(f"✓ Loaders working: {len(archetypes)} archetypes, {sum(len(s) for s in scenarios.values())} scenarios")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_monte_carlo_readiness():
    """Test that data is ready for Monte Carlo simulation."""
    print("\n" + "="*60)
    print("Test 7: Monte Carlo Simulation Readiness")
    print("="*60)
    
    try:
        # Simulate a simple Monte Carlo use case
        loader = DataLoader()
        
        # Load an archetype
        vic = loader.load_archetype("volatile_vic")
        mu = vic["base_mu"]
        sigma = vic["base_sigma"]
        
        # Get seasonality adjustment
        platforms = vic["platforms"]
        if platforms:
            platform = platforms[0]
            if platform in ["uber", "lyft"]:
                gig_type = "rideshare"
            elif platform in ["doordash", "instacart"]:
                gig_type = "delivery"
            else:
                gig_type = "general_gig"
            
            march_mult = loader.get_seasonality(gig_type, "mar")
            adjusted_mu = mu * march_mult
            
            print(f"✓ Baseline: μ=${mu:,.0f}/month")
            print(f"✓ March adjustment: {march_mult:.2f}x → μ=${adjusted_mu:,.0f}/month")
        
        # Get a recession scenario
        recession = loader.get_scenario("recession", "recession_2020")
        impact = recession["platform_impacts"].get("delivery", 0.95)
        shock_mu = mu * impact
        
        print(f"✓ COVID recession impact: {impact:.2f}x → μ=${shock_mu:,.0f}/month")
        
        # Check we have all necessary data
        expense_data = loader.get_expense_data()
        if "income_volatility" not in expense_data:
            print("✗ Missing income volatility data")
            return False
        
        print("✓ All data ready for Monte Carlo simulation")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_integration_tests():
    """Run all integration tests."""
    print("="*60)
    print("VarLend Data Pipeline - Integration Tests")
    print("="*60)
    
    tests = [
        ("Static Parameters", test_static_params),
        ("Monte Carlo Calibration", test_calibration),
        ("Archetype Generation", test_archetypes),
        ("Scenario Building", test_scenarios),
        ("Configuration Export", test_export),
        ("Data Loaders", test_loaders),
        ("Monte Carlo Readiness", test_monte_carlo_readiness),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            passed = test_func()
            results.append((name, passed))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*60)
    print("Integration Test Summary")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    print("\n" + "="*60)
    if passed == total:
        print(f"✓ ALL TESTS PASSED ({passed}/{total})")
        print("="*60)
        print("\n🎉 Data pipeline is fully operational!")
        print("\nNext steps:")
        print("  1. Build Monte Carlo simulation engine")
        print("  2. Integrate with data loaders:")
        print("     from data_pipeline.loaders import load_archetype, get_seasonality")
        print("     vic = load_archetype('volatile_vic')")
        print("     mu, sigma = vic['base_mu'], vic['base_sigma']")
        print("  3. Run simulations with real archetype data")
        return 0
    else:
        print(f"✗ TESTS FAILED ({passed}/{total} passed)")
        print("="*60)
        print("\nPlease fix failing tests before proceeding.")
        return 1


if __name__ == "__main__":
    exit_code = run_integration_tests()
    sys.exit(exit_code)

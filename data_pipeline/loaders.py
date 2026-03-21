"""
Data loaders for Monte Carlo simulation.

Simple functions to load and access exported configuration data.
This is the interface between the data pipeline and the Monte Carlo simulation.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class DataLoader:
    """
    Central data loader for VarLend simulation data.
    
    Usage:
        loader = DataLoader()
        vic = loader.load_archetype('volatile_vic')
        seasonality = loader.get_seasonality('delivery', 'mar')
        recession = loader.get_scenario('recession', 'recession_2020')
    """
    
    def __init__(self, data_dir=None):
        """
        Initialize data loader.
        
        Args:
            data_dir: Path to data directory (defaults to data_pipeline/data)
        """
        if data_dir is None:
            # Default to data directory relative to this file
            base_path = Path(__file__).parent
            self.data_dir = base_path / "data"
        else:
            self.data_dir = Path(data_dir)
        
        # Cache loaded data
        self._cache = {}
    
    def _load_json(self, filename):
        """Load and cache a JSON file."""
        if filename not in self._cache:
            filepath = self.data_dir / filename
            if not filepath.exists():
                raise FileNotFoundError(f"Data file not found: {filename}")
            
            with open(filepath, 'r') as f:
                self._cache[filename] = json.load(f)
        
        return self._cache[filename]
    
    def load_archetype(self, archetype_id: str) -> Dict[str, Any]:
        """
        Load a specific archetype by ID.
        
        Args:
            archetype_id: Archetype identifier (e.g., 'volatile_vic')
        
        Returns:
            Dictionary with archetype parameters
        
        Raises:
            ValueError: If archetype ID not found
        """
        data = self._load_json("archetypes.json")
        archetypes = data.get("archetypes", [])
        
        for archetype in archetypes:
            if archetype.get("id") == archetype_id:
                return archetype
        
        available_ids = [a.get("id") for a in archetypes]
        raise ValueError(
            f"Archetype '{archetype_id}' not found. "
            f"Available: {', '.join(available_ids)}"
        )
    
    def list_archetypes(self) -> List[str]:
        """
        Get list of all available archetype IDs.
        
        Returns:
            List of archetype IDs
        """
        data = self._load_json("archetypes.json")
        archetypes = data.get("archetypes", [])
        return [a.get("id") for a in archetypes]
    
    def get_seasonality(self, gig_type: str, month: Optional[str] = None) -> Any:
        """
        Get seasonality multiplier(s) for a gig type.
        
        Args:
            gig_type: Type of gig work ('delivery', 'rideshare', 'general_gig')
            month: Specific month ('jan', 'feb', etc.) or None for all months
        
        Returns:
            Single multiplier (if month specified) or dict of all multipliers
        """
        data = self._load_json("seasonality.json")
        seasonality = data.get("seasonality", {})
        
        if gig_type not in seasonality:
            raise ValueError(f"Unknown gig type: {gig_type}")
        
        gig_seasonality = seasonality[gig_type]
        
        if month is None:
            return gig_seasonality
        
        if month not in gig_seasonality:
            raise ValueError(f"Unknown month: {month}")
        
        return gig_seasonality[month]
    
    def get_scenario(self, category: str, scenario_name: str) -> Dict[str, Any]:
        """
        Get a specific macro shock scenario.
        
        Args:
            category: Scenario category ('recession', 'gas_spike', 'regulatory', 'tech_disruption')
            scenario_name: Specific scenario name (e.g., 'recession_2020')
        
        Returns:
            Dictionary with scenario parameters
        """
        data = self._load_json("macro_params.json")
        scenarios = data.get("scenarios", {})
        
        if category not in scenarios:
            raise ValueError(f"Unknown scenario category: {category}")
        
        category_scenarios = scenarios[category]
        
        if scenario_name not in category_scenarios:
            available = list(category_scenarios.keys())
            raise ValueError(
                f"Scenario '{scenario_name}' not found in {category}. "
                f"Available: {', '.join(available)}"
            )
        
        return category_scenarios[scenario_name]
    
    def list_scenarios(self, category: Optional[str] = None) -> Dict[str, List[str]]:
        """
        List available scenarios.
        
        Args:
            category: Optional category to filter by
        
        Returns:
            Dictionary mapping categories to scenario lists
        """
        data = self._load_json("macro_params.json")
        scenarios = data.get("scenarios", {})
        
        result = {}
        for cat, cat_scenarios in scenarios.items():
            if cat == "baseline_probabilities":
                continue
            if category is None or cat == category:
                if isinstance(cat_scenarios, dict):
                    result[cat] = list(cat_scenarios.keys())
        
        return result
    
    def get_expense_data(self) -> Dict[str, Any]:
        """
        Get all expense and life event data.
        
        Returns:
            Dictionary with base expenses, life events, etc.
        """
        return self._load_json("expenses.json")
    
    def get_base_expenses(self) -> Dict[str, Any]:
        """Get base expense structure."""
        data = self.get_expense_data()
        return data.get("base_expenses", {})
    
    def get_life_event_probabilities(self) -> Dict[str, Any]:
        """Get life event probability data."""
        data = self.get_expense_data()
        life_events = data.get("life_events", {})
        return life_events.get("probabilities", {})
    
    def get_income_volatility_params(self) -> Dict[str, Any]:
        """Get income volatility parameters (from JPMorgan research)."""
        data = self.get_expense_data()
        return data.get("income_volatility", {})
    
    def clear_cache(self):
        """Clear the internal data cache (force reload on next access)."""
        self._cache = {}


# Convenience functions for direct access
_default_loader = None


def get_loader(data_dir=None) -> DataLoader:
    """Get the default data loader instance (singleton pattern)."""
    global _default_loader
    if _default_loader is None or data_dir is not None:
        _default_loader = DataLoader(data_dir)
    return _default_loader


def load_archetype(archetype_id: str) -> Dict[str, Any]:
    """Load archetype by ID using default loader."""
    return get_loader().load_archetype(archetype_id)


def get_seasonality(gig_type: str, month: Optional[str] = None) -> Any:
    """Get seasonality multiplier using default loader."""
    return get_loader().get_seasonality(gig_type, month)


def get_scenario(category: str, scenario_name: str) -> Dict[str, Any]:
    """Get scenario using default loader."""
    return get_loader().get_scenario(category, scenario_name)


def get_income_params(archetype_id: str) -> tuple:
    """
    Get (μ, σ) parameters for an archetype.
    
    Convenience function that returns just the income parameters.
    
    Args:
        archetype_id: Archetype identifier
    
    Returns:
        Tuple of (mu, sigma)
    """
    archetype = load_archetype(archetype_id)
    return (archetype["base_mu"], archetype["base_sigma"])


def map_platform_to_gig_type(platform: str) -> str:
    """
    Map a platform name to its gig type for seasonality lookup.
    
    Args:
        platform: Platform name (e.g., 'uber', 'doordash')
    
    Returns:
        Gig type ('rideshare', 'delivery', or 'general_gig')
    """
    delivery_platforms = ["doordash", "grubhub", "instacart", "ubereats"]
    rideshare_platforms = ["uber", "lyft"]
    
    platform_lower = platform.lower()
    
    if platform_lower in delivery_platforms:
        return "delivery"
    elif platform_lower in rideshare_platforms:
        return "rideshare"
    else:
        return "general_gig"


if __name__ == "__main__":
    print("="*60)
    print("VarLend Data Loaders - Test Suite")
    print("="*60)
    
    loader = DataLoader()
    
    # Test 1: Load archetypes
    print("\n=== Test 1: Load Archetypes ===")
    archetype_ids = loader.list_archetypes()
    print(f"Available archetypes: {', '.join(archetype_ids)}")
    
    for arch_id in archetype_ids[:3]:  # Test first 3
        arch = loader.load_archetype(arch_id)
        print(f"  {arch['name']}: μ=${arch['base_mu']:,.0f}, σ=${arch['base_sigma']:,.0f}")
    
    # Test 2: Get seasonality
    print("\n=== Test 2: Get Seasonality ===")
    for gig_type in ["delivery", "rideshare"]:
        march = loader.get_seasonality(gig_type, "mar")
        dec = loader.get_seasonality(gig_type, "dec")
        print(f"{gig_type}: March={march:.2f}, December={dec:.2f}")
    
    # Test 3: Get scenarios
    print("\n=== Test 3: Get Scenarios ===")
    scenarios = loader.list_scenarios()
    for category, scenario_list in scenarios.items():
        print(f"{category}: {len(scenario_list)} scenario(s)")
        for scenario_name in scenario_list[:2]:  # Show first 2
            scenario = loader.get_scenario(category, scenario_name)
            print(f"  - {scenario['name']}")
    
    # Test 4: Get expense data
    print("\n=== Test 4: Get Expense Data ===")
    base_expenses = loader.get_base_expenses()
    print(f"Base expense categories: {len(base_expenses)}")
    print(f"  Self-employment tax: {base_expenses['self_employment_tax_rate']:.1%}")
    
    life_events = loader.get_life_event_probabilities()
    print(f"Life event categories: {len(life_events)}")
    
    income_vol = loader.get_income_volatility_params()
    print(f"Median CV from JPMorgan: {income_vol['median_cv']:.1%}")
    
    # Test 5: Convenience functions
    print("\n=== Test 5: Convenience Functions ===")
    mu, sigma = get_income_params("volatile_vic")
    print(f"Volatile Vic params: μ=${mu:,.0f}, σ=${sigma:,.0f}")
    
    gig_type = map_platform_to_gig_type("uber")
    print(f"Uber → {gig_type}")
    
    gig_type = map_platform_to_gig_type("doordash")
    print(f"DoorDash → {gig_type}")
    
    # Test 6: Error handling
    print("\n=== Test 6: Error Handling ===")
    try:
        loader.load_archetype("nonexistent")
        print("  ✗ Should have raised ValueError")
    except ValueError as e:
        print(f"  ✓ Correctly raised error: {str(e)[:50]}...")
    
    print("\n" + "="*60)
    print("✓ All loader tests completed successfully")
    print("="*60)
    print("\nUsage example:")
    print("  from data_pipeline.loaders import load_archetype, get_seasonality")
    print("  ")
    print("  vic = load_archetype('volatile_vic')")
    print("  mu, sigma = vic['base_mu'], vic['base_sigma']")
    print("  ")
    print("  march_multiplier = get_seasonality('delivery', 'mar')")
    print("  adjusted_mu = mu * march_multiplier")

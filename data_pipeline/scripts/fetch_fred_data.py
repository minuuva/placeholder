"""
Script to pre-download FRED data before hackathon.

Run this the night before to ensure all necessary historical data is cached.
This eliminates dependency on API availability during the demo.
"""

import sys
import os
from pathlib import Path
import json
import csv

# Add parent directory to path to import fred_client
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingest.fred_client import FREDClient


def fetch_all_data(api_key=None):
    """
    Fetch all required FRED data and save to cache.
    
    Args:
        api_key: FRED API key (optional, uses env variable if not provided)
    """
    print("="*60)
    print("FRED Data Fetch Script")
    print("="*60)
    
    client = FREDClient(api_key=api_key)
    
    if not client.api_key:
        print("\n⚠ WARNING: No FRED API key found!")
        print("Set FRED_API_KEY environment variable or pass as argument.")
        print("Get a free API key at: https://fred.stlouisfed.org/")
        print("\nContinuing with fallback data generation...")
    
    print(f"\nCache directory: {client.cache_dir}")
    
    # Fetch gas prices (most critical for expense modeling)
    print("\n" + "="*60)
    print("1. Fetching Gas Prices (GASREGW)...")
    print("="*60)
    try:
        gas_data = client.get_gas_prices(start_date='2020-01-01')
        print(f"✓ Retrieved {len(gas_data)} observations")
        if gas_data:
            print(f"  Date range: {gas_data[0]['date']} to {gas_data[-1]['date']}")
            print(f"  Latest price: ${gas_data[-1]['value']:.3f}/gallon")
            
            # Also save as CSV for easy inspection
            csv_path = client.cache_dir / 'gas_prices.csv'
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'value'])
                writer.writeheader()
                writer.writerows(gas_data)
            print(f"  Saved CSV: {csv_path.name}")
        
        # Get statistics
        stats = client.get_gas_price_statistics(start_date='2020-01-01')
        if stats:
            print(f"\n  Statistics (2020-present):")
            print(f"    Mean: ${stats['mean']:.3f}/gallon")
            print(f"    Range: ${stats['min']:.3f} - ${stats['max']:.3f}")
            print(f"    Volatility: {stats['coefficient_of_variation']:.1%} CV")
    except Exception as e:
        print(f"✗ Failed to fetch gas prices: {e}")
    
    # Fetch unemployment rate (for recession calibration)
    print("\n" + "="*60)
    print("2. Fetching Unemployment Rate (UNRATE)...")
    print("="*60)
    try:
        unemployment_data = client.get_unemployment_rate(start_date='2007-01-01')
        print(f"✓ Retrieved {len(unemployment_data)} observations")
        if unemployment_data:
            print(f"  Date range: {unemployment_data[0]['date']} to {unemployment_data[-1]['date']}")
            print(f"  Latest rate: {unemployment_data[-1]['value']:.1f}%")
            
            # Save as CSV
            csv_path = client.cache_dir / 'unemployment_rate.csv'
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'value'])
                writer.writeheader()
                writer.writerows(unemployment_data)
            print(f"  Saved CSV: {csv_path.name}")
            
            # Find peaks (recession indicators)
            values = [obs['value'] for obs in unemployment_data]
            max_rate = max(values)
            max_idx = values.index(max_rate)
            print(f"  Peak unemployment: {max_rate:.1f}% on {unemployment_data[max_idx]['date']}")
    except Exception as e:
        print(f"✗ Failed to fetch unemployment data: {e}")
    
    # Fetch inflation data (CPI)
    print("\n" + "="*60)
    print("3. Fetching Inflation/CPI (CPIAUCSL)...")
    print("="*60)
    try:
        cpi_data = client.get_inflation_rate(start_date='2020-01-01')
        print(f"✓ Retrieved {len(cpi_data)} observations")
        if cpi_data:
            print(f"  Date range: {cpi_data[0]['date']} to {cpi_data[-1]['date']}")
            print(f"  Latest CPI: {cpi_data[-1]['value']:.2f}")
            
            # Calculate inflation rate (year-over-year)
            if len(cpi_data) >= 12:
                recent = cpi_data[-1]['value']
                year_ago = cpi_data[-13]['value']
                inflation_rate = ((recent - year_ago) / year_ago) * 100
                print(f"  YoY inflation: {inflation_rate:.1f}%")
            
            # Save as CSV
            csv_path = client.cache_dir / 'inflation_cpi.csv'
            with open(csv_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'value'])
                writer.writeheader()
                writer.writerows(cpi_data)
            print(f"  Saved CSV: {csv_path.name}")
    except Exception as e:
        print(f"✗ Failed to fetch inflation data: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    cached_files = list(client.cache_dir.glob('*.json')) + list(client.cache_dir.glob('*.csv'))
    print(f"\nCached files ({len(cached_files)}):")
    for f in sorted(cached_files):
        size_kb = f.stat().st_size / 1024
        print(f"  ✓ {f.name} ({size_kb:.1f} KB)")
    
    print("\n" + "="*60)
    print("✓ Data fetch complete!")
    print("="*60)
    print("\nYou can now run the data pipeline without internet connectivity.")
    print("The cached data will be used automatically if the API is unavailable.")


def generate_recession_reference_data():
    """
    Generate reference data for major recessions to use in scenario calibration.
    """
    print("\n" + "="*60)
    print("Generating Recession Reference Data...")
    print("="*60)
    
    # Historical recession data (manually curated from FRED)
    recessions = {
        "2008_financial_crisis": {
            "name": "2008 Financial Crisis",
            "start_date": "2007-12-01",
            "end_date": "2009-06-01",
            "duration_months": 18,
            "unemployment_peak": 10.0,  # Peak in Oct 2009
            "unemployment_start": 5.0,
            "gdp_decline_percent": -4.3,
            "characteristics": {
                "housing_crash": True,
                "credit_freeze": True,
                "consumer_spending_drop": "severe",
                "gas_price_spike": True,  # Mid-2008
                "gas_price_crash": True,  # Late 2008
            },
            "gig_economy_impact": {
                "rideshare": 0.70,  # -30% (less discretionary spending)
                "delivery": 0.85,  # -15% (less food delivery adoption)
                "freelance": 0.75,  # -25% (business cutbacks)
            }
        },
        "2020_covid_recession": {
            "name": "COVID-19 Recession",
            "start_date": "2020-02-01",
            "end_date": "2020-04-01",
            "duration_months": 2,  # Shortest on record
            "unemployment_peak": 14.7,  # Peak in April 2020
            "unemployment_start": 3.5,
            "gdp_decline_percent": -31.4,  # Q2 2020 annualized
            "characteristics": {
                "lockdowns": True,
                "stimulus_payments": True,
                "remote_work_surge": True,
                "gas_price_crash": True,
                "supply_chain_disruption": True,
            },
            "gig_economy_impact": {
                "rideshare": 0.40,  # -60% (lockdowns, no travel)
                "delivery": 1.30,  # +30% (surge in demand)
                "freelance": 1.10,  # +10% (remote work boom)
            }
        },
        "2022_inflation_slowdown": {
            "name": "2022 Inflation Slowdown",
            "start_date": "2022-06-01",
            "end_date": "2023-12-01",
            "duration_months": 18,
            "unemployment_peak": 4.0,  # Relatively low
            "unemployment_start": 3.6,
            "gdp_decline_percent": -1.6,  # Q1 2022
            "characteristics": {
                "high_inflation": True,
                "interest_rate_hikes": True,
                "gas_price_spike": True,
                "tech_layoffs": True,
            },
            "gig_economy_impact": {
                "rideshare": 0.95,  # -5% (reduced discretionary spending)
                "delivery": 1.05,  # +5% (sustained habits from COVID)
                "freelance": 0.90,  # -10% (tech sector cuts)
            }
        }
    }
    
    # Save recession reference data
    base_path = Path(__file__).parent.parent
    output_path = base_path / "data" / "historical" / "recession_reference.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(recessions, f, indent=2)
    
    print(f"✓ Saved recession reference data: {output_path.name}")
    print(f"\n  Recessions documented: {len(recessions)}")
    for key, data in recessions.items():
        print(f"    - {data['name']} ({data['duration_months']} months)")
    
    return recessions


if __name__ == "__main__":
    # Check for API key in environment or command line
    api_key = os.getenv('FRED_API_KEY')
    
    if len(sys.argv) > 1:
        api_key = sys.argv[1]
    
    # Fetch data
    try:
        fetch_all_data(api_key)
        
        # Generate recession reference data
        generate_recession_reference_data()
        
        print("\n✓ All data fetching complete!")
        print("\nNext steps:")
        print("  1. Review cached data in data_pipeline/data/historical/")
        print("  2. Run calibrate_monte_carlo.py to generate simulation parameters")
        print("  3. Run export_configs.py to generate final JSON files")
        
    except Exception as e:
        print(f"\n✗ Error during data fetch: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

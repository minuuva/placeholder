"""
FRED API client for fetching macroeconomic data.

Minimal implementation focusing on gas prices (GASREGW) with fallback to cached data.
This ensures the demo works even if the FRED API is unavailable during the hackathon.
"""

import os
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path


class FREDClient:
    """
    Client for Federal Reserve Economic Data (FRED) API.
    
    Focuses on gas price data (GASREGW) for expense modeling.
    Includes automatic fallback to cached CSV data if API fails.
    """
    
    def __init__(self, api_key=None, cache_dir=None):
        """
        Initialize FRED client.
        
        Args:
            api_key: FRED API key (defaults to FRED_API_KEY env variable)
            cache_dir: Directory for cached data (defaults to data/historical)
        """
        self.api_key = api_key or os.getenv('FRED_API_KEY')
        self.base_url = "https://api.stlouisfed.org/fred/series/observations"
        
        # Set cache directory
        if cache_dir is None:
            # Default to data/historical relative to this file
            base_path = Path(__file__).parent.parent
            self.cache_dir = base_path / "data" / "historical"
        else:
            self.cache_dir = Path(cache_dir)
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_gas_prices(self, start_date=None, end_date=None, use_cache_fallback=True):
        """
        Fetch weekly regular gas prices (GASREGW series).
        
        Args:
            start_date: Start date (YYYY-MM-DD format), defaults to 2020-01-01
            end_date: End date (YYYY-MM-DD format), defaults to today
            use_cache_fallback: If True, fall back to cached data on API failure
        
        Returns:
            List of dictionaries with 'date' and 'value' keys
        """
        # Set default dates
        if start_date is None:
            start_date = '2020-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Try API first if we have a key
        if self.api_key:
            try:
                data = self._fetch_from_api('GASREGW', start_date, end_date)
                if data:
                    # Cache the successful result
                    self._cache_data('gas_prices.json', data)
                    return data
            except Exception as e:
                print(f"Warning: FRED API request failed: {e}")
        
        # Fall back to cached data
        if use_cache_fallback:
            print("Falling back to cached gas price data...")
            return self._load_cached_gas_prices()
        
        raise ValueError("No FRED API key and cache fallback disabled")
    
    def get_unemployment_rate(self, start_date=None, end_date=None):
        """
        Fetch unemployment rate (UNRATE series).
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
        
        Returns:
            List of dictionaries with 'date' and 'value' keys
        """
        if start_date is None:
            start_date = '2020-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data = self._fetch_from_api('UNRATE', start_date, end_date)
            if data:
                self._cache_data('unemployment_rate.json', data)
                return data
        except Exception as e:
            print(f"Warning: Failed to fetch unemployment data: {e}")
            return self._load_cached_data('unemployment_rate.json')
    
    def get_inflation_rate(self, start_date=None, end_date=None):
        """
        Fetch CPI (CPIAUCSL series) for inflation tracking.
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
        
        Returns:
            List of dictionaries with 'date' and 'value' keys
        """
        if start_date is None:
            start_date = '2020-01-01'
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        try:
            data = self._fetch_from_api('CPIAUCSL', start_date, end_date)
            if data:
                self._cache_data('inflation_cpi.json', data)
                return data
        except Exception as e:
            print(f"Warning: Failed to fetch inflation data: {e}")
            return self._load_cached_data('inflation_cpi.json')
    
    def _fetch_from_api(self, series_id, start_date, end_date):
        """
        Fetch data from FRED API.
        
        Args:
            series_id: FRED series identifier (e.g., 'GASREGW')
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        
        Returns:
            List of dictionaries with 'date' and 'value' keys
        """
        if not self.api_key:
            raise ValueError("FRED API key not set")
        
        params = {
            'series_id': series_id,
            'api_key': self.api_key,
            'file_type': 'json',
            'observation_start': start_date,
            'observation_end': end_date,
        }
        
        response = requests.get(self.base_url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse observations
        if 'observations' in data:
            observations = []
            for obs in data['observations']:
                # Skip missing values (marked as '.')
                if obs['value'] != '.':
                    observations.append({
                        'date': obs['date'],
                        'value': float(obs['value'])
                    })
            return observations
        
        return []
    
    def _cache_data(self, filename, data):
        """Save data to cache directory as JSON."""
        cache_path = self.cache_dir / filename
        with open(cache_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load_cached_data(self, filename):
        """Load data from cache directory."""
        cache_path = self.cache_dir / filename
        if cache_path.exists():
            with open(cache_path, 'r') as f:
                return json.load(f)
        return []
    
    def _load_cached_gas_prices(self):
        """
        Load cached gas price data.
        
        Returns:
            List of dictionaries with 'date' and 'value' keys
        """
        # Try JSON cache first
        data = self._load_cached_data('gas_prices.json')
        if data:
            return data
        
        # Try CSV fallback
        csv_path = self.cache_dir / 'gas_prices.csv'
        if csv_path.exists():
            import csv
            data = []
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        data.append({
                            'date': row['date'],
                            'value': float(row['value'])
                        })
                    except (KeyError, ValueError):
                        continue
            return data
        
        # Return fallback data if no cache exists
        print("Warning: No cached gas price data found. Using fallback values.")
        return self._get_fallback_gas_prices()
    
    def _get_fallback_gas_prices(self):
        """
        Generate fallback gas price data based on recent averages.
        Used only if both API and cache fail.
        """
        # Generate synthetic data for last 5 years
        # Based on average $3.50/gallon with typical volatility
        base_price = 3.50
        data = []
        
        start_date = datetime.now() - timedelta(days=365*5)
        current_date = start_date
        
        while current_date <= datetime.now():
            # Add some seasonal variation
            month = current_date.month
            seasonal_factor = 1.0
            if month in [5, 6, 7]:  # Summer driving season
                seasonal_factor = 1.15
            elif month in [11, 12, 1]:  # Winter
                seasonal_factor = 0.95
            
            price = base_price * seasonal_factor
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'value': round(price, 3)
            })
            
            # Move to next week
            current_date += timedelta(days=7)
        
        return data
    
    def get_gas_price_statistics(self, start_date=None, end_date=None):
        """
        Get statistical summary of gas prices over a period.
        
        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)
        
        Returns:
            Dictionary with mean, min, max, volatility statistics
        """
        data = self.get_gas_prices(start_date, end_date)
        
        if not data:
            return None
        
        prices = [obs['value'] for obs in data]
        
        mean_price = sum(prices) / len(prices)
        min_price = min(prices)
        max_price = max(prices)
        
        # Calculate volatility (standard deviation)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        volatility = variance ** 0.5
        
        return {
            'mean': round(mean_price, 3),
            'min': round(min_price, 3),
            'max': round(max_price, 3),
            'volatility': round(volatility, 3),
            'coefficient_of_variation': round(volatility / mean_price, 3),
            'n_observations': len(prices),
            'date_range': (data[0]['date'], data[-1]['date']),
        }


def test_client():
    """Test the FRED client with and without API key."""
    print("Testing FRED client...")
    
    client = FREDClient()
    
    # Test 1: Get gas prices (will use fallback if no API key)
    print("\n=== Test 1: Gas Prices ===")
    try:
        gas_data = client.get_gas_prices(start_date='2023-01-01')
        print(f"✓ Retrieved {len(gas_data)} gas price observations")
        if gas_data:
            print(f"  Latest: {gas_data[-1]['date']} = ${gas_data[-1]['value']:.3f}/gallon")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 2: Get gas price statistics
    print("\n=== Test 2: Gas Price Statistics ===")
    try:
        stats = client.get_gas_price_statistics(start_date='2023-01-01')
        if stats:
            print(f"✓ Statistics calculated:")
            print(f"  Mean: ${stats['mean']:.3f}/gallon")
            print(f"  Range: ${stats['min']:.3f} - ${stats['max']:.3f}")
            print(f"  Volatility: ${stats['volatility']:.3f} (CV: {stats['coefficient_of_variation']:.1%})")
            print(f"  Observations: {stats['n_observations']}")
    except Exception as e:
        print(f"✗ Failed: {e}")
    
    # Test 3: Check cache directory
    print("\n=== Test 3: Cache Directory ===")
    if client.cache_dir.exists():
        cached_files = list(client.cache_dir.glob('*.json')) + list(client.cache_dir.glob('*.csv'))
        print(f"✓ Cache directory exists: {client.cache_dir}")
        print(f"  Cached files: {len(cached_files)}")
        for f in cached_files:
            print(f"    - {f.name}")
    else:
        print(f"✓ Cache directory created: {client.cache_dir}")
    
    print("\n✓ FRED client tests completed")


if __name__ == "__main__":
    test_client()

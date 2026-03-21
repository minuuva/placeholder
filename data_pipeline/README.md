# VarLend Data Pipeline

**Research-backed data transformation pipeline for gig worker risk assessment**

This pipeline transforms published research findings and macroeconomic data into clean, simulation-ready parameters for Monte Carlo risk modeling. All parameters are traceable to credible sources (JPMorgan Chase Institute, Gridwise, FRED, etc.) for defensibility during hackathon presentations.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Data Sources & Citations](#data-sources--citations)
6. [Pipeline Components](#pipeline-components)
7. [Output Files](#output-files)
8. [Usage Examples](#usage-examples)
9. [Validation & Testing](#validation--testing)

---

## Overview

The VarLend data pipeline solves a critical challenge: **transforming fragmented research into cohesive simulation parameters**. Traditional lenders reject gig workers because high income variance looks like risk. VarLend's Monte Carlo approach distinguishes variance from actual default risk—but only if the input parameters are credible.

### Key Features

✅ **Research-backed parameters**: Every number traces to JPMorgan Chase, Gridwise, FRED, or industry studies  
✅ **Geographic differentiation**: Adjusts for SF vs. rural Ohio income/expense differences  
✅ **Scenario calibration**: Recession shocks based on actual 2008/2020 data  
✅ **Reproducible**: Deterministic output, cached data for offline demos  
✅ **Monte Carlo ready**: Clean JSON configs that simulation engines can consume directly

### What This Pipeline Does

```
Research Papers + FRED Data
         ↓
   [Data Pipeline]
         ↓
JSON Configs (μ, σ, scenarios, events)
         ↓
   Monte Carlo Simulation
         ↓
   Risk Scores & Loan Recommendations
```

---

## Architecture

```
data_pipeline/
├── ingest/                      # Data acquisition
│   ├── static_params.py         # JPMorgan/Gridwise hardcoded research
│   ├── metro_adjustments.py    # Geographic multipliers
│   └── fred_client.py           # FRED API wrapper (with CSV fallback)
├── transform/                   # Data transformation
│   ├── calibrate_monte_carlo.py # Research → (μ, σ) parameters
│   ├── build_archetypes.py      # Generate 5 gig worker personas
│   └── build_scenarios.py       # Recession/shock calibration
├── output/                      # Export layer
│   └── export_configs.py        # Write clean JSON files
├── data/                        # Output directory
│   ├── archetypes.json          # 5 gig worker personas
│   ├── seasonality.json         # Monthly income multipliers
│   ├── macro_params.json        # 9 shock scenarios
│   ├── expenses.json            # Expense structure + life events
│   └── historical/              # Cached FRED data (CSVs)
├── scripts/                     # Utilities
│   ├── fetch_fred_data.py       # Pre-download macro data
│   ├── validate_pipeline.py    # Quality checks
│   └── test_integration.py     # End-to-end tests
├── loaders.py                   # Data loading interface
├── requirements.txt
└── README.md
```

---

## Installation

### Prerequisites

- Python 3.9+
- Virtual environment (recommended)

### Setup

```bash
# Clone or navigate to project
cd data_pipeline

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Optional: FRED API Key

For live macro data fetching (not required for demo):

```bash
export FRED_API_KEY="your_key_here"
```

Get a free key at: https://fred.stlouisfed.org/

---

## Quick Start

### Generate All Configuration Files

```bash
# Activate virtual environment
source venv/bin/activate

# Export all configs (archetypes, seasonality, scenarios, expenses)
python output/export_configs.py

# Validate outputs
python scripts/validate_pipeline.py

# Run integration tests
python scripts/test_integration.py
```

**Expected output:**
- ✅ 4 JSON files in `data/` (15.1 KB total)
- ✅ All validations pass
- ✅ 7/7 integration tests pass

### Use in Monte Carlo Simulation

```python
from data_pipeline.loaders import load_archetype, get_seasonality, get_scenario

# Load a gig worker persona
vic = load_archetype('volatile_vic')
mu = vic['base_mu']          # $1,642/month
sigma = vic['base_sigma']    # $680/month
cv = vic['coefficient_of_variation']  # 41.4%

# Apply seasonal adjustment (March spike)
march_mult = get_seasonality('delivery', 'mar')  # 1.15x
adjusted_mu = mu * march_mult  # $1,889/month

# Apply recession shock
covid = get_scenario('recession', 'recession_2020')
delivery_impact = covid['platform_impacts']['delivery']  # 1.30 (surge)
shock_mu = mu * delivery_impact  # $2,135/month

# Now run your Monte Carlo simulation with these parameters
```

---

## Data Sources & Citations

### Primary Sources

| Source | What We Use | Citation |
|--------|-------------|----------|
| **JPMorgan Chase Institute** | 36% income volatility CV, 21% extreme swings, 6-week emergency buffer | [Household Financial Stability Report](https://www.jpmorganchase.com/institute) |
| **Gridwise** | $23.33/hr Uber earnings (2025) | [2025 Driver Earnings Report](https://gridwise.io) |
| **Triplog** | $200-500/week part-time, $800-1500/week full-time | [Gig Worker Income Guide](https://triplog.com) |
| **FRED (St. Louis Fed)** | Gas prices (GASREGW), unemployment (UNRATE), CPI | [FRED API](https://fred.stlouisfed.org) |
| **BLS** | Metro wage data, cost of living indices | [Bureau of Labor Statistics](https://bls.gov) |

### Recession Calibration

| Event | Duration | Unemployment Δ | Gig Impact Source |
|-------|----------|---------------|-------------------|
| 2008 Financial Crisis | 18 months | +5.3pp | Historical analysis + expert estimates |
| 2020 COVID Recession | 2 months | +11.2pp | Real-time gig platform reports (rideshare -60%, delivery +30%) |
| 2022 Inflation Slowdown | 18 months | +0.4pp | Industry surveys + platform disclosures |

---

## Pipeline Components

### 1. Static Parameters (`ingest/static_params.py`)

Hardcoded research findings:
- **Income volatility**: 36% CV, 9% typical swing, 21% extreme swing (JPMorgan)
- **Platform earnings**: Hourly rates for Uber, DoorDash, Instacart, etc. (Gridwise/Triplog)
- **Expenses**: Gas ($150-400/week), maintenance ($50-100/month), tax (15.3%)
- **Seasonality**: March/December spikes from JPMorgan data
- **Life events**: Probabilities for vehicle repairs, health issues, platform deactivations

### 2. Metro Adjustments (`ingest/metro_adjustments.py`)

Geographic multipliers for 6 markets:

| Metro | Income Multiplier | Expense Multiplier | Competition Index |
|-------|------------------:|-------------------:|------------------:|
| National | 1.0x | 1.0x | 1.0x |
| San Francisco | 1.4x | 1.6x | 1.3x |
| New York | 1.3x | 1.5x | 1.4x |
| Atlanta | 0.95x | 0.85x | 0.9x |
| Dallas | 0.98x | 0.88x | 0.95x |
| Rural | 0.7x | 0.75x | 0.6x |

### 3. FRED Client (`ingest/fred_client.py`)

Minimal API wrapper with robust fallback:
- **Primary**: Fetch live gas prices (GASREGW)
- **Fallback 1**: Load cached JSON
- **Fallback 2**: Load cached CSV
- **Fallback 3**: Generate synthetic data based on recent averages

**Why this matters**: Demo still works if internet fails.

### 4. Calibration (`transform/calibrate_monte_carlo.py`)

The core transformation:

```python
# Transform hourly rate + hours → Monthly net income (μ)
Uber driver, 40 hrs/week, national
→ Hourly: $23.33
→ Monthly gross: $4,041
→ Expenses: $1,666 (gas, maintenance, insurance, phone)
→ Self-employment tax: $618
→ Net income (μ): $2,012

# Apply volatility research → Standard deviation (σ)
JPMorgan 36% CV → σ = $724

# Result: (μ=$2,012, σ=$724) ready for Monte Carlo
```

### 5. Archetypes (`transform/build_archetypes.py`)

5 differentiated personas:

| Archetype | Platforms | Hours/wk | Metro | μ | σ | CV | Risk |
|-----------|-----------|----------|-------|---|---|----|------|
| **Volatile Vic** | DoorDash | 45 | National | $1,642 | $680 | 41.4% | High |
| **Steady Sarah** | Uber+DD+IC | 40 | Atlanta | $1,450 | $327 | 22.5% | Low |
| **Weekend Warrior** | Uber | 15 | Dallas | $581 | $209 | 36.0% | Low |
| **SF Hustler** | Uber+DD | 50 | SF | $3,948 | $1,080 | 27.4% | Medium |
| **Rising Ryan** | DD+IC | 35 | National | $803 | $230 | 28.6% | Medium |

### 6. Scenarios (`transform/build_scenarios.py`)

9 macro shock scenarios across 4 categories:

**Recession (3)**
- 2008 Financial Crisis: -30% rideshare, -15% delivery
- COVID-19 Recession: -60% rideshare, +30% delivery
- 2022 Inflation Slowdown: -5% rideshare, +5% delivery

**Gas Spike (2)**
- Moderate (+25%): -10% delivery income
- Severe (+50%): -20% delivery income, +10% churn

**Regulatory (2)**
- AB5 Classification: -5% to -10% income
- Minimum Wage: +5% income, -15% volatility

**Tech Disruption (2)**
- Autonomous Vehicles: -5% rideshare (pilot phase)
- AI Optimization: +10% delivery efficiency

---

## Output Files

### `archetypes.json` (5.7 KB)

```json
{
  "metadata": {
    "generated_at": "2026-03-21T14:40:21",
    "source": "JPMorgan Chase Institute + Gridwise + industry research",
    "count": 5
  },
  "archetypes": [
    {
      "id": "volatile_vic",
      "name": "Volatile Vic",
      "base_mu": 1642.31,
      "base_sigma": 679.92,
      "coefficient_of_variation": 0.414,
      "platforms": ["doordash"],
      "hours_per_week": 45,
      "metro": "national",
      "default_risk_category": "high"
      // ... more fields
    }
    // ... 4 more archetypes
  ]
}
```

### `seasonality.json` (1.3 KB)

Monthly multipliers for each gig type:

```json
{
  "seasonality": {
    "delivery": {
      "jan": 1.05, "feb": 0.95, "mar": 1.15,
      "dec": 1.35  // Holiday peak
    }
  }
}
```

### `macro_params.json` (5.4 KB)

Shock scenarios with platform-specific impacts:

```json
{
  "scenarios": {
    "recession": {
      "recession_2020": {
        "name": "COVID-19 Recession",
        "duration_months": 2,
        "platform_impacts": {
          "rideshare": 0.40,  // -60%
          "delivery": 1.30    // +30%
        }
      }
    }
  }
}
```

### `expenses.json` (2.6 KB)

Expense structure and life event probabilities.

---

## Usage Examples

### Example 1: Load Archetype for Simulation

```python
from data_pipeline.loaders import load_archetype
import numpy as np

# Load gig worker persona
vic = load_archetype('volatile_vic')

# Extract parameters
mu = vic['base_mu']
sigma = vic['base_sigma']

# Run Monte Carlo simulation
n_simulations = 10000
n_months = 24

income_paths = np.random.normal(mu, sigma, (n_simulations, n_months))

# Calculate default probability
loan_amount = 5000
monthly_payment = loan_amount / 24
default_prob = (income_paths < monthly_payment * 2).any(axis=1).mean()

print(f"Default probability: {default_prob:.1%}")
```

### Example 2: Seasonal Adjustment

```python
from data_pipeline.loaders import get_seasonality

# Get delivery seasonality
months = ['jan', 'mar', 'jul', 'dec']
multipliers = [get_seasonality('delivery', m) for m in months]

print(f"Delivery income by month:")
for month, mult in zip(months, multipliers):
    print(f"  {month.capitalize()}: {mult:.2f}x")
# Output:
#   Jan: 1.05x
#   Mar: 1.15x (spike!)
#   Jul: 0.85x (summer lull)
#   Dec: 1.35x (holiday peak!)
```

### Example 3: Recession Scenario

```python
from data_pipeline.loaders import get_scenario, load_archetype

# Load baseline archetype
vic = load_archetype('volatile_vic')
base_mu = vic['base_mu']

# Apply recession shock
covid = get_scenario('recession', 'recession_2020')
delivery_impact = covid['platform_impacts']['delivery']  # 1.30

# Calculate adjusted income
shock_mu = base_mu * delivery_impact
delta = shock_mu - base_mu

print(f"Baseline: ${base_mu:,.0f}/month")
print(f"COVID shock: ${shock_mu:,.0f}/month ({delta:+.0f})")
# Output:
#   Baseline: $1,642/month
#   COVID shock: $2,135/month (+493)  # Delivery surged!
```

### Example 4: Compare All Archetypes

```python
from data_pipeline.loaders import DataLoader

loader = DataLoader()
archetypes = loader.list_archetypes()

print(f"{'Archetype':<20} {'Income (μ)':<12} {'CV':<8} {'Risk'}")
print("-" * 50)

for arch_id in archetypes:
    arch = loader.load_archetype(arch_id)
    print(f"{arch['name']:<20} ${arch['base_mu']:>9,.0f}  {arch['coefficient_of_variation']:>6.1%}  {arch['default_risk_category']}")
```

---

## Validation & Testing

### Run Validation Suite

```bash
python scripts/validate_pipeline.py
```

**Checks:**
- ✅ All archetypes have required fields
- ✅ Income parameters (μ, σ) are positive and reasonable
- ✅ Seasonality multipliers average to ~1.0
- ✅ Probabilities are in [0, 1] range
- ✅ Cross-file consistency (platforms match seasonality types)

### Run Integration Tests

```bash
python scripts/test_integration.py
```

**Tests:**
1. Static parameters validate
2. Calibration produces valid (μ, σ)
3. All 5 archetypes generate successfully
4. All 9 scenarios build correctly
5. All 4 JSON files export
6. Loaders can read all data
7. Monte Carlo simulation readiness

**Expected result:** `✓ ALL TESTS PASSED (7/7)`

---

## FAQ

**Q: Do I need a FRED API key?**  
A: No. The pipeline has fallback data. API key only needed for fetching latest macro data.

**Q: Can I add more archetypes?**  
A: Yes! Edit `transform/build_archetypes.py`, add a `create_your_archetype()` function, and re-run export.

**Q: How do I change metro areas?**  
A: Edit `ingest/metro_adjustments.py` to add/modify metro multipliers.

**Q: What if my simulation needs different parameters?**  
A: The loaders return full dictionaries. Access any field: `arch['skill_growth_rate']`, `arch['churn_risk']`, etc.

**Q: Can I use this for non-gig workers?**  
A: Yes! The calibration functions are generic. Just provide different hourly rates and variance multipliers.

---

## Troubleshooting

### Issue: `FileNotFoundError: archetypes.json`

**Solution:** Run export first:
```bash
python output/export_configs.py
```

### Issue: Validation warnings about high CV

**Solution:** This is expected for single-platform workers (Volatile Vic). The 41% CV comes from JPMorgan research on gig workers.

### Issue: FRED API timeout

**Solution:** Pipeline automatically falls back to cached/synthetic data. This is intentional for demo reliability.

---

## Credits & License

**Created for VarLend Hackathon Project**

Data sources:
- JPMorgan Chase Institute
- Gridwise
- Triplog
- Federal Reserve Economic Data (FRED)
- U.S. Bureau of Labor Statistics (BLS)

**License:** MIT (or specify your license)

---

## Next Steps

Once the data pipeline is complete, integrate with:

1. **Monte Carlo Simulation Engine**: Use `loaders.py` to feed parameters into income path generation
2. **Risk Scoring Model**: Build default probability calculator using archetype data
3. **Loan Optimization**: Find optimal loan amounts using risk curves
4. **Visualization Dashboard**: Display archetype comparisons and scenario impacts

**Happy simulating!** 🎉

# VarLend

**Risk assessment for gig workers with volatile income**

VarLend uses Monte Carlo simulation to distinguish income variance from actual default risk, enabling lending to gig workers that traditional banks reject.

---

## Project Status

✅ **Data Pipeline**: Complete  
⏳ **Monte Carlo Engine**: Ready for implementation  
⏳ **Life Simulation**: Ready for implementation  
⏳ **AI Layer**: Ready for implementation

---

## Quick Start

### Data Pipeline (Complete)

The data pipeline transforms research-backed parameters into simulation-ready JSON configs.

```bash
# Navigate to data pipeline
cd data_pipeline

# Setup (one-time)
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Generate all configuration files
python output/export_configs.py

# Validate
python scripts/validate_pipeline.py

# Test end-to-end
python scripts/test_integration.py
```

**Result:** 4 JSON files ready for Monte Carlo simulation

### Use the Data

```python
from data_pipeline.loaders import load_archetype, get_seasonality

# Load a gig worker persona
vic = load_archetype('volatile_vic')
mu = vic['base_mu']      # $1,642/month
sigma = vic['base_sigma']  # $680/month

# Apply seasonal adjustment
march_mult = get_seasonality('delivery', 'mar')  # 1.15x
adjusted_mu = mu * march_mult  # $1,889/month
```

---

## Architecture

```
VarLend/
├── data_pipeline/           ✅ COMPLETE
│   ├── ingest/              # Data acquisition (FRED, research params)
│   ├── transform/           # Calibration & archetype generation
│   ├── output/              # JSON export
│   ├── data/                # Generated configs (15.1 KB)
│   ├── loaders.py           # Data access interface
│   └── README.md            # Full documentation
│
├── monte_carlo/             ⏳ TODO: Core simulation engine
│   ├── simulation.py        # Income path generation
│   ├── risk_calculator.py   # Default probability
│   └── loan_optimizer.py    # Optimal loan sizing
│
├── life_simulation/         ⏳ TODO: Dynamic modeling
│   ├── event_engine.py      # Life events (car repair, health)
│   ├── seasonality.py       # Time-varying income
│   └── portfolio.py         # Platform diversification
│
├── ai_layer/                ⏳ TODO: Scenario generation
│   ├── scenario_parser.py   # Natural language → parameters
│   └── claude_client.py     # Claude API integration
│
└── visualization/           ⏳ TODO: Dashboard
    ├── dashboard.py         # Streamlit app
    └── charts.py            # Risk visualizations
```

---

## Data Pipeline Complete! ✅

### What's Been Built

1. **Static Parameters**: JPMorgan Chase + Gridwise research (36% CV, hourly rates, expenses)
2. **Metro Adjustments**: SF/NYC/Atlanta/Dallas/Rural income/expense multipliers
3. **FRED Integration**: Gas prices with fallback to cached data
4. **Calibration**: Research → (μ, σ) transformation for Monte Carlo
5. **Archetypes**: 5 gig worker personas (Volatile Vic, Steady Sarah, etc.)
6. **Scenarios**: 9 macro shocks (2008/2020 recessions, gas spikes, regulation)
7. **Export**: Clean JSON configs (4 files, 15.1 KB)
8. **Validation**: Quality checks + integration tests (7/7 passing)
9. **Loaders**: Simple interface for Monte Carlo consumption

### Key Metrics

- **5 Archetypes**: Income range $581-$3,948/month, CV 22.5%-41.4%
- **9 Scenarios**: Recession, gas spikes, regulatory changes, tech disruption
- **6 Metro Areas**: National baseline + 5 adjusted markets
- **12 Months**: Seasonality multipliers for delivery/rideshare/general gig
- **Citations**: Every parameter traceable to JPMorgan/Gridwise/FRED

### Example Usage

```python
# Integration with Monte Carlo (example)
from data_pipeline.loaders import load_archetype
import numpy as np

# Load archetype
vic = load_archetype('volatile_vic')
mu, sigma = vic['base_mu'], vic['base_sigma']

# Generate income paths
paths = np.random.normal(mu, sigma, (10000, 24))

# Calculate default probability
loan_payment = 250  # $250/month payment
default_prob = (paths.cumsum(axis=1) < paths.sum(axis=1, keepdims=True) * 0.15).any(axis=1).mean()

print(f"P(default) = {default_prob:.1%}")
```

---

## Next Steps

### Priority 1: Monte Carlo Engine

Build the core simulation:
- Income path generation (10k paths, 24 months)
- Default probability calculation
- Loan amount optimization
- Risk score generation

**Dependencies:** Just NumPy + data pipeline loaders

### Priority 2: Life Simulation

Add dynamic modeling:
- Monthly event sampling (car repair, health, platform deactivation)
- Seasonality application (Q4 surge, summer lull)
- Portfolio evolution (adding platforms over time)
- Macro shock triggers

**Dependencies:** Monte Carlo engine + scenario data

### Priority 3: AI Layer (Optional)

Natural language scenario generation:
- Claude API integration
- Prompt: "What if gas prices spike 40%?" → Parameter adjustments
- Comparative analysis (baseline vs. scenario)

**Dependencies:** Life simulation

### Priority 4: Visualization

Streamlit dashboard:
- Archetype comparison
- Risk curves
- Scenario impact charts
- Live AI scenario builder

**Dependencies:** All of above

---

## Documentation

- **Data Pipeline**: See [`data_pipeline/README.md`](data_pipeline/README.md) for complete documentation
- **Citations**: All sources documented with links
- **Examples**: Usage patterns for each component
- **Testing**: Validation and integration test suites

---

## Credits

**Data Sources:**
- JPMorgan Chase Institute (income volatility research)
- Gridwise (2025 gig worker earnings)
- Triplog (part-time/full-time income ranges)
- Federal Reserve Economic Data (FRED)
- U.S. Bureau of Labor Statistics (BLS)

**Hackathon Project**: VarLend - Risk assessment for gig workers

---

## Current Status Summary

```
✅ Data Pipeline: 100% complete (12/12 tasks)
   - All parameters calibrated
   - All archetypes generated
   - All scenarios built
   - All configs exported
   - All tests passing

⏳ Monte Carlo Engine: 0% (ready to start)
⏳ Life Simulation: 0% (ready to start)
⏳ AI Layer: 0% (optional)
⏳ Visualization: 0% (ready to start)

Total Project: ~15% complete
```

**Ready for hackathon:** Data pipeline is production-quality, fully tested, and documented. Monte Carlo implementation can proceed immediately with clean parameter access via loaders.

---

**Let's build the future of gig worker lending!** 🚀

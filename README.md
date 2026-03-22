# VarLend

**Risk assessment for gig workers with volatile income**

VarLend uses Monte Carlo simulation to distinguish income variance from actual default risk, enabling lending to gig workers that traditional banks reject.

---

## Project Status

✅ **Data Pipeline**: Complete  
✅ **Monte Carlo Engine**: Complete (by another developer)  
✅ **Life Simulation (Layer 2)**: Complete  
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

### Layer 2: Life Simulation Engine (Complete) ✅

The Life Simulation Engine generates realistic 24-month life trajectories with events, portfolio evolution, and macro shocks.

```bash
# Run test suite
cd life_simulation
python test_life_simulation.py

# Expected output: All 7 tests passing
```

**What Layer 2 Does:**
- **Event Sampling**: Probabilistically generates life events (vehicle repairs, health issues, platform deactivations)
- **Portfolio Evolution**: Models skill growth (logarithmic curve) and platform diversification (2.3 platforms @ month 12)
- **Macro Triggers**: Activates recession/gas spike scenarios based on baseline probabilities
- **Cascading Effects**: Major expenses → debt payments, health issues → reduced capacity
- **AIScenario Compilation**: Converts life trajectory into `ParameterShift` and `DiscreteJump` objects for Monte Carlo

**Example Usage:**

```python
from life_simulation.trajectory_builder import build_life_trajectory

# Generate a life trajectory
trajectory = build_life_trajectory('volatile_vic', n_months=24, random_seed=42)

print(f"Events: {len(trajectory.events)}")
print(f"Macro shock: {trajectory.macro_shock}")
print(f"Portfolio: {len(trajectory.portfolio_states[0].active_platforms)} → {len(trajectory.portfolio_states[-1].active_platforms)} platforms")

# AIScenario is ready for Monte Carlo
ai_scenario = trajectory.ai_scenario
print(f"Parameter shifts: {len(ai_scenario.parameter_shifts)}")
print(f"Discrete jumps: {len(ai_scenario.discrete_jumps)}")
```

**Integration with Monte Carlo:**

```python
from life_simulation.run_life_simulation import run_full_life_simulation
from monte_carlo_sim.src.integration.profile_builder import CustomerApplication
from monte_carlo_sim.src.types import LoanConfig

# Run combined Layer 1 + Layer 2 simulation
trajectory, result = run_full_life_simulation(
    archetype_id='steady_sarah',
    customer_application=customer,
    loan_config=LoanConfig(amount=5000, term_months=24, annual_rate=0.12),
    random_seed=42
)

print(f"P(default): {result.p_default:.2%}")
print(f"Risk tier: {result.recommended_loan.risk_tier.value}")
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
├── monte_carlo_sim/         ✅ COMPLETE
│   ├── src/engine/          # Core simulation engine
│   ├── src/types.py         # Data structures (WorkerProfile, AIScenario)
│   ├── src/integration/     # Data pipeline integration
│   ├── src/risk/            # Risk metrics & loan evaluation
│   └── main.py              # Standalone demo
│
├── life_simulation/         ✅ COMPLETE (Layer 2)
│   ├── types.py             # LifeEvent, PortfolioState, LifeTrajectory
│   ├── event_sampler.py     # Probabilistic life event generation
│   ├── portfolio_evolution.py # Skill growth & platform diversification
│   ├── macro_triggers.py    # Recession/gas spike activation
│   ├── cascading_effects.py # Event follow-on impacts
│   ├── scenario_converter.py # Trajectory → AIScenario
│   ├── trajectory_builder.py # Main orchestrator
│   ├── run_life_simulation.py # Layer 1 + Layer 2 integration
│   └── test_life_simulation.py # Comprehensive test suite
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

### Priority 1: AI Layer (Optional Enhancement)

Natural language scenario generation:
- Claude API integration
- Prompt: "What if gas prices spike 40%?" → Parameter adjustments
- Comparative analysis (baseline vs. scenario)

**Dependencies:** Life simulation complete ✅

### Priority 2: Visualization

Streamlit dashboard:
- Archetype comparison
- Risk curves (P(default) over time)
- Scenario impact charts
- Live trajectory visualization
- Life event timeline display

**Dependencies:** Monte Carlo + Life Simulation complete ✅

### Priority 3: Production Hardening

- API endpoints for loan evaluation
- Database integration for customer applications
- Performance optimization (parallel simulation)
- Deployment configuration

---

## Documentation

- **Data Pipeline**: See [`data_pipeline/README.md`](data_pipeline/README.md) for complete documentation
- **Monte Carlo Engine**: See [`monte_carlo_sim/README.md`](monte_carlo_sim/README.md) for simulation details
- **Life Simulation (Layer 2)**: Documented in module docstrings and test suite
- **Citations**: All sources documented with links
- **Examples**: Usage patterns for each component
- **Testing**: Comprehensive test suites for data pipeline and life simulation

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

✅ Monte Carlo Engine: 100% complete
   - Vectorized jump-diffusion model
   - Multi-stream correlation
   - Time-varying parameters (AIScenario support)
   - Default detection logic
   - Loan optimization

✅ Life Simulation (Layer 2): 100% complete (10/10 tasks)
   - Event sampling (vehicle, health, platform, housing, positive)
   - Portfolio evolution (skill growth, diversification)
   - Macro shock triggers (recession, gas spikes)
   - Cascading effects (debt, stress)
   - AIScenario compilation
   - Full integration with Monte Carlo
   - Comprehensive test suite (7/7 passing)

⏳ AI Layer: 0% (optional)
⏳ Visualization: 0% (ready to start)

Total Project: ~70% complete
```

**Ready for hackathon:** Three-layer architecture complete! Data pipeline, Monte Carlo simulation, and Life Simulation Engine are production-quality, fully tested, and integrated. The system can now model realistic gig worker trajectories with dynamic events and portfolio evolution.

---

**Let's build the future of gig worker lending!** 🚀

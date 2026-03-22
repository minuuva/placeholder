# Lasso - Volatility as Information, Not Risk

Monte Carlo risk assessment platform for gig worker loans. Transforms income volatility into actionable risk intelligence for banks, without relying on traditional credit scores.

## What Makes Lasso Different

Lasso is an **information expansion tool** for banks, not a decision engine. We provide comprehensive risk profiles through Monte Carlo simulation of income volatility, life events, and macro shocks - enabling banks to make informed lending decisions about gig workers who lack traditional credit histories.

## Architecture

Three-layer Monte Carlo simulation system:

- **Layer 1: Core Monte Carlo Engine** (`monte_carlo_sim/`) - Jump-diffusion income model with vectorized path simulation
- **Layer 2: Life Simulation Engine** (`life_simulation/`) - Probabilistic life events (vehicle repairs, health issues, platform disruptions) sampled per-path for true independence
- **Layer 3: AI Scenario Generator** (`ai_model/`) - Natural language scenario interpretation and risk summarization

## Tech Stack

**Backend (Python):**
- FastAPI REST API (`ai_model/api/server.py`)
- NumPy/SciPy for Monte Carlo simulation
- LLM integration (Claude/OpenAI) for natural language processing
- Matplotlib for visualization

**Frontend (Next.js):**
- React + TypeScript + Tailwind CSS
- Conversational UI for applicant data collection
- Real-time scenario stress testing
- Dynamic chart rendering

**Data Pipeline:**
- FRED API integration for macro data
- Pre-cached datasets (JPMorgan Institute, Gridwise Research)
- Platform-specific income/expense calibration

## Quick Start

### 1. Backend Setup

```bash
# From repo root
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set API key in .env
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# Run backend
python -m uvicorn ai_model.api.server:app --reload
```

Backend runs at `http://127.0.0.1:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install

# Set API keys in .env.local
cp .env.local.example .env.local
# Edit .env.local with your keys

npm run dev
```

Frontend runs at `http://localhost:3000`

## Visualization Output (5 Charts)

Lasso generates 5 visualizations for each risk assessment:

1. **Income Paths** - Monte Carlo trajectories with P10/P50/P90 bands and base income reference
2. **Life Event Timeline** - Probabilistic life events and their income/expense impacts
3. **Default Timing Analysis** - When defaults occur among defaulting paths (conditional percentiles)
4. **Income Parameter Evolution** - How mean income and volatility change over the life trajectory
5. **3D Risk Surface** - Default probability across loan amount/term combinations (shows optimization landscape)

## API Usage

### Simulate Endpoint

```bash
POST http://127.0.0.1:8000/api/simulate
```

Example request:

```json
{
  "query": "Assess risk for this applicant",
  "user_data": {
    "platforms": ["uber", "lyft"],
    "hours_per_week": 40,
    "metro_area": "san_francisco",
    "months_as_gig_worker": 18,
    "has_vehicle": true,
    "liquid_savings": 20000,
    "monthly_fixed_expenses": 500,
    "existing_debt_obligations": 1500
  },
  "loan_preferences": {
    "amount": 5000,
    "term_months": 6
  },
  "generate_charts": true
}
```

Response includes:
- **summary**: Detailed 300-500 word risk profile (LLM-generated)
- **quick_summary**: 2-3 sentence overview
- **metrics**: P(default), expected loss, CVaR 95%, risk tier
- **charts**: Array of chart metadata with paths
- **trajectory_info**: Life event sequence and portfolio evolution

## Key Features

### No Credit Scores
Lasso assesses risk entirely from gig work patterns, income volatility, emergency buffers, and platform diversification. Designed for workers excluded from traditional credit systems.

### True Path Independence
Each Monte Carlo path samples its own unique sequence of life events using Poisson/Bernoulli distributions. No batch determinism - every simulation is probabilistically independent.

### Scenario Stress Testing
Natural language scenario interface: "What if gas prices spike 40% in month 8?" The AI interprets scenarios and applies parameter shifts to the Monte Carlo engine.

### Information, Not Decisions
Lasso provides neutral risk assessment data. Banks make the final lending decision. No "Approve/Decline" language - only risk tiers (LOW, MODERATE, HIGH_RISK).

## Project Structure

```
.
├── ai_model/              # Layer 3: AI orchestration & API
│   ├── api/              # FastAPI endpoints
│   ├── prompts/          # LLM system prompts
│   └── visualization/    # Chart generation
├── monte_carlo_sim/       # Layer 1: Core simulation engine
│   └── src/
│       ├── engine/       # Monte Carlo engine + path events
│       ├── risk/         # Default detection & loan evaluation
│       └── profiles/     # Income modeling
├── life_simulation/       # Layer 2: Life trajectory builder
│   ├── trajectory_builder.py
│   ├── portfolio_evolution.py
│   └── macro_triggers.py
├── data_pipeline/         # Data ingestion & preprocessing
│   ├── data/             # Pre-cached datasets
│   └── transform/        # Income/expense calibration
└── frontend/              # Next.js web application
    ├── app/
    ├── components/
    └── lib/

```

## Development Notes

- Monte Carlo paths: 5000 (configurable)
- Time horizon: 24-36 months typical
- Random seed: 42 (for reproducibility during development)
- Chart filenames include unique `run_id` (timestamp) to prevent caching issues

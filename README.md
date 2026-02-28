# 🏁 AI Race Engineer

**Telemetry-driven probabilistic strategy decision system that replicates real pit wall workflows.**

Real Formula 1 telemetry → physics-informed tyre modeling → Monte Carlo simulation → AI-assisted reasoning.

> Built to demonstrate how AI/ML systems can support real-time decision-making in professional motorsport environments.

---

## The Problem

During a Formula 1 race, the pit wall has **seconds** to decide: *Do we pit now or stay out? 1-stop or 2-stop? How does a safety car change everything?*

These decisions depend on tyre degradation physics, probabilistic events (safety cars, weather), and compound-specific performance curves — all under extreme time pressure.

**This system automates that analysis.** It ingests real race telemetry, models tyre degradation, runs thousands of Monte Carlo simulations, and explains the optimal strategy through an AI agent grounded in simulation data (not hallucination).

---

## How It Works

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  FastF1          │────▶│  Feature Engineering  │────▶│  Strategy Engine     │
│  Telemetry API   │     │  Fuel correction      │     │  Lap time model      │
│  (Real F1 Data)  │     │  Degradation fitting  │     │  Piecewise tyre deg  │
│                  │     │  Cliff detection      │     │  Pit window optimizer │
└─────────────────┘     └──────────────────────┘     └─────────┬───────────┘
                                                               │
                                                               ▼
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Streamlit       │◀────│  LLM Tool-Calling    │◀────│  Monte Carlo Engine  │
│  Dashboard       │     │  Agent               │     │  Safety car sampling │
│  Interactive UI  │     │  RAG knowledge layer │     │  Degradation noise   │
│                  │     │  Simulation-grounded │     │  Win rate estimation │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
```

---

## Key Features

**📊 Physics-Informed Tyre Modeling**
Fuel-corrected degradation analysis with piecewise cliff detection. Compounds modeled with linear wear + quadratic cliff onset — matching real-world tyre behavior.

**🎲 Monte Carlo Strategy Simulation**
Probabilistic comparison of 1-stop vs 2-stop strategies under safety car uncertainty and degradation variance. Outputs win rates, confidence scores, and risk sensitivity.

**🤖 Tool-Calling AI Agent (No Hallucination)**
The LLM *never generates numbers*. It calls the simulation engine, receives structured results, and explains them. Every claim is backed by a simulation run.

**📚 RAG Knowledge Layer**
FIA regulations and strategy theory retrieved via ChromaDB embeddings. The agent cites rules and theory when answering questions.

**⚡ Vectorized Computation**
NumPy-vectorized lap time model with pre-computed stint caching. ~50-100x faster than naive Python loops.

**🔧 Configurable Parameters**
All constants extracted to `simulator/config.py`. No magic numbers — every threshold is documented, tunable, and version-controlled.

---

## Engineering Metrics

The system computes per-stint:

| Metric | Description |
|--------|-------------|
| `deg_slope_sec_per_lap` | Fuel-corrected linear degradation rate |
| `pace_drop` | Late-stint vs early-stint pace delta |
| `consistency_score` | Lap time standard deviation |
| `push_ratio` | Fraction of laps within 0.3s of personal best |
| `cliff_lap` | First lap with sudden degradation spike |

Fuel burn correction: **~0.035 sec/lap** applied to isolate tyre wear from fuel mass reduction.

---

## Lap Time Model

```
lap_time = base_lap_time
         + compound_pace_offset
         + degradation_slope × tyre_age
         + cliff_multiplier × max(0, tyre_age − cliff_onset)²
         + warmup_penalty
```

Includes compound-specific cliff onset (softs degrade non-linearly after ~18 laps, hards after ~42), warmup penalty for fresh tyres, and pit stop time loss.

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/YOUR_USERNAME/ai-race-engineer.git
cd ai-race-engineer
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Configure API key
echo "OPENAI_API_KEY=your-key-here" > .env

# Generate race data
python ingestion/load_session.py
python ingestion/detect_stints.py
python ingestion/compute_features.py

# Start API server
python -m uvicorn api.main:app --reload

# Launch dashboard (new terminal)
streamlit run dashboard.py
```

See [DEMO.md](DEMO.md) for detailed setup instructions and usage guide.

---

## Project Structure

```
simulator/
  ├── config.py          # All tunable parameters (no magic numbers)
  ├── strategy.py        # Vectorized Monte Carlo strategy engine
ingestion/
  ├── load_session.py    # FastF1 telemetry download
  ├── detect_stints.py   # Compound-based stint boundary detection
  ├── compute_features.py # Degradation feature extraction
agent/
  ├── chat_engineer.py   # Tool-calling LLM orchestration
  ├── tools.py           # Simulation tool interface
  ├── explainer.py       # Strategy explanation generator
  ├── rag.py             # ChromaDB retrieval layer
knowledge/               # FIA rules, strategy theory documents
api/
  └── main.py            # FastAPI endpoints
dashboard.py             # Streamlit web UI
docs/
  └── technical_design.md # Architecture & design decisions
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Monte Carlo over Bayesian | Small discrete search space; need probability distributions, not point estimates |
| Tool-calling over direct LLM | Prevents hallucination; every number traces to a simulation |
| Piecewise degradation | Captures real tyre cliff behavior with minimal parameters |
| RAG over fine-tuning | FIA rules change annually; RAG allows updates without retraining |
| NumPy vectorization | 50-100x speedup on inner simulation loop |

Full design rationale: [docs/technical_design.md](docs/technical_design.md)

---

## Technical Stack

Python · FastF1 · NumPy · Pandas · FastAPI · Streamlit · OpenAI (GPT-4o-mini) · ChromaDB · Sentence-Transformers

---

## Roadmap

- [ ] Multi-driver comparative analysis with undercut modeling
- [ ] Traffic and dirty-air lap time effects
- [ ] Thermal tyre model (track/ambient temperature)
- [ ] Multiple safety car windows per race
- [ ] Docker containerization for cloud deployment
- [ ] Live telemetry streaming integration

---

## License

MIT

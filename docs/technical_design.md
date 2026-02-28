# Technical Design Document

## AI Race Engineer — Architecture & Design Decisions

---

## 1. System Overview

The AI Race Engineer is a telemetry-driven strategy decision system that replicates the workflow of a professional motorsport pit wall. It ingests real race telemetry, models tyre degradation physics, simulates race strategies under uncertainty, and provides AI-assisted reasoning through a tool-calling LLM agent.

```
FastF1 Telemetry → Feature Engineering → Strategy Engine → Monte Carlo Simulation
                                                                    ↓
                                              LLM Tool-Calling Agent ← RAG Knowledge Layer
                                                                    ↓
                                                         Streamlit Dashboard
```

---

## 2. Design Decisions & Tradeoffs

### 2.1 Why Monte Carlo over Bayesian Optimization?

**Decision:** Monte Carlo sampling for strategy comparison.

**Rationale:**
- Race strategy has a small, discrete decision space (1-stop vs 2-stop, with ~50 valid pit laps). Bayesian optimization excels in large continuous spaces where function evaluations are expensive — neither condition applies here.
- Monte Carlo naturally models *stochastic events* (safety cars, degradation variance) as random draws, which maps directly to how uncertainty manifests in real races.
- The output is a probability distribution over outcomes, not a point estimate. This gives the engineer a *confidence score*, not just a recommendation — critical for risk assessment on the pit wall.
- Monte Carlo results are interpretable: "1-stop wins 72% of simulations" is directly actionable in a way that a Bayesian posterior over pit laps is not.

**Tradeoff:** Monte Carlo requires more iterations for convergence than optimization-based approaches. At 300 iterations with the current lap model, wall-clock time is acceptable (<2s). For real-time use during a race, iteration count can be reduced to 100 with minimal confidence loss.

### 2.2 Why LLM Tool-Calling over Direct Generation?

**Decision:** The LLM never generates strategy numbers. It calls a simulation tool and explains the results.

**Rationale:**
- LLMs hallucinate numerical outputs. A model asked "should we 1-stop or 2-stop?" will generate plausible but ungrounded answers. By forcing tool use, every number in the response traces back to a simulation run.
- This architecture separates *reasoning* (LLM) from *computation* (simulation engine). The LLM decides *when* to run a simulation and *how* to interpret results, but never fabricates race times or win rates.
- Tool-calling creates an auditable chain: user question → parameter extraction → simulation → structured result → explanation. Each step can be logged and verified independently.

**Tradeoff:** Latency increases (two LLM calls + simulation). For interactive use, this is acceptable. For batch analysis, the simulation can be called directly without the LLM layer.

### 2.3 Why Vectorized NumPy over Pure Python Loops?

**Decision:** Replaced nested Python `for` loops with NumPy array operations for lap time computation.

**Rationale:**
- The original implementation computed each lap time individually in Python loops. For a 2-stop simulation scanning ~1,200 pit lap combinations × 57 laps each, this means ~68,000 Python-level operations per strategy per MC iteration.
- NumPy vectorization computes entire stint lap times as array operations, leveraging C-level SIMD instructions. This yields 50-100x speedup on the inner loop.
- Pre-computing stint 1 cumulative times in the 2-stop simulator avoids redundant recalculation across the pit2 search dimension.

**Tradeoff:** Slightly less readable than the explicit loop version. Mitigated by comprehensive docstrings and the `_stint_times()` abstraction.

### 2.4 Why Piecewise Degradation over Pure Linear?

**Decision:** Tyre degradation uses a linear + quadratic cliff model.

**Rationale:**
- Real tyre degradation is non-linear. Tyres exhibit approximately linear wear for most of their life, then experience a sudden performance "cliff" as the rubber compound overheats or wears through to the carcass.
- The piecewise model: `deg = slope * age + cliff_mult * max(0, age - cliff_onset)²` captures this behavior with only two additional parameters per compound.
- The cliff parameters are configurable per compound (softs cliff earlier than hards) and can be overridden with telemetry-derived values.

**Tradeoff:** More parameters to calibrate. Defaults are set conservatively based on 2023 Bahrain GP data. For production use, cliff parameters should be fitted from practice session telemetry.

### 2.5 Why RAG over Fine-Tuning for Domain Knowledge?

**Decision:** Retrieval-Augmented Generation with ChromaDB for FIA rules and strategy theory.

**Rationale:**
- FIA regulations change annually. Fine-tuning would bake in stale rules. RAG allows updating the knowledge base without retraining.
- The knowledge corpus is small and well-structured (rules documents, strategy theory). Embedding-based retrieval is sufficient — no need for complex ranking.
- RAG provides *citations*: the LLM's response can reference specific rules or theory passages, increasing trustworthiness.

**Tradeoff:** Retrieval quality depends on chunk granularity and embedding model. Current implementation uses paragraph-level chunks with `all-MiniLM-L6-v2`. For a larger knowledge base, a more sophisticated chunking strategy would be needed.

---

## 3. Data Pipeline

### 3.1 Ingestion

```
FastF1 API → Raw Laps (parquet) → Stint Detection → Feature Engineering
```

- **FastF1** provides official FIA timing data with lap-level granularity.
- Laps are filtered by driver, sorted by lap number, and stored in columnar format (Parquet) for efficient analytical queries.
- Stint boundaries are detected by compound changes (not pit events, which can be noisy in the data).

### 3.2 Feature Engineering

Each stint produces a feature vector:

| Feature | Description | Unit |
|---------|-------------|------|
| `deg_slope_sec_per_lap` | Fuel-corrected degradation rate (linear fit) | sec/lap |
| `pace_drop` | Average last-3 laps minus first-3 laps | sec |
| `consistency_score` | Std deviation of corrected lap times | sec |
| `push_ratio` | Fraction of laps within 0.3s of best | ratio |
| `cliff_lap` | First lap with >0.25s sudden increase | lap number |

**Fuel correction** adds `0.035 × lap_number` to each lap time, normalizing out the ~0.035s/lap gain from fuel burn-off (~1.5kg/lap × ~0.023s/kg for F1 cars).

---

## 4. API Design

FastAPI was chosen for:
- Automatic OpenAPI/Swagger documentation (critical for demonstrating the system)
- Native async support for future concurrent simulation requests
- Pydantic validation on request parameters

Endpoints:
- `GET /drivers` — List available drivers in dataset
- `POST /recommend` — Run strategy simulation with parameters
- `POST /chat` — Interactive AI engineer conversation
- `GET /health` — Service health check

---

## 5. Configuration Philosophy

All numerical constants are extracted into `simulator/config.py`:
- `SimulationConfig` dataclass holds all tunable parameters
- `COMPOUNDS` dictionary holds per-compound tyre characteristics
- No magic numbers in business logic code

This enables:
- A/B testing different parameter sets
- Per-circuit configuration overrides
- Reproducible simulation results via config logging

---

## 6. Limitations & Future Work

### Current Limitations
- **Single-driver optimization:** Does not model traffic, undercuts, or position-relative strategy.
- **No tyre temperature model:** Degradation is distance-based, not thermal. Track temperature effects are not modeled.
- **Simplified safety car:** Binary SC event per race. Real races can have multiple SC periods with different timing impacts.
- **No DRS/dirty air modeling:** Lap times don't account for aerodynamic effects from nearby cars.

### Roadmap
- **Multi-driver comparative analysis** with position-aware strategy
- **Traffic and undercut modeling** using gap data from telemetry
- **Thermal tyre model** incorporating track/ambient temperature
- **Multiple safety car windows** with configurable probability curves
- **Containerized deployment** (Docker) for cloud-hosted demo
- **Live telemetry streaming** for real-time strategy updates during sessions

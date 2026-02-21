🏁 AI Race Engineer
Telemetry-Driven Probabilistic Strategy Decision System
📌 Overview

AI Race Engineer is an end-to-end motorsport decision intelligence system that combines:

Real Formula race telemetry ingestion (FastF1)

Physics-informed tyre degradation modeling

Deterministic race strategy simulation

Monte Carlo probabilistic modeling

LLM tool-calling orchestration

Interactive dashboard interface

The system replicates real pit-wall decision workflows used in professional racing environments.

🚀 Key Features

📊 Fuel-corrected tyre degradation analysis

🏎 1-stop vs 2-stop strategy optimizer

🎲 Monte Carlo safety car modeling

🤖 Tool-calling AI race engineer agent

💬 Interactive strategy chat interface

🖥 Streamlit web dashboard

🧠 Architecture
FastF1 Telemetry
        ↓
Feature Engineering
        ↓
Strategy Engine
        ↓
Monte Carlo Simulation
        ↓
Recommendation Engine
        ↓
LLM Tool-Calling Agent
        ↓
Streamlit Dashboard

📊 Engineering Metrics

The system computes:

Fuel-corrected degradation slope

Pace drop across stint

Consistency score

Push ratio

Tyre cliff detection

Fuel burn correction ≈ 0.035 sec/lap is applied to isolate tyre wear.

🏎 Strategy Model

Lap time model:

lap_time =
    base_lap_time
  + compound_offset
  + degradation_slope * tyre_age
  + warmup_penalty


Includes:

Tyre warmup penalty

Compound-specific degradation

Pit stop time loss

Safety car probability modeling

🎲 Monte Carlo Simulation

Each simulation run:

Applies safety car probability

Adjusts pit loss under safety car

Evaluates strategy outcome

Outputs:

Strategy win probabilities

Confidence score

Risk sensitivity

🤖 AI Tool-Calling Design

The LLM:

Parses user question

Extracts parameters

Calls strategy tool

Receives structured result

Generates grounded explanation

This prevents hallucination and ensures simulation-backed reasoning.

🖥 Dashboard

Run locally:

streamlit run dashboard.py


Allows:

Driver selection

Pit loss adjustment

Safety car probability tuning

Monte Carlo iteration control

Live AI strategy discussion

📂 Project Structure
ingestion/        → telemetry processing
simulator/        → strategy engine
agent/            → LLM orchestration
dashboard.py      → web UI
app.py            → standalone execution

🔬 Technical Highlights

Time-series telemetry analytics

Physics-informed simulation

Probabilistic modeling

LLM tool-calling orchestration

Secure environment variable management

Modular, extensible architecture

🛣 Roadmap

RAG knowledge layer (FIA rules, tyre theory)

Traffic and undercut modeling

Multi-driver comparative analysis

Containerized microservices

Cloud deployment
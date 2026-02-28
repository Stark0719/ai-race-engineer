"""
AI Race Engineer — FastAPI Backend
===================================
REST API for strategy simulation and AI chat.

Endpoints:
    GET  /health     — Service health check
    GET  /drivers    — List available drivers
    POST /recommend  — Run Monte Carlo strategy simulation
    POST /chat       — Interactive AI race engineer conversation
"""

from fastapi import FastAPI
import pandas as pd
import json
from datetime import datetime
from pathlib import Path

from simulator.strategy import recommend_strategy
from simulator.config import SimulationConfig
from agent.chat_engineer import chat_with_engineer
from agent.rag import load_documents


app = FastAPI(
    title="AI Race Engineer API",
    description="Telemetry-driven probabilistic race strategy engine",
    version="1.0.0",
)

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

# Load data at startup
features = pd.read_parquet("data/stint_features.parquet")
laps = pd.read_parquet("data/laps.parquet")
load_documents()

# Default simulation config
config = SimulationConfig()


@app.get("/health")
def health():
    return {
        "status": "ok",
        "drivers_loaded": len(features["Driver"].unique()),
        "laps_loaded": len(laps),
    }


@app.get("/drivers")
def list_drivers():
    return {"drivers": sorted(features["Driver"].unique().tolist())}


@app.post("/recommend")
def recommend(
    driver_code: str,
    pit_loss: float = 20,
    safety_car_prob: float = 0.2,
    iterations: int = 300,
):
    driver_laps = laps[laps["Driver"] == driver_code]
    base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()

    decision = recommend_strategy(
        iterations=iterations,
        total_laps=57,
        base_lap_time=base_lap_time,
        pit_loss_time=pit_loss,
        one_stop_compounds=("medium", "hard"),
        two_stop_compounds=("soft", "medium", "hard"),
        safety_car_prob=safety_car_prob,
        config=config,
    )

    # Log decision
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "driver": driver_code,
        "pit_loss": pit_loss,
        "safety_car_prob": safety_car_prob,
        "iterations": iterations,
        "decision": decision,
    }
    with open("logs/strategy_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return decision


@app.post("/chat")
def chat(driver_code: str, message: str):
    driver_laps = laps[laps["Driver"] == driver_code]
    base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()

    response = chat_with_engineer(
        user_message=message,
        driver_code=driver_code,
        base_lap_time=base_lap_time,
    )

    # Log conversation
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "driver": driver_code,
        "user_message": message,
        "response": response,
    }
    with open("logs/chat_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return {"response": response}

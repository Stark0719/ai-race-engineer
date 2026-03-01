"""
AI Race Engineer — FastAPI Backend v5
======================================
REST API + WebSocket with telemetry logging for post-race analysis.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import pandas as pd
import json
import asyncio
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

from simulator.strategy import recommend_strategy
from simulator.config import SimulationConfig, COMPOUNDS
from simulator.tracks.profiles import TRACKS
from agent.chat_engineer import chat_with_engineer
from agent.rag import load_documents
from live.car_simulator import LiveCarSimulator


app = FastAPI(title="AI Race Engineer API", version="5.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])

Path("logs").mkdir(exist_ok=True)
Path("static").mkdir(exist_ok=True)
if Path("static").exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")

features = pd.read_parquet("data/stint_features.parquet")
laps = pd.read_parquet("data/laps.parquet")
load_documents()
config = SimulationConfig()


# ---- Health & Info ----

@app.get("/health")
def health():
    return {"status": "ok", "tracks": list(TRACKS.keys())}


@app.get("/drivers")
def list_drivers():
    return {"drivers": sorted(features["Driver"].unique().tolist())}


@app.get("/tracks")
def list_tracks():
    return {
        "tracks": {
            key: {
                "name": t.name, "country": t.country,
                "total_laps": t.total_laps,
                "base_lap_time": t.base_lap_time_sec,
                "pit_loss": t.pit_loss_sec,
                "safety_car_prob": t.safety_car_probability,
                "circuit_length_m": t.circuit_length_m,
                "waypoints_xy": t.xy_points,
            }
            for key, t in TRACKS.items()
        }
    }


@app.get("/viewer")
def viewer():
    return FileResponse("static/viewer3d.html")


# ---- Strategy ----

@app.post("/recommend")
def recommend(driver_code: str, pit_loss: float = 20,
              safety_car_prob: float = 0.2, iterations: int = 300):
    driver_stints = features[features["Driver"] == driver_code]
    stint = driver_stints.iloc[0]
    real_deg = stint["deg_slope_sec_per_lap"]
    driver_laps = laps[laps["Driver"] == driver_code]
    base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()

    # Override medium compound degradation with real telemetry
    saved_deg = COMPOUNDS["medium"]["deg"]
    COMPOUNDS["medium"]["deg"] = real_deg

    decision = recommend_strategy(
        iterations=iterations, total_laps=57,
        base_lap_time=base_lap_time, pit_loss_time=pit_loss,
        one_stop_compounds=("medium", "hard"),
        two_stop_compounds=("soft", "medium", "hard"),
        safety_car_prob=safety_car_prob, config=config,
    )
    COMPOUNDS["medium"]["deg"] = saved_deg

    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "driver": driver_code, "pit_loss": pit_loss,
        "safety_car_prob": safety_car_prob,
        "iterations": iterations, "decision": decision,
    }
    with open("logs/strategy_logs.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return decision


# ---- Chat ----

@app.post("/chat")
def chat(driver_code: str, message: str):
    driver_laps = laps[laps["Driver"] == driver_code]
    base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()
    response = chat_with_engineer(
        user_message=message, driver_code=driver_code,
        base_lap_time=base_lap_time,
    )
    return {"response": response}


# ---- Live Telemetry WebSocket ----

@app.websocket("/ws/live/{track_key}")
async def live_telemetry(websocket: WebSocket, track_key: str):
    await websocket.accept()

    if track_key not in TRACKS:
        await websocket.send_json({"error": f"Unknown track: {track_key}"})
        await websocket.close()
        return

    try:
        start_msg = await asyncio.wait_for(websocket.receive_text(), timeout=10)
        start_cfg = json.loads(start_msg)
    except (asyncio.TimeoutError, json.JSONDecodeError):
        start_cfg = {}

    compound = start_cfg.get("compound", "medium")
    driver = start_cfg.get("driver", "VER")
    speed_multiplier = float(start_cfg.get("speed_multiplier", 10))
    pit_lap = int(start_cfg.get("pit_lap", 0))
    next_compound = start_cfg.get("next_compound", "hard")

    sim = LiveCarSimulator(track_key, compound=compound, driver=driver, config=config)
    if pit_lap > 0:
        sim.pit_stop_at_lap = pit_lap
        sim.next_compound = next_compound

    track = TRACKS[track_key]
    await websocket.send_json({
        "type": "track_info",
        "name": track.name, "country": track.country,
        "total_laps": track.total_laps,
        "waypoints_xy": track.xy_points,
        "track_width": track.track_width_m,
    })

    tick_rate = 10
    real_dt = 1.0 / tick_rate
    dt_sim = speed_multiplier * real_dt

    # Telemetry log for post-race analysis
    telemetry_log = []
    race_active = True

    try:
        while race_active and not sim.is_race_finished():
            sim.tick(dt_sim, real_dt=real_dt)
            frame = sim.generate_frame()
            fd = asdict(frame)
            fd["type"] = "telemetry"
            telemetry_log.append(fd)
            await websocket.send_json(fd)

            # Check for commands (non-blocking)
            try:
                msg = await asyncio.wait_for(websocket.receive_text(), timeout=0.001)
                data = json.loads(msg)
                cmd = data.get("command")
                if cmd == "pit":
                    sim.pit_stop(data.get("compound", "hard"))
                elif cmd == "stop":
                    race_active = False
                elif cmd == "speed":
                    speed_multiplier = float(data.get("value", speed_multiplier))
                    dt_sim = speed_multiplier * real_dt
            except asyncio.TimeoutError:
                pass

            await asyncio.sleep(real_dt)

        # Save telemetry log
        log_path = f"logs/telemetry_{track_key}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_path, "w") as f:
            json.dump(telemetry_log, f)

        await websocket.send_json({
            "type": "race_finished",
            "total_laps": sim.lap_number - 1,
            "total_time": round(sim.total_race_time, 2),
            "pit_history": sim.pit_history,
            "telemetry_log_path": log_path,
        })
    except WebSocketDisconnect:
        pass

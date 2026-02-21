import fastf1
import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
CACHE_DIR = BASE_DIR / "cache"
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

def load_race(season=2023, gp="Bahrain"):
    fastf1.Cache.enable_cache(CACHE_DIR)

    session = fastf1.get_session(season, gp, "R")
    session.load()

    laps = session.laps

    df = laps[[
        "Driver",
        "LapNumber",
        "LapTime",
        "Compound",
        "TyreLife",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time"
    ]].copy()

    df["LapTime"] = df["LapTime"].dt.total_seconds()
    df["Sector1Time"] = df["Sector1Time"].dt.total_seconds()
    df["Sector2Time"] = df["Sector2Time"].dt.total_seconds()
    df["Sector3Time"] = df["Sector3Time"].dt.total_seconds()

    output = DATA_DIR / "laps.parquet"
    df.to_parquet(output, index=False)

    print("Saved laps to", output)

if __name__ == "__main__":
    load_race()

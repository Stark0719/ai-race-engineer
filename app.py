"""
Standalone execution script.
Run strategy simulation for a single driver and print results.

Usage:
    python app.py
"""

import pandas as pd
from simulator.strategy import recommend_strategy
from simulator.config import COMPOUNDS, SimulationConfig
from agent.explainer import explain_strategy


def main():
    # Load telemetry-derived features
    features = pd.read_parquet("data/stint_features.parquet")
    laps = pd.read_parquet("data/laps.parquet")

    # Select driver
    driver_code = "VER"
    driver_stints = features[features["Driver"] == driver_code]
    stint = driver_stints.iloc[0]

    real_deg = stint["deg_slope_sec_per_lap"]
    print(f"\nDriver: {driver_code}")
    print(f"Fuel-corrected degradation: {real_deg:.4f} sec/lap")

    # Estimate base lap time from top-5 laps
    driver_laps = laps[laps["Driver"] == driver_code]
    base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()
    print(f"Base lap time (best 5 avg): {base_lap_time:.2f} sec")

    # Override medium compound degradation with telemetry-derived value
    COMPOUNDS["medium"]["deg"] = real_deg

    # Run strategy recommendation
    config = SimulationConfig()
    decision = recommend_strategy(
        iterations=300,
        total_laps=57,
        base_lap_time=base_lap_time,
        pit_loss_time=20,
        one_stop_compounds=("medium", "hard"),
        two_stop_compounds=("soft", "medium", "hard"),
        safety_car_prob=0.2,
        config=config,
    )

    # Print results
    print("\n--- Strategy Decision ---")
    print(f"Recommended:     {decision['recommended']}")
    print(f"Confidence:      {decision['confidence'] * 100:.1f}%")
    print(f"1-stop win rate: {decision['one_stop_win_rate'] * 100:.1f}%")
    print(f"2-stop win rate: {decision['two_stop_win_rate'] * 100:.1f}%")
    print(f"Mean delta:      {decision['mean_delta_seconds']:.2f}s")

    # AI explanation
    print("\n--- AI Race Engineer ---")
    explanation = explain_strategy(decision, driver_code)
    print(explanation)


if __name__ == "__main__":
    main()

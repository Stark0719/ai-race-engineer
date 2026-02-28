"""
Stint Feature Engineering
=========================
Extracts tyre degradation metrics from raw lap telemetry.
All thresholds are drawn from SimulationConfig (no magic numbers).
"""

import pandas as pd
import numpy as np
from simulator.config import SimulationConfig


def compute_stint_features(
    laps_path: str = "data/laps.parquet",
    stints_path: str = "data/stints.parquet",
    output_path: str = "data/stint_features.parquet",
    config: SimulationConfig = None,
):
    """
    Compute per-stint degradation features from lap data.

    Metrics computed:
    - deg_slope_sec_per_lap : fuel-corrected linear degradation rate
    - pace_drop             : delta between last-3 and first-3 lap averages
    - consistency_score     : std of fuel-corrected lap times (lower = better)
    - push_ratio            : fraction of laps within threshold of best lap
    - cliff_lap             : first lap where delta exceeds cliff threshold (or None)

    Parameters
    ----------
    laps_path : str
        Path to raw laps parquet file.
    stints_path : str
        Path to stint summary parquet file.
    output_path : str
        Path to write computed features.
    config : SimulationConfig
        Thresholds and constants. Uses defaults if None.
    """
    if config is None:
        config = SimulationConfig()

    laps = pd.read_parquet(laps_path)
    stints = pd.read_parquet(stints_path)
    laps = laps.sort_values(["Driver", "LapNumber"]).copy()

    features = []

    for _, stint in stints.iterrows():
        driver = stint["Driver"]
        stint_number = stint["stint_number"]

        stint_laps = laps[
            (laps["Driver"] == driver)
            & (laps["LapNumber"] >= stint["start_lap"])
            & (laps["LapNumber"] <= stint["end_lap"])
        ].copy()

        # Skip short stints
        if len(stint_laps) < config.min_stint_laps_for_features:
            continue

        # Remove warmup laps
        stint_laps = stint_laps.iloc[config.warmup_laps_to_discard:]

        # Remove slow laps (pit in/out, traffic, incidents)
        stint_laps = stint_laps[
            stint_laps["LapTime"] < stint_laps["LapTime"].quantile(config.outlier_quantile)
        ]

        if len(stint_laps) < 5:
            continue

        # Fuel correction: lighter car = faster, so we ADD fuel effect to normalize
        stint_laps["CorrectedLapTime"] = (
            stint_laps["LapTime"] + config.fuel_effect * stint_laps["LapNumber"]
        )

        # Linear degradation slope via least-squares fit
        x = stint_laps["LapNumber"].values
        y = stint_laps["CorrectedLapTime"].values
        slope, intercept = np.polyfit(x, y, 1)

        # Pace drop: average of last 3 laps minus average of first 3
        pace_drop = (
            stint_laps["CorrectedLapTime"].iloc[-3:].mean()
            - stint_laps["CorrectedLapTime"].iloc[:3].mean()
        )

        # Consistency: lower standard deviation = more consistent driver
        consistency = stint_laps["CorrectedLapTime"].std()

        # Push ratio: fraction of laps close to personal best
        best_lap = stint_laps["CorrectedLapTime"].min()
        push_laps = (stint_laps["CorrectedLapTime"] < best_lap + config.push_threshold).sum()
        push_ratio = push_laps / len(stint_laps)

        # Tyre cliff detection: first lap with sudden time increase
        lap_deltas = np.diff(stint_laps["CorrectedLapTime"].values)
        cliff_lap = None
        for i, delta in enumerate(lap_deltas):
            if delta > config.cliff_threshold:
                cliff_lap = int(stint_laps["LapNumber"].iloc[i + 1])
                break

        features.append({
            "Driver": driver,
            "stint_number": stint_number,
            "compound": stint["compound"],
            "lap_count": stint["lap_count"],
            "deg_slope_sec_per_lap": round(slope, 6),
            "pace_drop": round(pace_drop, 3),
            "consistency_score": round(consistency, 3),
            "push_ratio": round(push_ratio, 3),
            "cliff_lap": cliff_lap,
        })

    feature_df = pd.DataFrame(features)
    feature_df.to_parquet(output_path, index=False)

    print(f"Saved {len(feature_df)} stint features to {output_path}")
    print(feature_df.head())


if __name__ == "__main__":
    compute_stint_features()

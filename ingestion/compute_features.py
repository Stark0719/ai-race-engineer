import pandas as pd
import numpy as np

FUEL_EFFECT = 0.035  # seconds per lap


def compute_stint_features(
    laps_path="data/laps.parquet",
    stints_path="data/stints.parquet"
):
    laps = pd.read_parquet(laps_path)
    stints = pd.read_parquet(stints_path)

    laps = laps.sort_values(["Driver", "LapNumber"]).copy()

    features = []

    for _, stint in stints.iterrows():
        driver = stint["Driver"]
        stint_number = stint["stint_number"]

        stint_laps = laps[
            (laps["Driver"] == driver) &
            (laps["LapNumber"] >= stint["start_lap"]) &
            (laps["LapNumber"] <= stint["end_lap"])
        ].copy()

        # Ignore short stints
        if len(stint_laps) < 8:
            continue

        # Remove first 2 laps (warmup)
        stint_laps = stint_laps.iloc[2:]

        # Remove slow laps (pit in/out or traffic)
        stint_laps = stint_laps[
            stint_laps["LapTime"] < stint_laps["LapTime"].quantile(0.90)
        ]

        if len(stint_laps) < 5:
            continue

        # Fuel correction
        stint_laps["CorrectedLapTime"] = (
            stint_laps["LapTime"] +
            FUEL_EFFECT * stint_laps["LapNumber"]
        )

        # Degradation slope
        x = stint_laps["LapNumber"].values
        y = stint_laps["CorrectedLapTime"].values

        slope, intercept = np.polyfit(x, y, 1)

        # Pace drop
        pace_drop = (
            stint_laps["CorrectedLapTime"].iloc[-3:].mean() -
            stint_laps["CorrectedLapTime"].iloc[:3].mean()
        )

        # Consistency
        consistency = stint_laps["CorrectedLapTime"].std()

        # Push ratio
        best_lap = stint_laps["CorrectedLapTime"].min()
        push_laps = (
            stint_laps["CorrectedLapTime"] < best_lap + 0.3
        ).sum()
        push_ratio = push_laps / len(stint_laps)

        # Tyre cliff detection
        lap_deltas = np.diff(stint_laps["CorrectedLapTime"].values)

        cliff_lap = None
        for i, delta in enumerate(lap_deltas):
            if delta > 0.25:  # 0.25 sec sudden jump
                cliff_lap = int(stint_laps["LapNumber"].iloc[i + 1])
                break

        features.append({
            "Driver": driver,
            "stint_number": stint_number,
            "compound": stint["compound"],
            "lap_count": stint["lap_count"],
            "deg_slope_sec_per_lap": slope,
            "pace_drop": pace_drop,
            "consistency_score": consistency,
            "push_ratio": push_ratio,
            "cliff_lap": cliff_lap
        })

    feature_df = pd.DataFrame(features)
    feature_df.to_parquet("data/stint_features.parquet", index=False)

    print("Saved stint features to data/stint_features.parquet")
    print(feature_df.head())


if __name__ == "__main__":
    compute_stint_features()

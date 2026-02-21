import pandas as pd

def detect_stints(laps_path="data/laps.parquet"):
    df = pd.read_parquet(laps_path)

    df = df.sort_values(["Driver", "LapNumber"]).copy()

    # Identify compound changes per driver
    df["compound_change"] = (
        df.groupby("Driver")["Compound"]
        .apply(lambda x: x != x.shift(1))
        .reset_index(level=0, drop=True)
    )

    # Create stint_id counter per driver
    df["stint_number"] = (
        df.groupby("Driver")["compound_change"]
        .cumsum()
    )

    # Build stint summary
    stint_summary = (
        df.groupby(["Driver", "stint_number"])
        .agg(
            compound=("Compound", "first"),
            start_lap=("LapNumber", "min"),
            end_lap=("LapNumber", "max"),
            lap_count=("LapNumber", "count"),
            avg_lap_time=("LapTime", "mean"),
            best_lap_time=("LapTime", "min")
        )
        .reset_index()
    )

    stint_summary.to_parquet("data/stints.parquet", index=False)

    print("Saved stint summary to data/stints.parquet")
    print(stint_summary.head())

if __name__ == "__main__":
    detect_stints()

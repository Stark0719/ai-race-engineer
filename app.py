import pandas as pd
from simulator.strategy import recommend_strategy, COMPOUNDS

# ----------------------------------
# 1️⃣ Load real stint features
# ----------------------------------

features = pd.read_parquet("data/stint_features.parquet")

# Choose driver
driver_code = "VER"

driver_stints = features[features["Driver"] == driver_code]

# Use first stint as reference
stint = driver_stints.iloc[0]

real_deg = stint["deg_slope_sec_per_lap"]

print(f"\nDriver: {driver_code}")
print(f"Fuel-corrected degradation: {real_deg:.4f} sec/lap")

# ----------------------------------
# 2️⃣ Estimate base lap time
# ----------------------------------

laps = pd.read_parquet("data/laps.parquet")

driver_laps = laps[laps["Driver"] == driver_code]

base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()

print(f"Base lap time (best lap): {base_lap_time:.2f} sec")

# ----------------------------------
# 3️⃣ Override compound degradation
# ----------------------------------

COMPOUNDS["medium"]["deg"] = real_deg

# ----------------------------------
# 4️⃣ Run strategy recommendation
# ----------------------------------

decision = recommend_strategy(
    iterations=300,
    total_laps=57,
    base_lap_time=base_lap_time,
    pit_loss_time=20,
    one_stop_compounds=("medium", "hard"),
    two_stop_compounds=("soft", "medium", "hard"),
    safety_car_prob=0.2
)

# ----------------------------------
# 5️⃣ Print clean decision
# ----------------------------------

print("\nStrategy Decision")
print("-------------------")
print(f"Recommended: {decision['recommended']}")
print(f"Confidence: {decision['confidence']*100:.1f}%")
print(f"1-stop win rate: {decision['one_stop_win_rate']*100:.1f}%")
print(f"2-stop win rate: {decision['two_stop_win_rate']*100:.1f}%")

from agent.explainer import explain_strategy

print("\nAI Race Engineer Explanation")
print("------------------------------")

explanation = explain_strategy(decision, driver_code)

print(explanation)



# # from simulator.strategy import simulate_one_stop_compound

# # pit_lap, race_time = simulate_one_stop_compound(
# #     total_laps=57,
# #     base_lap_time=92,
# #     pit_loss_time=20,
# #     compound_1="soft",
# #     compound_2="medium"
# # )

# # print("Best pit lap:", pit_lap)
# # print("Predicted race time:", race_time)


# from simulator.strategy import simulate_one_stop_compound, simulate_two_stop

# # 1 stop
# pit_lap, time_1stop = simulate_one_stop_compound(
#     total_laps=57,
#     base_lap_time=92,
#     pit_loss_time=15,
#     compound_1="medium",
#     compound_2="hard"
# )

# # 2 stop
# pits, time_2stop = simulate_two_stop(
#     total_laps=57,
#     base_lap_time=92,
#     pit_loss_time=15,
#     compound_1="soft",
#     compound_2="medium",
#     compound_3="hard"
# )

# print("1-stop:", pit_lap, time_1stop)
# print("2-stop:", pits, time_2stop)

# if time_1stop < time_2stop:
#     print("Recommended: 1 stop")
# else:
#     print("Recommended: 2 stop")
    

# from simulator.strategy import monte_carlo_compare

# result = monte_carlo_compare(
#     iterations=300,
#     total_laps=57,
#     base_lap_time=92,
#     pit_loss_time=20,
#     one_stop_compounds=("medium", "hard"),
#     two_stop_compounds=("soft", "medium", "hard"),
#     safety_car_prob=0.2
# )

# print(result)

# from simulator.strategy import recommend_strategy

# decision = recommend_strategy(
#     iterations=300,
#     total_laps=57,
#     base_lap_time=92,
#     pit_loss_time=20,
#     one_stop_compounds=("medium", "hard"),
#     two_stop_compounds=("soft", "medium", "hard"),
#     safety_car_prob=0.2
# )

# print(decision)


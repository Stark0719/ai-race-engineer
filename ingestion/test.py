import pandas as pd
#stints 
stints = pd.read_parquet("data/stints.parquet")

print(stints[stints["Driver"] == "VER"])

#deg_slop_sec_per_lap
# f = pd.read_parquet("data/stint_features.parquet")
# print(f[f["Driver"] == "VER"])


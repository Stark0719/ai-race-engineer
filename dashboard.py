import streamlit as st
import requests

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Race Engineer", layout="wide")
st.title("🏁 AI Race Engineer Console")

# ---------------------------------
# Load drivers from API
# ---------------------------------

drivers_response = requests.get(f"{API_BASE}/drivers")
drivers = drivers_response.json()["drivers"]

# ---------------------------------
# Sidebar Controls
# ---------------------------------

st.sidebar.header("Simulation Controls")

driver_code = st.sidebar.selectbox("Select Driver", drivers)
pit_loss = st.sidebar.slider("Pit Loss (seconds)", 5, 30, 20)
safety_car_prob = st.sidebar.slider("Safety Car Probability", 0.0, 0.5, 0.2)
iterations = st.sidebar.slider("Monte Carlo Iterations", 100, 1000, 300)

# ---------------------------------
# Run Strategy Simulation
# ---------------------------------

if st.button("Run Strategy Simulation"):

    response = requests.post(
        f"{API_BASE}/recommend",
        params={
            "driver_code": driver_code,
            "pit_loss": pit_loss,
            "safety_car_prob": safety_car_prob,
            "iterations": iterations
        }
    )

    decision = response.json()

    st.subheader("📊 Strategy Recommendation")

    col1, col2, col3 = st.columns(3)

    col1.metric("Recommended", decision["recommended"])
    col2.metric("Confidence", f"{decision['confidence']*100:.1f}%")
    col3.metric("1-stop Win Rate", f"{decision['one_stop_win_rate']*100:.1f}%")

    st.divider()

# ---------------------------------
# Chat Section
# ---------------------------------

st.subheader("💬 Ask the AI Race Engineer")

user_input = st.text_input("Enter your question:")

if user_input:

    chat_response = requests.post(
        f"{API_BASE}/chat",
        params={
            "driver_code": driver_code,
            "message": user_input
        }
    )

    st.write(chat_response.json()["response"])


# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
# from simulator.strategy import recommend_strategy, COMPOUNDS
# # from agent.explainer import explain_strategy

# import requests

# API_BASE = "http://127.0.0.1:8000"

# st.set_page_config(page_title="AI Race Engineer", layout="wide")

# st.title("🏁 AI Race Engineer Console")

# # ---------------------------------
# # Load data
# # ---------------------------------

# features = pd.read_parquet("data/stint_features.parquet")
# laps = pd.read_parquet("data/laps.parquet")

# drivers = sorted(features["Driver"].unique())

# # ---------------------------------
# # Sidebar controls
# # ---------------------------------

# st.sidebar.header("Simulation Controls")

# driver_code = st.sidebar.selectbox("Select Driver", drivers)

# pit_loss = st.sidebar.slider("Pit Loss (seconds)", 5, 30, 20)

# safety_car_prob = st.sidebar.slider("Safety Car Probability", 0.0, 0.5, 0.2)

# iterations = st.sidebar.slider("Monte Carlo Iterations", 100, 1000, 300)

# # ---------------------------------
# # Extract Driver Data
# # ---------------------------------

# # driver_stints = features[features["Driver"] == driver_code]
# # stint = driver_stints.iloc[0]

# # real_deg = stint["deg_slope_sec_per_lap"]

# # driver_laps = laps[laps["Driver"] == driver_code]
# # base_lap_time = driver_laps.nsmallest(5, "LapTime")["LapTime"].mean()

# # # Override compound degradation
# # COMPOUNDS["medium"]["deg"] = real_deg

# # ---------------------------------
# # Run Simulation
# # ---------------------------------

# if st.button("Run Strategy Simulation"):

#     response = requests.post(
#         f"{API_BASE}/recommend",
#         params={
#             "driver_code": driver_code,
#             "pit_loss": pit_loss,
#             "safety_car_prob": safety_car_prob,
#             "iterations": iterations
#         }
#     )

#     decision = response.json()


#     st.subheader("📊 Strategy Recommendation")

#     col1, col2, col3 = st.columns(3)

#     col1.metric("Recommended", decision["recommended"])
#     col2.metric("Confidence", f"{decision['confidence']*100:.1f}%")
#     col3.metric("1-stop Win Rate", f"{decision['one_stop_win_rate']*100:.1f}%")

#     st.divider()

#     st.subheader("🧠 AI Race Engineer Explanation")

#     explanation = explain_strategy(decision, driver_code)

#     st.write(explanation)
    
#     labels = ["1-stop", "2-stop"]
#     values = [
#         decision["one_stop_win_rate"] * 100,
#         decision["two_stop_win_rate"] * 100
#     ]

#     fig, ax = plt.subplots()
#     ax.bar(labels, values)
#     ax.set_ylabel("Win Rate (%)")
#     ax.set_title("Strategy Win Probability")

#     st.pyplot(fig)
# from agent.chat_engineer import chat_with_engineer

# st.divider()
# st.subheader("💬 Ask the AI Race Engineer")

# user_input = st.text_input("Enter your question:")

# if user_input:

#     chat_response = requests.post(
#         f"{API_BASE}/chat",
#         params={
#             "driver_code": driver_code,
#             "message": user_input
#         }
#     )

#     st.write(chat_response.json()["response"])


#     st.write(response)

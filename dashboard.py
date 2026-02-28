"""
AI Race Engineer — Streamlit Dashboard
=======================================
Interactive strategy simulation console with visualization.
Connects to the FastAPI backend for simulation and AI chat.
"""

import streamlit as st
import requests
import plotly.graph_objects as go

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="AI Race Engineer", layout="wide")
st.title("🏁 AI Race Engineer Console")

# ---------------------------------
# Load drivers from API
# ---------------------------------

try:
    drivers_response = requests.get(f"{API_BASE}/drivers", timeout=5)
    drivers = drivers_response.json()["drivers"]
except requests.exceptions.ConnectionError:
    st.error("Cannot connect to API. Start the backend with: `python -m uvicorn api.main:app --reload`")
    st.stop()

# ---------------------------------
# Sidebar Controls
# ---------------------------------

st.sidebar.header("⚙️ Simulation Controls")

driver_code = st.sidebar.selectbox("Select Driver", drivers)
pit_loss = st.sidebar.slider("Pit Loss (seconds)", 5, 30, 20)
safety_car_prob = st.sidebar.slider("Safety Car Probability", 0.0, 0.5, 0.2, step=0.05)
iterations = st.sidebar.slider("Monte Carlo Iterations", 100, 1000, 300, step=100)

st.sidebar.markdown("---")
st.sidebar.caption("Adjust parameters and run simulation to see strategy recommendations.")

# ---------------------------------
# Run Strategy Simulation
# ---------------------------------

if st.button("🏎️ Run Strategy Simulation", type="primary"):

    with st.spinner("Running Monte Carlo simulation..."):
        response = requests.post(
            f"{API_BASE}/recommend",
            params={
                "driver_code": driver_code,
                "pit_loss": pit_loss,
                "safety_car_prob": safety_car_prob,
                "iterations": iterations,
            },
        )

    decision = response.json()

    # --- Metrics Row ---
    st.subheader("📊 Strategy Recommendation")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Recommended", decision["recommended"])
    col2.metric("Confidence", f"{decision['confidence'] * 100:.1f}%")
    col3.metric("1-Stop Win Rate", f"{decision['one_stop_win_rate'] * 100:.1f}%")
    col4.metric("2-Stop Win Rate", f"{decision['two_stop_win_rate'] * 100:.1f}%")

    # --- Charts Row ---
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        # Win rate comparison bar chart
        fig_bar = go.Figure(data=[
            go.Bar(
                x=["1-Stop", "2-Stop"],
                y=[decision["one_stop_win_rate"] * 100, decision["two_stop_win_rate"] * 100],
                marker_color=["#2196F3", "#FF9800"],
                text=[f"{decision['one_stop_win_rate'] * 100:.1f}%",
                      f"{decision['two_stop_win_rate'] * 100:.1f}%"],
                textposition="outside",
            )
        ])
        fig_bar.update_layout(
            title="Strategy Win Probability",
            yaxis_title="Win Rate (%)",
            yaxis_range=[0, 100],
            height=350,
            margin=dict(t=50, b=30),
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with chart_col2:
        # Mean race time comparison
        if "one_stop_mean_time" in decision:
            fig_time = go.Figure(data=[
                go.Bar(
                    x=["1-Stop", "2-Stop"],
                    y=[decision["one_stop_mean_time"], decision["two_stop_mean_time"]],
                    marker_color=["#2196F3", "#FF9800"],
                    text=[f"{decision['one_stop_mean_time']:.1f}s",
                          f"{decision['two_stop_mean_time']:.1f}s"],
                    textposition="outside",
                )
            ])
            fig_time.update_layout(
                title="Mean Race Time",
                yaxis_title="Total Race Time (sec)",
                height=350,
                margin=dict(t=50, b=30),
            )
            st.plotly_chart(fig_time, use_container_width=True)

    # --- Detailed Stats ---
    if "mean_delta_seconds" in decision:
        st.markdown("---")
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        detail_col1.metric("Mean Time Delta", f"{decision['mean_delta_seconds']:.2f}s",
                          help="Negative = 1-stop faster on average")
        detail_col2.metric("Delta Std Dev", f"{decision['std_delta_seconds']:.2f}s",
                          help="Uncertainty in time difference between strategies")
        detail_col3.metric("Iterations", f"{decision['iterations']}")

    st.divider()

# ---------------------------------
# Chat Section
# ---------------------------------

st.subheader("💬 Ask the AI Race Engineer")
st.caption("Try: 'What happens if pit loss drops to 12 seconds?' or 'Is 2-stop better under safety car?'")

user_input = st.text_input("Enter your question:", placeholder="e.g., Explain undercut strategy")

if user_input:
    with st.spinner("Analyzing..."):
        chat_response = requests.post(
            f"{API_BASE}/chat",
            params={"driver_code": driver_code, "message": user_input},
        )

    st.markdown(chat_response.json()["response"])

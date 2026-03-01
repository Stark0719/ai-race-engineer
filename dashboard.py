"""
AI Race Engineer — Unified Dashboard v6
=========================================
Two tabs:
  📊 Strategy Simulation — Monte Carlo + AI chat
  🏎️ Live Telemetry — real-time sim, track map, charts, export, post-race analysis

Run:
    python -m uvicorn api.main:app --reload
    streamlit run dashboard.py
"""

import streamlit as st
import json
import requests
import plotly.graph_objects as go
import streamlit.components.v1 as stc
from collections import deque

API_BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"
COMPOUND_COLORS = {"soft": "#FF3333", "medium": "#FFD700", "hard": "#CCCCCC"}

st.set_page_config(page_title="AI Race Engineer", layout="wide")
st.title("🏁 AI Race Engineer Console")

try:
    drivers = requests.get(f"{API_BASE}/drivers", timeout=3).json()["drivers"]
    tracks_data = requests.get(f"{API_BASE}/tracks", timeout=3).json()["tracks"]
except Exception:
    st.error("❌ Cannot connect to API. Run: `python -m uvicorn api.main:app --reload`")
    st.stop()

for key in ["race_running", "telemetry_data", "lap_times"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key != "race_running" else False

tab_strategy, tab_live = st.tabs(["📊 Strategy Simulation", "🏎️ Live Telemetry"])

# =================================================================
# TAB 1 — STRATEGY SIMULATION
# =================================================================
with tab_strategy:
    st.sidebar.header("⚙️ Strategy Controls")
    driver_code = st.sidebar.selectbox("Driver", drivers)
    pit_loss = st.sidebar.slider("Pit Loss (sec)", 5, 30, 20)
    safety_car_prob = st.sidebar.slider("Safety Car Prob", 0.0, 0.5, 0.2, step=0.05)
    iterations = st.sidebar.number_input("Monte Carlo Iterations", 50, 5000, 300, step=50)

    if st.button("🏎️ Run Strategy Simulation", type="primary"):
        with st.spinner(f"Running {iterations} iterations..."):
            resp = requests.post(f"{API_BASE}/recommend", params={
                "driver_code": driver_code, "pit_loss": pit_loss,
                "safety_car_prob": safety_car_prob, "iterations": iterations})
        d = resp.json()

        st.subheader("📊 Strategy Recommendation")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Recommended", d["recommended"])
        c2.metric("Confidence", f"{d['confidence']*100:.1f}%")
        c3.metric("1-Stop Win", f"{d['one_stop_win_rate']*100:.1f}%")
        c4.metric("2-Stop Win", f"{d['two_stop_win_rate']*100:.1f}%")

        ch1, ch2 = st.columns(2)
        with ch1:
            fig = go.Figure(data=[go.Bar(
                x=["1-Stop", "2-Stop"],
                y=[d["one_stop_win_rate"]*100, d["two_stop_win_rate"]*100],
                marker_color=["#2196F3", "#FF9800"],
                text=[f"{d['one_stop_win_rate']*100:.1f}%",
                      f"{d['two_stop_win_rate']*100:.1f}%"],
                textposition="outside")])
            fig.update_layout(title="Win Probability", yaxis_title="%",
                             yaxis_range=[0, 100], height=350)
            st.plotly_chart(fig, use_container_width=True)
        with ch2:
            st.markdown(f"""
**Parameters:** {driver_code} | Pit loss {d['pit_loss']}s | SC {d['safety_car_probability']*100:.0f}% | {iterations} runs

**Result:** **{d['recommended']}** wins **{d['confidence']*100:.1f}%** of simulations.

{"⚠️ Low confidence — consider track position." if d['confidence'] < 0.65 else "✅ High confidence."}
""")

    st.divider()
    st.subheader("💬 AI Race Engineer")
    st.caption("Try: 'What if pit loss is 12s?' · 'Explain undercut' · 'Is 2-stop better with safety car?'")
    user_q = st.text_input("Question:", placeholder="e.g. Explain undercut strategy")
    if user_q:
        with st.spinner("Analyzing..."):
            r = requests.post(f"{API_BASE}/chat",
                              params={"driver_code": driver_code, "message": user_q})
        st.markdown(r.json()["response"])

# =================================================================
# TAB 2 — LIVE TELEMETRY
# =================================================================
with tab_live:
    st.sidebar.markdown("---")
    st.sidebar.header("🏎️ Live Race Config")

    track_keys = list(tracks_data.keys())
    track_key = st.sidebar.selectbox("Track", track_keys,
        format_func=lambda k: f"{tracks_data[k]['name']} ({tracks_data[k]['country']})")
    ti = tracks_data[track_key]

    compound = st.sidebar.selectbox("Start Compound", ["soft", "medium", "hard"], index=1)
    speed_mult = st.sidebar.slider("Sim Speed (×)", 1, 50, 10)
    pit_lap = st.sidebar.number_input("Pit on Lap (0=none)", 0, ti["total_laps"], 0)
    next_compound = st.sidebar.selectbox("Pit to", ["soft", "medium", "hard"], index=2)
    st.sidebar.info(f"**{ti['name']}**\n{ti['circuit_length_m']/1000:.1f}km · "
                    f"{ti['total_laps']} laps · SC {ti['safety_car_prob']*100:.0f}%")

    wps = ti["waypoints_xy"]
    tx = [p[0] for p in wps] + [wps[0][0]]
    ty = [p[1] for p in wps] + [wps[0][1]]

    c_start, c_stop, c_export = st.columns(3)
    if c_start.button("🟢 Start Race", type="primary", use_container_width=True):
        st.session_state.race_running = True
        st.session_state.telemetry_data = []
        st.session_state.lap_times = []
    if c_stop.button("🔴 Stop Race", use_container_width=True):
        st.session_state.race_running = False
    if st.session_state.telemetry_data:
        c_export.download_button("📥 Export Data",
            data=json.dumps(st.session_state.telemetry_data),
            file_name=f"telemetry_{track_key}.json",
            mime="application/json", use_container_width=True)

    status_ph = st.empty()

    # ---- 3D Live Car View (embedded from FastAPI) ----
    st.subheader("🎮 3D Live Car Simulation")
    st.caption("🖱️ Drag to orbit camera • Scroll to zoom • "
               "[Open fullscreen ↗](http://127.0.0.1:8000/viewer)")
    stc.iframe(f"{API_BASE}/viewer", height=500, scrolling=False)

    # ---- Track map + Metrics side by side ----
    map_col, met_col = st.columns([3, 2])
    with map_col:
        map_ph = st.empty()
    with met_col:
        metrics_ph = st.empty()
    ch_l, ch_r = st.columns(2)
    with ch_l:
        speed_ph = st.empty()
    with ch_r:
        tyre_ph = st.empty()
    lap_ph = st.empty()
    strat_ph = st.empty()

    def make_map(cx=None, cy=None, cpd="medium"):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tx, y=ty, mode="lines",
            line=dict(width=8, color="#444"), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=[wps[0][0]], y=[wps[0][1]], mode="markers",
            marker=dict(size=12, color="white", symbol="square",
                       line=dict(width=2, color="#666")), showlegend=False))
        if cx is not None:
            fig.add_trace(go.Scatter(x=[cx], y=[cy], mode="markers",
                marker=dict(size=18, color=COMPOUND_COLORS.get(cpd, "#0f0"),
                           line=dict(width=3, color="white")), showlegend=False))
        fig.update_layout(
            xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False,
                       zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
            margin=dict(l=5, r=5, t=5, b=5), height=400)
        return fig

    map_ph.plotly_chart(make_map(), use_container_width=True, key="map_init")

    # ---- RACE LOOP ----
    if st.session_state.race_running:
        try:
            from websocket import create_connection, WebSocketTimeoutException
        except ImportError:
            st.error("Run: `pip install websocket-client`")
            st.session_state.race_running = False
            st.stop()

        status_ph.info("🏎️ Connecting...")
        try:
            ws = create_connection(f"{WS_BASE}/ws/live/{track_key}", timeout=5)
            ws.send(json.dumps({"compound": compound, "driver": "VER",
                "speed_multiplier": speed_mult,
                "pit_lap": pit_lap, "next_compound": next_compound}))

            track_msg = json.loads(ws.recv())
            total_laps = track_msg.get("total_laps", ti["total_laps"])
            status_ph.success(f"🟢 {track_msg.get('name','')} — {total_laps} laps @ {speed_mult}×")

            spd_buf = deque(maxlen=300)
            tmp_buf = deque(maxlen=300)
            prev_lap = 1
            fn = 0
            uk = 0

            while st.session_state.race_running:
                try:
                    ws.settimeout(2.0)
                    raw = ws.recv()
                    data = json.loads(raw)
                except WebSocketTimeoutException:
                    continue
                except Exception:
                    break

                if data.get("type") == "race_finished":
                    status_ph.success(
                        f"🏁 Finished! {data['total_laps']} laps — {data['total_time']:.1f}s")
                    st.session_state.race_running = False
                    break
                if data.get("type") != "telemetry":
                    continue

                fn += 1
                st.session_state.telemetry_data.append(data)
                spd_buf.append(data["speed_kph"])
                tmp_buf.append(data["tyre_temp_c"])

                if data["lap_number"] > prev_lap and data["last_lap_time"] > 0:
                    st.session_state.lap_times.append({
                        "lap": prev_lap, "time": data["last_lap_time"],
                        "compound": data["tyre_compound"],
                        "s1": data["sector_1_time"], "s2": data["sector_2_time"],
                        "s3": data["sector_3_time"]})
                    prev_lap = data["lap_number"]

                if fn % 5 != 0:
                    continue
                uk += 1

                map_ph.plotly_chart(make_map(data["x"], data["y"], data["tyre_compound"]),
                    use_container_width=True, key=f"m{uk}")

                flags = []
                if data["safety_car"]: flags.append("⚠️ SC")
                if data["in_pit"]: flags.append("🔧 PIT")
                metrics_ph.markdown(f"""
| | |
|:--|:--|
| **Lap** | **{data['lap_number']}** / {total_laps} |
| **Sector** | S{data['sector']} |
| **Speed** | **{data['speed_kph']:.0f}** kph |
| **Gear** | {data['gear']} {'DRS' if data['drs'] else ''} |
| **Tyre** | **{data['tyre_compound'].upper()}** ({data['tyre_age_laps']} laps) |
| **Temp** | {data['tyre_temp_c']:.0f}°C |
| **Wear** | {data['tyre_wear_pct']*100:.1f}% |
| **Fuel** | {data['fuel_remaining_kg']:.1f} kg |
| **Last** | {data['last_lap_time']:.3f}s |
| **Pos** | P{data['position']} {' '.join(flags)} |
""")

                fs = go.Figure()
                fs.add_trace(go.Scatter(y=list(spd_buf), mode="lines",
                    line=dict(color="#00D4FF", width=1.5),
                    fill="tozeroy", fillcolor="rgba(0,212,255,0.1)"))
                fs.update_layout(title="Speed", yaxis_title="kph", height=230,
                    margin=dict(l=40,r=10,t=35,b=20), yaxis_range=[0,380],
                    template="plotly_dark", xaxis=dict(showticklabels=False))
                speed_ph.plotly_chart(fs, use_container_width=True, key=f"s{uk}")

                ft = go.Figure()
                ft.add_trace(go.Scatter(y=list(tmp_buf), mode="lines",
                    line=dict(color="#FF6B35", width=1.5),
                    fill="tozeroy", fillcolor="rgba(255,107,53,0.1)"))
                ft.add_hrect(y0=85, y1=105, fillcolor="rgba(0,255,0,0.08)",
                    line_width=0)
                ft.update_layout(title="Tyre Temp", yaxis_title="°C", height=230,
                    margin=dict(l=40,r=10,t=35,b=20), yaxis_range=[30,140],
                    template="plotly_dark", xaxis=dict(showticklabels=False))
                tyre_ph.plotly_chart(ft, use_container_width=True, key=f"t{uk}")

                lt = st.session_state.lap_times
                if lt:
                    fl = go.Figure()
                    fl.add_trace(go.Scatter(
                        x=[l["lap"] for l in lt], y=[l["time"] for l in lt],
                        mode="lines+markers",
                        marker=dict(size=8,
                            color=[COMPOUND_COLORS.get(l["compound"],"#0f0") for l in lt],
                            line=dict(width=1, color="white")),
                        line=dict(color="#888", width=1),
                        text=[f"S1:{l['s1']:.1f} S2:{l['s2']:.1f} S3:{l['s3']:.1f}" for l in lt],
                        hovertemplate="Lap %{x}<br>%{y:.3f}s<br>%{text}<extra></extra>"))
                    fl.update_layout(title="Lap Times", xaxis_title="Lap",
                        yaxis_title="s", height=280,
                        margin=dict(l=40,r=10,t=35,b=30), template="plotly_dark")
                    lap_ph.plotly_chart(fl, use_container_width=True, key=f"l{uk}")

                if lt and len(lt) % 5 == 0:
                    avg5 = sum(l["time"] for l in lt[-5:])/min(5,len(lt))
                    wear = data['tyre_wear_pct']
                    strat_ph.info(
                        f"📊 **Lap {data['lap_number']}** — "
                        f"Avg(5): **{avg5:.2f}s** | "
                        f"Wear: {wear*100:.0f}% | "
                        f"{'💡 Consider pit stop' if wear > 0.5 else '✅ Tyres OK'}")

            ws.close()
        except Exception as e:
            status_ph.error(f"Error: {e}")
        st.session_state.race_running = False

    # ---- Post-race ----
    if st.session_state.telemetry_data and not st.session_state.race_running:
        st.divider()
        st.subheader("📈 Post-Race Analysis")
        td = st.session_state.telemetry_data
        lt = st.session_state.lap_times
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Frames", len(td))
        c2.metric("Laps", len(lt))
        if lt:
            c3.metric("Best Lap", f"{min(l['time'] for l in lt):.3f}s")
            c4.metric("Avg Lap", f"{sum(l['time'] for l in lt)/len(lt):.3f}s")

        if lt and st.button("🎲 Run Monte Carlo on Race Data"):
            with st.spinner(f"Running {iterations} simulations..."):
                resp = requests.post(f"{API_BASE}/recommend", params={
                    "driver_code": driver_code, "pit_loss": ti["pit_loss"],
                    "safety_car_prob": ti["safety_car_prob"],
                    "iterations": iterations})
            d = resp.json()
            st.success(f"**{d['recommended']}** @ {d['confidence']*100:.1f}% confidence")

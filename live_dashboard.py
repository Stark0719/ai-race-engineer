"""
Live Race Dashboard v5
======================
- 3D viewer embedded as iframe (from FastAPI /viewer)
- 2D track map (Plotly XY)
- Live telemetry charts
- Stable Streamlit keys

Run:
    python -m uvicorn api.main:app --reload
    streamlit run live_dashboard.py
    
    3D Viewer also available standalone at: http://127.0.0.1:8000/viewer
"""

import streamlit as st
import json
import plotly.graph_objects as go
import requests
import streamlit.components.v1 as stc
from collections import deque

st.set_page_config(page_title="Live Race Engineer", layout="wide")
st.title("🏎️ AI Race Engineer — Live Telemetry")

API_BASE = "http://127.0.0.1:8000"
WS_BASE = "ws://127.0.0.1:8000"
COMPOUND_COLORS = {"soft": "#FF3333", "medium": "#FFD700", "hard": "#CCCCCC"}

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
st.sidebar.header("🏁 Race Configuration")
try:
    tracks_resp = requests.get(f"{API_BASE}/tracks", timeout=5).json()["tracks"]
except Exception:
    st.error("Cannot connect to API. Run: `python -m uvicorn api.main:app --reload`")
    st.stop()

track_keys = list(tracks_resp.keys())
track_labels = {k: f"{v['name']} ({v['country']})" for k, v in tracks_resp.items()}
track_key = st.sidebar.selectbox("Select Track", track_keys,
                                  format_func=lambda k: track_labels[k])
ti = tracks_resp[track_key]
st.sidebar.markdown(f"**{ti['circuit_length_m']/1000:.1f} km** | "
                    f"**{ti['total_laps']} laps** | "
                    f"**Base:** {ti['base_lap_time']:.1f}s")
st.sidebar.markdown(f"**Pit loss:** {ti['pit_loss']}s | "
                    f"**SC prob:** {ti['safety_car_prob']*100:.0f}%")

compound = st.sidebar.selectbox("Starting Compound", ["soft", "medium", "hard"], index=1)
speed_mult = st.sidebar.slider("Simulation Speed", 1, 50, 10)
pit_lap = st.sidebar.number_input("Pit Stop on Lap", 0, ti["total_laps"], 0)
next_compound = st.sidebar.selectbox("Pit to Compound", ["soft", "medium", "hard"], index=2)

wps = ti["waypoints_xy"]
track_x = [p[0] for p in wps] + [wps[0][0]]
track_y = [p[1] for p in wps] + [wps[0][1]]

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
c_start, c_stop = st.columns(2)
start_clicked = c_start.button("🟢 Start Race", type="primary", use_container_width=True)
stop_clicked = c_stop.button("🔴 Stop Race", use_container_width=True)

status_ph = st.empty()

# 3D viewer as full-width iframe
st.subheader("🎮 3D Race View")
st.caption("🖱️ Drag to orbit • Scroll to zoom — "
           "[Open fullscreen ↗](http://127.0.0.1:8000/viewer)")
stc.iframe(f"{API_BASE}/viewer", height=550, scrolling=False)

# 2D map + metrics
map_col, metrics_col = st.columns([1, 1])
with map_col:
    st.subheader("📍 Track Map")
    map_ph = st.empty()
with metrics_col:
    st.subheader("📊 Telemetry")
    metrics_ph = st.empty()

ch1, ch2 = st.columns(2)
with ch1:
    speed_ph = st.empty()
with ch2:
    tyre_ph = st.empty()
lap_ph = st.empty()


# ---------------------------------------------------------------------------
# 2D Track Map
# ---------------------------------------------------------------------------
def make_track_fig(car_x=None, car_y=None, compound="medium"):
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=track_x, y=track_y, mode="lines",
        line=dict(width=6, color="#444"), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[wps[0][0]], y=[wps[0][1]], mode="markers",
        marker=dict(size=10, color="white", symbol="square"), showlegend=False))
    if car_x is not None:
        fig.add_trace(go.Scatter(
            x=[car_x], y=[car_y], mode="markers",
            marker=dict(size=14, color=COMPOUND_COLORS.get(compound, "#0f0"),
                       line=dict(width=2, color="white")), showlegend=False))
    fig.update_layout(
        xaxis=dict(scaleanchor="y", scaleratio=1, showgrid=False,
                   zeroline=False, visible=False),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="#1a1a2e", paper_bgcolor="#1a1a2e",
        margin=dict(l=5, r=5, t=5, b=5), height=350)
    return fig


map_ph.plotly_chart(make_track_fig(), use_container_width=True, key="map_init")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "running" not in st.session_state:
    st.session_state.running = False
if stop_clicked:
    st.session_state.running = False
if start_clicked:
    st.session_state.running = True

# ---------------------------------------------------------------------------
# RACE LOOP (telemetry data for charts — 3D viewer runs independently)
# ---------------------------------------------------------------------------
if st.session_state.running:
    from websocket import create_connection, WebSocketTimeoutException

    status_ph.info("🏎️ Connecting to telemetry stream...")

    try:
        ws = create_connection(f"{WS_BASE}/ws/live/{track_key}", timeout=5)
        ws.send(json.dumps({
            "compound": compound, "driver": "VER",
            "speed_multiplier": speed_mult,
            "pit_lap": pit_lap, "next_compound": next_compound,
        }))

        track_msg = json.loads(ws.recv())
        total_laps = track_msg.get("total_laps", "?")
        status_ph.success(f"🟢 Racing — {track_msg.get('name', track_key)} — {total_laps} laps")

        speeds = deque(maxlen=300)
        temps = deque(maxlen=300)
        lap_times = []
        prev_lap = 1
        n = 0
        uk = 0

        while True:
            try:
                ws.settimeout(3.0)
                raw = ws.recv()
                data = json.loads(raw)
            except WebSocketTimeoutException:
                continue
            except Exception:
                break

            if data.get("type") == "race_finished":
                status_ph.success(f"🏁 Finished! {data['total_laps']} laps — {data['total_time']:.1f}s")
                break
            if data.get("type") != "telemetry":
                continue

            n += 1
            speeds.append(data["speed_kph"])
            temps.append(data["tyre_temp_c"])

            if data["lap_number"] > prev_lap and data["last_lap_time"] > 0:
                lap_times.append({
                    "lap": prev_lap, "time": data["last_lap_time"],
                    "compound": data["tyre_compound"],
                    "s1": data["sector_1_time"], "s2": data["sector_2_time"],
                    "s3": data["sector_3_time"],
                })
                prev_lap = data["lap_number"]

            if n % 5 != 0:
                continue

            uk += 1
            d = data

            # ---- 2D MAP ----
            map_ph.plotly_chart(
                make_track_fig(d["x"], d["y"], d["tyre_compound"]),
                use_container_width=True, key=f"m{uk}")

            # ---- METRICS TABLE ----
            sc = "⚠️ SC " if d["safety_car"] else ""
            pit = "🔧 PIT " if d["in_pit"] else ""
            flag = f"{sc}{pit}" or "🟢 "
            metrics_ph.markdown(f"""
| | |
|---|---|
| **Lap** | {d['lap_number']} / {total_laps} |
| **Sector** | S{d['sector']} |
| **Speed** | {d['speed_kph']:.0f} kph |
| **Gear** | {d['gear']} {'DRS' if d['drs'] else ''} |
| **Tyre** | {d['tyre_compound'].upper()} ({d['tyre_age_laps']} laps) |
| **Tyre Temp** | {d['tyre_temp_c']:.0f}°C |
| **Tyre Wear** | {d['tyre_wear_pct']*100:.0f}% |
| **Fuel** | {d['fuel_remaining_kg']:.0f} kg |
| **Last Lap** | {d['last_lap_time']:.2f}s |
| **Position** | P{d['position']} {flag}|
""")

            # ---- SPEED ----
            fs = go.Figure()
            fs.add_trace(go.Scatter(y=list(speeds), mode="lines",
                line=dict(color="#00D4FF", width=1.5),
                fill="tozeroy", fillcolor="rgba(0,212,255,0.1)"))
            fs.update_layout(title="Speed Trace", yaxis_title="kph",
                height=220, margin=dict(l=40, r=10, t=35, b=20),
                yaxis_range=[0, 380], template="plotly_dark",
                xaxis=dict(showticklabels=False))
            speed_ph.plotly_chart(fs, use_container_width=True, key=f"s{uk}")

            # ---- TYRE TEMP ----
            ft = go.Figure()
            ft.add_trace(go.Scatter(y=list(temps), mode="lines",
                line=dict(color="#FF6B35", width=1.5),
                fill="tozeroy", fillcolor="rgba(255,107,53,0.1)"))
            ft.add_hrect(y0=85, y1=105, fillcolor="rgba(0,255,0,0.1)",
                        line_width=0)
            ft.update_layout(title="Tyre Temperature", yaxis_title="°C",
                height=220, margin=dict(l=40, r=10, t=35, b=20),
                yaxis_range=[30, 140], template="plotly_dark",
                xaxis=dict(showticklabels=False))
            tyre_ph.plotly_chart(ft, use_container_width=True, key=f"t{uk}")

            # ---- LAP TIMES ----
            if lap_times:
                fl = go.Figure()
                fl.add_trace(go.Scatter(
                    x=[l["lap"] for l in lap_times],
                    y=[l["time"] for l in lap_times],
                    mode="lines+markers",
                    marker=dict(size=8,
                        color=[COMPOUND_COLORS.get(l["compound"], "#0f0") for l in lap_times],
                        line=dict(width=1, color="white")),
                    line=dict(color="#888", width=1),
                    text=[f"S1:{l['s1']:.1f} S2:{l['s2']:.1f} S3:{l['s3']:.1f}" for l in lap_times],
                    hovertemplate="Lap %{x}<br>%{y:.2f}s<br>%{text}<extra></extra>"))
                fl.update_layout(title="Lap Times", xaxis_title="Lap",
                    yaxis_title="s", height=260,
                    margin=dict(l=40, r=10, t=35, b=30),
                    template="plotly_dark")
                lap_ph.plotly_chart(fl, use_container_width=True, key=f"l{uk}")

        ws.close()
    except Exception as e:
        status_ph.error(f"Connection error: {e}")
    st.session_state.running = False

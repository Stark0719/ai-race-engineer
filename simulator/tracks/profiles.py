"""
Track Profiles v6 — Explicit Coordinates
==========================================
Each track defined as explicit (x, y, speed) waypoints traced from
real circuit maps. No procedural generation = no overlap bugs.

Coordinates are in meters, origin at start/finish line.
Speed in kph at each waypoint.

Tracks are defined clockwise and form closed loops.
"""

from dataclasses import dataclass
import math


@dataclass
class TrackProfile:
    name: str
    country: str
    total_laps: int
    pit_loss_sec: float
    base_lap_time_sec: float
    safety_car_probability: float
    circuit_length_m: float
    sector_boundaries: list
    sector_base_times: list
    waypoints: list
    track_width_m: float = 12.0

    @property
    def xy_points(self):
        return [(w[0], w[1]) for w in self.waypoints]

    @property
    def speeds(self):
        return [w[2] for w in self.waypoints]

    def interpolate_position(self, fraction: float) -> tuple:
        n = len(self.waypoints)
        f = fraction % 1.0
        idx = f * n
        i0 = int(idx) % n
        i1 = (i0 + 1) % n
        t = idx - int(idx)
        return (self.waypoints[i0][0]*(1-t) + self.waypoints[i1][0]*t,
                self.waypoints[i0][1]*(1-t) + self.waypoints[i1][1]*t)

    def interpolate_speed(self, fraction: float) -> float:
        n = len(self.waypoints)
        f = fraction % 1.0
        idx = f * n
        i0 = int(idx) % n
        i1 = (i0 + 1) % n
        t = idx - int(idx)
        return self.waypoints[i0][2]*(1-t) + self.waypoints[i1][2]*t

    def get_sector(self, fraction: float) -> int:
        f = fraction % 1.0
        for i in range(len(self.sector_boundaries) - 1):
            if f < self.sector_boundaries[i+1]:
                return i + 1
        return len(self.sector_boundaries) - 1

    def get_heading(self, fraction: float) -> float:
        n = len(self.waypoints)
        f = fraction % 1.0
        i0 = int(f * n) % n
        i1 = (i0 + 1) % n
        dx = self.waypoints[i1][0] - self.waypoints[i0][0]
        dy = self.waypoints[i1][1] - self.waypoints[i0][1]
        return math.atan2(dy, dx)


def _smooth(pts, n_out=200):
    """Resample and smooth a list of (x,y,speed) via linear interpolation."""
    # Compute cumulative arc length
    dists = [0.0]
    for i in range(1, len(pts)):
        dx = pts[i][0] - pts[i-1][0]
        dy = pts[i][1] - pts[i-1][1]
        dists.append(dists[-1] + math.sqrt(dx*dx + dy*dy))
    total = dists[-1]
    
    result = []
    for j in range(n_out):
        target = (j / n_out) * total
        # Find segment
        for i in range(len(dists)-1):
            if dists[i+1] >= target:
                t = (target - dists[i]) / (dists[i+1] - dists[i]) if dists[i+1] > dists[i] else 0
                x = pts[i][0] + t * (pts[i+1][0] - pts[i][0])
                y = pts[i][1] + t * (pts[i+1][1] - pts[i][1])
                s = pts[i][2] + t * (pts[i+1][2] - pts[i][2])
                result.append((round(x, 1), round(y, 1), round(s, 0)))
                break
    return result


# =====================================================================
# BAHRAIN INTERNATIONAL CIRCUIT — 5.412km, clockwise
# Traced from official FIA track map, scaled to meters
# Origin at S/F line, X=right, Y=up
# =====================================================================
_bahrain_raw = [
    (0, 0, 310),        # S/F line
    (100, 0, 320),
    (200, 0, 330),
    (300, 0, 330),
    (400, 5, 320),      # Approaching T1
    (460, 10, 200),
    (480, -30, 80),      # T1 apex (tight right)
    (470, -70, 100),
    (440, -90, 130),     # T2 (left)
    (420, -60, 150),
    (400, -30, 170),     # T3 (right)
    (370, -50, 160),
    (340, -80, 200),
    (300, -110, 280),    # Straight to T4
    (250, -130, 290),
    (200, -160, 280),
    (170, -200, 170),    # T4 (long right)
    (160, -250, 160),
    (180, -290, 170),
    (220, -310, 260),    # Short straight
    (260, -300, 270),
    (300, -280, 220),
    (310, -240, 100),    # T5-T6 chicane
    (280, -220, 90),
    (260, -240, 100),
    (240, -280, 130),
    (200, -320, 280),    # Straight
    (160, -360, 290),
    (120, -400, 300),
    (80, -430, 280),
    (30, -440, 170),     # T7-T8
    (-10, -420, 150),
    (-30, -380, 170),
    (-50, -340, 300),    # Back straight
    (-60, -280, 310),
    (-70, -220, 310),
    (-80, -160, 310),
    (-90, -110, 200),    # T9-T10 (tight)
    (-120, -80, 90),
    (-140, -110, 100),
    (-130, -150, 270),   # Short straight
    (-120, -200, 270),
    (-100, -240, 200),   # T11
    (-80, -280, 130),
    (-110, -300, 80),    # T12 (tight)
    (-140, -280, 90),
    (-160, -250, 100),   # T13
    (-140, -220, 130),
    (-120, -180, 300),   # Long straight to T14
    (-110, -120, 310),
    (-100, -60, 310),
    (-90, 0, 310),
    (-80, 60, 300),
    (-60, 100, 200),     # T14
    (-30, 120, 100),
    (0, 100, 130),
    (20, 70, 150),       # T15 (left)
    (10, 40, 280),
    (0, 10, 310),        # Back to S/F
]

# =====================================================================
# MONZA — 5.793km, clockwise, temple of speed
# Long straights separated by tight chicanes
# =====================================================================
_monza_raw = [
    (0, 0, 340),          # S/F
    (150, 0, 350),
    (300, 0, 350),
    (450, 5, 340),
    (550, 10, 200),       # T1 Rettifilo chicane
    (570, -20, 70),
    (560, -50, 70),
    (580, -70, 100),
    (610, -60, 250),
    (650, -40, 300),      # Straight to Curva Grande
    (700, -30, 320),
    (780, -10, 330),
    (850, 20, 280),       # Curva Grande (fast right)
    (900, 60, 270),
    (930, 110, 280),
    (940, 170, 310),      # Straight
    (950, 250, 330),
    (960, 340, 340),
    (970, 420, 300),
    (950, 460, 60),       # Roggia chicane
    (930, 440, 60),
    (940, 410, 80),
    (960, 390, 200),
    (940, 360, 250),      # Lesmos
    (900, 340, 200),
    (860, 350, 190),
    (840, 380, 200),
    (810, 420, 300),      # Back straight
    (780, 480, 330),
    (750, 550, 340),
    (720, 620, 345),
    (690, 680, 340),
    (660, 720, 200),      # Ascari chicane
    (640, 700, 60),
    (620, 720, 60),
    (640, 750, 80),
    (660, 740, 200),
    (680, 710, 300),      # Straight to Parabolica
    (700, 660, 330),
    (700, 600, 340),
    (680, 540, 300),
    (640, 490, 210),      # Parabolica (long right)
    (580, 460, 200),
    (510, 440, 210),
    (440, 410, 230),
    (370, 370, 270),
    (300, 320, 300),
    (220, 250, 310),
    (150, 170, 320),      # Straight back
    (100, 100, 330),
    (50, 50, 340),
    (10, 10, 340),
]

# =====================================================================
# SILVERSTONE — 5.891km, clockwise, fast and flowing
# =====================================================================
_silverstone_raw = [
    (0, 0, 300),          # S/F
    (100, 0, 310),
    (200, 10, 310),
    (280, 30, 250),       # Copse (fast right)
    (320, 70, 240),
    (340, 120, 260),
    (340, 180, 290),
    (320, 230, 200),      # Maggotts
    (280, 260, 180),
    (240, 240, 170),      # Becketts (left)
    (200, 260, 170),
    (170, 300, 180),      # Chapel (right)
    (150, 340, 290),
    (130, 400, 310),      # Hangar Straight
    (110, 470, 320),
    (100, 540, 320),
    (90, 600, 310),
    (60, 650, 180),       # Stowe
    (20, 680, 150),
    (-20, 670, 110),      # Vale (left)
    (-50, 640, 130),
    (-30, 600, 140),      # Club (right)
    (0, 570, 200),
    (20, 530, 270),
    (40, 480, 280),
    (20, 430, 200),       # Abbey (left)
    (-10, 400, 140),
    (-40, 380, 120),      # Farm (left)
    (-80, 370, 150),
    (-120, 380, 200),
    (-150, 360, 120),     # Village (right)
    (-180, 330, 130),
    (-200, 290, 150),     # The Loop (left)
    (-180, 250, 160),
    (-150, 230, 280),     # Straight
    (-130, 190, 300),
    (-110, 140, 310),
    (-100, 90, 200),      # Brooklands
    (-70, 60, 100),
    (-40, 50, 130),       # Luffield
    (-20, 30, 150),
    (-10, 10, 300),
]

# =====================================================================
# SINGAPORE — 4.940km, clockwise, tight street circuit
# =====================================================================
_singapore_raw = [
    (0, 0, 280),
    (80, 0, 285),
    (160, 5, 280),
    (220, 10, 150),       # T1
    (240, -30, 70),
    (220, -60, 80),
    (190, -40, 200),
    (170, -10, 240),
    (160, 30, 150),       # T3-5
    (130, 50, 60),
    (100, 30, 70),
    (80, 50, 200),
    (70, 90, 260),
    (60, 140, 265),
    (40, 180, 200),       # T7
    (10, 200, 70),
    (-20, 180, 80),
    (-30, 150, 200),
    (-40, 110, 255),
    (-60, 70, 150),       # T9-11
    (-80, 40, 85),
    (-100, 60, 80),
    (-80, 90, 90),
    (-60, 120, 270),      # Straight
    (-70, 170, 275),
    (-80, 220, 260),
    (-100, 260, 100),     # T13
    (-120, 240, 60),
    (-140, 260, 80),
    (-130, 290, 230),
    (-120, 330, 235),
    (-100, 360, 150),     # T16-18
    (-70, 380, 70),
    (-40, 360, 60),
    (-50, 330, 80),
    (-70, 310, 100),
    (-50, 280, 200),
    (-30, 250, 260),
    (-10, 200, 265),
    (0, 150, 250),
    (10, 100, 240),       # T22-23 approach back
    (10, 50, 270),
    (5, 10, 280),
]

# =====================================================================
# SPA-FRANCORCHAMPS — 7.004km, clockwise, the classic
# =====================================================================
_spa_raw = [
    (0, 0, 300),          # S/F
    (100, -10, 310),
    (180, -20, 280),
    (220, -50, 100),      # La Source hairpin
    (210, -90, 55),
    (170, -100, 80),
    (130, -80, 250),      # Down to Eau Rouge
    (100, -40, 280),
    (80, 10, 260),        # Eau Rouge (left)
    (60, 60, 270),        # Raidillon (right + uphill)
    (80, 120, 300),
    (100, 200, 330),      # Kemmel Straight
    (120, 300, 340),
    (140, 400, 340),
    (170, 470, 250),      # Les Combes
    (200, 500, 130),
    (230, 480, 120),
    (250, 440, 140),
    (280, 400, 280),      # Straight
    (300, 350, 300),
    (310, 300, 280),
    (280, 260, 150),      # Bruxelles
    (240, 250, 140),
    (220, 280, 160),
    (200, 320, 280),      # Straight
    (170, 370, 290),
    (130, 420, 220),      # Pouhon (double left)
    (80, 450, 200),
    (30, 460, 200),
    (-20, 440, 210),
    (-60, 400, 280),      # Straight
    (-90, 350, 290),
    (-110, 300, 250),
    (-120, 250, 140),     # Stavelot
    (-100, 210, 130),
    (-70, 200, 160),
    (-40, 210, 290),      # Straight to Blanchimont
    (-20, 180, 310),
    (0, 140, 320),
    (20, 100, 290),       # Blanchimont (fast)
    (30, 60, 280),
    (10, 30, 100),        # Bus Stop chicane
    (-10, 10, 55),
    (-20, -10, 60),
    (-10, -20, 200),
    (0, -10, 300),        # Back to S/F
]


# Build all tracks with smoothing
TRACKS: dict = {
    "bahrain": TrackProfile(
        name="Bahrain International Circuit", country="Bahrain",
        total_laps=57, pit_loss_sec=21.5, base_lap_time_sec=93.0,
        safety_car_probability=0.25, circuit_length_m=5412,
        sector_boundaries=[0.0, 0.345, 0.667, 1.0],
        sector_base_times=[30.5, 32.0, 30.5],
        waypoints=_smooth(_bahrain_raw, 200),
    ),
    "monza": TrackProfile(
        name="Autodromo Nazionale Monza", country="Italy",
        total_laps=53, pit_loss_sec=24.0, base_lap_time_sec=82.5,
        safety_car_probability=0.20, circuit_length_m=5793,
        sector_boundaries=[0.0, 0.356, 0.656, 1.0],
        sector_base_times=[26.5, 24.8, 31.2],
        waypoints=_smooth(_monza_raw, 200),
    ),
    "silverstone": TrackProfile(
        name="Silverstone Circuit", country="United Kingdom",
        total_laps=52, pit_loss_sec=20.5, base_lap_time_sec=89.5,
        safety_car_probability=0.15, circuit_length_m=5891,
        sector_boundaries=[0.0, 0.33, 0.66, 1.0],
        sector_base_times=[29.0, 30.5, 30.0],
        waypoints=_smooth(_silverstone_raw, 200),
    ),
    "singapore": TrackProfile(
        name="Marina Bay Street Circuit", country="Singapore",
        total_laps=61, pit_loss_sec=28.0, base_lap_time_sec=100.0,
        safety_car_probability=0.55, circuit_length_m=4940,
        sector_boundaries=[0.0, 0.35, 0.68, 1.0],
        sector_base_times=[34.0, 33.5, 32.5],
        waypoints=_smooth(_singapore_raw, 180),
    ),
    "spa": TrackProfile(
        name="Circuit de Spa-Francorchamps", country="Belgium",
        total_laps=44, pit_loss_sec=22.0, base_lap_time_sec=107.0,
        safety_car_probability=0.30, circuit_length_m=7004,
        sector_boundaries=[0.0, 0.37, 0.70, 1.0],
        sector_base_times=[35.0, 38.0, 34.0],
        waypoints=_smooth(_spa_raw, 250),
    ),
}

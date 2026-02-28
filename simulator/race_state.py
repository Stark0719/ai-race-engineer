from dataclasses import dataclass

@dataclass
class RaceState:
    total_laps: int
    current_lap: int
    current_compound: str
    laps_on_tyre: int
    gap_ahead: float     # seconds
    gap_behind: float    # seconds
    position: int
    base_lap_time: float
    pit_loss_time: float

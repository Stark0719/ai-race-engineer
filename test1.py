from simulator.strategy import monte_carlo_with_field, evaluate_position_strategy
from simulator.race_state import RaceState

state = RaceState(
    total_laps=57,
    current_lap=20,
    current_compound="medium",
    laps_on_tyre=10,
    gap_ahead=2.5,
    gap_behind=1.2,
    position=2,
    base_lap_time=92,
    pit_loss_time=18
)

results = monte_carlo_with_field(
    iterations=200,
    race_state=state,
    one_stop_compounds=("medium", "hard"),
    two_stop_compounds=("soft", "medium", "hard")
)

print(evaluate_position_strategy(results))

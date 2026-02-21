from simulator.strategy import recommend_strategy


def strategy_tool(
    driver_code,
    total_laps,
    base_lap_time,
    pit_loss_time,
    safety_car_prob,
    iterations
):
    decision = recommend_strategy(
        iterations=iterations,
        total_laps=total_laps,
        base_lap_time=base_lap_time,
        pit_loss_time=pit_loss_time,
        one_stop_compounds=("medium", "hard"),
        two_stop_compounds=("soft", "medium", "hard"),
        safety_car_prob=safety_car_prob
    )

    return decision

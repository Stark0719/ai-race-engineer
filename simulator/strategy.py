import random

import random
from simulator.field import generate_field
from simulator.race_state import RaceState


COMPOUNDS = {
    "soft":  {"pace_offset": -0.8, "deg": 0.08},
    "medium": {"pace_offset": 0.0,  "deg": 0.03},
    "hard":  {"pace_offset": 0.5,  "deg": 0.015}
}


def simulate_one_stop_compound(
    total_laps,
    base_lap_time,
    pit_loss_time,
    compound_1,
    compound_2
):
    best_time = float("inf")
    best_pit_lap = None

    for pit_lap in range(5, total_laps - 5):

        total_time = 0

        # First stint
        for lap in range(1, pit_lap + 1):

            warmup_penalty = 0.7 if lap <= 2 else 0

            lap_time = (
                base_lap_time
                + COMPOUNDS[compound_1]["pace_offset"]
                + COMPOUNDS[compound_1]["deg"] * lap
                + warmup_penalty
            )

            total_time += lap_time

        # PIT STOP
        total_time += pit_loss_time

        # Second stint
        for lap in range(1, total_laps - pit_lap + 1):

            warmup_penalty = 0.7 if lap <= 2 else 0

            lap_time = (
                base_lap_time
                + COMPOUNDS[compound_2]["pace_offset"]
                + COMPOUNDS[compound_2]["deg"] * lap
                + warmup_penalty
            )

            total_time += lap_time

        if total_time < best_time:
            best_time = total_time
            best_pit_lap = pit_lap

    return best_pit_lap, best_time


def simulate_two_stop(
    total_laps,
    base_lap_time,
    pit_loss_time,
    compound_1,
    compound_2,
    compound_3
):
    best_time = float("inf")
    best_pits = None

    for pit1 in range(5, total_laps - 10):
        for pit2 in range(pit1 + 5, total_laps - 5):

            total_time = 0

            # Stint 1
            for lap in range(1, pit1 + 1):

                warmup_penalty = 0.7 if lap <= 2 else 0

                total_time += (
                    base_lap_time
                    + COMPOUNDS[compound_1]["pace_offset"]
                    + COMPOUNDS[compound_1]["deg"] * lap
                    + warmup_penalty
                )

            total_time += pit_loss_time

            # Stint 2
            for lap in range(1, pit2 - pit1 + 1):

                warmup_penalty = 0.7 if lap <= 2 else 0

                total_time += (
                    base_lap_time
                    + COMPOUNDS[compound_2]["pace_offset"]
                    + COMPOUNDS[compound_2]["deg"] * lap
                    + warmup_penalty
                )

            total_time += pit_loss_time

            # Stint 3
            for lap in range(1, total_laps - pit2 + 1):

                warmup_penalty = 0.7 if lap <= 2 else 0

                total_time += (
                    base_lap_time
                    + COMPOUNDS[compound_3]["pace_offset"]
                    + COMPOUNDS[compound_3]["deg"] * lap
                    + warmup_penalty
                )

            if total_time < best_time:
                best_time = total_time
                best_pits = (pit1, pit2)

    return best_pits, best_time

def monte_carlo_compare(
    iterations,
    total_laps,
    base_lap_time,
    pit_loss_time,
    one_stop_compounds,
    two_stop_compounds,
    safety_car_prob=0.2
):
    one_stop_wins = 0
    two_stop_wins = 0

    for _ in range(iterations):

        # Random safety car event
        if random.random() < safety_car_prob:
            adjusted_pit_loss = pit_loss_time * 0.4  # reduced pit loss
        else:
            adjusted_pit_loss = pit_loss_time
        
        deg_noise = random.uniform(-0.005, 0.005)
        original_medium_deg = COMPOUNDS["medium"]["deg"]
        COMPOUNDS["medium"]["deg"] = max(0, original_medium_deg + deg_noise)

        
        # Run strategies
        pit1, time1 = simulate_one_stop_compound(
            total_laps,
            base_lap_time,
            adjusted_pit_loss,
            *one_stop_compounds
        )

        pits2, time2 = simulate_two_stop(
            total_laps,
            base_lap_time,
            adjusted_pit_loss,
            *two_stop_compounds
        )
        
        # Restore degradation after iteration
        COMPOUNDS["medium"]["deg"] = original_medium_deg

        if time1 < time2:
            one_stop_wins += 1
        else:
            two_stop_wins += 1

    return {
        "one_stop_win_rate": one_stop_wins / iterations,
        "two_stop_win_rate": two_stop_wins / iterations
    }

def recommend_strategy(
    iterations,
    total_laps,
    base_lap_time,
    pit_loss_time,
    one_stop_compounds,
    two_stop_compounds,
    safety_car_prob=0.2
):
    result = monte_carlo_compare(
        iterations=iterations,
        total_laps=total_laps,
        base_lap_time=base_lap_time,
        pit_loss_time=pit_loss_time,
        one_stop_compounds=one_stop_compounds,
        two_stop_compounds=two_stop_compounds,
        safety_car_prob=safety_car_prob
    )

    one_rate = result["one_stop_win_rate"]
    two_rate = result["two_stop_win_rate"]

    if one_rate > two_rate:
        recommended = "1-stop"
        confidence = one_rate
    else:
        recommended = "2-stop"
        confidence = two_rate

    return {
        "recommended": recommended,
        "confidence": confidence,
        "one_stop_win_rate": one_rate,
        "two_stop_win_rate": two_rate,
        "pit_loss": pit_loss_time,
        "safety_car_probability": safety_car_prob
    }

def estimate_rejoin_position(
    race_state,
    field_lap_times,
    remaining_laps
):
    pit_time = race_state.pit_loss_time

    projected_time = (
        remaining_laps * race_state.base_lap_time
        + pit_time
    )

    positions = 1
    for rival_time in field_lap_times:
        rival_total = remaining_laps * rival_time
        if rival_total < projected_time:
            positions += 1

    return positions


def monte_carlo_with_field(
    iterations,
    race_state,
    one_stop_compounds,
    two_stop_compounds,
    safety_car_prob=0.2
):
    position_results = {
        "one_stop": [],
        "two_stop": []
    }

    for _ in range(iterations):

        # Generate simplified field
        field = generate_field(race_state.base_lap_time)

        # Safety car logic
        if random.random() < safety_car_prob:
            adjusted_pit_loss = race_state.pit_loss_time * 0.4
        else:
            adjusted_pit_loss = race_state.pit_loss_time

        remaining_laps = race_state.total_laps - race_state.current_lap

        # Simulate strategies (time-based)
        _, time_1 = simulate_one_stop_compound(
            remaining_laps,
            race_state.base_lap_time,
            adjusted_pit_loss,
            *one_stop_compounds
        )

        _, time_2 = simulate_two_stop(
            remaining_laps,
            race_state.base_lap_time,
            adjusted_pit_loss,
            *two_stop_compounds
        )

        # Convert time to position
        pos_1 = 1
        pos_2 = 1

        for rival_lap in field:
            rival_total = remaining_laps * rival_lap

            if rival_total < time_1:
                pos_1 += 1

            if rival_total < time_2:
                pos_2 += 1

        # Traffic penalty if not leading
        if pos_1 > 1:
            pos_1 += random.choice([0, 1])

        if pos_2 > 1:
            pos_2 += random.choice([0, 1])

        position_results["one_stop"].append(pos_1)
        position_results["two_stop"].append(pos_2)

    return position_results

def evaluate_position_strategy(position_results):

    one_positions = position_results["one_stop"]
    two_positions = position_results["two_stop"]

    avg_one = sum(one_positions) / len(one_positions)
    avg_two = sum(two_positions) / len(two_positions)

    p1_one = one_positions.count(1) / len(one_positions)
    p1_two = two_positions.count(1) / len(two_positions)

    podium_one = sum(p <= 3 for p in one_positions) / len(one_positions)
    podium_two = sum(p <= 3 for p in two_positions) / len(two_positions)

    if avg_one < avg_two:
        recommended = "1-stop"
    else:
        recommended = "2-stop"

    return {
        "recommended": recommended,
        "avg_position_one_stop": avg_one,
        "avg_position_two_stop": avg_two,
        "p1_prob_one_stop": p1_one,
        "p1_prob_two_stop": p1_two,
        "podium_prob_one_stop": podium_one,
        "podium_prob_two_stop": podium_two
    }

import random

def generate_field(base_lap_time, num_cars=5):
    field = []
    for i in range(num_cars):
        offset = random.uniform(-0.4, 0.4)
        field.append(base_lap_time + offset)
    return sorted(field)

import random
from collections import Counter

# ----------------------------
# Domain knowledge (ecology)
# ----------------------------

PLANT_SPECIES = {
    "grass": {
        "edibility": 0.8,
        "growth_rate": 0.20
    },
    "clover": {
        "edibility": 0.6,
        "growth_rate": 0.15
    },
    "shrub": {
        "edibility": 0.2,
        "growth_rate": 0.05
    }
}

ANIMAL_SPECIES = {
    "rabbit": ["grass", "clover"],
    "deer": ["grass", "clover", "shrub"]
}

LOCATIONS = ["meadow", "forest_edge", "clearing"]

TIME_STEPS = 6
NUM_TRACES = 6000


# ----------------------------
# Object definitions
# ----------------------------

class Plant:
    def __init__(self, pid):
        self.id = pid
        self.species = random.choice(list(PLANT_SPECIES.keys()))
        self.location = random.choice(LOCATIONS)
        self.alive = True
        self.eaten = False

    def step(self):
        """Plants may grow (stay alive) or die naturally"""
        if not self.alive:
            return

        # Natural death
        if random.random() < 0.03:
            self.alive = False

        # Regrowth / resilience modeled implicitly
        # (survival probability encoded in low death rate)


class Animal:
    def __init__(self, aid):
        self.id = aid
        self.species = random.choice(list(ANIMAL_SPECIES.keys()))
        self.location = random.choice(LOCATIONS)

    def move(self):
        self.location = random.choice(LOCATIONS)

    def try_eat(self, plants):
        """Attempt to eat a compatible plant in the same location"""
        for plant in plants:
            if (
                plant.alive
                and plant.location == self.location
                and plant.species in ANIMAL_SPECIES[self.species]
            ):
                p_eat = PLANT_SPECIES[plant.species]["edibility"]
                if random.random() < p_eat:
                    plant.alive = False
                    plant.eaten = True
                    return True
        return False


# ----------------------------
# World simulation
# ----------------------------

def simulate_world():
    num_animals = random.randint(1, 5)
    num_plants = random.randint(2, 6)

    animals = [Animal(i) for i in range(num_animals)]
    plants = [Plant(i) for i in range(num_plants)]

    eaten_any = False

    for _ in range(TIME_STEPS):
        for animal in animals:
            animal.move()
            if animal.try_eat(plants):
                eaten_any = True

        for plant in plants:
            plant.step()

    return {
        "plants": plants,
        "eaten_any": eaten_any
    }


# ----------------------------
# Conditioning & inference
# ----------------------------

def run_inference():
    conditioned = []

    for _ in range(NUM_TRACES):
        trace = simulate_world()
        if trace["eaten_any"]:  # observation
            conditioned.append(trace)

    return conditioned


def estimate_probabilities(traces):
    plant0_eaten = 0
    majority_survive = 0

    for trace in traces:
        plants = trace["plants"]
        alive = sum(p.alive for p in plants)

        for p in plants:
            if p.id == 0 and p.eaten:
                plant0_eaten += 1

        if alive > len(plants) / 2:
            majority_survive += 1

    total = len(traces)

    return {
        "P(plant 0 eaten | eating observed)": plant0_eaten / total,
        "P(>50% plants survive | eating observed)": majority_survive / total,
        "Conditioned traces": total
    }


# ----------------------------
# Main
# ----------------------------

if __name__ == "__main__":
    traces = run_inference()
    results = estimate_probabilities(traces)

    print("Conditioned on: at least one animal ate a plant\n")
    for k, v in results.items():
        print(f"{k}: {v:.3f}" if isinstance(v, float) else f"{k}: {v}")

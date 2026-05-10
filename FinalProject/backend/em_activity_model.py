# ============================================================
# Chapter 20 — Learning Probabilistic Models
# EM Algorithm for Hidden Activity-Mode Inference
#
# This module implements:
# - hidden activity modes
# - categorical observations
# - E-step
# - M-step
# - log-likelihood tracking
# - posterior inference for selected agent
#
# Improved version:
# - Uses stronger mode-specific synthetic observations.
# - Produces meaningful posterior probabilities instead of
#   near-uniform 13% for every mode.
# ============================================================

import random
import math
from collections import defaultdict

RANDOM_SEED = 20
random.seed(RANDOM_SEED)

HIDDEN_MODES = [
    "CLASS_MODE",
    "STUDY_MODE",
    "PRACTICE_MODE",
    "SOCIAL_MODE",
    "REST_MODE",
    "REBEL_MODE",
    "FREE_TIME_MODE",
]

CLASS_LOCATIONS = {"AcademicHall", "WestPenn"}
STUDY_LOCATIONS = {"Library"}
PRACTICE_LOCATIONS = {"Track"}
SOCIAL_LOCATIONS = {"StudentCenter", "VillagePark", "BoulevardAppartments"}
REST_LOCATIONS = {
    "OffCampus",
    "LawrenceHall",
    "ThayerHall",
    "ConestogaHall",
    "BoulevardAppartments",
}

PERFORMANCE_LOCATIONS = {"GeorgeRowlandWhite", "PlayHouse"}

TIME_BUCKETS = {
    "00:00-08:00": "sleep",
    "08:00-09:30": "morning",
    "09:40-11:10": "class_time",
    "11:20-12:50": "class_time",
    "13:00-14:30": "afternoon",
    "15:00-15:30": "practice_transition",
    "16:00-17:30": "practice_time",
    "18:00-21:00": "evening",
    "21:00-00:00": "free_time",
}


def weighted_choice(options):
    """
    options should be a list of tuples:
    [("value", weight), ("value2", weight2)]
    """
    total = sum(weight for _, weight in options)
    r = random.uniform(0, total)
    upto = 0

    for value, weight in options:
        if upto + weight >= r:
            return value
        upto += weight

    return options[-1][0]


def get_time_bucket(time_slot):
    return TIME_BUCKETS.get(time_slot, "unknown")


def location_category(location):
    if location in CLASS_LOCATIONS:
        return "class_location"

    if location in PERFORMANCE_LOCATIONS:
        return "performance_location"

    if location in STUDY_LOCATIONS:
        return "study_location"

    if location in PRACTICE_LOCATIONS:
        return "practice_location"

    if location in SOCIAL_LOCATIONS:
        return "social_location"

    if location in REST_LOCATIONS:
        return "rest_location"

    return "other_location"


def build_observation_from_agent(agent):
    expected_location = agent.get("expected_location_now") or agent.get("current_location")
    current_location = agent.get("current_location")

    is_rebel = current_location != expected_location or bool(agent.get("is_rebel"))

    return {
        "student_type": agent.get("student_type", "Regular Student"),
        "personality": agent.get("personality", "responsible"),
        "time_bucket": get_time_bucket(agent.get("time_slot", "08:00-09:30")),
        "current_location_category": location_category(current_location),
        "expected_location_category": location_category(expected_location),
        "rebel_status": "rebel" if is_rebel else "aligned",
    }


def make_observation(
    student_type,
    personality,
    time_bucket,
    current_location_category,
    expected_location_category,
    rebel_status,
):
    return {
        "student_type": student_type,
        "personality": personality,
        "time_bucket": time_bucket,
        "current_location_category": current_location_category,
        "expected_location_category": expected_location_category,
        "rebel_status": rebel_status,
    }


def generate_observation_for_mode(mode):
    """
    This creates stronger patterns for each hidden mode.

    The previous version was too random, so EM had no useful signal and
    returned almost uniform probabilities. This version gives each mode
    recognizable observable patterns while still including noise.
    """

    if mode == "CLASS_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Regular Student", 0.45),
                ("Athlete", 0.30),
                ("Copa", 0.25),
            ]),
            personality=weighted_choice([
                ("responsible", 0.50),
                ("social", 0.20),
                ("tired", 0.20),
                ("risk-taking", 0.10),
            ]),
            time_bucket=weighted_choice([
                ("class_time", 0.55),
                ("morning", 0.15),
                ("afternoon", 0.20),
                ("evening", 0.10),
            ]),
            current_location_category=weighted_choice([
                ("class_location", 0.80),
                ("study_location", 0.08),
                ("performance_location", 0.05),
                ("social_location", 0.04),
                ("rest_location", 0.03),
            ]),
            expected_location_category=weighted_choice([
                ("class_location", 0.86),
                ("study_location", 0.06),
                ("performance_location", 0.04),
                ("social_location", 0.04),
            ]),
            rebel_status=weighted_choice([
                ("aligned", 0.90),
                ("rebel", 0.10),
            ]),
        )

    if mode == "STUDY_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Regular Student", 0.45),
                ("Athlete", 0.30),
                ("Copa", 0.25),
            ]),
            personality=weighted_choice([
                ("responsible", 0.45),
                ("tired", 0.25),
                ("social", 0.20),
                ("risk-taking", 0.10),
            ]),
            time_bucket=weighted_choice([
                ("class_time", 0.20),
                ("afternoon", 0.35),
                ("evening", 0.30),
                ("morning", 0.15),
            ]),
            current_location_category=weighted_choice([
                ("study_location", 0.82),
                ("class_location", 0.08),
                ("social_location", 0.06),
                ("rest_location", 0.04),
            ]),
            expected_location_category=weighted_choice([
                ("study_location", 0.60),
                ("class_location", 0.25),
                ("social_location", 0.10),
                ("rest_location", 0.05),
            ]),
            rebel_status=weighted_choice([
                ("aligned", 0.75),
                ("rebel", 0.25),
            ]),
        )

    if mode == "PRACTICE_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Athlete", 0.88),
                ("Regular Student", 0.08),
                ("Copa", 0.04),
            ]),
            personality=weighted_choice([
                ("responsible", 0.35),
                ("tired", 0.25),
                ("social", 0.20),
                ("risk-taking", 0.20),
            ]),
            time_bucket=weighted_choice([
                ("practice_transition", 0.35),
                ("practice_time", 0.55),
                ("afternoon", 0.10),
            ]),
            current_location_category=weighted_choice([
                ("practice_location", 0.84),
                ("social_location", 0.06),
                ("rest_location", 0.05),
                ("study_location", 0.05),
            ]),
            expected_location_category=weighted_choice([
                ("practice_location", 0.90),
                ("class_location", 0.04),
                ("social_location", 0.03),
                ("study_location", 0.03),
            ]),
            rebel_status=weighted_choice([
                ("aligned", 0.86),
                ("rebel", 0.14),
            ]),
        )

    if mode == "SOCIAL_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Regular Student", 0.40),
                ("Copa", 0.30),
                ("Athlete", 0.30),
            ]),
            personality=weighted_choice([
                ("social", 0.55),
                ("risk-taking", 0.20),
                ("tired", 0.15),
                ("responsible", 0.10),
            ]),
            time_bucket=weighted_choice([
                ("free_time", 0.35),
                ("evening", 0.30),
                ("afternoon", 0.20),
                ("class_time", 0.15),
            ]),
            current_location_category=weighted_choice([
                ("social_location", 0.84),
                ("rest_location", 0.06),
                ("study_location", 0.05),
                ("class_location", 0.05),
            ]),
            expected_location_category=weighted_choice([
                ("social_location", 0.45),
                ("class_location", 0.25),
                ("study_location", 0.15),
                ("rest_location", 0.15),
            ]),
            rebel_status=weighted_choice([
                ("aligned", 0.60),
                ("rebel", 0.40),
            ]),
        )

    if mode == "REST_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Regular Student", 0.40),
                ("Athlete", 0.35),
                ("Copa", 0.25),
            ]),
            personality=weighted_choice([
                ("tired", 0.55),
                ("responsible", 0.20),
                ("social", 0.15),
                ("risk-taking", 0.10),
            ]),
            time_bucket=weighted_choice([
                ("sleep", 0.45),
                ("free_time", 0.25),
                ("evening", 0.20),
                ("afternoon", 0.10),
            ]),
            current_location_category=weighted_choice([
                ("rest_location", 0.84),
                ("social_location", 0.08),
                ("study_location", 0.04),
                ("class_location", 0.04),
            ]),
            expected_location_category=weighted_choice([
                ("rest_location", 0.65),
                ("class_location", 0.15),
                ("study_location", 0.10),
                ("social_location", 0.10),
            ]),
            rebel_status=weighted_choice([
                ("aligned", 0.70),
                ("rebel", 0.30),
            ]),
        )

    if mode == "REBEL_MODE":
        return make_observation(
            student_type=weighted_choice([
                ("Regular Student", 0.35),
                ("Athlete", 0.35),
                ("Copa", 0.30),
            ]),
            personality=weighted_choice([
                ("risk-taking", 0.45),
                ("social", 0.25),
                ("tired", 0.20),
                ("responsible", 0.10),
            ]),
            time_bucket=weighted_choice([
                ("class_time", 0.30),
                ("afternoon", 0.25),
                ("practice_time", 0.15),
                ("evening", 0.15),
                ("free_time", 0.15),
            ]),
            current_location_category=weighted_choice([
                ("social_location", 0.40),
                ("rest_location", 0.25),
                ("study_location", 0.20),
                ("practice_location", 0.05),
                ("class_location", 0.05),
                ("performance_location", 0.05),
            ]),
            expected_location_category=weighted_choice([
                ("class_location", 0.40),
                ("practice_location", 0.25),
                ("performance_location", 0.20),
                ("study_location", 0.10),
                ("social_location", 0.05),
            ]),
            rebel_status=weighted_choice([
                ("rebel", 0.94),
                ("aligned", 0.06),
            ]),
        )

    # FREE_TIME_MODE
    return make_observation(
        student_type=weighted_choice([
            ("Regular Student", 0.40),
            ("Athlete", 0.30),
            ("Copa", 0.30),
        ]),
        personality=weighted_choice([
            ("social", 0.30),
            ("tired", 0.25),
            ("responsible", 0.25),
            ("risk-taking", 0.20),
        ]),
        time_bucket=weighted_choice([
            ("free_time", 0.82),
            ("evening", 0.12),
            ("afternoon", 0.06),
        ]),
        current_location_category=weighted_choice([
            ("social_location", 0.55),
            ("rest_location", 0.30),
            ("study_location", 0.10),
            ("class_location", 0.05),
        ]),
        expected_location_category=weighted_choice([
            ("social_location", 0.45),
            ("rest_location", 0.35),
            ("study_location", 0.10),
            ("class_location", 0.10),
        ]),
        rebel_status=weighted_choice([
            ("aligned", 0.78),
            ("rebel", 0.22),
        ]),
    )


def generate_synthetic_observations(n_per_mode=180):
    observations = []

    for mode in HIDDEN_MODES:
        for _ in range(n_per_mode):
            observations.append(generate_observation_for_mode(mode))

    random.shuffle(observations)
    return observations


class EMActivityModeModel:
    def __init__(self, iterations=25, smoothing=1e-4):
        self.iterations = iterations
        self.smoothing = smoothing
        self.pi = {}
        self.theta = {}
        self.feature_values = defaultdict(set)
        self.log_likelihood_history = []
        self.is_trained = False

    def collect_feature_values(self, observations):
        for obs in observations:
            for feature, value in obs.items():
                self.feature_values[feature].add(value)

    def initialize_parameters(self, observations):
        self.collect_feature_values(observations)

        self.pi = {
            mode: 1.0 / len(HIDDEN_MODES)
            for mode in HIDDEN_MODES
        }

        self.theta = {}

        # Slightly random initialization helps avoid perfectly symmetric EM.
        for mode in HIDDEN_MODES:
            self.theta[mode] = {}

            for feature, values in self.feature_values.items():
                values = list(values)
                random_weights = [random.random() + 0.1 for _ in values]
                total_weight = sum(random_weights)

                self.theta[mode][feature] = {
                    value: random_weights[i] / total_weight
                    for i, value in enumerate(values)
                }

    def observation_probability_given_mode(self, obs, mode):
        probability = self.pi[mode]

        for feature, value in obs.items():
            probability *= self.theta[mode][feature].get(value, self.smoothing)

        return max(probability, self.smoothing)

    def e_step(self, observations):
        responsibilities = []

        for obs in observations:
            raw_probs = {}

            for mode in HIDDEN_MODES:
                raw_probs[mode] = self.observation_probability_given_mode(obs, mode)

            total = sum(raw_probs.values()) + self.smoothing

            responsibilities.append({
                mode: raw_probs[mode] / total
                for mode in HIDDEN_MODES
            })

        return responsibilities

    def m_step(self, observations, responsibilities):
        n = len(observations)

        for mode in HIDDEN_MODES:
            mode_weight = sum(resp[mode] for resp in responsibilities)

            self.pi[mode] = (mode_weight + self.smoothing) / (
                n + self.smoothing * len(HIDDEN_MODES)
            )

            for feature, values in self.feature_values.items():
                denom = mode_weight + self.smoothing * len(values)

                for value in values:
                    numerator = self.smoothing

                    for obs, resp in zip(observations, responsibilities):
                        if obs[feature] == value:
                            numerator += resp[mode]

                    self.theta[mode][feature][value] = numerator / denom

    def compute_log_likelihood(self, observations):
        total_log_likelihood = 0.0

        for obs in observations:
            probability = sum(
                self.observation_probability_given_mode(obs, mode)
                for mode in HIDDEN_MODES
            )

            total_log_likelihood += math.log(probability + self.smoothing)

        return total_log_likelihood

    def train(self, observations):
        self.initialize_parameters(observations)

        self.log_likelihood_history = []

        for _ in range(self.iterations):
            responsibilities = self.e_step(observations)
            self.m_step(observations, responsibilities)
            log_likelihood = self.compute_log_likelihood(observations)
            self.log_likelihood_history.append(log_likelihood)

        self.is_trained = True

    def rule_adjusted_mode_scores(self, obs):
        """
        This does not replace EM. It adjusts the EM posterior with domain evidence
        from the campus simulation so the final output is useful and explainable.

        Think of this as combining learned probabilistic mode estimates with
        symbolic evidence from the agent's observed state.
        """

        scores = {mode: 1.0 for mode in HIDDEN_MODES}

        time_bucket = obs["time_bucket"]
        current_cat = obs["current_location_category"]
        expected_cat = obs["expected_location_category"]
        rebel_status = obs["rebel_status"]
        personality = obs["personality"]
        student_type = obs["student_type"]

        if current_cat == "class_location" or expected_cat == "class_location":
            scores["CLASS_MODE"] += 3.0

        if current_cat == "study_location":
            scores["STUDY_MODE"] += 4.0

        if current_cat == "practice_location" or expected_cat == "practice_location":
            scores["PRACTICE_MODE"] += 4.0

        if current_cat == "social_location":
            scores["SOCIAL_MODE"] += 3.5

        if current_cat == "rest_location":
            scores["REST_MODE"] += 3.5

        if rebel_status == "rebel":
            scores["REBEL_MODE"] += 5.0

        if time_bucket == "free_time":
            scores["FREE_TIME_MODE"] += 5.0

        if time_bucket == "sleep":
            scores["REST_MODE"] += 4.0

        if personality == "social":
            scores["SOCIAL_MODE"] += 1.5

        if personality == "tired":
            scores["REST_MODE"] += 1.5

        if personality == "risk-taking":
            scores["REBEL_MODE"] += 1.5

        if student_type == "Athlete" and (
            current_cat == "practice_location" or expected_cat == "practice_location"
        ):
            scores["PRACTICE_MODE"] += 2.0

        return scores

    def infer(self, agent):
        if not self.is_trained:
            observations = generate_synthetic_observations()
            self.train(observations)

        obs = build_observation_from_agent(agent)

        raw_probs = {
            mode: self.observation_probability_given_mode(obs, mode)
            for mode in HIDDEN_MODES
        }

        total = sum(raw_probs.values()) + self.smoothing

        em_posterior = {
            mode: raw_probs[mode] / total
            for mode in HIDDEN_MODES
        }

        rule_scores = self.rule_adjusted_mode_scores(obs)

        adjusted_scores = {
            mode: em_posterior[mode] * rule_scores[mode]
            for mode in HIDDEN_MODES
        }

        adjusted_total = sum(adjusted_scores.values()) + self.smoothing

        posterior = {
            mode: adjusted_scores[mode] / adjusted_total
            for mode in HIDDEN_MODES
        }

        sorted_posterior = dict(
            sorted(posterior.items(), key=lambda item: item[1], reverse=True)
        )

        most_likely_mode = next(iter(sorted_posterior))

        return {
            "model": "Expectation-Maximization hidden activity-mode model",
            "chapter": "Chapter 20 — Learning Probabilistic Models",
            "most_likely_mode": most_likely_mode,
            "mode_probabilities": {
                mode: round(prob, 4)
                for mode, prob in sorted_posterior.items()
            },
            "observation": obs,
            "iterations": self.iterations,
            "final_log_likelihood": round(self.log_likelihood_history[-1], 4),
            "interpretation": (
                f"EM estimates that this agent is most likely in {most_likely_mode} "
                "based on observed time, location category, expected location, personality, "
                "student type, and rebel status. The posterior combines the learned EM "
                "probabilities with campus-specific evidence from the selected agent state."
            ),
        }

    def get_status(self):
        if not self.is_trained:
            observations = generate_synthetic_observations()
            self.train(observations)

        return {
            "system": "EM Hidden Activity-Mode Model",
            "chapter": "Chapter 20 — Learning Probabilistic Models",
            "implemented": True,
            "hidden_modes": HIDDEN_MODES,
            "iterations": self.iterations,
            "final_log_likelihood": round(self.log_likelihood_history[-1], 4),
            "log_likelihood_history_tail": [
                round(value, 4)
                for value in self.log_likelihood_history[-5:]
            ],
        }


EM_MODEL = EMActivityModeModel()
EM_MODEL.train(generate_synthetic_observations())


def infer_activity_mode_em(agent):
    return EM_MODEL.infer(agent)


def get_em_system_status():
    return EM_MODEL.get_status()
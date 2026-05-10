# ============================================================
# Chapter 21 — Reinforcement Learning
# Q-Learning Module for Campus Agent Decisions
#
# This module implements:
# - state abstraction
# - action set
# - reward function
# - Q-learning training loop
# - learned policy recommendation
# ============================================================

import random
from collections import defaultdict

RANDOM_SEED = 21
random.seed(RANDOM_SEED)

ACTIONS = [
    "FOLLOW_EXPECTED",
    "STAY_CURRENT",
    "GO_SOCIAL",
    "GO_HOME",
    "GO_LIBRARY",
    "REBEL",
]

SOCIAL_LOCATIONS = {"StudentCenter", "VillagePark", "BoulevardAppartments"}
CLASS_LOCATIONS = {"AcademicHall", "WestPenn"}
PERFORMANCE_LOCATIONS = {"GeorgeRowlandWhite", "PlayHouse"}
STUDY_LOCATIONS = {"Library"}
PRACTICE_LOCATIONS = {"Track"}

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


def get_time_bucket(time_slot):
    return TIME_BUCKETS.get(time_slot, "unknown")


def is_obligation_state(student_type, sport, expected_location, time_slot):
    if expected_location in CLASS_LOCATIONS:
        return True

    if student_type == "Copa" and expected_location in PERFORMANCE_LOCATIONS:
        return True

    if student_type == "Athlete" and sport == "TrackAndField":
        if time_slot in {"15:00-15:30", "16:00-17:30"}:
            return True

    return False


def build_state_from_values(
    student_type,
    personality,
    time_slot,
    expected_location,
    current_location,
    sport=None,
    missed_classes=0,
    academic_risk=0.0,
):
    time_bucket = get_time_bucket(time_slot)

    obligation = is_obligation_state(
        student_type,
        sport,
        expected_location,
        time_slot,
    )

    is_rebel = expected_location != current_location

    risk_level = "low"
    if academic_risk >= 0.50:
        risk_level = "high"
    elif academic_risk >= 0.25:
        risk_level = "medium"

    missed_level = "none"
    if missed_classes >= 2:
        missed_level = "multiple"
    elif missed_classes == 1:
        missed_level = "one"

    return (
        student_type,
        personality,
        time_bucket,
        "obligation" if obligation else "no_obligation",
        "rebel" if is_rebel else "aligned",
        risk_level,
        missed_level,
    )


def build_state(agent):
    return build_state_from_values(
        student_type=agent.get("student_type", "Regular Student"),
        personality=agent.get("personality", "responsible"),
        time_slot=agent.get("time_slot", "08:00-09:30"),
        expected_location=agent.get("expected_location_now") or agent.get("current_location"),
        current_location=agent.get("current_location"),
        sport=agent.get("sport"),
        missed_classes=agent.get("missed_classes", 0),
        academic_risk=agent.get("academic_risk", 0.0),
    )


def reward_function(state, action):
    (
        student_type,
        personality,
        time_bucket,
        obligation_status,
        rebel_status,
        risk_level,
        missed_level,
    ) = state

    reward = 0.0

    has_obligation = obligation_status == "obligation"
    is_free_time = time_bucket == "free_time"
    is_practice_time = time_bucket in {"practice_transition", "practice_time"}

    # General schedule logic
    if action == "FOLLOW_EXPECTED":
        reward += 5.0 if has_obligation else 2.0

    if action == "STAY_CURRENT":
        reward += 1.0
        if rebel_status == "rebel" and has_obligation:
            reward -= 3.0

    if action == "REBEL":
        reward -= 4.0 if has_obligation else 0.5

    # Personality preferences
    if personality == "responsible":
        if action == "FOLLOW_EXPECTED":
            reward += 2.0
        if action == "REBEL":
            reward -= 3.0

    if personality == "social":
        if action == "GO_SOCIAL":
            reward += 2.5
        if is_free_time and action == "GO_SOCIAL":
            reward += 2.0

    if personality == "tired":
        if action == "GO_HOME":
            reward += 2.5
        if has_obligation and action == "GO_HOME":
            reward -= 1.5

    if personality == "risk-taking":
        if action == "REBEL":
            reward += 1.5
        if has_obligation and action == "REBEL":
            reward -= 2.0

    # Student type rules
    if student_type == "Athlete" and is_practice_time:
        if action == "FOLLOW_EXPECTED":
            reward += 3.0
        if action == "REBEL":
            reward -= 5.0

    # Academic consequences
    if risk_level == "medium" and action == "REBEL":
        reward -= 2.0

    if risk_level == "high" and action == "REBEL":
        reward -= 4.0

    if missed_level == "one" and action == "REBEL":
        reward -= 2.0

    if missed_level == "multiple" and action == "REBEL":
        reward -= 5.0

    return reward


def transition_state(state, action):
    (
        student_type,
        personality,
        time_bucket,
        obligation_status,
        rebel_status,
        risk_level,
        missed_level,
    ) = state

    next_rebel_status = rebel_status
    next_risk_level = risk_level
    next_missed_level = missed_level

    if action == "FOLLOW_EXPECTED":
        next_rebel_status = "aligned"

    if action == "REBEL":
        next_rebel_status = "rebel"

        if risk_level == "low":
            next_risk_level = "medium"
        elif risk_level == "medium":
            next_risk_level = "high"

        if missed_level == "none":
            next_missed_level = "one"
        elif missed_level == "one":
            next_missed_level = "multiple"

    return (
        student_type,
        personality,
        time_bucket,
        obligation_status,
        next_rebel_status,
        next_risk_level,
        next_missed_level,
    )


def create_training_states():
    student_types = ["Athlete", "Copa", "Regular Student"]
    personalities = ["responsible", "social", "tired", "risk-taking"]
    time_slots = list(TIME_BUCKETS.keys())
    expected_locations = [
        "AcademicHall",
        "WestPenn",
        "StudentCenter",
        "VillagePark",
        "Library",
        "Track",
        "PlayHouse",
        "GeorgeRowlandWhite",
        "OffCampus",
    ]

    states = []

    for student_type in student_types:
        for personality in personalities:
            for time_slot in time_slots:
                for expected_location in expected_locations:
                    for current_location in expected_locations:
                        sport = "TrackAndField" if student_type == "Athlete" else None
                        state = build_state_from_values(
                            student_type=student_type,
                            personality=personality,
                            time_slot=time_slot,
                            expected_location=expected_location,
                            current_location=current_location,
                            sport=sport,
                            missed_classes=0,
                            academic_risk=0.0,
                        )
                        states.append(state)

    return list(set(states))


class QLearningCampusAgent:
    def __init__(
        self,
        alpha=0.15,
        gamma=0.90,
        epsilon=0.20,
        epsilon_decay=0.995,
        epsilon_min=0.02,
        training_episodes=2500,
    ):
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.training_episodes = training_episodes
        self.q_table = defaultdict(lambda: {action: 0.0 for action in ACTIONS})
        self.training_rewards = []
        self.is_trained = False

    def choose_action(self, state):
        if random.random() < self.epsilon:
            return random.choice(ACTIONS)

        q_values = self.q_table[state]
        return max(q_values, key=q_values.get)

    def train(self):
        states = create_training_states()

        for _ in range(self.training_episodes):
            state = random.choice(states)
            total_reward = 0.0

            for _step in range(8):
                action = self.choose_action(state)
                reward = reward_function(state, action)
                next_state = transition_state(state, action)

                old_q = self.q_table[state][action]
                best_next_q = max(self.q_table[next_state].values())

                new_q = old_q + self.alpha * (
                    reward + self.gamma * best_next_q - old_q
                )

                self.q_table[state][action] = new_q
                state = next_state
                total_reward += reward

            self.training_rewards.append(total_reward)
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)

        self.is_trained = True

    def recommend_action(self, agent):
        if not self.is_trained:
            self.train()

        state = build_state(agent)
        q_values = self.q_table[state]

        best_action = max(q_values, key=q_values.get)

        sorted_q_values = dict(
            sorted(q_values.items(), key=lambda item: item[1], reverse=True)
        )

        return {
            "model": "Q-learning",
            "chapter": "Chapter 21 — Reinforcement Learning",
            "state": {
                "student_type": state[0],
                "personality": state[1],
                "time_bucket": state[2],
                "obligation_status": state[3],
                "alignment_status": state[4],
                "academic_risk_level": state[5],
                "missed_class_level": state[6],
            },
            "recommended_action": best_action,
            "q_values": {
                action: round(value, 4)
                for action, value in sorted_q_values.items()
            },
            "training_episodes": self.training_episodes,
            "training_average_reward_last_100": round(
                sum(self.training_rewards[-100:]) / max(1, len(self.training_rewards[-100:])),
                4,
            ),
            "interpretation": (
                f"The learned Q-table recommends {best_action} because it has the highest "
                "learned long-term reward for this agent state."
            ),
        }

    def get_status(self):
        if not self.is_trained:
            self.train()

        return {
            "system": "Q-Learning Campus Decision Model",
            "chapter": "Chapter 21 — Reinforcement Learning",
            "implemented": True,
            "actions": ACTIONS,
            "training_episodes": self.training_episodes,
            "states_learned": len(self.q_table),
            "epsilon_final": round(self.epsilon, 4),
            "average_reward_last_100": round(
                sum(self.training_rewards[-100:]) / max(1, len(self.training_rewards[-100:])),
                4,
            ),
        }


RL_MODEL = QLearningCampusAgent()
RL_MODEL.train()


def get_rl_recommendation(agent):
    return RL_MODEL.recommend_action(agent)


def get_rl_system_status():
    return RL_MODEL.get_status()
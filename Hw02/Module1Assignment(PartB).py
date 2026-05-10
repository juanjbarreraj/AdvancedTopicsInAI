from dataclasses import dataclass
from typing import Dict, List, Tuple, Callable
import math

# -----------------------------
# 1) Uncertain world variable
# -----------------------------
# World state: Traffic ∈ {Heavy, Light}
STATES = ["Heavy", "Light"]

# Prior belief P(Traffic)
prior: Dict[str, float] = {
    "Heavy": 0.4,
    "Light": 0.6,
}

# -----------------------------
# 2) Actions (at least two)
# -----------------------------
# Two "act" actions plus an optional "sense" action
ACTIONS = ["Highway", "SideRoad"]
SENSE_ACTION = "CheckTraffic"  # information-gathering action

# -----------------------------
# 3) Utility function
# -----------------------------
# Utility can be anything; here it's "negative cost" (higher is better).
# We'll define costs by (action, state) then utility = -cost.
costs: Dict[Tuple[str, str], float] = {
    ("Highway", "Light"): 10,
    ("Highway", "Heavy"): 35,
    ("SideRoad", "Light"): 18,
    ("SideRoad", "Heavy"): 22,
}

def utility(action: str, state: str) -> float:
    """Utility is negative travel time/cost (maximize utility)."""
    return -costs[(action, state)]

# -----------------------------
# 4) Expected utility
# -----------------------------
def expected_utility(action: str, belief: Dict[str, float]) -> float:
    return sum(belief[s] * utility(action, s) for s in STATES)

def best_action(belief: Dict[str, float], actions: List[str] = ACTIONS) -> Tuple[str, float]:
    eus = {a: expected_utility(a, belief) for a in actions}
    a_star = max(eus, key=eus.get)
    return a_star, eus[a_star]

# -----------------------------
# 5) Information model (sensor)
# -----------------------------
# Observation O ∈ {ReportHeavy, ReportLight}
OBS = ["ReportHeavy", "ReportLight"]

# Likelihood P(O | Traffic)
# Sensor is imperfect: 80% correct
likelihood: Dict[Tuple[str, str], float] = {
    ("ReportHeavy", "Heavy"): 0.8,
    ("ReportLight", "Heavy"): 0.2,
    ("ReportHeavy", "Light"): 0.2,
    ("ReportLight", "Light"): 0.8,
}

def p_obs_given_state(obs: str, state: str) -> float:
    return likelihood[(obs, state)]

def p_obs(obs: str, belief: Dict[str, float]) -> float:
    """Marginal P(obs) = Σ_s P(obs|s)P(s)."""
    return sum(p_obs_given_state(obs, s) * belief[s] for s in STATES)

def bayes_update(belief: Dict[str, float], obs: str) -> Dict[str, float]:
    """Posterior P(s|obs) ∝ P(obs|s)P(s)."""
    unnorm = {s: p_obs_given_state(obs, s) * belief[s] for s in STATES}
    z = sum(unnorm.values())
    if z == 0:
        # Shouldn't happen with sane probabilities, but keep safe behavior.
        return belief.copy()
    return {s: unnorm[s] / z for s in STATES}

# -----------------------------
# 6) Value of information (VOI)
# -----------------------------
def expected_utility_with_information(
    belief: Dict[str, float],
    actions: List[str] = ACTIONS
) -> float:
    """
    EU if we first observe (via sensor) and then choose best action for each observation.
    This is: Σ_o P(o) * max_a EU(a | P(s|o))
    """
    total = 0.0
    for obs in OBS:
        po = p_obs(obs, belief)
        post = bayes_update(belief, obs)
        _, best_eu_post = best_action(post, actions)
        total += po * best_eu_post
    return total

def value_of_information(belief: Dict[str, float], info_cost: float = 0.0) -> float:
    """
    VOI = (EU with information - cost_of_info) - EU without information
    """
    _, eu_without = best_action(belief, ACTIONS)
    eu_with = expected_utility_with_information(belief, ACTIONS) - info_cost
    return eu_with - eu_without

# -----------------------------
# 7) Agent policy: choose act vs sense
# -----------------------------
@dataclass
class RationalAgent:
    belief: Dict[str, float]
    info_cost: float = 2.0  # checking traffic takes time/effort

    def choose(self) -> str:
        """
        Choose between directly acting or gathering info, based on expected utility.
        """
        # Best direct action
        direct_action, eu_direct = best_action(self.belief, ACTIONS)

        # EU if we check first, then act optimally
        eu_check_then_act = expected_utility_with_information(self.belief, ACTIONS) - self.info_cost

        # Pick whichever has higher expected utility
        if eu_check_then_act > eu_direct:
            return SENSE_ACTION
        return direct_action

    def act_after_observation(self, obs: str) -> str:
        """After sensing, update beliefs and choose best action."""
        self.belief = bayes_update(self.belief, obs)
        action, _ = best_action(self.belief, ACTIONS)
        return action

# -----------------------------
# Demo run
# -----------------------------
if __name__ == "__main__":
    agent = RationalAgent(belief=prior.copy(), info_cost=2.0)

    # Print expected utilities of direct actions
    print("Prior belief:", agent.belief)
    for a in ACTIONS:
        print(f"EU({a}) = {expected_utility(a, agent.belief):.3f}")

    best_direct, eu_best_direct = best_action(agent.belief, ACTIONS)
    print(f"\nBest direct action: {best_direct} with EU = {eu_best_direct:.3f}")

    eu_info = expected_utility_with_information(agent.belief, ACTIONS)
    voi = value_of_information(agent.belief, info_cost=agent.info_cost)
    print(f"EU(with info, before info_cost) = {eu_info:.3f}")
    print(f"Value of Information (VOI) with info_cost={agent.info_cost} = {voi:.3f}")

    choice = agent.choose()
    print(f"\nAgent chooses: {choice}")

    # If the agent chooses to check, simulate an observation
    if choice == SENSE_ACTION:
        # Example: pretend the sensor reports "Heavy"
        obs = "ReportHeavy"
        next_action = agent.act_after_observation(obs)
        print(f"Observed: {obs}")
        print("Posterior belief:", agent.belief)
        print("Then agent acts:", next_action)

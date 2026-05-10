from collections import Counter, defaultdict
import math


CAMPUS_GRAPH = {
    "VillagePark": ["StudentCenter", "LawrenceHall", "Track"],
    "BoulevardAppartments": ["StudentCenter", "WestPenn", "GeorgeRowlandWhite"],
    "StudentCenter": ["VillagePark", "BoulevardAppartments", "WestPenn", "LawrenceHall", "Library"],
    "WestPenn": ["StudentCenter", "BoulevardAppartments", "AcademicHall", "GeorgeRowlandWhite"],
    "ConestogaHall": ["LawrenceHall", "AcademicHall"],
    "LawrenceHall": ["ConestogaHall", "ThayerHall", "StudentCenter", "VillagePark"],
    "ThayerHall": ["LawrenceHall", "Library"],
    "AcademicHall": ["ConestogaHall", "WestPenn", "Library"],
    "GeorgeRowlandWhite": ["WestPenn", "BoulevardAppartments", "PlayHouse"],
    "Library": ["ThayerHall", "AcademicHall", "StudentCenter", "PlayHouse"],
    "PlayHouse": ["Library", "GeorgeRowlandWhite"],
    "Track": ["VillagePark", "StudentCenter"],
    "OffCampus": ["StudentCenter", "BoulevardAppartments", "WestPenn"],
}


LOCATION_LABELS = {
    "VillagePark": "Village Park",
    "BoulevardAppartments": "Boulevard Apartments",
    "StudentCenter": "Student Center",
    "WestPenn": "West Penn",
    "ConestogaHall": "Conestoga Hall",
    "LawrenceHall": "Lawrence Hall",
    "ThayerHall": "Thayer Hall",
    "AcademicHall": "Academic Hall",
    "GeorgeRowlandWhite": "George Rowland White",
    "Library": "Library",
    "PlayHouse": "Playhouse",
    "Track": "Track",
    "OffCampus": "Off Campus",
}


STUDENT_TYPE_LOCATION_FIT = {
    "Athlete": {
        "Track": 1.0,
        "StudentCenter": 0.8,
        "WestPenn": 0.65,
        "VillagePark": 0.55,
        "Library": 0.45,
        "AcademicHall": 0.45,
        "OffCampus": 0.35,
    },
    "Copa": {
        "PlayHouse": 1.0,
        "GeorgeRowlandWhite": 0.95,
        "LawrenceHall": 0.75,
        "AcademicHall": 0.55,
        "Library": 0.5,
        "StudentCenter": 0.45,
        "OffCampus": 0.35,
    },
    "Regular Student": {
        "Library": 1.0,
        "AcademicHall": 0.9,
        "StudentCenter": 0.8,
        "ThayerHall": 0.65,
        "LawrenceHall": 0.6,
        "WestPenn": 0.55,
        "OffCampus": 0.4,
    },
}


ACTIVITY_MODE_RULES = {
    "Track": "athletic_training",
    "StudentCenter": "campus_activity",
    "WestPenn": "academic_or_athletic_support",
    "VillagePark": "social_or_transition",
    "Library": "study",
    "AcademicHall": "academic_class",
    "ThayerHall": "academic_class",
    "LawrenceHall": "academic_or_performance_support",
    "PlayHouse": "performance_or_rehearsal",
    "GeorgeRowlandWhite": "performance_or_rehearsal",
    "BoulevardAppartments": "residential_life",
    "ConestogaHall": "residential_life",
    "OffCampus": "off_campus",
}


def format_location(location):
    return LOCATION_LABELS.get(location, location or "Unknown")


def shortest_path_distance(start, goal):
    if start == goal:
        return 0

    if start not in CAMPUS_GRAPH or goal not in CAMPUS_GRAPH:
        return 4

    queue = [(start, 0)]
    visited = {start}

    while queue:
        current, distance = queue.pop(0)

        for neighbor in CAMPUS_GRAPH.get(current, []):
            if neighbor == goal:
                return distance + 1

            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, distance + 1))

    return 4


def estimate_busy_beliefs(all_agents):
    """
    Week 1/2 connection:
    This approximates P(Busy(location)) from the current visible agent state.
    Instead of using hidden Monte Carlo traces here, the live app estimates
    crowding from the current multiagent distribution.
    """
    total_agents = max(len(all_agents), 1)
    location_counts = Counter(
        agent.get("current_location", "Unknown") for agent in all_agents
    )

    busy_beliefs = {}

    for location, count in location_counts.items():
        fraction = count / total_agents

        busy_beliefs[location] = {
            "location": location,
            "display_location": format_location(location),
            "agent_count": count,
            "total_agents": total_agents,
            "estimated_busy_probability": round(min(1.0, fraction * 2.2), 4),
            "crowd_fraction": round(fraction, 4),
        }

    return busy_beliefs


def infer_activity_mode(agent):
    """
    Week 6 connection:
    This is a live hidden-mode inference layer. It infers an activity mode
    from student type, sport, time slot, current location, and next destination.
    """
    student_type = agent.get("student_type", "Unknown")
    sport = agent.get("sport")
    current_location = agent.get("current_location")
    next_destination = agent.get("next_destination")
    time_slot = agent.get("time_slot", "")

    base_mode = ACTIVITY_MODE_RULES.get(current_location, "unknown_activity")

    if student_type == "Athlete":
        if current_location == "Track" or next_destination == "Track":
            return {
                "activity_mode": "athletic_training",
                "confidence": 0.92,
                "reason": "Athlete is currently at or moving toward Track.",
            }

        if sport and current_location in {"StudentCenter", "WestPenn"}:
            return {
                "activity_mode": "athletic_support",
                "confidence": 0.78,
                "reason": "Athlete is in a location commonly associated with athletic support or campus preparation.",
            }

    if student_type == "Copa":
        if current_location in {"PlayHouse", "GeorgeRowlandWhite"} or next_destination in {"PlayHouse", "GeorgeRowlandWhite"}:
            return {
                "activity_mode": "performance_or_rehearsal",
                "confidence": 0.9,
                "reason": "COPA student is located in or moving toward a performance-related space.",
            }

    if student_type == "Regular Student":
        if current_location in {"Library", "AcademicHall", "ThayerHall"}:
            return {
                "activity_mode": "academic_study_or_class",
                "confidence": 0.85,
                "reason": "Regular student is in an academic or study-focused location.",
            }

    if "18:00" in time_slot and next_destination == "OffCampus":
        return {
            "activity_mode": "leaving_campus",
            "confidence": 0.8,
            "reason": "The time slot is late in the day and the next destination is Off Campus.",
        }

    return {
        "activity_mode": base_mode,
        "confidence": 0.65,
        "reason": f"The current location is associated with {base_mode}.",
    }


def score_location_fit(student_type, location):
    type_table = STUDENT_TYPE_LOCATION_FIT.get(student_type, {})
    return type_table.get(location, 0.35)


def compute_expected_utilities(agent, all_agents):
    """
    Week 2 connection:
    Computes expected utility over possible destinations.

    Utility = location fit reward - walking cost - crowding cost - mismatch cost
    """
    student_type = agent.get("student_type", "Unknown")
    current_location = agent.get("current_location")
    scheduled_next = agent.get("next_destination")

    busy_beliefs = estimate_busy_beliefs(all_agents)

    candidate_locations = set(CAMPUS_GRAPH.keys())
    if scheduled_next:
        candidate_locations.add(scheduled_next)

    utilities = []

    for destination in sorted(candidate_locations):
        distance = shortest_path_distance(current_location, destination)
        fit_score = score_location_fit(student_type, destination)

        busy_probability = busy_beliefs.get(destination, {}).get(
            "estimated_busy_probability", 0.0
        )

        scheduled_bonus = 2.0 if destination == scheduled_next else 0.0
        walking_cost = distance * 0.7
        crowding_cost = busy_probability * 1.5
        mismatch_cost = (1.0 - fit_score) * 1.2

        utility = scheduled_bonus + (fit_score * 3.0) - walking_cost - crowding_cost - mismatch_cost

        utilities.append({
            "destination": destination,
            "display_destination": format_location(destination),
            "distance": distance,
            "fit_score": round(fit_score, 4),
            "busy_probability": round(busy_probability, 4),
            "scheduled_bonus": round(scheduled_bonus, 4),
            "walking_cost": round(walking_cost, 4),
            "crowding_cost": round(crowding_cost, 4),
            "mismatch_cost": round(mismatch_cost, 4),
            "expected_utility": round(utility, 4),
        })

    utilities.sort(key=lambda item: item["expected_utility"], reverse=True)

    return {
        "best_destination": utilities[0],
        "top_utilities": utilities[:5],
    }


def compute_value_of_information(agent, all_agents):
    """
    Week 2 connection:
    Simplified live VOI estimate for checking crowd conditions.
    """
    utility_info = compute_expected_utilities(agent, all_agents)
    best_utility = utility_info["best_destination"]["expected_utility"]

    current_location = agent.get("current_location")
    next_destination = agent.get("next_destination")

    busy_beliefs = estimate_busy_beliefs(all_agents)
    next_busy = busy_beliefs.get(next_destination, {}).get(
        "estimated_busy_probability", 0.0
    )

    info_cost = 0.25
    possible_gain_from_checking = next_busy * 0.9

    voi = possible_gain_from_checking - info_cost

    return {
        "information_action": "Check destination crowd before moving",
        "current_location": format_location(current_location),
        "destination_to_check": format_location(next_destination),
        "best_direct_utility": best_utility,
        "estimated_busy_probability_at_destination": round(next_busy, 4),
        "information_cost": info_cost,
        "estimated_value_of_information": round(voi, 4),
        "recommend_checking": voi > 0,
    }


def analyze_multiagent_congestion(agent, all_agents):
    """
    Week 4 connection:
    Detects shared-destination competition and congestion.
    """
    current_location = agent.get("current_location")
    next_destination = agent.get("next_destination")

    current_counts = Counter(a.get("current_location") for a in all_agents)
    next_counts = Counter(a.get("next_destination") for a in all_agents)

    agents_sharing_current = [
        a.get("agent_id") for a in all_agents
        if a.get("current_location") == current_location
    ]

    agents_sharing_next = [
        a.get("agent_id") for a in all_agents
        if a.get("next_destination") == next_destination
    ]

    congestion_level = "low"
    if next_counts[next_destination] >= 4:
        congestion_level = "high"
    elif next_counts[next_destination] >= 2:
        congestion_level = "medium"

    return {
        "current_location": format_location(current_location),
        "next_destination": format_location(next_destination),
        "total_agents_considered": len(all_agents),
        "agents_at_current_location": agents_sharing_current,
        "agents_targeting_same_destination": agents_sharing_next,
        "current_location_count": current_counts[current_location],
        "next_destination_count": next_counts[next_destination],
        "congestion_level": congestion_level,
        "multiagent_interpretation": (
            f"{len(agents_sharing_next)} agent(s) are targeting {format_location(next_destination)}. "
            f"This creates a {congestion_level} congestion effect."
        ),
    }


def rl_style_action_recommendation(agent):
    """
    Week 8 connection:
    Simplified RL-style reward evaluation for STAY vs MOVE.
    """
    current_location = agent.get("current_location")
    next_destination = agent.get("next_destination")
    student_type = agent.get("student_type", "Unknown")
    sport = agent.get("sport")

    distance = shortest_path_distance(current_location, next_destination)

    stay_reward = 0.0
    move_reward = 0.0

    if current_location == next_destination:
        stay_reward += 3.0
        move_reward -= 1.0
    else:
        move_reward += 2.0
        move_reward -= distance * 0.4
        stay_reward -= 1.5

    if student_type == "Athlete" and sport == "TrackAndField" and next_destination == "Track":
        move_reward += 2.0

    if student_type == "Copa" and next_destination in {"PlayHouse", "GeorgeRowlandWhite"}:
        move_reward += 2.0

    if student_type == "Regular Student" and next_destination in {"Library", "AcademicHall"}:
        move_reward += 1.5

    recommended_action = "STAY" if stay_reward >= move_reward else "MOVE"

    return {
        "state": {
            "current_location": current_location,
            "next_destination": next_destination,
            "student_type": student_type,
            "sport": sport,
        },
        "available_actions": ["STAY", "MOVE"],
        "q_style_scores": {
            "STAY": round(stay_reward, 4),
            "MOVE": round(move_reward, 4),
        },
        "recommended_action": recommended_action,
        "interpretation": (
            f"The RL-style policy recommends {recommended_action} because it has the higher estimated reward."
        ),
    }


def estimate_probability_to_destination(agent, all_agents):
    """
    Week 5/6 connection:
    Produces a probability-like estimate for the scheduled next destination.
    """
    student_type = agent.get("student_type", "Unknown")
    current_location = agent.get("current_location")
    next_destination = agent.get("next_destination")

    fit_score = score_location_fit(student_type, next_destination)
    distance = shortest_path_distance(current_location, next_destination)

    busy_beliefs = estimate_busy_beliefs(all_agents)
    busy_probability = busy_beliefs.get(next_destination, {}).get(
        "estimated_busy_probability", 0.0
    )

    distance_factor = max(0.2, 1.0 - (distance * 0.12))
    crowd_factor = max(0.3, 1.0 - (busy_probability * 0.35))

    probability = fit_score * distance_factor * crowd_factor

    if next_destination == current_location:
        probability = max(probability, 0.85)

    return {
        "target_destination": next_destination,
        "display_target_destination": format_location(next_destination),
        "student_type_fit": round(fit_score, 4),
        "distance_factor": round(distance_factor, 4),
        "crowd_factor": round(crowd_factor, 4),
        "estimated_probability": round(min(1.0, probability), 4),
    }


def run_campus_ai_reasoning(agent, all_agents):
    """
    Master function used by Flask.

    This combines the semester AI modules into one live reasoning object.
    """
    return {
        "belief_estimation": estimate_busy_beliefs(all_agents),
        "activity_mode_inference": infer_activity_mode(agent),
        "expected_utility": compute_expected_utilities(agent, all_agents),
        "value_of_information": compute_value_of_information(agent, all_agents),
        "multiagent_congestion": analyze_multiagent_congestion(agent, all_agents),
        "rl_action_recommendation": rl_style_action_recommendation(agent),
        "probability_to_destination": estimate_probability_to_destination(agent, all_agents),
"implemented_ai_layers": [
    "Crowd belief estimation from live multiagent state",
    "Expected utility decision scoring",
    "Value of information estimation",
    "Hidden activity-mode inference",
    "Multiagent congestion analysis",
    "Graph-based movement distance",
    "Q-style reward action scoring",
    "Probability-to-destination estimation",
],
    }
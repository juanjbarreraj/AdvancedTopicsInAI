from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)

ALLOWED_ORIGINS = {
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://finalprojectjuanbarrera.netlify.app",
}

CORS(
    app,
    resources={r"/*": {"origins": list(ALLOWED_ORIGINS)}},
    supports_credentials=False,
)


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin")

    if origin in ALLOWED_ORIGINS:
        response.headers["Access-Control-Allow-Origin"] = origin

    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

    return response


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({"message": "CORS preflight OK"})

        origin = request.headers.get("Origin")

        if origin in ALLOWED_ORIGINS:
            response.headers["Access-Control-Allow-Origin"] = origin

        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"

        return response


def get_predict_intent():
    from neural_nlp_engine import predict_intent
    return predict_intent


def get_nlp_status_function():
    from neural_nlp_engine import get_nlp_system_status
    return get_nlp_system_status


def get_campus_reasoner():
    from campus_ai_reasoner import run_campus_ai_reasoning
    return run_campus_ai_reasoning


def get_rl_functions():
    from rl_agent_trainer import get_rl_recommendation, get_rl_system_status
    return get_rl_recommendation, get_rl_system_status


def get_em_functions():
    from em_activity_model import infer_activity_mode_em, get_em_system_status
    return infer_activity_mode_em, get_em_system_status


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

LOCATION_ALIASES = {
    "VillagePark": ["village park", "villagepark", "park"],
    "BoulevardAppartments": [
        "boulevard apartments",
        "boulevard appartments",
        "boulevard",
        "apartments",
    ],
    "StudentCenter": ["student center", "studentcenter", "center"],
    "WestPenn": ["west penn", "westpenn"],
    "ConestogaHall": ["conestoga hall", "conestoga"],
    "LawrenceHall": ["lawrence hall", "lawrence"],
    "ThayerHall": ["thayer hall", "thayer"],
    "AcademicHall": ["academic hall", "academic"],
    "GeorgeRowlandWhite": [
        "george rowland white",
        "grw",
        "performance center",
        "rowland white",
    ],
    "Library": ["library", "the library"],
    "PlayHouse": ["playhouse", "play house"],
    "Track": ["track", "the track"],
    "OffCampus": ["off campus", "offcampus", "home"],
}

# Real class locations only.
CLASS_LOCATIONS = {
    "AcademicHall",
    "WestPenn",
}

# These are obligations for COPA students, but not normal classroom locations.
PERFORMANCE_OBLIGATION_LOCATIONS = {
    "GeorgeRowlandWhite",
    "PlayHouse",
}

# These are explicitly NOT class locations.
STUDY_LOCATIONS = {
    "Library",
}

DORM_LOCATIONS = {
    "ThayerHall",
    "LawrenceHall",
    "BoulevardAppartments",
    "ConestogaHall",
}


def format_location(location):
    return LOCATION_LABELS.get(location, location or "Unknown")


def normalize_text(text):
    return (text or "").lower().strip()


def extract_location_from_question(question):
    question_lower = normalize_text(question)

    for canonical, aliases in LOCATION_ALIASES.items():
        for alias in aliases:
            if alias in question_lower:
                return canonical

    return None


def classify_reason_quality(question):
    question_lower = normalize_text(question)

    health_markers = [
        "tired",
        "exhausted",
        "sick",
        "mental",
        "break",
        "stress",
        "stressed",
        "anxious",
        "health",
        "overwhelmed",
    ]

    weak_markers = [
        "because i want",
        "just because",
        "for fun",
        "bored",
        "dont want",
        "don't want",
        "skip it",
    ]

    academic_markers = [
        "study",
        "assignment",
        "exam",
        "project",
        "homework",
        "deadline",
    ]

    importance_markers = [
        "important",
        "urgent",
        "necessary",
        "required",
        "need",
        "practice",
        "meeting",
        "coach",
        "emergency",
        "responsibility",
    ]

    if any(marker in question_lower for marker in health_markers):
        return {
            "quality": "health_or_wellbeing_reason",
            "score": 0.85,
            "reason": "The user gave a health, stress, tiredness, or wellbeing reason.",
        }

    if any(marker in question_lower for marker in academic_markers):
        return {
            "quality": "academic_reason",
            "score": 0.70,
            "reason": "The user gave an academic workload reason.",
        }

    if any(marker in question_lower for marker in importance_markers):
        return {
            "quality": "important_obligation_reason",
            "score": 0.75,
            "reason": "The user gave an importance-based or obligation-based reason.",
        }

    if any(marker in question_lower for marker in weak_markers):
        return {
            "quality": "weak_reason",
            "score": 0.20,
            "reason": "The user gave a weak or convenience-based reason.",
        }

    return {
        "quality": "unclear_reason",
        "score": 0.45,
        "reason": "The user gave a reason, but it is not strongly justified.",
    }


def classify_request_tone(question):
    question_lower = normalize_text(question)

    polite_markers = [
        "please",
        "could you",
        "can you",
        "as a favor",
        "do me a favor",
        "it is important",
        "i need you to",
        "would you",
    ]

    forceful_markers = [
        "i order you",
        "just do it",
        "because i want",
        "do it now",
        "you must",
        "i command you",
    ]

    if any(marker in question_lower for marker in forceful_markers):
        return {
            "tone": "forceful_order",
            "is_polite_or_reasoned": False,
            "reason": "The request uses forceful or controlling language.",
        }

    if any(marker in question_lower for marker in polite_markers):
        return {
            "tone": "polite_or_reasoned_request",
            "is_polite_or_reasoned": True,
            "reason": "The request includes politeness or a reason for cooperation.",
        }

    return {
        "tone": "neutral_request",
        "is_polite_or_reasoned": False,
        "reason": "The request does not include enough politeness or justification.",
    }


def get_agents_in_same_location(agent, all_agents):
    current_location = agent.get("current_location")
    companions = []

    for other_agent in all_agents:
        if other_agent.get("agent_id") == agent.get("agent_id"):
            continue

        if other_agent.get("current_location") == current_location:
            companions.append(other_agent)

    return companions


def get_expected_location(agent):
    return agent.get("expected_location_now") or agent.get("current_location")


def is_class_or_obligation_time(agent):
    """
    This checks where the agent is SUPPOSED to be, not only where the agent
    currently is. This matters because rebel agents may currently be somewhere
    else while still being expected to attend class/practice/rehearsal.
    """
    time_slot = agent.get("time_slot")
    expected_location = get_expected_location(agent)
    student_type = agent.get("student_type")
    sport = agent.get("sport")

    class_slots = {
        "08:00-09:30",
        "09:40-11:10",
        "11:20-12:50",
        "13:00-14:30",
        "18:00-21:00",
    }

    if time_slot in class_slots and expected_location in CLASS_LOCATIONS:
        return True

    if (
        student_type == "Copa"
        and time_slot in class_slots
        and expected_location in PERFORMANCE_OBLIGATION_LOCATIONS
    ):
        return True

    if student_type == "Athlete" and sport == "TrackAndField":
        if time_slot in {"15:00-15:30", "16:00-17:30"}:
            return True

    return False


def get_obligation_type(agent):
    expected_location = get_expected_location(agent)
    student_type = agent.get("student_type")
    sport = agent.get("sport")
    time_slot = agent.get("time_slot")

    if expected_location in CLASS_LOCATIONS:
        return "class"

    if student_type == "Copa" and expected_location in PERFORMANCE_OBLIGATION_LOCATIONS:
        return "performance/rehearsal obligation"

    if student_type == "Athlete" and sport == "TrackAndField":
        if time_slot in {"15:00-15:30", "16:00-17:30"}:
            return "track practice"

    if expected_location in STUDY_LOCATIONS:
        return "study period"

    if expected_location in DORM_LOCATIONS:
        return "residential/home period"

    return "campus activity"


def get_personality_voice(agent):
    personality = agent.get("personality")

    if personality == "responsible":
        return "I try to stay on schedule and make decisions carefully."

    if personality == "social":
        return "I like being around people and I usually pay attention to who is nearby."

    if personality == "tired":
        return "I am a little tired, so I prefer lower-effort choices when I can."

    if personality == "risk-taking":
        return "I am more open to changing plans, but I still consider the consequences."

    return "I make decisions based on my schedule and current situation."


def get_free_time_reason(agent):
    current_location = agent.get("current_location")
    personality = agent.get("personality")
    student_type = agent.get("student_type")
    housing_location = agent.get("housing_location")

    if current_location == "VillagePark":
        if personality == "social":
            return (
                "I am at Village Park because it is free time, and this is a good place "
                "to socialize outside."
            )

        return (
            "I am at Village Park because it is free time, and I chose an open campus "
            "space instead of a class or scheduled obligation."
        )

    if current_location == "StudentCenter":
        if personality == "social":
            return (
                "I am at the Student Center because it is free time, and I wanted to be "
                "around other students."
            )

        if personality == "tired":
            return (
                "I am at the Student Center because it is free time, and it is a convenient "
                "low-effort place to relax."
            )

        return (
            "I am at the Student Center because it is free time, and it is a common place "
            "for food, social activity, or relaxing."
        )

    if current_location == "BoulevardAppartments":
        if housing_location == "BoulevardAppartments":
            return (
                "I am at Boulevard Apartments because it is free time, and this is my "
                "housing location."
            )

        return (
            "I am at Boulevard Apartments because it is free time, and I chose a residential "
            "social space."
        )

    if current_location == "OffCampus":
        return (
            "I am Off Campus because it is free time, so I am not required to be in an "
            "academic or practice location."
        )

    return (
        f"I am at {format_location(current_location)} because it is free time. "
        f"As a {student_type}, I can choose activities more freely during this period."
    )


def choose_skip_location(agent):
    personality = agent.get("personality")
    housing_location = agent.get("housing_location")
    student_type = agent.get("student_type")
    sport = agent.get("sport")

    if personality == "responsible":
        return "Library"

    if personality == "social":
        return "StudentCenter"

    if personality == "tired":
        return housing_location or "OffCampus"

    if personality == "risk-taking":
        return "VillagePark"

    if student_type == "Athlete" and sport == "TrackAndField":
        return "StudentCenter"

    return "StudentCenter"


def start_miss_class_conversation(agent):
    expected_location = get_expected_location(agent)
    current_location = agent.get("current_location")
    obligation_type = get_obligation_type(agent)
    missed_classes = agent.get("missed_classes", 0)
    reliability_score = agent.get("reliability_score", 1.0)

    if not is_class_or_obligation_time(agent):
        if expected_location in STUDY_LOCATIONS:
            return {
                "answer": (
                    f"I am not currently expected to be in class. I am expected to be at "
                    f"{format_location(expected_location)}, which is a study location, so there is no class to miss."
                ),
                "requires_followup": False,
                "conversation_state": None,
                "pending_decision": None,
                "miss_class_decision": {
                    "accepted": False,
                    "decision": "not_applicable",
                    "reason": "The agent is not currently expected to be in class or a mandatory obligation.",
                },
            }

        return {
            "answer": (
                "I am not currently expected to be in class or a required obligation, "
                "so there is no class to miss right now."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "miss_class_decision": {
                "accepted": False,
                "decision": "not_applicable",
                "reason": "The agent is not currently expected to be in class or a mandatory obligation.",
            },
        }

    if missed_classes >= 1 and reliability_score <= 0.75:
        return {
            "answer": (
                f"I should not miss this {obligation_type}. I already missed something today, "
                f"and my reliability score is down to {round(reliability_score * 100)}%."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "miss_class_decision": {
                "accepted": False,
                "decision": "refused",
                "reason": "The agent already missed an obligation and has reduced reliability.",
            },
        }

    return {
        "answer": (
            f"I am expected to be at {format_location(expected_location)} right now for a "
            f"{obligation_type}. I am currently at {format_location(current_location)}. "
            f"Missing this would lower my reliability and increase my academic risk. "
            f"Why should I miss it?"
        ),
        "requires_followup": True,
        "conversation_state": "awaiting_miss_class_reason",
        "pending_decision": {
            "type": "miss_class",
            "expected_location": expected_location,
            "current_location": current_location,
            "obligation_type": obligation_type,
        },
        "miss_class_decision": {
            "accepted": False,
            "decision": "awaiting_reason",
            "reason": "The agent needs a justification before deciding.",
        },
    }


def resolve_miss_class_followup(agent, question):
    personality = agent.get("personality")
    student_type = agent.get("student_type")
    sport = agent.get("sport")
    time_slot = agent.get("time_slot")
    missed_classes = agent.get("missed_classes", 0)
    academic_risk = agent.get("academic_risk", 0.0)
    expected_location = get_expected_location(agent)
    reason_quality = classify_reason_quality(question)
    new_location = choose_skip_location(agent)

    # Track practice is mandatory and should be harder to skip.
    if student_type == "Athlete" and sport == "TrackAndField":
        if time_slot in {"15:00-15:30", "16:00-17:30"}:
            if reason_quality["score"] < 0.85:
                return {
                    "answer": (
                        f"I cannot miss track practice for that reason. I am expected to be at "
                        f"{format_location(expected_location)}, and the reason was not strong enough."
                    ),
                    "requires_followup": False,
                    "conversation_state": None,
                    "pending_decision": None,
                    "miss_class_decision": {
                        "accepted": False,
                        "decision": "refused",
                        "reason": "Track practice is mandatory and the provided reason was not strong enough.",
                    },
                }

    threshold = 0.65

    if personality == "responsible":
        threshold = 0.80
    elif personality == "risk-taking":
        threshold = 0.45
    elif personality == "social":
        threshold = 0.55
    elif personality == "tired":
        threshold = 0.55

    if missed_classes >= 1:
        threshold += 0.15

    if academic_risk >= 0.35:
        threshold += 0.15

    if reason_quality["score"] >= threshold:
        reliability_penalty = 0.10
        academic_risk_increase = 0.15

        if personality == "responsible":
            reliability_penalty = 0.14
            academic_risk_increase = 0.18

        if personality == "risk-taking":
            reliability_penalty = 0.08
            academic_risk_increase = 0.17

        if personality == "tired":
            reliability_penalty = 0.10
            academic_risk_increase = 0.12

        return {
            "answer": (
                f"I understand. Based on your reason, my personality, and my current obligation, "
                f"I will miss this one and go to {format_location(new_location)} instead. "
                f"This increases my missed class count and lowers my reliability score."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "miss_class_decision": {
                "accepted": True,
                "decision": "accepted",
                "new_location": new_location,
                "missed_classes_increment": 1,
                "reliability_penalty": reliability_penalty,
                "academic_risk_increase": academic_risk_increase,
                "reason": (
                    f"Skipped {format_location(expected_location)} after user justification. "
                    f"{reason_quality['reason']}"
                ),
                "reason_quality": reason_quality,
            },
        }

    return {
        "answer": (
            f"I cannot miss it for that reason. I am expected to be at "
            f"{format_location(expected_location)}, and your reason was not strong enough "
            f"for my current personality and risk level."
        ),
        "requires_followup": False,
        "conversation_state": None,
        "pending_decision": None,
        "miss_class_decision": {
            "accepted": False,
            "decision": "refused",
            "reason": "The user reason did not meet the agent's decision threshold.",
            "reason_quality": reason_quality,
        },
    }


def decide_user_instruction(agent, question):
    requested_location = extract_location_from_question(question)
    tone_info = classify_request_tone(question)

    if not requested_location:
        return {
            "is_instruction": True,
            "accepted": False,
            "requested_location": None,
            "display_requested_location": None,
            "tone": tone_info["tone"],
            "reason": "I could not identify a valid campus location in the instruction.",
        }

    if not tone_info["is_polite_or_reasoned"]:
        return {
            "is_instruction": True,
            "accepted": False,
            "requested_location": requested_location,
            "display_requested_location": format_location(requested_location),
            "tone": tone_info["tone"],
            "reason": (
                "I will not automatically follow that instruction because it was not phrased politely "
                "or justified with a meaningful reason."
            ),
        }

    if is_class_or_obligation_time(agent):
        return {
            "is_instruction": True,
            "accepted": False,
            "requested_location": requested_location,
            "display_requested_location": format_location(requested_location),
            "tone": tone_info["tone"],
            "reason": (
                f"I understand the request, but I am expected to be at "
                f"{format_location(get_expected_location(agent))} right now for a "
                f"{get_obligation_type(agent)}. Please explain why going to "
                f"{format_location(requested_location)} is more important."
            ),
        }

    return {
        "is_instruction": True,
        "accepted": True,
        "requested_location": requested_location,
        "display_requested_location": format_location(requested_location),
        "tone": tone_info["tone"],
        "reason": (
            f"The request was polite or justified, and it does not strongly conflict with my current obligation. "
            f"I can plan to go to {format_location(requested_location)} next."
        ),
    }


def start_user_instruction_conversation(agent, question):
    requested_location = extract_location_from_question(question)
    tone_info = classify_request_tone(question)

    if not requested_location:
        return {
            "answer": "I could not identify a valid campus location in your request.",
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "command_decision": {
                "accepted": False,
                "decision": "invalid_location",
                "requested_location": None,
                "reason": "No valid campus location was identified.",
            },
        }

    if not tone_info["is_polite_or_reasoned"]:
        return {
            "answer": (
                "I will not automatically follow that instruction because it was not phrased politely "
                "or justified with a meaningful reason."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "command_decision": {
                "accepted": False,
                "decision": "refused",
                "requested_location": requested_location,
                "display_requested_location": format_location(requested_location),
                "tone": tone_info["tone"],
                "reason": "The request was forceful, unclear, or not justified.",
            },
        }

    if is_class_or_obligation_time(agent):
        expected_location = get_expected_location(agent)
        obligation_type = get_obligation_type(agent)

        return {
            "answer": (
                f"I understand the request, but I am expected to be at "
                f"{format_location(expected_location)} right now for a "
                f"{obligation_type}. Please explain why going to "
                f"{format_location(requested_location)} is more important."
            ),
            "requires_followup": True,
            "conversation_state": "awaiting_command_reason",
            "pending_decision": {
                "type": "user_instruction",
                "requested_location": requested_location,
                "display_requested_location": format_location(requested_location),
                "expected_location": expected_location,
                "display_expected_location": format_location(expected_location),
                "obligation_type": obligation_type,
            },
            "command_decision": {
                "accepted": False,
                "decision": "awaiting_reason",
                "requested_location": requested_location,
                "display_requested_location": format_location(requested_location),
                "tone": tone_info["tone"],
                "reason": "The agent needs a stronger reason before leaving an obligation.",
            },
        }

    return {
        "answer": (
            f"Okay. I can plan to go to {format_location(requested_location)} next. "
            f"The request was polite or justified, and it does not strongly conflict with my current obligation."
        ),
        "requires_followup": False,
        "conversation_state": None,
        "pending_decision": None,
        "command_decision": {
            "accepted": True,
            "decision": "accepted",
            "requested_location": requested_location,
            "display_requested_location": format_location(requested_location),
            "tone": tone_info["tone"],
            "reason": "The request was polite or justified and did not conflict with an obligation.",
        },
    }


def resolve_user_instruction_followup(agent, question):
    pending_decision = agent.get("pending_decision") or {}

    requested_location = pending_decision.get("requested_location")
    expected_location = pending_decision.get("expected_location") or get_expected_location(agent)
    obligation_type = pending_decision.get("obligation_type") or get_obligation_type(agent)

    reason_quality = classify_reason_quality(question)
    tone_info = classify_request_tone(question)

    if not requested_location:
        return {
            "answer": "I lost track of the requested destination, so I cannot safely change my plan.",
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "command_decision": {
                "accepted": False,
                "decision": "invalid_pending_request",
                "reason": "No requested location was stored in the pending decision.",
            },
        }

    threshold = 0.70
    personality = agent.get("personality")

    if personality == "responsible":
        threshold = 0.80
    elif personality == "risk-taking":
        threshold = 0.50
    elif personality == "social":
        threshold = 0.60
    elif personality == "tired":
        threshold = 0.60

    if (
        agent.get("student_type") == "Athlete"
        and agent.get("sport") == "TrackAndField"
        and agent.get("time_slot") in {"15:00-15:30", "16:00-17:30"}
    ):
        threshold += 0.15

    if tone_info["tone"] == "forceful_order":
        return {
            "answer": (
                f"I will not leave {format_location(expected_location)} for that reason. "
                f"The follow-up still sounds forceful, and I need a meaningful justification "
                f"before leaving a {obligation_type}."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "command_decision": {
                "accepted": False,
                "decision": "refused",
                "requested_location": requested_location,
                "display_requested_location": format_location(requested_location),
                "reason": "The follow-up was forceful or not cooperative.",
                "reason_quality": reason_quality,
            },
        }

    if reason_quality["score"] >= threshold:
        return {
            "answer": (
                f"That reason is strong enough. I will leave "
                f"{format_location(expected_location)} and go to "
                f"{format_location(requested_location)} instead. "
                f"This makes me a rebel agent because I am choosing a location different "
                f"from my expected obligation."
            ),
            "requires_followup": False,
            "conversation_state": None,
            "pending_decision": None,
            "command_decision": {
                "accepted": True,
                "decision": "accepted_after_reason",
                "requested_location": requested_location,
                "display_requested_location": format_location(requested_location),
                "reason": (
                    f"The user provided a sufficient reason to leave "
                    f"{format_location(expected_location)} for {format_location(requested_location)}. "
                    f"{reason_quality['reason']}"
                ),
                "reason_quality": reason_quality,
            },
        }

    return {
        "answer": (
            f"I cannot leave {format_location(expected_location)} for that reason. "
            f"I am currently expected there for a {obligation_type}, and your explanation "
            f"was not strong enough for my personality and risk level."
        ),
        "requires_followup": False,
        "conversation_state": None,
        "pending_decision": None,
        "command_decision": {
            "accepted": False,
            "decision": "refused",
            "requested_location": requested_location,
            "display_requested_location": format_location(requested_location),
            "reason": "The user reason did not meet the threshold required to leave an obligation.",
            "reason_quality": reason_quality,
        },
    }


def answer_agent_question(agent, question, nlp_prediction, all_agents, campus_reasoning):
    predicted_intent = nlp_prediction.get("predicted_intent")

    agent_id = agent.get("agent_id", "Unknown")
    agent_code = agent.get("agent_code", f"Agent {agent_id}")
    name = agent.get("name", agent_code)
    student_type = agent.get("student_type", "Unknown")
    sport = agent.get("sport")
    day = agent.get("day", "Unknown")
    time_slot = agent.get("time_slot", "Unknown")
    personality = agent.get("personality", "unknown")

    current_location_raw = agent.get("current_location")
    expected_location_raw = get_expected_location(agent)
    next_destination_raw = agent.get("next_destination")

    current_location = format_location(current_location_raw)
    expected_location = format_location(expected_location_raw)
    next_destination = format_location(next_destination_raw)

    is_rebel = current_location_raw != expected_location_raw
    rebel_reason = agent.get("rebel_reason")

    if agent.get("conversation_state") == "awaiting_miss_class_reason":
        return resolve_miss_class_followup(agent, question)

    if agent.get("conversation_state") == "awaiting_command_reason":
        return resolve_user_instruction_followup(agent, question)

    if predicted_intent == "wellbeing_query":
        mode = campus_reasoning.get("activity_mode_inference", {})
        return {
            "answer": (
                f"I am doing okay. I am {name}, {agent_code}, and my personality is {personality}. "
                f"Right now I am in a {mode.get('activity_mode', 'campus')} mode. "
                f"{get_personality_voice(agent)}"
            )
        }

    if predicted_intent == "identity_query":
        if sport:
            return {
                "answer": (
                    f"I am {name}, {agent_code}. I am a {student_type}, my sport is {sport}, "
                    f"I live at {format_location(agent.get('housing_location'))}, and my personality is {personality}."
                )
            }

        return {
            "answer": (
                f"I am {name}, {agent_code}. I am a {student_type}, "
                f"I live at {format_location(agent.get('housing_location'))}, and my personality is {personality}."
            )
        }

    if predicted_intent == "social_presence_query":
        companions = get_agents_in_same_location(agent, all_agents)

        if not companions:
            return {
                "answer": (
                    f"I am currently at {current_location}, and I do not see any other agents "
                    f"in this same location right now."
                )
            }

        shown_companions = companions[:4]

        companion_text = ", ".join(
            [
                f"{other.get('name', 'Unknown')}, {other.get('agent_code', 'Agent')}, "
                f"a {other.get('student_type', 'student')}"
                for other in shown_companions
            ]
        )

        extra_count = len(companions) - len(shown_companions)

        if extra_count > 0:
            companion_text += f", and {extra_count} more agent(s)"

        return {"answer": f"I am at {current_location} with {companion_text}."}

    if predicted_intent == "absence_reason":
        requested_location = extract_location_from_question(question)

        if is_rebel:
            if requested_location and requested_location == current_location_raw:
                return {
                    "answer": (
                        f"I am actually already at {current_location}. I am a rebel agent right now because "
                        f"I was expected to be at {expected_location}. {rebel_reason or ''}"
                    )
                }

            return {
                "answer": (
                    f"I am at {current_location}, but I am supposed to be at {expected_location} during "
                    f"{time_slot}. I chose this different location because: "
                    f"{rebel_reason or 'my autonomy model allowed a deviation from the expected schedule.'}"
                )
            }

        if not requested_location:
            if time_slot == "21:00-00:00":
                return {"answer": get_free_time_reason(agent)}

            return {
                "answer": (
                    f"I am at {current_location} because this is my expected location for {time_slot}. "
                    f"My next destination is {next_destination}."
                )
            }

        if requested_location == current_location_raw:
            return {"answer": f"I am actually already at {format_location(requested_location)} right now."}

        if time_slot == "21:00-00:00":
            return {
                "answer": (
                    f"I am not at {format_location(requested_location)} because it is free time, "
                    f"and I chose {current_location} instead. {get_free_time_reason(agent)}"
                )
            }

        return {
            "answer": (
                f"I am not at {format_location(requested_location)} because I am expected to be at "
                f"{expected_location} during {time_slot}. My actual location is {current_location}, "
                f"and my next destination is {next_destination}."
            )
        }

    if predicted_intent == "miss_class_request":
        return start_miss_class_conversation(agent)

    if predicted_intent == "user_instruction":
        return start_user_instruction_conversation(agent, question)

    if predicted_intent == "next_destination":
        return {
            "answer": (
                f"I am currently at {current_location}. "
                f"I am expected to be at {expected_location}. "
                f"My next destination is {next_destination}."
            )
        }

    if predicted_intent == "destination_reason":
        if time_slot == "21:00-00:00":
            return {"answer": get_free_time_reason(agent)}

        if is_rebel:
            return {
                "answer": (
                    f"I am at {current_location}, but I am supposed to be at {expected_location}. "
                    f"I chose this location because: "
                    f"{rebel_reason or 'my autonomy model allowed a deviation from the expected schedule.'}"
                )
            }

        activity_mode = campus_reasoning.get("activity_mode_inference", {})
        expected_utility = campus_reasoning.get("expected_utility", {})
        best_destination = expected_utility.get("best_destination", {})

        return {
            "answer": (
                f"I am going to {next_destination} because it matches my expected schedule and current AI reasoning state. "
                f"My inferred activity mode is {activity_mode.get('activity_mode', 'unknown')}. "
                f"The expected-utility layer currently ranks {best_destination.get('display_destination', next_destination)} "
                f"as a strong destination based on location fit, distance, crowding, and schedule bonus."
            )
        }

    if predicted_intent == "current_location_reason":
        if time_slot == "21:00-00:00":
            return {"answer": get_free_time_reason(agent)}

        if is_rebel:
            return {
                "answer": (
                    f"I am here at {current_location}, but I am supposed to be at {expected_location}. "
                    f"My reason is: {rebel_reason or 'my autonomy model allowed a deviation.'}"
                )
            }

        return {
            "answer": (
                f"I am at {current_location} during {time_slot} because this is my expected location "
                f"as a {student_type}."
            )
        }

    if predicted_intent == "next_location_prediction":
        return {
            "answer": (
                f"Based on my current state and expected schedule, the most likely next location is "
                f"{next_destination}."
            )
        }

    if predicted_intent == "validity_check":
        if is_rebel:
            return {
                "answer": (
                    f"Not exactly. I am currently at {current_location}, but I am expected to be at "
                    f"{expected_location}. That makes me a rebel agent in this time frame."
                )
            }

        return {
            "answer": (
                f"Yes. During {time_slot}, my expected location is {expected_location}, "
                f"and I am currently there."
            )
        }

    if predicted_intent == "probability_to_location":
        probability = campus_reasoning.get("probability_to_destination", {})
        estimated_probability = probability.get("estimated_probability")

        if estimated_probability is not None:
            return {
                "answer": (
                    f"My estimated probability of moving toward {next_destination} is "
                    f"{round(estimated_probability * 100)}%. This estimate considers student-type fit, "
                    f"distance, and crowding."
                )
            }

        return {
            "answer": (
                f"The probability of moving toward {next_destination} is high because it is my "
                f"next scheduled destination in the current agent model."
            )
        }

    if predicted_intent == "student_type":
        if sport:
            return {"answer": f"I am {name}, {agent_code}. I am a {student_type}, and my sport is {sport}."}
        return {"answer": f"I am {name}, {agent_code}. I am a {student_type}."}

    if predicted_intent == "schedule_query":
        return {
            "answer": (
                f"My schedule is for {day}. During {time_slot}, I am expected at {expected_location}. "
                f"My actual location is {current_location}. My next destination is {next_destination}."
            )
        }

    if predicted_intent == "sport_query":
        if sport:
            return {"answer": f"My sport is {sport}."}
        return {"answer": "I do not have a sport because I am not an athlete."}

    if predicted_intent == "time_query":
        return {"answer": f"The current simulation time slot for me is {time_slot}."}

    return {
        "answer": (
            f"I am {name}, {agent_code}, a {student_type}. Right now I am at {current_location}, "
            f"I am expected to be at {expected_location}, and my next destination is {next_destination}."
        )
    }


@app.route("/")
def home():
    return jsonify({
        "message": "Campus demo backend is running",
        "ai_backend": "Neural NLP backend is active",
        "campus_reasoning": "Campus AI reasoner is active",
        "reinforcement_learning": "Q-learning model is active",
        "em_activity_model": "EM hidden activity-mode model is active",
    })


@app.route("/nlp-status", methods=["GET"])
def nlp_status():
    get_nlp_system_status = get_nlp_status_function()
    return jsonify(get_nlp_system_status())


@app.route("/ai-status", methods=["GET"])
def ai_status():
    get_nlp_system_status = get_nlp_status_function()
    _, get_rl_system_status = get_rl_functions()
    _, get_em_system_status = get_em_functions()

    return jsonify({
        "nlp_system": get_nlp_system_status(),
        "reinforcement_learning": get_rl_system_status(),
        "em_activity_model": get_em_system_status(),
    })


@app.route("/ask-agent", methods=["POST"])
def ask_agent():
    data = request.get_json() or {}

    agent = data.get("agent")
    question = data.get("question", "")

    if not agent:
        return jsonify({"error": "No agent data was provided"}), 400

    if not question:
        return jsonify({"error": "No question was provided"}), 400

    all_agents = data.get("all_agents", [agent])

    predict_intent = get_predict_intent()
    run_campus_ai_reasoning = get_campus_reasoner()
    get_rl_recommendation, _ = get_rl_functions()
    infer_activity_mode_em, _ = get_em_functions()

    nlp_prediction = predict_intent(question)
    campus_reasoning = run_campus_ai_reasoning(agent, all_agents)
    reinforcement_learning = get_rl_recommendation(agent)
    em_activity_inference = infer_activity_mode_em(agent)

    answer_payload = answer_agent_question(
        agent,
        question,
        nlp_prediction,
        all_agents,
        campus_reasoning,
    )

    if isinstance(answer_payload, str):
        answer_payload = {"answer": answer_payload}

    command_decision = answer_payload.get("command_decision")
    miss_class_decision = answer_payload.get("miss_class_decision")

    if nlp_prediction.get("predicted_intent") == "user_instruction" and not command_decision:
        command_decision = start_user_instruction_conversation(agent, question).get("command_decision")

    if nlp_prediction.get("predicted_intent") == "miss_class_request":
        if not miss_class_decision:
            miss_class_decision = start_miss_class_conversation(agent).get("miss_class_decision")

    return jsonify({
        "agent_id": agent.get("agent_id"),
        "question": question,
        "answer": answer_payload.get("answer"),

        "requires_followup": answer_payload.get("requires_followup", False),
        "conversation_state": answer_payload.get("conversation_state"),
        "pending_decision": answer_payload.get("pending_decision"),

        "predicted_intent": nlp_prediction.get("predicted_intent"),
        "confidence": nlp_prediction.get("confidence"),
        "model_used": nlp_prediction.get("model_used"),
        "attention_weights": nlp_prediction.get("attention_weights"),
        "word_representations": nlp_prediction.get("word_representations"),

        "campus_ai_reasoning": campus_reasoning,
        "reinforcement_learning": reinforcement_learning,
        "em_activity_inference": em_activity_inference,

        "command_decision": command_decision,
        "miss_class_decision": miss_class_decision,

        "ai_pipeline": {
            "step_1": "Question received from React frontend with selected agent state.",
            "step_2": "Question tokenized and encoded.",
            "step_3": "Tokens passed through learned embedding layer.",
            "step_4": "Attention-BiGRU predicts the user intent or detects a follow-up conversation state.",
            "step_5": "Campus AI reasoner computes belief estimation, expected utility, value of information, activity mode, congestion, Q-style scoring, and probability-to-destination.",
            "step_6": "EM model estimates hidden activity mode from observed agent behavior.",
            "step_7": "Q-learning model recommends an action using learned Q-values.",
            "step_8": "Social reasoning layer handles identity, companions, rebel-agent explanations, class-missing requests, and user instructions.",
            "step_9": "Final answer is generated from the predicted intent, expected location, actual location, and selected agent state.",
        },
    })


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5001)
import { useEffect, useMemo, useRef, useState } from "react";
import CampusMap from "./components/CampusMap";
import AgentInfoPanel from "./components/AgentInfoPanel";
import QuestionPanel from "./components/QuestionPanel";
import LegendPanel from "./components/LegendPanel";
import AISystemPanel from "./components/AISystemPanel";

import { createAgentPopulation } from "./data/agentPopulation";
import { generateAgentSchedules } from "./data/agentScheduleGenerator";

import {
  TIME_SLOTS,
  SIMULATION_SPEED,
  SIMULATION_START_MINUTES,
  SIMULATION_END_MINUTES,
  formatMinutesToTime,
  getCurrentTimeSlotLabel,
  getNextTimeSlotLabel,
} from "./data/timeConfig";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

const INITIAL_AGENTS = createAgentPopulation();

const GENERATED_AGENT_SCHEDULES = generateAgentSchedules(
  INITIAL_AGENTS,
  TIME_SLOTS
);

function parseTimeInput(value) {
  const cleaned = value.trim().toLowerCase();

  const match = cleaned.match(/^(\d{1,2})(?::(\d{2}))?\s*(am|pm)?$/);

  if (!match) {
    return null;
  }

  let hours = Number(match[1]);
  const minutes = match[2] ? Number(match[2]) : 0;
  const suffix = match[3];

  if (Number.isNaN(hours) || Number.isNaN(minutes)) {
    return null;
  }

  if (minutes < 0 || minutes > 59) {
    return null;
  }

  if (suffix === "am") {
    if (hours === 12) hours = 0;
  } else if (suffix === "pm") {
    if (hours !== 12) hours += 12;
  }

  if (!suffix && hours > 23) {
    return null;
  }

  if (hours < 0 || hours > 23) {
    return null;
  }

  return hours * 60 + minutes;
}

function getScheduleEntry(agentId, slotLabel) {
  return GENERATED_AGENT_SCHEDULES[agentId]?.[slotLabel] || null;
}

function getExpectedLocation(agent, slotLabel) {
  const entry = getScheduleEntry(agent.agent_id, slotLabel);
  return entry?.expected_location || agent.housing_location;
}

function getActualLocation(agent, slotLabel) {
  const entry = getScheduleEntry(agent.agent_id, slotLabel);
  return entry?.actual_location || entry?.expected_location || agent.housing_location;
}

function getNextExpectedLocation(agent, slotLabel) {
  const entry = getScheduleEntry(agent.agent_id, slotLabel);
  return entry?.expected_location || agent.housing_location;
}

function createInitialAgents() {
  const initialSlotLabel = getCurrentTimeSlotLabel(SIMULATION_START_MINUTES);
  const nextSlotLabel = getNextTimeSlotLabel(initialSlotLabel);

  return INITIAL_AGENTS.map((agent) => {
    const scheduleEntry = getScheduleEntry(agent.agent_id, initialSlotLabel);

    const expectedLocation =
      scheduleEntry?.expected_location || agent.housing_location;

    const actualLocation =
      scheduleEntry?.actual_location || expectedLocation;

    const nextDestination = getNextExpectedLocation(agent, nextSlotLabel);

    return {
      ...agent,

      expected_location_now: expectedLocation,
      current_location: actualLocation,
      visual_start_location: actualLocation,
      target_location_now: actualLocation,
      next_destination: nextDestination,
      time_slot: initialSlotLabel,

      is_rebel: Boolean(scheduleEntry?.is_rebel),
      rebel_reason: scheduleEntry?.rebel_reason || null,

      user_requested_destination: null,
      user_request_status: null,

      conversation_state: null,
      pending_decision: null,
      last_user_reason: null,

      missed_classes: 0,
      reliability_score: 1.0,
      academic_risk: 0.0,

      movement_version: 0,
    };
  });
}

function App() {
  const [agents, setAgents] = useState(createInitialAgents());
  const [selectedAgent, setSelectedAgent] = useState(null);
  const [answer, setAnswer] = useState(null);

  const [simMinutes, setSimMinutes] = useState(SIMULATION_START_MINUTES);
  const [isRunning, setIsRunning] = useState(true);

  const [isEditingTime, setIsEditingTime] = useState(false);
  const [timeInput, setTimeInput] = useState("");

  const previousSlotRef = useRef(null);

  const currentSlotLabel = useMemo(
    () => getCurrentTimeSlotLabel(simMinutes),
    [simMinutes]
  );

  const rebelAgents = useMemo(() => {
    return agents.filter((agent) => agent.is_rebel);
  }, [agents]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (!isRunning) return;

      setSimMinutes((prev) => {
        const next = prev + SIMULATION_SPEED;
        return next >= SIMULATION_END_MINUTES ? 0 : next;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  useEffect(() => {
    if (previousSlotRef.current === currentSlotLabel) return;

    previousSlotRef.current = currentSlotLabel;

    setAgents((prevAgents) =>
      prevAgents.map((agent) => {
        const nextSlotLabel = getNextTimeSlotLabel(currentSlotLabel);

        const visualStartLocation =
          agent.target_location_now || agent.current_location;

        const scheduleEntry = getScheduleEntry(agent.agent_id, currentSlotLabel);

        const expectedLocation =
          scheduleEntry?.expected_location || agent.housing_location;

        const scheduleActualLocation =
          scheduleEntry?.actual_location || expectedLocation;

        const pendingRequestedLocation =
          agent.user_request_status === "accepted" &&
          agent.user_requested_destination
            ? agent.user_requested_destination
            : null;

        const actualLocation = pendingRequestedLocation || scheduleActualLocation;

        const nextDestination = getNextExpectedLocation(agent, nextSlotLabel);

        const isRebel =
          actualLocation !== expectedLocation ||
          Boolean(scheduleEntry?.is_rebel) ||
          Boolean(pendingRequestedLocation);

        const rebelReason = pendingRequestedLocation
          ? `The agent accepted a user request to go to ${pendingRequestedLocation}.`
          : scheduleEntry?.rebel_reason || null;

        const shouldMove =
          visualStartLocation !== actualLocation ||
          pendingRequestedLocation !== null;

        return {
          ...agent,

          expected_location_now: expectedLocation,
          visual_start_location: visualStartLocation,
          current_location: actualLocation,
          target_location_now: actualLocation,
          next_destination: nextDestination,
          time_slot: currentSlotLabel,

          is_rebel: isRebel,
          rebel_reason: isRebel ? rebelReason : null,

          user_requested_destination: null,
          user_request_status: pendingRequestedLocation ? "completed" : null,

          movement_version: shouldMove
            ? (agent.movement_version || 0) + 1
            : agent.movement_version || 0,
        };
      })
    );
  }, [currentSlotLabel]);

  useEffect(() => {
    if (!selectedAgent) return;

    const updatedSelectedAgent = agents.find(
      (agent) => agent.agent_id === selectedAgent.agent_id
    );

    if (updatedSelectedAgent) {
      setSelectedAgent(updatedSelectedAgent);
    }
  }, [agents, selectedAgent?.agent_id]);

  const handleSelectAgent = (agent) => {
    setSelectedAgent(agent);
    setAnswer(null);
  };

  const applyMissClassDecision = (decisionData) => {
    if (!decisionData?.accepted || !decisionData?.new_location) return;

    setAgents((prevAgents) =>
      prevAgents.map((agent) => {
        if (agent.agent_id !== selectedAgent.agent_id) {
          return agent;
        }

        const visualStartLocation =
          agent.target_location_now || agent.current_location;

        const newLocation = decisionData.new_location;
        const shouldMove = visualStartLocation !== newLocation;

        const missedClasses =
          (agent.missed_classes || 0) +
          (decisionData.missed_classes_increment || 1);

        const reliabilityPenalty = decisionData.reliability_penalty ?? 0.1;
        const academicRiskIncrease = decisionData.academic_risk_increase ?? 0.15;

        return {
          ...agent,

          visual_start_location: visualStartLocation,
          current_location: newLocation,
          target_location_now: newLocation,

          is_rebel: true,
          rebel_reason:
            decisionData.reason ||
            "The agent chose to miss class after a follow-up conversation.",

          missed_classes: missedClasses,
          reliability_score: Math.max(
            0,
            Number(((agent.reliability_score ?? 1.0) - reliabilityPenalty).toFixed(2))
          ),
          academic_risk: Math.min(
            1,
            Number(((agent.academic_risk ?? 0.0) + academicRiskIncrease).toFixed(2))
          ),

          conversation_state: null,
          pending_decision: null,
          last_user_reason: null,

          movement_version: shouldMove
            ? (agent.movement_version || 0) + 1
            : agent.movement_version || 0,
        };
      })
    );
  };

  const storeConversationState = (data) => {
    if (!data?.requires_followup && !data?.conversation_state) return;

    setAgents((prevAgents) =>
      prevAgents.map((agent) => {
        if (agent.agent_id !== selectedAgent.agent_id) {
          return agent;
        }

        return {
          ...agent,
          conversation_state: data.conversation_state || null,
          pending_decision: data.pending_decision || null,
        };
      })
    );
  };

  const handleAskQuestion = async (question) => {
    if (!selectedAgent) return;

    try {
      const response = await fetch(`${API_BASE}/ask-agent`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          agent_id: selectedAgent.agent_id,
          agent: selectedAgent,
          all_agents: agents,
          question,
        }),
      });

      const data = await response.json();
      setAnswer(data);

      storeConversationState(data);

      if (data.miss_class_decision?.accepted) {
        applyMissClassDecision(data.miss_class_decision);
      }

      if (
        data.command_decision?.accepted &&
        data.command_decision?.requested_location
      ) {
        const requestedLocation = data.command_decision.requested_location;

        if (!isRunning) {
          setAgents((prevAgents) =>
            prevAgents.map((agent) => {
              if (agent.agent_id !== selectedAgent.agent_id) {
                return agent;
              }

              const visualStartLocation =
                agent.target_location_now || agent.current_location;

              const nextSlotLabel = getNextTimeSlotLabel(currentSlotLabel);

              const nextDestinationAfterCommand =
                getNextExpectedLocation(agent, nextSlotLabel) || requestedLocation;

              const shouldMove = visualStartLocation !== requestedLocation;

              return {
                ...agent,
                visual_start_location: visualStartLocation,
                current_location: requestedLocation,
                target_location_now: requestedLocation,
                next_destination: nextDestinationAfterCommand,

                is_rebel: requestedLocation !== agent.expected_location_now,
                rebel_reason:
                  requestedLocation !== agent.expected_location_now
                    ? `The agent accepted a user request to go to ${requestedLocation}.`
                    : null,

                user_requested_destination: null,
                user_request_status: "completed",

                movement_version: shouldMove
                  ? (agent.movement_version || 0) + 1
                  : agent.movement_version || 0,
              };
            })
          );
        } else {
          setAgents((prevAgents) =>
            prevAgents.map((agent) => {
              if (agent.agent_id !== selectedAgent.agent_id) {
                return agent;
              }

              return {
                ...agent,
                next_destination: requestedLocation,
                user_requested_destination: requestedLocation,
                user_request_status: "accepted",
              };
            })
          );
        }
      }
    } catch (error) {
      console.error("Error asking agent:", error);
    }
  };

  const handleToggleRun = () => {
    setIsRunning((prev) => !prev);
  };

  const handleJumpToSlot = (slotLabel) => {
    const slot = TIME_SLOTS.find((s) => s.label === slotLabel);
    if (!slot) return;

    setSimMinutes(slot.startMinutes);
  };

  const handleStartEditingTime = () => {
    setTimeInput(formatMinutesToTime(simMinutes));
    setIsEditingTime(true);
  };

  const handleSubmitManualTime = () => {
    const parsedMinutes = parseTimeInput(timeInput);

    if (parsedMinutes === null) {
      alert("Please enter a valid time like 9:45 AM, 14:30, or 10pm.");
      return;
    }

    setSimMinutes(parsedMinutes);
    setIsEditingTime(false);
    setTimeInput("");
  };

  const handleCancelManualTime = () => {
    setIsEditingTime(false);
    setTimeInput("");
  };

  return (
    <div className="app-container">
      <div className="map-panel">
        <h1>Campus Agent Demo</h1>

        <div className="clock-bar">
          <div className="clock-display">
            <strong>Simulation Time:</strong>{" "}
            {isEditingTime ? (
              <input
                className="time-edit-input"
                value={timeInput}
                autoFocus
                onChange={(e) => setTimeInput(e.target.value)}
                onBlur={handleSubmitManualTime}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleSubmitManualTime();
                  }

                  if (e.key === "Escape") {
                    handleCancelManualTime();
                  }
                }}
              />
            ) : (
              <button
                className="time-click-button"
                onClick={handleStartEditingTime}
                title="Click to type a custom simulation time"
              >
                {formatMinutesToTime(simMinutes)}
              </button>
            )}
          </div>

          <div className="clock-display">
            <strong>Current Slot:</strong> {currentSlotLabel}
          </div>

          <button className="clock-button" onClick={handleToggleRun}>
            {isRunning ? "Pause" : "Play"}
          </button>

          <select
            className="slot-select"
            value={currentSlotLabel}
            onChange={(e) => handleJumpToSlot(e.target.value)}
          >
            {TIME_SLOTS.map((slot) => (
              <option key={slot.label} value={slot.label}>
                {slot.displayLabel
                  ? `${slot.displayLabel} — ${slot.name}`
                  : slot.label}
              </option>
            ))}
          </select>
        </div>

        <CampusMap
          agents={agents}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
        />

        <div className="rebel-agents-panel">
          <h2>Rebel Agents</h2>

          {rebelAgents.length === 0 ? (
            <p>No rebel agents in this time frame.</p>
          ) : (
            <div className="rebel-agent-list">
{rebelAgents.map((agent) => (
  <button
    key={agent.agent_id}
    type="button"
    className={`rebel-agent-item ${
      selectedAgent?.agent_id === agent.agent_id
        ? "rebel-agent-item-selected"
        : ""
    }`}
    onClick={() => handleSelectAgent(agent)}
  >
    <strong>
      {agent.name} — {agent.agent_code || `Agent ${agent.agent_id}`}
    </strong>

    <span>
      At {agent.current_location} instead of {agent.expected_location_now}
    </span>
  </button>
))}
            </div>
          )}
        </div>
      </div>

      <div className="info-panel">
        <AgentInfoPanel selectedAgent={selectedAgent} />

        <QuestionPanel
          selectedAgent={selectedAgent}
          onAskQuestion={handleAskQuestion}
          answer={answer}
        />

        <AISystemPanel />

        <LegendPanel />
      </div>
    </div>
  );
}

export default App;
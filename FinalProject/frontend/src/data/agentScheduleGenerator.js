const CLASS_LOCATIONS = ["AcademicHall", "WestPenn"];

const STUDY_LOCATIONS = ["Library"];

const DORM_LOCATIONS = [
  "BoulevardAppartments",
  "ConestogaHall",
  "LawrenceHall",
];

const COPA_OBLIGATION_LOCATIONS = ["PlayHouse", "GeorgeRowlandWhite"];

const COPA_SUPPORT_LOCATIONS = [
  "PlayHouse",
  "GeorgeRowlandWhite",
  "StudentCenter",
];

const ATHLETE_SUPPORT_LOCATIONS = [
  "StudentCenter",
  "WestPenn",
  "Library",
];

const FREE_TIME_LOCATIONS = [
  "VillagePark",
  "StudentCenter",
  "BoulevardAppartments",
];

const SOCIAL_LOCATIONS = [
  "VillagePark",
  "StudentCenter",
  "BoulevardAppartments",
];

const LOW_EFFORT_LOCATIONS = [
  "StudentCenter",
  "Library",
];

const REGULAR_TRACK_ALLOWED_SLOTS = [
  "08:00-09:30",
  "09:40-11:10",
  "11:20-12:50",
  "13:00-14:30",
];

const TRACK_PRACTICE_SLOTS = ["15:00-15:30", "16:00-17:30"];

function deterministicIndex(agentId, slotLabel, modulo) {
  const text = `${agentId}-${slotLabel}`;
  let hash = 0;

  for (let i = 0; i < text.length; i++) {
    hash = (hash * 31 + text.charCodeAt(i)) % 100000;
  }

  return hash % modulo;
}

function chooseFromList(list, agentId, slotLabel) {
  const index = deterministicIndex(agentId, slotLabel, list.length);
  return list[index];
}

function assignEveningClassAgents(agents) {
  /*
    15% of 50 students = 7.5, rounded to 8.
    These students take 6 PM - 9 PM classes at West Penn or Academic Hall.
  */

  const eveningClassCount = Math.round(agents.length * 0.15);

  return new Set(
    agents
      .slice()
      .sort((a, b) => a.agent_id - b.agent_id)
      .slice(0, eveningClassCount)
      .map((agent) => agent.agent_id)
  );
}

function getExpectedLocation(agent, slotLabel, eveningClassAgentIds) {
  const home = agent.housing_location;

  if (slotLabel === "00:00-08:00") {
    return home;
  }

  if (slotLabel === "08:00-09:30") {
    if (agent.student_type === "Athlete") {
      if (agent.sport === "TrackAndField") {
        return "StudentCenter";
      }

      return chooseFromList(
        [...CLASS_LOCATIONS, ...ATHLETE_SUPPORT_LOCATIONS],
        agent.agent_id,
        slotLabel
      );
    }

    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_OBLIGATION_LOCATIONS, "StudentCenter"],
        agent.agent_id,
        slotLabel
      );
    }

    if (deterministicIndex(agent.agent_id, slotLabel, 100) < 18) {
      return "Track";
    }

    return chooseFromList(
      [...CLASS_LOCATIONS, ...STUDY_LOCATIONS, "StudentCenter"],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "09:40-11:10") {
    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_OBLIGATION_LOCATIONS, ...CLASS_LOCATIONS],
        agent.agent_id,
        slotLabel
      );
    }

    if (
      agent.student_type === "Regular Student" &&
      REGULAR_TRACK_ALLOWED_SLOTS.includes(slotLabel) &&
      deterministicIndex(agent.agent_id, slotLabel, 100) < 12
    ) {
      return "Track";
    }

    return chooseFromList(
      [...CLASS_LOCATIONS, ...STUDY_LOCATIONS],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "11:20-12:50") {
    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_OBLIGATION_LOCATIONS, ...CLASS_LOCATIONS, "StudentCenter"],
        agent.agent_id,
        slotLabel
      );
    }

    if (
      agent.student_type === "Regular Student" &&
      deterministicIndex(agent.agent_id, slotLabel, 100) < 10
    ) {
      return "Track";
    }

    return chooseFromList(
      [...CLASS_LOCATIONS, ...STUDY_LOCATIONS, "StudentCenter"],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "13:00-14:30") {
    if (agent.student_type === "Athlete") {
      return chooseFromList(
        ["StudentCenter", "WestPenn", "Library"],
        agent.agent_id,
        slotLabel
      );
    }

    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_OBLIGATION_LOCATIONS, ...CLASS_LOCATIONS],
        agent.agent_id,
        slotLabel
      );
    }

    if (
      agent.student_type === "Regular Student" &&
      deterministicIndex(agent.agent_id, slotLabel, 100) < 15
    ) {
      return "Track";
    }

    return chooseFromList(
      [...CLASS_LOCATIONS, ...STUDY_LOCATIONS, "StudentCenter"],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "15:00-15:30") {
    if (agent.student_type === "Athlete") {
      if (agent.sport === "TrackAndField") {
        return "Track";
      }

      return "StudentCenter";
    }

    if (agent.student_type === "Copa") {
      return chooseFromList(
        COPA_OBLIGATION_LOCATIONS,
        agent.agent_id,
        slotLabel
      );
    }

    return chooseFromList(
      ["Library", "StudentCenter", "AcademicHall"],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "16:00-17:30") {
    if (agent.student_type === "Athlete") {
      if (agent.sport === "TrackAndField") {
        return "Track";
      }

      return chooseFromList(
        ["StudentCenter", "WestPenn", "OffCampus"],
        agent.agent_id,
        slotLabel
      );
    }

    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_OBLIGATION_LOCATIONS, "StudentCenter"],
        agent.agent_id,
        slotLabel
      );
    }

    return chooseFromList(
      ["Library", "StudentCenter", "AcademicHall", "WestPenn"],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "18:00-21:00") {
    if (eveningClassAgentIds.has(agent.agent_id)) {
      return agent.agent_id % 2 === 0 ? "AcademicHall" : "WestPenn";
    }

    if (agent.student_type === "Athlete" && agent.sport === "TrackAndField") {
      return chooseFromList(
        ["Track", "StudentCenter", "VillagePark"],
        agent.agent_id,
        slotLabel
      );
    }

    if (agent.student_type === "Copa") {
      return chooseFromList(
        [...COPA_SUPPORT_LOCATIONS, "StudentCenter"],
        agent.agent_id,
        slotLabel
      );
    }

    return chooseFromList(
      ["StudentCenter", "Library", "VillagePark", home],
      agent.agent_id,
      slotLabel
    );
  }

  if (slotLabel === "21:00-00:00") {
    return chooseFromList(FREE_TIME_LOCATIONS, agent.agent_id, slotLabel);
  }

  return home;
}

function getRebelChance(agent, slotLabel, expectedLocation) {
  /*
    Target rebel rate:
    Around 10% - 15% per time frame.

    Personality modifiers:
    - responsible: lower
    - social: moderate
    - tired: moderate
    - risk-taking: higher
  */

  if (slotLabel === "00:00-08:00") {
    return 0;
  }

  let chance = 12;

  if (agent.personality === "responsible") chance = 6;
  if (agent.personality === "social") chance = 13;
  if (agent.personality === "tired") chance = 14;
  if (agent.personality === "risk-taking") chance = 18;

  /*
    Track practice is mandatory for TrackAndField from 3:00 PM to 5:30 PM,
    but there is still room for rebellion.
  */
  if (
    agent.student_type === "Athlete" &&
    agent.sport === "TrackAndField" &&
    TRACK_PRACTICE_SLOTS.includes(slotLabel) &&
    expectedLocation === "Track"
  ) {
    chance += 2;
  }

  return chance;
}

function shouldBecomeRebel(agent, slotLabel, expectedLocation) {
  const chance = getRebelChance(agent, slotLabel, expectedLocation);
  const score = deterministicIndex(agent.agent_id, `${slotLabel}-rebel`, 100);

  return score < chance;
}

function chooseRebelLocation(agent, slotLabel, expectedLocation) {
  let options = [];

  if (agent.personality === "responsible") {
    options = ["Library", "StudentCenter"];
  } else if (agent.personality === "social") {
    options = SOCIAL_LOCATIONS;
  } else if (agent.personality === "tired") {
    options = [agent.housing_location, "StudentCenter", "OffCampus"];
  } else if (agent.personality === "risk-taking") {
    options = [
      "VillagePark",
      "StudentCenter",
      "OffCampus",
      "BoulevardAppartments",
    ];
  } else {
    options = LOW_EFFORT_LOCATIONS;
  }

  /*
    Regular students should not rebel into Track after 3 PM.
  */
  if (
    agent.student_type === "Regular Student" &&
    ["15:00-15:30", "16:00-17:30", "18:00-21:00"].includes(slotLabel)
  ) {
    options = options.filter((location) => location !== "Track");
  }

  const filteredOptions = options.filter(
    (location) => location !== expectedLocation
  );

  if (filteredOptions.length === 0) {
    return expectedLocation;
  }

  return chooseFromList(filteredOptions, agent.agent_id, `${slotLabel}-actual`);
}

function buildRebelReason(agent, expectedLocation, actualLocation, slotLabel) {
  if (expectedLocation === actualLocation) {
    return null;
  }

  if (
    agent.student_type === "Athlete" &&
    agent.sport === "TrackAndField" &&
    TRACK_PRACTICE_SLOTS.includes(slotLabel) &&
    expectedLocation === "Track"
  ) {
    return (
      "I was expected to be at Track for mandatory practice, but my autonomy model " +
      "allowed a deviation from practice during this time slot."
    );
  }

  if (agent.personality === "responsible") {
    return (
      "I usually follow my schedule, but I chose a lower-risk alternative location " +
      "instead of the expected scheduled location."
    );
  }

  if (agent.personality === "social") {
    return (
      "I chose a more social location instead of the expected scheduled location."
    );
  }

  if (agent.personality === "tired") {
    return (
      "I chose a lower-effort location because my agent personality is tired."
    );
  }

  if (agent.personality === "risk-taking") {
    return (
      "I chose to deviate because my agent personality is more willing to take risks."
    );
  }

  return "I chose a different location than my expected scheduled location.";
}

function createScheduleEntry(agent, slotLabel, eveningClassAgentIds) {
  const expectedLocation = getExpectedLocation(
    agent,
    slotLabel,
    eveningClassAgentIds
  );

  const isRebel = shouldBecomeRebel(agent, slotLabel, expectedLocation);

  const actualLocation = isRebel
    ? chooseRebelLocation(agent, slotLabel, expectedLocation)
    : expectedLocation;

  return {
    expected_location: expectedLocation,
    actual_location: actualLocation,
    is_rebel: actualLocation !== expectedLocation,
    rebel_reason: buildRebelReason(
      agent,
      expectedLocation,
      actualLocation,
      slotLabel
    ),
  };
}

export function generateAgentSchedules(agents, timeSlots) {
  const eveningClassAgentIds = assignEveningClassAgents(agents);

  const schedules = {};

  agents.forEach((agent) => {
    schedules[agent.agent_id] = {};

    timeSlots.forEach((slot) => {
      schedules[agent.agent_id][slot.label] = createScheduleEntry(
        agent,
        slot.label,
        eveningClassAgentIds
      );
    });
  });

  return schedules;
}

export function getScheduleSummary(agents, schedules, timeSlots) {
  const summary = {};

  timeSlots.forEach((slot) => {
    summary[slot.label] = {};

    agents.forEach((agent) => {
      const entry = schedules[agent.agent_id]?.[slot.label];
      const actualLocation = entry?.actual_location || "Unknown";

      summary[slot.label][actualLocation] =
        (summary[slot.label][actualLocation] || 0) + 1;
    });
  });

  return summary;
}

export function getRebelAgentsForSlot(agents, schedules, slotLabel) {
  return agents
    .map((agent) => {
      const entry = schedules[agent.agent_id]?.[slotLabel];

      return {
        ...agent,
        expected_location_now: entry?.expected_location,
        current_location: entry?.actual_location,
        is_rebel: Boolean(entry?.is_rebel),
        rebel_reason: entry?.rebel_reason || null,
      };
    })
    .filter((agent) => agent.is_rebel);
}
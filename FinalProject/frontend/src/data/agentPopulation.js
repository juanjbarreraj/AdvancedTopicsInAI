const FIRST_NAMES = [
    "Mateo",
    "Sofia",
    "Marcus",
    "Isabella",
    "Diego",
    "Camila",
    "Andre",
    "Valentina",
    "Lucas",
    "Maya",
    "Julian",
    "Elena",
    "Nicolas",
    "Ariana",
    "Gabriel",
    "Luna",
    "Sebastian",
    "Natalia",
    "Ethan",
    "Mia",
    "David",
    "Emma",
    "Leo",
    "Victoria",
    "Daniel",
    "Carolina",
    "Samuel",
    "Lucia",
    "Adrian",
    "Clara",
    "Javier",
    "Bianca",
    "Noah",
    "Olivia",
    "Luis",
    "Ana",
    "Marco",
    "Paula",
    "Thiago",
    "Rosa",
    "Kevin",
    "Sara",
    "Alejandro",
    "Nina",
    "Carlos",
    "Valeria",
    "Brandon",
    "Gabriela",
    "Miguel",
    "Mariana",
  ];
  
  const PERSONALITIES = [
    "responsible",
    "social",
    "tired",
    "risk-taking",
  ];
  
  const ATHLETE_SPORTS = [
    "TrackAndField",
    "Baseball",
    "Soccer",
    "Basketball",
  ];
  
  const DORM_LOCATIONS = [
    "BoulevardAppartments",
    "ConestogaHall",
    "LawrenceHall",
  ];
  
  function formatAgentCode(agentNumber) {
    return `Agent ${String(agentNumber).padStart(3, "0")}`;
  }
  
  function getPersonality(index) {
    return PERSONALITIES[index % PERSONALITIES.length];
  }
  
  function getAthleteSport(index) {
    return ATHLETE_SPORTS[index % ATHLETE_SPORTS.length];
  }
  
  function distributeDormHousing(agentIndexWithinDormGroup) {
    /*
      35 dorm residents split as evenly as possible:
  
      Boulevard Apartments: 12
      Conestoga Hall: 12
      Lawrence Hall: 11
    */
  
    if (agentIndexWithinDormGroup < 12) {
      return "BoulevardAppartments";
    }
  
    if (agentIndexWithinDormGroup < 24) {
      return "ConestogaHall";
    }
  
    return "LawrenceHall";
  }
  
  function createAgent({
    agentNumber,
    name,
    studentType,
    sport = null,
    housingLocation,
    livesOnCampus,
    personality,
  }) {
    return {
      agent_id: agentNumber,
      agent_code: formatAgentCode(agentNumber),
      name,
      student_type: studentType,
      sport,
      housing_location: housingLocation,
      lives_on_campus: livesOnCampus,
      personality,
  
      // These fields will be filled by schedule logic.
      current_location: housingLocation,
      visual_start_location: housingLocation,
      target_location_now: housingLocation,
      next_destination: housingLocation,
  
      day: "Tuesday",
      time_slot: "00:00-08:00",
    };
  }
  
  export function createAgentPopulation() {
    const agents = [];
  
    /*
      Total agents: 50
  
      70% live on campus = 35 agents
        - 40% COPA = 14
        - 40% Regular = 14
        - 20% Athletes = 7
  
      30% live off campus = 15 agents
    */
  
    let agentNumber = 1;
    let dormIndex = 0;
  
    // 14 COPA dorm residents
    for (let i = 0; i < 14; i++) {
      agents.push(
        createAgent({
          agentNumber,
          name: FIRST_NAMES[agentNumber - 1],
          studentType: "Copa",
          sport: null,
          housingLocation: distributeDormHousing(dormIndex),
          livesOnCampus: true,
          personality: getPersonality(agentNumber - 1),
        })
      );
  
      agentNumber += 1;
      dormIndex += 1;
    }
  
    // 14 Regular dorm residents
    for (let i = 0; i < 14; i++) {
      agents.push(
        createAgent({
          agentNumber,
          name: FIRST_NAMES[agentNumber - 1],
          studentType: "Regular Student",
          sport: null,
          housingLocation: distributeDormHousing(dormIndex),
          livesOnCampus: true,
          personality: getPersonality(agentNumber - 1),
        })
      );
  
      agentNumber += 1;
      dormIndex += 1;
    }
  
    // 7 Athlete dorm residents
    for (let i = 0; i < 7; i++) {
      agents.push(
        createAgent({
          agentNumber,
          name: FIRST_NAMES[agentNumber - 1],
          studentType: "Athlete",
          sport: getAthleteSport(i),
          housingLocation: distributeDormHousing(dormIndex),
          livesOnCampus: true,
          personality: getPersonality(agentNumber - 1),
        })
      );
  
      agentNumber += 1;
      dormIndex += 1;
    }
  
    // 15 off-campus residents
    for (let i = 0; i < 15; i++) {
      let studentType = "Regular Student";
      let sport = null;
  
      if (i < 5) {
        studentType = "Athlete";
        sport = getAthleteSport(i);
      } else if (i < 10) {
        studentType = "Copa";
      }
  
      agents.push(
        createAgent({
          agentNumber,
          name: FIRST_NAMES[agentNumber - 1],
          studentType,
          sport,
          housingLocation: "OffCampus",
          livesOnCampus: false,
          personality: getPersonality(agentNumber - 1),
        })
      );
  
      agentNumber += 1;
    }
  
    return agents;
  }
  
  export function getPopulationSummary(agents) {
    const summary = {
      total_agents: agents.length,
      lives_on_campus: 0,
      lives_off_campus: 0,
      by_student_type: {},
      by_housing_location: {},
      by_personality: {},
    };
  
    agents.forEach((agent) => {
      if (agent.lives_on_campus) {
        summary.lives_on_campus += 1;
      } else {
        summary.lives_off_campus += 1;
      }
  
      summary.by_student_type[agent.student_type] =
        (summary.by_student_type[agent.student_type] || 0) + 1;
  
      summary.by_housing_location[agent.housing_location] =
        (summary.by_housing_location[agent.housing_location] || 0) + 1;
  
      summary.by_personality[agent.personality] =
        (summary.by_personality[agent.personality] || 0) + 1;
    });
  
    return summary;
  }
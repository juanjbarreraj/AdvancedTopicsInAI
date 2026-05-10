import { CAMPUS_POSITIONS } from "../data/campusPositions";
import { buildCampusRoute } from "../data/campusPaths";
import LocationNode from "./LocationNode";
import AgentDot from "./AgentDot";

function getOffsetPosition(basePosition, index, total) {
  if (!basePosition) return null;

  if (total <= 1) {
    return {
      x: basePosition.x + 2.2,
      y: basePosition.y,
    };
  }

  const radius = 3.5;
  const safeIndex = Math.max(index, 0);
  const angle = (2 * Math.PI * safeIndex) / total;

  return {
    x: basePosition.x + Math.cos(angle) * radius,
    y: basePosition.y + Math.sin(angle) * radius,
  };
}

function groupAgentsByLocation(agents, locationField) {
  return agents.reduce((groups, agent) => {
    const location =
      agent[locationField] ||
      agent.target_location_now ||
      agent.current_location ||
      "Unknown";

    if (!groups[location]) {
      groups[location] = [];
    }

    groups[location].push(agent.agent_id);
    return groups;
  }, {});
}

function CampusMap({ agents, selectedAgent, onSelectAgent }) {
  const currentLocationGroups = groupAgentsByLocation(
    agents,
    "visual_start_location"
  );

  const targetLocationGroups = groupAgentsByLocation(
    agents,
    "target_location_now"
  );

  return (
    <div className="campus-map">
      {Object.entries(CAMPUS_POSITIONS).map(([name, position]) => (
        <LocationNode key={name} name={name} position={position} />
      ))}

      {agents.map((agent) => {
        const startLocation =
          agent.visual_start_location ||
          agent.current_location ||
          agent.housing_location;

        const targetLocation =
          agent.target_location_now ||
          agent.current_location ||
          agent.housing_location;

        const startBase = CAMPUS_POSITIONS[startLocation];
        const endBase = CAMPUS_POSITIONS[targetLocation];

        if (!startBase || !endBase) {
          console.warn("Missing campus position for agent:", {
            agent,
            startLocation,
            targetLocation,
          });

          return null;
        }

        const currentGroup = currentLocationGroups[startLocation] || [];
        const targetGroup = targetLocationGroups[targetLocation] || [];

        const currentIndex = currentGroup.indexOf(agent.agent_id);
        const targetIndex = targetGroup.indexOf(agent.agent_id);

        const startPosition = getOffsetPosition(
          startBase,
          currentIndex,
          currentGroup.length
        );

        const endPosition = getOffsetPosition(
          endBase,
          targetIndex,
          targetGroup.length
        );

        const routePoints = buildCampusRoute(
          startLocation,
          targetLocation,
          startPosition,
          endPosition
        );

        return (
          <AgentDot
            key={agent.agent_id}
            agent={agent}
            pathPoints={routePoints}
            isSelected={selectedAgent?.agent_id === agent.agent_id}
            onClick={onSelectAgent}
            movementVersion={agent.movement_version || 0}
          />
        );
      })}
    </div>
  );
}

export default CampusMap;
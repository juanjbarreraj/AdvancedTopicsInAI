function formatLocationName(location) {
  const locationLabels = {
    VillagePark: "Village Park",
    BoulevardAppartments: "Boulevard Apartments",
    StudentCenter: "Student Center",
    WestPenn: "West Penn",
    ConestogaHall: "Conestoga Hall",
    LawrenceHall: "Lawrence Hall",
    ThayerHall: "Thayer Hall",
    AcademicHall: "Academic Hall",
    GeorgeRowlandWhite: "George Rowland White",
    Library: "Library",
    PlayHouse: "Playhouse",
    Track: "Track",
    OffCampus: "Off Campus",
  };

  return locationLabels[location] || location || "Unknown";
}

function AgentInfoPanel({ selectedAgent }) {
  if (!selectedAgent) {
    return (
      <div className="panel-card">
        <h2>Selected Agent</h2>
        <p>Click a dot on the campus map to view agent details.</p>
      </div>
    );
  }

  return (
    <div className="panel-card">
      <h2>Selected Agent</h2>

      <p>
        <strong>Agent ID:</strong> {selectedAgent.agent_id}
      </p>

      <p>
  <strong>Name:</strong> {selectedAgent.name}
</p>

<p>
  <strong>Personality:</strong> {selectedAgent.personality}
</p>

<p>
  <strong>Housing:</strong>{" "}
  {formatLocationName(selectedAgent.housing_location)}
</p>

<p>
  <strong>Lives On Campus:</strong>{" "}
  {selectedAgent.lives_on_campus ? "Yes" : "No"}
</p>

      <p>
        <strong>Student Type:</strong> {selectedAgent.student_type}
      </p>

      {selectedAgent.sport && (
        <p>
          <strong>Sport:</strong> {selectedAgent.sport}
        </p>
      )}

      <p>
        <strong>Day:</strong> {selectedAgent.day}
      </p>

      <p>
        <strong>Time Slot:</strong> {selectedAgent.time_slot}
      </p>

      <p>
        <strong>Current Location:</strong>{" "}
        {formatLocationName(selectedAgent.current_location)}
      </p>

      <p>
        <strong>Next Destination:</strong>{" "}
        {formatLocationName(selectedAgent.next_destination)}
      </p>
    </div>
  );
}

export default AgentInfoPanel;
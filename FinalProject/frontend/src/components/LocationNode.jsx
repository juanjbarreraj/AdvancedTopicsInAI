const LOCATION_LABELS = {
  VillagePark: "Village Park",
  BoulevardAppartments: "Boulevard Apartments",
  StudentCenter: "Student Center",
  WestPenn: "West Penn",
  ConestogaHall: "Conestoga Hall",
  LawrenceHall: "Lawrence Hall",
  ThayerHall: "Thayer Hall",
  AcademicHall: "Academic Hall",
  GeorgeRowlandWhite: "George Rowland White Performance Center",
  Library: "Library",
  PlayHouse: "Playhouse",
  Track: "Track",
};

function LocationNode({ name, position }) {
  const locationLabel = LOCATION_LABELS[name] || name;

  return (
    <div
      className="location-node"
      title={locationLabel}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
      }}
    />
  );
}

export default LocationNode;
const LOCATION_LEGEND = [
    { id: 1, name: "Village Park" },
    { id: 2, name: "Boulevard Apartments" },
    { id: 3, name: "Student Center" },
    { id: 4, name: "West Penn" },
    { id: 5, name: "Conestoga Hall" },
    { id: 6, name: "Lawrence Hall" },
    { id: 7, name: "Thayer Hall" },
    { id: 8, name: "Academic Hall" },
    { id: 9, name: "George Rowland White Performance Center" },
    { id: 10, name: "Library" },
    { id: 11, name: "Playhouse" },
    { id: 12, name: "Track" },
  ];
  
  function LegendPanel() {
    return (
      <div className="panel-card">
        <h3>Campus Legend</h3>
  
        <div className="legend-grid">
          {LOCATION_LEGEND.map((loc) => (
            <div key={loc.id} className="legend-item">
              <div className="legend-number">{loc.id}</div>
              <div className="legend-name">{loc.name}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }
  
  export default LegendPanel;
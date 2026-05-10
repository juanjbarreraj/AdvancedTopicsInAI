function distance(a, b) {
    const dx = a.x - b.x;
    const dy = a.y - b.y;
    return Math.sqrt(dx * dx + dy * dy);
  }
  
  export const PATH_NODES = {
    // Main north row
    northWest: { x: 30, y: 12 },
    northCenter: { x: 50, y: 12 },
    northEast: { x: 75, y: 12 },
  
    // Upper middle connectors
    westUpper: { x: 20, y: 28 },
    centerUpper: { x: 50, y: 28 },
    eastUpper: { x: 76, y: 28 },
  
    // Middle ring / center lawn connectors
    westMid: { x: 20, y: 44 },
    centerMid: { x: 50, y: 44 },
    eastMid: { x: 76, y: 44 },
  
    // Lower middle connectors
    westLower: { x: 20, y: 62 },
    centerLower: { x: 50, y: 62 },
    eastLower: { x: 76, y: 62 },
  
    // South row
    southWest: { x: 30, y: 80 },
    southCenter: { x: 50, y: 80 },
    southEast: { x: 76, y: 80 },
  
    // Special track connector
    trackNorth: { x: 50, y: 89 },
  
    // Building access points
    libraryAccess: { x: 30, y: 12 },
    playhouseAccess: { x: 76, y: 12 },
    thayerAccess: { x: 20, y: 28 },
    studentCenterAccess: { x: 76, y: 28 },
    lawrenceAccess: { x: 20, y: 44 },
    villageParkAccess: { x: 50, y: 44 },
    boulevardAccess: { x: 76, y: 44 },
    conestogaAccess: { x: 20, y: 56 },
    westPennAccess: { x: 76, y: 56 },
    academicAccess: { x: 30, y: 68 },
    grwAccess: { x: 76, y: 68 },
    offCampusAccess: { x: 90, y: 90 },
  };
  
  export const PATH_GRAPH = {
    northWest: ["northCenter", "westUpper", "libraryAccess"],
    northCenter: ["northWest", "northEast", "centerUpper"],
    northEast: ["northCenter", "eastUpper", "playhouseAccess"],
  
    westUpper: ["northWest", "centerUpper", "westMid", "thayerAccess"],
    centerUpper: ["northCenter", "westUpper", "eastUpper", "centerMid"],
    eastUpper: ["northEast", "centerUpper", "eastMid", "studentCenterAccess"],
  
    westMid: ["westUpper", "centerMid", "westLower", "lawrenceAccess", "conestogaAccess"],
    centerMid: ["centerUpper", "westMid", "eastMid", "centerLower", "villageParkAccess"],
    eastMid: ["eastUpper", "centerMid", "eastLower", "boulevardAccess", "westPennAccess"],
  
    westLower: ["westMid", "centerLower", "southWest", "conestogaAccess"],
    centerLower: ["centerMid", "westLower", "eastLower", "southCenter", "academicAccess"],
    eastLower: ["eastMid", "centerLower", "southEast", "grwAccess", "westPennAccess"],
  
    southWest: ["westLower", "southCenter", "academicAccess"],
    southCenter: ["southWest", "southEast", "trackNorth"],
    southEast: ["eastLower", "southCenter", "grwAccess"],
  
    trackNorth: ["southCenter"],
  
    libraryAccess: ["northWest"],
    playhouseAccess: ["northEast"],
    thayerAccess: ["westUpper"],
    studentCenterAccess: ["eastUpper"],
    lawrenceAccess: ["westMid"],
    villageParkAccess: ["centerMid"],
    boulevardAccess: ["eastMid"],
    conestogaAccess: ["westMid", "westLower"],
    westPennAccess: ["eastMid", "eastLower"],
    academicAccess: ["centerLower", "southWest"],
    grwAccess: ["eastLower", "southEast"],
    offCampusAccess: [],
  };
  
  export const LOCATION_ACCESS_NODES = {
    VillagePark: "villageParkAccess",
    BoulevardAppartments: "boulevardAccess",
    StudentCenter: "studentCenterAccess",
    WestPenn: "westPennAccess",
    ConestogaHall: "conestogaAccess",
    LawrenceHall: "lawrenceAccess",
    ThayerHall: "thayerAccess",
    AcademicHall: "academicAccess",
    GeorgeRowlandWhite: "grwAccess",
    Library: "libraryAccess",
    PlayHouse: "playhouseAccess",
    Track: "trackNorth",
    OffCampus: "offCampusAccess",
  };
  
  function reconstructPath(previous, endNode) {
    const result = [];
    let current = endNode;
  
    while (current) {
      result.unshift(current);
      current = previous[current];
    }
  
    return result;
  }
  
  function shortestPath(startNode, endNode) {
    if (!startNode || !endNode) return [];
    if (startNode === endNode) return [startNode];
  
    const distances = {};
    const previous = {};
    const unvisited = new Set(Object.keys(PATH_GRAPH));
  
    Object.keys(PATH_GRAPH).forEach((node) => {
      distances[node] = Infinity;
      previous[node] = null;
    });
  
    distances[startNode] = 0;
  
    while (unvisited.size > 0) {
      let current = null;
      let bestDistance = Infinity;
  
      unvisited.forEach((node) => {
        if (distances[node] < bestDistance) {
          bestDistance = distances[node];
          current = node;
        }
      });
  
      if (!current) break;
      if (current === endNode) break;
  
      unvisited.delete(current);
  
      const neighbors = PATH_GRAPH[current] || [];
  
      neighbors.forEach((neighbor) => {
        if (!unvisited.has(neighbor)) return;
  
        const edgeWeight = distance(PATH_NODES[current], PATH_NODES[neighbor]);
        const candidateDistance = distances[current] + edgeWeight;
  
        if (candidateDistance < distances[neighbor]) {
          distances[neighbor] = candidateDistance;
          previous[neighbor] = current;
        }
      });
    }
  
    return reconstructPath(previous, endNode);
  }
  
  function dedupeConsecutivePoints(points) {
    if (!points.length) return points;
  
    const cleaned = [points[0]];
  
    for (let i = 1; i < points.length; i++) {
      const prev = cleaned[cleaned.length - 1];
      const curr = points[i];
  
      if (distance(prev, curr) > 0.2) {
        cleaned.push(curr);
      }
    }
  
    return cleaned;
  }
  
  export function buildCampusRoute(startLocation, endLocation, startPoint, endPoint) {
    if (!startPoint || !endPoint) return [];
  
    if (startLocation === endLocation) {
      return dedupeConsecutivePoints([startPoint, endPoint]);
    }
  
    const startAccessNode = LOCATION_ACCESS_NODES[startLocation];
    const endAccessNode = LOCATION_ACCESS_NODES[endLocation];
  
    if (!startAccessNode || !endAccessNode) {
      return dedupeConsecutivePoints([startPoint, endPoint]);
    }
  
    if (endLocation === "OffCampus") {
      return dedupeConsecutivePoints([
        startPoint,
        PATH_NODES[startAccessNode],
        PATH_NODES.eastLower,
        PATH_NODES.southEast,
        PATH_NODES.offCampusAccess,
        endPoint,
      ]);
    }
  
    const nodePath = shortestPath(startAccessNode, endAccessNode);
    const routePoints = [
      startPoint,
      PATH_NODES[startAccessNode],
      ...nodePath.map((nodeName) => PATH_NODES[nodeName]),
      PATH_NODES[endAccessNode],
      endPoint,
    ];
  
    return dedupeConsecutivePoints(routePoints);
  }
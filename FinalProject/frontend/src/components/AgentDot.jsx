import { useEffect, useRef, useState } from "react";

function getSegmentLength(a, b) {
  if (!a || !b) return 0;

  const dx = b.x - a.x;
  const dy = b.y - a.y;

  return Math.sqrt(dx * dx + dy * dy);
}

function getTotalPathLength(points) {
  if (!points || points.length < 2) return 0;

  let total = 0;

  for (let i = 0; i < points.length - 1; i++) {
    total += getSegmentLength(points[i], points[i + 1]);
  }

  return total;
}

function interpolateAlongPath(points, progress) {
  if (!points || points.length === 0) return null;
  if (points.length === 1) return points[0];

  const totalLength = getTotalPathLength(points);

  if (totalLength === 0) {
    return points[points.length - 1];
  }

  const targetDistance = totalLength * progress;
  let distanceCovered = 0;

  for (let i = 0; i < points.length - 1; i++) {
    const start = points[i];
    const end = points[i + 1];
    const segmentLength = getSegmentLength(start, end);

    if (distanceCovered + segmentLength >= targetDistance) {
      const remaining = targetDistance - distanceCovered;

      const localProgress =
        segmentLength === 0 ? 0 : remaining / segmentLength;

      return {
        x: start.x + (end.x - start.x) * localProgress,
        y: start.y + (end.y - start.y) * localProgress,
      };
    }

    distanceCovered += segmentLength;
  }

  return points[points.length - 1];
}

function AgentDot({
  agent,
  pathPoints,
  isSelected,
  onClick,
  movementVersion,
}) {
  const [position, setPosition] = useState(pathPoints?.[0] || null);

  const positionRef = useRef(pathPoints?.[0] || null);
  const pathRef = useRef(pathPoints || []);
  const lastMovementVersionRef = useRef(null);
  const animationFrameRef = useRef(null);

  useEffect(() => {
    pathRef.current = pathPoints || [];

    if (!positionRef.current && pathPoints?.length) {
      setPosition(pathPoints[0]);
      positionRef.current = pathPoints[0];
    }
  }, [pathPoints]);

  useEffect(() => {
    positionRef.current = position;
  }, [position]);

  useEffect(() => {
    if (lastMovementVersionRef.current === movementVersion) return;

    const currentPath = pathRef.current;

    if (!currentPath || currentPath.length === 0) return;

    lastMovementVersionRef.current = movementVersion;

    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    const totalLength = getTotalPathLength(currentPath);

    if (totalLength === 0) {
      const finalPoint = currentPath[currentPath.length - 1];
      setPosition(finalPoint);
      positionRef.current = finalPoint;
      return;
    }

    /*
      Movement speed:
      Previous version was:
      Math.max(1800, Math.min(6500, totalLength * 60))

      This version is about 50% slower:
      - minimum: 2700ms instead of 1800ms
      - maximum: 9750ms instead of 6500ms
      - route scaling: totalLength * 90 instead of * 60
    */
    const duration = Math.max(2700, Math.min(9750, totalLength * 90));

    const startTime = performance.now();

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const nextPosition = interpolateAlongPath(currentPath, progress);

      if (nextPosition) {
        setPosition(nextPosition);
        positionRef.current = nextPosition;
      }

      if (progress < 1) {
        animationFrameRef.current = requestAnimationFrame(animate);
      } else {
        const finalPoint = currentPath[currentPath.length - 1];
        setPosition(finalPoint);
        positionRef.current = finalPoint;
        animationFrameRef.current = null;
      }
    };

    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
        animationFrameRef.current = null;
      }
    };
  }, [movementVersion]);

  const getAgentClass = () => {
    if (agent.student_type === "Athlete") return "agent-athlete";
    if (agent.student_type === "Copa") return "agent-copa";
    return "agent-regular";
  };

  if (!position) return null;

  return (
    <div
      className={`agent-dot ${getAgentClass()} ${
        isSelected ? "selected" : ""
      }`}
      style={{
        left: `${position.x}%`,
        top: `${position.y}%`,
      }}
      title={`${agent.name || "Agent"} ${agent.agent_id}: ${
        agent.current_location
      } → ${agent.next_destination}`}
      onClick={() => onClick(agent)}
    />
  );
}

export default AgentDot;
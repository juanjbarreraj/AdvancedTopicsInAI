import { useEffect, useState } from "react";

const API_BASE =
  import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

function AISystemPanel() {
  const [status, setStatus] = useState(null);
  const [showDetails, setShowDetails] = useState(false);

  useEffect(() => {
    async function fetchStatus() {
      try {
        const response = await fetch(`${API_BASE}/ai-status`);
        const data = await response.json();
        setStatus(data);
      } catch (error) {
        console.error("Error loading AI system status:", error);
      }
    }

    fetchStatus();
  }, []);

  if (!status) {
    return (
      <div className="panel-card">
        <h3>AI System Status</h3>
        <p>Loading AI system status...</p>
      </div>
    );
  }

  const nlp = status.nlp_system;
  const rl = status.reinforcement_learning;
  const em = status.em_activity_model;

  return (
    <div className="panel-card">
      <h3>AI System Status</h3>

      <div className="ai-status-list">
        <div>
          <strong>NLP:</strong>{" "}
          {nlp?.system_name || "Neural NLP System"}
        </div>

        <div>
          <strong>Reinforcement Learning:</strong>{" "}
          {rl?.system || "Q-Learning Campus Decision Model"}
        </div>

        <div>
          <strong>EM Hidden Activity Model:</strong>{" "}
          {em?.system || "EM Hidden Activity-Mode Model"}
        </div>

        <div>
          <strong>Device:</strong> {nlp?.device || "CPU"}
        </div>

        <div>✓ Word Representations</div>
        <div>✓ GRU Sequence Modeling</div>
        <div>✓ Attention-BiGRU Model</div>
        <div>✓ Transfer Learning Extension</div>
        <div>✓ System Analysis Metrics</div>
        <div>✓ EM Hidden-Mode Inference</div>
        <div>✓ Q-Learning Reinforcement Learning</div>
        <div>✓ End-to-End AI Integration</div>
      </div>

      <button
        className="details-button"
        onClick={() => setShowDetails((prev) => !prev)}
      >
        {showDetails ? "Hide AI Details" : "Show AI Details"}
      </button>

      {showDetails && (
        <div className="ai-status-details">
          <h4>NLP System</h4>
          <pre>{JSON.stringify(nlp, null, 2)}</pre>

          <h4>Reinforcement Learning</h4>
          <pre>{JSON.stringify(rl, null, 2)}</pre>

          <h4>EM Hidden Activity Model</h4>
          <pre>{JSON.stringify(em, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}

export default AISystemPanel;
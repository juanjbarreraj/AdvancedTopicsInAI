import { useEffect, useState } from "react";

function QuestionPanel({ selectedAgent, onAskQuestion, answer }) {
  const [question, setQuestion] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [typedAnswer, setTypedAnswer] = useState("");

  const exampleQuestions = [
    "How are you?",
    "Who are you?",
    "Who are you with?",
    "Where are you going next?",
    "Why are you here?",
    "Why are you not in the Library?",
    "Can we miss class?",
    "Please go to Village Park next.",
  ];

  useEffect(() => {
    if (!answer?.answer) {
      setTypedAnswer("");
      return;
    }

    setTypedAnswer("");

    const fullAnswer = answer.answer;
    let index = 0;

    const typingInterval = setInterval(() => {
      index += 1;
      setTypedAnswer(fullAnswer.slice(0, index));

      if (index >= fullAnswer.length) {
        clearInterval(typingInterval);
      }
    }, 25);

    return () => clearInterval(typingInterval);
  }, [answer]);

  const handleSubmit = async (questionToAsk = question) => {
    if (!selectedAgent) {
      alert("Please click an agent first.");
      return;
    }

    if (!questionToAsk.trim()) {
      alert("Please type or select a question.");
      return;
    }

    try {
      setIsLoading(true);
      setTypedAnswer("");
      await onAskQuestion(questionToAsk);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExampleClick = async (exampleQuestion) => {
    setQuestion(exampleQuestion);
    await handleSubmit(exampleQuestion);
  };

  const reasoning = answer?.campus_ai_reasoning;
  const activityMode = reasoning?.activity_mode_inference;
  const expectedUtility = reasoning?.expected_utility;
  const valueOfInformation = reasoning?.value_of_information;
  const congestion = reasoning?.multiagent_congestion;
  const rlRecommendation = reasoning?.rl_action_recommendation;
  const probability = reasoning?.probability_to_destination;

  const reinforcementLearning = answer?.reinforcement_learning;
  const emActivityInference = answer?.em_activity_inference;

  const missClassDecision = answer?.miss_class_decision;
  const commandDecision = answer?.command_decision;

  return (
    <div className="panel-card">
      <h2>Ask the Agent</h2>

      <p className="panel-help-text">
        Select a question or type your own question to ask the selected agent.
      </p>

      {selectedAgent?.conversation_state === "awaiting_miss_class_reason" && (
        <div className="conversation-state-box">
          <strong>Conversation State:</strong> The agent is waiting for your
          reason before deciding whether to miss class.
        </div>
      )}

      <input
        type="text"
        className="question-input"
        placeholder={
          selectedAgent
            ? "Example: I am exhausted and need a break."
            : "Select an agent first..."
        }
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            handleSubmit();
          }
        }}
        disabled={!selectedAgent || isLoading}
      />

      <button
        className="ask-button"
        onClick={() => handleSubmit()}
        disabled={!selectedAgent || isLoading}
      >
        {isLoading ? "Thinking..." : "Ask"}
      </button>

      <div className="example-question-list">
        {exampleQuestions.map((exampleQuestion) => (
          <button
            key={exampleQuestion}
            className="example-question-button"
            onClick={() => handleExampleClick(exampleQuestion)}
            disabled={!selectedAgent || isLoading}
          >
            {exampleQuestion}
          </button>
        ))}
      </div>

      <div className="answer-box machine-answer-box">
        {isLoading ? (
          <p className="machine-thinking">
            Processing question through neural NLP model...
          </p>
        ) : answer ? (
          <>
            <p>
              <strong>Question:</strong> {answer.question}
            </p>

            <div className="machine-response">
              <strong>Machine Response:</strong>
              <div className="typing-text">
                {typedAnswer}
                <span className="typing-cursor">|</span>
              </div>
            </div>

            {(answer.requires_followup ||
              answer.conversation_state ||
              answer.pending_decision) && (
              <div className="decision-followup-box">
                <h4>Conversation Follow-Up State</h4>

                {answer.requires_followup && (
                  <p>
                    <strong>Requires Follow-Up:</strong> Yes
                  </p>
                )}

                {answer.conversation_state && (
                  <p>
                    <strong>Conversation State:</strong>{" "}
                    {answer.conversation_state}
                  </p>
                )}

                {answer.pending_decision && (
                  <>
                    <p>
                      <strong>Pending Decision:</strong>{" "}
                      {answer.pending_decision.type}
                    </p>

                    <p>
                      <strong>Expected Location:</strong>{" "}
                      {answer.pending_decision.expected_location}
                    </p>

                    <p>
                      <strong>Current Location:</strong>{" "}
                      {answer.pending_decision.current_location}
                    </p>

                    <p>
                      <strong>Obligation Type:</strong>{" "}
                      {answer.pending_decision.obligation_type}
                    </p>
                  </>
                )}
              </div>
            )}

            {missClassDecision && (
              <div className="decision-followup-box">
                <h4>Miss-Class Decision</h4>

                <p>
                  <strong>Decision:</strong>{" "}
                  {missClassDecision.decision || "Not available"}
                </p>

                <p>
                  <strong>Accepted:</strong>{" "}
                  {missClassDecision.accepted ? "Yes" : "No"}
                </p>

                {missClassDecision.new_location && (
                  <p>
                    <strong>New Location:</strong>{" "}
                    {missClassDecision.new_location}
                  </p>
                )}

                {missClassDecision.missed_classes_increment && (
                  <p>
                    <strong>Missed Classes Added:</strong>{" "}
                    {missClassDecision.missed_classes_increment}
                  </p>
                )}

                {missClassDecision.reliability_penalty !== undefined && (
                  <p>
                    <strong>Reliability Penalty:</strong>{" "}
                    {missClassDecision.reliability_penalty}
                  </p>
                )}

                {missClassDecision.academic_risk_increase !== undefined && (
                  <p>
                    <strong>Academic Risk Increase:</strong>{" "}
                    {missClassDecision.academic_risk_increase}
                  </p>
                )}

                {missClassDecision.reason && (
                  <p>
                    <strong>Reason:</strong> {missClassDecision.reason}
                  </p>
                )}

                {missClassDecision.reason_quality && (
                  <p>
                    <strong>Reason Quality:</strong>{" "}
                    {missClassDecision.reason_quality.quality} (
                    {missClassDecision.reason_quality.score})
                  </p>
                )}
              </div>
            )}

            {commandDecision && (
              <div className="decision-followup-box">
                <h4>User Command Decision</h4>

                <p>
                  <strong>Accepted:</strong>{" "}
                  {commandDecision.accepted ? "Yes" : "No"}
                </p>

                <p>
                  <strong>Tone:</strong> {commandDecision.tone}
                </p>

                {commandDecision.display_requested_location && (
                  <p>
                    <strong>Requested Location:</strong>{" "}
                    {commandDecision.display_requested_location}
                  </p>
                )}

                <p>
                  <strong>Reason:</strong> {commandDecision.reason}
                </p>
              </div>
            )}

            {emActivityInference && (
              <div className="decision-followup-box">
                <h4>EM Hidden Activity-Mode Inference</h4>

                <p>
                  <strong>Model:</strong> {emActivityInference.model}
                </p>

                <p>
                  <strong>Chapter:</strong> {emActivityInference.chapter}
                </p>

                <p>
                  <strong>Most Likely Mode:</strong>{" "}
                  {emActivityInference.most_likely_mode}
                </p>

                <p>
                  <strong>Iterations:</strong> {emActivityInference.iterations}
                </p>

                <p>
                  <strong>Final Log-Likelihood:</strong>{" "}
                  {emActivityInference.final_log_likelihood}
                </p>

                <p>{emActivityInference.interpretation}</p>

                {emActivityInference.mode_probabilities && (
                  <div className="utility-list">
                    {Object.entries(emActivityInference.mode_probabilities).map(
                      ([mode, probability]) => (
                        <div key={mode} className="utility-row">
                          <span>{mode}</span>
                          <span>{Math.round(probability * 100)}%</span>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            )}

            {reinforcementLearning && (
              <div className="decision-followup-box">
                <h4>Q-Learning Reinforcement Learning Evidence</h4>

                <p>
                  <strong>Model:</strong> {reinforcementLearning.model}
                </p>

                <p>
                  <strong>Chapter:</strong> {reinforcementLearning.chapter}
                </p>

                <p>
                  <strong>Recommended Action:</strong>{" "}
                  {reinforcementLearning.recommended_action}
                </p>

                <p>
                  <strong>Training Episodes:</strong>{" "}
                  {reinforcementLearning.training_episodes}
                </p>

                <p>
                  <strong>Average Reward Last 100:</strong>{" "}
                  {reinforcementLearning.training_average_reward_last_100}
                </p>

                <p>{reinforcementLearning.interpretation}</p>

                {reinforcementLearning.q_values && (
                  <div className="utility-list">
                    {Object.entries(reinforcementLearning.q_values).map(
                      ([action, value]) => (
                        <div key={action} className="utility-row">
                          <span>{action}</span>
                          <span>Q: {value}</span>
                        </div>
                      )
                    )}
                  </div>
                )}
              </div>
            )}

            <div className="ai-evidence-box">
              <h4>AI/NLP Evidence</h4>

              <p>
                <strong>Predicted Intent:</strong>{" "}
                {answer.predicted_intent || "Not returned"}
              </p>

              <p>
                <strong>Confidence:</strong>{" "}
                {answer.confidence !== undefined
                  ? `${Math.round(answer.confidence * 100)}%`
                  : "Not returned"}
              </p>

              <p>
                <strong>Model Used:</strong>{" "}
                {answer.model_used || "Not returned"}
              </p>

              {answer.attention_weights &&
                answer.attention_weights.length > 0 && (
                  <div className="attention-section">
                    <strong>Attention Weights:</strong>

                    <div className="attention-token-grid">
                      {answer.attention_weights.map((item, index) => (
                        <div key={index} className="attention-token">
                          <span className="attention-token-word">
                            {item.token}
                          </span>
                          <span className="attention-token-weight">
                            {item.weight}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

              {answer.word_representations?.nearest_neighbors && (
                <div className="word-representation-section">
                  <strong>Word Representations:</strong>

                  {Object.entries(
                    answer.word_representations.nearest_neighbors
                  ).map(([word, neighbors]) => (
                    <div key={word} className="neighbor-row">
                      <span className="neighbor-word">{word}:</span>
                      <span className="neighbor-list">
                        {neighbors.length > 0
                          ? neighbors
                              .map(
                                ([neighbor, score]) =>
                                  `${neighbor} (${score})`
                              )
                              .join(", ")
                          : "No close neighbors found"}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {answer.ai_pipeline && (
                <div className="pipeline-section">
                  <strong>End-to-End AI Pipeline:</strong>
                  <ol>
                    {Object.values(answer.ai_pipeline).map((step, index) => (
                      <li key={index}>{step}</li>
                    ))}
                  </ol>
                </div>
              )}
            </div>

            {reasoning && (
              <div className="campus-reasoning-box">
                <h4>Campus AI Reasoning Evidence</h4>

                <p className="reasoning-intro">
                  This section is computed live from the selected agent, all
                  visible agents, the current time slot, and the neural NLP
                  intent prediction.
                </p>

                {activityMode && (
                  <div className="reasoning-card">
                    <h5>Hidden Activity Mode Inference</h5>
                    <p>
                      <strong>Mode:</strong> {activityMode.activity_mode}
                    </p>
                    <p>
                      <strong>Confidence:</strong>{" "}
                      {Math.round(activityMode.confidence * 100)}%
                    </p>
                    <p>{activityMode.reason}</p>
                  </div>
                )}

                {expectedUtility?.best_destination && (
                  <div className="reasoning-card">
                    <h5>Expected Utility Decision Scoring</h5>

                    <p>
                      <strong>Best Destination:</strong>{" "}
                      {expectedUtility.best_destination.display_destination}
                    </p>

                    <p>
                      <strong>Expected Utility:</strong>{" "}
                      {expectedUtility.best_destination.expected_utility}
                    </p>

                    <p>
                      The system compares destinations using location fit,
                      graph distance, crowding cost, and the scheduled
                      destination bonus.
                    </p>

                    <div className="utility-list">
                      {expectedUtility.top_utilities
                        ?.slice(0, 3)
                        .map((item) => (
                          <div
                            key={item.destination}
                            className="utility-row"
                          >
                            <span>{item.display_destination}</span>
                            <span>EU: {item.expected_utility}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {valueOfInformation && (
                  <div className="reasoning-card">
                    <h5>Value of Information</h5>

                    <p>
                      <strong>Information Action:</strong>{" "}
                      {valueOfInformation.information_action}
                    </p>

                    <p>
                      <strong>Estimated VOI:</strong>{" "}
                      {valueOfInformation.estimated_value_of_information}
                    </p>

                    <p>
                      <strong>Recommend Checking:</strong>{" "}
                      {valueOfInformation.recommend_checking ? "Yes" : "No"}
                    </p>
                  </div>
                )}

                {congestion && (
                  <div className="reasoning-card">
                    <h5>Multiagent Congestion Analysis</h5>

                    <p>
                      <strong>Congestion Level:</strong>{" "}
                      {congestion.congestion_level}
                    </p>

                    <p>{congestion.multiagent_interpretation}</p>

                    <p>
                      <strong>Agents targeting same destination:</strong>{" "}
                      {congestion.agents_targeting_same_destination?.join(
                        ", "
                      )}
                    </p>

                    <p>
                      <strong>Total Agents Considered:</strong>{" "}
                      {congestion.total_agents_considered || "Not shown"}
                    </p>
                  </div>
                )}

                {rlRecommendation && (
                  <div className="reasoning-card">
                    <h5>Q-Style Reward Action Scoring</h5>

                    <p>
                      <strong>Recommended Action:</strong>{" "}
                      {rlRecommendation.recommended_action}
                    </p>

                    <p>
                      <strong>STAY Score:</strong>{" "}
                      {rlRecommendation.q_style_scores?.STAY}
                    </p>

                    <p>
                      <strong>MOVE Score:</strong>{" "}
                      {rlRecommendation.q_style_scores?.MOVE}
                    </p>

                    <p>{rlRecommendation.interpretation}</p>
                  </div>
                )}

                {probability && (
                  <div className="reasoning-card">
                    <h5>Probability-to-Destination Estimate</h5>

                    <p>
                      <strong>Target Destination:</strong>{" "}
                      {probability.display_target_destination}
                    </p>

                    <p>
                      <strong>Estimated Probability:</strong>{" "}
                      {Math.round(probability.estimated_probability * 100)}%
                    </p>

                    <p>
                      <strong>Student-Type Fit:</strong>{" "}
                      {probability.student_type_fit}
                    </p>

                    <p>
                      <strong>Distance Factor:</strong>{" "}
                      {probability.distance_factor}
                    </p>

                    <p>
                      <strong>Crowd Factor:</strong> {probability.crowd_factor}
                    </p>
                  </div>
                )}

                {reasoning.implemented_ai_layers && (
                  <div className="reasoning-card">
                    <h5>Implemented Campus AI Layers</h5>

                    <ul>
                      {reasoning.implemented_ai_layers.map((layer) => (
                        <li key={layer}>{layer}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <p>No question asked yet.</p>
        )}
      </div>
    </div>
  );
}

export default QuestionPanel;
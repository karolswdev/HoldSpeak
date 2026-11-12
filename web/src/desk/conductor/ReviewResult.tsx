import { InspectorBody, PaneActions } from "../surface";
import { reviewResult, type AgentReview } from "../agentFlights";

/** The one AG12 pair result shared by the lane Result and the NEEDS YOU row. */
export function ReviewResult({ review, title = true }: { review: AgentReview | null | undefined; title?: boolean }) {
  const result = reviewResult(review);
  if (!result) return null;
  return (
    <div data-testid="agent-review-result" data-feedback-redact="true">
      <InspectorBody>
        <PaneActions>
          {title ? <strong>Result</strong> : null}
          {result.rounds > 0 ? (
            <span data-testid="agent-review-rounds">
              {result.rounds} {result.rounds === 1 ? "round" : "rounds"}
            </span>
          ) : null}
        </PaneActions>
        {result.findingsLeft.length ? (
          <ul className="cw-review-findings" data-testid="agent-review-findings">
            {result.findingsLeft.map((finding, index) => (
              <li key={`${finding.level}:${finding.text}:${index}`}>
                <strong>{finding.level}:</strong> {finding.text}
              </li>
            ))}
          </ul>
        ) : (
          <span className="cw-review-clear" data-testid="agent-review-clear">
            MUST: none
          </span>
        )}
        {result.reason ? <span className="cw-review-reason">{result.reason}</span> : null}
      </InspectorBody>
    </div>
  );
}

// HS-159-05 -- test result display (ACT-002): count, up to five
// entities, observed time, "Test passed -- 0 current matches" honesty.

import type { TestResult as TestResultType } from "./model";

export function TestResultDisplay({
  result,
  testState,
}: {
  result: TestResultType;
  testState: string;
}) {
  const isPassed = testState === "passed";
  const isFailed = testState === "failed";

  return (
    <div
      className="setup-test-result"
      data-test-state={testState}
      data-testid="setup-test-result"
      role="status"
      aria-live="polite"
    >
      {/* Status line */}
      <div className="setup-test-result-status">
        <span className="setup-test-result-icon" aria-hidden="true">
          {isPassed ? "✓" : isFailed ? "✗" : "…"}
        </span>
        <span>{result.message}</span>
      </div>

      {/* Entity count */}
      <div className="setup-test-result-count">
        {result.entityCount} current match{result.entityCount !== 1 ? "es" : ""}
      </div>

      {/* Representative entities (up to 5) */}
      {result.representativeEntities.length > 0 ? (
        <div className="setup-test-result-entities">
          {result.representativeEntities.slice(0, 5).map((entity, i) => (
            <div key={i} className="setup-test-result-entity">
              {entityLabel(entity)}
            </div>
          ))}
        </div>
      ) : null}

      {/* Observed time */}
      <div className="setup-test-result-time">
        Observed at {formatTime(result.observedAt)}
      </div>

      {/* Error detail */}
      {result.error ? (
        <div className="setup-test-result-error">
          {result.error.type}: {result.error.message}
        </div>
      ) : null}
    </div>
  );
}

function entityLabel(entity: Record<string, unknown>): string {
  // Best-effort label from common fields
  const title = entity.title ?? entity.text ?? entity.name ?? entity.id;
  return String(title ?? "Unknown");
}

function formatTime(iso: string): string {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

// HS-167-05 -- test result display (D2/D3): N matches · M calls · s as
// receipt-style tokens, ledger rows of matches (emblem + title + StateChip),
// state as a StateChip. No sentence.

import {
  StateChip,
  SurfaceLedger,
  SurfaceLedgerRow,
  type ChipState,
} from "../../../desk/surface";
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

  const chipState: ChipState = isPassed
    ? "success"
    : isFailed
      ? "failure"
      : "working";

  // Receipt-style count tokens
  const countParts: string[] = [];
  countParts.push(
    `${result.entityCount} match${result.entityCount !== 1 ? "es" : ""}`,
  );
  if (result.calls != null && result.calls > 0) {
    countParts.push(`${result.calls} call${result.calls !== 1 ? "s" : ""}`);
  }
  if (result.durationMs != null && result.durationMs > 0) {
    countParts.push(`${(result.durationMs / 1000).toFixed(1)}s`);
  }

  return (
    <div
      className="setup-test-result"
      data-test-state={testState}
      data-testid="setup-test-result"
      role="status"
      aria-live="polite"
    >
      {/* State as StateChip */}
      <StateChip state={chipState} label={isPassed ? "Ready" : isFailed ? "Failed" : "Testing"} />

      {/* Receipt-style count tokens */}
      <span className="setup-test-result-counts">
        {countParts.map((part, i) => (
          <span key={i} className="surface-token" data-chip>
            {part}
          </span>
        ))}
      </span>

      {/* Ledger rows of matches (emblem + title + StateChip) */}
      {result.representativeEntities.length > 0 ? (
        <SurfaceLedger count={`MATCHES ${result.entityCount}`} cols="room">
          <ul className="surface-ledger-rows">
            {result.representativeEntities.slice(0, 5).map((entity, i) => {
              const title = entityTitle(entity);
              const id = entity.id != null ? String(entity.id) : "";
              const state = entity.state != null ? String(entity.state) : "";
              return (
                <SurfaceLedgerRow
                  key={i}
                  expands={false}
                  lead={
                    <span className="setup-test-entity-emblem" aria-hidden="true">
                      {"◉"}
                    </span>
                  }
                  primary={id ? `#${id} ${title}` : title}
                  cells={
                    state ? (
                      <StateChip state="idle" label={state} />
                    ) : null
                  }
                />
              );
            })}
          </ul>
        </SurfaceLedger>
      ) : null}

      {/* Error detail */}
      {result.error ? (
        <div className="setup-test-result-error">
          <StateChip state="failure" label={result.error.type} />
          <span className="surface-token" data-tone="danger">
            {result.error.message}
          </span>
        </div>
      ) : null}
    </div>
  );
}

/** Extract a human title from a normalized entity. */
function entityTitle(entity: Record<string, unknown>): string {
  const title = entity.title != null && String(entity.title) !== ""
    ? String(entity.title)
    : (entity.text != null
        ? String(entity.text)
        : (entity.name != null ? String(entity.name) : null));
  return title ?? "Unknown";
}

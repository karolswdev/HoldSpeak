// HS-159-05 -- activation review (ACT-001/WEB-CR-011): outcome, each
// Watch spec with ledger-aligned label/value rows, posture token,
// plain-words conditions, cadence, action, test result, first-run
// behavior, step indicator.
// Cmd/Ctrl+Enter activates (WEB-CMD-005).

import { useCallback, useEffect, type KeyboardEvent } from "react";
import {
  cadenceLabel,
  conditionPlainWords,
  modeLabel,
  ACTION_LABELS,
  STAGE_META,
  STAGE_COUNT,
  type SetupAnswer,
  type SetupProposal,
} from "./model";
import { TestResultDisplay } from "./TestResult";

export function ActivationReview({
  outcomeAnswer,
  signalsAnswer,
  proposals,
  onFinalize,
  onBack,
  finalizing,
}: {
  outcomeAnswer: SetupAnswer;
  signalsAnswer: SetupAnswer;
  proposals: SetupProposal[];
  onFinalize: () => void;
  onBack: () => void;
  finalizing: boolean;
}) {
  const selected = proposals.filter((p) => p.state === "selected");
  const passed = selected.filter((p) => p.testState === "passed");
  const untested = selected.filter((p) => !p.testState);
  const failed = selected.filter((p) => p.testState === "failed");

  // Cmd/Ctrl+Enter activates (WEB-CMD-005)
  useEffect(() => {
    const handler = (e: globalThis.KeyboardEvent) => {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && !finalizing) {
        e.preventDefault();
        onFinalize();
      }
      // Escape goes back (layered Escape)
      if (e.key === "Escape") {
        e.preventDefault();
        onBack();
      }
    };
    // Use capture on the review container, not document
    const el = document.getElementById("setup-review");
    el?.addEventListener("keydown", handler as EventListener);
    return () => el?.removeEventListener("keydown", handler as EventListener);
  }, [onFinalize, onBack, finalizing]);

  const meta = STAGE_META["review"];

  return (
    <div
      className="setup-review"
      id="setup-review"
      tabIndex={-1}
      data-testid="setup-review"
      role="region"
      aria-label="Activation review"
    >
      {/* Step indicator (defect 6) */}
      <div className="setup-step-token" aria-hidden="true" data-testid="setup-step-token">
        Step {meta.index} of {STAGE_COUNT}
      </div>

      <h3 className="setup-review-heading">Review before activation</h3>

      {/* Outcome */}
      <div className="setup-review-section" data-testid="review-outcome">
        <div className="setup-review-label">Outcome</div>
        <div className="setup-review-value">
          {outcomeAnswer.answer.normalized}
        </div>
      </div>

      {/* Signals */}
      <div className="setup-review-section" data-testid="review-signals">
        <div className="setup-review-label">Signals</div>
        <div className="setup-review-value">
          {signalsAnswer.answer.normalized}
        </div>
      </div>

      {/* Selected Watches */}
      <div className="setup-review-section" data-testid="review-watches">
        <div className="setup-review-label">
          Watches ({selected.length} selected, {passed.length} tested)
        </div>

        {selected.length === 0 ? (
          <div className="setup-review-blank">
            No Watches selected. A blank Project will be created.
          </div>
        ) : null}

        {selected.map((p) => (
          <ReviewWatchSpec key={p.id} proposal={p} />
        ))}
      </div>

      {/* Warnings */}
      {untested.length > 0 ? (
        <div className="setup-review-warning" role="alert">
          {untested.length} Watch{untested.length !== 1 ? "es" : ""} not yet
          tested. Only tested Watches will be activated.
        </div>
      ) : null}

      {failed.length > 0 ? (
        <div className="setup-review-warning" role="alert">
          {failed.length} Watch{failed.length !== 1 ? "es" : ""} failed
          testing and will not be activated.
        </div>
      ) : null}

      {/* First-run behavior */}
      <div className="setup-review-section" data-testid="review-first-run">
        <div className="setup-review-label">First-run behavior</div>
        <div className="setup-review-value">
          Baseline established without events. Use "Run initial assessment"
          after activation to evaluate current state.
        </div>
      </div>

      {/* Actions */}
      <div className="setup-review-actions">
        <button
          type="button"
          className="setup-review-back"
          onClick={onBack}
          disabled={finalizing}
        >
          Back
        </button>
        <button
          type="button"
          className="setup-review-activate"
          onClick={onFinalize}
          disabled={finalizing}
          data-testid="review-activate-btn"
        >
          {finalizing ? "Creating..." : "Create Project"}
        </button>
      </div>
    </div>
  );
}

function ReviewWatchSpec({ proposal }: { proposal: SetupProposal }) {
  const spec = proposal.spec;
  return (
    <div
      className="setup-review-watch"
      data-testid={`review-watch-${proposal.id}`}
    >
      <div className="setup-review-watch-name">{spec.name}</div>

      {/* Ledger-aligned label/value rows (defect 4) */}
      <dl className="setup-review-ledger" data-testid={`review-ledger-${proposal.id}`}>
        <div className="setup-review-ledger-row">
          <dt className="setup-review-ledger-label">Subject</dt>
          <dd className="setup-review-ledger-value">{spec.subject.kind}</dd>
        </div>
        <div className="setup-review-ledger-row">
          <dt className="setup-review-ledger-label">Conditions</dt>
          <dd
            className="setup-review-ledger-value"
            data-condition-raw={spec.rules.flatMap((r) =>
              r.condition.clauses.map((c) => `${c.field}:${c.comparison}${c.value != null ? `:${c.value}` : ""}`),
            ).join(",")}
          >
            {conditionPlainWords(spec)}
          </dd>
        </div>
        <div className="setup-review-ledger-row">
          <dt className="setup-review-ledger-label">Cadence</dt>
          <dd className="setup-review-ledger-value">{cadenceLabel(spec.trigger)}</dd>
        </div>
        <div className="setup-review-ledger-row">
          <dt className="setup-review-ledger-label">Action</dt>
          <dd className="setup-review-ledger-value">
            {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
          </dd>
        </div>
        <div className="setup-review-ledger-row">
          <dt className="setup-review-ledger-label">Mode</dt>
          <dd className="setup-review-ledger-value">
            <span className="setup-mode-token" data-mode={spec.mode}>
              {modeLabel(spec.mode)}
            </span>
          </dd>
        </div>
      </dl>

      {proposal.testResult ? (
        <TestResultDisplay
          result={proposal.testResult}
          testState={proposal.testState ?? ""}
        />
      ) : (
        <div className="setup-review-watch-untested">Not tested</div>
      )}
    </div>
  );
}

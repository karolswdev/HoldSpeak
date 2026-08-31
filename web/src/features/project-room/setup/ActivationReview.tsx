// HS-159-05 -- activation review (ACT-001/WEB-CR-011): outcome, each
// Watch spec, cadence, action, test result, first-run behavior.
// Cmd/Ctrl+Enter activates (WEB-CMD-005).

import { useCallback, useEffect, type KeyboardEvent } from "react";
import {
  cadenceLabel,
  conditionSummary,
  ACTION_LABELS,
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

  return (
    <div
      className="setup-review"
      id="setup-review"
      tabIndex={-1}
      data-testid="setup-review"
      role="region"
      aria-label="Activation review"
    >
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
      <div className="setup-review-watch-details">
        <div className="setup-review-watch-row">
          <span className="setup-review-watch-key">Subject</span>
          <span>{spec.subject.kind}</span>
        </div>
        <div className="setup-review-watch-row">
          <span className="setup-review-watch-key">Conditions</span>
          <span>{conditionSummary(spec)}</span>
        </div>
        <div className="setup-review-watch-row">
          <span className="setup-review-watch-key">Cadence</span>
          <span>{cadenceLabel(spec.trigger)}</span>
        </div>
        <div className="setup-review-watch-row">
          <span className="setup-review-watch-key">Action</span>
          <span>{ACTION_LABELS[spec.action.kind] ?? spec.action.kind}</span>
        </div>
        <div className="setup-review-watch-row">
          <span className="setup-review-watch-key">Mode</span>
          <span>{spec.mode}</span>
        </div>
      </div>
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

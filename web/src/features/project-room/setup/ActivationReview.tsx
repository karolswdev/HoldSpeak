// HS-159-05 -- activation review (ACT-001/WEB-CR-011): consequence headline,
// outcome, each Watch spec with ledger-aligned label/value rows, posture token,
// plain-words conditions, cadence, action, framed test evidence, first-run
// behavior, step indicator, pinned SurfaceFooter for activate/back verbs.
// Cmd/Ctrl+Enter activates (WEB-CMD-005).

import { useCallback, useEffect, type KeyboardEvent } from "react";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import { EgressChip } from "../../../desk/surface";
import {
  cadenceLabel,
  conditionPlainWords,
  inferProjectName,
  modeLabel,
  ACTION_LABELS,
  STAGE_META,
  STAGE_COUNT,
  type SetupAnswer,
  type SetupProposal,
} from "./model";

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

  // Derive the project name the same way the server does (read-only; no wire override)
  const projectName = inferProjectName(outcomeAnswer.answer.normalized);
  const testedCount = passed.length;

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

      {/* Consequence headline -- the anchor: says what activation MEANS */}
      <h3
        className="setup-review-headline"
        data-testid="review-headline"
      >
        This creates {"“"}{projectName}{"”"} with{" "}
        {testedCount} tested {testedCount === 1 ? "Watch" : "Watches"}
      </h3>

      {/* Outcome */}
      <div className="setup-review-section" data-testid="review-outcome">
        <div className="setup-review-label">Outcome</div>
        <div className="setup-review-value">
          {outcomeAnswer.answer.normalized}
        </div>
      </div>

      {/* What to notice (was "Signals" -- speaks the question's words) */}
      <div className="setup-review-section" data-testid="review-signals" data-section="signals">
        <div className="setup-review-label">What to notice</div>
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

      {/* Pinned footer -- primary verb in frame, always (fix 3) */}
      <SurfaceFooter
        verbs={
          <>
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
          </>
        }
      />
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

      {/* Egress badge for GitHub watches (HS-161-05) */}
      {proposal.providerId === "github" ? (
        <EgressChip
          label="local + cloud"
          scope="mixed"
          title="This Watch reads from github.com."
        />
      ) : null}

      {/* Framed test evidence (fix 5): compact bordered inset block */}
      {proposal.testResult ? (
        <ReviewTestEvidence
          result={proposal.testResult}
          testState={proposal.testState ?? ""}
        />
      ) : (
        <div className="setup-review-watch-untested">Not tested</div>
      )}
    </div>
  );
}

/** Framed test evidence block: pass token, count, sample entities, observed time
 *  as ONE compact object (not four floating lines). */
function ReviewTestEvidence({
  result,
  testState,
}: {
  result: import("./model").TestResult;
  testState: string;
}) {
  const isPassed = testState === "passed";
  const isFailed = testState === "failed";

  return (
    <div
      className="setup-review-evidence"
      data-test-state={testState}
      data-testid="review-test-evidence"
    >
      {/* Pass/fail token + count on one line */}
      <div className="setup-review-evidence-header">
        <span className="setup-review-evidence-icon" aria-hidden="true">
          {isPassed ? "✓" : isFailed ? "✗" : "…"}
        </span>
        <span className="setup-review-evidence-status">
          {isPassed ? "Test passed" : isFailed ? "Test failed" : "Testing"}
        </span>
        <span className="setup-review-evidence-count">
          {result.entityCount} current {result.entityCount === 1 ? "match" : "matches"}
        </span>
      </div>

      {/* Sample entities as a tight list */}
      {result.representativeEntities.length > 0 ? (
        <ul className="setup-review-evidence-entities">
          {result.representativeEntities.slice(0, 5).map((entity, i) => (
            <li key={i} className="setup-review-evidence-entity">
              {entityLabel(entity)}
            </li>
          ))}
        </ul>
      ) : null}

      {/* Observed time as meta */}
      <div className="setup-review-evidence-time">
        Observed at {formatTime(result.observedAt)}
      </div>

      {/* Error detail */}
      {result.error ? (
        <div className="setup-review-evidence-error">
          {result.error.type}: {result.error.message}
        </div>
      ) : null}
    </div>
  );
}

/** Label for a normalized entity (reaction_service._normalize_entity).
 *  PR entities: id=PR number, title, state. Native: title/text/name. */
function entityLabel(entity: Record<string, unknown>): string {
  // HS-166-04: prefer key (KAN-3) over numeric id for Jira entities
  const key = entity.key != null && String(entity.key) !== ""
    ? String(entity.key)
    : null;
  const id = entity.id != null ? String(entity.id) : "";
  const title = entity.title != null && String(entity.title) !== ""
    ? String(entity.title)
    : (entity.summary != null && String(entity.summary) !== ""
      ? String(entity.summary)
      : (entity.text != null ? String(entity.text) : (entity.name != null ? String(entity.name) : null)));
  const lead = key ?? (id ? `#${id}` : "");
  if (title) {
    return lead ? `${lead} ${title}` : title;
  }
  return lead || "Unknown";
}

function formatTime(iso: string): string {
  if (!iso) return "unknown";
  try {
    return new Date(iso).toLocaleTimeString();
  } catch {
    return iso;
  }
}

// HS-159-05 -- the live brief: outcome, watches by state --
// mentioned/proposed/tested/disabled/active per INT-011.
// Compact rows: name anchor + cadence chip + action in plain words.
// State grouping headers with count chips (the 158 grammar).

import {
  cadenceLabel,
  proposalBriefState,
  ACTION_LABELS,
  type SetupAnswer,
  type SetupProposal,
  type WatchBriefState,
} from "./model";
import type { ControllerState } from "./useSetupController";

const BRIEF_STATE_LABEL: Record<WatchBriefState, string> = {
  mentioned: "Mentioned",
  proposed: "Proposed",
  tested: "Tested",
  disabled: "Disabled",
  active: "Active",
};

export function SetupBrief({ state }: { state: ControllerState }) {
  return (
    <aside className="setup-brief" aria-label="Project brief" data-testid="setup-brief">
      <h3 className="setup-brief-heading">Project brief</h3>

      {/* Outcome */}
      <BriefOutcome state={state} />

      {/* Watch summary */}
      <BriefWatches state={state} />
    </aside>
  );
}

function BriefOutcome({ state }: { state: ControllerState }) {
  let outcomeText = "";

  if (state.kind === "outcome") {
    outcomeText = state.draft;
  } else if (state.kind === "signals") {
    outcomeText = state.outcomeAnswer.answer.normalized;
  } else if (state.kind === "proposals" || state.kind === "review") {
    outcomeText = state.outcomeAnswer.answer.normalized;
  }

  if (!outcomeText) {
    return (
      <div className="setup-brief-section" data-testid="brief-outcome">
        <div className="setup-brief-label">Outcome</div>
        <div className="setup-brief-empty">Not yet defined</div>
      </div>
    );
  }

  return (
    <div className="setup-brief-section" data-testid="brief-outcome">
      <div className="setup-brief-label">Outcome</div>
      <div className="setup-brief-value">{outcomeText}</div>
    </div>
  );
}

function BriefWatches({ state }: { state: ControllerState }) {
  let proposals: SetupProposal[] = [];
  let signalsText = "";

  if (state.kind === "signals") {
    signalsText = state.draft;
  }
  if (state.kind === "proposals") {
    proposals = state.proposals;
    signalsText = state.signalsAnswer.answer.normalized;
  }
  if (state.kind === "review") {
    proposals = state.proposals;
    signalsText = state.signalsAnswer.answer.normalized;
  }

  if (proposals.length === 0 && !signalsText) {
    return null;
  }

  // Group proposals by brief state (INT-011)
  const grouped: Record<WatchBriefState, SetupProposal[]> = {
    mentioned: [],
    proposed: [],
    tested: [],
    disabled: [],
    active: [],
  };

  for (const p of proposals) {
    const bs = proposalBriefState(p);
    grouped[bs].push(p);
  }

  const stateOrder: WatchBriefState[] = [
    "active",
    "tested",
    "proposed",
    "mentioned",
    "disabled",
  ];

  return (
    <div className="setup-brief-section" data-testid="brief-watches">
      <div className="setup-brief-label">Watches</div>

      {signalsText && proposals.length === 0 ? (
        <div className="setup-brief-signals">{signalsText}</div>
      ) : null}

      {stateOrder.map((bs) =>
        grouped[bs].length > 0 ? (
          <div key={bs} className="setup-brief-group" data-brief-state={bs}>
            <div className="setup-brief-group-header">
              <span className="setup-brief-group-label">
                {BRIEF_STATE_LABEL[bs]}
              </span>
              <span className="setup-brief-count-chip" data-testid={`brief-count-${bs}`}>
                {grouped[bs].length}
              </span>
            </div>
            {grouped[bs].map((p) => (
              <BriefWatchRow key={p.id} proposal={p} />
            ))}
          </div>
        ) : null,
      )}
    </div>
  );
}

function BriefWatchRow({ proposal }: { proposal: SetupProposal }) {
  const spec = proposal.spec;
  return (
    <div className="setup-brief-watch" data-testid={`brief-watch-${proposal.id}`}>
      <div className="setup-brief-watch-name">{spec.name}</div>
      <div className="setup-brief-watch-meta">
        <span className="setup-brief-watch-chip">{cadenceLabel(spec.trigger)}</span>
        <span className="setup-brief-watch-action">
          {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
        </span>
      </div>
      {proposal.testResult ? (
        <div
          className="setup-brief-watch-test"
          data-test-state={proposal.testState}
        >
          {proposal.testResult.message}
        </div>
      ) : null}
    </div>
  );
}

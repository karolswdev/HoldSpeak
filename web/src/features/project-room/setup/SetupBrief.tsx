// HS-167-04 — the brief recomposed: SurfaceFacts for OUTCOME/NOTICE/SOURCES,
// watch summary with state groups and count chips.

import {
  SurfaceFacts,
  SurfaceSection,
} from "../../../desk/surface/Surface";
import {
  cadenceLabel,
  proposalBriefState,
  ACTION_LABELS,
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
  let outcomeText = "";
  let signalsText = "";
  let proposals: SetupProposal[] = [];

  if (state.kind === "outcome") {
    outcomeText = state.draft;
  } else if (state.kind === "signals") {
    outcomeText = state.outcomeAnswer.answer.normalized;
    signalsText = state.draft;
  } else if (state.kind === "proposals" || state.kind === "review") {
    outcomeText = state.outcomeAnswer.answer.normalized;
    signalsText = state.signalsAnswer.answer.normalized;
    proposals = state.proposals;
  }

  const facts: Record<string, string> = {};
  if (outcomeText) facts.OUTCOME = outcomeText;
  if (signalsText) facts.NOTICE = signalsText;

  return (
    <aside aria-label="Project brief" data-testid="setup-brief">
      <SurfaceSection label="THE BRIEF">
        <div data-testid="brief-outcome">
          {Object.keys(facts).length > 0 ? (
            <SurfaceFacts value={facts} />
          ) : (
            <span className="surface-fact-empty">Not yet defined</span>
          )}
        </div>
      </SurfaceSection>

      {(proposals.length > 0 || (signalsText && proposals.length === 0)) ? (
        <BriefWatches proposals={proposals} signalsText={signalsText} />
      ) : null}
    </aside>
  );
}

function BriefWatches({ proposals, signalsText }: { proposals: SetupProposal[]; signalsText: string }) {
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
    <div data-testid="brief-watches">
      {signalsText && proposals.length === 0 ? (
        <div className="setup-brief-signals-text">{signalsText}</div>
      ) : null}

      {stateOrder.map((bs) =>
        grouped[bs].length > 0 ? (
          <div key={bs} data-brief-state={bs}>
            <div className="setup-brief-state-row">
              <span>{BRIEF_STATE_LABEL[bs]}</span>
              <span className="surface-token" data-testid={`brief-count-${bs}`}>
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
    <div data-testid={`brief-watch-${proposal.id}`} className="setup-brief-watch-entry">
      <div className="setup-brief-watch-name">{spec.name}</div>
      <div className="setup-brief-watch-meta">
        <span className="setup-brief-watch-chip">{cadenceLabel(spec.trigger)}</span>
        <span className="setup-brief-watch-action">
          {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
        </span>
      </div>
      {proposal.testResult ? (
        <div data-test-state={proposal.testState}>
          {proposal.testResult.message}
        </div>
      ) : null}
    </div>
  );
}

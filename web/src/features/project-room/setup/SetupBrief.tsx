// HS-167-05 — the brief recomposed: SurfaceFacts for OUTCOME/NOTICE/SOURCES,
// proposed watches as a SurfaceLedger cols="room" with provider emblems,
// cadence tokens, action chips, and ProvenanceChips.

import {
  SurfaceFacts,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  ProvenanceChip,
  StateChip,
  CheckGadget,
  type ChipState,
} from "../../../desk/surface";
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

const BRIEF_STATE_CHIP: Record<WatchBriefState, ChipState> = {
  mentioned: "idle",
  proposed: "active",
  tested: "success",
  disabled: "unreachable",
  active: "success",
};

/** Provider emblem glyph. */
const PROVIDER_EMBLEM: Record<string, string> = {
  github: "◉",
  jira: "◆",
  meeting: "▶",
  local: "⌁",
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
            <SurfaceSection label={`${BRIEF_STATE_LABEL[bs]} ${grouped[bs].length}`}>
              <span data-testid={`brief-count-${bs}`} hidden aria-hidden="true">
                {grouped[bs].length}
              </span>
              <SurfaceLedger count={`${BRIEF_STATE_LABEL[bs].toUpperCase()} ${grouped[bs].length}`} cols="room">
                <ul className="surface-ledger-rows">
                  {grouped[bs].map((p) => (
                    <BriefWatchRow key={p.id} proposal={p} briefState={bs} />
                  ))}
                </ul>
              </SurfaceLedger>
            </SurfaceSection>
          </div>
        ) : null,
      )}
    </div>
  );
}

function BriefWatchRow({ proposal, briefState }: { proposal: SetupProposal; briefState: WatchBriefState }) {
  const spec = proposal.spec;
  const emblem = PROVIDER_EMBLEM[proposal.providerId] ?? "◉";

  return (
    <SurfaceLedgerRow
      data-testid={`brief-watch-${proposal.id}`}
      expands={false}
      wrap
      lead={
        <span className="setup-brief-watch-emblem" aria-hidden="true">
          {emblem}
        </span>
      }
      primary={
        <span className="setup-brief-watch-name">{spec.name}</span>
      }
      cells={
        <>
          <span className="surface-token setup-brief-watch-chip" data-chip>
            {cadenceLabel(spec.trigger)}
          </span>
          <span className="surface-token setup-brief-watch-action" data-chip>
            {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
          </span>
          {proposal.providerId ? (
            <ProvenanceChip source={proposal.providerId} />
          ) : null}
        </>
      }
      trailing={
        <StateChip state={BRIEF_STATE_CHIP[briefState]} label={BRIEF_STATE_LABEL[briefState]} />
      }
    />
  );
}

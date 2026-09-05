// PARKED (HS-170-02): retired by Phase 169; kept for reference, not built or scanned.
// HS-167-05 -- the brief recomposed: SurfaceFacts for OUTCOME/NOTICE/TOOLS/SOURCES,
// proposed watches as a SurfaceLedger cols="room" with provider emblems,
// cadence tokens, action chips, and ProvenanceChips.
// HS-168-04: TOOLS fact row (GitHub . Connected, Jira . Sign in);
// one section label per state group (the duplicate "PROPOSED N" retired).

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
import type { ConnectionTool } from "../../../pages/cores/connections/api";
import { connectionChipLabel } from "../../../pages/cores/connections";
import type { ConnectionState } from "../../../pages/cores/connections/api";

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
  github: "GH",
  jira: "J",
  native: "◉",
  meeting: "◉",
  local: "◉",
};

/** Tool state label for the brief — ONE vocabulary with Settings → Connections (counsel S-1). */
function toolBriefLabel(state: string, providerId: string): string {
  return connectionChipLabel(state as ConnectionState, providerId);
}

/** Tool provider display name. */
function toolDisplayName(providerId: string): string {
  if (providerId === "github") return "GitHub";
  if (providerId === "jira") return "Jira";
  return providerId;
}

export function SetupBrief({
  state,
  connectionTools,
}: {
  state: ControllerState;
  connectionTools?: ConnectionTool[];
}) {
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

  // HS-168-04: TOOLS fact row -- only connector-pack providers
  const connectorTools = (connectionTools ?? []).filter(
    (t) => t.provider_id === "github" || t.provider_id === "jira",
  );

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

      {/* HS-168-04: TOOLS fact row */}
      {connectorTools.length > 0 ? (
        <SurfaceSection label="TOOLS">
          <div className="setup-brief-tools" data-testid="brief-tools">
            {connectorTools.map((tool) => {
              const name = toolDisplayName(tool.provider_id);
              const stateLabel = toolBriefLabel(tool.state, tool.provider_id);
              const isWarning = tool.state !== "connected";
              return (
                <div key={tool.provider_id} className="setup-brief-tool-line" data-state={tool.state}>
                  <span>{name}</span>
                  <span className="setup-brief-tool-sep">{" · "}</span>
                  <span className={isWarning ? "setup-brief-tool-warn" : ""}>{stateLabel}</span>
                </div>
              );
            })}
          </div>
        </SurfaceSection>
      ) : null}

      {(proposals.length > 0 || (signalsText && proposals.length === 0)) ? (
        <BriefWatches proposals={proposals} signalsText={signalsText} />
      ) : null}
    </aside>
  );
}

function BriefWatches({ proposals, signalsText }: { proposals: SetupProposal[]; signalsText: string }) {
  // HS-168-05: brief shows only chosen sources (selected or tested).
  // Unselected proposals live on the cards, not in the brief.
  const chosen = proposals.filter((p) => p.state === "selected" || p.testState === "passed");

  return (
    <div data-testid="brief-watches">
      {signalsText && proposals.length === 0 ? (
        <div className="setup-brief-signals-text">{signalsText}</div>
      ) : null}

      <SurfaceSection label={`SOURCES ${chosen.length}`}>
        <span data-testid="brief-sources-count" hidden aria-hidden="true">
          {chosen.length}
        </span>
        {chosen.length > 0 ? (
          <SurfaceLedger cols="room">
            <ul className="surface-ledger-rows">
              {chosen.map((p) => (
                <BriefWatchRow key={p.id} proposal={p} briefState={proposalBriefState(p)} />
              ))}
            </ul>
          </SurfaceLedger>
        ) : (
          <span className="surface-token setup-brief-none" data-chip>NONE YET</span>
        )}
      </SurfaceSection>
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

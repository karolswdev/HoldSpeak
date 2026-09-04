// HS-159-05 -- suggestion cards consume ChoiceCardShell from the surface
// library barrel. The shell owns the card visual language (HS-156-08);
// this feature adds the multi-select listbox interaction model on top
// (div[role="option"], aria-selected, Space toggle, roving focus).
// HS-168-04: provider StateChip from proposal.connection; disconnected
// cards have NO tier and their click lights the TOOLS connect card
// (never a wizard). Connected provider cards sort before native ones
// (the wire's order stays).
//
// Glass selectors preserved: setup-suggestion-cards (testid),
// [role="option"], .setup-card-rationale, .setup-card-test-btn,
// .setup-card-test.

import { useCallback, useRef } from "react";
import {
  ChoiceCardShell,
  Disclosure,
  EgressChip,
  StateChip,
  ProvenanceChip,
  useRovingRows,
} from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import {
  cadenceLabel,
  conditionPlainWords,
  proposalBriefState,
  modeLabel,
  ACTION_LABELS,
  type SetupProposal,
  type WatchBriefState,
} from "./model";
import { connectionChipLabel } from "../../../pages/cores/connections";
import type { ConnectionState } from "../../../pages/cores/connections/api";

const STATE_LABEL: Record<WatchBriefState, string> = {
  mentioned: "Mentioned",
  proposed: "Ready to select",
  tested: "Tested",
  disabled: "Disabled",
  active: "Active",
};

/** Provider-specific StateChip from proposal.connection (HS-168-04).
 *  ONE label vocabulary with Settings → Connections (counsel S-1). */
function connectionStateChip(proposal: SetupProposal): { state: "success" | "warning" | "failure" | "idle" | "unreachable"; label: string } | null {
  const conn = proposal.connection;
  if (!conn) return null;
  const label = connectionChipLabel(conn.state as ConnectionState, proposal.providerId);
  switch (conn.state) {
    case "connected": return { state: "success", label };
    case "owner_action_required": return { state: "warning", label };
    case "unavailable": return { state: "failure", label };
    case "degraded": return { state: "unreachable", label };
    case "not_configured": return { state: "idle", label };
    default: return null;
  }
}

/** Provenance chip source from provider id. */
function provenanceSource(providerId: string): { source: string; boundary: string } | null {
  if (providerId === "github") return { source: "gh", boundary: "github.com" };
  if (providerId === "jira") return { source: "acli", boundary: "" };
  return null;
}

/** Test result chip label: "Tested . N matches". */
function testedLabel(proposal: SetupProposal): string {
  if (proposal.testState !== "passed") return "";
  const count = proposal.testResult?.entityCount ?? 0;
  return `Tested · ${count} ${count === 1 ? "match" : "matches"}`;
}

export function SuggestionCards({
  proposals,
  onSelect,
  onDeselect,
  onTest,
  suggesting,
}: {
  proposals: SetupProposal[];
  onSelect: (id: string) => void;
  onDeselect: (id: string) => void;
  onTest: (id: string) => void;
  suggesting: boolean;
}) {
  const listRef = useRef<HTMLDivElement>(null);
  useRovingRows(listRef, { selector: '[role="option"]' });

  if (suggesting) {
    return (
      <div className="setup-cards" aria-live="polite" role="status">
        <div className="setup-cards-loading">Generating suggestions...</div>
      </div>
    );
  }

  if (proposals.length === 0) {
    return (
      <div className="setup-cards" data-testid="setup-blank-path">
        <div className="setup-cards-blank" aria-live="polite">
          No Watch suggestions available. You can create a blank Project and add Watches later.
        </div>
      </div>
    );
  }

  return (
    <div
      ref={listRef}
      className="setup-cards"
      role="listbox"
      aria-label="Watch suggestions"
      aria-live="polite"
      data-testid="setup-suggestion-cards"
    >
      <div className="sr-only" role="status">
        {proposals.length} suggestion{proposals.length !== 1 ? "s" : ""} available
      </div>
      {proposals.map((p) => (
        <SuggestionCard
          key={p.id}
          proposal={p}
          onSelect={onSelect}
          onDeselect={onDeselect}
          onTest={onTest}
        />
      ))}
    </div>
  );
}

function SuggestionCard({
  proposal,
  onSelect,
  onDeselect,
  onTest,
}: {
  proposal: SetupProposal;
  onSelect: (id: string) => void;
  onDeselect: (id: string) => void;
  onTest: (id: string) => void;
}) {
  const isSelected = proposal.state === "selected";
  const briefState = proposalBriefState(proposal);
  const spec = proposal.spec;
  const connChip = connectionStateChip(proposal);
  const isDisconnected = connChip && connChip.state !== "success" && (proposal.providerId === "github" || proposal.providerId === "jira");
  const prov = provenanceSource(proposal.providerId);

  // HS-168-04: disconnected provider card = no tier
  const cardTier = isDisconnected ? undefined : (isSelected ? "ok" : undefined);

  const handleToggle = useCallback(() => {
    if (isSelected) onDeselect(proposal.id);
    else onSelect(proposal.id);
  }, [isSelected, proposal.id, onSelect, onDeselect]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      // Space toggles selection (WEB-CMD-005)
      if (e.key === " ") {
        e.preventDefault();
        handleToggle();
      }
    },
    [handleToggle],
  );

  // HS-168-04: tested state chip
  const tested = testedLabel(proposal);

  return (
    <ChoiceCardShell
      label={spec.name}
      emblem={proposal.providerId === "github" ? "GH" : proposal.providerId === "jira" ? "J" : proposal.providerId === "meeting" ? "◎" : undefined}
      tier={cardTier}
      selected={isSelected}
      role="option"
      aria-selected={isSelected}
      data-testid={`setup-card-${proposal.id}`}
      data-state={briefState}
      data-disconnected={isDisconnected || undefined}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleToggle}
    >
      {/* Chip row: cadence + action + provenance + connection state */}
      <div className="setup-card-chips">
        <span className="surface-token" data-chip>
          CADENCE {cadenceLabel(spec.trigger)}
        </span>
        <span className="surface-token" data-chip>
          ACTION {ACTION_LABELS[spec.action.kind] ? modeLabel(spec.action.kind).toLowerCase() : spec.action.kind}
        </span>
        {prov ? (
          <ProvenanceChip
            source={prov.source}
            boundary={proposal.providerId === "jira"
              ? String(spec.subject.scope?.connection_ref ?? "").split("|")[0] || prov.boundary
              : prov.boundary}
          />
        ) : (
          <ProvenanceChip source="local" />
        )}
        {/* HS-168-04: provider connection StateChip */}
        {connChip ? (
          <StateChip state={connChip.state} label={connChip.label} />
        ) : null}
        {/* HS-168-04: tested state chip */}
        {tested ? (
          <StateChip state="success" label={tested} />
        ) : null}
      </div>

      {/* Rationale: as facts/Disclosure instead of sentences (D7b) */}
      {proposal.rationale.fact ? (
        <Disclosure label="Rationale">
          <div className="setup-card-rationale">
            {proposal.rationale.fact}
            {proposal.rationale.detail ? ` -- ${proposal.rationale.detail}` : ""}
          </div>
        </Disclosure>
      ) : null}

      {/* Test state */}
      {proposal.testState && proposal.testState !== "passed" ? (
        <div className="setup-card-test" data-test-state={proposal.testState}>
          {proposal.testResult?.message ?? `Test: ${proposal.testState}`}
        </div>
      ) : null}

      {/* Test button (only for selected proposals without test state) */}
      {isSelected && !proposal.testState ? (
        <Button
          dense
          variant="ghost"
          className="setup-card-test-btn"
          onClick={(e: React.MouseEvent) => {
            e.stopPropagation();
            onTest(proposal.id);
          }}
          aria-label={`Test: ${spec.name}`}
        >
          Test
        </Button>
      ) : null}
    </ChoiceCardShell>
  );
}

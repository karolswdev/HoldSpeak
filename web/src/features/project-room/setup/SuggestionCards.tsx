// HS-159-05 -- suggestion cards as OBJECTS (INT-008): source chip,
// subject, plain-words conditions, cadence, readiness, rationale.
// Cards are labeled CONTROLS, not clickable prose (WEB-A11Y-008).
// Space toggles selection, arrows traverse (WEB-CMD-005).

import { useCallback, useRef } from "react";
import { useRovingRows } from "../../../desk/surface/roving";
import {
  cadenceLabel,
  conditionSummary,
  proposalBriefState,
  ACTION_LABELS,
  type SetupProposal,
  type WatchBriefState,
} from "./model";

const STATE_LABEL: Record<WatchBriefState, string> = {
  mentioned: "Mentioned",
  proposed: "Ready to select",
  tested: "Tested",
  disabled: "Disabled",
  active: "Active",
};

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

  return (
    <div
      className="setup-card"
      role="option"
      aria-selected={isSelected}
      data-testid={`setup-card-${proposal.id}`}
      data-state={briefState}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleToggle}
    >
      {/* Source chip */}
      <div className="setup-card-source">
        <span className="setup-card-chip">{proposal.providerId}</span>
        <span className="setup-card-readiness" data-state={briefState}>
          {STATE_LABEL[briefState]}
        </span>
      </div>

      {/* Subject */}
      <div className="setup-card-name">{spec.name}</div>

      {/* Intent / subject kind */}
      <div className="setup-card-subject">
        <span className="setup-card-subject-kind">{spec.subject.kind}</span>
      </div>

      {/* Plain-words conditions */}
      <div className="setup-card-conditions">{conditionSummary(spec)}</div>

      {/* Action */}
      <div className="setup-card-action">
        {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
      </div>

      {/* Cadence */}
      <div className="setup-card-cadence">{cadenceLabel(spec.trigger)}</div>

      {/* Rationale */}
      <div className="setup-card-rationale">
        {proposal.rationale.fact}
        {proposal.rationale.detail ? ` -- ${proposal.rationale.detail}` : ""}
      </div>

      {/* Test state */}
      {proposal.testState ? (
        <div className="setup-card-test" data-test-state={proposal.testState}>
          {proposal.testResult?.message ?? `Test: ${proposal.testState}`}
        </div>
      ) : null}

      {/* Test button (only for selected proposals) */}
      {isSelected && !proposal.testState ? (
        <button
          type="button"
          className="setup-card-test-btn"
          onClick={(e) => {
            e.stopPropagation();
            onTest(proposal.id);
          }}
          aria-label={`Test: ${spec.name}`}
        >
          Test
        </button>
      ) : null}
    </div>
  );
}

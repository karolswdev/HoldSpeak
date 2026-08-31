// HS-159-05 -- suggestion cards ARE ChoiceCards: the surface library's
// card visual language (HS-156-08) carries each proposal object.
//
// Semantic reconciliation: ChoiceCardGroup imposes radiogroup (single-
// select). Setup suggestions are multi-select (listbox/option, Space
// toggles). So we use the ChoiceCard CSS classes on div[role="option"]
// directly — the visual language without the radio interaction model.
// data-selected stamps the library's accent-wash selection presence;
// aria-selected preserves the a11y contract.
//
// Glass selectors preserved: setup-suggestion-cards (testid),
// [role="option"], .setup-card-rationale, .setup-card-test-btn,
// .setup-card-test.

import { useCallback, useRef } from "react";
import { useRovingRows } from "../../../desk/surface/roving";
import { Disclosure } from "../../../desk/surface/patterns/Disclosure";
import "../../../desk/surface/patterns/choice-card.css";
import {
  cadenceLabel,
  conditionPlainWords,
  proposalBriefState,
  modeLabel,
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
      className="surface-choice-card"
      role="option"
      aria-selected={isSelected}
      data-testid={`setup-card-${proposal.id}`}
      data-state={briefState}
      data-selected={isSelected || undefined}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleToggle}
    >
      {/* Head: name anchor */}
      <div className="surface-choice-card-head">
        <span className="surface-choice-card-label">{spec.name}</span>
      </div>

      {/* Summary: plain-words condition — the one-line anchor (156-08 law) */}
      <div
        className="surface-choice-card-summary"
        data-condition-raw={spec.rules.flatMap((r) =>
          r.condition.clauses.map((c) => `${c.field}:${c.comparison}${c.value != null ? `:${c.value}` : ""}`),
        ).join(",")}
      >
        {conditionPlainWords(spec)}
      </div>

      {/* Facts: chips in the library's fact-chip layout */}
      <div className="surface-choice-card-facts">
        <div className="surface-choice-card-fact" data-chip="source">
          <span className="surface-choice-card-fact-key">source</span>
          <span className="surface-choice-card-fact-val">{proposal.providerId}</span>
        </div>
        <div className="surface-choice-card-fact" data-chip="subject">
          <span className="surface-choice-card-fact-key">subject</span>
          <span className="surface-choice-card-fact-val">{spec.subject.kind}</span>
        </div>
        <div className="surface-choice-card-fact" data-chip="cadence">
          <span className="surface-choice-card-fact-key">cadence</span>
          <span className="surface-choice-card-fact-val">{cadenceLabel(spec.trigger)}</span>
        </div>
        <div className="surface-choice-card-fact" data-chip="mode" data-mode={spec.mode}>
          <span className="surface-choice-card-fact-key">mode</span>
          <span className="surface-choice-card-fact-val">{modeLabel(spec.mode)}</span>
        </div>
      </div>

      {/* Readiness state token (custom — no ChoiceCard slot for this) */}
      <span className="setup-card-readiness" data-state={briefState}>
        {STATE_LABEL[briefState]}
      </span>

      {/* Rationale: visible footer — glass test asserts is_visible */}
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

      {/* Test button (only for selected proposals without test state) */}
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

      {/* Fold: action detail behind a Disclosure (ChoiceCard fold pattern) */}
      <div
        className="surface-choice-card-fold"
        onClick={(e) => e.stopPropagation()}
      >
        <Disclosure label="Action" defaultOpen={false}>
          <div className="setup-card-action-detail">
            {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
          </div>
        </Disclosure>
      </div>
    </div>
  );
}

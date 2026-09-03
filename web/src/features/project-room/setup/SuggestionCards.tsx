// HS-159-05 -- suggestion cards consume ChoiceCardShell from the surface
// library barrel. The shell owns the card visual language (HS-156-08);
// this feature adds the multi-select listbox interaction model on top
// (div[role="option"], aria-selected, Space toggle, roving focus).
//
// Glass selectors preserved: setup-suggestion-cards (testid),
// [role="option"], .setup-card-rationale, .setup-card-test-btn,
// .setup-card-test.

import { useCallback, useRef } from "react";
import {
  ChoiceCardShell,
  Disclosure,
  EgressChip,
  useRovingRows,
} from "../../../desk/surface";
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
    <ChoiceCardShell
      label={spec.name}
      summary={
        <span
          data-condition-raw={spec.rules.flatMap((r) =>
            r.condition.clauses.map((c) => `${c.field}:${c.comparison}${c.value != null ? `:${c.value}` : ""}`),
          ).join(",")}
        >
          {conditionPlainWords(spec)}
        </span>
      }
      facts={[
        { label: "source", value: proposal.providerId },
        { label: "subject", value: spec.subject.kind },
        { label: "cadence", value: cadenceLabel(spec.trigger) },
        { label: "mode", value: modeLabel(spec.mode) },
      ]}
      fold={
        <div className="setup-card-action-detail">
          {ACTION_LABELS[spec.action.kind] ?? spec.action.kind}
        </div>
      }
      foldLabel="Action"
      selected={isSelected}
      onFoldClick={(e) => e.stopPropagation()}
      role="option"
      aria-selected={isSelected}
      data-testid={`setup-card-${proposal.id}`}
      data-state={briefState}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      onClick={handleToggle}
    >
      {/* Readiness state token (custom -- no ChoiceCard slot for this) */}
      <span className="setup-card-readiness" data-state={briefState}>
        {STATE_LABEL[briefState]}
      </span>

      {/* Rationale: visible footer -- glass test asserts is_visible */}
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

      {/* Egress badge for provider cards (HS-161-05 + HS-166-04) */}
      {proposal.providerId === "github" ? (
        <EgressChip
          label="local + cloud"
          scope="mixed"
          title="This Watch reads from github.com."
        />
      ) : null}
      {proposal.providerId === "jira" ? (
        <EgressChip
          label="local + cloud"
          scope="mixed"
          title={`This Watch reads from ${spec.subject.scope?.connection_ref
            ? String(spec.subject.scope.connection_ref).split("|")[0]
            : "Jira"}.`}
        />
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
    </ChoiceCardShell>
  );
}

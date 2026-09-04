// HS-159-05 -- SetupInterview component tests: two questions (INT-003),
// keyboard behaviors (WEB-CMD-005), voice-never-submits (WEB-CMD-006),
// card object slots (INT-008), brief state mirroring, Blank path.

import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

/* ── Mock SurfaceFooter (renders inline in test env) ── */
vi.mock("../../../../desk/surface/SurfaceFooter", () => ({
  SurfaceFooter: ({
    egress,
    receipt,
    verbs,
  }: {
    egress?: React.ReactNode;
    receipt?: React.ReactNode;
    verbs?: React.ReactNode;
  }) => (
    <footer data-testid="surface-footer">
      {egress}
      {receipt}
      {verbs}
    </footer>
  ),
}));

/* ── Mock MicButton (voice fills, never submits) ── */
vi.mock("../../../../desk/surface/controls/MicButton", () => ({
  MicButton: ({
    onText,
    label,
  }: {
    onText: (text: string) => void;
    label?: string;
  }) => (
    <button
      data-testid="mic-btn"
      aria-label={label}
      onClick={() => onText("voice input")}
    >
      Mic
    </button>
  ),
}));

import { SetupInterview } from "../SetupInterview";
import { SuggestionCards } from "../SuggestionCards";
import { SetupBrief } from "../SetupBrief";
import { ActivationReview } from "../ActivationReview";
import type { ControllerState } from "../useSetupController";
import {
  conditionPlainWords,
  inferProjectName,
  modeLabel,
  STAGE_META,
  STAGE_COUNT,
  type SetupAnswer,
  type SetupProposal,
  type WatchSpec,
} from "../model";

/* ── Helpers ── */

function makeAnswer(questionId: string, text: string): SetupAnswer {
  return {
    id: `pans_${questionId}`,
    sessionId: "psetup_test",
    questionId,
    answerSchema: "SetupAnswer@1",
    answer: { original: text, normalized: text },
    revision: 1,
    createdAt: "2026-08-31T10:00:00",
  };
}

function makeProposal(id: string, overrides: Partial<SetupProposal> = {}): SetupProposal {
  return {
    id,
    sessionId: "psetup_test",
    providerId: "native",
    specSchema: "WatchSpec@1",
    spec: {
      schema: "WatchSpec@1",
      name: "Meeting activity",
      intent: "Watch meetings",
      provider: { id: "native", transport: "local_domain" },
      subject: { kind: "meetings", scope: { meeting_ids: ["m1"] } },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses: [{ field: "content", comparison: "changed" }],
          },
          actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
        },
      ],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    },
    rationale: { fact: "1 recent meetings", detail: "Sprint planning", subjectCount: 1 },
    state: "proposed",
    testState: null,
    testResult: null,
    createdAt: "2026-08-31T10:00:00",
    updatedAt: "2026-08-31T10:00:00",
    ...overrides,
  };
}

/* ── SetupInterview tests ── */

describe("SetupInterview", () => {
  const noop = () => {};

  it("shows outcome question on outcome stage", () => {
    const state: ControllerState = { kind: "outcome", draft: "" };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={noop}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    expect(screen.getByTestId("setup-question-outcome")).toBeTruthy();
    // HS-167-04: question text is now the placeholder (D2 well species)
    expect(
      screen.getByPlaceholderText("What outcome are you trying to create or protect?"),
    ).toBeTruthy();
  });

  it("shows signals question with collapsed outcome on signals stage", () => {
    const state: ControllerState = {
      kind: "signals",
      draft: "",
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
    };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={noop}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    // Collapsed outcome answer visible
    expect(screen.getByTestId("setup-answer-outcome")).toBeTruthy();
    expect(screen.getByText("Ship Q4")).toBeTruthy();

    // Active signals question
    expect(screen.getByTestId("setup-question-signals")).toBeTruthy();
    // HS-167-04: question text is now the placeholder (D2 well species)
    expect(
      screen.getByPlaceholderText("What would you want HoldSpeak to notice without being asked?"),
    ).toBeTruthy();
  });

  it("shows both collapsed answers on proposals stage", () => {
    const state: ControllerState = {
      kind: "proposals",
      proposals: [],
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
      signalsAnswer: makeAnswer("signals", "PRs stale"),
      suggesting: false,
    };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={noop}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    expect(screen.getByTestId("setup-answer-outcome")).toBeTruthy();
    expect(screen.getByTestId("setup-answer-signals")).toBeTruthy();
    expect(screen.getByText("Ship Q4")).toBeTruthy();
    expect(screen.getByText("PRs stale")).toBeTruthy();
  });

  it("calls onSubmitOutcome on Enter (WEB-CMD-005)", () => {
    const onSubmit = vi.fn();
    const state: ControllerState = { kind: "outcome", draft: "My outcome" };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={onSubmit}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.keyDown(textarea, { key: "Enter" });
    expect(onSubmit).toHaveBeenCalledWith("My outcome");
  });

  it("does NOT submit on Shift+Enter (newline, WEB-CMD-005)", () => {
    const onSubmit = vi.fn();
    const state: ControllerState = { kind: "outcome", draft: "My outcome" };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={onSubmit}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits on Cmd+Enter (WEB-CMD-005)", () => {
    const onSubmit = vi.fn();
    const state: ControllerState = { kind: "outcome", draft: "My outcome" };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={onSubmit}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    const textarea = screen.getByRole("textbox");
    fireEvent.keyDown(textarea, { key: "Enter", metaKey: true });
    expect(onSubmit).toHaveBeenCalledWith("My outcome");
  });

  it("voice fills draft but never submits (WEB-CMD-006)", () => {
    const onSubmit = vi.fn();
    const onDraft = vi.fn();
    const state: ControllerState = { kind: "outcome", draft: "" };
    render(
      <SetupInterview
        state={state}
        error=""
        onSubmitOutcome={onSubmit}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={onDraft}
      />,
    );

    const micBtn = screen.getAllByTestId("mic-btn")[0];
    fireEvent.click(micBtn);
    // Mic calls onText with "voice input" which calls onDraft
    expect(onDraft).toHaveBeenCalledWith("voice input");
    // But onSubmit was never called
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("shows error when error prop is set", () => {
    const state: ControllerState = { kind: "outcome", draft: "" };
    render(
      <SetupInterview
        state={state}
        error="Something went wrong"
        onSubmitOutcome={noop}
        onSubmitSignals={noop}
        onEditOutcome={noop}
        onEditSignals={noop}
        onSetDraft={noop}
      />,
    );

    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText("Something went wrong")).toBeTruthy();
  });
});

/* ── SuggestionCards tests ── */

describe("SuggestionCards", () => {
  const noop = () => {};

  // HS-168-04: card recomposed with chips row + Disclosure rationale
  it("renders suggestion cards with chips row and testid (INT-008)", () => {
    const proposals = [makeProposal("wprop_1")];
    render(
      <SuggestionCards
        proposals={proposals}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    // Card present with correct testid and name label
    expect(screen.getByTestId("setup-card-wprop_1")).toBeTruthy();
    expect(screen.getByText("Meeting activity")).toBeTruthy(); // name anchor (label)
    // Chips row carries cadence + action tokens
    const card = screen.getByTestId("setup-card-wprop_1");
    expect(card.textContent).toContain("CADENCE");
    expect(card.textContent).toContain("local");
    // Rationale in a Disclosure (click to open)
    const disclosureTrigger = card.querySelector(".surface-disclosure-trigger") as HTMLElement;
    if (disclosureTrigger) {
      fireEvent.click(disclosureTrigger);
      expect(screen.getByText(/1 recent meetings/)).toBeTruthy();
    }
  });

  it("renders Blank path when no proposals (INT-002)", () => {
    render(
      <SuggestionCards
        proposals={[]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    expect(screen.getByTestId("setup-blank-path")).toBeTruthy();
  });

  it("shows loading state when suggesting", () => {
    render(
      <SuggestionCards
        proposals={[]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={true}
      />,
    );

    expect(screen.getByText("Generating suggestions...")).toBeTruthy();
  });

  it("Space toggles selection (WEB-CMD-005)", () => {
    const onSelect = vi.fn();
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={onSelect}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    const card = screen.getByTestId("setup-card-wprop_1");
    fireEvent.keyDown(card, { key: " " });
    expect(onSelect).toHaveBeenCalledWith("wprop_1");
  });

  it("Space deselects a selected card", () => {
    const onDeselect = vi.fn();
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1", { state: "selected" })]}
        onSelect={noop}
        onDeselect={onDeselect}
        onTest={noop}
        suggesting={false}
      />,
    );

    const card = screen.getByTestId("setup-card-wprop_1");
    fireEvent.keyDown(card, { key: " " });
    expect(onDeselect).toHaveBeenCalledWith("wprop_1");
  });

  it("cards are labeled as controls (WEB-A11Y-008)", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    expect(screen.getByRole("listbox")).toBeTruthy();
    expect(screen.getByRole("option")).toBeTruthy();
  });

  it("announces proposal count (WEB-A11Y-008)", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1"), makeProposal("wprop_2")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    expect(screen.getByText("2 suggestions available")).toBeTruthy();
  });

  it("shows test result on tested cards", () => {
    const tested = makeProposal("wprop_1", {
      state: "selected",
      testState: "passed",
      testResult: {
        entityCount: 1,
        representativeEntities: [],
        observedAt: "2026-08-31T10:04:00",
        error: null,
        message: "Test passed -- 1 current matches",
      },
    });
    render(
      <SuggestionCards
        proposals={[tested]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );

    // HS-168-04: passed tests show a "Tested . N matches" StateChip
    const card = screen.getByTestId("setup-card-wprop_1");
    expect(card.textContent).toContain("Tested");
    expect(card.textContent).toContain("1 match");
  });
});

/* ── SetupBrief tests ── */

describe("SetupBrief", () => {
  it("shows empty outcome on outcome stage", () => {
    const state: ControllerState = { kind: "outcome", draft: "" };
    render(<SetupBrief state={state} />);

    expect(screen.getByTestId("brief-outcome")).toBeTruthy();
    expect(screen.getByText("Not yet defined")).toBeTruthy();
  });

  it("mirrors outcome draft live", () => {
    const state: ControllerState = { kind: "outcome", draft: "My draft outcome" };
    render(<SetupBrief state={state} />);

    expect(screen.getByText("My draft outcome")).toBeTruthy();
  });

  it("shows outcome answer on signals stage", () => {
    const state: ControllerState = {
      kind: "signals",
      draft: "",
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
    };
    render(<SetupBrief state={state} />);

    expect(screen.getByText("Ship Q4")).toBeTruthy();
  });

  it("distinguishes five watch states in brief (INT-011)", () => {
    const proposals: SetupProposal[] = [
      makeProposal("wprop_proposed", { state: "proposed" }),
      makeProposal("wprop_tested", { state: "selected", testState: "passed" }),
      makeProposal("wprop_disabled", { state: "deselected" }),
    ];
    const state: ControllerState = {
      kind: "proposals",
      proposals,
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
      signalsAnswer: makeAnswer("signals", "PRs stale"),
      suggesting: false,
    };
    render(<SetupBrief state={state} />);

    expect(screen.getByTestId("brief-watches")).toBeTruthy();
    // Should have groups for proposed, tested, disabled
    const groups = screen.getByTestId("brief-watches").querySelectorAll("[data-brief-state]");
    const states = Array.from(groups).map((g) => g.getAttribute("data-brief-state"));
    expect(states).toContain("proposed");
    expect(states).toContain("tested");
    expect(states).toContain("disabled");
  });

  // HS-168-04: brief groups use SurfaceLedger count labels instead of hidden testids
  it("brief groups show count in ledger label (defect 5)", () => {
    const proposals: SetupProposal[] = [
      makeProposal("wprop_1", { state: "proposed" }),
      makeProposal("wprop_2", { state: "proposed" }),
      makeProposal("wprop_3", { state: "selected", testState: "passed" }),
    ];
    const state: ControllerState = {
      kind: "proposals",
      proposals,
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
      signalsAnswer: makeAnswer("signals", "PRs stale"),
      suggesting: false,
    };
    render(<SetupBrief state={state} />);

    // Count shows in ledger count label
    const brief = screen.getByTestId("brief-watches");
    expect(brief.textContent).toContain("PROPOSED 2");
    expect(brief.textContent).toContain("TESTED 1");
  });

  it("brief watch rows show cadence chip and action (defect 5)", () => {
    const proposals: SetupProposal[] = [
      makeProposal("wprop_1", { state: "proposed" }),
    ];
    const state: ControllerState = {
      kind: "proposals",
      proposals,
      outcomeAnswer: makeAnswer("outcome", "Ship Q4"),
      signalsAnswer: makeAnswer("signals", "PRs stale"),
      suggesting: false,
    };
    render(<SetupBrief state={state} />);

    const row = screen.getByTestId("brief-watch-wprop_1");
    // Name anchor present
    expect(row.querySelector(".setup-brief-watch-name")?.textContent).toBe("Meeting activity");
    // Cadence chip
    expect(row.querySelector(".setup-brief-watch-chip")?.textContent).toBe("Every 35 min");
    // Action in plain words
    expect(row.querySelector(".setup-brief-watch-action")?.textContent).toBe("Put it in Project attention");
  });
});

/* ── Plain-words conditions (defect 2) ── */

describe("conditionPlainWords", () => {
  function specWith(comparison: string, field: string, value?: unknown, subjectKind = "meetings"): WatchSpec {
    return {
      schema: "WatchSpec@1",
      name: "test",
      intent: "test",
      provider: { id: "native", transport: "local_domain" },
      subject: { kind: subjectKind },
      trigger: { kind: "poll", everyMinutes: 35 },
      rules: [
        {
          condition: {
            schema: "WatchCondition@1",
            operator: "any",
            clauses: [{ field, comparison, value }],
          },
          actions: [{ schema: "WatchAction@1", kind: "project.observe" }],
        },
      ],
      action: { schema: "WatchAction@1", kind: "project.observe" },
      mode: "yolo",
    };
  }

  it("maps 'changed' to plain words", () => {
    expect(conditionPlainWords(specWith("changed", "content"))).toBe(
      "When content changes",
    );
  });

  it("maps 'changed_to' with value", () => {
    expect(conditionPlainWords(specWith("changed_to", "lifecycle", "accepted", "decisions"))).toBe(
      "When lifecycle becomes accepted",
    );
  });

  it("maps 'equals' with value", () => {
    expect(conditionPlainWords(specWith("equals", "lifecycle", "accepted", "decisions"))).toBe(
      "When lifecycle is accepted",
    );
  });

  it("maps 'older_than' with value", () => {
    expect(conditionPlainWords(specWith("older_than", "due_date", "7d", "action_items"))).toBe(
      "When due_date is older than 7d",
    );
  });

  it("maps 'contains' with value", () => {
    expect(conditionPlainWords(specWith("contains", "tags", "urgent"))).toBe(
      "When tags contains urgent",
    );
  });

  it("maps 'exists'", () => {
    expect(conditionPlainWords(specWith("exists", "assignee"))).toBe(
      "When assignee exists",
    );
  });

  it("returns 'On any change' when no clauses", () => {
    const spec = specWith("changed", "content");
    spec.rules = [];
    expect(conditionPlainWords(spec)).toBe("On any change");
  });

  it("falls back gracefully for unknown comparison", () => {
    const result = conditionPlainWords(specWith("custom_check", "status", "done"));
    // Should not contain raw JSON, should be a readable sentence
    expect(result).toContain("When");
    expect(result).toContain("custom_check");
    expect(result).toContain("done");
  });
});

/* ── Mode label (defect 3) ── */

describe("modeLabel", () => {
  it("maps yolo to YOLO", () => {
    expect(modeLabel("yolo")).toBe("YOLO");
  });

  it("maps safe to Secure", () => {
    expect(modeLabel("safe")).toBe("Secure");
  });

  it("maps neutral to Normal", () => {
    expect(modeLabel("neutral")).toBe("Normal");
  });

  it("falls back to raw value for unknown modes", () => {
    expect(modeLabel("custom")).toBe("custom");
  });
});

/* ── Card object slots (defect 1) ── */

// HS-168-04: SuggestionCards recomposed — chips row, Disclosure rationale,
// ProvenanceChip, no ChoiceCard fact slots.
describe("SuggestionCards structure (HS-168-04)", () => {
  const noop = () => {};

  it("card has name label from ChoiceCardShell", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    const label = card.querySelector(".surface-choice-card-label");
    expect(label?.textContent).toBe("Meeting activity");
  });

  it("card renders as ChoiceCard (surface-choice-card class)", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    expect(card.classList.contains("surface-choice-card")).toBe(true);
  });

  it("chips row has CADENCE and ACTION tokens", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    const chipsRow = card.querySelector(".setup-card-chips");
    expect(chipsRow).toBeTruthy();
    const text = chipsRow!.textContent ?? "";
    expect(text).toContain("CADENCE");
    expect(text).toContain("ACTION");
  });

  it("ProvenanceChip renders with source 'local' for native cards", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    const provSource = card.querySelector(".surface-provenance-source");
    expect(provSource?.textContent).toBe("local");
  });

  it("rationale is inside a Disclosure, not a visible footer", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1")]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    const disclosure = card.querySelector(".surface-disclosure");
    expect(disclosure).toBeTruthy();
    // Open the disclosure to see the rationale
    const trigger = card.querySelector(".surface-disclosure-trigger") as HTMLElement;
    expect(trigger).toBeTruthy();
    fireEvent.click(trigger);
    const rationale = card.querySelector(".setup-card-rationale");
    expect(rationale?.textContent).toContain("1 recent meetings");
  });

  it("selected card shows presence via aria-selected", () => {
    render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1", { state: "selected" })]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    expect(card.getAttribute("aria-selected")).toBe("true");
  });

  it("selection presence via data-selected state toggle", () => {
    const { rerender } = render(
      <SuggestionCards
        proposals={[makeProposal("wprop_1", { state: "proposed" })]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    const card = screen.getByTestId("setup-card-wprop_1");
    expect(card.hasAttribute("data-selected")).toBe(false);

    rerender(
      <SuggestionCards
        proposals={[makeProposal("wprop_1", { state: "selected" })]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    expect(card.hasAttribute("data-selected")).toBe(true);
  });
});

/* ── Review: WHAT WILL RUN ledger + THE BRIEF facts (HS-167-04 D4) ── */

describe("ActivationReview beauty", () => {
  const noop = () => {};
  const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
  const signalsAnswer = makeAnswer("signals", "PRs stale");

  it("renders one SurfaceLedgerRow per watch in WHAT WILL RUN", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected", testState: "passed" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    // HS-167-04: watch row rendered as SurfaceLedgerRow (one row per watch)
    const watchRow = screen.getByTestId("review-watch-wprop_1");
    expect(watchRow).toBeTruthy();
    // Watch name visible in the row's primary
    const primary = watchRow.querySelector(".surface-ledger-primary");
    expect(primary?.textContent).toContain("Meeting activity");
  });

  it("watch row carries cadence and action tokens in cells", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    const watchRow = screen.getByTestId("review-watch-wprop_1");
    // Cadence token
    expect(watchRow.textContent).toContain("Every 35 min");
    // Action token
    expect(watchRow.textContent).toContain("Put it in Project attention");
  });

  it("THE BRIEF renders outcome and signals as SurfaceFacts", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    // HS-167-04: outcome and signals in SurfaceFacts (dl with dt/dd)
    const outcome = screen.getByTestId("review-outcome");
    expect(outcome).toBeTruthy();
    const signals = screen.getByTestId("review-signals");
    expect(signals).toBeTruthy();
    expect(signals.getAttribute("data-section")).toBe("signals");
  });
});

/* ── Step system consistency (defect 6) — HS-167-04: step tokens
     replaced by ProgressPlan in SetupRoot; model constants kept ── */

describe("Stage model consistency", () => {
  it("STAGE_META has consistent 4-stage system", () => {
    expect(STAGE_COUNT).toBe(4);
    expect(STAGE_META["outcome"].index).toBe(1);
    expect(STAGE_META["signals"].index).toBe(2);
    expect(STAGE_META["proposals"].index).toBe(3);
    expect(STAGE_META["review"].index).toBe(4);
  });
});

/* ── Beauty Round 2: legibility of consequence (HS-159-05) ── */

describe("Consequence headline (fix 1)", () => {
  const noop = () => {};

  it("renders headline with inferred name and tested count", () => {
    const outcomeAnswer = makeAnswer("outcome", "Ship Q4 Payments Platform");
    const signalsAnswer = makeAnswer("signals", "PRs stale");
    const proposals = [
      makeProposal("wprop_1", { state: "selected", testState: "passed" }),
      makeProposal("wprop_2", { state: "selected", testState: "passed" }),
    ];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    const headline = screen.getByTestId("review-headline");
    expect(headline).toBeTruthy();
    // Name derived from outcome answer
    expect(headline.textContent).toContain("Ship Q4 Payments Platform");
    expect(headline.textContent).toContain("2 tested Watches");
  });

  it("uses singular Watch for 1 tested", () => {
    const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
    const signalsAnswer = makeAnswer("signals", "PRs stale");
    const proposals = [
      makeProposal("wprop_1", { state: "selected", testState: "passed" }),
    ];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    const headline = screen.getByTestId("review-headline");
    expect(headline.textContent).toContain("1 tested Watch");
    // Not "Watches"
    expect(headline.textContent).not.toContain("Watches");
  });

  it("falls back to 'New Project' when outcome is empty", () => {
    const outcomeAnswer = makeAnswer("outcome", "");
    const signalsAnswer = makeAnswer("signals", "PRs stale");
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={[]}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    const headline = screen.getByTestId("review-headline");
    expect(headline.textContent).toContain("New Project");
    expect(headline.textContent).toContain("0 tested Watches");
  });
});

describe("inferProjectName", () => {
  it("truncates at 80 chars", () => {
    const long = "A".repeat(100);
    expect(inferProjectName(long)).toBe("A".repeat(80));
  });

  it("returns 'New Project' for empty string", () => {
    expect(inferProjectName("")).toBe("New Project");
  });

  it("returns 'New Project' for whitespace only", () => {
    expect(inferProjectName("   ")).toBe("New Project");
  });

  it("trims whitespace", () => {
    expect(inferProjectName("  Ship Q4  ")).toBe("Ship Q4");
  });
});

describe("No fact duplication at review (fix 2)", () => {
  it("review stage does not render the brief panel", () => {
    // When at review, SetupRoot should NOT mount SetupBrief.
    // We test this indirectly: the ActivationReview does not include
    // a SetupBrief, and the SetupRoot review branch renders without
    // SurfaceColumns.  We verify the review region is present and
    // no setup-brief testid exists in its tree.
    const noop = () => {};
    const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
    const signalsAnswer = makeAnswer("signals", "PRs stale");
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    const { container } = render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    // ActivationReview does not contain a brief panel
    expect(container.querySelector('[data-testid="setup-brief"]')).toBeNull();
    // But the review sections ARE present (outcome, signals, watches)
    expect(screen.getByTestId("review-outcome")).toBeTruthy();
    expect(screen.getByTestId("review-signals")).toBeTruthy();
    expect(screen.getByTestId("review-watches")).toBeTruthy();
  });
});

describe("Pinned footer verb (fix 3)", () => {
  const noop = () => {};
  const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
  const signalsAnswer = makeAnswer("signals", "PRs stale");

  it("activate button is inside a SurfaceFooter", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    // The mocked SurfaceFooter renders a <footer data-testid="surface-footer">
    const footer = screen.getByTestId("surface-footer");
    expect(footer).toBeTruthy();
    // The activate button lives inside it
    const activateBtn = screen.getByTestId("review-activate-btn");
    expect(footer.contains(activateBtn)).toBe(true);
  });

  it("Back button is inside the footer", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    const footer = screen.getByTestId("surface-footer");
    const backBtn = footer.querySelector(".setup-review-back");
    expect(backBtn).toBeTruthy();
    expect(backBtn?.textContent).toBe("Back");
  });
});

describe("'What to notice' header (fix 4)", () => {
  const noop = () => {};
  const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
  const signalsAnswer = makeAnswer("signals", "PRs stale");

  it("review signals section carries machine key", () => {
    const proposals = [makeProposal("wprop_1", { state: "selected" })];
    render(
      <ActivationReview
        outcomeAnswer={outcomeAnswer}
        signalsAnswer={signalsAnswer}
        proposals={proposals}
        onFinalize={noop}
        onBack={noop}
        finalizing={false}
      />,
    );

    // HS-167-04: signals data rendered through SurfaceFacts; machine key preserved
    const section = screen.getByTestId("review-signals");
    expect(section.getAttribute("data-section")).toBe("signals");
  });
});

/* ── HS-167-04: evidence blocks retired — watches are single ledger rows
     with test state visible as CheckGadget + cadence/action tokens ── */

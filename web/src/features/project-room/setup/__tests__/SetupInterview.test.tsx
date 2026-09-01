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
    expect(
      screen.getByText("What outcome are you trying to create or protect?"),
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
    expect(
      screen.getByText("What would you want HoldSpeak to notice without being asked?"),
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

  it("renders suggestion cards with object slots (INT-008)", () => {
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

    // Object slots present
    expect(screen.getByTestId("setup-card-wprop_1")).toBeTruthy();
    expect(screen.getByText("Meeting activity")).toBeTruthy(); // name anchor (label)
    expect(screen.getByText("native")).toBeTruthy(); // source fact value
    expect(screen.getByText("meetings")).toBeTruthy(); // subject fact value
    // Defect 2: plain-words conditions (was "content changed")
    expect(screen.getByText("When meeting content changes")).toBeTruthy(); // summary
    // Action lives behind the fold (ChoiceCard fold pattern) — open it
    const card = screen.getByTestId("setup-card-wprop_1");
    const foldTrigger = card.querySelector(".surface-disclosure-trigger") as HTMLElement;
    fireEvent.click(foldTrigger);
    expect(screen.getByText("Put it in Project attention")).toBeTruthy(); // action in fold
    expect(screen.getByText("Every 35 min")).toBeTruthy(); // cadence fact value
    expect(screen.getByText(/1 recent meetings/)).toBeTruthy(); // rationale footer
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

    expect(screen.getByText("Test passed -- 1 current matches")).toBeTruthy();
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

  it("brief groups show count chips (defect 5)", () => {
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

    // Count chips for proposed (2) and tested (1)
    const proposedCount = screen.getByTestId("brief-count-proposed");
    expect(proposedCount.textContent).toBe("2");
    const testedCount = screen.getByTestId("brief-count-tested");
    expect(testedCount.textContent).toBe("1");
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
      "When meeting content changes",
    );
  });

  it("maps 'changed_to' with value", () => {
    expect(conditionPlainWords(specWith("changed_to", "lifecycle", "accepted", "decisions"))).toBe(
      "When decision lifecycle becomes accepted",
    );
  });

  it("maps 'equals' with value", () => {
    expect(conditionPlainWords(specWith("equals", "lifecycle", "accepted", "decisions"))).toBe(
      "When decision lifecycle is accepted",
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

describe("SuggestionCards object structure", () => {
  const noop = () => {};

  it("renders chips in ChoiceCardShell fact slots (was bespoke chip row)", () => {
    // HS-159: facts now flow through ChoiceCardShell's facts prop.
    // data-chip attributes are gone (the shell renders standard facts).
    // Glass selectors (.surface-choice-card-fact, -fact-val) preserved.
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
    const facts = card.querySelectorAll(".surface-choice-card-fact");
    expect(facts.length).toBe(4); // source, subject, cadence, mode

    expect(facts[0].querySelector(".surface-choice-card-fact-val")?.textContent).toBe("native");
    expect(facts[1].querySelector(".surface-choice-card-fact-val")?.textContent).toBe("meetings");
    expect(facts[2].querySelector(".surface-choice-card-fact-val")?.textContent).toBe("Every 35 min");
    expect(facts[3].querySelector(".surface-choice-card-fact-val")?.textContent).toBe("YOLO");
  });

  it("card has name as ChoiceCard label anchor (was .setup-card-name)", () => {
    // CHANGED: name now lives in .surface-choice-card-label
    // (ChoiceCard head slot) instead of .setup-card-name.
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
    const name = card.querySelector(".surface-choice-card-label");
    expect(name?.textContent).toBe("Meeting activity");
  });

  it("card has rationale as footer", () => {
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
    const rationale = card.querySelector(".setup-card-rationale");
    expect(rationale?.textContent).toContain("1 recent meetings");
  });

  it("card has readiness state token", () => {
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
    const readiness = card.querySelector(".setup-card-readiness");
    expect(readiness?.textContent).toBe("Ready to select");
    expect(readiness?.getAttribute("data-state")).toBe("proposed");
  });

  it("condition raw values on ChoiceCard summary (was .setup-card-conditions)", () => {
    // CHANGED: conditions now render in .surface-choice-card-summary
    // (ChoiceCard one-line anchor slot) instead of .setup-card-conditions.
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
    const summary = card.querySelector(".surface-choice-card-summary");
    // HS-159: data-condition-raw is now on the content span inside the
    // summary div (ChoiceCardShell wraps the summary prop in the div).
    const condSpan = summary?.querySelector("[data-condition-raw]");
    expect(condSpan?.getAttribute("data-condition-raw")).toBe("content:changed");
  });

  it("selected card shows presence (accent) via aria-selected", () => {
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

  /* ── NEW: ChoiceCard visual language assertions (HS-159-05 R4) ── */

  it("renders as ChoiceCard (surface-choice-card class)", () => {
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

  it("summary line is the plain-words condition", () => {
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
    const summary = card.querySelector(".surface-choice-card-summary");
    expect(summary).toBeTruthy();
    expect(summary?.textContent).toBe("When meeting content changes");
  });

  it("selection presence via the library's data-selected state", () => {
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
    // Unselected: no data-selected
    expect(card.hasAttribute("data-selected")).toBe(false);

    // Re-render as selected
    rerender(
      <SuggestionCards
        proposals={[makeProposal("wprop_1", { state: "selected" })]}
        onSelect={noop}
        onDeselect={noop}
        onTest={noop}
        suggesting={false}
      />,
    );
    // Selected: data-selected stamped (drives accent wash via choice-card.css)
    expect(card.hasAttribute("data-selected")).toBe(true);
  });

  it("fold carries action detail (ChoiceCard fold pattern)", () => {
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
    // Fold is present
    const fold = card.querySelector(".surface-choice-card-fold");
    expect(fold).toBeTruthy();
    // Action hidden until fold opened
    expect(card.querySelector(".setup-card-action-detail")).toBeNull();
    // Open the fold
    const trigger = fold!.querySelector(".surface-disclosure-trigger") as HTMLElement;
    fireEvent.click(trigger);
    // Action now visible
    const actionDetail = card.querySelector(".setup-card-action-detail");
    expect(actionDetail?.textContent).toBe("Put it in Project attention");
  });

  it("rationale is visible footer (not folded — glass selector)", () => {
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
    const rationale = card.querySelector(".setup-card-rationale");
    expect(rationale).toBeTruthy();
    expect(rationale?.textContent).toContain("1 recent meetings");
    // Rationale is NOT inside the fold
    const fold = card.querySelector(".surface-choice-card-fold");
    expect(fold?.contains(rationale!)).toBe(false);
  });

  it("chips render in ChoiceCard fact slots", () => {
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
    const factsContainer = card.querySelector(".surface-choice-card-facts");
    expect(factsContainer).toBeTruthy();
    const facts = factsContainer!.querySelectorAll(".surface-choice-card-fact");
    expect(facts.length).toBe(4);
    // Each fact has key/value structure
    facts.forEach((fact) => {
      expect(fact.querySelector(".surface-choice-card-fact-key")).toBeTruthy();
      expect(fact.querySelector(".surface-choice-card-fact-val")).toBeTruthy();
    });
  });
});

/* ── Review ledger alignment and YOLO token (defects 3, 4) ── */

describe("ActivationReview beauty", () => {
  const noop = () => {};
  const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
  const signalsAnswer = makeAnswer("signals", "PRs stale");

  it("renders ledger-aligned label/value rows for watch spec", () => {
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

    const ledger = screen.getByTestId("review-ledger-wprop_1");
    expect(ledger).toBeTruthy();

    // Check label/value pairs
    const rows = ledger.querySelectorAll(".setup-review-ledger-row");
    expect(rows.length).toBe(5); // Subject, Conditions, Cadence, Action, Mode

    // Labels aligned
    const labels = Array.from(rows).map((r) => r.querySelector("dt")?.textContent);
    expect(labels).toEqual(["Subject", "Conditions", "Cadence", "Action", "Mode"]);
  });

  it("renders mode as a posture token with data-mode (defect 3)", () => {
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

    const modeToken = screen.getByTestId("review-watch-wprop_1").querySelector(".setup-mode-token");
    expect(modeToken).toBeTruthy();
    expect(modeToken?.textContent).toBe("YOLO");
    expect(modeToken?.getAttribute("data-mode")).toBe("yolo");
  });

  it("renders plain-words conditions in review (defect 2)", () => {
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

    // Find the Conditions row
    const conditionValue = screen.getByTestId("review-ledger-wprop_1")
      .querySelectorAll(".setup-review-ledger-row")[1]
      .querySelector("dd");
    expect(conditionValue?.textContent).toBe("When meeting content changes");
    // Machine value in data attribute
    expect(conditionValue?.getAttribute("data-condition-raw")).toBe("content:changed");
  });

  it("shows step indicator on review (defect 6)", () => {
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

    const token = screen.getByTestId("setup-step-token");
    expect(token.textContent).toBe("Step 4 of 4");
  });
});

/* ── Step token consistency (defect 6) ── */

describe("Step token across stages", () => {
  const noop = () => {};

  it("outcome stage shows Step 1 of 4", () => {
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

    const token = screen.getByTestId("setup-step-token");
    expect(token.textContent).toBe("Step 1 of 4");
  });

  it("signals stage shows Step 2 of 4", () => {
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

    const tokens = screen.getAllByTestId("setup-step-token");
    // The active question has the token
    const signalsToken = tokens[tokens.length - 1];
    expect(signalsToken.textContent).toBe("Step 2 of 4");
  });

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

  it("review signals section is labeled 'What to notice'", () => {
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

    const section = screen.getByTestId("review-signals");
    const label = section.querySelector(".setup-review-label");
    expect(label?.textContent).toBe("What to notice");
    // data- attribute preserves machine key
    expect(section.getAttribute("data-section")).toBe("signals");
  });
});

describe("Framed test evidence (fix 5)", () => {
  const noop = () => {};
  const outcomeAnswer = makeAnswer("outcome", "Ship Q4");
  const signalsAnswer = makeAnswer("signals", "PRs stale");

  it("renders evidence as one framed block with pass token, count, entities, time", () => {
    const proposals = [
      makeProposal("wprop_1", {
        state: "selected",
        testState: "passed",
        testResult: {
          entityCount: 1,
          representativeEntities: [{ title: "Sprint 7 Planning" }],
          observedAt: "2026-08-31T10:04:00",
          error: null,
          message: "Test passed -- 1 current matches",
        },
      }),
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

    const evidence = screen.getByTestId("review-test-evidence");
    expect(evidence).toBeTruthy();
    expect(evidence.getAttribute("data-test-state")).toBe("passed");

    // One block contains: pass icon, count, entity, time
    const header = evidence.querySelector(".setup-review-evidence-header");
    expect(header).toBeTruthy();
    expect(header?.textContent).toContain("Test passed");
    expect(header?.textContent).toContain("1 current match");

    // Entity in list
    const entity = evidence.querySelector(".setup-review-evidence-entity");
    expect(entity?.textContent).toBe("Sprint 7 Planning");

    // Observed time
    const time = evidence.querySelector(".setup-review-evidence-time");
    expect(time?.textContent).toContain("Observed at");

    // It is a bordered inset (has the evidence class with border)
    expect(evidence.classList.contains("setup-review-evidence")).toBe(true);
  });

  it("uses plural matches for count > 1", () => {
    const proposals = [
      makeProposal("wprop_1", {
        state: "selected",
        testState: "passed",
        testResult: {
          entityCount: 3,
          representativeEntities: [
            { title: "Item 1" },
            { title: "Item 2" },
            { title: "Item 3" },
          ],
          observedAt: "2026-08-31T10:04:00",
          error: null,
          message: "Test passed -- 3 current matches",
        },
      }),
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

    const header = screen.getByTestId("review-test-evidence")
      .querySelector(".setup-review-evidence-header");
    expect(header?.textContent).toContain("3 current matches");

    // All three entities in list
    const entities = screen.getByTestId("review-test-evidence")
      .querySelectorAll(".setup-review-evidence-entity");
    expect(entities.length).toBe(3);
  });
});

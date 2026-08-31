// HS-159-05 -- SetupInterview component tests: two questions (INT-003),
// keyboard behaviors (WEB-CMD-005), voice-never-submits (WEB-CMD-006),
// card object slots (INT-008), brief state mirroring, Blank path.

import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

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
import type { ControllerState } from "../useSetupController";
import type { SetupAnswer, SetupProposal } from "../model";

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
    expect(screen.getByText("Meeting activity")).toBeTruthy(); // name
    expect(screen.getByText("native")).toBeTruthy(); // source chip
    expect(screen.getByText("meetings")).toBeTruthy(); // subject kind
    expect(screen.getByText("content changed")).toBeTruthy(); // conditions
    expect(screen.getByText("Put it in Project attention")).toBeTruthy(); // action
    expect(screen.getByText("Every 35 min")).toBeTruthy(); // cadence
    expect(screen.getByText(/1 recent meetings/)).toBeTruthy(); // rationale
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
});

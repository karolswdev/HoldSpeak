/**
 * Inventory C, gap 1 (Astra's finding on PR #770) — a decision cited under a
 * Room answer opens the decision and leaves the answer where it is.
 *
 * Red before the fix: the Room sent a `decision:` / `desk_decision:` citation
 * to a view named "decisions". No such view exists, so the Room drew History:
 * the answer left the screen and nothing opened. Harness copied from
 * room200TaskResume.test.tsx; the click is the rendered citation chip in the
 * mounted Room.
 */
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { openPrimitive } from "../../../desk/shell";
import { ProjectRoomCore } from "../ProjectRoomCore";

const asks = vi.hoisted(() => ({
  runAsk: vi.fn(),
  saveAskTask: vi.fn(),
  listUnfinishedAsks: vi.fn(),
  resumeAskTask: vi.fn(),
  discardAskTask: vi.fn(),
  stopAskTask: vi.fn(),
}));
vi.mock("../../../desk/ask", async () => {
  const actual =
    await vi.importActual<typeof import("../../../desk/ask")>("../../../desk/ask");
  return { ...actual, ...asks };
});

const assignment = vi.hoisted(() => ({ getAssignmentEditor: vi.fn() }));
vi.mock("../../../pages/cores/assignmentExperience", async () => {
  const actual = await vi.importActual<
    typeof import("../../../pages/cores/assignmentExperience")
  >("../../../pages/cores/assignmentExperience");
  return { ...actual, getAssignmentEditor: assignment.getAssignmentEditor };
});

const apiFetch = vi.fn();
vi.mock("../../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../../lib/api")>("../../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../../../desk/shell", async () => {
  const actual = await vi.importActual<typeof import("../../../desk/shell")>("../../../desk/shell");
  return { ...actual, openPrimitive: vi.fn(), openSurfaceOr: vi.fn() };
});

function WindowHarness({ scope }: { scope?: string }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <TitleSlotContext.Provider value={() => {}}>
      <WingSlotContext.Provider value={setWings}>
        <div data-testid="wing-slot">{wings}</div>
        <ProjectRoomCore scope={scope} />
      </WingSlotContext.Provider>
    </TitleSlotContext.Provider>
  );
}

function roomResponse() {
  return {
    project_id: "p1", revision: 3, observed_at: "2026-09-07T10:00:00",
    project: {
      id: "p1", name: "Ship the Q4 platform", description: null, is_archived: false,
      meeting_count: 0, created_at: "2026-08-01T00:00:00", updated_at: "2026-09-07T10:00:00",
      purpose: null, outcome_text: "Ship the Q4 platform", owner_ref: null, lifecycle: "active",
      posture: null, posture_reason: null, start_at: "2026-08-01", target_at: null, revision: 3,
    },
    items: { state: "ok", focus: [], totals_by_type: {}, total: 0 },
    meetings: { state: "ok", count: 0, latest: null },
    resources: { state: "ok", count: 0, latest: null },
    changes: { state: "ok", recent: [] },
    review: { state: "absent", reason: "not_yet_built" },
    needsYou: { state: "ok", items: [], count: 0 },
    sources: { state: "ok", items: [], count: 0, nextCheckAt: null },
    health: {
      state: "ok", assessment: "on_track", reason: null,
      inputs: { overdue: 0, ciFailing: false, reviewWaitingDays: null, targetPassed: false },
    },
    sinceRead: { state: "ok", readAt: null, groups: [] },
    decisions: { state: "ok", items: [] },
    commitments: { state: "ok", items: [] },
    target: { state: "absent", reason: "none" },
    updates: { state: "absent", reason: "not_yet_built" },
    steward: { state: "absent", reason: "not_yet_built" },
  };
}

function response(url: string) {
  if (url.includes("/room/read")) return { read_at: new Date().toISOString() };
  if (url.includes("/room")) return roomResponse();
  if (url.includes("/meetings")) return { meetings: [] };
  if (url.startsWith("/api/decisions")) return { decisions: [] };
  if (url.includes("/artifacts")) return { artifacts: [] };
  if (url.includes("/since-last-meeting"))
    return { current_meeting: null, since_last_meeting: null };
  return {};
}

const SAVED_TASK = {
  id: "asktask_1",
  projectId: "p1",
  invocationId: "ask_deadbeef",
  purpose: "what is left before the cut-over",
  lens: "Project",
  state: "saved" as const,
  savedAt: "2026-09-07T09:04:00",
  updatedAt: "2026-09-07T09:04:00",
  resumeOrder: 1,
  custody: "here" as const,
};

const ANSWER = {
  ok: true,
  output: "Three things are left.",
  invocationId: "ask_deadbeef",
  egress: null,
  model: "",
  profileId: null,
  inferenceTarget: null,
  actualPlacement: null,
  contextIds: [],
  contextTitles: [],
  groundingClaims: [],
  groundingReceipt: null,
};

beforeEach(() => {
  apiFetch.mockImplementation((url: string) => Promise.resolve(response(url)));
  assignment.getAssignmentEditor.mockResolvedValue({
    effective: { status: "unassigned", assignment: null },
  });
  asks.listUnfinishedAsks.mockResolvedValue({ items: [], nextCursor: null });
  asks.saveAskTask.mockResolvedValue(SAVED_TASK);
  asks.runAsk.mockResolvedValue(ANSWER);
  asks.resumeAskTask.mockResolvedValue({
    ok: true, task: { ...SAVED_TASK, state: "accepted" }, answer: ANSWER,
    claimed: true, dispatched: false, error: "",
  });
  asks.discardAskTask.mockResolvedValue(true);
  asks.stopAskTask.mockResolvedValue({ ok: true, task: null, changed: true });
  useDesk.setState({
    windowsById: {}, items: { ...EMPTY_ITEMS }, projects: [], inferenceTargets: [],
  });
});

afterEach(() => { vi.clearAllMocks(); });

async function askAndGetAnswer(sourceRefs: string[]) {
  asks.runAsk.mockResolvedValue({
    ...ANSWER,
    output: "We adopted quorumdb for the ledger.",
    groundingReceipt: {
      selection: "relevance", matchedCount: sourceRefs.length, overflowCount: 0, sourceRefs,
    },
  });
  render(<WindowHarness scope="project:p1" />);
  const well = await screen.findByLabelText("Ask this project");
  await userEvent.click(well);
  await userEvent.paste("what did we decide about quorumdb");
  await userEvent.keyboard("{Enter}");
  return await screen.findByTestId("room-ask-answer");
}

describe("a decision cited under a Room answer", () => {
  it.each([
    ["desk_decision:decision_7ce0", "the one ref name"],
    ["decision:decision_7ce0", "a row filed under the old name"],
  ])("%s (%s): the chip opens the decision; the answer stays", async (ref) => {
    apiFetch.mockImplementation((url: string) =>
      url === "/api/decisions/decision_7ce0"
        ? Promise.resolve({ decision: { id: "decision_7ce0", title: "Adopt quorumdb" } })
        : Promise.resolve(response(url)),
    );
    const answer = await askAndGetAnswer([ref]);
    expect(answer.textContent).toContain("We adopted quorumdb for the ledger.");

    await userEvent.click(screen.getByRole("button", { name: "Decision · decision_7ce0" }));

    await waitFor(() => expect(openPrimitive).toHaveBeenCalledWith("decision:decision_7ce0"));
    // The Room did not change wing: the answer is still drawn, History is not.
    expect(screen.getByTestId("room-ask-answer").textContent).toContain("We adopted quorumdb for the ledger.");
    expect(screen.queryByTestId("room-history")).toBeNull();
    expect(screen.getByTestId("room-ask-well")).toBeTruthy();
  });
});

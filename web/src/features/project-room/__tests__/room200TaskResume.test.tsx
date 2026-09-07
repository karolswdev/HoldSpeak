/**
 * HS-200-41 — the Room ask well: durable, resumable, and back in the loop.
 *
 * Three things are proved here, and each of them was a real hole:
 *  1. the ask is SAVED before it is dispatched, and runs under the identity
 *     the save minted (ruling B3) — the words no longer die with the tab;
 *  2. a saved ask draws the `TaskResume` row and comes back on `Resume`;
 *  3. `MODEL · NOT SET` heals without a reload once a model is assigned —
 *     the defect on the very seam return-to-task sends him back to.
 */
import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../../desk/api";
import { TitleSlotContext } from "../../../desk/surface/title";
import { WingSlotContext } from "../../../desk/surface/wings";
import { useDesk } from "../../../desk/store";
import { announceTaskReturn } from "../../../desk/returnToTask";
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

describe("HS-200-41: the ask is durable before it is dispatched", () => {
  it("saves the words FIRST, then runs under the identity the save minted", async () => {
    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByLabelText("Ask this project");
    await userEvent.click(well);
    await userEvent.paste("what is left before the cut-over");
    await userEvent.keyboard("{Enter}");

    await waitFor(() => expect(asks.runAsk).toHaveBeenCalled());
    // Ruling B3: the row exists BEFORE anything is dispatched.
    expect(asks.saveAskTask).toHaveBeenCalledWith("p1", {
      purpose: "what is left before the cut-over",
      lens: "Project",
      grounding: {
        meeting_ids: [], artifact_ids: [], refs: ["project:p1"], expand: "summary",
      },
    });
    expect(asks.saveAskTask.mock.invocationCallOrder[0]).toBeLessThan(
      asks.runAsk.mock.invocationCallOrder[0],
    );
    // And the run carries the identity the save minted — the client never
    // invents a second one.
    expect(asks.runAsk.mock.calls[0][0].invocationId).toBe("ask_deadbeef");
    // The answer settles the record against `ask_results` (claimed, not
    // re-dispatched), so a finished ask does not linger as unfinished.
    await waitFor(() => expect(asks.resumeAskTask).toHaveBeenCalledWith("asktask_1"));
  });

  it("a failed run records WHY it stopped — the code alone — and stays resumable", async () => {
    asks.runAsk.mockResolvedValue({
      ...ANSWER,
      ok: false,
      output: "model file not found: qwen3-35b.gguf",
      refusalCode: "inference_target_unavailable",
    });
    const FAILED = {
      ...SAVED_TASK,
      state: "failed" as const,
      stoppedReason: "model file not found: qwen3-35b.gguf",
      stoppedCode: "inference_target_unavailable",
    };
    asks.listUnfinishedAsks
      .mockResolvedValueOnce({ items: [], nextCursor: null })
      .mockResolvedValue({ items: [FAILED], nextCursor: null });

    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByLabelText("Ask this project");
    await userEvent.click(well);
    await userEvent.paste("what is left before the cut-over");
    await userEvent.keyboard("{Enter}");

    // The CODE goes back to the store, never the sentence: the server
    // resolves its own reason from its live placement.
    await waitFor(() =>
      expect(asks.stopAskTask).toHaveBeenCalledWith(
        "asktask_1",
        "inference_target_unavailable",
      ),
    );
    // Nothing was settled as accepted: the record stays unfinished.
    expect(asks.resumeAskTask).not.toHaveBeenCalled();
    // And the row he comes back to is right there, with its verb.
    const row = await screen.findByTestId("room-unfinished-asktask_1");
    expect(within(row).getByRole("status", { name: "FAILED" })).toBeInTheDocument();
    // The hub's own words, verbatim (ruling B5), on their own wrapping row.
    expect(
      within(row).getByText("model file not found: qwen3-35b.gguf"),
    ).toBeInTheDocument();
    expect(
      within(row).getByRole("button", {
        name: "Check: what is left before the cut-over",
      }),
    ).toBeEnabled();

    // F6: SAID ONCE. The row carries the failure, so the composer's red
    // prose underneath is gone — at 393 it was the same sentence three times.
    expect(document.querySelectorAll(".room-ask-error")).toHaveLength(0);
    expect(
      screen.getAllByText("model file not found: qwen3-35b.gguf"),
    ).toHaveLength(1);
  });

  it("a failure that reached no row still speaks — it is all that can", async () => {
    // No code means no row was stopped, so the inline line is the only voice
    // left. Removing it too would have swallowed the failure entirely.
    asks.runAsk.mockResolvedValue({
      ...ANSWER, ok: false, output: "Could not reach the server.", refusalCode: "",
    });
    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByLabelText("Ask this project");
    await userEvent.click(well);
    await userEvent.paste("what is left before the cut-over");
    await userEvent.keyboard("{Enter}");
    expect(await screen.findByText("Could not reach the server.")).toBeInTheDocument();
  });

  it("a refusal with no code records nothing — the client invents no token", async () => {
    asks.runAsk.mockResolvedValue({
      ...ANSWER, ok: false, output: "Could not reach the server.", refusalCode: "",
    });
    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByLabelText("Ask this project");
    await userEvent.click(well);
    await userEvent.paste("what is left before the cut-over");
    await userEvent.keyboard("{Enter}");

    expect(await screen.findByText("Could not reach the server.")).toBeInTheDocument();
    expect(asks.stopAskTask).not.toHaveBeenCalled();
  });

  it("a no-op stop (changed: false) is not drawn as a failure", async () => {
    // A repeat on an already-failed row comes back `changed: false`. The face
    // must not treat that as an error: the row already says what happened, so
    // nothing extra is drawn and the well stays usable.
    asks.runAsk.mockResolvedValue({
      ...ANSWER, ok: false, output: "model file not found: qwen3-35b.gguf",
      refusalCode: "inference_target_unavailable",
    });
    asks.stopAskTask.mockResolvedValue({ ok: true, task: null, changed: false });
    asks.listUnfinishedAsks
      .mockResolvedValueOnce({ items: [], nextCursor: null })
      .mockResolvedValue({
        items: [{
          ...SAVED_TASK, state: "failed" as const,
          stoppedReason: "model file not found: qwen3-35b.gguf",
          stoppedCode: "inference_target_unavailable",
        }],
        nextCursor: null,
      });

    render(<WindowHarness scope="project:p1" />);
    const well = await screen.findByLabelText("Ask this project");
    await userEvent.click(well);
    await userEvent.paste("what is left before the cut-over");
    await userEvent.keyboard("{Enter}");

    // The row speaks, once; nothing about `changed` reaches the face.
    const row = await screen.findByTestId("room-unfinished-asktask_1");
    expect(
      within(row).getByText("model file not found: qwen3-35b.gguf"),
    ).toBeInTheDocument();
    expect(document.querySelectorAll(".room-ask-error")).toHaveLength(0);
    expect(screen.queryByText(/changed/i)).toBeNull();
    // The well is usable again: nothing latched.
    expect(screen.getByLabelText("Ask this project")).toBeEnabled();
  });
});

describe("HS-200-41: the saved ask has a face and a way back", () => {
  it("draws the TaskResume row with its custody token and one verb", async () => {
    asks.listUnfinishedAsks.mockResolvedValue({ items: [SAVED_TASK], nextCursor: null });
    render(<WindowHarness scope="project:p1" />);

    const row = await screen.findByTestId("room-unfinished-asktask_1");
    // F5: it is a SECTION in the Room body, not a ledger inside the
    // composer's sticky foot. At five rows the sticky container covered every
    // other section and the Room was gone behind a wall of unfinished asks.
    expect(row.closest(".room-ask-container")).toBeNull();
    expect(screen.getByTestId("room-ask-well").contains(row)).toBe(false);
    expect(within(row).getByText("what is left before the cut-over")).toBeInTheDocument();
    expect(within(row).getByRole("status", { name: "SAVED 09:04" })).toBeInTheDocument();
    // Ruling B7 — and never the egress word, and never a host id (F1).
    expect(within(row).getByText("SAVED HERE")).toBeInTheDocument();
    expect(screen.queryByText(/THIS DEVICE/)).toBeNull();
    expect(row.textContent || "").not.toMatch(/refhost|[0-9a-f]{16,}/i);
    // The ask carries no recipe, so the row draws no recipe token at all.
    expect(within(row).queryByText(/RECIPE/)).toBeNull();
    expect(
      within(row).getByRole("button", {
        name: "Resume: what is left before the cut-over",
      }),
    ).toBeInTheDocument();
  });

  it("Resume claims the answer and puts the purpose back in the well", async () => {
    asks.listUnfinishedAsks
      .mockResolvedValueOnce({ items: [SAVED_TASK], nextCursor: null })
      .mockResolvedValue({ items: [], nextCursor: null });
    render(<WindowHarness scope="project:p1" />);

    const row = await screen.findByTestId("room-unfinished-asktask_1");
    await userEvent.click(within(row).getByRole("button", { name: /^Resume: / }));

    await waitFor(() => expect(asks.resumeAskTask).toHaveBeenCalledWith("asktask_1"));
    expect(await screen.findByTestId("room-ask-answer")).toHaveTextContent(
      "Three things are left.",
    );
    expect(screen.getByLabelText("Ask this project")).toHaveValue(
      "what is left before the cut-over",
    );
    // Nothing re-ran: the answer was already on disk (ruling B3).
    expect(asks.runAsk).not.toHaveBeenCalled();
  });

  it("Discard is behind MORE and takes two presses", async () => {
    asks.listUnfinishedAsks.mockResolvedValue({ items: [SAVED_TASK], nextCursor: null });
    render(<WindowHarness scope="project:p1" />);

    const row = await screen.findByTestId("room-unfinished-asktask_1");
    await userEvent.click(within(row).getByRole("button", { name: /MORE/ }));
    const discard = within(row).getByRole("button", { name: "Discard the unfinished ask" });
    await userEvent.click(discard);
    expect(asks.discardAskTask).not.toHaveBeenCalled();
    await userEvent.click(discard);
    await waitFor(() => expect(asks.discardAskTask).toHaveBeenCalledWith("asktask_1"));
  });

  it("one row keeps the filled primary; more than one draws quiet verbs", async () => {
    // The ratified board draws UNFINISHED 1 — one row, one filled primary.
    // Five filled primaries is no lead at all. Flagged to the owner as a
    // board question; this is the ruling in force meanwhile.
    asks.listUnfinishedAsks.mockResolvedValue({ items: [SAVED_TASK], nextCursor: null });
    const one = render(<WindowHarness scope="project:p1" />);
    let row = await screen.findByTestId("room-unfinished-asktask_1");
    expect(
      within(row).getByRole("button", { name: /^Resume: / }).className,
    ).toContain("btn--primary");
    one.unmount();

    asks.listUnfinishedAsks.mockResolvedValue({
      items: [SAVED_TASK, { ...SAVED_TASK, id: "asktask_2", purpose: "the other one" }],
      nextCursor: null,
    });
    render(<WindowHarness scope="project:p1" />);
    row = await screen.findByTestId("room-unfinished-asktask_1");
    const verbs = screen.getAllByRole("button", { name: /^Resume: / });
    expect(verbs).toHaveLength(2);
    for (const verb of verbs) expect(verb.className).not.toContain("btn--primary");
  });

  it("no unfinished work draws NO caption — never UNFINISHED 0", async () => {
    render(<WindowHarness scope="project:p1" />);
    await screen.findByLabelText("Ask this project");
    expect(screen.queryByTestId("room-unfinished")).toBeNull();
    expect(screen.queryByText(/UNFINISHED/)).toBeNull();
  });
});

describe("HS-200-41: the Room ask well is in the return-to-task loop", () => {
  it("re-reads the saved work on the signal, without a reload", async () => {
    asks.listUnfinishedAsks.mockResolvedValue({ items: [], nextCursor: null });
    render(<WindowHarness scope="project:p1" />);
    await screen.findByLabelText("Ask this project");
    await waitFor(() => expect(asks.listUnfinishedAsks).toHaveBeenCalled());
    const before = asks.listUnfinishedAsks.mock.calls.length;

    announceTaskReturn();

    await waitFor(() =>
      expect(asks.listUnfinishedAsks.mock.calls.length).toBeGreaterThan(before),
    );
  });

  it("MODEL · NOT SET heals on the same signal — the defect fixed here", async () => {
    // The old hook re-read only on [projectId, targets], and
    // `inferenceTargets` moves only when the whole desk calls refresh().
    // So the owner pressed Choose, assigned a model, came back — and the
    // chip still read NOT SET. That is the STATE half of return-to-task
    // failing on the surface this story sends him back to.
    render(<WindowHarness scope="project:p1" />);
    expect(await screen.findByText("MODEL · NOT SET")).toBeInTheDocument();

    // A model is assigned while he is away, and the endpoint is one the
    // desk store has never heard of.
    assignment.getAssignmentEditor.mockResolvedValue({
      effective: {
        status: "assigned",
        assignment: {
          entries: [{ profile_id: "pf-1", boundary: "private_network", label: "Qwen3" }],
        },
      },
    });
    apiFetch.mockImplementation((url: string) => {
      if (String(url) === "/api/inference-targets")
        return Promise.resolve({
          targets: [
            {
              profile_id: "pf-1",
              endpoint: "http://192.168.1.43:8080",
              boundary: "private_network",
            },
          ],
        });
      return Promise.resolve(response(String(url)));
    });

    announceTaskReturn();

    expect(await screen.findByText("MODEL · 192.168.1.43:8080")).toBeInTheDocument();
    expect(screen.queryByText("MODEL · NOT SET")).toBeNull();
  });
});

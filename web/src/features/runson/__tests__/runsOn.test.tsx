// PHILO-16 (C) — Runs on, the Models window as a Switchboard.
//
// Ported intents of the parked Concierge tests (features/concierge/__tests__):
// the engine truth (state from the authority's fit, never reachability), the
// repairs and the add row, plus the board's own: a drop writes the whole
// chain with CAS, 409 redraws, Undo, Meetings writes the summary row, Try it
// (local, off-machine behind the press, speech), FOUND → Use it, the bar.

import { act, fireEvent, render, renderHook, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useBuilderTools } from "../../../desk/builderTools";
import { ApiError } from "../../../lib/api";
import type { Detection, Roster, RosterRow } from "../api";
import type { LocalAiRead } from "../../../desk/firstrun/localAi";

const m = vi.hoisted(() => ({
  readRoster: vi.fn(),
  readDetection: vi.fn(),
  discoverLan: vi.fn(),
  writeChain: vi.fn(),
  clearChain: vi.fn(),
  readAcquisition: vi.fn(),
  taskProbe: vi.fn(),
  probe: vi.fn(),
  download: vi.fn(),
  summary: vi.fn(),
  define: vi.fn(),
  check: vi.fn(),
  startCapture: vi.fn(),
  stopAndTranscribe: vi.fn(),
  cancelCapture: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    readRoster: m.readRoster,
    readDetection: m.readDetection,
    discoverLan: m.discoverLan,
    writeChain: m.writeChain,
    clearChain: m.clearChain,
    readAcquisition: m.readAcquisition,
  };
});

vi.mock("../../concierge/api", () => ({
  conciergeTaskProbe: m.taskProbe,
  conciergeProbe: m.probe,
  conciergeDownload: m.download,
  conciergeSummarySelection: m.summary,
  defineEndpoint: m.define,
  checkEndpoint: m.check,
}));

vi.mock("../../../lib/speakToFill", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/speakToFill")>()),
  startCapture: m.startCapture,
  stopAndTranscribe: m.stopAndTranscribe,
  cancelCapture: m.cancelCapture,
}));

vi.mock("../../concierge/MeaningSearchRow", () => ({ MeaningSearchRow: () => null }));
// PHILO-17 speech: the speech truth is the hub's (its own vitest file fences
// the row); here only "is speech set up" moves.
const speechState = vi.hoisted(() => ({ notSetUp: false, readKind: "ok" as LocalAiRead["kind"] }));
vi.mock("../../../desk/firstrun/SpeechSetup", () => ({
  useSpeechSetup: () => ({
    notSetUp: speechState.readKind === "ok" && speechState.notSetUp,
    ready: speechState.readKind === "ok" && !speechState.notSetUp,
    ai: { read: { kind: speechState.readKind } },
  }),
  SpeechSetup: ({ testId }: { testId: string }) => <span data-testid={testId}>Speech is not set up</span>,
}));
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: m.openSurfaceOr }));

import { RunsOnCore } from "../RunsOnCore";
import { useRunsOn } from "../useRunsOn";

const Q27 = { profile_id: "q27", profile_revision: 1, label: "qwen3.8 27B", boundary: "private_network", readiness: "ready" };
const Q4B = { profile_id: "q4b", profile_revision: 2, label: "Qwen 3.5 4B", boundary: "local", readiness: "ready" };
const WHISPER = { profile_id: "whisper-small", profile_revision: 1, label: "Whisper small", boundary: "local", readiness: "ready" };

function row(id: string, label: string, over: Partial<RosterRow> = {}): RosterRow {
  return {
    id,
    label,
    inherited_from: "global",
    assignment: { revision: 3, entries: [Q27], issues: [] },
    status: "assigned",
    repair: null,
    editor_capability_id: null,
    expected_revision: 0,
    ...over,
  };
}

function roster(): Roster {
  return {
    rows: [
      row("global", "Default for AI work", { inherited_from: null, expected_revision: 3, editor_capability_id: "ask.answer" }),
      row("thoughts_notes", "Thoughts & notes", {
        inherited_from: "group",
        assignment: { revision: 2, entries: [Q4B], issues: [] },
        expected_revision: 2,
        editor_capability_id: "ask.answer",
      }),
      row("writing_dictation", "Writing & dictation"),
      row("speech_recognition", "Speech recognition", {
        inherited_from: "group",
        assignment: { revision: 1, entries: [WHISPER], issues: [] },
        expected_revision: 1,
        editor_capability_id: "speech.transcribe",
      }),
      row("meetings", "Meetings", { editor_capability_id: "meeting.deferred_analysis" }),
      row("agents_tools", "Agents & tools", { editor_capability_id: "agent.plan" }),
      row("background", "Background", { editor_capability_id: "memory.embed" }),
    ],
    tasks: [
      { id: "ask.answer", label: "Ask answer", group: { id: "thoughts_notes", label: "Thoughts & notes" }, has_override: false },
      { id: "meeting.deferred_analysis", label: "Deferred meeting analysis", group: { id: "meetings", label: "Meetings" }, has_override: false },
      { id: "meeting.auto_title", label: "Meeting title", group: { id: "meetings", label: "Meetings" }, has_override: false },
      { id: "meeting.live_analysis", label: "Live meeting analysis", group: { id: "meetings", label: "Meetings" }, has_override: false },
      { id: "speech.transcribe", label: "Speech transcription", group: { id: "speech_recognition", label: "Speech recognition" }, has_override: false },
    ],
  };
}

function detection(): Detection {
  return {
    engines: [
      {
        id: "lan:q27", kind: "lan", name: "qwen3.8 27B", host: "192.168.1.43", state: "READY",
        profileId: "q27", profileRevision: 1, runtimeToken: "LLAMA.CPP", latencyMs: 410,
        fits: {
          meetings: { state: "LIMITED", blocked: ["Calendar"] },
          agents_tools: { state: "READY" },
          thoughts_notes: { state: "READY" },
        },
      },
      {
        id: "local:q4b", kind: "local", name: "Qwen 3.5 4B", host: "THIS DEVICE", state: "READY",
        profileId: "q4b", profileRevision: 2, sizeBytes: 2_700_000_000,
        fits: { agents_tools: { state: "INCOMPATIBLE", blocked: ["Agents"] }, thoughts_notes: { state: "READY" } },
      },
      {
        id: "local:whisper:mlx:small", kind: "local", name: "Whisper small", host: "THIS DEVICE", state: "READY",
        profileId: "whisper-small", profileRevision: 1, audioCapable: true,
      },
      {
        id: "cloud:openrouter", kind: "cloud", name: "OpenRouter", host: "openrouter.ai", state: "READY",
        profileId: "openrouter", profileRevision: 1, keySet: true, fits: { meetings: { state: "READY" } },
      },
      {
        id: "preset:vision", kind: "preset", name: "Qwen 3.5 4B vision file", host: "THIS DEVICE", state: "WAITING",
        presetId: "vision", sizeBytes: 890_000_000, downloadHost: "huggingface.co",
      },
      {
        id: "local:ollama:11434:llama3.3", kind: "local", name: "Llama 3.3 8B", host: "THIS DEVICE", state: "READY",
        found: true, baseUrl: "http://127.0.0.1:11434/v1", legacyLabel: "llama3.3",
      },
    ],
    hardware: { capability: { apple_silicon: true, ram_gb: 36 } },
    checkedAt: "2026-10-09T09:14:00Z",
    repairs: [],
    // The REAL producer's answer for an inherited summary row (Astra r1
    // C2): `assigned` through the Default for AI work, at revision 0, with
    // no own head (the roster's has_override is false).
    summaryAssignment: {
      capabilityId: "meeting.deferred_analysis", status: "assigned", assignmentRevision: 0,
      profileId: "q27", profileRevision: 1, label: "qwen3.8 27B", boundary: "lan", readiness: "ready",
    },
  };
}

beforeEach(() => {
  speechState.readKind = "ok";
  speechState.notSetUp = false;
  for (const fn of Object.values(m)) fn.mockReset();
  m.readRoster.mockResolvedValue(roster());
  m.readDetection.mockResolvedValue(detection());
  m.discoverLan.mockResolvedValue({ engines: [], checkedAt: "2026-10-09T09:14:00Z", partial: false, unavailable: false, hostsChecked: 0 });
  m.writeChain.mockResolvedValue({ revision: 7 });
  m.clearChain.mockResolvedValue({ revision: 8 });
  m.summary.mockResolvedValue({
    status: "succeeded", state: "READY", plainReason: "",
    summaryAssignment: { ...detection().summaryAssignment!, profileId: "openrouter", assignmentRevision: 5 },
  });
});

afterEach(() => {
  vi.useRealTimers();
});

async function board(scope?: string) {
  render(<RunsOnCore scope={scope} />);
  await screen.findByTestId("runson-assignments");
  await waitFor(() => expect(screen.getByTestId("switchboard-engine-openrouter")).toBeTruthy());
}

describe("Runs on — paint and words", () => {
  it.each(["roster", "detection"] as const)("marks initial reads pending with %s first and preserves useful controls", async (first) => {
    let finishRoster!: (value: Roster) => void;
    let finishDetection!: (value: Detection) => void;
    m.readRoster.mockReturnValue(new Promise<Roster>((resolve) => { finishRoster = resolve; }));
    m.readDetection.mockReturnValue(new Promise<Detection>((resolve) => { finishDetection = resolve; }));
    speechState.readKind = "loading";
    const view = render(<RunsOnCore/>);
    const face = screen.getByTestId("runson-root");
    expect(face).toHaveAttribute("aria-busy", "true");
    expect(screen.getByRole("button", { name: "Find on LAN" })).toBeEnabled();
    await act(async () => { if (first === "roster") finishRoster(roster()); else finishDetection(detection()); });
    expect(face).toHaveAttribute("aria-busy", "true");
    if (first === "roster") expect(screen.getAllByTestId(/^switchboard-job-/)).toHaveLength(7);
    await act(async () => { if (first === "roster") finishDetection(detection()); else finishRoster(roster()); });
    expect(face).toHaveAttribute("aria-busy", "true");
    speechState.readKind = "ok";
    speechState.notSetUp = true;
    view.rerender(<RunsOnCore/>);
    expect(screen.getByTestId("runson-speech-setup")).toBeInTheDocument();
    expect(face).not.toHaveAttribute("aria-busy");
    speechState.notSetUp = false;
  });

  it.each(["roster", "detection"] as const)("clears initial pending state when the %s read fails", async (failed) => {
    if (failed === "roster") m.readRoster.mockRejectedValue(new Error("Roster offline"));
    else m.readDetection.mockRejectedValue(new Error("Detection offline"));
    render(<RunsOnCore/>);
    await waitFor(() => expect(screen.getByTestId("runson-root")).not.toHaveAttribute("aria-busy"));
    expect(m.readRoster).toHaveBeenCalled();
    expect(m.readDetection).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Find on LAN" })).toBeEnabled();
  });

  it("clears initial pending state when the speech read becomes unread", async () => {
    speechState.readKind = "loading";
    const view = render(<RunsOnCore/>);
    await screen.findByTestId("switchboard-engine-openrouter");
    expect(screen.getByTestId("runson-root")).toHaveAttribute("aria-busy", "true");
    speechState.readKind = "unread";
    view.rerender(<RunsOnCore/>);
    expect(screen.getByTestId("runson-root")).not.toHaveAttribute("aria-busy");
    expect(screen.queryByTestId("runson-speech-setup")).toBeNull();
  });

  it("paints the roster's jobs before the detection lands, then the engines fill in", async () => {
    let finish: (value: Detection) => void = () => {};
    m.readDetection.mockReturnValue(new Promise<Detection>((resolve) => (finish = resolve)));
    render(<RunsOnCore />);
    await screen.findByTestId("runson-assignments");
    expect(screen.getAllByTestId(/^switchboard-job-/)).toHaveLength(7);
    expect(screen.getByTestId("runson-fact").textContent).toBe("3 engines");
    expect(screen.queryByTestId("switchboard-engine-openrouter")).toBeNull();
    // Wires already draw from the roster: speech, thoughts, default.
    expect(screen.getAllByTestId("switchboard-wire").map((w) => w.getAttribute("data-job"))).toEqual([
      "speech_recognition",
      "thoughts_notes",
      "default",
    ]);
    await act(async () => finish(detection()));
    expect(await screen.findByTestId("switchboard-engine-openrouter")).toBeTruthy();
    expect(screen.getByTestId("runson-fact").textContent).toBe("4 engines");
  });

  it("draws one of five words per job, from the authority's fit (never reachability)", async () => {
    await board();
    const state = (id: string) => screen.getByTestId(`switchboard-job-${id}`).getAttribute("data-state");
    expect(state("meetings")).toBe("limited"); // q27 cannot do Calendar work
    expect(state("agents_tools")).toBe("ready");
    expect(state("thoughts_notes")).toBe("ready");
    // Engines grammar (2026-10-30): the status bar says what he has; the
    // job words are on the jobs themselves.
    expect(screen.getByTestId("runson-fact").textContent).toMatch(/^\d+ engines?$/);
    // Retired: no picker wells, no Adjust, no Use these, no summaries verb.
    for (const word of ["Use these", "Use this for summaries", "Adjust", "Cancel"]) {
      expect(screen.queryByRole("button", { name: word })).toBeNull();
    }
  });

  it("each card leads with what he gets and where it runs; task names are its details (PHILO-17 U16)", async () => {
    await board();
    const lead = (id: string) =>
      screen.getByTestId(`switchboard-job-${id}`).querySelector(".switchboard-job-name")?.textContent;
    // An own wire on this Mac; a LAN engine by its address; the default.
    expect(lead("thoughts_notes")).toBe("Answers and notes → Qwen 3.5 4B · on this Mac");
    expect(lead("speech_recognition")).toBe("Speech to text → Whisper small · on this Mac");
    expect(lead("meetings")).toBe("Meeting summaries → qwen3.8 27B · on 192.168.1.43");
    expect(lead("default")).toBe("Default engine → qwen3.8 27B · on 192.168.1.43");
    expect(lead("writing_dictation")).toBe("Dictation clean-up → qwen3.8 27B · on 192.168.1.43");
    expect(lead("background")).toContain("Background work → ");
    // Task ids leave the face for the card's details.
    const meetings = screen.getByTestId("switchboard-job-meetings");
    expect(meetings.getAttribute("title")).toBe("Deferred meeting analysis · Meeting title · Live meeting analysis");
    const face = screen.getByTestId("runson-assignments").querySelector(".switchboard")!.textContent ?? "";
    for (const gone of ["TASKS", "FOLLOWS DEFAULT", "EVERY JOB WITHOUT ITS OWN WIRE", "Default for AI work", "DEFERRED MEETING ANALYSIS", "THIS DEVICE ONLY"]) {
      expect(face).not.toContain(gone);
    }
    // A job that rides the default says so in plain words.
    expect(meetings.textContent).toContain("Uses default engine");
    expect(screen.getByTestId("switchboard-job-thoughts_notes").textContent).not.toContain("Uses default engine");
  });

  it("the summaries lead names the summary route, not the Meetings wire (Astra r1 M2)", async () => {
    // A local Meetings wire, and a cloud summary override: summaries leave
    // this Mac, so the lead must say where they go.
    const local = roster();
    local.rows = local.rows.map((r) =>
      r.id === "meetings"
        ? { ...r, inherited_from: "group", assignment: { revision: 1, entries: [Q4B], issues: [] }, expected_revision: 1 }
        : r,
    );
    m.readRoster.mockResolvedValue(local);
    const cloud = detection();
    cloud.summaryAssignment = { ...cloud.summaryAssignment!, profileId: "openrouter", profileRevision: 1, label: "OpenRouter", boundary: "cloud" };
    m.readDetection.mockResolvedValue(cloud);
    await board();
    const lead = () => screen.getByTestId("switchboard-job-meetings").querySelector(".switchboard-job-name")?.textContent;
    await waitFor(() => expect(lead()).toBe("Meeting summaries → OpenRouter · on openrouter.ai"));
  });

  it("withholds the summary route until detection says it; a failed read says not known with Try again (Astra r2 M1)", async () => {
    // A local Meetings wire: the lead must not borrow it while detection loads.
    const local = roster();
    local.rows = local.rows.map((r) =>
      r.id === "meetings"
        ? { ...r, inherited_from: "group", assignment: { revision: 1, entries: [Q4B], issues: [] }, expected_revision: 1 }
        : r,
    );
    m.readRoster.mockResolvedValue(local);
    let fail: (reason: unknown) => void = () => {};
    m.readDetection.mockReturnValueOnce(new Promise<Detection>((_, reject) => (fail = reject)));
    render(<RunsOnCore />);
    await screen.findByTestId("runson-assignments");
    const lead = () => screen.getByTestId("switchboard-job-meetings").querySelector(".switchboard-job-name")?.textContent;
    expect(lead()).toBe("Meeting summaries → checking…");
    await act(async () => fail(new Error("offline")));
    await waitFor(() => expect(lead()).toBe("Meeting summaries → not known"));
    expect(lead()).not.toContain("this Mac");
    // Try again reads detection again; the real route then lands.
    m.readDetection.mockResolvedValueOnce(detection());
    fireEvent.click(screen.getByTestId("runson-read-again"));
    await waitFor(() => expect(lead()).toBe("Meeting summaries → qwen3.8 27B · on 192.168.1.43"));
    expect(screen.queryByTestId("runson-read-again")).toBeNull();
  });

  it("summaries off: the lead says off", async () => {
    const off = detection();
    off.summaryAssignment = { ...off.summaryAssignment!, status: "off", profileId: null, profileRevision: null, label: null };
    m.readDetection.mockResolvedValue(off);
    await board();
    expect(screen.getByTestId("switchboard-job-meetings").querySelector(".switchboard-job-name")?.textContent).toBe(
      "Meeting summaries → off",
    );
  });

  it("a caller's scope opens on its job (hot wires)", async () => {
    await board("summary");
    expect(screen.getByTestId("switchboard-job-meetings").className).toContain("is-selected");
  });

  it("the selected job's Details fold stays selected when opened", async () => {
    await board("thoughts_notes");
    const row = screen.getByTestId("switchboard-job-thoughts_notes");
    const fold = within(row).getByText("Details").closest("details")!;
    fireEvent.click(fold.querySelector("summary")!);
    expect(row.className).toContain("is-selected");
    expect(fold.isConnected).toBe(true);
  });
});

describe("Runs on — a drop writes", () => {
  it("writes the job's whole chain with the row's own revision; Undo writes the previous chain back", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    await waitFor(() => expect(m.writeChain).toHaveBeenCalledTimes(1));
    expect(m.writeChain).toHaveBeenCalledWith({
      scope: { kind: "group", group_id: "thoughts_notes" },
      expectedRevision: 2,
      entries: [
        { profile_id: "q27", profile_revision: 1 },
        { profile_id: "q4b", profile_revision: 2 },
      ],
    });
    const receipt = await screen.findByTestId("runson-receipt");
    expect(receipt.textContent).toMatch(/^Changed at \d\d:\d\d · Answers and notes → qwen3.8 27B$/);
    // UX-CANON A.9: no host chip on the status bar; the engine's fold names it.
    expect(screen.queryByTestId("runson-egress")).toBeNull();
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() => expect(m.writeChain).toHaveBeenCalledTimes(2));
    // C1: Undo is a CAS write against the revision the patch produced (7).
    expect(m.writeChain).toHaveBeenLastCalledWith({
      scope: { kind: "group", group_id: "thoughts_notes" },
      expectedRevision: 7,
      entries: [{ profile_id: "q4b", profile_revision: 2 }],
    });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Undone at/));
  });

  it("⌥ adds a fallback after the first", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter", altKey: true });
    await waitFor(() => expect(m.writeChain).toHaveBeenCalled());
    expect(m.writeChain.mock.calls[0][0].entries.map((e: { profile_id: string }) => e.profile_id)).toEqual(["q4b", "q27"]);
    expect((await screen.findByTestId("runson-receipt")).textContent).toContain("· Fallback");
  });

  it("Meetings also writes the exact summary row the queue reads; Undo restores inheritance (C2)", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-meetings"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-openrouter"), { key: "Enter" });
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(1));
    expect(m.writeChain).toHaveBeenCalledWith({
      scope: { kind: "group", group_id: "meetings" },
      expectedRevision: 0,
      entries: [{ profile_id: "openrouter", profile_revision: 1 }],
    });
    expect(m.summary.mock.calls[0][0]).toMatchObject({
      expectedAssignmentRevision: 0,
      profileId: "openrouter",
      profileRevision: 1,
    });
    // Undo of a first patch: the group follows the default again (clear at
    // the revision the patch produced), and the summary row, which was
    // INHERITED before (has_override false; the producer said `assigned`),
    // is cleared at the revision our own write produced, never re-written
    // as an explicit override of the inherited engine.
    fireEvent.click(await screen.findByTestId("runson-undo"));
    await waitFor(() => expect(m.clearChain).toHaveBeenCalledTimes(2));
    expect(m.clearChain.mock.calls[0][0]).toEqual({
      scope: { kind: "group", group_id: "meetings" },
      capabilityId: "meeting.deferred_analysis",
      expectedRevision: 7,
    });
    expect(m.clearChain.mock.calls[1][0]).toEqual({
      scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
      capabilityId: "meeting.deferred_analysis",
      expectedRevision: 5,
    });
    expect(m.summary).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Undone at \d\d:\d\d · Meeting summaries$/));
  });

  it("Meetings Undo of an OWN summary row gives it its own engine back, and says a refusal (C2, A.10)", async () => {
    const owned = roster();
    owned.tasks = owned.tasks.map((t) => (t.id === "meeting.deferred_analysis" ? { ...t, has_override: true } : t));
    m.readRoster.mockResolvedValue(owned);
    const det = detection();
    det.summaryAssignment = { ...det.summaryAssignment!, assignmentRevision: 4, profileId: "q4b", profileRevision: 2 };
    m.readDetection.mockResolvedValue(det);
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-meetings"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-openrouter"), { key: "Enter" });
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(1));
    expect(m.summary.mock.calls[0][0]).toMatchObject({ expectedAssignmentRevision: 4 });
    m.summary.mockResolvedValueOnce({ status: "conflict", state: "CONFLICT", plainReason: "", summaryAssignment: null });
    fireEvent.click(await screen.findByTestId("runson-undo"));
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(2));
    expect(m.summary.mock.calls[1][0]).toMatchObject({ expectedAssignmentRevision: 5, profileId: "q4b", profileRevision: 2 });
    await waitFor(() =>
      expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Undone at .* · Meeting summaries · Summaries changed elsewhere$/),
    );
  });

  it("two Meetings patches, Undo, Undo: inheritance restored, no CHANGED ELSEWHERE (M3 r2)", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-meetings"));
    // After the first patch the roster says Meetings and its summary row are
    // its own (the real producer after a write); the patch re-reads it.
    const owned = roster();
    owned.rows[4] = { ...owned.rows[4], inherited_from: "group", expected_revision: 7,
      assignment: { revision: 7, entries: [{ ...Q27, profile_id: "openrouter", label: "OpenRouter" }], issues: [] } };
    owned.tasks = owned.tasks.map((t) => (t.id === "meeting.deferred_analysis" ? { ...t, has_override: true } : t));
    const reads = m.readRoster.mock.calls.length;
    m.readRoster.mockResolvedValue(owned);
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-openrouter"), { key: "Enter" });
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(1));
    await screen.findByTestId("runson-undo");
    await waitFor(() => expect(m.readRoster.mock.calls.length).toBeGreaterThan(reads));
    await waitFor(() => expect(screen.getAllByTestId("switchboard-wire").some((w) => w.getAttribute("data-job") === "meetings")).toBe(true));
    m.summary.mockResolvedValueOnce({
      status: "succeeded", state: "READY", plainReason: "",
      summaryAssignment: { ...detection().summaryAssignment!, profileId: "q27", assignmentRevision: 6 },
    });
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(2));
    expect(m.summary.mock.calls[1][0]).toMatchObject({ expectedAssignmentRevision: 5, profileId: "q27" });
    // Undo 1: the summary row gets its own engine back (OpenRouter), CAS 6,
    // and produces 9; Undo 2 must clear it at 9, not at the stale 5.
    m.summary.mockResolvedValueOnce({
      status: "succeeded", state: "READY", plainReason: "",
      summaryAssignment: { ...detection().summaryAssignment!, profileId: "openrouter", assignmentRevision: 9 },
    });
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() => expect(m.summary).toHaveBeenCalledTimes(3));
    expect(m.summary.mock.calls[2][0]).toMatchObject({ expectedAssignmentRevision: 6, profileId: "openrouter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Undone at .* · Meeting summaries$/));
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() =>
      expect(m.clearChain).toHaveBeenCalledWith({
        scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
        capabilityId: "meeting.deferred_analysis",
        expectedRevision: 9,
      }),
    );
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Undone at .* · Meeting summaries$/));
    expect(screen.getByTestId("runson-receipt").textContent?.toLowerCase()).not.toContain("changed elsewhere");
    expect(screen.queryByTestId("runson-undo")).toBeNull();
  });

  it("Undo refuses when another writer moved the row since the patch (C1: no lost update)", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    await waitFor(() => expect(m.writeChain).toHaveBeenCalledTimes(1));
    m.writeChain.mockRejectedValueOnce(
      new ApiError(409, "Assignment changed.", { code: "inference_assignment_revision_conflict" }),
    );
    fireEvent.click(await screen.findByTestId("runson-undo"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("Could not undo Answers and notes · It changed elsewhere first"));
    expect(m.writeChain.mock.calls[1][0].expectedRevision).toBe(7);
    // The entry is gone: no second Undo can overwrite the other writer.
    expect(screen.queryByTestId("runson-undo")).toBeNull();
    expect(m.writeChain).toHaveBeenCalledTimes(2);
  });

  it("409: re-reads, redraws, and says it changed elsewhere first (no blind retry)", async () => {
    await board();
    const reads = m.readRoster.mock.calls.length;
    m.writeChain.mockRejectedValueOnce(
      new ApiError(409, "Assignment changed.", { code: "inference_assignment_revision_conflict" }),
    );
    fireEvent.click(screen.getByTestId("switchboard-job-agents_tools"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("Could not change Custom tasks · It changed elsewhere first"));
    expect(m.writeChain).toHaveBeenCalledTimes(1);
    expect(m.readRoster.mock.calls.length).toBeGreaterThan(reads);
  });

  it("refuses what the job cannot take, with the reason in the foot and no write", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-speech_recognition"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    expect((await screen.findByTestId("runson-receipt")).textContent).toMatch(/^Could not put Speech to text on .+ · Speech engines only · Nothing changed$/);
    fireEvent.click(screen.getByTestId("switchboard-job-agents_tools"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q4b"), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Could not put Custom tasks on .+ · Without agents · Nothing changed$/));
    expect(m.writeChain).not.toHaveBeenCalled();
  });
});

// Recorded through the real MeetingWebServer ASGI HTTP route, adopted kernel
// and a controlled provider leaf (2026-10-14, record_probe.py). This is a wire
// replay for the face; it does not claim physical model inference.
const completedProbe = {
  "state": "READY",
  "ok": true,
  "capabilityId": "ask.answer",
  "group": "thoughts_notes",
  "testedTask": "Answers",
  "sampleInput": "What is 2 + 2?",
  "sampleOutput": "4",
  "emptyOutput": false,
  "outcome": "succeeded",
  "reasonCode": "",
  "engine": "configured_local_engine",
  "model": "protocol-provider",
  "boundary": "local",
  "host": "THIS DEVICE",
  "latencyMs": 84,
  "routePlanId": "irp_e8bb2f643ad5289e19f52fe528103323b044663f4377f4545a58f8465efebc5c",
  "executionId": "ire_b805ab8bcb94451c644173a89eed2f7a",
  "operationId": "routeprobed158b5bf697eefcf66792371",
  "legs": [
    {
      "ordinal": 1,
      "profileId": "protocol-provider",
      "deploymentRevisionId": "dep2_660d3f8ef6f5318ddbecbb96175012f6514a1533d44ccd3fe122d4e1b3db7ff8",
      "boundary": "local",
      "status": "attempted",
      "disposition": ""
    }
  ],
  "allModelsFailed": false
};
const blankProbe = {
  "state": "READY",
  "ok": true,
  "capabilityId": "ask.answer",
  "group": "thoughts_notes",
  "testedTask": "Answers",
  "sampleInput": "What is 2 + 2?",
  "sampleOutput": "",
  "emptyOutput": true,
  "outcome": "succeeded",
  "reasonCode": "",
  "engine": "configured_local_engine",
  "model": "protocol-provider",
  "boundary": "local",
  "host": "THIS DEVICE",
  "latencyMs": 72,
  "routePlanId": "irp_4582b839c9be7be85ddf467be97aa8c9188c910fe22d7b6ed14805251e8b3d26",
  "executionId": "ire_93675ab93f4f4ea05349d0a5b107f4ba",
  "operationId": "routeprobe901507777ce89b366c467522",
  "legs": [
    {
      "ordinal": 1,
      "profileId": "protocol-provider",
      "deploymentRevisionId": "dep2_660d3f8ef6f5318ddbecbb96175012f6514a1533d44ccd3fe122d4e1b3db7ff8",
      "boundary": "local",
      "status": "attempted",
      "disposition": ""
    }
  ],
  "allModelsFailed": false
};

describe("Runs on — Try it", () => {
  it("the first local press runs its task and lands the actual sample on the job", async () => {
    m.taskProbe.mockResolvedValue(completedProbe);
    await board();
    fireEvent.click(screen.getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(screen.getByTestId("runson-trial-state-thoughts_notes").textContent).toBe("Completed · Answers · protocol-provider · 84 MS"));
    expect(m.taskProbe).toHaveBeenCalledWith("ask.answer", undefined, ["q4b"]);
    expect(screen.getByTestId("runson-trial-input-thoughts_notes").textContent).toBe(completedProbe.sampleInput);
    expect(screen.getByTestId("runson-trial-output-thoughts_notes").textContent).toBe(completedProbe.sampleOutput);
    expect(m.probe).not.toHaveBeenCalled();
  });

  it("the first remote press names its destination and starts the real job, without a footer confirmation", async () => {
    m.taskProbe.mockResolvedValue(completedProbe);
    await board();
    const row = screen.getByTestId("switchboard-job-meetings");
    expect(within(row).getByTestId("runson-trial-egress-meetings").textContent).toBe("192.168.1.43");
    fireEvent.click(within(row).getByTestId("runson-try-meetings"));
    await waitFor(() => expect(m.taskProbe).toHaveBeenCalledWith("meeting.deferred_analysis", true, ["q27"]));
    expect(screen.queryByTestId("runson-try-confirm")).toBeNull();
    expect(m.probe).not.toHaveBeenCalled();
    expect(screen.queryByTestId("runson-egress")).toBeNull();
    expect(await screen.findByTestId("runson-trial-output-meetings")).toBeTruthy();
  });

  it.each([
    ["writing_dictation", "speech.rewrite"],
    ["thoughts_notes", "ask.answer"],
    ["meetings", "meeting.deferred_analysis"],
    ["agents_tools", "recipe.run"],
    ["background", "background.rails_summary"],
  ])("%s tests its bounded real task %s", async (job, capability) => {
    m.taskProbe.mockResolvedValue(completedProbe);
    await board();
    fireEvent.click(screen.getByTestId(`runson-try-${job}`));
    await waitFor(() => expect(m.taskProbe).toHaveBeenCalledTimes(1));
    expect(m.taskProbe.mock.calls[0][0]).toBe(capability);
    expect(m.probe).not.toHaveBeenCalled();
  });

  it("shows every known remote fallback before the press and binds the full chain", async () => {
    m.taskProbe.mockResolvedValue(completedProbe);
    const routed = roster();
    routed.rows[1].assignment!.entries = [Q4B, Q27, { ...Q27, profile_id: "openrouter", label: "OpenRouter", boundary: "cloud" }];
    m.readRoster.mockResolvedValue(routed);
    await board();
    const row = screen.getByTestId("switchboard-job-thoughts_notes");
    expect(within(row).getAllByTestId("runson-trial-egress-thoughts_notes").map((chip) => chip.textContent)).toEqual(["192.168.1.43", "openrouter.ai"]);
    fireEvent.click(within(row).getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(m.taskProbe).toHaveBeenCalledWith("ask.answer", true, ["q4b", "q27", "openrouter"]));
  });

  it("the Meetings trial binds the actual summary head instead of the group's wire", async () => {
    m.taskProbe.mockResolvedValue(completedProbe);
    const det = detection();
    det.summaryAssignment = { ...det.summaryAssignment!, profileId: "openrouter", profileRevision: 1, label: "OpenRouter", boundary: "cloud" };
    m.readDetection.mockResolvedValue(det);
    await board();
    expect(screen.getByTestId("runson-trial-egress-meetings").textContent).toBe("openrouter.ai");
    fireEvent.click(screen.getByTestId("runson-try-meetings"));
    await waitFor(() => expect(m.taskProbe).toHaveBeenCalledWith("meeting.deferred_analysis", true, ["openrouter"]));
  });

  it("a server refusal stays on the job and never asks for another confirmation", async () => {
    m.taskProbe.mockResolvedValue({ state: "REFUSED", ok: false, reasonCode: "route_probe_assignment_changed", legs: [] });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-meetings"));
    await waitFor(() => expect(screen.getByTestId("runson-trial-state-meetings").textContent).toBe("Not tried · Route changed"));
    expect(m.taskProbe).toHaveBeenCalledTimes(1);
    expect(screen.queryByTestId("runson-try-confirm")).toBeNull();
  });

  it("the displayed binding compares job, engine, destination and revision", async () => {
    const { consentHolds, consentHost } = await import("../useRunsOn");
    const engine = { key: "q27", host: "192.168.1.43", baseUrl: "http://192.168.1.43:8080/v1", profileRevision: 2 } as never;
    const consent = { job: "meetings", engineKey: "q27", engineHost: consentHost(engine), engineRevision: 2, host: "192.168.1.43", scope: "local" as const };
    expect(consentHolds(consent, "meetings", engine)).toBe(true);
    for (const changed of [{ host: "192.168.1.99" }, { baseUrl: "http://10.0.0.9/v1" }, { key: "other" }, { profileRevision: 3 }]) {
      expect(consentHolds(consent, "meetings", { ...(engine as object), ...changed } as never)).toBe(false);
    }
    expect(consentHolds(consent, "agents_tools", engine)).toBe(false);
  });

  it("a remote address is disclosed even when the engine was labelled local", async () => {
    const { offMachine } = await import("../model");
    expect(offMachine({ kind: "local", emblem: "MAC", host: "127.0.0.1.", baseUrl: "http://127.0.0.1.:8080/v1" } as never)).toBe(true);
    expect(offMachine({ kind: "local", emblem: "MAC", host: "THIS DEVICE", baseUrl: "http://127.0.0.1:8080/v1" } as never)).toBe(false);
  });

  it("a stale displayed destination refuses before dispatch", async () => {
    const { useRunsOn } = await import("../useRunsOn");
    const view = renderHook(() => useRunsOn());
    await waitFor(() => expect(view.result.current.trialBindingsForJob("meetings")[0]?.host).toBe("192.168.1.43"));
    const shown = view.result.current.trialBindingsForJob("meetings");
    const moved = detection();
    moved.engines = moved.engines.map((engine) => engine.profileId === "q27" ? { ...engine, host: "192.168.1.99", baseUrl: "http://192.168.1.99:8080/v1" } : engine);
    m.readDetection.mockResolvedValue(moved);
    act(() => view.result.current.readAgain());
    await waitFor(() => expect(view.result.current.trialBindingsForJob("meetings")[0]?.host).toBe("192.168.1.99"));
    act(() => view.result.current.tryJob("meetings", shown));
    expect(m.taskProbe).not.toHaveBeenCalled();
    expect(view.result.current.results.meetings.tokens).toEqual(["Not tried", "Route changed"]);
  });

  it("a successful empty output is neutral Completed, never Broken / inference succeeded", async () => {
    m.taskProbe.mockResolvedValue(blankProbe);
    await board();
    fireEvent.click(screen.getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(screen.getByTestId("runson-trial-state-thoughts_notes").textContent).toContain("No text returned"));
    const result = screen.getByTestId("runson-trial-state-thoughts_notes");
    expect(result.textContent).toContain("Completed");
    expect(result.textContent).not.toMatch(/BROKEN|inference succeeded/i);
    expect(result.closest("[data-tone]")?.getAttribute("data-tone")).toBe("idle");
  });

  it.each(["board", "list"])("%s keeps loading and one request in the same job row", async (layout) => {
    const rect = vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({ width: layout === "list" ? 393 : 1000, height: 600, top: 0, left: 0, right: 1000, bottom: 600, x: 0, y: 0, toJSON: () => ({}) });
    let finish!: (value: typeof completedProbe) => void;
    m.taskProbe.mockReturnValue(new Promise((resolve) => { finish = resolve; }));
    try {
      render(<RunsOnCore scope="thoughts_notes" />);
      const button = await screen.findByTestId("runson-try-thoughts_notes");
      fireEvent.click(button);
      expect(button.closest(".switchboard-job")?.getAttribute("data-job-id")).toBe("thoughts_notes");
      expect(button.getAttribute("aria-busy")).toBe("true");
      expect(button.hasAttribute("disabled")).toBe(true);
      expect(screen.getByTestId("runson-trial-state-thoughts_notes").textContent).toBe("Trying");
      fireEvent.click(button);
      expect(m.taskProbe).toHaveBeenCalledTimes(1);
      await act(async () => finish(completedProbe));
      expect(button.getAttribute("aria-busy")).toBeNull();
      expect(screen.getByTestId("runson-trial-output-thoughts_notes").textContent).toBe(completedProbe.sampleOutput);
    } finally { rect.mockRestore(); }
  });

  it("the default engine has no trial", async () => {
    await board();
    expect(screen.queryByTestId("runson-try-default")).toBeNull();
  });

  it("a probe with no latency shows no ms token (A.8)", async () => {
    m.taskProbe.mockResolvedValue({ ...completedProbe, latencyMs: 0 });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(screen.getByTestId("runson-trial-state-thoughts_notes").textContent).toBe("Completed · Answers · protocol-provider"));
  });

  it("Speech keeps its Stop action, then shows Transcribing until the actual text returns", async () => {
    let finish!: (text: string) => void;
    m.startCapture.mockResolvedValue(undefined);
    m.stopAndTranscribe.mockReturnValue(new Promise((resolve) => { finish = resolve; }));
    await board();
    const button = screen.getByTestId("runson-try-speech_recognition");
    fireEvent.click(button);
    await waitFor(() => expect(button.textContent).toBe("Stop"));
    fireEvent.click(button);
    expect(button.getAttribute("aria-busy")).toBe("true");
    expect(screen.getByTestId("runson-trial-state-speech_recognition").textContent).toBe("Transcribing");
    fireEvent.click(button);
    expect(m.startCapture).toHaveBeenCalledTimes(1);
    await act(async () => finish("freeze the old ledger on nov 5"));
    expect(screen.getByTestId("runson-trial-state-speech_recognition").textContent).toMatch(/^HEARD: "freeze the old ledger on nov 5"( · \d+ MS)?$/);
    expect(m.probe).not.toHaveBeenCalled();
    expect(m.taskProbe).not.toHaveBeenCalled();
  });
});

describe("Runs on — speech not set up (PHILO-17)", () => {
  it.each(["success", "failure"])("closing a transcribing host leaves a newer capture alone after late %s", async (outcome) => {
    let finish!: (text: string) => void;
    let fail!: (cause: Error) => void;
    m.startCapture.mockResolvedValue(undefined);
    m.stopAndTranscribe.mockReturnValue(new Promise<string>((resolve, reject) => { finish = resolve; fail = reject; }));
    const old = renderHook(() => useRunsOn());
    act(() => old.result.current.tryJob("speech_recognition", []));
    await waitFor(() => expect(old.result.current.listening).toBe(true));
    act(() => old.result.current.tryJob("speech_recognition", []));
    expect(m.stopAndTranscribe).toHaveBeenCalledTimes(1);
    expect(old.result.current.listening).toBe(false);

    // The first hold has ended at Stop; this successful host now owns the
    // shared mic while the previous transcription response is pending.
    const current = renderHook(() => useRunsOn());
    act(() => current.result.current.tryJob("speech_recognition", []));
    await waitFor(() => expect(current.result.current.listening).toBe(true));
    old.unmount();
    expect(m.cancelCapture).not.toHaveBeenCalled();
    await act(async () => {
      if (outcome === "success") finish("Earlier transcription");
      else fail(new Error("Earlier transcription failed"));
    });
    expect(m.cancelCapture).not.toHaveBeenCalled();
    expect(current.result.current.listening).toBe(true);
    current.unmount();
    expect(m.cancelCapture).toHaveBeenCalledTimes(1);
  });

  it("releases this host's live capture when it closes without transcribing", async () => {
    m.startCapture.mockResolvedValue(undefined);
    const host = renderHook(() => useRunsOn());
    act(() => host.result.current.tryJob("speech_recognition", []));
    await waitFor(() => expect(host.result.current.listening).toBe(true));
    host.unmount();
    expect(m.cancelCapture).toHaveBeenCalledTimes(1);
    expect(m.stopAndTranscribe).not.toHaveBeenCalled();
  });

  it("releases a capture that finishes starting after this host closes", async () => {
    let started!: () => void;
    m.startCapture.mockReturnValue(new Promise<void>((resolve) => { started = resolve; }));
    const host = renderHook(() => useRunsOn());
    act(() => host.result.current.tryJob("speech_recognition", []));
    host.unmount();
    expect(m.cancelCapture).not.toHaveBeenCalled();
    await act(async () => started());
    expect(m.cancelCapture).toHaveBeenCalledTimes(1);
    expect(m.stopAndTranscribe).not.toHaveBeenCalled();
  });

  it("closing idle or refused hosts leaves another host's capture alone", async () => {
    m.startCapture.mockResolvedValueOnce(undefined).mockRejectedValueOnce(new Error("floor held"));
    const owner = renderHook(() => useRunsOn());
    act(() => owner.result.current.tryJob("speech_recognition", []));
    await waitFor(() => expect(owner.result.current.listening).toBe(true));
    const idle = renderHook(() => useRunsOn());
    idle.unmount();
    const refused = renderHook(() => useRunsOn());
    act(() => refused.result.current.tryJob("speech_recognition", []));
    await waitFor(() => expect(refused.result.current.trying).toBeNull());
    refused.unmount();
    expect(m.cancelCapture).not.toHaveBeenCalled();
    expect(m.stopAndTranscribe).not.toHaveBeenCalled();
    owner.unmount();
    expect(m.cancelCapture).toHaveBeenCalledTimes(1);
  });

  afterEach(() => {
    speechState.notSetUp = false;
  });

  it("the Speech job keeps its setup row after Try it answers", async () => {
    speechState.notSetUp = true;
    m.startCapture.mockResolvedValue(undefined);
    m.stopAndTranscribe.mockRejectedValue(new Error("no speech model"));
    await board();
    expect(screen.getByTestId("runson-speech-setup").textContent).toBe("Speech is not set up");
    fireEvent.click(screen.getByTestId("runson-try-speech_recognition"));
    await waitFor(() => expect(screen.getByTestId("runson-try-speech_recognition").textContent).toBe("Stop"));
    fireEvent.click(screen.getByTestId("runson-try-speech_recognition"));
    await waitFor(() => expect(m.stopAndTranscribe).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByTestId("runson-try-speech_recognition").textContent).toBe("Try it"));
    expect(screen.getByTestId("runson-speech-setup")).toBeTruthy();
  });
});

describe("Runs on — FOUND, downloads, the add row", () => {
  it("a cold desk offers discovery before downloads and job assignment", async () => {
    const cold = roster();
    cold.rows = cold.rows.map((item) => ({ ...item, status: "unassigned", assignment: { revision: 0, entries: [], issues: [] } }));
    m.readRoster.mockResolvedValue(cold);
    const det = detection();
    det.engines = det.engines.filter((engine) => engine.kind === "preset");
    m.readDetection.mockResolvedValue(det);
    const view = render(<RunsOnCore />);
    await screen.findByTestId("runson-engines-empty");
    const find = screen.getByRole("button", { name: "Find on LAN" });
    // W1-KIT: Add an engine (the verb that makes an engine) is the one
    // primary on a cold desk too; Find on LAN is a plain verb beside it.
    expect(find.className).toContain("btn--secondary");
    expect(screen.getByTestId("concierge-add-engine").className).toContain("btn--primary");
    await screen.findByTestId("runson-download-preset:vision");
    expect(view.container.querySelector<HTMLDetailsElement>(".runson-downloads")?.open).toBe(false);
    expect(view.container.querySelectorAll("[data-job-id]")).toHaveLength(0);
    expect(m.discoverLan).not.toHaveBeenCalled();
  });
  it("Find on LAN adds transient Found rows and leaves adoption to Use it", async () => {
    m.discoverLan.mockResolvedValue({
      engines: [{
        id: "lan:192.168.1.43:8080:qwen3.8-27b", kind: "lan", name: "qwen3.8-27b",
        host: "192.168.1.43", state: "READY", legacyLabel: "qwen3.8-27b",
        baseUrl: "http://192.168.1.43:8080/v1", found: true,
      }],
      checkedAt: "2026-10-13T10:00:00Z", partial: false, unavailable: false, hostsChecked: 254,
    });
    m.define.mockResolvedValue({ profileId: "engine-192-168-1-43-8080", profileRevision: 1 });
    await board();
    fireEvent.click(screen.getByTestId("runson-find-lan"));
    await waitFor(() => expect(m.discoverLan).toHaveBeenCalledTimes(1));
    // Engines grammar: a found row in the Engines list; the address is a
    // fact row of its fold, said once (no host chip on the row, A.9).
    const found = await screen.findByTestId("runson-engine-lan:192.168.1.43:8080:qwen3.8-27b");
    expect(found.querySelector(".kit-listrow-meta")?.textContent).toBe("Your network");
    fireEvent.click(found.querySelector(".kit-listrow-main") as HTMLElement);
    expect(within(found).getByTestId("runson-fold-goes").textContent).toContain("http://192.168.1.43:8080/v1");
    expect(found.textContent?.match(/192\.168\.1\.43/g)).toHaveLength(1);
    expect(screen.getByTestId("runson-receipt").textContent).toBe("Found on the LAN");
    fireEvent.click(within(found).getByRole("button", { name: "Use it" }));
    await waitFor(() => expect(m.define).toHaveBeenCalledWith(expect.objectContaining({
      endpoint: "http://192.168.1.43:8080/v1", model: "qwen3.8-27b",
    })));
  });

  it("Find on LAN says when the bounded scan finds no engine", async () => {
    m.discoverLan.mockResolvedValue({ engines: [], checkedAt: "2026-10-13T10:00:00Z", partial: true, unavailable: false, hostsChecked: 254 });
    await board();
    fireEvent.click(screen.getByTestId("runson-find-lan"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("No engine found on the LAN · Partial"));
  });

  it("Find on LAN does not duplicate a saved endpoint with the same URL and model", async () => {
    const saved = detection();
    saved.engines = [...saved.engines, {
      id: "lan:saved-qwen", kind: "lan", name: "Qwen3.8 27B", legacyLabel: "My LAN server",
      host: "192.168.1.43", state: "READY", profileId: "saved-qwen", profileRevision: 1,
      baseUrl: "http://192.168.1.43:8080/v1/",
    }];
    m.readDetection.mockResolvedValue(saved);
    m.discoverLan.mockResolvedValue({
      engines: [{
        id: "lan:192.168.1.43:8080:qwen3.8-27b", kind: "lan", name: "qwen3.8-27b",
        host: "192.168.1.43", state: "READY", legacyLabel: "qwen3.8-27b",
        baseUrl: "http://192.168.1.43:8080/v1", found: true,
      }],
      checkedAt: "2026-10-13T10:00:00Z", partial: false, unavailable: false, hostsChecked: 254,
    });
    await board();
    fireEvent.click(screen.getByTestId("runson-find-lan"));
    await waitFor(() => expect(m.discoverLan).toHaveBeenCalledTimes(1));
    expect(screen.queryByTestId("runson-engine-lan:192.168.1.43:8080:qwen3.8-27b")).toBeNull();
    expect(screen.getByTestId("runson-engine-saved-qwen")).toBeTruthy();
  });

  it("Find on LAN keeps rows when the initial detection read finishes later", async () => {
    let finish: (value: Detection) => void = () => {};
    m.readDetection.mockReturnValue(new Promise<Detection>((resolve) => { finish = resolve; }));
    m.discoverLan.mockResolvedValue({
      engines: [{
        id: "lan:192.168.1.43:8080:qwen3.8-27b", kind: "lan", name: "qwen3.8-27b",
        host: "192.168.1.43", state: "READY", legacyLabel: "qwen3.8-27b",
        baseUrl: "http://192.168.1.43:8080/v1", found: true,
      }],
      checkedAt: "2026-10-13T10:00:00Z", partial: false, unavailable: false, hostsChecked: 254,
    });
    render(<RunsOnCore />);
    await screen.findByTestId("runson-assignments");
    fireEvent.click(screen.getByTestId("runson-find-lan"));
    await waitFor(() => expect(m.discoverLan).toHaveBeenCalledTimes(1));
    await act(async () => finish(detection()));
    expect(await screen.findByTestId("runson-engine-lan:192.168.1.43:8080:qwen3.8-27b")).toBeTruthy();
  });

  it("Find on LAN names a failed discovery", async () => {
    m.discoverLan.mockRejectedValue(new Error("offline"));
    await board();
    fireEvent.click(screen.getByTestId("runson-find-lan"));
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("LAN search failed"));
    expect(screen.getByTestId("runson-receipt").getAttribute("data-tone")).toBe("danger");
  });

  it("FOUND → Use it adds the engine through the Model Library; it joins with no wire", async () => {
    m.define.mockResolvedValue({ profileId: "engine-127-0-0-1-11434", profileRevision: 1 });
    await board();
    // Betterment E2: a loopback server is on this Mac, and the caption says so.
    expect(screen.getByTestId("runson-found").querySelector(".kit-listday-label")?.textContent).toBe("Found on this Mac");
    expect(screen.getByTestId("runson-found-engines").textContent).toBe("1 found on this Mac");
    const found = screen.getByTestId("runson-engine-local:ollama:11434:llama3.3");
    const reads = m.readDetection.mock.calls.length;
    fireEvent.click(within(found).getByRole("button", { name: "Use it" }));
    await waitFor(() => expect(m.define).toHaveBeenCalledTimes(1));
    expect(m.define.mock.calls[0][0]).toMatchObject({ endpoint: "http://127.0.0.1:11434/v1", model: "llama3.3" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Added at \d\d:\d\d · Llama 3.3 8B$/));
    expect(m.readDetection.mock.calls.length).toBeGreaterThan(reads);
    expect(m.writeChain).not.toHaveBeenCalled();
  });

  it("a Download names the internet host, never THIS DEVICE, and fills the bar in place", async () => {
    m.download.mockResolvedValue({ jobId: "acq-1", presetId: "vision", progress: { received: 0, total: 0 } });
    m.readAcquisition
      .mockResolvedValueOnce({ state: "downloading", percent: 40 })
      .mockResolvedValue({ state: "ready", percent: 100 });
    await board();
    // Engines grammar: a row of the Download a local model fold; its fold
    // names the internet host it downloads from.
    const plate = screen.getByTestId("runson-engine-preset:vision");
    fireEvent.click(plate.querySelector(".kit-listrow-main") as HTMLElement);
    expect(within(plate).getByTestId("runson-fold-goes").textContent).toBe("Downloads fromhuggingface.co");
    expect(plate.textContent?.toLowerCase()).not.toContain("this device");
    fireEvent.click(within(plate).getByRole("button", { name: "Download" }));
    await waitFor(() => expect(m.download).toHaveBeenCalledWith("vision"));
    // In flight, it is a row of the Engines list with the bar along its foot.
    await waitFor(
      () => expect((screen.getByTestId("runson-engine-preset:vision").querySelector(".kit-listrow-progress") as HTMLElement | null)?.style.width).toBe("40%"),
      { timeout: 4000 },
    );
    expect(screen.getByTestId("runson-engine-state-preset:vision").textContent).toBe("Downloading 40 %");
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^Downloaded at/), { timeout: 4000 });
    expect(m.readAcquisition).toHaveBeenCalledWith("acq-1");
  }, 10_000);

  it("a failed download keeps BROKEN and its reason until retried (V3)", async () => {
    m.download.mockResolvedValue({ jobId: "acq-2", presetId: "vision", progress: { received: 0, total: 0 } });
    m.readAcquisition.mockResolvedValue({ state: "failed", percent: 12, error: "model_download_network" });
    await board();
    const plate = screen.getByTestId("runson-engine-preset:vision");
    fireEvent.click(within(plate).getByRole("button", { name: "Download" }));
    await waitFor(
      () => expect(screen.getByTestId("runson-receipt").textContent).toBe("Download stopped · Qwen 3.5 4B vision file · Network"),
      { timeout: 4000 },
    );
    const state = () => screen.getByTestId("runson-engine-state-preset:vision");
    expect(state().textContent).toBe("Download stopped");
    expect(state().getAttribute("data-tone")).toBe("fail");
    expect(screen.getByTestId("runson-engine-preset:vision").textContent).not.toContain("Not downloaded");
    // A retry clears the reason.
    m.readAcquisition.mockResolvedValue({ state: "downloading", percent: 30, error: null });
    fireEvent.click(within(screen.getByTestId("runson-engine-preset:vision")).getByRole("button", { name: "Download" }));
    await waitFor(() => expect(state().textContent?.toLowerCase()).not.toContain("stopped"));
  }, 10_000);

  it("the Add row's refusal is tokens, never the server's sentence (A.3)", async () => {
    m.check.mockResolvedValue({ ok: false, models: [], detail: "Nothing answers at this address." });
    await board();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-lan")); // Betterment E4: the kind first
    const row = screen.getByTestId("concierge-add-engine-row");
    fireEvent.change(within(row).getAllByRole("textbox")[0], { target: { value: "http://127.0.0.1:9/v1" } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await waitFor(() => expect(screen.getByTestId("concierge-add-reason").textContent).toBe("127.0.0.1:9"));
    expect(row.textContent).toContain("Unreachable");
    expect(row.textContent).not.toContain("Nothing answers");
  });

  it("Add an engine: address + Check inline, then Add through define-endpoint; the Check answer stays a token", async () => {
    m.check.mockResolvedValue({ ok: true, models: ["stub-model"], detail: "", tools: "no" });
    m.define.mockResolvedValue({ profileId: "engine-x", profileRevision: 1 });
    await board();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.click(screen.getByTestId("runson-kind-lan")); // Betterment E4: the kind first
    const row = screen.getByTestId("concierge-add-engine-row");
    fireEvent.change(within(row).getAllByRole("textbox")[0], { target: { value: "http://10.0.0.5:8080/v1" } });
    expect(screen.getByTestId("concierge-add-egress").textContent).toContain("10.0.0.5:8080");
    expect(screen.queryByTestId("concierge-add-use")).toBeNull();
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await waitFor(() => expect(screen.getByTestId("concierge-add-pick").getAttribute("data-model")).toBe("stub-model"));
    expect(screen.getByTestId("concierge-add-tools").textContent).toBe("No tools");
    fireEvent.click(screen.getByTestId("concierge-add-use"));
    await waitFor(() => expect(m.define).toHaveBeenCalled());
    expect(m.define.mock.calls[0][0]).toMatchObject({ endpoint: "http://10.0.0.5:8080/v1", model: "stub-model" });
    expect(m.summary).not.toHaveBeenCalled(); // joins the column; no assignment
    // Betterment E3: the picker stays, the used model says ADDED.
    await waitFor(() => expect(within(screen.getByTestId("concierge-add-pick")).getByText("Added")).toBeTruthy());
  });
});

// Betterment E5 (DECISIONS #8): the drag switchboard these tests drive is
// parked behind Builder tools; What runs where is engines.app.test.tsx.
beforeEach(() => {
  useBuilderTools.getState().setOn(true);
});
afterEach(() => {
  useBuilderTools.getState().setOn(false);
});

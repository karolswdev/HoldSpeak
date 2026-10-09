// PHILO-16 (C) — Runs on, the Models window as a Switchboard.
//
// Ported intents of the parked Concierge tests (features/concierge/__tests__):
// the engine truth (state from the authority's fit, never reachability), the
// repairs and the add row, plus the board's own: a drop writes the whole
// chain with CAS, 409 redraws, Undo, Meetings writes the summary row, Try it
// (local, off-machine behind the press, speech), FOUND → Use it, the bar.

import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import type { Detection, Roster, RosterRow } from "../api";

const m = vi.hoisted(() => ({
  readRoster: vi.fn(),
  readDetection: vi.fn(),
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
vi.mock("../../../desk/shell", () => ({ openSurfaceOr: m.openSurfaceOr }));

import { RunsOnCore } from "../RunsOnCore";

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
  for (const fn of Object.values(m)) fn.mockReset();
  m.readRoster.mockResolvedValue(roster());
  m.readDetection.mockResolvedValue(detection());
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
  await screen.findByTestId("switchboard");
  await waitFor(() => expect(screen.getByTestId("switchboard-engine-openrouter")).toBeTruthy());
}

describe("Runs on — paint and words", () => {
  it("paints the roster's jobs before the detection lands, then the engines fill in", async () => {
    let finish: (value: Detection) => void = () => {};
    m.readDetection.mockReturnValue(new Promise<Detection>((resolve) => (finish = resolve)));
    render(<RunsOnCore />);
    await screen.findByTestId("switchboard");
    expect(screen.getAllByTestId(/^switchboard-job-/)).toHaveLength(7);
    expect(screen.getByTestId("runson-fact").textContent).toBe("7 jobs · 3 engines");
    expect(screen.queryByTestId("switchboard-engine-openrouter")).toBeNull();
    // Wires already draw from the roster: speech, thoughts, default.
    expect(screen.getAllByTestId("switchboard-wire").map((w) => w.getAttribute("data-job"))).toEqual([
      "speech_recognition",
      "thoughts_notes",
      "default",
    ]);
    await act(async () => finish(detection()));
    expect(await screen.findByTestId("switchboard-engine-openrouter")).toBeTruthy();
    expect(screen.getByTestId("runson-fact").textContent).toBe("7 jobs · 4 engines");
  });

  it("draws one of five words per job, from the authority's fit (never reachability)", async () => {
    await board();
    const state = (id: string) => screen.getByTestId(`switchboard-job-${id}`).getAttribute("data-state");
    expect(state("meetings")).toBe("limited"); // q27 cannot do Calendar work
    expect(state("agents_tools")).toBe("ready");
    expect(state("thoughts_notes")).toBe("ready");
    const strip = screen.getByTestId("runson-strip").textContent ?? "";
    expect(strip).toContain("6 ready");
    expect(strip).toContain("1 limited");
    expect(strip).toContain("THIS MAC · M‑SERIES · 36 GB");
    // Retired: no picker wells, no Adjust, no Use these, no summaries verb.
    for (const word of ["Use these", "Use this for summaries", "Adjust", "Cancel"]) {
      expect(screen.queryByRole("button", { name: word })).toBeNull();
    }
  });

  it("a caller's scope opens on its job (hot wires)", async () => {
    await board("summary");
    expect(screen.getByTestId("switchboard-job-meetings").className).toContain("is-selected");
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
    expect(receipt.textContent).toMatch(/^PATCHED \d\d:\d\d · Thoughts & notes → qwen3.8 27B$/);
    expect(screen.getByTestId("runson-egress").textContent).toContain("192.168.1.43");
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() => expect(m.writeChain).toHaveBeenCalledTimes(2));
    // C1: Undo is a CAS write against the revision the patch produced (7).
    expect(m.writeChain).toHaveBeenLastCalledWith({
      scope: { kind: "group", group_id: "thoughts_notes" },
      expectedRevision: 7,
      entries: [{ profile_id: "q4b", profile_revision: 2 }],
    });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE/));
  });

  it("⌥ adds a fallback after the first", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-thoughts_notes"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter", altKey: true });
    await waitFor(() => expect(m.writeChain).toHaveBeenCalled());
    expect(m.writeChain.mock.calls[0][0].entries.map((e: { profile_id: string }) => e.profile_id)).toEqual(["q4b", "q27"]);
    expect((await screen.findByTestId("runson-receipt")).textContent).toContain("FALLBACK");
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
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE \d\d:\d\d · Meetings$/));
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
      expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE .* · Meetings · SUMMARIES CHANGED ELSEWHERE$/),
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
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE .* · Meetings$/));
    fireEvent.click(screen.getByTestId("runson-undo"));
    await waitFor(() =>
      expect(m.clearChain).toHaveBeenCalledWith({
        scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
        capabilityId: "meeting.deferred_analysis",
        expectedRevision: 9,
      }),
    );
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^UNDONE .* · Meetings$/));
    expect(screen.getByTestId("runson-receipt").textContent).not.toContain("CHANGED ELSEWHERE");
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
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("CHANGED ELSEWHERE · Thoughts & notes"));
    expect(m.writeChain.mock.calls[1][0].expectedRevision).toBe(7);
    // The entry is gone: no second Undo can overwrite the other writer.
    expect(screen.queryByTestId("runson-undo")).toBeNull();
    expect(m.writeChain).toHaveBeenCalledTimes(2);
  });

  it("409: re-reads, redraws, and says CHANGED ELSEWHERE (no blind retry)", async () => {
    await board();
    const reads = m.readRoster.mock.calls.length;
    m.writeChain.mockRejectedValueOnce(
      new ApiError(409, "Assignment changed.", { code: "inference_assignment_revision_conflict" }),
    );
    fireEvent.click(screen.getByTestId("switchboard-job-agents_tools"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("CHANGED ELSEWHERE"));
    expect(m.writeChain).toHaveBeenCalledTimes(1);
    expect(m.readRoster.mock.calls.length).toBeGreaterThan(reads);
  });

  it("refuses what the job cannot take, with the reason in the foot and no write", async () => {
    await board();
    fireEvent.click(screen.getByTestId("switchboard-job-speech_recognition"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q27"), { key: "Enter" });
    expect((await screen.findByTestId("runson-receipt")).textContent).toBe("REFUSED · SPEECH RECOGNITION · SPEECH ENGINES ONLY");
    fireEvent.click(screen.getByTestId("switchboard-job-agents_tools"));
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-q4b"), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toBe("REFUSED · AGENTS & TOOLS · WITHOUT AGENTS"));
    expect(m.writeChain).not.toHaveBeenCalled();
  });
});

describe("Runs on — Try it", () => {
  it("runs the real route on a local job and lands the answer on the job", async () => {
    m.taskProbe.mockResolvedValue({ state: "READY", ok: true, model: "Qwen 3.5 4B", latencyMs: 412, host: "THIS DEVICE", legs: [] });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(screen.getByTestId("switchboard-result-thoughts_notes").textContent).toBe("READY · Qwen 3.5 4B · 412 MS"));
    expect(m.taskProbe).toHaveBeenCalledWith("ask.answer", undefined);
  });

  it("an off-machine Try waits for the press that names the host (Article III)", async () => {
    m.probe.mockResolvedValue({ state: "READY", host: "192.168.1.43", latencyMs: 410 });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-meetings"));
    const confirm = await screen.findByTestId("runson-try-confirm");
    expect(confirm.textContent).toBe("Try on 192.168.1.43");
    expect(m.probe).not.toHaveBeenCalled();
    fireEvent.click(confirm);
    await waitFor(() => expect(m.probe).toHaveBeenCalledWith("lan:q27", false));
    await waitFor(() =>
      expect(screen.getByTestId("switchboard-result-meetings").textContent).toBe("REACHED · qwen3.8 27B · 410 MS · WITHOUT CALENDAR"),
    );
    expect(screen.getByTestId("runson-egress").textContent).toContain("192.168.1.43");
  });

  it("a pending consent is bound to its engine: a re-patch voids it and asks for the new host (C3)", async () => {
    // The cloud branch's real answer (concierge_service.probe, no getter):
    // NOT_SET, no latency; never a READY.
    m.probe.mockResolvedValue({ state: "NOT_SET", host: "openrouter.ai", latencyMs: null, keySet: true });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-meetings"));
    expect((await screen.findByTestId("runson-try-confirm")).textContent).toBe("Try on 192.168.1.43");
    // Meetings is patched to another engine while the press is pending.
    const moved = roster();
    moved.rows[4] = { ...moved.rows[4], inherited_from: "group", expected_revision: 1,
      assignment: { revision: 1, entries: [{ ...Q27, profile_id: "openrouter", label: "OpenRouter", boundary: "cloud" }], issues: [] } };
    m.readRoster.mockResolvedValue(moved);
    // (Try it already selected Meetings.)
    expect(screen.getByTestId("switchboard-job-meetings").className).toContain("is-selected");
    fireEvent.keyDown(screen.getByTestId("switchboard-engine-openrouter"), { key: "Enter" });
    await waitFor(() => expect(screen.getByTestId("runson-try-confirm").textContent).toBe("Try on OPENROUTER.AI"));
    expect(m.probe).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("runson-try-confirm"));
    await waitFor(() => expect(m.probe).toHaveBeenCalledTimes(1));
    expect(m.probe).toHaveBeenCalledWith("cloud:openrouter", true);
    expect(m.probe).not.toHaveBeenCalledWith("lan:q27", expect.anything());
    await waitFor(() => expect(screen.getByTestId("switchboard-result-meetings").textContent).toBe("NOT CHECKED · OpenRouter"));
  });

  it("a refreshed detection that moves the SAME engine to another host voids the press (C3 r2)", async () => {
    m.probe.mockResolvedValue({ state: "READY", host: "192.168.1.99", latencyMs: 12 });
    m.define.mockResolvedValue({ profileId: "engine-x", profileRevision: 1 });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-meetings"));
    expect((await screen.findByTestId("runson-try-confirm")).textContent).toBe("Try on 192.168.1.43");
    // The next detection answers the same engine id at another address
    // (a re-defined endpoint); any refresh of the board reads it.
    const moved = detection();
    moved.engines = moved.engines.map((e) =>
      e.id === "lan:q27" ? { ...e, host: "192.168.1.99", baseUrl: "http://192.168.1.99:8080/v1" } : e,
    );
    m.readDetection.mockResolvedValue(moved);
    fireEvent.click(within(screen.getByTestId("switchboard-engine-local:ollama:11434:llama3.3")).getByRole("button", { name: "Use it" }));
    await waitFor(() => expect(screen.getByTestId("runson-try-confirm").textContent).toBe("Try on 192.168.1.99"));
    expect(m.probe).not.toHaveBeenCalled();
    fireEvent.click(screen.getByTestId("runson-try-confirm"));
    await waitFor(() => expect(m.probe).toHaveBeenCalledTimes(1));
  });

  it("consentHolds compares the job, the engine id AND the destination", async () => {
    const { consentHolds, consentHost } = await import("../useRunsOn");
    const engine = { key: "q27", host: "192.168.1.43", baseUrl: "http://192.168.1.43:8080/v1" } as never;
    const consent = { job: "meetings", engineKey: "q27", engineHost: consentHost(engine), host: "192.168.1.43", scope: "local" as const };
    expect(consentHolds(consent, "meetings", engine)).toBe(true);
    expect(consentHolds(consent, "meetings", { ...(engine as object), host: "192.168.1.99" } as never)).toBe(false);
    expect(consentHolds(consent, "meetings", { ...(engine as object), baseUrl: "http://10.0.0.9/v1" } as never)).toBe(false);
    expect(consentHolds(consent, "meetings", { ...(engine as object), key: "other" } as never)).toBe(false);
    expect(consentHolds(consent, "agents_tools", engine)).toBe(false);
  });

  it("a cloud Try that probes nothing says NOT CHECKED, never READY (V2)", async () => {
    m.probe.mockResolvedValue({ state: "NOT_SET", host: "openrouter.ai", latencyMs: null, keySet: true });
    const det = detection();
    const routed = roster();
    routed.rows[5] = { ...routed.rows[5], inherited_from: "group",
      assignment: { revision: 1, entries: [{ ...Q27, profile_id: "openrouter", label: "OpenRouter", boundary: "cloud" }], issues: [] } };
    m.readRoster.mockResolvedValue(routed);
    m.readDetection.mockResolvedValue(det);
    await board();
    fireEvent.click(screen.getByTestId("runson-try-agents_tools"));
    fireEvent.click(await screen.findByTestId("runson-try-confirm"));
    await waitFor(() => expect(screen.getByTestId("switchboard-result-agents_tools").textContent).toBe("NOT CHECKED · OpenRouter"));
    expect(screen.getByTestId("switchboard-result-agents_tools").textContent).not.toContain("READY");
  });

  it("a probe with no latency shows no ms token (A.8)", async () => {
    m.taskProbe.mockResolvedValue({ state: "READY", ok: true, model: "Qwen 3.5 4B", latencyMs: 0, host: "THIS DEVICE", legs: [] });
    await board();
    fireEvent.click(screen.getByTestId("runson-try-thoughts_notes"));
    await waitFor(() => expect(screen.getByTestId("switchboard-result-thoughts_notes").textContent).toBe("READY · Qwen 3.5 4B"));
  });

  it("Speech: you speak, it shows what it heard", async () => {
    m.startCapture.mockResolvedValue(undefined);
    m.stopAndTranscribe.mockResolvedValue("freeze the old ledger on nov 5");
    await board();
    fireEvent.click(screen.getByTestId("runson-try-speech_recognition"));
    await waitFor(() => expect(screen.getByTestId("runson-try-speech_recognition").textContent).toBe("Stop"));
    fireEvent.click(screen.getByTestId("runson-try-speech_recognition"));
    await waitFor(() =>
      expect(screen.getByTestId("switchboard-result-speech_recognition").textContent).toMatch(/^HEARD: "freeze the old ledger on nov 5"( · \d+ MS)?$/),
    );
    expect(m.probe).not.toHaveBeenCalled();
  });
});

describe("Runs on — FOUND, downloads, the add row", () => {
  it("FOUND → Use it adds the engine through the Model Library; it joins with no wire", async () => {
    m.define.mockResolvedValue({ profileId: "engine-127-0-0-1-11434", profileRevision: 1 });
    await board();
    expect(screen.getByTestId("switchboard-found-cap").textContent).toBe("Found · 1");
    const found = screen.getByTestId("switchboard-engine-local:ollama:11434:llama3.3");
    const reads = m.readDetection.mock.calls.length;
    fireEvent.click(within(found).getByRole("button", { name: "Use it" }));
    await waitFor(() => expect(m.define).toHaveBeenCalledTimes(1));
    expect(m.define.mock.calls[0][0]).toMatchObject({ endpoint: "http://127.0.0.1:11434/v1", model: "llama3.3" });
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^ADDED \d\d:\d\d · Llama 3.3 8B$/));
    expect(m.readDetection.mock.calls.length).toBeGreaterThan(reads);
    expect(m.writeChain).not.toHaveBeenCalled();
  });

  it("a Download names the internet host, never THIS DEVICE, and fills the bar in place", async () => {
    m.download.mockResolvedValue({ jobId: "acq-1", presetId: "vision", progress: { received: 0, total: 0 } });
    m.readAcquisition
      .mockResolvedValueOnce({ state: "downloading", percent: 40 })
      .mockResolvedValue({ state: "ready", percent: 100 });
    await board();
    const plate = screen.getByTestId("switchboard-engine-preset:vision");
    expect(plate.textContent).toContain("HUGGINGFACE.CO");
    expect(plate.textContent).not.toContain("THIS DEVICE");
    fireEvent.click(within(plate).getByRole("button", { name: "Download" }));
    await waitFor(() => expect(m.download).toHaveBeenCalledWith("vision"));
    await waitFor(
      () => expect(screen.getByTestId("switchboard-bar-preset:vision").getAttribute("aria-valuenow")).toBe("40"),
      { timeout: 4000 },
    );
    expect(screen.getByTestId("switchboard-lamp-preset:vision").getAttribute("data-lamp")).toBe("busy");
    await waitFor(() => expect(screen.getByTestId("runson-receipt").textContent).toMatch(/^DOWNLOADED/), { timeout: 4000 });
    expect(m.readAcquisition).toHaveBeenCalledWith("acq-1");
  }, 10_000);

  it("a failed download keeps BROKEN and its reason until retried (V3)", async () => {
    m.download.mockResolvedValue({ jobId: "acq-2", presetId: "vision", progress: { received: 0, total: 0 } });
    m.readAcquisition.mockResolvedValue({ state: "failed", percent: 12, error: "model_download_network" });
    await board();
    const plate = screen.getByTestId("switchboard-engine-preset:vision");
    fireEvent.click(within(plate).getByRole("button", { name: "Download" }));
    await waitFor(
      () => expect(screen.getByTestId("runson-receipt").textContent).toBe("DOWNLOAD STOPPED · Qwen 3.5 4B vision file · NETWORK"),
      { timeout: 4000 },
    );
    expect(screen.getByTestId("switchboard-lamp-preset:vision").getAttribute("data-lamp")).toBe("broken");
    expect(screen.getByTestId("switchboard-engine-preset:vision").textContent).toContain("STOPPED · NETWORK");
    expect(screen.getByTestId("switchboard-engine-preset:vision").textContent).not.toContain("NOT DOWNLOADED");
    // A retry clears the reason.
    m.readAcquisition.mockResolvedValue({ state: "downloading", percent: 30, error: null });
    fireEvent.click(within(screen.getByTestId("switchboard-engine-preset:vision")).getByRole("button", { name: "Download" }));
    await waitFor(() => expect(screen.getByTestId("switchboard-engine-preset:vision").textContent).not.toContain("STOPPED"));
  }, 10_000);

  it("the Add row's refusal is tokens, never the server's sentence (A.3)", async () => {
    m.check.mockResolvedValue({ ok: false, models: [], detail: "Nothing answers at this address." });
    await board();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    const row = screen.getByTestId("concierge-add-engine-row");
    fireEvent.change(within(row).getAllByRole("textbox")[0], { target: { value: "http://127.0.0.1:9/v1" } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await waitFor(() => expect(screen.getByTestId("concierge-add-reason").textContent).toBe("127.0.0.1:9"));
    expect(row.textContent).toContain("UNREACHABLE");
    expect(row.textContent).not.toContain("Nothing answers");
  });

  it("Add an engine: address + Check inline, then Add through define-endpoint; the Check answer stays a token", async () => {
    m.check.mockResolvedValue({ ok: true, models: ["stub-model"], detail: "", tools: "no" });
    m.define.mockResolvedValue({ profileId: "engine-x", profileRevision: 1 });
    await board();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    const row = screen.getByTestId("concierge-add-engine-row");
    fireEvent.change(within(row).getAllByRole("textbox")[0], { target: { value: "http://10.0.0.5:8080/v1" } });
    expect(screen.getByTestId("concierge-add-egress").textContent).toContain("10.0.0.5:8080");
    expect((screen.getByTestId("concierge-add-submit") as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await waitFor(() => expect(screen.getByTestId("concierge-add-model").textContent).toBe("stub-model"));
    expect(screen.getByTestId("concierge-add-tools").textContent).toBe("NO TOOLS");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));
    await waitFor(() => expect(m.define).toHaveBeenCalled());
    expect(m.define.mock.calls[0][0]).toMatchObject({ endpoint: "http://10.0.0.5:8080/v1", model: "stub-model" });
    expect(m.summary).not.toHaveBeenCalled(); // joins the column; no assignment
    await waitFor(() => expect(screen.queryByTestId("concierge-add-engine-row")).toBeNull());
  });
});

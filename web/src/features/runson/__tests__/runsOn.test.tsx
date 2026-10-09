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
      { id: "ask.answer", label: "Ask answer", group: { id: "thoughts_notes", label: "Thoughts & notes" } },
      { id: "meeting.deferred_analysis", label: "Deferred meeting analysis", group: { id: "meetings", label: "Meetings" } },
      { id: "meeting.auto_title", label: "Meeting title", group: { id: "meetings", label: "Meetings" } },
      { id: "meeting.live_analysis", label: "Live meeting analysis", group: { id: "meetings", label: "Meetings" } },
      { id: "speech.transcribe", label: "Speech transcription", group: { id: "speech_recognition", label: "Speech recognition" } },
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
    summaryAssignment: {
      capabilityId: "meeting.deferred_analysis", status: "unassigned", assignmentRevision: 0,
      profileId: null, profileRevision: null, label: null, boundary: null, readiness: null,
    },
  };
}

beforeEach(() => {
  for (const fn of Object.values(m)) fn.mockReset();
  m.readRoster.mockResolvedValue(roster());
  m.readDetection.mockResolvedValue(detection());
  m.writeChain.mockResolvedValue({});
  m.clearChain.mockResolvedValue({});
  m.summary.mockResolvedValue({ status: "succeeded", state: "READY", plainReason: "", summaryAssignment: null });
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
    expect(m.writeChain).toHaveBeenLastCalledWith({
      scope: { kind: "group", group_id: "thoughts_notes" },
      expectedRevision: 2,
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

  it("Meetings also writes the exact summary row the queue reads; Undo clears both", async () => {
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
    // Undo of a first patch: the group follows the default again (clear),
    // and the summary row, unassigned before, is cleared too.
    const after = roster();
    after.rows[4] = { ...after.rows[4], inherited_from: "group", expected_revision: 1,
      assignment: { revision: 1, entries: [{ ...Q27, profile_id: "openrouter", label: "OpenRouter" }], issues: [] } };
    m.readRoster.mockResolvedValue(after);
    const det = detection();
    det.summaryAssignment = { ...det.summaryAssignment!, status: "assigned", assignmentRevision: 1, profileId: "openrouter", profileRevision: 1 };
    m.readDetection.mockResolvedValue(det);
    fireEvent.click(await screen.findByTestId("runson-undo"));
    await waitFor(() => expect(m.clearChain).toHaveBeenCalledTimes(2));
    expect(m.clearChain.mock.calls[0][0]).toEqual({
      scope: { kind: "group", group_id: "meetings" },
      capabilityId: "meeting.deferred_analysis",
      expectedRevision: 1,
    });
    expect(m.clearChain.mock.calls[1][0]).toEqual({
      scope: { kind: "capability", capability_id: "meeting.deferred_analysis" },
      capabilityId: "meeting.deferred_analysis",
      expectedRevision: 1,
    });
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

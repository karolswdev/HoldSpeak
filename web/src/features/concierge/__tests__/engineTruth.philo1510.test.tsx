// PHILO-16 (C): these tests describe the PARKED ConciergeCore (it renders
// nowhere now). Their live intents are ported to features/runson/__tests__
// (state words, a drop writes the chain, 409, Try it, FOUND, the bar, the
// add row); they stay green against the parked core until it is retired.
/* PHILO-15 10 — the engine setup tells the truth (B05, B06, B10).
 * READY only where the whole group runs; LIMITED names the work it cannot
 * do; "Use these" keeps the window and says what it set; the Check names
 * the server's own answer about tool calls. */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConciergeCore } from "../ConciergeCore";
import { applicableSetRows, receiptLine, summaryRowFromAssignment, type SetRow } from "../useConciergeController";
import { ApiError } from "../../../lib/api";
import type { DetectResponse, ProposeResponse } from "../api";

const mocks = vi.hoisted(() => ({
  detect: vi.fn(),
  propose: vi.fn(),
  probe: vi.fn(),
  taskProbe: vi.fn(),
  apply: vi.fn(),
  download: vi.fn(),
  checkEndpoint: vi.fn(),
  defineEndpoint: vi.fn(),
  summarySelection: vi.fn(),
  closeSurfaceWindow: vi.fn(),
}));

vi.mock("../api", async () => {
  const actual = await vi.importActual<typeof import("../api")>("../api");
  return {
    ...actual,
    conciergeDetect: mocks.detect,
    conciergePropose: mocks.propose,
    conciergeProbe: mocks.probe,
    conciergeTaskProbe: mocks.taskProbe,
    conciergeApply: mocks.apply,
    conciergeDownload: mocks.download,
    checkEndpoint: mocks.checkEndpoint,
    defineEndpoint: mocks.defineEndpoint,
    conciergeSummarySelection: mocks.summarySelection,
  };
});

vi.mock("../../../desk/store", () => ({
  useDesk: { getState: () => ({ closeSurfaceWindow: mocks.closeSurfaceWindow }) },
}));


const LAN_URL = "http://192.168.1.43:8080/v1";

function detection(): DetectResponse {
  return {
    engines: [
      { id: "lan:box", kind: "lan", name: "Qwen3.8 27B", host: "192.168.1.43", state: "READY",
        profileId: "engine-192-168-1-43-8080", baseUrl: LAN_URL },
      { id: "lan:other", kind: "lan", name: "Other box", host: "192.168.1.44", state: "READY" },
      { id: "local:whisper:mlx:base", kind: "local", name: "Whisper base", host: "THIS DEVICE", state: "READY" },
    ],
    hardware: { capability: { apple_silicon: true, system: "darwin", ram_gb: 36 } },
    runtimes: [],
    checkedAt: "2026-10-07T09:41:00Z",
    repairs: [],
    summaryAssignment: null,
  } as DetectResponse;
}

const FITS_AGENTS = {
  "lan:box": { state: "LIMITED" as const, blocked: ["Agents"] },
  "lan:other": { state: "UNKNOWN" as const },
};

function proposal(): ProposeResponse {
  return {
    rows: [
      { group: "thoughts_notes", label: "Thoughts & notes", engineId: "lan:box", host: "192.168.1.43",
        state: "READY", fits: { "lan:box": { state: "READY" }, "lan:other": { state: "UNKNOWN" } } },
      { group: "speech_recognition", label: "Speech recognition", engineId: "local:whisper:mlx:base",
        host: "THIS DEVICE", state: "READY", fits: { "local:whisper:mlx:base": { state: "READY" } } },
      { group: "agents_tools", label: "Agents & tools", engineId: "lan:other", host: "192.168.1.44",
        state: "UNKNOWN", fits: FITS_AGENTS },
      { group: "background", label: "Background", engineId: "lan:box", host: "192.168.1.43",
        state: "LIMITED", blocked: ["Calendar"], plainReason: "This engine cannot give a structured result.",
        fits: { "lan:box": { state: "LIMITED", blocked: ["Calendar"] } } },
    ],
    receipt: { groups: 4, engines: 2, waiting: 0, limited: 1, unknown: 1 },
  };
}

async function open() {
  mocks.detect.mockResolvedValue(detection());
  mocks.propose.mockResolvedValue(proposal());
  render(<ConciergeCore scope="" />);
  await screen.findByTestId("concierge-set-list");
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.probe.mockResolvedValue({ state: "READY", host: "192.168.1.43", latencyMs: 12 });
});

describe("PHILO-15 10 — READY means ready", () => {
  it("draws LIMITED with the owner's work names, no sentence, and UNKNOWN · TRY", async () => {
    await open();
    const background = screen.getByTestId("concierge-set-background");
    expect(within(background).getByText("LIMITED")).toBeTruthy();
    const limit = screen.getByTestId("concierge-set-limit-background").textContent ?? "";
    expect(limit).toBe("WITHOUTCALENDAR");
    expect(background.textContent).not.toContain("structured result");
    expect(within(screen.getByTestId("concierge-set-agents_tools")).getByText("UNKNOWN · TRY")).toBeTruthy();
    expect(screen.getByTestId("concierge-receipt").textContent).toContain("1 LIMITED");
  });

  // Astra r1 (finding 1): a pick reads the authority, never reachability.
  it("picking an engine takes its fit, and the probe never makes it READY", async () => {
    await open();
    fireEvent.click(screen.getByTestId("concierge-picker-agents_tools"));
    fireEvent.click(await screen.findByTestId("concierge-pick-agents_tools-lan:box"));
    const row = screen.getByTestId("concierge-set-agents_tools");
    await waitFor(() => expect(within(row).getByText("LIMITED")).toBeTruthy());
    expect(screen.getByTestId("concierge-set-limit-agents_tools").textContent).toContain("AGENTS");
    await waitFor(() => expect(mocks.probe).toHaveBeenCalled());
    await new Promise((r) => setTimeout(r, 20));
    expect(within(row).queryByText("READY")).toBeNull();
  });

  it("a pick with no answer reads UNKNOWN · TRY, never READY", async () => {
    await open();
    fireEvent.click(screen.getByTestId("concierge-picker-thoughts_notes"));
    fireEvent.click(await screen.findByTestId("concierge-pick-thoughts_notes-lan:other"));
    const row = screen.getByTestId("concierge-set-thoughts_notes");
    await waitFor(() => expect(within(row).getByText("UNKNOWN · TRY")).toBeTruthy());
  });

  it("an unreachable engine reads FAILED after the probe", async () => {
    mocks.probe.mockResolvedValue({ state: "UNREACHABLE", host: "x", latencyMs: null });
    await open();
    fireEvent.click(screen.getByTestId("concierge-picker-agents_tools"));
    fireEvent.click(await screen.findByTestId("concierge-pick-agents_tools-lan:box"));
    const row = screen.getByTestId("concierge-set-agents_tools");
    await waitFor(() => expect(within(row).getByText("FAILED")).toBeTruthy());
  });

  it("the saved summary engine reads the authority's answer, UNKNOWN without one", () => {
    const row: SetRow = {
      group: "meetings", label: "Meetings", engineId: "lan:box", host: "", state: "READY",
      pickerOpen: false, alternatives: [], fits: { "lan:box": { state: "LIMITED", blocked: ["Meeting plugins"] } },
    };
    const engines = detection().engines;
    const assigned = { capabilityId: "meeting.deferred_analysis", status: "assigned", assignmentRevision: 1,
      profileId: "engine-192-168-1-43-8080", profileRevision: 1, label: "Qwen", boundary: "lan", readiness: "ready" };
    expect(summaryRowFromAssignment(row, assigned as never, engines).state).toBe("LIMITED");
    expect(summaryRowFromAssignment({ ...row, fits: {} }, assigned as never, engines).state).toBe("UNKNOWN");
  });

  it("sends LIMITED and UNKNOWN groups, never INCOMPATIBLE or WAITING", () => {
    const rows = [
      { state: "READY", engineId: "a" },
      { state: "LIMITED", engineId: "a" },
      { state: "UNKNOWN", engineId: "b" },
      { state: "INCOMPATIBLE", engineId: "a" },
      { state: "WAITING", engineId: null },
      { state: "WAITING", engineId: "OFF" },
    ];
    expect(applicableSetRows(rows).map((r) => r.state)).toEqual(["READY", "LIMITED", "UNKNOWN", "WAITING"]);
  });
});

describe("PHILO-15 10 — receipts, not surprises (B10, Astra r1 finding 3)", () => {
  it("names every failed group with its token, and keeps them FAILED after the re-read", async () => {
    mocks.apply.mockResolvedValue({
      receipt: "r1",
      summary: { groups: 3, engines: 2, ready: 1, limited: 0, off: 0, failed: 2, engine: "Qwen3.8 27B",
        host: "192.168.1.43", default: { engineId: "lan:box" } },
      results: [
        { group: "thoughts_notes", state: "SKIPPED", token: "NO MODEL RECORD" },
        { group: "speech_recognition", state: "READY" },
        { group: "agents_tools", state: "FAILED", token: "INCOMPATIBLE" },
      ],
    });
    await open();
    // The hub's re-read carries the failures the press recorded on its
    // receipt (`lastApply`, concierge_service.last_apply), as the real
    // /api/concierge/detect does.
    mocks.detect.mockResolvedValue({
      ...detection(),
      lastApply: { receipt: "r1", failures: [
        { group: "thoughts_notes", token: "NO MODEL RECORD" },
        { group: "agents_tools", token: "INCOMPATIBLE" },
      ] },
    });
    fireEvent.click(screen.getByTestId("concierge-apply"));
    await waitFor(() =>
      expect(screen.getByTestId("concierge-receipt").textContent).toBe(
        "USING · QWEN3.8 27B · 1 GROUP · DEFAULT SET · THOUGHTS & NOTES · NO MODEL RECORD · AGENTS & TOOLS · INCOMPATIBLE",
      ),
    );
    expect(mocks.closeSurfaceWindow).not.toHaveBeenCalled();
    await waitFor(() => expect(mocks.propose).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.getByTestId("concierge-set-fail-thoughts_notes").textContent).toBe("NO MODEL RECORD"),
    );
    expect(screen.getByTestId("concierge-set-fail-agents_tools").textContent).toBe("INCOMPATIBLE");
  });

  // Astra r2 (finding 4): one cause is said once, with its count.
  it("says a repeated cause once, with the count", () => {
    expect(
      receiptLine({ kind: "set", engine: "", host: "", ready: 0, limited: 0, failed: 3, off: 0, defaultSet: false,
        failures: [
          { group: "a", label: "Thoughts & notes", token: "NO MODEL RECORD" },
          { group: "b", label: "Meetings", token: "NO MODEL RECORD" },
          { group: "c", label: "Agents & tools", token: "INCOMPATIBLE" },
        ] }),
    ).toBe("2 GROUPS · NO MODEL RECORD · AGENTS & TOOLS · INCOMPATIBLE");
  });

  // Astra r2 (finding 3): the failures are the hub's record; a fresh mount
  // (a reload, a reopen) reads them from detection.
  it("shows the last press's failures after a remount", async () => {
    mocks.detect.mockResolvedValue({
      ...detection(),
      lastApply: { receipt: "r9", failures: [
        { group: "thoughts_notes", token: "NO MODEL RECORD" },
        { group: "background", token: "NO MODEL RECORD" },
      ] },
    });
    mocks.propose.mockResolvedValue(proposal());
    render(<ConciergeCore scope="" />);
    await screen.findByTestId("concierge-set-list");
    expect(screen.getByTestId("concierge-set-fail-thoughts_notes").textContent).toBe("NO MODEL RECORD");
    expect(screen.getByTestId("concierge-set-fail-background").textContent).toBe("NO MODEL RECORD");
    expect(screen.getByTestId("concierge-receipt").textContent).toBe("2 GROUPS · NO MODEL RECORD");
  });

  it("the waiting-group refusal is a token, not the server's sentence", async () => {
    mocks.apply.mockRejectedValue(
      new ApiError(409, "Speech recognition waits for a download.", {
        code: "concierge_waiting_group", message: "Speech recognition waits for a download.",
        group: "speech_recognition",
      }),
    );
    await open();
    fireEvent.click(screen.getByTestId("concierge-apply"));
    await waitFor(() =>
      expect(screen.getByTestId("concierge-receipt").textContent).toBe(
        "SPEECH RECOGNITION · WAITS · SPEECH DOWNLOAD",
      ),
    );
    // The server's sentence is not shown anywhere on the face.
    expect(document.body.textContent).not.toContain("waits for a download");
  });

  it("writes the receipt line in tokens", () => {
    expect(
      receiptLine({ kind: "summaries", engine: "qwen3.8-27b", host: "192.168.1.43:8080",
        ready: 1, limited: 0, failed: 0, off: 0, defaultSet: true, failures: [] }),
    ).toBe("USING · QWEN3.8-27B · SUMMARIES · DEFAULT SET");
  });
});

describe("PHILO-15 10 — the Check asks the server about tool calls", () => {
  async function check(tools: string, myServer = false) {
    mocks.checkEndpoint.mockResolvedValue({ ok: true, models: ["qwen3.8-27b"], detail: "", tools });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByLabelText("Server address"), { target: { value: LAN_URL } });
    if (myServer) fireEvent.click(screen.getByLabelText("MY SERVER"));
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    return (await screen.findByTestId("concierge-add-tools")).textContent;
  }

  it("names TOOLS beside READY", async () => {
    expect(await check("yes")).toBe("TOOLS");
  });

  it("says TOOLS UNKNOWN when the server cannot say", async () => {
    expect(await check("unknown")).toBe("TOOLS UNKNOWN");
  });

  // Astra r1 (finding 4): MY SERVER is the owner's word; it travels with the Check.
  it("MY SERVER travels with the Check", async () => {
    await check("yes", true);
    expect(mocks.checkEndpoint).toHaveBeenCalledWith(LAN_URL, "", true);
  });
});

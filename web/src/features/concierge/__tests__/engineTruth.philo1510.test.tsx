/* PHILO-15 10 — the engine setup tells the truth (B05, B06, B10).
 * READY only where the whole group runs; LIMITED names the work it cannot
 * do; "Use these" keeps the window and says what it set; the Check names
 * the server's own answer about tool calls. */

import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConciergeCore } from "../ConciergeCore";
import { applicableSetRows, receiptLine } from "../useConciergeController";
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
      { id: "local:whisper:mlx:base", kind: "local", name: "Whisper base", host: "THIS DEVICE", state: "READY" },
    ],
    hardware: { capability: { apple_silicon: true, system: "darwin", ram_gb: 36 } },
    runtimes: [],
    checkedAt: "2026-10-07T09:41:00Z",
    repairs: [],
    summaryAssignment: null,
  } as DetectResponse;
}

function proposal(): ProposeResponse {
  return {
    rows: [
      { group: "thoughts_notes", label: "Thoughts & notes", engineId: "lan:box", host: "192.168.1.43",
        state: "LIMITED", blocked: ["Thought development"], plainReason: "This engine cannot give a structured result." },
      { group: "chat_practice", label: "Chat", engineId: "lan:box", host: "192.168.1.43",
        state: "INCOMPATIBLE", blocked: ["Chat compaction", "Chat guardrail"] },
      { group: "speech_recognition", label: "Speech recognition", engineId: "local:whisper:mlx:base",
        host: "THIS DEVICE", state: "READY" },
      { group: "background", label: "Background", engineId: "lan:other", host: "",
        state: "UNKNOWN" },
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
});

describe("PHILO-15 10 — READY means ready", () => {
  it("draws LIMITED with the blocked work, INCOMPATIBLE, and UNKNOWN · TRY", async () => {
    await open();
    const thoughts = screen.getByTestId("concierge-set-thoughts_notes");
    expect(within(thoughts).getByText("LIMITED")).toBeTruthy();
    expect(within(thoughts).queryByText("READY")).toBeNull();
    expect(screen.getByTestId("concierge-set-limit-thoughts_notes").textContent).toContain(
      "NO THOUGHT DEVELOPMENT",
    );
    expect(within(screen.getByTestId("concierge-set-chat_practice")).getByText("INCOMPATIBLE")).toBeTruthy();
    expect(within(screen.getByTestId("concierge-set-background")).getByText("UNKNOWN · TRY")).toBeTruthy();
    expect(screen.getByTestId("concierge-receipt").textContent).toContain("1 LIMITED");
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

describe("PHILO-15 10 — receipts, not surprises (B10)", () => {
  it("keeps the window after Use these and says what was set", async () => {
    mocks.apply.mockResolvedValue({
      receipt: "r1",
      summary: { groups: 3, engines: 2, ready: 1, limited: 1, off: 0, failed: 1, engine: "Qwen3.8 27B",
        host: "192.168.1.43", default: { engineId: "lan:box" } },
      results: [
        { group: "thoughts_notes", state: "LIMITED", blocked: ["Thought development"] },
        { group: "speech_recognition", state: "READY" },
        { group: "background", state: "SKIPPED", plainReason: "No profile for engine" },
      ],
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-apply"));
    await waitFor(() =>
      expect(screen.getByTestId("concierge-receipt").textContent).toContain("USING · QWEN3.8 27B"),
    );
    const receipt = screen.getByTestId("concierge-receipt").textContent ?? "";
    expect(receipt).toContain("2 GROUPS · 1 LIMITED · 1 FAILED · DEFAULT SET");
    expect(receipt).toContain("No profile for engine");
    expect(mocks.closeSurfaceWindow).not.toHaveBeenCalled();
    // The set is read again (quietly) so the rows show the server's fresh truth.
    await waitFor(() => expect(mocks.propose).toHaveBeenCalledTimes(2));
  });

  it("writes the receipt line in tokens", () => {
    expect(
      receiptLine({ kind: "summaries", engine: "qwen3.8-27b", host: "192.168.1.43:8080",
        ready: 1, limited: 0, failed: 0, off: 0, defaultSet: false, failures: [] }),
    ).toBe("USING · QWEN3.8-27B · SUMMARIES");
  });
});

describe("PHILO-15 10 — the Check asks the server about tool calls", () => {
  it("names TOOLS beside READY", async () => {
    mocks.checkEndpoint.mockResolvedValue({ ok: true, models: ["qwen3.8-27b"], detail: "", tools: "yes" });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByLabelText("Server address"), { target: { value: LAN_URL } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-tools")).textContent).toBe("TOOLS");
  });

  it("says TOOLS UNKNOWN when the server cannot say", async () => {
    mocks.checkEndpoint.mockResolvedValue({ ok: true, models: ["m"], detail: "", tools: "unknown" });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByLabelText("Server address"), { target: { value: LAN_URL } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-tools")).textContent).toBe("TOOLS UNKNOWN");
  });
});

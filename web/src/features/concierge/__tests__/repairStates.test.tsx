/* HS-200-04 — the four named repair states on the Concierge face.
 *
 * `needs_attention` is a word, not a repair. Each state names itself, names the
 * host where the repair happens, and carries exactly ONE verb that opens an
 * existing control. */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConciergeCore } from "../ConciergeCore";
import type { DetectResponse, ProposeResponse, Repair } from "../api";

const mocks = vi.hoisted(() => ({
  detect: vi.fn(),
  propose: vi.fn(),
  probe: vi.fn(),
  taskProbe: vi.fn(),
  apply: vi.fn(),
  download: vi.fn(),
  openSurfaceOr: vi.fn(),
  openSurface: vi.fn(),
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
  };
});

vi.mock("../../../desk/shell", () => ({
  openSurfaceOr: mocks.openSurfaceOr,
  openSurface: mocks.openSurface,
}));

vi.mock("../../../desk/store", () => ({
  useDesk: { getState: () => ({ closeSurfaceWindow: mocks.closeSurfaceWindow }) },
}));

function repair(over: Partial<Repair>): Repair {
  return {
    id: "r1",
    token: "CREDENTIAL EXPIRED",
    subject: "Migrated intel endpoint",
    host: "api.openai.com",
    scope: "cloud",
    groups: ["thoughts_notes"],
    groupLabels: ["Thoughts & notes"],
    verb: "Connections",
    control: "connections",
    engineId: "",
    presetId: "",
    baseUrl: "",
    detail: "",
    ...over,
  };
}

const GROUPS: Array<[string, string]> = [
  ["thoughts_notes", "Thoughts & notes"],
  ["chat_practice", "Chat"],
  ["writing_dictation", "Writing & dictation"],
  ["speech_recognition", "Speech recognition"],
  ["meetings", "Meetings"],
  ["agents_tools", "Agents & tools"],
  ["background", "Background"],
];

function detection(repairs: Repair[]): DetectResponse {
  return {
    engines: [
      {
        id: "lan:box",
        kind: "lan",
        name: "Qwen3.6 35B",
        host: "192.168.1.43",
        state: "READY",
        profileId: "box",
        baseUrl: "http://192.168.1.43:8080/v1",
      },
      {
        id: "preset:qwen35-08b",
        kind: "preset",
        name: "Qwen 3.5 0.8B",
        host: "THIS DEVICE",
        state: "WAITING",
        sizeBytes: 532_000_000,
        installed: false,
        presetId: "qwen35-08b",
      },
    ],
    hardware: { capability: { apple_silicon: true, system: "darwin", ram_gb: 36 } },
    runtimes: [],
    checkedAt: "2026-09-06T09:41:00Z",
    repairs,
  };
}

const proposal: ProposeResponse = {
  rows: GROUPS.map(([group, label]) => ({
    group,
    label,
    engineId: "lan:box",
    host: "192.168.1.43",
    state: "READY" as const,
  })),
  receipt: { groups: 7, engines: 1, waiting: 0 },
};

async function open(repairs: Repair[]) {
  mocks.detect.mockResolvedValue(detection(repairs));
  mocks.propose.mockResolvedValue(proposal);
  render(<ConciergeCore scope="" />);
  await screen.findByTestId("concierge-set-list");
}

describe("Concierge repair states (HS-200-04)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.taskProbe.mockResolvedValue({
      state: "READY",
      ok: true,
      capabilityId: "ask.answer",
      group: "thoughts_notes",
      reasonCode: "",
      model: "qwen3.6-35b",
      boundary: "private_network",
      host: "192.168.1.43",
      latencyMs: 41,
      legs: [],
    });
  });

  it("shows no repair section when nothing needs the owner", async () => {
    await open([]);
    expect(screen.queryByTestId("concierge-repair-list")).toBeNull();
    expect(screen.queryByTestId("concierge-repairs-label")).toBeNull();
  });

  it("names each state, its host, and exactly one verb", async () => {
    await open([
      repair({}),
      repair({
        id: "r2",
        token: "ENDPOINT UNREACHABLE",
        subject: "Qwen3.6 35B",
        host: "192.168.1.43",
        scope: "local",
        verb: "Check",
        control: "endpoint_editor",
        baseUrl: "http://192.168.1.43:8080/v1",
      }),
      repair({
        id: "r3",
        token: "MODEL FILE MISSING",
        subject: "Qwen 3.5 0.8B",
        host: "THIS DEVICE",
        scope: "local",
        verb: "Download",
        control: "model_library",
        presetId: "qwen35-08b",
        groups: ["writing_dictation"],
        groupLabels: ["Writing & dictation"],
      }),
      repair({
        id: "r4",
        token: "TOOL INCOMPATIBLE",
        subject: "Whisper base",
        host: "",
        scope: "local",
        verb: "Choose",
        control: "engine_picker",
        groups: ["agents_tools"],
        groupLabels: ["Agents & tools"],
      }),
    ]);

    expect(screen.getByTestId("concierge-repairs-label")).toHaveTextContent("NEEDS YOU 4");
    for (const token of [
      "credential-expired",
      "endpoint-unreachable",
      "model-file-missing",
      "tool-incompatible",
    ]) {
      const row = screen.getByTestId(`concierge-repair-${token}`);
      expect(row).toBeInTheDocument();
      // Exactly one verb on the row.
      expect(
        screen.getAllByTestId(`concierge-repair-verb-${token}`),
      ).toHaveLength(1);
    }
    expect(screen.getByText("API.OPENAI.COM")).toBeInTheDocument();
    expect(screen.getAllByText("THIS DEVICE").length).toBeGreaterThan(0);
  });

  it("the credential verb opens the Connections door", async () => {
    await open([repair({})]);
    fireEvent.click(screen.getByTestId("concierge-repair-verb-credential-expired"));
    await waitFor(() =>
      expect(mocks.openSurfaceOr).toHaveBeenCalledWith(
        "configure-integrations",
        "/settings",
      ),
    );
  });

  it("the endpoint verb opens the endpoint editor on that endpoint", async () => {
    await open([
      repair({
        token: "ENDPOINT UNREACHABLE",
        verb: "Check",
        control: "endpoint_editor",
        baseUrl: "http://192.168.1.43:8080/v1",
      }),
    ]);
    fireEvent.click(screen.getByTestId("concierge-repair-verb-endpoint-unreachable"));
    const field = await screen.findByDisplayValue("http://192.168.1.43:8080/v1");
    expect(field).toBeInTheDocument();
  });

  it("the incompatible verb opens that group's picker in place", async () => {
    await open([
      repair({
        token: "TOOL INCOMPATIBLE",
        verb: "Choose",
        control: "engine_picker",
        groups: ["agents_tools"],
        groupLabels: ["Agents & tools"],
      }),
    ]);
    fireEvent.click(screen.getByTestId("concierge-repair-verb-tool-incompatible"));
    expect(
      await screen.findByTestId("concierge-picker-well-agents_tools"),
    ).toBeInTheDocument();
    // In-world, never a modal.
    expect(document.querySelectorAll('[role="dialog"]')).toHaveLength(0);
  });

  it("the missing-file verb starts the Model Library acquisition", async () => {
    mocks.download.mockResolvedValue({
      jobId: "j1",
      presetId: "qwen35-08b",
      progress: { received: 0, total: 1 },
    });
    await open([
      repair({
        token: "MODEL FILE MISSING",
        verb: "Download",
        control: "model_library",
        presetId: "qwen35-08b",
      }),
    ]);
    fireEvent.click(screen.getByTestId("concierge-repair-verb-model-file-missing"));
    await waitFor(() => expect(mocks.download).toHaveBeenCalledWith("qwen35-08b"));
  });

  it("the probe names the model that served and the boundary it crossed", async () => {
    await open([]);
    fireEvent.click(screen.getByTestId("concierge-probe-run"));
    expect(await screen.findByTestId("concierge-probe-model")).toHaveTextContent(
      "qwen3.6-35b",
    );
    expect(screen.getByText("192.168.1.43")).toBeInTheDocument();
    expect(screen.getByText("41 MS")).toBeInTheDocument();
  });

  it("an off-machine probe is refused until the owner asks again", async () => {
    mocks.taskProbe.mockResolvedValueOnce({
      state: "REFUSED",
      ok: false,
      capabilityId: "ask.answer",
      group: "thoughts_notes",
      reasonCode: "route_probe_off_machine_not_confirmed",
      paid: true,
      legs: [{ ordinal: 1, deploymentRevisionId: "dep", boundary: "cloud" }],
    });
    await open([]);
    fireEvent.click(screen.getByTestId("concierge-probe-run"));
    // The cost is named before a paid probe, and no model is claimed.
    expect(await screen.findByText("1 TOKEN · $")).toBeInTheDocument();
    expect(screen.queryByTestId("concierge-probe-model")).toBeNull();

    fireEvent.click(screen.getByTestId("concierge-probe-run"));
    await waitFor(() =>
      expect(mocks.taskProbe).toHaveBeenLastCalledWith(undefined, true),
    );
  });
});

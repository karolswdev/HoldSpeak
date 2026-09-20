/* HS-201-09 — connect an engine from the face.
 *
 * The rehearsal (audits/rehearsal-07-opus.md) proved a stranger could not:
 * "Add an engine..." posted a body the service refuses, "Use these" was
 * disabled by an unrelated WAITING group, OFF changed no assignment, and a
 * reopened Models forgot the applied truth.
 *
 * Every assertion here reads what the face DID — the request it issued and
 * the row it drew — never the click.
 */

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ConciergeCore } from "../ConciergeCore";
import { ENDPOINT_DRAFT_KEYS } from "../endpointDraft";
import type {
  DetectResponse,
  ProposeResponse,
  SummaryAssignment,
} from "../api";

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
const LAN_MODEL = "Qwen3.6-35B-A3B-UD-Q5_K_XL.gguf";
const OTHER_URL = "http://192.168.1.44:8080/v1";

const GROUPS: Array<[string, string]> = [
  ["thoughts_notes", "Thoughts & notes"],
  ["chat_practice", "Chat"],
  ["writing_dictation", "Writing & dictation"],
  ["speech_recognition", "Speech recognition"],
  ["meetings", "Meetings"],
  ["agents_tools", "Agents & tools"],
  ["background", "Background"],
];

function detection(
  summaryAssignment: SummaryAssignment | null = null,
): DetectResponse {
  return {
    engines: [
      {
        id: "lan:box",
        kind: "lan",
        name: "Qwen3.6 35B A3B",
        host: "192.168.1.43",
        state: "READY",
        profileId: "engine-192-168-1-43-8080",
        baseUrl: LAN_URL,
      },
    ],
    hardware: { capability: { apple_silicon: true, system: "darwin", ram_gb: 36 } },
    runtimes: [],
    checkedAt: "2026-09-20T09:41:00Z",
    repairs: [],
    summaryAssignment,
  };
}

/** The proposal the rehearsal met: everything READY but Speech, which is
 *  WAITING on a download it has not run. */
function proposal(): ProposeResponse {
  return {
    rows: GROUPS.map(([group, label]) =>
      group === "speech_recognition"
        ? {
            group,
            label,
            engineId: null,
            host: "",
            state: "WAITING" as const,
          }
        : {
            group,
            label,
            engineId: "lan:box",
            host: "192.168.1.43",
            state: "READY" as const,
          },
    ),
    receipt: { groups: 7, engines: 1, waiting: 1 },
  };
}

async function open(summaryAssignment: SummaryAssignment | null = null) {
  mocks.detect.mockResolvedValue(detection(summaryAssignment));
  mocks.propose.mockResolvedValue(proposal());
  render(<ConciergeCore scope="" />);
  await screen.findByTestId("concierge-set-list");
}

function assigned(over: Partial<SummaryAssignment> = {}): SummaryAssignment {
  return {
    capabilityId: "meeting.deferred_analysis",
    status: "assigned",
    assignmentRevision: 2,
    profileId: "engine-192-168-1-43-8080",
    profileRevision: 1,
    label: "Qwen3.6 35B A3B",
    boundary: "lan",
    readiness: "ready",
    ...over,
  };
}

beforeEach(() => {
  vi.clearAllMocks();
  mocks.apply.mockResolvedValue({
    receipt: "concierge-apply-1",
    summary: { groups: 1, engines: 1, ready: 1, off: 0 },
    results: [{ group: "meetings", state: "READY" }],
  });
});

/* ── 1. the summary group applies on its own ── */

describe("Use these applies per group (defect 5)", () => {
  it("is enabled while an unrelated group is WAITING", async () => {
    await open();
    expect(screen.getByTestId("concierge-apply")).not.toBeDisabled();
  });

  it("never sends the WAITING group it did not touch", async () => {
    await open();
    fireEvent.click(screen.getByTestId("concierge-apply"));
    await waitFor(() => expect(mocks.apply).toHaveBeenCalled());
    const rows = mocks.apply.mock.calls[0][0] as Array<{ group: string }>;
    expect(rows.map((r) => r.group)).not.toContain("speech_recognition");
    expect(rows.map((r) => r.group)).toContain("meetings");
  });
});

/* ── 2. OFF is sent as OFF for the exact summary group ── */

describe("OFF on the summary group (defect 3)", () => {
  it("sends engineId OFF for meetings", async () => {
    await open();
    fireEvent.click(screen.getByTestId("concierge-picker-meetings"));
    fireEvent.click(await screen.findByTestId("concierge-pick-meetings-off"));
    fireEvent.click(screen.getByTestId("concierge-apply"));
    await waitFor(() => expect(mocks.apply).toHaveBeenCalled());
    const rows = mocks.apply.mock.calls[0][0] as Array<{
      group: string;
      engineId: string | null;
    }>;
    expect(rows.find((r) => r.group === "meetings")?.engineId).toBe("OFF");
  });
});

/* ── 3. the face shows the APPLIED truth on reopen ── */

describe("the Meetings row reads the assignment (defect 4)", () => {
  it("shows OFF after the owner turned it off, not the proposal", async () => {
    await open(
      assigned({
        status: "off",
        profileId: null,
        profileRevision: null,
        label: null,
        boundary: null,
        readiness: null,
      }),
    );
    const row = screen.getByTestId("concierge-set-meetings");
    expect(row.textContent).not.toContain("Qwen3.6 35B A3B");
    expect(
      screen.getByTestId("concierge-picker-meetings").textContent,
    ).toContain("—");
  });

  it("shows the applied engine when one is assigned", async () => {
    await open(assigned());
    expect(
      screen.getByTestId("concierge-picker-meetings").textContent,
    ).toContain("Qwen3.6 35B A3B");
  });

  it("names an assigned engine detection no longer lists", async () => {
    await open(
      assigned({ profileId: "engine-gone", label: "Retired engine" }),
    );
    expect(
      screen.getByTestId("concierge-picker-meetings").textContent,
    ).toContain("Retired engine");
  });
});

/* ── 4. Add an engine: the verb, the check, the reason, the selection ── */

describe("Add an engine (defect 1)", () => {
  it("is a library Button, not a span", async () => {
    await open();
    const verb = screen.getByTestId("concierge-add-engine");
    expect(verb.tagName).toBe("BUTTON");
    expect(verb.className).toContain("btn");
    expect(verb.textContent).toBe("Add an engine");
  });

  it("shows the refusal's plain reason beside the verb", async () => {
    mocks.checkEndpoint.mockResolvedValue({
      ok: false,
      models: [],
      detail: "The server has no /models route.",
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    const reason = await screen.findByTestId("concierge-add-reason");
    expect(reason.textContent).toBe("The server has no /models route.");
    // Beside the verb: the same add-engine row, not 400 px below it.
    expect(
      screen.getByTestId("concierge-add-engine-row").contains(reason),
    ).toBe(true);
    expect(screen.getByTestId("concierge-add-submit")).toBeDisabled();
  });

  it("names the model the server serves after a good check", async () => {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-model")).textContent).toBe(
      LAN_MODEL,
    );
    expect(screen.getByTestId("concierge-add-submit")).not.toBeDisabled();
  });

  it("posts a lawful draft and then the one summary selection", async () => {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    mocks.defineEndpoint.mockResolvedValue({
      profileId: "engine-192-168-1-43-8080",
      profileRevision: 1,
    });
    mocks.summarySelection.mockResolvedValue({
      status: "succeeded",
      state: "READY",
      plainReason: "",
      summaryAssignment: assigned(),
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));

    await waitFor(() => expect(mocks.summarySelection).toHaveBeenCalled());
    const draft = mocks.defineEndpoint.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(Object.keys(draft).sort()).toEqual([...ENDPOINT_DRAFT_KEYS].sort());
    expect(draft.profile_id).toBe("engine-192-168-1-43-8080");
    expect(draft.provider_family).toBe("openai_compatible");
    expect(draft.model).toBe(LAN_MODEL);
    expect(draft.endpoint).toBe(LAN_URL);
    expect(draft.label).toBe("192.168.1.43:8080");

    const selection = mocks.summarySelection.mock.calls[0][0] as Record<
      string,
      unknown
    >;
    expect(selection.profileId).toBe("engine-192-168-1-43-8080");
    expect(selection.profileRevision).toBe(1);
    expect(selection.expectedAssignmentRevision).toBe(0);
  });

  it("refuses to claim success when the selection did not succeed", async () => {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    mocks.defineEndpoint.mockResolvedValue({
      profileId: "engine-192-168-1-43-8080",
      profileRevision: 1,
    });
    mocks.summarySelection.mockResolvedValue({
      status: "partial",
      state: "FAILED",
      plainReason: "This engine cannot give a structured result.",
      summaryAssignment: null,
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));
    expect((await screen.findByTestId("concierge-add-reason")).textContent).toBe(
      "This engine cannot give a structured result.",
    );
  });

  it("keeps one filled primary while the well holds a READY engine", async () => {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    await open();
    expect(screen.getByTestId("concierge-apply").className).toContain(
      "btn--primary",
    );
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
    expect(screen.getByTestId("concierge-add-submit").className).toContain(
      "btn--primary",
    );
    expect(screen.getByTestId("concierge-apply").className).not.toContain(
      "btn--primary",
    );
  });
});

/* ── 5. a repair names its reason ── */

describe("TOOL INCOMPATIBLE carries its reason (defect 7)", () => {
  it("draws the service's plain line on the row", async () => {
    mocks.detect.mockResolvedValue({
      ...detection(),
      repairs: [
        {
          id: "tool-incompatible:Qwen",
          token: "TOOL INCOMPATIBLE" as const,
          subject: "Qwen3.6 35B A3B",
          host: "",
          scope: "local" as const,
          groups: ["agents_tools"],
          groupLabels: ["Agents & tools"],
          verb: "Choose",
          control: "engine_picker" as const,
          engineId: "",
          presetId: "",
          baseUrl: "",
          detail: "This engine cannot use tools.",
        },
      ],
    });
    mocks.propose.mockResolvedValue(proposal());
    render(<ConciergeCore scope="" />);
    const reason = await screen.findByTestId(
      "concierge-repair-reason-tool-incompatible",
    );
    expect(reason.textContent).toBe("This engine cannot use tools.");
  });
});

/* ═══ Counsel fix round (Astra, DO-NOT-RATIFY on PR #590) ══════════════ */

describe("the single gesture finishes setup (counsel 1)", () => {
  async function useTheEngine() {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    mocks.defineEndpoint.mockResolvedValue({
      profileId: "engine-192-168-1-43-8080",
      profileRevision: 1,
    });
    mocks.summarySelection.mockResolvedValue({
      status: "succeeded",
      state: "READY",
      plainReason: "",
      summaryAssignment: assigned(),
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
    fireEvent.click(screen.getByTestId("concierge-add-submit"));
  }

  it("fires the one readiness signal the arrival listens for", async () => {
    const heard: string[] = [];
    const listener = () => heard.push("settings-updated");
    window.addEventListener("holdspeak:settings-updated", listener);
    try {
      await useTheEngine();
      await waitFor(() => expect(heard).toHaveLength(1));
    } finally {
      window.removeEventListener("holdspeak:settings-updated", listener);
    }
  });

  it("closes the Models window, like ordinary Apply", async () => {
    await useTheEngine();
    await waitFor(() =>
      expect(mocks.closeSurfaceWindow).toHaveBeenCalledWith("surface-concierge"),
    );
  });
});

describe("a changed address invalidates the check (counsel 3)", () => {
  async function checkedAt(url: string) {
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: url },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
  }

  it("drops READY and the named model when the address changes", async () => {
    await checkedAt(LAN_URL);
    fireEvent.change(screen.getByDisplayValue(LAN_URL), {
      target: { value: OTHER_URL },
    });
    await waitFor(() =>
      expect(screen.queryByTestId("concierge-add-model")).toBeNull(),
    );
    expect(screen.getByTestId("concierge-add-submit")).toBeDisabled();
  });

  it("ignores a check answer for an address already replaced", async () => {
    const settled: Array<(value: unknown) => void> = [];
    mocks.checkEndpoint.mockImplementation(
      () =>
        new Promise((resolve) => {
          settled.push(resolve);
        }),
    );
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    // He edits the address while the first check is still in flight.
    fireEvent.change(screen.getByDisplayValue(LAN_URL), {
      target: { value: OTHER_URL },
    });
    settled[0]?.({ ok: true, models: [LAN_MODEL], detail: "Found 1 model." });
    await waitFor(() =>
      expect(screen.getByTestId("concierge-add-submit")).toBeDisabled(),
    );
    expect(screen.queryByTestId("concierge-add-model")).toBeNull();
  });

  /* Round 2 residual: the stale branches returned BEFORE clearing the
     in-flight flag, so `Check` stayed disabled (ConciergeCore.tsx) and the
     corrected address could never be checked at all. */

  async function openWithPendingCheck(
    settled: Array<{ resolve: (v: unknown) => void; reject: (e: unknown) => void }>,
  ) {
    mocks.checkEndpoint.mockImplementation(
      () =>
        new Promise((resolve, reject) => {
          settled.push({ resolve, reject });
        }),
    );
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    // He corrects the address while the first check is still in flight.
    fireEvent.change(screen.getByDisplayValue(LAN_URL), {
      target: { value: OTHER_URL },
    });
  }

  it("lets him check the corrected address after a stale ANSWER", async () => {
    const settled: Array<{
      resolve: (v: unknown) => void;
      reject: (e: unknown) => void;
    }> = [];
    await openWithPendingCheck(settled);
    settled[0]?.resolve({ ok: true, models: [LAN_MODEL], detail: "Found 1 model." });
    await waitFor(() =>
      expect(screen.getByTestId("concierge-add-check")).not.toBeDisabled(),
    );
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    settled[1]?.resolve({ ok: true, models: ["other-model"], detail: "Found 1 model." });
    expect((await screen.findByTestId("concierge-add-model")).textContent).toBe(
      "other-model",
    );
  });

  it("lets him check the corrected address after a stale FAILURE", async () => {
    const settled: Array<{
      resolve: (v: unknown) => void;
      reject: (e: unknown) => void;
    }> = [];
    await openWithPendingCheck(settled);
    settled[0]?.reject(new Error("the first address threw"));
    await waitFor(() =>
      expect(screen.getByTestId("concierge-add-check")).not.toBeDisabled(),
    );
    // The thrown answer belonged to the old address: it says nothing here.
    expect(screen.queryByTestId("concierge-add-reason")).toBeNull();
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    settled[1]?.resolve({ ok: true, models: ["other-model"], detail: "Found 1 model." });
    expect((await screen.findByTestId("concierge-add-model")).textContent).toBe(
      "other-model",
    );
  });
});

describe("the address the Check will contact is named (counsel 4c)", () => {
  it("draws the egress chip for the typed address", async () => {
    await open();
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    const chip = await screen.findByTestId("concierge-add-egress");
    expect(chip.textContent).toContain("192.168.1.43");
  });
});

describe("one filled primary, measured (counsel 4a)", () => {
  function withRepairsAndPresets(): DetectResponse {
    const base = detection();
    return {
      ...base,
      engines: [
        ...base.engines,
        {
          id: "preset:qwen35-08b",
          kind: "preset",
          name: "Quick local Qwen",
          host: "THIS DEVICE",
          state: "WAITING",
          sizeBytes: 2_600_000_000,
          installed: false,
          presetId: "qwen35-08b",
        },
        {
          id: "preset:qwen35-tiny",
          kind: "preset",
          name: "Tiny local Qwen",
          host: "THIS DEVICE",
          state: "WAITING",
          sizeBytes: 508_000_000,
          installed: false,
          presetId: "qwen35-tiny",
        },
      ],
      repairs: [
        {
          id: "tool-incompatible:Qwen",
          token: "TOOL INCOMPATIBLE" as const,
          subject: "Qwen3.6 35B A3B",
          host: "",
          scope: "local" as const,
          groups: ["agents_tools"],
          groupLabels: ["Agents & tools"],
          verb: "Choose",
          control: "engine_picker" as const,
          engineId: "",
          presetId: "",
          baseUrl: "",
          detail: "This engine cannot use tools.",
        },
        {
          id: "endpoint-unreachable:other",
          token: "ENDPOINT UNREACHABLE" as const,
          subject: "192.168.1.99:8080",
          host: "192.168.1.99",
          scope: "local" as const,
          groups: ["background"],
          groupLabels: ["Background"],
          verb: "Check",
          control: "endpoint_editor" as const,
          engineId: "",
          presetId: "",
          baseUrl: "http://192.168.1.99:8080/v1",
          detail: "Nothing answers at this address.",
        },
      ],
    };
  }

  function filled(): string[] {
    return [...document.querySelectorAll(".btn--primary")].map((b) =>
      (b.textContent || "").trim(),
    );
  }

  it("keeps exactly one with two repairs and two presets on the face", async () => {
    mocks.detect.mockResolvedValue(withRepairsAndPresets());
    mocks.propose.mockResolvedValue(proposal());
    render(<ConciergeCore scope="" />);
    await screen.findByTestId("concierge-set-list");
    expect(filled()).toEqual(["Choose"]);
  });

  it("hands it to the Add-engine verb while it holds a READY engine", async () => {
    mocks.detect.mockResolvedValue(withRepairsAndPresets());
    mocks.propose.mockResolvedValue(proposal());
    mocks.checkEndpoint.mockResolvedValue({
      ok: true,
      models: [LAN_MODEL],
      detail: "Found 1 model.",
    });
    render(<ConciergeCore scope="" />);
    await screen.findByTestId("concierge-set-list");
    fireEvent.click(screen.getByTestId("concierge-add-engine"));
    fireEvent.change(await screen.findByDisplayValue(""), {
      target: { value: LAN_URL },
    });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    await screen.findByTestId("concierge-add-model");
    expect(filled()).toEqual(["Use this for summaries"]);
  });

  it("gives it to a preset Download when nothing else claims it", async () => {
    const cold = withRepairsAndPresets();
    mocks.detect.mockResolvedValue({ ...cold, repairs: [] });
    mocks.propose.mockResolvedValue({
      rows: GROUPS.map(([group, label]) => ({
        group,
        label,
        engineId: null,
        host: "",
        state: "WAITING" as const,
      })),
      receipt: { groups: 7, engines: 0, waiting: 7 },
    });
    render(<ConciergeCore scope="" />);
    await screen.findByTestId("concierge-set-list");
    expect(filled()).toEqual(["Download"]);
  });
});

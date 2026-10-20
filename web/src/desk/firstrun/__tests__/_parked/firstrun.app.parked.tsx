/* First run, the app: the real FirstRun (every card, the Concierge controller
 * of "Use a server") on the hub's OWN recorded answers.
 *
 * The test diet (PHILO-17 final lane A, 2026-10-11): successors of the first-run
 * browser walks. Only `apiFetch` (the wire) is replaced. Every answer was
 * recorded on a real hub by tests/integration/test_desk_firstrun.py, which
 * asserts the hub half and fences these files' shape on every run
 * (HOLDSPEAK_WIRE_WRITE=1 rewrites them). One scenario is one hub boot: the
 * reads the face makes, the answer to each press, the reads after it. A read
 * the recording does not hold is a miss, and every test asserts none. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi, onTestFinished } from "vitest";
import { useBuilderTools } from "../../builderTools";

const mocks = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  refresh: vi.fn(),
  open: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ApiError: (await importOriginal<typeof import("../../../lib/api")>()).ApiError,
  apiFetch: mocks.apiFetch,
  readableError: (error: unknown) => (error instanceof Error ? error.message : "Request failed"),
}));
vi.mock("../../store", () => ({
  useDesk: Object.assign(() => undefined, {
    getState: () => ({ refresh: mocks.refresh, armEventRecording: vi.fn(), openAsk: vi.fn(), setup: null }),
  }),
}));
vi.mock("../../shell", () => ({ openSurfaceOr: mocks.open }));
vi.mock("../../../lib/micStreamSession", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/micStreamSession")>()),
  micStreamSupported: () => true,
  startStreamSession: vi.fn(),
  subscribeCaptureLevel: () => () => undefined,
}));

import { ApiError } from "../../../lib/api";
import { FirstRun } from "../FirstRun";
import { RunsOnCore } from "../../../features/runson/RunsOnCore";

// These behavior tests enter the optional setup and chat wells explicitly.
function renderExpandedFirstRun() {
 const view = render(<FirstRun />);
 view.container.querySelectorAll<HTMLDetailsElement>(".firstrun-chat, .firstrun-optional").forEach((fold) => { fold.open = true; });
 return view;
}


const RECORDED = import.meta.glob("../../__tests__/fixtures/firstrun-*/*.json", { eager: true, import: "default" }) as Record<
  string,
  { wire: unknown }
>;

function recorded(scenario: string, name: string): unknown {
  const file = RECORDED[`../../__tests__/fixtures/firstrun-${scenario}/${name}.json`];
  if (!file) throw new Error(`no recorded answer firstrun-${scenario}/${name}`);
  return structuredClone(file.wire);
}

/** One scenario's replay: `<stage><METHOD>_<path>` per read; `presses` maps
 *  a write to [its recorded answer, the stage after it]. */
class RecordedHub {
  calls: Array<{ method: string; path: string; json?: unknown }> = [];
  misses: string[] = [];
  constructor(
    readonly scenario: string,
    public stage: string,
    readonly presses: Record<string, [string, string | null]> = {},
  ) {}
  answer(path: string, init: { method?: string; json?: unknown } = {}): unknown {
    const method = (init.method ?? "GET").toUpperCase();
    this.calls.push({ method, path, json: init.json });
    const press = this.presses[`${method} ${path}`];
    if (press) {
      if (press[1]) this.stage = press[1];
      return recorded(this.scenario, press[0]);
    }
    try {
      return recorded(this.scenario, `${this.stage}${method}${path.replace(/\//g, "_")}`);
    } catch {
      this.misses.push(`${method} ${path}`);
      throw new ApiError(404, "not recorded", { code: "not_recorded" });
    }
  }
}

let hub: RecordedHub;

beforeEach(() => {
  mocks.refresh.mockReset().mockResolvedValue(undefined);
  mocks.open.mockReset();
  mocks.apiFetch.mockReset().mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) =>
    hub.answer(String(path), init),
  );
});
afterEach(() => vi.restoreAllMocks());

describe("First run — a LAN box as the default keeps the speech download (recorded hub)", () => {
  it("Use a server: TOOLS, NOW THE DEFAULT, THIS DEVICE (never LAN); Set up speech stays; First words is not lit", async () => {
    // replaces: tests/e2e/test_philo15_10_engine_truth_glass.py::TestColdFirstRun::test_the_lan_box_keeps_the_speech_download
    // (hub half: tests/integration/test_desk_firstrun.py::test_a_lan_box_as_default_keeps_the_speech_download)
    hub = new RecordedHub("lan", "0-cold", {
      "POST /api/setup/discover-models": ["check", null],
      "POST /api/inference/model-library/define-endpoint": ["define", null],
      "POST /api/concierge/summary-selection": ["select", "1-used"],
    });
    renderExpandedFirstRun();
    const card = await screen.findByTestId("firstrun-local-ai");
    fireEvent.click(await within(card).findByTestId("firstrun-lan-verb"));
    const speech = await screen.findByTestId("firstrun-speech-verb");
    expect(speech.textContent).toMatch(/^Set up speech · /);

    fireEvent.change(await screen.findByLabelText("Server address"), { target: { value: "http://127.0.0.1:8099/v1" } });
    fireEvent.click(screen.getByTestId("concierge-add-check"));
    expect((await screen.findByTestId("concierge-add-tools")).textContent).toBe("TOOLS");
    await waitFor(() => expect((screen.getByTestId("concierge-add-submit") as HTMLButtonElement).disabled).toBe(false));
    // Betterment ST0: the press is Use (it said "for summaries" and set every job).
    expect(screen.getByTestId("concierge-add-submit").textContent?.trim()).toBe("Use");
    await act(async () => {
      fireEvent.click(screen.getByTestId("concierge-add-submit"));
    });
    const receipt = await screen.findByTestId("firstrun-lan-receipt");
    expect(receipt.textContent).toContain("NOW THE DEFAULT");

    // A server on this machine is THIS DEVICE, never "LAN".
    await waitFor(() => expect(card.textContent).toContain("THIS DEVICE"));
    expect(card.textContent).not.toContain("LAN ·");
    // Speech is still missing: the download stays, the card is not done.
    expect(screen.getByTestId("firstrun-speech-verb")).toBeTruthy();
    expect(screen.getByTestId("firstrun-first-words").getAttribute("data-lit")).not.toBe("true");
    const select = hub.calls.find((c) => c.path === "/api/concierge/summary-selection");
    expect(select?.json).toMatchObject({ setDefault: true });
    expect(hub.misses).toEqual([]);
  });
});

describe("Engines after the first-run Use (recorded hub)", () => {
  it("no job is broken and Speech to text runs on no chat server", async () => {
    // Betterment ST0: after the press Engines said `Speech to text · runs on
    // 192.168.1.43`, TOOL INCOMPATIBLE and 1 BROKEN.
    // (hub half: tests/integration/test_desk_firstrun.py::test_a_lan_box_as_default_keeps_the_speech_download)
    hub = new RecordedHub("lan", "1-used");
    // Betterment E5: the job board this reads is parked behind Builder tools.
    useBuilderTools.getState().setOn(true);
    onTestFinished(() => useBuilderTools.getState().setOn(false));
    render(<RunsOnCore scope="" />);
    const strip = await screen.findByTestId("runson-strip");
    await waitFor(() => expect(strip.textContent).toMatch(/ready/));
    await waitFor(() => expect(hub.calls.some((c) => c.path === "/api/concierge/detect")).toBe(true));
    expect(strip.textContent).not.toMatch(/broken/);
    expect(document.body.textContent).not.toContain("TOOL INCOMPATIBLE");
    expect(screen.getByTestId("switchboard-job-speech_recognition").getAttribute("data-state")).not.toBe("broken");
    expect(hub.misses).toEqual([]);
  });
});

describe("First run — a denied calendar has a way forward (recorded hub)", () => {
  it("CALENDAR · NOT ALLOWED with Open System Settings and Check again; one open; allowed, the card moves on", async () => {
    // replaces: tests/e2e/test_philo15_04_small_gaps_glass.py::TestCalendarDenied::test_denied_has_a_way_forward
    // (hub half: tests/integration/test_desk_firstrun.py::test_a_denied_calendar_has_a_way_forward)
    hub = new RecordedHub("calendar-denied", "0-denied", {
      "POST /api/onboarding/calendar/macos/settings": ["open-settings", "1-allowed"],
    });
    renderExpandedFirstRun();
    const denied = await screen.findByTestId("firstrun-calendar-denied");
    expect(denied.textContent).toContain("CALENDAR · NOT ALLOWED");
    expect(within(denied).getAllByRole("button").map((b) => b.textContent)).toEqual(["Open System Settings", "Check again"]);

    await act(async () => {
      fireEvent.click(within(denied).getByRole("button", { name: "Open System Settings" }));
    });
    expect(hub.calls.filter((c) => c.path === "/api/onboarding/calendar/macos/settings")).toHaveLength(1);
    expect(within(denied).queryByText("SETTINGS · NOT OPENED")).toBeNull();

    // He allows it in System Settings; Check again reads the hub's new state.
    await act(async () => {
      fireEvent.click(within(denied).getByRole("button", { name: "Check again" }));
    });
    await waitFor(() => expect(screen.queryByTestId("firstrun-calendar-denied")).toBeNull());
    expect(hub.misses).toEqual([]);
  });
});

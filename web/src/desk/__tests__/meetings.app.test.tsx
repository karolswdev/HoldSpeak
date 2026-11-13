/* The Meetings app, rendered whole over the hub's REAL bodies (the test
 * diet, 2026-10-11).
 *
 * The browser rigs below seeded a real hub and read the Meetings face. Their
 * facts move here: the real list (`HistoryCore`) and the real meeting window
 * (`MeetingRecord`), with their own hooks and stores, over the bodies a real
 * hub served for the SAME seeds (fixtures/meetings-hub/*.json, captured from
 * `tests/e2e/glass_infra._boot` with each rig's own seed helper; the
 * `_source` key in each file names it). Only `apiFetch` is replaced: it
 * answers each GET with the captured body for that path. No field is
 * invented (SCAR LAW: a double that lies about the field a check reads
 * proves nothing). The one POST body not captured (the summary run) is the
 * shape `MeetingIntelService.run_intelligence` returns
 * (holdspeak/services/meeting_intel_service.py:268).
 *
 * Facts that stay with other tiers: overflow at 393 (T3, the sweep lane);
 * text clip on proposal primaries (real geometry, T3); a hub restart and the
 * route/409 behaviour of the hub itself (T1, sub-worker M2).
 */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { lazy, useEffect, useState, type ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiError } from "../../lib/api";
import { forgetExecutedReceipts } from "../../meetings/summaryRoute";
import { HistoryCore } from "../../pages/cores/HistoryCore";
import { MeetingRecord } from "../../pages/cores/history/MeetingRecord";
import { Mast, MastSlotContext, type MastDeclaration } from "../surface/patterns/Mast";
import { TitleSlotContext } from "../surface/title";
import { WindowIdContext } from "../components/window/windowIdContext";
import { WingSlotContext } from "../surface/wings";
import { openPrimitive, openSurfaceOr } from "../shell";
import { SurfaceWindowHost, type SurfaceRow } from "../components/SurfaceWindows";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { meetingAction } from "./helpers/meetingReader";
import review11a from "./fixtures/meetings-hub/review11a.json";
import readerR3 from "./fixtures/meetings-hub/reader-r3.json";
import readerR2 from "./fixtures/meetings-hub/reader-r2.json";
import { MeetingPreview } from "../../pages/cores/history/MeetingPreview";
import listAppTape from "./fixtures/meetings-hub/list-app.json";
import hs170 from "./fixtures/meetings-hub/hs170.json";
import guidePreview from "../walk/__fixtures__/meetings.preview.json";
import hs172 from "./fixtures/meetings-hub/hs172.json";
import p17t from "./fixtures/meetings-hub/p17t.json";
import successor from "./fixtures/meetings-hub/summary-successor.json";
import p17tReady from "./fixtures/meetings-hub/p17t-ready.json";
import lookedAt from "./fixtures/meetings-hub/looked-at.json";
import sinceLast from "./fixtures/meetings-hub/since-last.json";
import prepared from "./fixtures/meetings-hub/prepared.json";
import preparedFailed from "./fixtures/meetings-hub/prepared-failed.json";
import comingUp from "./fixtures/coming-up/coming-up.json";
import settingsWire from "./fixtures/settings-wire/settings.json";
import { ComingUp } from "../../pages/cores/history/ComingUp";
import { meetingRowView } from "../../pages/cores/history/CatalogRail";
import { appWalk } from "../walk/appWalks";
import { stepWindow } from "../walk/walk";
import { clockAt, CLOCK } from "../../test/clock";

vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: vi.fn(),
}));
const frameListeners = new Map<string, Set<(frame: { data: unknown }) => void>>();
const subscribe = (type: string, listener: (frame: { data: unknown }) => void) => {
  const set = frameListeners.get(type) ?? new Set();
  set.add(listener);
  frameListeners.set(type, set);
  return () => set.delete(listener);
};
vi.mock("../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
const emit = (type: string) => frameListeners.get(type)?.forEach((listener) => listener({ data: {} }));

type Fixture = Record<string, unknown> & { _now: string };
type Call = { path: string; init?: { method?: string; json?: unknown } };

/** The hub, as captured: each GET answers its captured body. The list read
 *  carries `limit=100` and the face's own params, so it is matched by its
 *  base; every other read is matched by its exact path. */
function hub(fixture: Record<string, unknown>, overrides: Record<string, unknown> = {}): Call[] {
  const calls: Call[] = [];
  const bodies: Record<string, unknown> = { ...fixture, ...overrides };
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: Call["init"]) => {
    const url = String(path);
    calls.push({ path: url, init });
    if (init?.method === "POST") {
      if (url.endsWith("/intelligence/run")) {
        // MeetingIntelService.run_intelligence (meeting_intel_service.py:268).
        // Captured from the SAME boot as the GET bodies: a meeting with words
        // and an assigned engine answers its admitted planned_route, never null.
        const answer = bodies[`POST ${url}`];
        if (answer === undefined) throw new Error(`no captured run answer for ${url}`);
        return answer as never;
      }
      if (url === "/api/notes") return { note: { id: "prepared-note" } } as never;
      if (url.endsWith("/transcribe")) return (bodies["POST /transcribe"] as { body: unknown })?.body as never;
      return {} as never;
    }
    if (url.startsWith("/api/meetings?") && !url.includes("parked=true")) return bodies["/api/meetings?limit=100"] as never;
    if (url in bodies) return bodies[url] as never;
    // The record's own read (`useMeetingData`) asks `/api/meetings/<id>`
    // with no query; the hub serves an unparked meeting the same body with or
    // without `include_parked` (it only widens the lookup to parked rows).
    if (/^\/api\/meetings\/[^/?]+$/.test(url) && `${url}?include_parked=true` in bodies) {
      return bodies[`${url}?include_parked=true`] as never;
    }
    return {} as never;
  });
  return calls;
}

function Shell({ children }: { children: ReactNode }) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <WingSlotContext.Provider value={setWings}>
      {wings}
      {children}
    </WingSlotContext.Provider>
  );
}

const hostedMeetingsRow: SurfaceRow = {
  key: "review-meetings",
  id: "surface-meetings",
  title: "Meetings",
  glyph: "M",
  eyebrow: "Meetings",
  Core: lazy(async () => ({ default: HistoryCore })),
};

/** The actual SurfaceWindowHost is part of this fence. A MeetingRecord-only
 * render misses the host's wing slot and the scope round-trip that desktop
 * Back must perform. */
function HostedMeetings() {
  const scope = useDesk((state) => state.windowsById[hostedMeetingsRow.id]?.scope ?? undefined);
  useEffect(() => {
    vi.mocked(openSurfaceOr).mockImplementation((key, _href, nextScope) => {
      useDesk.getState().openSurfaceWindow(key, nextScope);
    });
    useDesk.getState().openSurfaceWindow("review-meetings", "meeting:m-saved-outcomes");
  }, []);
  return (
    <div className="desk-next">
      <SurfaceWindowHost row={hostedMeetingsRow} scope={scope} items={EMPTY_ITEMS} />
    </div>
  );
}

/** Every <button> that is not the library Button (UX-CANON A.1); the rig's
 *  own probe: `.btn`, `.btn--chrome` or the library MicButton `.desk-mic`. */
function rawButtons(root: ParentNode = document): string[] {
  return [...root.querySelectorAll("button")]
    .filter((b) => !b.classList.contains("btn") && !b.classList.contains("btn--chrome") && !b.classList.contains("desk-mic"))
    .map((b) => (b.textContent ?? "").trim().slice(0, 40));
}

async function readerTab(label: string) {
  fireEvent.click(await screen.findByRole("tab", { name: label }));
}
const readerAction = meetingAction;
async function recordAction(label: string, press = true) {
  fireEvent.click(within(screen.getByTestId("meeting-toolbar")).getByRole("button", { name: "Actions ▾" }));
  const item = screen.getByRole("menuitem", { name: label });
  if (press) fireEvent.click(item);
}

const stateTokens = () => [...document.querySelectorAll("[data-testid='state-token']")].map((t) => (t.textContent ?? "").trim());

beforeEach(() => {
  vi.mocked(apiFetch).mockReset();
  vi.mocked(openPrimitive).mockReset();
  vi.mocked(openSurfaceOr).mockReset();
  useDesk.setState({ windowsById: {} } as never);
  frameListeners.clear();
  forgetExecutedReceipts();
});
afterEach(() => {
  vi.useRealTimers();
});

function at(fixture: Fixture) {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(fixture._now));
}

describe("the Meetings list over the HS-170 seed", () => {
  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (the list half, 1440) */
  it("Records uses one selection list with quiet empty state and no row controls", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const toolbar = await screen.findByRole("toolbar", { name: "Meetings" });
    // The page grammar is retired: no headline, no week tiles.
    expect(screen.queryByTestId("meetings-headline")).toBeNull();
    expect(screen.queryByTestId("meetings-week")).toBeNull();
    const offWords = await screen.findByTestId("meeting-row-m-off-words");
    expect(screen.getByRole("grid", { name: "Meetings" })).toContainElement(offWords);
    expect(offWords.querySelector(".surface-spine")).toBeNull();
    expect(offWords.querySelector("button")).toBeNull();
    // The run verb is the picked meeting's plate, never the rail's.
    expect(screen.queryAllByTestId("run-intelligence-btn")).toHaveLength(0);
    // Nothing picked: one line and the verb that makes a meeting.
    expect(screen.queryByTestId("meetings-preview")).toBeNull();
    // The meeting with no words says so.
    const vendor = screen.getByTestId("meeting-row-m-no-transcript");
    expect(within(vendor).getByTestId("no-transcript-token").textContent).toBe("No transcript");
    // The dead capture says INTERRUPTED; no row says REC.
    expect(within(screen.getByTestId("meeting-row-m-dead-rec")).getByTestId("state-token").textContent).toBe("Interrupted");
    expect(stateTokens()).not.toContain("Rec");
    expect(document.body.textContent).not.toContain("0 SEG");
    expect(screen.getByRole("searchbox", { name: "Find a meeting" })).toBeTruthy();
    expect(within(toolbar).getByRole("button", { name: "Open" })).toBeDisabled();
    expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (S-3: host chip + the run POST) */
  it("the selected meeting runs its summary with the disclosed route", async () => {
    at(hs170 as Fixture); const calls = hub(hs170 as Fixture);
    render(<Shell><HistoryCore scope="meeting:m-off-words" /></Shell>);
    const run = await readerAction("Summarise", false); await waitFor(() => expect(run).toBeEnabled());
    expect(document.querySelector(".gadget-chip-egress")).toBeNull();
    expect(document.body.textContent).not.toContain("same_device");
    fireEvent.click(run);
    const route = hs170["/api/meetings/m-off-words?include_parked=true"].planned_route;
    await waitFor(() => expect(calls).toContainEqual({ path: "/api/meetings/m-off-words/intelligence/run", init: { method: "POST", json: { expected_selection_hash: route.selection_hash } } }));
  });

  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (row → the meeting) */
  it("one press selects the meeting; Return opens its window", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-saved-outcomes");
    fireEvent.click(row);
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(openSurfaceOr).not.toHaveBeenCalled();
    await screen.findByTestId("meeting-list-preview");
    fireEvent.keyDown(row, { key: "Enter" });
    // `openSourceRef` hands the shell the meeting scope; the one Meetings
    // surface shows it in its pane, the rail beside it.
    expect(openSurfaceOr).toHaveBeenCalledWith(
      "review-meetings", "/history", "meeting:m-saved-outcomes",
    );
  });
});

describe("the hosted meeting record returns to its list", () => {
  it("Back clears the real host scope and keeps the picked row marked", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<HostedMeetings />);
    await screen.findByTestId("meeting-toolbar");
    await recordAction("All meetings", false);
    const back = screen.getByRole("menuitem", { name: "All meetings" });
    expect(screen.getByTestId("meeting-toolbar").closest(".desk-surface-window")).toBeTruthy();

    fireEvent.click(back);

    await waitFor(() => {
      expect(screen.queryByTestId("meeting-record-back")).toBeNull();
      expect(screen.getByTestId("meetings-toolbar")).toBeTruthy();
    });
    expect(screen.getByTestId("meeting-row-m-saved-outcomes")).toHaveAttribute("data-selected", "true");
  });
});

describe("the meeting window over the HS-170 seed", () => {
  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (the detail half) */
  it("gate proposals use selection verbs and the transcript has its own seat", async () => {
    at(hs170 as Fixture); hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} /></Shell>);
    await readerTab("Proposals");
    const grid = screen.getByRole("grid", { name: "Proposals" });
    const rows = within(grid).getAllByRole("row").filter(row => row.hasAttribute("data-object-id"));
    expect(rows).toHaveLength(3); expect(rows.every(row => !row.querySelector("button"))).toBe(true);
    fireEvent.click(rows[0]);
    expect(screen.getByRole("button", { name: "Decide" })).toBeEnabled();
    expect(screen.getByRole("button", { name: "Dismiss" })).toBeEnabled();
    expect(grid).toHaveTextContent("Decide: the PostgreSQL migration date");
    await readerTab("Transcript"); expect(screen.getAllByTestId("transcript-speaker").length).toBeGreaterThanOrEqual(2);
    expect(rawButtons()).toEqual([]);
  });
});

it("the collection review total includes tasks and decisions without calling them all tasks", async () => {
  hub(readerR3); render(<Shell><HistoryCore /></Shell>);
  await screen.findByTestId("meeting-row-reader");
  expect(within(screen.getByTestId("meeting-row-reader")).getByTestId("state-token")).toHaveTextContent("To confirm");
  expect(screen.getByTestId("meetings-status")).toHaveTextContent("2 items to confirm");
  expect(screen.getByTestId("meetings-status")).not.toHaveTextContent("2 tasks to confirm");
  expect(within(screen.getByTestId("meetings-status")).getByText("2 items to confirm").querySelector(".kit-dot")).toHaveAttribute("data-tone", "ask");
});

describe("the meeting after a run (HS-172 seed)", () => {
  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingAfterRun::test_meeting_ran_with_proposals (the list half, both widths) */
  it("the list names tasks to confirm without zero counters or host labels", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-ran");
    const token = within(row).getByTestId("state-token").textContent ?? "";
    expect(token).toBe("To confirm");
    const body = document.body.textContent ?? "";
    expect(body).not.toContain("0 NEEDS");
    expect(body).not.toContain("LOCAL");
    expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingAfterRun::test_meeting_ran_with_proposals[1440] (the detail) */
  it("saved summaries stay quiet and proposals keep owner and date values in their seats", async () => {
    at(hs172 as Fixture); hub(hs172 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await readerTab("Decisions");
    expect(screen.queryByTestId("meeting-summary-state")).toBeNull();
    await waitFor(() => expect(screen.getByRole("grid", { name: "Decisions" })).toHaveTextContent("cut-over on the 12th"));
    await readerTab("Tasks");
    const grid = screen.getByRole("grid", { name: "Tasks to confirm" });
    const rows = within(grid).getAllByRole("row").filter(row => row.hasAttribute("data-object-id"));
    expect(rows).toHaveLength(2); fireEvent.click(rows[0]);
    expect(screen.getByRole("button", { name: "Confirm" })).toBeEnabled();
    expect(await readerAction("Dismiss", false)).toBeEnabled(); screen.queryByRole("menu") && fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
    expect(document.body.textContent).not.toContain("192.168.1.43"); expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingQueued::test_meeting_queued */
  it("a queued meeting: QUEUED on the row and in the strip, no REMAINING, a Skip verb", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    const list = render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-queued");
    expect(within(row).getByTestId("state-token").textContent).toContain("Queued");
    // A running summary keeps its live mark and the shared steel meaning.
    expect(within(row).getByTestId("state-token")).toHaveAttribute("data-tone", "info");
    expect(within(row).getByTestId("state-token")).toHaveAttribute("data-live");
    list.unmount();
    render(<Shell><MeetingRecord meetingId="m-queued" onClose={() => undefined} /></Shell>);
    await waitFor(() => expect(screen.getByTestId("meeting-summary-state").textContent).toBe("Summary queued"));
    expect(document.body.textContent).not.toContain("REMAINING");
    await recordAction("Skip summary", false);
    expect(screen.getByRole("menuitem", { name: "Skip summary" })).not.toHaveAttribute("aria-disabled", "true");
    screen.queryByRole("menu") && fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
  });
});

describe("the summary face (HS-201-04 seed shapes)", () => {
  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again (station 1-2 on the record) */
  it("the record draws no route chip and the click sends the hash the route carried", async () => {
    at(hs170 as Fixture);
    const calls = hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-off-words" onClose={() => undefined} /></Shell>);
    await readerAction("Summarise", false);
    expect(screen.queryByTestId("detail-route")).toBeNull();
    expect(document.body.textContent).not.toContain("THIS DEVICE");
    const detail = (hs170 as Fixture)["/api/meetings/m-off-words?include_parked=true"] as { planned_route: { selection_hash: string } };
    fireEvent.click(await readerAction("Summarise", false));
    await waitFor(() =>
      expect(calls).toContainEqual({
        path: "/api/meetings/m-off-words/intelligence/run",
        init: { method: "POST", json: { expected_selection_hash: detail.planned_route.selection_hash } },
      }),
    );
  });

  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again (station 6: the footer chip is not a constant) */
  it("the Meetings status bar names no host, even for a LAN route (owner ruling 2026-10-25)", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    const first = render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    const footerChip = () => (document.querySelector(".kit-statusbar .gadget-chip-egress")?.textContent ?? "").trim();
    await waitFor(() => expect(footerChip()).toBe(""));
    first.unmount();
    // The same rows with the route's lead leg on a LAN host (the shape is the
    // captured one; only the host value differs): still no chip.
    const listed = (hs170 as Fixture)["/api/meetings?limit=100"] as { meetings: Array<Record<string, unknown>> };
    const lan = {
      ...listed,
      meetings: listed.meetings.map((m) => {
        const route = m.planned_route as { legs: Array<Record<string, unknown>> };
        return { ...m, planned_route: { ...route, legs: [{ ...route.legs[0], host: "192.168.1.43", boundary: "lan" }] } };
      }),
    };
    const detailKey = "/api/meetings/m-off-words?include_parked=true";
    const detail = (hs170 as Fixture)[detailKey] as Record<string, unknown>;
    const detailRoute = detail.planned_route as { legs: Array<Record<string, unknown>> };
    hub(hs170 as Fixture, {
      "/api/meetings?limit=100": lan,
      [detailKey]: { ...detail, planned_route: { ...detailRoute, legs: [{ ...detailRoute.legs[0], host: "192.168.1.43", boundary: "lan" }] } },
    });
    // The picked meeting: its status bar names no host either.
    render(<Shell><HistoryCore scope="meeting:m-off-words" /></Shell>);
    await screen.findByTestId("meeting-toolbar");
    const plate = await screen.findByTestId("meeting-toolbar");
    const verb = await readerAction("Summarise", false);
    expect(document.querySelector(".kit-statusbar .gadget-chip-egress")).toBeNull();
    expect(screen.queryByTestId("meeting-status")?.textContent ?? "").not.toContain("192.168.1.43");
    // The press that leaves the device names the host in its hover title.
    expect(verb.getAttribute("title")).toContain("192.168.1.43");
  });

  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_import_transcribes_then_queues_the_disclosed_summary (station 1: the Import door) */
  it("the head's Import opens the file picker at once; the chosen file opens the form", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    const picker = screen.getByTestId("meetings-import-picker") as HTMLInputElement;
    const opened = vi.spyOn(picker, "click").mockImplementation(() => undefined);
    fireEvent.click(within(screen.getByRole("toolbar", { name: "Meetings" })).getByRole("button", { name: "Import" }));
    // Capture C3: one press opens the picker; no wing switch, no drop well.
    expect(opened).toHaveBeenCalledTimes(1);
    expect(document.querySelector(".surface-dropwell")).toBeNull();
    fireEvent.change(picker, { target: { files: [new File(["RIFF"], "core_path_smoke_16k.wav", { type: "audio/wav" })] } });
    expect(await screen.findByRole("textbox", { name: "Title" })).toBeTruthy();
    expect(screen.getByTestId("import-when")).toBeTruthy();
  });
});

describe("Import asks when it was (betterment/capture C3)", () => {
  // Thursday 15 October 2026, 10:00 local: the 1:1 the capture walk dated Saturday.
  const thursday = new Date(2026, 9, 15, 10, 0);

  async function chooseInPicker(file: File) {
    const calls = hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    const picker = screen.getByTestId("meetings-import-picker") as HTMLInputElement;
    vi.spyOn(picker, "click").mockImplementation(() => undefined);
    fireEvent.click(screen.getByTestId("meetings-import"));
    fireEvent.change(picker, { target: { files: [file] } });
    const when = (await screen.findByTestId("import-when")) as HTMLInputElement;
    return { calls, when };
  }

  function importBody(calls: Call[]): FormData {
    const post = calls.find((c) => c.path === "/api/meetings/import" && c.init?.method === "POST");
    expect(post).toBeTruthy();
    return (post!.init as unknown as { body: FormData }).body;
  }

  it("fills from the file's modified time and sends it as started_at_ms", async () => {
    at(hs170 as Fixture);
    const file = new File(["Me: Thanks for the time, Theo."], "one-on-one-theo.txt", {
      type: "text/plain", lastModified: thursday.getTime(),
    });
    const { calls, when } = await chooseInPicker(file);
    await waitFor(() => expect(when.value).toBe("2026-10-15T10:00"));
    fireEvent.click(screen.getByRole("button", { name: "Import" }));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/meetings/import")).toBe(true));
    expect(importBody(calls).get("started_at_ms")).toBe(String(thursday.getTime()));
  });

  it("a date in the file name wins over the modified time", async () => {
    at(hs170 as Fixture);
    const file = new File(["Me: hello"], "1on1-theo-2026-10-15 10.00.txt", {
      type: "text/plain", lastModified: new Date(2026, 9, 17, 20, 22).getTime(),
    });
    const { when } = await chooseInPicker(file);
    await waitFor(() => expect(when.value).toBe("2026-10-15T10:00"));
  });

  it("a date in a VTT header wins over the name and the modified time", async () => {
    at(hs170 as Fixture);
    const vtt = "WEBVTT\n\nNOTE recorded 2026-10-15T10:00\n\n00:00:00.000 --> 00:00:04.000\n<v Me>Thanks, Theo.\n";
    const file = new File([vtt], "export-2026-10-17.vtt", {
      type: "text/vtt", lastModified: new Date(2026, 9, 17, 20, 22).getTime(),
    });
    const { when } = await chooseInPicker(file);
    await waitFor(() => expect(when.value).toBe("2026-10-15T10:00"));
  });

  it("the owner can change the date before Import", async () => {
    at(hs170 as Fixture);
    const file = new File(["Me: hello"], "notes.txt", { type: "text/plain", lastModified: thursday.getTime() });
    const { calls, when } = await chooseInPicker(file);
    await waitFor(() => expect(when.value).toBe("2026-10-15T10:00"));
    fireEvent.change(when, { target: { value: "2026-10-14T16:30" } });
    fireEvent.click(screen.getByRole("button", { name: "Import" }));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/meetings/import")).toBe(true));
    expect(importBody(calls).get("started_at_ms")).toBe(String(new Date(2026, 9, 14, 16, 30).getTime()));
  });

  it("a file dropped on the Meetings window opens the same form", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    const file = new File(["Me: hello"], "one-on-one-theo.txt", { type: "text/plain", lastModified: thursday.getTime() });
    fireEvent.drop(screen.getByTestId("meetings-drop"), { dataTransfer: { files: [file] } });
    const when = (await screen.findByTestId("import-when")) as HTMLInputElement;
    await waitFor(() => expect(when.value).toBe("2026-10-15T10:00"));
    expect(rawButtons()).toEqual([]);
  });
});

describe("the import lands on the open record with no reload (HS-202-02)", () => {
  /* replaces: tests/e2e/test_hs202_02_first_use_glass.py::test_the_import_reaches_the_open_record_with_no_reload (the queued-summary leg) */
  it("an open record that read the meeting before its words catches up to the transcript on the hub's frame", async () => {
    at(p17tReady as Fixture);
    const before = (p17tReady as Fixture)["/api/meetings/p17-audio-only?include_parked=true"];
    const after = (p17tReady as Fixture)["after:/api/meetings/p17-audio-only?include_parked=true"];
    let current = before;
    hub(p17tReady as Fixture);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: Call["init"]) =>
      String(path).startsWith("/api/meetings/p17-audio-only") && !String(path).slice("/api/meetings/p17-audio-only".length).startsWith("/")
        ? (current as never) : base(path, init as never));
    render(<Shell><MeetingRecord meetingId="p17-audio-only" onClose={() => undefined} /></Shell>);
    await waitFor(() => expect(document.querySelector("[data-testid=meeting-toolbar]")).toBeTruthy());
    expect(document.body.textContent).not.toContain("we ship the speech fix on friday");
    await readerTab("Transcript");
    current = after;
    act(() => emit("desk_changed"));
    await waitFor(() => expect(document.body.textContent).toContain("we ship the speech fix on friday"), { timeout: 3000 });
  });
});

describe("an audio-only meeting is transcribed in place (PHILO-17)", () => {
  /* replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (step 1, the face) */
  it("speech not set up: the record says so and offers Set up speech · n MB, never Transcribe", async () => {
    at(p17t as Fixture);
    hub(p17t as Fixture);
    render(<Shell><MeetingRecord meetingId="p17-audio-only" onClose={() => undefined} /></Shell>);
    await screen.findByText("No transcript: speech is not set up");
    await readerAction("Audio and speech");
    const setup = await screen.findByTestId("meeting-transcribe-speech-setup-verb");
    expect(screen.getByRole("tabpanel")).toContainElement(setup);
    expect(setup.textContent?.trim()).toMatch(/^Set up speech · \d+ MB$/);
    expect(screen.queryByRole("button", { name: "Transcribe" })).toBeNull();
  });

  /* replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (step 2, the row at 1440) */
  it("speech ready: the picked audio-only meeting's plate is Transcribe", async () => {
    at(p17tReady as Fixture);
    hub(p17tReady as Fixture);
    render(<Shell><HistoryCore scope="meeting:p17-audio-only" /></Shell>);
    await screen.findByTestId("meeting-toolbar");
    const plate = await screen.findByTestId("meeting-toolbar");
    await readerAction("Audio and speech");
    const verb = await screen.findByTestId("meeting-transcribe-verb");
    expect(screen.getByRole("tabpanel")).toContainElement(verb);
    expect(verb.textContent?.trim()).toBe("Transcribe");
  });

  /* replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (steps 2-3, the record) */
  it("speech ready: the record's Transcribe POSTs, and the transcript lands in the SAME record", async () => {
    at(p17tReady as Fixture);
    const calls = hub(p17tReady as Fixture);
    const after = (p17tReady as Fixture)["after:/api/meetings/p17-audio-only?include_parked=true"];
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    let transcribed = false;
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: Call["init"]) => {
      const url = String(path);
      if (url.endsWith("/transcribe") && init?.method === "POST") transcribed = true;
      if (transcribed && (url === "/api/meetings/p17-audio-only?include_parked=true" || url === "/api/meetings/p17-audio-only")) {
        calls.push({ path: url, init });
        return after as never;
      }
      return base(path, init as never);
    });
    render(<Shell><MeetingRecord meetingId="p17-audio-only" onClose={() => undefined} /></Shell>);
    await readerAction("Audio and speech");
    const verb = await screen.findByTestId("meeting-transcribe-verb");
    expect(verb.textContent?.trim()).toBe("Transcribe");
    fireEvent.click(verb);
    await readerTab("Transcript");
    await waitFor(() => expect(document.body.textContent).toContain("we ship the speech fix on friday"));
    expect(calls).toContainEqual({ path: "/api/meetings/p17-audio-only/transcribe", init: { method: "POST" } });
    expect(screen.queryByTestId("meeting-transcribe-verb")).toBeNull();
    expect(screen.queryByTestId("meeting-speech-missing")).toBeNull();
  });
});

describe("what the summary read (betterment/capture C2)", () => {
  /* The run receipt the hub served for Friday's summary
   * (fixtures/meetings-hub/looked-at.json, recorded by
   * tests/integration/test_desk_meetings.py), on the HS-172 record. */
  // Betterment D3: Thursday's promises are kept on arrival now, and the
  // recorded receipt reads Thursday and Wednesday (re-recorded).
  it("the Context seat lists the actual sources and dates with Open on the selection", async () => {
    at(hs172 as Fixture); hub(hs172 as Fixture, { "/api/meetings/m-ran?include_parked=true": { ...hs172["/api/meetings/m-ran?include_parked=true"], run_receipt: lookedAt.run_receipt } });
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await readerTab("Context");
    const rows = screen.getByRole("grid", { name: "Meeting context" });
    for (const source of lookedAt.run_receipt.looked_at) expect(rows).toHaveTextContent(source.title);
    expect(rows.querySelector('[role="row"] button')).toBeNull();
    fireEvent.click(within(rows).getAllByRole("row").find(row => row.hasAttribute("data-object-id"))!);
    expect(screen.getByRole("button", { name: "Open" })).toBeEnabled();
  });

  it("no memory read adds no Context seat or zero counter", async () => {
    hub(hs170 as Fixture); render(<Shell><MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} /></Shell>);
    await screen.findByTestId("meeting-toolbar");
    expect(screen.queryByRole("tab", { name: "Context" })).toBeNull(); expect(document.body.textContent).not.toMatch(/Looked at.*0/);
  });
});

describe("Since last time (betterment/capture C6)", () => {
  /* Friday's aftercare as the hub served it
   * (fixtures/meetings-hub/since-last.json, recorded by
   * tests/integration/test_desk_meetings.py), on the HS-172 record. */
  const since = sinceLast.aftercare.since_last_meeting;
  it("Context retains the prior meeting and closed, open and new outcomes", async () => {
    at(hs172 as Fixture); hub(hs172 as Fixture, { "/api/meetings/m-ran/aftercare": sinceLast.aftercare });
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await readerTab("Context");
    const aftercare = sinceLast.aftercare.since_last_meeting;
    const grid = screen.getByRole("grid", { name: "Meeting context" });
    expect(grid).toHaveTextContent(aftercare.previous_meeting.title);
    for (const row of [...aftercare.closed_actions, ...aftercare.still_open_actions, ...aftercare.new_actions, ...aftercare.new_decisions]) expect(grid).toHaveTextContent(row.task);
    expect(grid.querySelector('[role="row"] button')).toBeNull();
  });

  it("a meeting with no previous meeting adds no prior-meeting facts", async () => {
    hub(hs170 as Fixture); render(<Shell><MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} /></Shell>);
    await screen.findByTestId("meeting-toolbar"); expect(screen.queryByText(/Since last/)).toBeNull();
  });
});

describe("the meeting prepares its Results (betterment/capture C5, C5b)", () => {
  /* The architecture review as a real hub served it after the LAN engine
   * wrote its summary and its drafts (fixtures/meetings-hub/prepared.json,
   * recorded by tests/integration/test_meeting_plugins_engines.py). */
  const fixture = prepared as unknown as Fixture;
  const PREPARED = "/api/meetings/c5-review/prepared";
  const render5 = (overrides: Record<string, unknown> = {}) => {
    at(fixture); const calls = hub(fixture, overrides);
    render(<Shell><MeetingRecord meetingId="c5-review" onClose={() => undefined} /></Shell>); return calls;
  };

  it("a populated result list has no selection instruction or inactive result verbs", async () => {
    render5(); await readerTab("Results");
    await screen.findByTestId("meeting-prepared-followup");
    expect(screen.queryByText("Select a result")).toBeNull();
    const toolbar = screen.getByRole("toolbar", { name: "Prepared results actions" });
    expect(within(toolbar).getByRole("button", { name: "Read" })).toBeDisabled();
    expect(within(toolbar).queryByRole("button", { name: "Write again" })).toBeNull();
    expect(within(toolbar).getByRole("button", { name: "Prepare" })).toBeEnabled();
    fireEvent.click(screen.getByTestId("meeting-prepared-followup"));
    expect(await screen.findByTestId("meeting-prepared-draft")).toHaveTextContent("Adopt idempotent retries");
    expect(within(toolbar).getByRole("button", { name: "Copy" })).toBeEnabled();
    expect(within(toolbar).queryByRole("button", { name: "Write again" })).toBeNull();
  });

  it("prepared results are selection rows and the selected draft is readable", async () => {
    render5(); await readerTab("Results");
    const result = await screen.findByTestId("meeting-prepared-followup"); fireEvent.click(result);
    expect(result.querySelector("button")).toBeNull();
    expect(await screen.findByTestId("meeting-prepared-draft")).toHaveTextContent("Adopt idempotent retries");
    expect(screen.getByRole("button", { name: "Send…" })).toBeEnabled();
    expect(await readerAction("Open as note", false)).toBeEnabled(); screen.queryByRole("menu") && fireEvent.keyDown(screen.getByRole("menu"), { key: "Escape" });
  });

  it("Draft ready opens the result that serves the selected commitment", async () => {
    render5(); await readerTab("Commitments");
    const grid = screen.getByRole("grid", { name: "Commitments" });
    const rows = within(grid).getAllByRole("row").filter(row => row.hasAttribute("data-object-id"));
    const served = prepared["/api/meetings/c5-review/prepared"].results.find(row => row.kind === "adr")!;
    const action = served.serves![0];
    fireEvent.click(rows.find(row => row.getAttribute("data-object-id")?.includes(action))!);
    await readerAction("Draft ready");
    expect(await screen.findByTestId("meeting-prepared-draft")).toHaveTextContent("Client-side idempotency")
  });

  it("a prepared note is made once and Send opens its existing preview seat", async () => {
    const calls = render5(); await readerTab("Results");
    fireEvent.click(await screen.findByTestId("meeting-prepared-followup"));
    await readerAction("Open as note");
    await waitFor(() => expect(calls.filter(call => call.path === "/api/notes" && call.init?.method === "POST")).toHaveLength(1));
    await readerAction("Open as note");
    expect(calls.filter(call => call.path === "/api/notes" && call.init?.method === "POST")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Send…" }));
    await screen.findByTestId("send-well"); await waitFor(() => expect(screen.queryByTestId("meeting-status")).toBeNull()); expect(calls.filter(call => call.path.endsWith("/send") && call.init?.method === "POST")).toHaveLength(0);
  });

  it("a writing draft keeps its live reading seat", async () => {
    render5({ [PREPARED]: fixture[`${PREPARED}#writing`] });
    await readerTab("Results"); fireEvent.click(await screen.findByTestId("meeting-prepared-adr"));
    expect(await screen.findByRole("log", { name: "Prepared draft" })).toHaveTextContent("Writing draft");
  });

  it("a failed draft retains its reason and retries on the shown route", async () => {
    const calls = render5({ [PREPARED]: preparedFailed.prepared }); await readerTab("Results");
    fireEvent.click(await screen.findByTestId("meeting-prepared-adr"));
    expect(await screen.findByRole("alert")).toHaveTextContent("The engine did not finish this draft.");
    expect(screen.getByTestId("meeting-status")).toHaveTextContent("Draft failed");
    expect(screen.getByTestId("meeting-status")).not.toHaveTextContent("The engine did not finish this draft.");
    await readerAction("Write again");
    await waitFor(() => expect(calls.some(call => call.path === "/api/meetings/c5-review/prepare" && call.init?.method === "POST")).toBe(true));
  });

  it("Prepare offers only the kinds the hub says can be prepared", async () => {
    const calls = render5(); await readerTab("Results");
    const available = prepared["/api/meetings/c5-review/prepared"].can_prepare[0];
    await readerAction("Prepare");
    fireEvent.click(await screen.findByRole("menuitem", { name: `Prepare ${available.label}` }));
    await waitFor(() => expect(calls).toContainEqual({ path: "/api/meetings/c5-review/prepare", init: { method: "POST", json: { plugin_id: available.plugin_id, expected_selection_hash: prepared["/api/meetings/c5-review?include_parked=true"].planned_route.selection_hash } } }));
  });

  it("the reader has one contents strip and no retired Outcomes or Artifacts wing", async () => {
    render5(); await readerTab("Summary");
    expect(screen.getAllByRole("tablist")).toHaveLength(1);
    expect(screen.queryByRole("tab", { name: /Outcomes|Artifacts/ })).toBeNull();
  });
});

describe("One home for recording: Meetings ▸ Record (betterment/capture C7)", () => {
  // The hub's own answers at its real clock
  // (tests/unit/test_desk_chair.py::test_coming_up_arms_cancels_and_names_a_failed_fire):
  // a fire that raised, three calendar meetings ahead, the arm and the cancel.
  type Phase = "before" | "armed" | "cancelled";
  const pad2 = (n: number) => String(n).padStart(2, "0");
  const hhmm = (iso: string) => clockAt(iso);
  const wire = comingUp as unknown as Record<string, any>;

  function recordHub() {
    let phase: Phase = "before";
    const writes: Array<{ path: string; method: string; json?: unknown }> = [];
    vi.mocked(apiFetch).mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
      const url = String(path);
      const method = init?.method ?? "GET";
      if (method !== "GET") {
        writes.push({ path: url, method, json: init?.json });
        if (url === "/api/scheduled-recordings") { phase = "armed"; return structuredClone(wire["POST /api/scheduled-recordings"]); }
        if (url.endsWith("/cancel")) { phase = "cancelled"; return structuredClone(wire["POST /api/scheduled-recordings/<id>/cancel"]); }
        return {} as never;
      }
      if (url === "/api/door") return structuredClone(wire[`GET /api/door (${phase})`]);
      if (url === "/api/scheduled-recordings") return structuredClone(wire["GET /api/scheduled-recordings (before)"]);
      if (url === "/api/settings") return structuredClone(settingsWire) as never;
      if (url.startsWith("/api/meetings?") && !url.includes("parked=true")) return (hs170 as Fixture)["/api/meetings?limit=100"] as never;
      return {} as never;
    });
    return writes;
  }

  async function openRecordWing() {
    useDesk.setState({ comingUp: null, scheduledRecordings: [] } as never);
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(wire._now));
    const writes = recordHub();
    render(<Shell><HistoryCore /><div data-testid="capture"><ComingUp limit={2} data-testid="arrival-coming-up" /></div></Shell>);
    fireEvent.click(await screen.findByRole("tab", { name: "Record" }));
    const home = await screen.findByTestId("record-home");
    return { writes, home };
  }

  /** The list once read (before its first read it is an empty, busy section). */
  async function readList(testId: string): Promise<HTMLElement> {
    await waitFor(() => expect(screen.getByTestId(testId).getAttribute("aria-busy")).toBeNull());
    return screen.getByTestId(testId);
  }

  const rowOf = (root: HTMLElement, title: string) => {
    const row = within(root).getAllByRole("listitem").find((li) => (li.textContent ?? "").includes(title));
    if (!row) throw new Error(`no row ${title}`);
    return row;
  };

  it("Record, Import, Coming up with the failed fire first, Another time…, the auto-record switch; no drop-zone page", async () => {
    const { home } = await openRecordWing();
    expect(within(home).getByTestId("record-home-record").textContent).toContain("Record");
    expect(within(home).getByTestId("record-home-import").textContent).toBe("Import");
    expect(screen.queryByText("Drop it here, or browse")).toBeNull();
    const list = await readList("record-home-coming-up");
    await waitFor(() => expect(within(list).getAllByRole("listitem")).toHaveLength(4));
    expect(within(list).getAllByTestId("coming-up-title").map((t) => t.textContent)).toEqual([
      "Payments platform sync", "Platform design follow-up", "1:1 with Mira", "Architecture review",
    ]);
    const sync = wire["GET /api/scheduled-recordings (before)"].schedules.find((s: any) => s.id === "rec-sync");
    const failed = rowOf(list, "Payments platform sync");
    expect(within(failed).getByTestId("coming-up-state").textContent)
      .toBe(`Did not record · ${hhmm(sync.did_not_record.at)} · ${sync.did_not_record.reason}`);
    expect(within(failed).getByRole("button", { name: "Record now" })).toBeTruthy();
    // The reason is one of four plain phrases, never the exception text.
    expect(["No microphone", "Another recording is running", "HoldSpeak was not running", "Something went wrong"])
      .toContain(sync.did_not_record.reason);
    expect(list.textContent).not.toMatch(/NoneType|Error|Traceback|attribute|'/);
    // Tomorrow's meeting says its day.
    expect(within(rowOf(list, "Architecture review")).getByTestId("coming-up-slot").textContent).toMatch(new RegExp(`^[A-Z][a-z]{2} ${CLOCK}$`));
    // The manual form, in place.
    fireEvent.click(within(home).getByRole("button", { name: "Another time…" }));
    expect(within(home).getByTestId("schedule-form-inline")).toBeTruthy();
    expect(within(home).getByTestId("schedule-create-submit").textContent).toBe("Schedule");
    // The calendar is set up, so the switch shows, read from the hub (Off).
    const toggle = (await within(home).findByRole("checkbox", { name: "Record every meeting on my calendar" })) as HTMLInputElement;
    expect(toggle.checked).toBe(false);
    expect(rawButtons()).toEqual([]);
  });

  it("an arm made where Today makes it shows in Meetings ▸ Record and Capture; Cancel in Meetings disarms both", async () => {
    const { home, writes } = await openRecordWing();
    const list = await readList("record-home-coming-up");
    const capture = await readList("arrival-coming-up");
    await waitFor(() => expect(within(capture).getAllByRole("listitem")).toHaveLength(2));
    expect(within(rowOf(list, "Platform design follow-up")).getByRole("button", { name: /when it starts/ })).toBeTruthy();

    // Today's NEXT ▸ Record when it starts calls this store verb (TodayView.tsx).
    await act(async () => { await useDesk.getState().armEventRecording("ev-followup"); });
    const armed = wire["GET /api/door (armed)"].upcoming.find((r: any) => r.id === "ev-followup");
    const word = `Records at ${hhmm(armed.armed.arms_at)}`;
    await waitFor(() => expect(within(rowOf(list, "Platform design follow-up")).getByTestId("coming-up-state").textContent).toBe(word));
    expect(within(rowOf(capture, "Platform design follow-up")).getByTestId("coming-up-state").textContent).toBe(word);
    expect(writes).toEqual([{ path: "/api/scheduled-recordings", method: "POST", json: { calendar_event_id: "ev-followup" } }]);

    fireEvent.click(within(rowOf(list, "Platform design follow-up")).getByRole("button", { name: "Cancel the recording of Platform design follow-up" }));
    await waitFor(() => expect(within(rowOf(capture, "Platform design follow-up")).queryByTestId("coming-up-state")).toBeNull());
    expect(within(rowOf(list, "Platform design follow-up")).queryByTestId("coming-up-state")).toBeNull();
    expect(within(rowOf(capture, "Platform design follow-up")).getByRole("button", { name: /when it starts/ })).toBeTruthy();
    expect(writes.map((w) => `${w.method} ${w.path}`)).toEqual([
      "POST /api/scheduled-recordings",
      `POST /api/scheduled-recordings/${armed.armed.recording_id}/cancel`,
    ]);
  });

  it("the auto-record switch writes meeting.auto_record", async () => {
    const { home, writes } = await openRecordWing();
    const toggle = (await within(home).findByRole("checkbox", { name: "Record every meeting on my calendar" })) as HTMLInputElement;
    fireEvent.click(toggle);
    await waitFor(() => expect(writes).toEqual([{ path: "/api/settings", method: "PUT", json: { meeting: { auto_record: "all_calendar" } } }]));
    expect(toggle.checked).toBe(true);
  });
});

describe("DELIGHT 2 small joy: Try again turns the red dot blue, then green", () => {
  // The recorded HS-170 rows: m-saved-clean (complete, nothing to review)
  // and m-queued (queued). The failed row is m-saved-clean with the one field
  // the hub writes on a failed run (`intel_status: "failed"`, helpers.ts
  // stateToken).
  const rows = (hs170 as Fixture)["/api/meetings?limit=100"] as { meetings: Array<Record<string, unknown>> };
  const clean = rows.meetings.find((m) => m.id === "m-saved-clean")!;
  const queued = rows.meetings.find((m) => m.id === "m-queued")!;
  const failed: Record<string, unknown> = { ...clean, intel_status: "failed" };

  it("failed is red with Retry; the press makes it blue and live; the stored summary is green", () => {
    const before = meetingRowView(failed, { runningId: null });
    expect(before).toMatchObject({ tone: "fail", live: false });
    // The press: this client's run, before the hub's next read.
    const pressed = meetingRowView(failed, { runningId: String(failed.id) });
    expect(pressed).toMatchObject({ tone: "info", live: true, isRunning: true });
    // The poll reads the hub's queued state: still blue.
    expect(meetingRowView(queued, { runningId: null })).toMatchObject({ tone: "info", live: true });
    // The run settles: the recorded complete row is green, the dot is still.
    expect(meetingRowView(clean, { runningId: null })).toMatchObject({ tone: "ok", live: false });
  });

  it("a run that cannot drain stays red, never a calm blue", () => {
    expect(meetingRowView(failed, { runningId: String(failed.id), drainerAbsent: true })).toMatchObject({ tone: "fail", live: false });
  });
});


describe("the meeting ledger and its reading doors", () => {
  it("the Meetings guide selects a row before it shows the summary and actions", async () => {
    // The seeded guide rig records both list and detail. The older hs170
    // tape has no stored summary, so it cannot prove the summary's ring.
    hub(guidePreview);
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meetings-toolbar");
    const script = appWalk("review-meetings")!;
    for (const step of script.steps) {
      expect(stepWindow(step, "surface-meetings")).toBe("surface-meetings");
      const selector = (target: string) => /^[a-z][a-z0-9-]*$/.test(target) ? `[data-testid="${target}"]` : target;
      if (step.press) {const row = document.querySelector<HTMLElement>(selector(step.press.target)); expect(row).toBeTruthy(); fireEvent.click(row!);}
      await waitFor(() => expect(document.querySelector(selector(step.highlight!.target))).toBeTruthy());
      expect(step.ask).toBeUndefined();
    }
  });

  it("Summary and Transcript are whole seats in the same object window", async () => {
    at(prepared as Fixture); hub(prepared as Fixture);
    render(<Shell><MeetingRecord meetingId="c5-review" onClose={() => undefined} /></Shell>);
    const wire = prepared["/api/meetings/c5-review?include_parked=true"];
    expect(await screen.findByTestId("meeting-summary")).toHaveTextContent(wire.intel.summary);
    await readerTab("Transcript"); expect((await screen.findAllByTestId("transcript-speaker")).length).toBeGreaterThan(0);
    expect(screen.queryByTestId("meeting-summary")).toBeNull();
    await readerTab("Summary"); expect(await screen.findByTestId("meeting-summary")).toHaveTextContent(wire.intel.summary);
  });

  it("a refused Confirm keeps its draft across reader tabs", async () => {
    at(hs172 as Fixture); hub(hs172 as Fixture);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path).endsWith("/confirm") ? Promise.reject(new Error("Hub unavailable")) : base(path, init));
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await readerTab("Decisions");
    const row = await screen.findByText("cut-over on the 12th"); fireEvent.click(row.closest('[role="row"]')!);
    await readerAction("Edit");
    fireEvent.change(screen.getByRole("textbox", { name: "Decision" }), { target: { value: "Keep this edit" } });
    await readerTab("Transcript"); await readerTab("Decisions");
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Keep this edit");
    fireEvent.click(within(screen.getByRole("region", { name: "Edit decision" })).getByRole("button", { name: "Confirm" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("textbox", { name: "Decision" })).toHaveValue("Keep this edit");
  });
});


describe("Records selection and recovery", () => {
  it("Summarise acts on the selection and posts its declared route", async () => {
    const calls = hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const toolbar = await screen.findByRole("toolbar", { name: "Meetings" });
    fireEvent.click(await screen.findByTestId("meeting-row-m-queued"));
    expect(within(toolbar).getByRole("button", { name: "Summarise" })).toBeDisabled();
    fireEvent.click(screen.getByTestId("meeting-row-m-off-words"));
    fireEvent.click(within(toolbar).getByRole("button", { name: "Summarise" }));
    const wire = hs170["/api/meetings?limit=100"].meetings.find((row) => row.id === "m-off-words")!;
    await waitFor(() => expect(calls).toContainEqual({
      path: "/api/meetings/m-off-words/intelligence/run",
      init: { method: "POST", json: { expected_selection_hash: wire.planned_route.selection_hash } },
    }));
    expect(await screen.findByTestId("meetings-run-receipt")).toHaveTextContent("Queued at");
  });

  it("previews on selection and opens on double-click", async () => {
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const normal = await screen.findByTestId("meeting-row-m-saved-clean");
    fireEvent.click(normal);
    expect(openSurfaceOr).not.toHaveBeenCalled();
    await waitFor(() => expect(screen.getByTestId("meeting-list-preview")).toHaveTextContent("No summary"));
    fireEvent.doubleClick(normal);
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:m-saved-clean");
  });

  it("a failed Delete keeps the selection and can retry once, with Undo after success", async () => {
    const calls = hub(hs170 as Fixture);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    let fail = true;
    vi.mocked(apiFetch).mockImplementation((path, init) => {
      if (init?.method === "DELETE") {
        calls.push({ path: String(path), init });
        return fail ? Promise.reject(new Error("Hub unavailable")) : Promise.resolve({} as never);
      }
      return base(path, init);
    });
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-saved-clean");
    fireEvent.click(row);
    fireEvent.keyDown(row, { key: "Backspace" });
    await screen.findByTestId("meetings-park-receipt");
    expect(row).toHaveAttribute("aria-selected", "true");
    expect(row).toBeInTheDocument();
    fail = false;
    fireEvent.keyDown(row, { key: "Delete" });
    await waitFor(() => expect(screen.queryByTestId("meeting-row-m-saved-clean")).toBeNull());
    const receipt = screen.getByTestId("meetings-park-receipt");
    fireEvent.click(within(receipt).getByRole("button", { name: /Restore/ }));
    await waitFor(() => expect(calls.some((call) => call.path === "/api/meetings/m-saved-clean/restore" && call.init?.method === "POST")).toBe(true));
    expect(calls.filter((call) => call.init?.method === "DELETE")).toHaveLength(2);
  });
});

describe("Records tasks to confirm", () => {
  it("reads proposed tasks in a selection list and keeps a failed edit", async () => {
    const calls = hub(hs172 as Fixture);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path).endsWith("/edit")
      ? Promise.reject(new Error("Hub unavailable")) : base(path, init));
    render(<Shell><HistoryCore /></Shell>);
    fireEvent.click(await screen.findByTestId("meeting-row-m-ran"));
    fireEvent.click(screen.getByRole("button", { name: "Meeting contents" }));
    fireEvent.click(screen.getByRole("menuitemradio", { name: "Tasks to confirm" }));
    const proposal = hs172["/api/meetings/m-ran/follow-through-proposals"].proposals.find((row) => row.kind === "action")!;
    const row = await screen.findByTestId(`meeting-task-${proposal.id}`);
    expect(within(row).queryByRole("button")).toBeNull();
    fireEvent.click(row);
    const bar = screen.getByRole("toolbar", { name: "Tasks to confirm actions" });
    expect(within(bar).getByRole("button", { name: "Confirm" })).toBeEnabled();
    fireEvent.click(within(bar).getByRole("button", { name: "Edit" }));
    const task = screen.getByRole("textbox", { name: "Task" });
    fireEvent.change(task, { target: { value: "Keep this task edit" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Not saved");
    expect(task).toHaveValue("Keep this task edit");
    expect(calls.some((call) => call.path.endsWith("/confirm"))).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.queryByRole("textbox", { name: "Task" })).toBeNull();
    expect(screen.getByTestId(`meeting-task-${proposal.id}`)).toHaveTextContent(proposal.text);
  });

  it("withholds Send to… until the selected record has a saved summary", async () => {
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const bar = await screen.findByRole("toolbar", { name: "Meetings" });
    expect(within(bar).getByRole("button", { name: "Send to…" })).toBeDisabled();
    const row = await screen.findByTestId("meeting-row-m-saved-clean");
    fireEvent.click(row);
    expect(within(bar).getByRole("button", { name: "Send to…" })).toBeDisabled();
    fireEvent.contextMenu(row);
    expect(within(screen.getByRole("menu", { name: "Meetings actions" })).getByRole("menuitem", { name: "Send to…" })).toBeDisabled();
  });
});


describe("Deleted collection recovery", () => {
  it("keeps a failed Deleted read distinct from empty and retries in the same collection", async () => {
    hub(hs170 as Fixture);
    const original = vi.mocked(apiFetch).getMockImplementation()!;
    let unavailable = true;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path) === "/api/meetings?parked=true" && unavailable
      ? Promise.reject(new Error("Deleted meetings not read")) : original(path, init));
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-saved-clean");
    fireEvent.click(screen.getByRole("tab", { name: "Deleted" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Deleted meetings not read");
    expect(screen.queryByText("No deleted meetings")).toBeNull();
    unavailable = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("No deleted meetings")).toBeVisible();
    expect(screen.getByRole("tab", { name: "Deleted" })).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("tab", { name: "Records" }));
    expect(screen.getByTestId("meeting-row-m-saved-clean")).toBeVisible();
  });
});


it("Restore selects its acknowledged record and an older list read cannot remove it", async () => {
  const calls = hub(listAppTape, { "/api/meetings?limit=100": listAppTape["GET active while deleted"] });
  const original = vi.mocked(apiFetch).getMockImplementation()!;
  let refresh = false;
  let finishRead: (body: unknown) => void = () => {};
  vi.mocked(apiFetch).mockImplementation((path, init) => {
    if (String(path) === "/api/meetings?limit=100" && refresh)
      return new Promise(resolve => { finishRead = resolve; }) as never;
    if (String(path) === "/api/meetings/dana/restore" && init?.method === "POST") {
      calls.push({ path: String(path), init });
      return Promise.resolve(listAppTape["POST /api/meetings/dana/restore"]) as never;
    }
    return original(path, init);
  });
  render(<Shell><HistoryCore /></Shell>);
  await screen.findByTestId("meeting-row-platform");
  expect(screen.queryByTestId("meeting-row-dana")).toBeNull();
  fireEvent.click(screen.getByRole("tab", { name: "Deleted" }));
  fireEvent.click(await screen.findByTestId("meeting-row-dana"));
  refresh = true;
  act(() => window.dispatchEvent(new Event("focus")));
  fireEvent.click(within(screen.getByRole("toolbar", { name: "Meetings" })).getByRole("button", { name: "Restore" }));
  const restored = await screen.findByTestId("meeting-row-dana");
  await waitFor(() => expect(screen.getByRole("tab", { name: "Records" })).toHaveAttribute("aria-selected", "true"));
  expect(restored).toHaveAttribute("aria-selected", "true");
  await act(async () => finishRead(listAppTape["GET active while deleted"]));
  expect(screen.getByTestId("meeting-row-dana")).toHaveAttribute("aria-selected", "true");
  expect(within(screen.getByRole("toolbar", { name: "Meetings" })).getByRole("button", { name: "Send to…" })).toBeEnabled();
  expect(screen.getByTestId("meeting-list-preview")).toHaveTextContent("28 min");
  expect(calls.filter(call => call.init?.method === "POST")).toHaveLength(1);
  expect(screen.getByTestId("meetings-park-receipt")).toHaveTextContent("Restored at");
  fireEvent.change(screen.getByRole("searchbox", {name:"Find a meeting"}), {target:{value:"missing meeting"}});
  await waitFor(()=>expect(screen.queryByText(/Restored at/)).toBeNull());
});


describe("round 2 Records defects", () => {
  it("keeps the collection chrome and status while rows wait", async () => {
    hub(hs170 as Fixture);
    const original = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path) === "/api/meetings?limit=100"
      ? new Promise(() => {}) as never : original(path, init));
    render(<Shell><HistoryCore /></Shell>);
    expect(screen.getByRole("tab", { name: "Records" })).toBeVisible();
    expect(screen.getByRole("toolbar", { name: "Meetings" })).toBeVisible();
    expect(screen.queryByRole("columnheader", { name: "Meeting" })).toBeNull();
    expect(screen.getByTestId("meetings-status")).toBeVisible();
  });
  it("shows a failed tasks read in the kit state inside the task well", async () => {
    hub(hs172 as Fixture);
    const original = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => /outcome-review|follow-through-proposals/.test(String(path))
      ? Promise.reject(new Error("Hub unavailable")) : original(path, init));
    const meeting = hs172["/api/meetings?limit=100"].meetings[0];
    render(<MeetingPreview meeting={meeting} view="tasks" />);
    const failure = await screen.findByRole("alert");
    expect(failure.closest('.surface-action-notice[role="alert"]')).toBeTruthy();
    expect(within(failure).getByRole("button", { name: "Try again" })).toBeVisible();
  });
  it("shows the recorded summary failure reason in the selected pane", async () => {
    hub(readerR2);
    render(<MeetingPreview meeting={readerR2["/api/meetings/vendor"]} />);
    expect(await screen.findByText("The summary engine timed out.", { exact: true })).toBeVisible();
    expect(screen.getByTestId("meeting-list-preview")).not.toHaveTextContent("No summary");
  });
});

describe("the meeting object window", () => {
  it("selects a task inside a hosted object window without a menu notification loop", async () => {
    hub(hs172 as Fixture);
    render(<WindowIdContext.Provider value="reader-test"><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></WindowIdContext.Provider>);
    await readerTab("Tasks"); const row = await screen.findByTestId("meeting-task-" + hs172["/api/meetings/m-ran/follow-through-proposals"].proposals.find(row => row.kind === "action")!.id);
    fireEvent.click(row); expect(row).toHaveAttribute("aria-selected", "true");
    fireEvent.click(screen.getByRole("button", { name: "Edit" })); expect(screen.getByRole("textbox", { name: "Task" })).toBeVisible();
  });
  it("shows the saved failure reason and retries that meeting on its declared route", async () => {
    const path = "/api/meetings/m-off-words?include_parked=true";
    const original = hs170[path];
    const calls = hub(hs170 as Fixture, { [path]: { ...original, intel_status: readerR2["/api/meetings/vendor"].intel_status } });
    render(<MeetingRecord meetingId="m-off-words" onClose={() => undefined} />);
    const failure = await screen.findByTestId("meeting-summary-failure");
    expect(failure).toHaveTextContent("The summary engine timed out.");
    fireEvent.click(within(failure).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(calls).toContainEqual({ path: "/api/meetings/m-off-words/intelligence/run", init: { method: "POST", json: { expected_selection_hash: original.planned_route.selection_hash } } }));
  });
  it("closes Delete when its meeting changes and never deletes the new target on the old answer", async () => {
    const calls = hub(hs170 as Fixture);
    const { rerender } = render(<MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} />);
    const remove = await readerAction("Delete", false); await waitFor(() => expect(remove).toBeEnabled()); fireEvent.click(remove);
    expect(screen.getByRole("region", { name: /^Delete .+\?$/ })).toBeVisible();
    expect(screen.getByRole("button", { name: "Cancel" })).toHaveFocus();
    rerender(<MeetingRecord meetingId="m-off-words" onClose={() => undefined} />);
    await waitFor(() => expect(screen.queryByRole("region", { name: /^Delete .+\?$/ })).toBeNull());
    expect(calls.some(call => call.init?.method === "DELETE")).toBe(false);
    expect(await readerAction("Delete", false)).toHaveTextContent("Delete");
  });
});


describe("R3 reader feedback and actions", () => {
  const proposal = readerR3["/api/meetings/reader/outcome-review"].proposals;
  async function action(name: string) {
    const button = screen.queryByRole("button", { name });
    if (button) fireEvent.click(button);
    else { fireEvent.click(screen.getByRole("button", { name: "Actions ▾" })); fireEvent.click(screen.getByRole("menuitem", { name })); }
  }
  function rejectedWrites() {
    const calls = hub(readerR3); const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => init?.method === "POST" && /\/(confirm|edit)$/.test(path) ? Promise.reject(new Error("Hub unavailable")) : base(path, init)); return calls;
  }
  it("names the empty Recovery pane and its current status", async () => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab("Recovery");
    await waitFor(() => expect(screen.getByRole("tabpanel")).toHaveTextContent("No repair needed"));
    expect(screen.getByTestId("meeting-status")).toHaveTextContent("Ready");
  });
  it("replaces failed decision feedback with the current task edit failure and clears it on change", async () => {
    rejectedWrites(); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab("Decisions"); fireEvent.click(await screen.findByTestId("meeting-outcome-ft-" + proposal.find(row => row.kind === "decision")!.id));
    await action("Confirm"); await waitFor(() => expect(screen.getByTestId("meeting-status")).toHaveTextContent("Failed"));
    await readerTab("Tasks"); expect(screen.queryByTestId("meeting-status")?.textContent ?? "").not.toContain("Could not confirm");
    fireEvent.click(await screen.findByTestId("meeting-task-" + proposal.find(row => row.kind === "action")!.id)); await action("Edit");
    fireEvent.change(screen.getByRole("textbox", { name: "Owner" }), { target: { value: "Dana" } }); await action("Save");
    expect(await screen.findByRole("alert")).toHaveTextContent("Not saved · Hub unavailable");
    await waitFor(() => expect(screen.getByTestId("meeting-status")).toHaveTextContent("Failed"));
    expect(screen.getByTestId("meeting-status")).not.toHaveTextContent("Could not confirm");
    await action("Cancel"); expect(screen.queryByTestId("meeting-status")?.textContent ?? "").not.toContain("Not saved");
    await readerTab("Summary"); expect(screen.queryByTestId("meeting-status")?.textContent ?? "").not.toMatch(/Could not confirm|Not saved/);
  });
  it("keeps Records task edit failures in the status bar as well as the inspector", async () => {
    rejectedWrites(); render(<Shell><HistoryCore /></Shell>);
    fireEvent.click(await screen.findByTestId("meeting-row-reader"));
    const picker = screen.getByRole("button", { name: "Meeting contents" }); fireEvent.click(picker);
    fireEvent.click(screen.getByRole("menuitemradio", { name: "Tasks to confirm" }));
    fireEvent.click(await screen.findByTestId("meeting-task-" + proposal[0].id)); await action("Edit"); await action("Save");
    expect(await screen.findByRole("alert")).toHaveTextContent("Not saved · Hub unavailable");
    await waitFor(() => expect(screen.getByTestId("meetings-status")).toHaveTextContent("Failed"));
    expect(screen.getByTestId("meetings-status")).not.toHaveTextContent(/tasks to confirm|1 failed/);
  });
  it.each(["Decisions", "Commitments"])("%s shows only its applicable selection verbs", async label => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab(label);
    const toolbar = screen.getByRole("toolbar", { name: `${label} actions` });
    expect(within(toolbar).getAllByRole("button").map(button => button.textContent)).toEqual(["Open"]);
    const proposal = readerR3["/api/meetings/reader/outcome-review"].proposals.find(row => row.kind === (label === "Decisions" ? "decision" : "action"))!;
    fireEvent.click(await screen.findByTestId(`meeting-outcome-ft-${proposal.id}`));
    expect(within(toolbar).getByRole("button", { name: "Confirm" })).toBeEnabled();
    expect(within(toolbar).getByRole("button", { name: "Edit" })).toBeEnabled();
    expect(within(toolbar).getByRole("button", { name: "Dismiss" })).toBeEnabled();
    expect(within(toolbar).queryByRole("button", { name: "Done" })).toBeNull();
    expect(within(toolbar).queryByRole("button", { name: "Draft ready" })).toBeNull();
  });
  it.each(["Tasks", "Decisions", "Commitments", "Results"])("draws one verb row in %s before and after selection", async label => {
    if (label === "Results") at(prepared as Fixture); hub(label === "Results" ? prepared : readerR3); render(<MeetingRecord meetingId={label === "Results" ? "c5-review" : "reader"} onClose={() => undefined} />);
    await readerTab(label); const grid = await screen.findByRole("grid");
    expect(screen.getAllByRole("toolbar")).toHaveLength(2);
    expect(screen.getByRole("button", { name: label === "Tasks" ? "Confirm" : label === "Results" ? "Read" : "Open" })).toBeDisabled();
    const first = grid.querySelector<HTMLElement>('[data-object-id]'); if (first) fireEvent.click(first);
    expect(screen.getAllByRole("toolbar")).toHaveLength(2);
    expect(screen.getAllByRole("button", { name: "Actions ▾" })).toHaveLength(1);
  });
  it.each(["Proposals", "Context"])("uses the same toolbar for %s with selection verbs disabled until a pick", async label => {
    const fixture = label === "Proposals" ? hs170 : hs172, id = label === "Proposals" ? "m-saved-outcomes" : "m-ran";
    at(fixture as Fixture); hub(fixture, label === "Context" ? { "/api/meetings/m-ran?include_parked=true": { ...hs172["/api/meetings/m-ran?include_parked=true"], run_receipt: lookedAt.run_receipt } } : {});
    render(<MeetingRecord meetingId={id} onClose={() => undefined} />);
    await readerTab(label);
    const grid = await screen.findByRole("grid"), toolbar = screen.getByRole("toolbar", {name: label === "Context" ? "Meeting context actions" : "Proposals actions"});
    expect(screen.getAllByRole("toolbar")).toHaveLength(2);
    expect(within(toolbar).getByRole("button", { name: label === "Context" ? "Open" : "Decide" })).toBeDisabled();
    fireEvent.click(grid.querySelector<HTMLElement>('[data-object-id]')!);
    expect(screen.getAllByRole("toolbar")).toHaveLength(2);
    expect(within(toolbar).getByRole("button", { name: label === "Context" ? "Open" : "Decide" })).toBeEnabled();
    expect(screen.getAllByRole("button", { name: "Actions ▾" })).toHaveLength(1);
  });
  it("does not put a late task refusal on the next selected task", async () => {
    at(hs172 as Fixture); hub(hs172);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    let refuse!: (error: Error) => void;
    vi.mocked(apiFetch).mockImplementation((path, init) => init?.method === "POST" && path.endsWith("/confirm") ? new Promise((_, reject) => { refuse = reject; }) : base(path, init));
    render(<MeetingRecord meetingId="m-ran" onClose={() => undefined} />);
    await readerTab("Tasks");
    const grid = await screen.findByRole("grid", { name: "Tasks to confirm" });
    const rows = grid.querySelectorAll<HTMLElement>('[data-object-id]');
    fireEvent.click(rows[0]); await readerAction("Confirm"); fireEvent.click(rows[1]);
    await act(async () => refuse(new Error("Hub unavailable")));
    expect(rows[1]).toHaveAttribute("aria-selected", "true");
    expect(screen.queryByTestId("meeting-status")?.textContent ?? "").not.toContain("Not confirmed");
  });
  it("keeps summary retry available and uses the kit failure seat", async () => {
    hub(readerR2, { "/api/meetings/vendor?include_parked=true": readerR2["/api/meetings/vendor"] }); render(<MeetingRecord meetingId="vendor" onClose={() => undefined} />);
    const failure = await screen.findByTestId("meeting-summary-failure");
    expect(within(failure).getByRole("alert")).toHaveClass("surface-action-notice");
    expect(within(failure).getByRole("button", { name: "Try again" })).toBeEnabled();
  });

  it("keeps a failed task read out of the Summary status", async () => {
    hub(readerR3); const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path).includes("outcome-review") ? Promise.reject(new Error("Hub unavailable")) : base(path, init));
    render(<Shell><HistoryCore /></Shell>);
    fireEvent.click(await screen.findByTestId("meeting-row-reader"));
    fireEvent.click(screen.getByRole("button", { name: "Meeting contents" }));
    fireEvent.click(screen.getByRole("menuitemradio", { name: "Tasks to confirm" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Tasks not read");
    await waitFor(() => expect(screen.getByTestId("meetings-status")).toHaveTextContent("Failed"));
    fireEvent.click(screen.getByRole("button", { name: "Meeting contents" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Summary" }));
    await waitFor(() => expect(screen.getByTestId("meetings-status")).not.toHaveTextContent("Tasks not read"));
  });

});

describe("R4 meeting actions and edit failures", () => {
  it("keeps the meeting actions in one menu across a row selection and an edit", async () => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab("Tasks");
    for (const name of ["Summarise", "Send to…", "Delete"]) expect(screen.queryByRole("button", {name})).toBeNull();
    const task = readerR3["/api/meetings/reader/outcome-review"].proposals.find(row => row.kind === "action")!;
    fireEvent.click(await screen.findByTestId(`meeting-task-${task.id}`)); await readerAction("Edit");
    fireEvent.click(screen.getByRole("button", {name:"Actions ▾"}));
    for (const name of ["Summarise", "Send to…", "Delete"]) expect(screen.getByRole("menuitem", {name})).toBeTruthy();
    fireEvent.click(screen.getByRole("menuitem", {name:"Delete"}));
    expect(screen.getByRole("region", {name:/^Delete .+\?$/})).toBeVisible();
    expect(within(screen.getByRole("region", {name:/^Delete .+\?$/})).getByRole("button", {name:"Cancel"})).toHaveFocus();
    expect(screen.getByRole("textbox", {name:"Owner"})).toBeVisible();
  });
  it("puts a failed decision confirmation in the same form notice seat as a task save", async () => {
    hub(readerR3); const base=vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path,init)=>init?.method === "POST" && path.endsWith("/confirm") ? Promise.reject(new Error("Hub unavailable")) : base(path,init));
    render(<MeetingRecord meetingId="reader" onClose={() => undefined} />); await readerTab("Decisions");
    const decision=readerR3["/api/meetings/reader/outcome-review"].proposals.find(row=>row.kind === "decision")!;
    fireEvent.click(await screen.findByTestId(`meeting-outcome-ft-${decision.id}`)); await readerAction("Edit");
    fireEvent.change(screen.getByRole("textbox", {name:"Owner"}), {target:{value:"Dana"}});
    fireEvent.click(within(screen.getByRole("region", {name:"Edit decision"})).getByRole("button", {name:"Confirm"}));
    const error=await screen.findByRole("alert"); expect(error.closest(".surface-inspector-notice")).toBeTruthy();
    expect(error).toHaveTextContent("Hub unavailable"); expect(screen.getByRole("textbox", {name:"Owner"})).toHaveValue("Dana");
  });
});

describe("wave 11 meeting reader", () => {
  it("keeps the meeting name through summary failure and its other reading panes", async () => {
    const title=vi.fn(); hub(readerR2, {'/api/meetings/vendor?include_parked=true':readerR2['/api/meetings/vendor']});
    render(<TitleSlotContext.Provider value={title}><MeetingRecord meetingId="vendor" onClose={() => undefined} /></TitleSlotContext.Provider>);
    await screen.findByTestId('meeting-summary-failure');
    await waitFor(()=>expect(title).toHaveBeenLastCalledWith(readerR2['/api/meetings/vendor'].title));
    await readerTab('Transcript');
    expect(screen.getByRole('tabpanel').querySelector('.surface-well')).toBeNull();
    expect(screen.getByRole('tabpanel').querySelector('.surface-preference-well')).toBeTruthy();
    await waitFor(()=>expect(title).toHaveBeenLastCalledWith(readerR2['/api/meetings/vendor'].title));
  });

  it("keeps the known meeting name while its own read waits or fails", async () => {
    const title=vi.fn(); hub(readerR3); const base=vi.mocked(apiFetch).getMockImplementation()!;
    let refuse!: (reason:Error)=>void;
    vi.mocked(apiFetch).mockImplementation((path,init)=>path === '/api/meetings/reader?include_parked=true' ? new Promise((_,reject)=>{refuse=reject;}) : base(path,init));
    render(<TitleSlotContext.Provider value={title}><MeetingRecord meetingId="reader" name="Platform review" onClose={()=>undefined} /></TitleSlotContext.Provider>);
    expect(title).toHaveBeenLastCalledWith('Platform review');
    await act(async()=>refuse(new Error('Hub unavailable')));
    expect(await screen.findByRole('alert')).toHaveTextContent('Hub unavailable');
    expect(title).toHaveBeenLastCalledWith('Platform review');
  });
  it("returns from an object action to Summary on a desktop window", async () => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await screen.findByTestId('meeting-summary');
    await readerAction('Rename');
    expect(screen.getByRole('textbox', {name:'Name'})).toHaveValue('Platform review');
    fireEvent.click(screen.getByTestId('meeting-pane-back'));
    expect(await screen.findByTestId('meeting-summary')).toBeVisible();
    expect(screen.queryByRole('textbox', {name:'Name'})).toBeNull();
  });
  it("says the Recovery failure once and keeps a short failure state", async () => {
    hub(readerR3); const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => path.endsWith('/intel-recovery') ? Promise.reject(new Error('Hub unavailable')) : base(path, init));
    render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab('Recovery');
    expect(await screen.findByRole('alert')).toHaveTextContent('Recovery not read');
    expect(screen.getAllByText('Recovery not read', {exact:true})).toHaveLength(1);
    expect(screen.getByTestId('meeting-status')).toHaveTextContent('Failed');
  });
  it("offers Try again for a failed summary even before an engine is assigned", async () => {
    hub(readerR2, {'/api/meetings/vendor?include_parked=true':readerR2['/api/meetings/vendor']});
    render(<MeetingRecord meetingId="vendor" onClose={() => undefined} />);
    const pane = await screen.findByTestId('meeting-summary-failure');
    expect(within(pane).getByRole('button', {name:'Try again'})).toBeEnabled();
  });
  it("shows a failed summary retry in the selected meeting pane and retains Try again", async () => {
    hub(readerR2); const base=vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path,init)=>init?.method === "POST" && path.endsWith('/intelligence/run') ? Promise.reject(new Error('Hub unavailable')) : base(path,init));
    render(<MeetingPreview meeting={readerR2['/api/meetings/vendor']} view="summary" />);
    fireEvent.click(within(await screen.findByTestId('meeting-summary-failure')).getByRole('button', {name:'Try again'}));
    const failed=await screen.findByTestId('meeting-summary-retry-failure');
    expect(within(failed).getByRole('alert')).toHaveTextContent('Hub unavailable');
    expect(within(failed).getByRole('button', {name:'Try again'})).toBeEnabled();
    expect(screen.queryByText('The summary engine timed out.')).toBeNull();
  });
  it("keeps all task verbs with their list and only meeting verbs in Actions", async () => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab('Tasks');
    const toolbar = screen.getByRole('toolbar', {name:'Tasks to confirm actions'});
    for (const name of ['Confirm','Edit','Dismiss']) expect(within(toolbar).getByRole('button', {name})).toBeDisabled();
    const task = readerR3['/api/meetings/reader/outcome-review'].proposals.find(row=>row.kind==='action')!;
    fireEvent.click(await screen.findByTestId(`meeting-task-${task.id}`));
    expect(within(toolbar).getByRole('button', {name:'Dismiss'})).toBeEnabled();
    fireEvent.click(within(screen.getByTestId('meeting-toolbar')).getByRole('button', {name:'Actions ▾'}));
    const menu=screen.getByRole('menu', {name:'Meeting actions'});
    expect(within(menu).queryByRole('menuitem', {name:'Dismiss'})).toBeNull();
    expect(within(menu).getAllByRole('separator').length).toBeGreaterThan(0);
    expect(within(menu).getAllByRole('menuitem').at(-1)).toHaveTextContent('Delete');
  });
  it("names the decision field and the meeting to delete", async () => {
    hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
    await readerTab('Decisions');
    const decision=readerR3['/api/meetings/reader/outcome-review'].proposals.find(row=>row.kind==='decision')!;
    fireEvent.click(await screen.findByTestId(`meeting-outcome-ft-${decision.id}`)); await readerAction('Edit');
    expect(screen.getByRole('region', {name:'Edit decision'})).toBeVisible();
    expect(screen.getByRole('textbox', {name:'Decision'})).toHaveValue(decision.text);
    await readerAction('Delete');
    expect(screen.getByRole('region', {name:'Delete Platform review?'})).toBeVisible();
    expect(within(screen.getByRole('region', {name:'Delete Platform review?'})).getByRole('button', {name:'Cancel'})).toHaveFocus();
  });
  it.each([[p17t,'Speech is not set up','Setup needed'],[p17tReady,'Speech ready','Ready']])("puts audio readiness beside its verb and a short state in the bar", async (fixture, words, state) => {
    at(fixture as Fixture); hub(fixture as Fixture);
    render(<MeetingRecord meetingId="p17-audio-only" onClose={() => undefined} />);
    await readerTab('Audio');
    await waitFor(()=>expect(screen.getByRole('tabpanel')).toHaveTextContent(String(words)));
    expect(screen.getByRole('tabpanel').querySelector('.egress-chip')).toBeNull();
    expect(screen.getByRole('tabpanel')).not.toHaveTextContent('huggingface.co');
    await waitFor(()=>expect(screen.getByTestId('meeting-status')).toHaveTextContent(String(state)));
  });
  it("uses the read task count instead of a stale list count", async () => {
    hub(readerR3); const status=vi.fn();
    render(<MeetingPreview meeting={readerR3['/api/meetings/reader?include_parked=true']} view="tasks" onTaskStatus={status} />);
    await screen.findByTestId('meeting-task-'+readerR3['/api/meetings/reader/outcome-review'].proposals[0].id);
    expect(screen.queryByText('No tasks to confirm')).toBeNull();
    await waitFor(()=>expect(status).toHaveBeenLastCalledWith(expect.arrayContaining([expect.objectContaining({key:'tasks-count',text:'1 task to confirm'})])));
  });
});

it("Confirm all sends the held review bindings and retains the rows after refusal", async () => {
  const calls = hub(review11a.gets);
  const base = vi.mocked(apiFetch).getMockImplementation()!;
  vi.mocked(apiFetch).mockImplementation((path, init) => init?.method === "POST" && path === review11a.path
    ? (() => { calls.push({ path, init }); return Promise.reject(new ApiError(409, review11a.refusal.error, review11a.refusal)); })()
    : base(path, init));
  render(<Shell><MeetingRecord meetingId={review11a.meeting_id} onClose={() => undefined} /></Shell>);
  await readerTab("Decisions");
  await waitFor(() => expect(screen.getByRole("grid", { name: "Decisions" })).toHaveTextContent("Keep the reviewed plan"));
  const confirm = await readerAction("Confirm all", false);
  expect(confirm).toBeEnabled();
  fireEvent.click(confirm);
  await waitFor(() => expect(calls.find(call => call.path === review11a.path)?.init?.json).toEqual({ bindings: review11a.bindings }));
  await waitFor(() => expect(screen.getByTestId("meeting-status")).toHaveTextContent("Failed"));
  expect(screen.getByRole("grid", { name: "Decisions" })).toHaveTextContent("Keep the reviewed plan");
});

// Real admissions/completions from the first-use browser producer. The queue
// may replace its admitted leaf before execution; neither detail replay exposes queued.
it("shows a successor result without reload and keeps an older receipt from finishing the next press", async () => {
  at(successor as Fixture);
  const id = successor.initial.id;
  const path = `/api/meetings/${id}`;
  let shown: Record<string, unknown> = successor.initial;
  let presses = 0;
  let staleRead!: () => void;
  const stale = new Promise<void>(resolve => { staleRead = resolve; });
  hub({});
  const base = vi.mocked(apiFetch).getMockImplementation()!;
  vi.mocked(apiFetch).mockImplementation(async (url: string, init?: Call["init"]) => {
    if (url === `${path}/intelligence/run` && init?.method === "POST") {
      presses++;
      if (presses === 1) { shown = successor.first_completed; return successor.first_admitted as never; }
      return successor.second_admitted as never;
    }
    if (url === path || url === `${path}?include_parked=true`) {
      if (presses === 2) staleRead();
      return shown as never;
    }
    return base(url, init);
  });
  render(<Shell><MeetingRecord meetingId={id} onClose={() => undefined} /></Shell>);
  const run = await readerAction("Summarise", false);
  await waitFor(() => expect(run).not.toHaveAttribute("aria-disabled", "true"));
  fireEvent.click(run);
  expect(await screen.findByTestId("meeting-summary")).toHaveTextContent(successor.first_completed.intel.summary);
  expect(screen.getByTestId("meeting-status")).not.toHaveTextContent("Summary running");
  // The next press starts from that old receipt. A stale final read
  // must keep the new press running, even when its result text is identical.
  await act(async () => { await readerAction("Summarise"); await stale; });
  expect(screen.queryByTestId("meeting-summary")).toBeNull();
  expect(screen.getByRole("log", {name:"Summary work"})).toBeInTheDocument();
  shown = successor.second_completed;
  act(() => emit("aftercare_ready"));
  expect(await screen.findByTestId("meeting-summary")).toHaveTextContent(successor.second_completed.intel.summary);
  await waitFor(() => expect(screen.getByTestId("meeting-status")).not.toHaveTextContent("Summary running"));
  expect(presses).toBe(2);
});


it("blank task facts yield their columns to the task name", async () => {
  hub(readerR3); render(<MeetingRecord meetingId="reader" onClose={() => undefined} />);
  await readerTab("Tasks");
  const grid = await screen.findByRole("grid", {name:"Tasks to confirm"});
  await within(grid).findByText("Write the migration plan");
  expect(within(grid).queryByRole("columnheader", {name:"Owner"})).toBeNull();
  expect(within(grid).queryByRole("columnheader", {name:"Due"})).toBeNull();
});

it("the collection names the aggregate items and the selected task count separately", async () => {
  function CountedWindow() {
    const [mast,setMast] = useState<MastDeclaration | null>(null);
    return <MastSlotContext.Provider value={setMast}><Mast framed kind="meeting" title="Meetings" figures={mast?.figures} /><Shell><HistoryCore /></Shell></MastSlotContext.Provider>;
  }
  hub(readerR3); render(<CountedWindow />);
  const row = await screen.findByTestId("meeting-row-reader");
  await waitFor(() => expect(screen.getByTestId("meetings-status")).toHaveTextContent("2 items to confirm"));
  expect(screen.getByText("items to confirm").nextElementSibling).toHaveTextContent("2");
  fireEvent.click(row);
  await waitFor(() => expect(screen.getByTestId("meetings-status")).toHaveTextContent("1 task to confirm"));
  expect(screen.getByText("items to confirm").nextElementSibling).toHaveTextContent("2");
});

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
import { apiFetch } from "../../lib/api";
import { forgetExecutedReceipts } from "../../meetings/summaryRoute";
import { HistoryCore } from "../../pages/cores/HistoryCore";
import { MeetingRecord } from "../../pages/cores/history/MeetingRecord";
import { WingSlotContext } from "../surface/wings";
import { openPrimitive, openSurfaceOr } from "../shell";
import { SurfaceWindowHost, type SurfaceRow } from "../components/SurfaceWindows";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import hs170 from "./fixtures/meetings-hub/hs170.json";
import guidePreview from "../walk/__fixtures__/meetings.preview.json";
import hs172 from "./fixtures/meetings-hub/hs172.json";
import p17t from "./fixtures/meetings-hub/p17t.json";
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
function hub(fixture: Fixture, overrides: Record<string, unknown> = {}): Call[] {
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
    expect(screen.getByText("Select a meeting to read its summary.")).toBeTruthy();
    // The meeting with no words says so.
    const vendor = screen.getByTestId("meeting-row-m-no-transcript");
    expect(within(vendor).getByTestId("no-transcript-token").textContent).toBe("No transcript");
    // The dead capture says INTERRUPTED; no row says REC.
    expect(within(screen.getByTestId("meeting-row-m-dead-rec")).getByTestId("state-token").textContent).toBe("Interrupted");
    expect(stateTokens()).not.toContain("Rec");
    expect(document.body.textContent).not.toContain("0 SEG");
    expect(screen.getByRole("textbox", { name: "Find a meeting" })).toBeTruthy();
    expect(within(toolbar).getByRole("button", { name: "Open" })).toBeDisabled();
    expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (S-3: host chip + the run POST) */
  it("the picked meeting keeps same-device work quiet; its plate's Run summary POSTs the disclosed route", async () => {
    at(hs170 as Fixture);
    const calls = hub(hs170 as Fixture);
    render(<Shell><HistoryCore scope="meeting:m-off-words" /></Shell>);
    const plate = await screen.findByTestId("meeting-plate");
    await waitFor(() => expect(plate.getAttribute("data-kind")).toBe("run"));
    // Owner ruling 2026-10-25: no route chip beside the verb at all.
    const chip = () => document.querySelector(".gadget-chip-egress");
    expect(chip()).toBeNull();
    expect(document.body.textContent).not.toContain("same_device");
    fireEvent.click(await within(plate).findByTestId("detail-run-intelligence-btn"));
    const listed = (hs170 as Fixture)["/api/meetings?limit=100"] as { meetings: Array<{ id: string; planned_route: { selection_hash: string } }> };
    const hash = listed.meetings.find((m) => m.id === "m-off-words")!.planned_route.selection_hash;
    await waitFor(() =>
      expect(calls.filter((c) => c.init?.method === "POST")).toContainEqual({
        path: "/api/meetings/m-off-words/intelligence/run",
        init: { method: "POST", json: { expected_selection_hash: hash } },
      }),
    );
    // The hub's answer admits the SAME route the record disclosed.
    const answer = (hs170 as Fixture)["POST /api/meetings/m-off-words/intelligence/run"] as { planned_route: { selection_hash: string; status: string } };
    expect(answer.planned_route).toMatchObject({ status: "ready", selection_hash: hash });
    await waitFor(() => expect(chip()).toBeNull());
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
    const back = await screen.findByTestId("meeting-record-back");
    expect(screen.getByTestId("meeting-record-back").closest(".desk-surface-window")?.querySelector("[data-testid=meeting-mast]")).toBeTruthy();

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
  it("one review fact, the rail at Summary, three rows with Decide and Dismiss, the proposal text, speaker tokens", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} /></Shell>);
    // Window grammar (2026-10-24): no headline; the status bar says what is
    // left to review, once, in warm words.
    await waitFor(() => expect(screen.getByTestId("meeting-review-count").textContent).toBe("3 to review"));
    // The language: the mast names the meeting once; the plate is the review
    // (its one verb), the spine's last mark waits on him.
    expect(screen.getByTestId("meeting-mast")).toBeTruthy();
    expect(screen.getByTestId("meeting-plate").getAttribute("data-kind")).toBe("review");
    expect(screen.getByTestId("meeting-plate")).toHaveTextContent("3 to review");
    expect(screen.getByTestId("meeting-spine").getAttribute("aria-label")).toContain("3 to file");
    // The ledger by weight: the meeting's three asks lead it, each a row
    // with its verbs; no caption counts them again.
    const rows = await screen.findAllByTestId("meeting-needs-row");
    expect(rows).toHaveLength(3);
    expect(screen.getByTestId("meeting-plate")).toContainElement(rows[0]);
    const verbs = (label: string) =>
      rows.flatMap((row) => [...row.querySelectorAll(".btn")]).filter((b) => (b.textContent ?? "").includes(label));
    expect(verbs("Decide")).toHaveLength(3);
    expect(verbs("Dismiss")).toHaveLength(3);
    expect(document.body.textContent).toContain("Decide: the PostgreSQL migration date");
    fireEvent.click(screen.getByTestId("meeting-read-transcript"));
    expect(screen.getAllByTestId("transcript-speaker").length).toBeGreaterThanOrEqual(2);
    expect(rawButtons()).toEqual([]);
  });
});

describe("the meeting after a run (HS-172 seed)", () => {
  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingAfterRun::test_meeting_ran_with_proposals (the list half, both widths) */
  it("the list names tasks to confirm without zero counters or host labels", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-ran");
    const token = within(row).getByTestId("state-token").textContent ?? "";
    expect(token).toBe("Tasks to confirm");
    const body = document.body.textContent ?? "";
    expect(body).not.toContain("0 NEEDS");
    expect(body).not.toContain("LOCAL");
    expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingAfterRun::test_meeting_ran_with_proposals[1440] (the detail) */
  it("SUMMARISED, 41 S and the host; Decisions · 1 and Commitments · 2; three Confirm and three Dismiss with owner facts", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    const ledger = await screen.findByTestId("meeting-ledger");
    await waitFor(() => expect(screen.getAllByTestId("meeting-decisions-row")).toHaveLength(1));
    // Window grammar: the status bar says the summary's state. No host on the
    // record (owner ruling 2026-10-25).
    expect(screen.getByTestId("meeting-summary-state").textContent).toBe("Summary stored");
    expect(document.body.textContent).not.toContain("192.168.1.43");
    expect(document.querySelector(".gadget-chip-egress")).toBeNull();
    expect(screen.getAllByTestId("meeting-commitments-row")).toHaveLength(2);
    expect(screen.getAllByTestId("proposal-confirm-btn")).toHaveLength(3);
    expect(screen.getAllByTestId("proposal-more-btn")).toHaveLength(3);
    fireEvent.click(screen.getAllByTestId("proposal-more-btn")[0]);
    expect(screen.getByRole("menuitem", { name: "Dismiss" })).toBeTruthy();
    const ledgers = screen.getByTestId("meeting-plate").textContent ?? "";
    expect(ledger.querySelector("[data-testid=proposal-confirm-btn]")).toBeNull();
    expect(ledgers).toContain("Marek owns the PostgreSQL migration");
    expect(ledgers).toContain("no owner · by Fri");
    expect(ledgers).not.toMatch(/TO (DECIDE|CONFIRM)/);
    expect(rawButtons()).toEqual([]);
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
    expect(await screen.findByTestId("detail-skip-btn")).toBeTruthy();
  });
});

describe("the summary face (HS-201-04 seed shapes)", () => {
  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again (station 1-2 on the record) */
  it("the record draws no route chip and the click sends the hash the route carried", async () => {
    at(hs170 as Fixture);
    const calls = hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-off-words" onClose={() => undefined} /></Shell>);
    await screen.findByTestId("detail-run-intelligence-btn");
    expect(screen.queryByTestId("detail-route")).toBeNull();
    expect(document.body.textContent).not.toContain("THIS DEVICE");
    const detail = (hs170 as Fixture)["/api/meetings/m-off-words?include_parked=true"] as { planned_route: { selection_hash: string } };
    fireEvent.click(screen.getByTestId("detail-run-intelligence-btn"));
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
    await screen.findByTestId("meeting-mast");
    const plate = await screen.findByTestId("meeting-plate");
    const verb = await within(plate).findByTestId("detail-run-intelligence-btn");
    expect(document.querySelector(".kit-statusbar .gadget-chip-egress")).toBeNull();
    expect(screen.getByTestId("meeting-status").textContent).not.toContain("192.168.1.43");
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
    await waitFor(() => expect(document.querySelector("[data-testid=meeting-mast]")).toBeTruthy());
    expect(document.body.textContent).not.toContain("we ship the speech fix on friday");
    fireEvent.click(screen.getByTestId("meeting-read-transcript"));
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
    await waitFor(() => expect(screen.getByTestId("meeting-mast").textContent).toContain("speech not set up"));
    expect(screen.getByTestId("meeting-plate").getAttribute("data-kind")).toBe("transcribe");
    const setup = await screen.findByTestId("meeting-transcribe-speech-setup-verb");
    expect(setup.textContent?.trim()).toMatch(/^Set up speech · \d+ MB$/);
    expect(screen.queryByRole("button", { name: "Transcribe" })).toBeNull();
  });

  /* replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (step 2, the row at 1440) */
  it("speech ready: the picked audio-only meeting's plate is Transcribe", async () => {
    at(p17tReady as Fixture);
    hub(p17tReady as Fixture);
    render(<Shell><HistoryCore scope="meeting:p17-audio-only" /></Shell>);
    await screen.findByTestId("meeting-mast");
    const plate = await screen.findByTestId("meeting-plate");
    const verb = await within(plate).findByTestId("meeting-transcribe-verb");
    expect(plate.getAttribute("data-kind")).toBe("transcribe");
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
    const verb = await screen.findByTestId("meeting-transcribe-verb");
    expect(verb.textContent?.trim()).toBe("Transcribe");
    fireEvent.click(verb);
    fireEvent.click(screen.getByTestId("meeting-read-transcript"));
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
  it("a folded Looked at · 2 under the transcript; each source a link with its date", async () => {
    at(hs172 as Fixture);
    const detailPath = "/api/meetings/m-ran?include_parked=true";
    const detail = (hs172 as Fixture)[detailPath] as Record<string, unknown>;
    hub(hs172 as Fixture, { [detailPath]: { ...detail, run_receipt: lookedAt.run_receipt } });
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    fireEvent.click(await screen.findByRole("button", { name: "Read context" }));
    const fold = await screen.findByRole("button", { name: /Looked at · 2/ });
    expect(screen.queryByTestId("meeting-looked-at")).toBeNull();
    fireEvent.click(fold);
    const list = await screen.findByTestId("meeting-looked-at");
    const rows = [...list.querySelectorAll("li")].map((li) => li.textContent ?? "");
    expect(rows[0]).toContain("Thursday sync");
    expect(rows[0]).toContain("Thu 15 Oct");
    expect(rows[1]).toContain("Wednesday planning");
    expect(rows[1]).toContain("Wed 14 Oct");
    expect(list.textContent).not.toContain("Friday");
    fireEvent.click(within(list).getByRole("button", { name: "Thursday sync" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", "meeting:c2-thu");
    expect(rawButtons()).toEqual([]);
  });

  it("no memory read: no fold, no zero counter", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await screen.findByTestId("meeting-ledger");
    expect(screen.queryByRole("button", { name: /Looked at/ })).toBeNull();
  });
});

describe("Since last time (betterment/capture C6)", () => {
  /* Friday's aftercare as the hub served it
   * (fixtures/meetings-hub/since-last.json, recorded by
   * tests/integration/test_desk_meetings.py), on the HS-172 record. */
  const since = sinceLast.aftercare.since_last_meeting;
  it("one folded line under the summary names the sync and its day; unfolded, closed, still open and new, each a link", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture, { "/api/meetings/m-ran/aftercare": sinceLast.aftercare });
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    fireEvent.click(await screen.findByRole("button", { name: "Read context" }));
    const fold = await screen.findByRole("button", { name: "Since Payments platform sync, Thu 15 Oct: 1 closed · 2 still open · 2 new" });
    expect(screen.queryByTestId("meeting-ledger")).toBeNull();
    expect(screen.queryByTestId("meeting-since")).toBeNull();
    fireEvent.click(fold);
    const body = await screen.findByTestId("meeting-since");
    expect(within(screen.getByTestId("meeting-since-closed")).getByText(since.closed_actions[0].task)).toBeTruthy();
    const open = screen.getByTestId("meeting-since-open");
    expect(open.textContent).toContain("Profile the reconciliation job");
    expect(open.textContent).toContain("Draft the rollback runbook for the cutover");
    expect(screen.getByTestId("meeting-since-new").textContent).toContain("Write the ADR for idempotent retries");
    fireEvent.click(within(open).getByRole("button", { name: "Profile the reconciliation job" }));
    expect(openSurfaceOr).toHaveBeenCalledWith("review-meetings", "/history", `meeting:${since.previous_meeting.id}`);
    expect(body.textContent).not.toMatch(/\b0 /);
    expect(rawButtons()).toEqual([]);
  });

  it("no previous meeting of the same kind: no line", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture, { "/api/meetings/m-ran/aftercare": { ...sinceLast.aftercare, since_last_meeting: null } });
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    await screen.findByTestId("meeting-ledger");
    expect(screen.queryByRole("button", { name: /^Since / })).toBeNull();
  });
});

describe("the meeting prepares its Results (betterment/capture C5, C5b)", () => {
  /* The architecture review as a real hub served it after the LAN engine
   * wrote its summary and its drafts (fixtures/meetings-hub/prepared.json,
   * recorded by tests/integration/test_meeting_plugins_engines.py). */
  const fixture = prepared as unknown as Fixture;
  const PREPARED = "/api/meetings/c5-review/prepared";
  const render5 = () => render(<Shell><MeetingRecord meetingId="c5-review" onClose={() => undefined} /></Shell>);

  it("the Results are ledger rows after the actions: one line each, title and kind, Send first; the title reads the draft", async () => {
    at(fixture);
    hub(fixture);
    render5();
    await screen.findByTestId("meeting-prepared-adr", undefined, { timeout: 8000 });
    const section = screen.getByTestId("meeting-ledger");
    const commitments = screen.getAllByTestId("meeting-commitments-row");
    const last = commitments[commitments.length - 1];
    expect(last.compareDocumentPosition(screen.getByTestId("meeting-prepared-adr")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    const adr = within(section).getByTestId("meeting-prepared-adr");
    expect(adr.textContent).toContain("ADR: ");
    expect(adr.textContent).toContain("ADR draft");
    const verbs = within(adr).getAllByRole("button").map((b) => (b.textContent ?? "").trim());
    expect(verbs).toEqual(["Send…", "Open as note", "Copy"]);
    expect(within(section).getByTestId("meeting-prepared-followup").textContent).toContain("Follow-up");
    expect(within(section).getByTestId("meeting-prepared-stakeholder_update").textContent).toContain("Update for stakeholders");
    expect(section.textContent).not.toMatch(/Drafter|ART 0|artifact/i);
    expect(screen.queryByTestId("meeting-prepared-draft")).toBeNull();
    expect(adr.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(adr);
    const draft = await screen.findByTestId("meeting-prepared-draft");
    expect(draft.textContent).toMatch(/idempoten/i);
    expect(draft.textContent).not.toContain("###");
    expect(draft.textContent).not.toContain("Source windows");
    expect(rawButtons()).toEqual([]);
  });

  it("an action whose words ask for the ADR says Draft ready, and its press opens the ADR draft", async () => {
    at(fixture);
    hub(fixture);
    render5();
    await screen.findByTestId("meeting-prepared-adr", undefined, { timeout: 8000 });
    const ready = screen.getAllByRole("button", { name: /^Draft ready: ADR: / });
    expect(ready.length).toBeGreaterThan(0);
    expect(ready[0].closest("[data-testid=meeting-commitments-row]")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: /^Draft ready: Update for stakeholders/ }).length).toBeGreaterThan(0);
    fireEvent.click(ready[0]);
    const draft = await screen.findByTestId("meeting-prepared-draft");
    expect(draft.closest("li")?.querySelector("[data-testid='meeting-prepared-adr']")).toBeTruthy();
  });

  it("Open as note makes a note of the draft; Send… opens the Send well under the line; nothing is sent", async () => {
    at(fixture);
    const calls = hub(fixture);
    render5();
    const adr = await screen.findByTestId("meeting-prepared-adr");
    fireEvent.click(within(adr).getByRole("button", { name: "Open as note" }));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/notes" && c.init?.method === "POST")).toBe(true));
    const note = calls.find((c) => c.path === "/api/notes")!.init!.json as { title: string; body_markdown: string };
    expect(note.title).toMatch(/^ADR: /);
    expect(note.body_markdown).toMatch(/idempoten/i);
    expect(note.body_markdown).not.toContain("###");
    fireEvent.click(within(adr).getByRole("button", { name: "Send…" }));
    const well = await screen.findByTestId("meeting-prepared-send");
    expect(well.closest("li")?.querySelector("[data-testid='meeting-prepared-adr']")).toBeTruthy();
    expect(within(adr).getByRole("button", { name: "Hide" })).toBeTruthy();
    const posts = calls.filter((c) => c.init?.method === "POST").map((c) => c.path);
    expect(posts.filter((p) => /send|channel|deliver/i.test(p))).toEqual([]);
  });

  it("while a draft is written it says Writing… in place", async () => {
    at(fixture);
    hub(fixture, { [PREPARED]: fixture[`${PREPARED}#writing`] });
    render5();
    const adr = await screen.findByTestId("meeting-prepared-adr");
    expect(within(adr).getByTestId("meeting-prepared-writing").textContent).toMatch(/^Writing… · \d+ s$/);
    expect(within(adr).queryByRole("button", { name: "Open as note" })).toBeNull();
  });

  it("a failed draft says why, and Write again asks the hub for that one draft on the route he was shown", async () => {
    at(fixture);
    const calls = hub(fixture, { [PREPARED]: preparedFailed.prepared });
    render5();
    const adr = await screen.findByTestId("meeting-prepared-adr");
    const row = adr.closest("li") as HTMLElement;
    expect(within(row).getByTestId("meeting-prepared-failed").textContent).toBe("The engine did not finish this draft.");
    fireEvent.click(within(adr).getByRole("button", { name: "Write again" }));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/meetings/c5-review/prepare")).toBe(true));
    const body = calls.find((c) => c.path === "/api/meetings/c5-review/prepare")!.init!.json as Record<string, unknown>;
    expect(body.plugin_id).toBe("adr_drafter");
    const detail = fixture["/api/meetings/c5-review?include_parked=true"] as { planned_route?: { selection_hash?: string } };
    expect(body.expected_selection_hash).toBe(detail.planned_route?.selection_hash);
  });

  it("Prepare… lists the kinds not prepared yet and writes the one he picks", async () => {
    at(fixture);
    const calls = hub(fixture);
    render5();
    // The record draws its body once its first reads end (MEETING_READS_CAP_MS);
    // under a loaded full run that is past findByRole's 1 s default.
    const prepareButton = await screen.findByRole("button", { name: "Prepare…" }, { timeout: 8000 });
    fireEvent.click(prepareButton);
    const menu = await screen.findByRole("menu");
    const labels = within(menu).getAllByRole("menuitem").map((m) => (m.textContent ?? "").trim());
    expect(labels).toContain("Risks");
    expect(labels).not.toContain("ADR draft");
    fireEvent.click(within(menu).getByRole("menuitem", { name: "Risks" }));
    await waitFor(() => expect(calls.some((c) => c.path === "/api/meetings/c5-review/prepare")).toBe(true));
    expect((calls.find((c) => c.path === "/api/meetings/c5-review/prepare")!.init!.json as Record<string, unknown>).plugin_id)
      .toBe("risk_heatmap");
  });

  it("the meeting window has one wing, Outcomes; no Artifacts wing", async () => {
    at(fixture);
    hub(fixture);
    render5();
    await screen.findByTestId("meeting-prepared", undefined, { timeout: 8000 });
    expect(screen.queryByRole("tab", { name: /Artifacts/i })).toBeNull();
    expect(screen.queryByRole("button", { name: /^Artifacts$/i })).toBeNull();
  });
});

describe("One home for recording: Meetings ▸ Record (betterment/capture C7)", () => {
  // The hub's own answers at its real clock
  // (tests/unit/test_desk_chair.py::test_coming_up_arms_cancels_and_names_a_failed_fire):
  // a fire that raised, three calendar meetings ahead, the arm and the cancel.
  type Phase = "before" | "armed" | "cancelled";
  const pad2 = (n: number) => String(n).padStart(2, "0");
  const hhmm = (iso: string) => { const d = new Date(iso); return `${pad2(d.getHours())}:${pad2(d.getMinutes())}`; };
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
    expect(within(rowOf(list, "Architecture review")).getByTestId("coming-up-slot").textContent).toMatch(/^[A-Z][a-z]{2} \d\d:\d\d$/);
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
    hub(guidePreview as Fixture);
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

  it("opens each long read in the pane and Back returns to the ledger", async () => {
    at(prepared as Fixture);
    hub(prepared as Fixture);
    render(<Shell><MeetingRecord meetingId="c5-review" onClose={() => undefined} /></Shell>);
    const ledger = await screen.findByTestId("meeting-ledger");
    expect(within(ledger).queryByTestId("meeting-summary-text")).toBeNull();
    expect(screen.queryByTestId("transcript-speaker")).toBeNull();
    fireEvent.click(await within(ledger).findByRole("button", { name: "Read summary" }));
    const reader = await screen.findByTestId("meeting-reader");
    const wire = prepared["/api/meetings/c5-review?include_parked=true"];
    expect(within(reader).getByTestId("meeting-summary-text").textContent).toBe(wire.intel.summary);
    expect(screen.queryByTestId("meeting-ledger")).toBeNull();
    fireEvent.click(within(reader).getByRole("button", { name: "Back" }));
    fireEvent.click(screen.getByRole("button", { name: "Read transcript" }));
    expect(await screen.findAllByTestId("transcript-speaker")).not.toHaveLength(0);
    expect(screen.queryByTestId("meeting-summary-text")).toBeNull();
    fireEvent.click(screen.getByTestId("meeting-reader-back"));
    expect(await screen.findByTestId("meeting-ledger")).toBeTruthy();
  });

  it("a refused Confirm keeps the proposal and its edit in the one review plate", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    const base = vi.mocked(apiFetch).getMockImplementation()!;
    vi.mocked(apiFetch).mockImplementation((path, init) => String(path).endsWith("/confirm")
      ? Promise.reject(new Error("Hub unavailable")) : base(path, init));
    render(<Shell><MeetingRecord meetingId="m-ran" onClose={() => undefined} /></Shell>);
    const plate = await screen.findByTestId("meeting-plate");
    const confirm = (await within(plate).findAllByTestId("proposal-confirm-btn"))[0];
    const row = confirm.closest("li")!;
    fireEvent.click(within(row).getByTestId("proposal-more-btn"));
    fireEvent.click(screen.getByRole("menuitem", { name: "Edit" }));
    const task = within(row).getByRole("textbox", { name: "Task" });
    fireEvent.change(task, { target: { value: "Keep this edit" } });
    fireEvent.click(screen.getByTestId("meeting-read-transcript"));
    fireEvent.click(await screen.findByTestId("meeting-reader-back"));
    expect(within(row).getByRole("textbox", { name: "Task" })).toHaveValue("Keep this edit");
    fireEvent.click(confirm);
    expect(await screen.findByText("Could not confirm the proposal · Nothing changed · Try again")).toBeTruthy();
    expect(plate).toHaveTextContent("Keep this edit");
    expect(within(plate).getByRole("button", { name: "Confirm: Keep this edit" })).toBeTruthy();
    expect(screen.getByTestId("meeting-ledger").textContent).not.toContain("Keep this edit");
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
    fireEvent.click(screen.getByRole("tab", { name: "Tasks to confirm" }));
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

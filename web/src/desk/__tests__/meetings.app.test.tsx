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
import hs172 from "./fixtures/meetings-hub/hs172.json";
import p17t from "./fixtures/meetings-hub/p17t.json";
import p17tReady from "./fixtures/meetings-hub/p17t-ready.json";

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
  it("headline, ONE Run summary on the meeting with words, NO TRANSCRIPT, INTERRUPTED, no REC, no 0 SEG, no raw button", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const headline = await screen.findByTestId("meetings-headline");
    await waitFor(() => expect(headline.textContent).not.toBe(""));
    // The rig read `1 ... summary`; the seed's queued meeting wins the headline.
    expect(headline.textContent).toBe("1 summary queued");
    await screen.findByTestId("meeting-row-m-off-words");
    const run = screen.getAllByTestId("run-intelligence-btn");
    expect(run).toHaveLength(1);
    expect(within(screen.getByTestId("meeting-row-m-off-words")).getByTestId("run-intelligence-btn")).toBe(run[0]);
    // The meeting with no words says so and offers no run.
    const vendor = screen.getByTestId("meeting-row-m-no-transcript");
    expect(within(vendor).getByTestId("no-transcript-token").textContent).toBe("NO TRANSCRIPT");
    expect(within(vendor).queryByTestId("run-intelligence-btn")).toBeNull();
    // The dead capture says INTERRUPTED; no row says REC.
    expect(within(screen.getByTestId("meeting-row-m-dead-rec")).getByTestId("state-token").textContent).toBe("Interrupted");
    expect(stateTokens()).not.toContain("Rec");
    expect(document.body.textContent).not.toContain("0 SEG");
    // HS-170-04 restored doors: search with its mic, and the facet row
    // (the seed's one open action draws HAS OPEN ACTIONS).
    expect(document.querySelector(".meetings-search .gadget-string input")).toBeTruthy();
    expect(screen.getByTestId("meetings-facets").textContent).toContain("HAS OPEN ACTIONS");
    expect(rawButtons()).toEqual([]);
  });

  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (S-3: host chip + the run POST) */
  it("the row keeps same-device work quiet; Run summary POSTs the disclosed route", async () => {
    at(hs170 as Fixture);
    const calls = hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-off-words");
    const chip = () => within(row).getByTestId("row-route").querySelector(".gadget-chip-egress");
    // Same-device work has no egress to disclose. The route remains bound to
    // the run and never leaks its wire enum.
    expect(chip()).toBeNull();
    expect(row.textContent).not.toContain("same_device");
    fireEvent.click(within(row).getByTestId("run-intelligence-btn"));
    const listed = (hs170 as Fixture)["/api/meetings?limit=100"] as { meetings: Array<{ id: string; planned_route: { selection_hash: string } }> };
    const hash = listed.meetings.find((m) => m.id === "m-off-words")!.planned_route.selection_hash;
    await waitFor(() =>
      expect(calls.filter((c) => c.init?.method === "POST")).toContainEqual({
        path: "/api/meetings/m-off-words/intelligence/run",
        init: { method: "POST", json: { expected_selection_hash: hash } },
      }),
    );
    // The hub's answer admits the SAME route the row disclosed (the real
    // path, not the missing-route fallback of summaryRoute.ts).
    const answer = (hs170 as Fixture)["POST /api/meetings/m-off-words/intelligence/run"] as { planned_route: { selection_hash: string; status: string } };
    expect(answer.planned_route).toMatchObject({ status: "ready", selection_hash: hash });
    // The row remains quiet through the run.
    await waitFor(() => expect(chip()).toBeNull());
  });

  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (row → the meeting's own window) */
  it("a row opens the meeting's own window", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-saved-outcomes");
    fireEvent.click(row.querySelector(".meetings-stream-row-body")!);
    // `openSourceRef` hands the shell the meeting scope. The one Meetings
    // surface owns the record and its Back control returns to this list.
    expect(openSurfaceOr).toHaveBeenCalledWith(
      "review-meetings", "/history", "meeting:m-saved-outcomes",
    );
  });
});

describe("the hosted meeting record returns to its list", () => {
  it("desktop Back clears the real host scope and keeps the selected list row", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<HostedMeetings />);
    const back = await screen.findByTestId("meeting-record-back");
    expect(back).toBeVisible();
    expect(screen.getByTestId("meeting-record-back").closest(".desk-surface-window")?.querySelector(".meetings-detail-head")).toBeTruthy();

    fireEvent.click(back);

    await waitFor(() => {
      expect(screen.queryByTestId("meeting-record-back")).toBeNull();
      expect(screen.getByTestId("meetings-headline")).toBeTruthy();
    });
    expect(screen.getByTestId("meeting-row-m-saved-outcomes")).toHaveAttribute("data-selected", "true");
  });
});

describe("the meeting window over the HS-170 seed", () => {
  /* replaces: tests/e2e/test_hs170_meetings_glass.py::TestMeetingsGlass::test_meetings_face (the detail half) */
  it("one display, TO REVIEW 3, three rows with Decide and Dismiss, the proposal text, speaker tokens", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-saved-outcomes" onClose={() => undefined} /></Shell>);
    await waitFor(() => expect(document.querySelector(".meetings-detail-head .surface-display")?.textContent).toBe("Design review"));
    const head = await screen.findByText("TO REVIEW 3");
    expect(head.closest(".meetings-detail-needs-head")).toBeTruthy();
    const rows = document.querySelectorAll(".meetings-detail-outcome-row");
    expect(rows).toHaveLength(3);
    const verbs = (label: string) =>
      [...document.querySelectorAll(".meetings-detail-outcome-verb .btn")].filter((b) => (b.textContent ?? "").includes(label));
    expect(verbs("Decide")).toHaveLength(3);
    expect(verbs("Dismiss")).toHaveLength(3);
    expect(document.body.textContent).toContain("Decide: the PostgreSQL migration date");
    expect(screen.getAllByTestId("transcript-speaker").length).toBeGreaterThanOrEqual(2);
    expect(rawButtons()).toEqual([]);
  });
});

describe("the meeting after a run (HS-172 seed)", () => {
  /* replaces: tests/e2e/test_hs172_meeting_glass.py::TestMeetingAfterRun::test_meeting_ran_with_proposals (the list half, both widths) */
  it("the list row says RAN or TO REVIEW; no zero counter, no LOCAL, no raw button", async () => {
    at(hs172 as Fixture);
    hub(hs172 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const row = await screen.findByTestId("meeting-row-m-ran");
    const token = within(row).getByTestId("state-token").textContent ?? "";
    expect(token.includes("Ran") || token.includes("to review")).toBe(true);
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
    const decisions = await screen.findByTestId("meeting-decisions");
    const facts = document.querySelector(".meetings-detail-facts")?.textContent ?? "";
    expect(facts).toContain("SUMMARISED");
    expect(facts).toContain("41 S");
    expect(facts).toContain("192.168.1.43");
    const commitments = screen.getByTestId("meeting-commitments");
    expect(decisions.querySelector("h3")?.textContent).toBe("Decided · 1");
    expect(commitments.querySelector("h3")?.textContent).toBe("Who owes what · 2");
    expect(screen.getAllByTestId("proposal-confirm-btn")).toHaveLength(3);
    expect(screen.getAllByTestId("proposal-more-btn")).toHaveLength(3);
    screen.getAllByTestId("proposal-more-btn").forEach((button) => fireEvent.click(button));
    expect(screen.getAllByTestId("proposal-dismiss-btn")).toHaveLength(3);
    const ledgers = `${decisions.textContent}${commitments.textContent}`;
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
    list.unmount();
    render(<Shell><MeetingRecord meetingId="m-queued" onClose={() => undefined} /></Shell>);
    await waitFor(() => expect(document.querySelector(".meetings-detail-facts")?.textContent).toContain("QUEUED"));
    expect(document.body.textContent).not.toContain("REMAINING");
    expect(await screen.findByTestId("detail-skip-btn")).toBeTruthy();
  });
});

describe("the summary face (HS-201-04 seed shapes)", () => {
  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_the_summary_is_asked_for_disclosed_and_found_again (station 1-2 on the record) */
  it("the record discloses the host before the click and the click sends the disclosed hash", async () => {
    at(hs170 as Fixture);
    const calls = hub(hs170 as Fixture);
    render(<Shell><MeetingRecord meetingId="m-off-words" onClose={() => undefined} /></Shell>);
    const route = await screen.findByTestId("detail-route");
    expect(route.textContent).not.toContain("THIS DEVICE");
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
  it("the Meetings footer chip names the route's host, not a constant", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    const first = render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    const footerChip = () => (document.querySelector(".surface-footer .gadget-chip-egress")?.textContent ?? "").trim();
    await waitFor(() => expect(footerChip()).toBe(""));
    first.unmount();
    // The same rows with the route's lead leg on a LAN host (the shape is the
    // captured one; only the host value differs): the chip follows it.
    const listed = (hs170 as Fixture)["/api/meetings?limit=100"] as { meetings: Array<Record<string, unknown>> };
    const lan = {
      ...listed,
      meetings: listed.meetings.map((m) => {
        const route = m.planned_route as { legs: Array<Record<string, unknown>> };
        return { ...m, planned_route: { ...route, legs: [{ ...route.legs[0], host: "192.168.1.43", boundary: "lan" }] } };
      }),
    };
    hub(hs170 as Fixture, { "/api/meetings?limit=100": lan });
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    await waitFor(() => expect(footerChip()).toContain("192.168.1.43"));
    expect(footerChip()).toContain("192.168.1.43");
  });

  /* replaces: tests/e2e/test_hs201_summary_face_glass.py::test_import_transcribes_then_queues_the_disclosed_summary (station 1: the Import door) */
  it("the head's Import opens the drop well in the Meetings window", async () => {
    at(hs170 as Fixture);
    hub(hs170 as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    await screen.findByTestId("meeting-row-m-off-words");
    fireEvent.click(within(document.querySelector(".meetings-head-verbs") as HTMLElement).getByRole("button", { name: "Import" }));
    await waitFor(() => expect(document.querySelector(".surface-dropwell input[type=file]")).toBeTruthy());
    const input = document.querySelector(".surface-dropwell input[type=file]") as HTMLInputElement;
    fireEvent.change(input, { target: { files: [new File(["RIFF"], "core_path_smoke_16k.wav", { type: "audio/wav" })] } });
    expect(await screen.findByRole("textbox", { name: "Title" })).toBeTruthy();
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
    await waitFor(() => expect(document.querySelector(".meetings-detail-head")).toBeTruthy());
    expect(document.body.textContent).not.toContain("we ship the speech fix on friday");
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
    await screen.findByTestId("meeting-speech-missing");
    const setup = await screen.findByTestId("meeting-transcribe-speech-setup-verb");
    expect(setup.textContent?.trim()).toMatch(/^Set up speech · \d+ MB$/);
    expect(screen.queryByRole("button", { name: "Transcribe" })).toBeNull();
  });

  /* replaces: tests/e2e/test_philo17_transcribe_glass.py::test_an_audio_only_meeting_is_transcribed_in_place (step 2, the row at 1440) */
  it("speech ready: the list row offers Transcribe", async () => {
    at(p17tReady as Fixture);
    hub(p17tReady as Fixture);
    render(<Shell><HistoryCore /></Shell>);
    const verb = await screen.findByTestId("row-transcribe-verb");
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
    await waitFor(() => expect(document.body.textContent).toContain("we ship the speech fix on friday"));
    expect(calls).toContainEqual({ path: "/api/meetings/p17-audio-only/transcribe", init: { method: "POST" } });
    expect(screen.queryByTestId("meeting-transcribe-verb")).toBeNull();
    expect(screen.queryByTestId("meeting-speech-missing")).toBeNull();
  });
});

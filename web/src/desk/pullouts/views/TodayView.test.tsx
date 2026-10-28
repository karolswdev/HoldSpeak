import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { PERSON_OPEN_EVENT } from "../../objectWindows";
import { DAY_SAID_KEY, TodayView, countdown, currentStep, dayGreeting, dayLight, dayPart, toFinish } from "./TodayView";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return { ...actual, openSurfaceOr: shell.openSurfaceOr };
});

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
}

const inMinutes = (n: number) => new Date(Date.now() + n * 60_000).toISOString();

function hub(routes: Record<string, (init?: RequestInit) => Response>) {
  const calls: Array<[string, RequestInit | undefined]> = [];
  vi.stubGlobal("fetch", vi.fn(async (input: string, init?: RequestInit) => {
    const key = String(input);
    calls.push([key, init]);
    const handler = routes[key];
    return handler ? handler(init) : json({}, 404);
  }));
  return calls;
}

// The day is fixed at 09:00: "+120 min" is still today at any wall-clock
// hour (the suite failed after 22:00).
beforeEach(() => {
  // DELIGHT slice 3: the once-per-day flag lives in localStorage; each case
  // starts as a viewer who has not seen the day's line.
  window.localStorage.clear();
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 9, 12, 9, 0, 0));
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("PHILO-17 Today: the day as a timeline", () => {
  it("DELIGHT slice 2: knows the hour — the greeting and the day's light", () => {
    // 2026-10-27 is a Tuesday.
    const at = (h: number, m = 0) => new Date(2026, 9, 27, h, m, 0);
    expect(dayGreeting(at(7))).toBe("Tuesday morning");
    expect(dayGreeting(at(14))).toBe("Tuesday afternoon");
    expect(dayGreeting(at(19, 30))).toBe("Tuesday evening");
    expect(dayGreeting(at(23))).toBe("Tuesday night");
    expect(dayPart(at(4, 59))).toBe("night");
    expect(dayPart(at(5))).toBe("morning");
    expect(dayPart(at(12))).toBe("afternoon");
    expect(dayPart(at(18))).toBe("evening");
    expect(dayLight(at(7))).toBe("warm");
    expect(dayLight(at(14))).toBeUndefined();
    expect(dayLight(at(19))).toBe("cool");
    expect(dayLight(at(2))).toBe("cool");
  });

  it("DELIGHT slice 2: after the day's last meeting the status bar says That is the day", async () => {
    vi.setSystemTime(new Date(2026, 9, 12, 17, 30, 0));
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [{ id: "m1", title: "Payments weekly", started_at: inMinutes(-120),
        transcriptWords: 40, intel_status: "ready", has_summary: true }] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    window.localStorage.removeItem(DAY_SAID_KEY);
    const first = render(<TodayView />);
    expect((await screen.findByTestId("today-status-day")).textContent).toContain("That is the day");
    expect(screen.queryByTestId("today-status-ahead")).toBeNull();
    // DELIGHT slice 3: said once per day, per viewer. Today opened again the
    // same day shows the count; the next day says it again.
    expect(window.localStorage.getItem(DAY_SAID_KEY)).toBe("2026-10-12");
    first.unmount();
    const again = render(<TodayView />);
    await waitFor(() => expect(screen.getByTestId("today-body").getAttribute("aria-busy")).toBeNull());
    expect(screen.queryByTestId("today-status-day")).toBeNull();
    again.unmount();
    window.localStorage.setItem(DAY_SAID_KEY, "2026-10-11");
    render(<TodayView />);
    expect(await screen.findByTestId("today-status-day")).toBeTruthy();
    window.localStorage.removeItem(DAY_SAID_KEY);
  });

  it("DELIGHT slice 3: a day line already said today shows the counts instead", async () => {
    vi.setSystemTime(new Date(2026, 9, 12, 17, 30, 0));
    window.localStorage.setItem(DAY_SAID_KEY, "2026-10-12");
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [{ id: "m1", title: "Payments weekly", started_at: inMinutes(-120),
        transcriptWords: 40, intel_status: "ready", has_summary: true }] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    const said = render(<TodayView />);
    await waitFor(() => expect(screen.getByTestId("today-body").getAttribute("aria-busy")).toBeNull());
    expect(screen.queryByTestId("today-status-day")).toBeNull();
    // The same day without the flag says the line: the case above is not empty.
    said.unmount();
    window.localStorage.removeItem(DAY_SAID_KEY);
    render(<TodayView />);
    expect(await screen.findByTestId("today-status-day")).toBeTruthy();
  });

  it("DELIGHT slice 2: the day line greets by the hour and the paper takes the light", async () => {
    hub({ "/api/door": () => json({ calendar_configured: true, upcoming: [] }), "/api/desk/needs-you": () => json({ items: [] }) });
    const { container } = render(<TodayView />);
    // The suite's clock: Monday 12 Oct 2026, 09:00.
    expect(screen.getByTestId("today-greeting").textContent).toBe("Monday morning");
    expect(screen.getByTestId("today-day").textContent).toBe("Monday morning · 12 Oct");
    expect(container.querySelector(".today")?.getAttribute("data-light")).toBe("warm");
    await screen.findByTestId("today-toolbar");
  });

  it("counts down in minutes, then hours, then now", () => {
    const now = new Date("2026-10-12T09:00:00");
    expect(countdown(new Date("2026-10-12T10:08:00"), now)).toBe("in 1 h 08 min");
    expect(countdown(new Date("2026-10-12T09:20:00"), now)).toBe("in 20 min");
    expect(countdown(new Date("2026-10-12T08:59:00"), now)).toBe("now");
  });

  it("lights Prep before the meeting, Record once it is armed or started", () => {
    const now = new Date("2026-10-12T09:00:00");
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T10:00:00" }, now)).toBe(0);
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T10:00:00", armed: { recording_id: "r" } }, now)).toBe(1);
    expect(currentStep({ id: "e", source: "calendar_event", starts_at: "2026-10-12T08:30:00" }, now)).toBe(1);
  });

  it("finishes only recent meetings whose summary is not made", () => {
    const now = new Date();
    const rows = [
      { id: "a", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "disabled" },
      { id: "b", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "ready", has_summary: true },
      { id: "c", started_at: inMinutes(-60 * 24 * 9), transcriptWords: 40, intel_status: "disabled" },
    ];
    expect(toFinish(rows, now).map((row) => row.id)).toEqual(["a"]);
  });

  it("draws the next meeting with its steps and later meetings (D4: no Owed or To decide plate)", async () => {
    const calls = hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: inMinutes(50), ends_at: inMinutes(80), person_label: "Priya Nair", person_relationship_id: "r1" },
        { id: "ev2", source: "calendar_event", title: "Ledger cutover sync", starts_at: inMinutes(120), ends_at: inMinutes(150), project_id: "p1", project_name: "Payments" },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [{ id: "unfinished", title: "Old meeting", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "disabled" }] }),
      "/api/desk/needs-you": () => json({ items: [{ proposalId: "pr1", projectId: "p1", title: "Freeze the ledger on Nov 12", meetingTitle: "Ledger cutover sync" }] }),
      "/api/people/readiness": () => json({ readiness: "ready" }),
      "/api/people/relationships?counts=1": () => json({ relationships: [{ id: "r1", you_owe_count: 1, owes_you_count: 1 }] }),
      "/api/proposals/pr1/confirm": () => json({ ok: true }),
    });
    render(<TodayView />);
    const next = await screen.findByTestId("today-next");
    expect(within(next).getByText("1:1 Priya")).toBeTruthy();
    expect(within(next).getByTestId("today-countdown").textContent).toBe("in 50 min");
    expect(within(next).getByText("Prep", { selector: ".kit-step-word" }).closest("li")?.getAttribute("aria-current")).toBe("step");
    expect(within(next).getByRole("button", { name: "Prep" })).toBeTruthy();
    // Betterment D4: a row of Needs you leads; the record verb is secondary.
    await waitFor(() => expect(screen.getByTestId("today-needs").querySelector(".btn--primary")).toBeTruthy());
    expect(within(next).getByRole("button", { name: "Record when it starts" }).className).not.toContain("btn--primary");
    expect(screen.getAllByTestId("today-later")).toHaveLength(1);
    expect(screen.getByTestId("today-now")).toBeTruthy();
    expect(next.compareDocumentPosition(screen.getByTestId("today-finish")) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    // Betterment D4: the Owed and To decide plates left; their rows are the
    // top of Needs you (the same rows as the Needs-you window).
    expect(screen.queryByTestId("today-owed")).toBeNull();
    expect(screen.queryByTestId("today-decide")).toBeNull();
    expect(calls.some(([url, init]) => url.includes("/proposals/") && init?.method === "POST")).toBe(false);
    // One filled primary in the window.
    expect(document.querySelectorAll(".btn--primary")).toHaveLength(1);
  });

  it("shows the changed page on Monday after what I owe", async () => {
    hub({
      "/api/door": () => json({ calendar_configured: false, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
      "/api/people/readiness": () => json({ readiness: "ready" }),
      "/api/people/relationships?counts=1": () => json({ relationships: [] }),
      "/api/memory/pages?scope=desk": () => json({ pages: [
        { slug: "what-i-owe", question: "What do I owe?", sentences: [{ text: "You owe Mira feedback by Friday.", refs: [] }], built_at: "2026-10-12T09:00:00Z", stale: false, new_sources: 0, model: "pages", boundary: "local" },
        { slug: "what-changed-this-week", question: "What changed this week?", sentences: [{ text: "The cutover review moved to Friday.", refs: [] }], built_at: "2026-10-12T09:00:00Z", stale: false, new_sources: 0, model: "pages", boundary: "local" },
      ] }),
    });
    render(<TodayView />);
    expect((await screen.findByTestId("today-owe")).textContent).toContain("You owe Mira feedback by Friday.");
    expect(screen.getByTestId("today-changed").textContent).toContain("The cutover review moved to Friday.");
  });

  it("an empty day with no calendar names the next step", async () => {
    hub({
      "/api/door": () => json({ calendar_configured: false, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
      "/api/people/relationships": () => json({ relationships: [] }),
    });
    render(<TodayView />);
    // Betterment D4: the empty desk is ONE line under Needs you.
    const empty = await screen.findByTestId("today-empty-desk");
    expect(empty.textContent).toContain("No meetings and no calendar yet.");
    expect(within(empty).getByRole("button", { name: "Connect calendar" }).className).toContain("btn--primary");
    expect(screen.queryByTestId("today-empty")).toBeNull();
    expect(screen.getByRole("button", { name: "Record now" }).className).not.toContain("btn--primary");
    expect(screen.queryByTestId("today-owed")).toBeNull();
  });

  it("MUST 3: a failed read says so with Retry; it never reads as empty", async () => {
    hub({
      "/api/door": () => json({ detail: "down" }, 503),
      "/api/meetings?limit=40": () => json({ detail: "down" }, 503),
      "/api/desk/needs-you": () => json({ detail: "down" }, 503),
      "/api/people/readiness": () => json({ readiness: "ready" }),
      "/api/people/relationships?counts=1": () => json({ detail: "down" }, 503),
    });
    render(<TodayView />);
    expect(await screen.findByTestId("today-door-failed")).toHaveTextContent("Could not read the calendar");
    expect(screen.queryByText("No calendar yet")).toBeNull();
    expect(screen.getByTestId("today-meetings-failed")).toHaveTextContent("Could not read the meetings");
    expect(await screen.findByTestId("today-needs-failed")).toHaveTextContent("Needs you could not be read");
    expect(screen.queryByTestId("today-owed")).toBeNull();
    expect(within(screen.getByTestId("today-door-failed")).getByRole("button", { name: "Retry" })).toBeTruthy();
  });

  it("MUST 3: a refused arm says so beside its verb", async () => {
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: inMinutes(50), ends_at: inMinutes(80) },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [{ proposalId: "pr1", title: "Freeze the ledger" }] }),
      "/api/proposals/pr1/confirm": () => json({ detail: "proposal_not_open" }, 409),
      "/api/scheduled-recordings": () => json({ detail: "calendar_event_not_found" }, 404),
    });
    render(<TodayView />);
    fireEvent.click(await screen.findByRole("button", { name: "Record when it starts" }));
    expect(await screen.findByTestId("today-arm-failed")).toHaveTextContent("Not armed. Try again");
  });

  it("an armed next meeting says when it arms", async () => {
    const start = new Date(Date.now() + 50 * 60_000);
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: start.toISOString(), ends_at: inMinutes(80),
          armed: { recording_id: "s1", arms_at: start.toISOString() } },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    render(<TodayView />);
    const pad = (n: number) => String(n).padStart(2, "0");
    expect(await screen.findByTestId("today-armed")).toHaveTextContent(`Armed for ${pad(start.getHours())}:${pad(start.getMinutes())}`);
  });

  it("MUST 2 (amended 2026-10-25): Make the summary names where the run goes in its hover title; no chip on the row", async () => {
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [{
        id: "m1", title: "Vendor sync", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "disabled",
        planned_route: { status: "ready", reason_code: null, selection_hash: "sha256:abc", legs: [
          { ordinal: 1, host: "192.168.1.43", boundary: "lan", profile_id: "p1", profile_revision: 1, deployment_revision_id: "d1" },
          { ordinal: 2, host: "api.example.com", boundary: "cloud", profile_id: "p2", profile_revision: 1, deployment_revision_id: "d2" },
        ] },
      }] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    render(<TodayView />);
    const row = await screen.findByTestId("today-finish");
    expect(within(row).queryByTestId("today-route")).toBeNull();
    expect(row.querySelector(".gadget-chip-egress")).toBeNull();
    expect(row.textContent).not.toMatch(/192\.168|api\.example\.com|\bLAN\b|CLOUD/);
    // The lead host and its fallback, said before the press, on the verb.
    const verb = within(row).getByRole("button", { name: "Make the summary" });
    expect(verb.getAttribute("title")).toBe("Summary runs on 192.168.1.43 · LAN, fallback api.example.com");
  });

  it("MUST 1 (amended 2026-10-25): after the run, a failed attempt stays shown as its outcome, the host in its title", async () => {
    const route = { status: "ready", reason_code: null, selection_hash: "sha256:abc", legs: [
      { ordinal: 1, host: "192.168.1.43", boundary: "lan", profile_id: "p1", profile_revision: 1, deployment_revision_id: "d1" },
      { ordinal: 2, host: "api.example.com", boundary: "cloud", profile_id: "p2", profile_revision: 1, deployment_revision_id: "d2" },
    ] };
    const failedRow = {
      id: "m1", title: "Vendor sync", started_at: inMinutes(-60), transcriptWords: 40,
      intel_status: "error", planned_route: route,
    };
    // The recorded completion: LAN refused the call, the cloud fallback made it.
    const madeRow = {
      ...failedRow, intel_status: "ready", has_summary: true,
      run_receipt: { receipt_id: "rr1", job_id: "j1", meeting_id: "m1", selection_hash: "sha256:abc", outcome: "succeeded",
        attempts: [
          { leg_ordinal: 1, host: "192.168.1.43", outcome: "failed" },
          { leg_ordinal: 2, host: "api.example.com", outcome: "succeeded" },
        ] },
    };
    let ran = false;
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [] }),
      "/api/meetings?limit=40": () => json({ meetings: [ran ? madeRow : failedRow] }),
      "/api/desk/needs-you": () => json({ items: [] }),
      "/api/meetings/m1/intelligence/run": () => { ran = true; return json({ jobId: "j1", state: "queued", drainer: "absent" }); },
    });
    render(<TodayView />);
    const row = await screen.findByTestId("today-finish");
    fireEvent.click(within(row).getByRole("button", { name: "Make the summary" }));
    const made = await screen.findByTestId("today-just-made");
    await waitFor(() => expect(made).toHaveTextContent("Summary made"));
    const attempts = within(made).getByTestId("today-made-attempts");
    // The failed attempt with its outcome; the host only in its title.
    expect(attempts.textContent).toBe("FAILED");
    expect(attempts.querySelector("[title]")?.getAttribute("title")).toBe("192.168.1.43 · LAN");
    expect(attempts.querySelector(".gadget-chip-egress")).toBeNull();
    expect(screen.queryByTestId("today-finish")).toBeNull();
  });

  it("late in the day, the next meeting after midnight leads, with its day", async () => {
    vi.setSystemTime(new Date(2026, 9, 12, 23, 40, 0));
    const start = new Date(2026, 9, 13, 0, 30, 0);
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: start.toISOString(), ends_at: new Date(2026, 9, 13, 1, 0).toISOString(),
          person_label: "Priya Nair", person_relationship_id: "r1" },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    render(<TodayView />);
    const next = await screen.findByTestId("today-next");
    expect(next.textContent).toContain("Tue");
    expect(within(next).getByTestId("today-countdown").textContent).toBe("in 50 min");
    expect(screen.queryByTestId("today-empty")).toBeNull();
  });

  it("Prep opens the 1:1's person on the Prep lens; Choose engine opens Runs on", async () => {
    // replaces: tests/e2e/test_philo17_today_glass.py::test_open_prep_and_make_the_summary_land_in_one_press
    const opened: unknown[] = [];
    const onPerson = (e: Event) => opened.push((e as CustomEvent).detail);
    window.addEventListener(PERSON_OPEN_EVENT, onPerson);
    hub({
      "/api/door": () => json({ calendar_configured: true, upcoming: [
        { id: "ev1", source: "calendar_event", title: "1:1 Priya", starts_at: inMinutes(50), ends_at: inMinutes(80),
          person_label: "Priya Nair", person_relationship_id: "r1" },
      ] }),
      "/api/meetings?limit=40": () => json({ meetings: [{
        id: "m1", title: "Vendor sync", started_at: inMinutes(-60), transcriptWords: 40, intel_status: "disabled",
        planned_route: { status: "unavailable", reason_code: "no_engine", selection_hash: null, legs: [] },
      }] }),
      "/api/desk/needs-you": () => json({ items: [] }),
    });
    try {
      render(<TodayView />);
      fireEvent.click(await screen.findByTestId("today-open-prep"));
      expect(opened).toEqual([expect.objectContaining({ relationshipId: "r1", lens: "prep" })]);
      fireEvent.click(await screen.findByRole("button", { name: "Choose engine" }));
      expect(shell.openSurfaceOr).toHaveBeenCalledWith("open-concierge", "/models", "meetings");
    } finally {
      window.removeEventListener(PERSON_OPEN_EVENT, onPerson);
    }
  });

});

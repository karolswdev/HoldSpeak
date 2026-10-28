// Betterment daily D4: Today is one page, on the hub's OWN answers.
//
// fixtures/daily-week/today.json holds the real hub's reads of the recon's
// week (D1: after the nine keeps, the LAN engine set) with its day on the
// calendar (the 1:1 with Mira in 90 minutes, her series linked to her),
// recorded by tests/unit/test_desk_brief.py::test_today_on_the_daily_week_reads_the_one_number_the_day_and_since_yesterday.
// The brief in it was made by the hub on the read Today makes
// (`/api/brief/latest?ensure=1`): no Generate press. Only apiFetch is a
// double; Today, the Needs-you rows and the needs-you reader are the real ones.
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { recordedGet, type Gets } from "../../test/recordedHub";
import TODAY from "./fixtures/daily-week/today.json";
import EMPTY from "./fixtures/daily-week/today-empty.json";

const api = vi.hoisted(() => ({ fetch: vi.fn() }));
vi.mock("../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../lib/api")>()),
  apiFetch: api.fetch,
}));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openCoderSession: vi.fn(),
  openSurfaceOr: vi.fn(),
}));
const chair = vi.hoisted(() => ({ openChairWindow: vi.fn() }));
vi.mock("../chair/chairWindows", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../chair/chairWindows")>()),
  openChairWindow: chair.openChairWindow,
}));
vi.mock("../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../documentSendsLazy", () => ({
  NoteSendWells: ({ id }: { id: string }) => <div data-testid="note-send-wells" data-note={id} />,
  BriefSendWells: () => <div data-testid="brief-send-wells" />,
}));

import { TodayView } from "../pullouts/views/TodayView";
import { PERSON_OPEN_EVENT } from "../objectWindows";

const GETS = TODAY.gets as Gets;
const RECORDED_AT = new Date(String(TODAY.recordedAt));

function replay(gets: Gets = GETS) {
  const reads: string[] = [];
  const posts: Array<{ url: string; json: unknown }> = [];
  api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
    if (init?.method && init.method !== "GET") {
      posts.push({ url: String(url), json: init.json });
      return {};
    }
    reads.push(String(url));
    return recordedGet(gets, String(url));
  });
  return { reads, posts };
}

const needsRows = () => [...document.querySelectorAll<HTMLElement>("[data-testid='today-needs'] li.needs-row")];
const rowNames = () => needsRows().map((li) => li.querySelector(".needs-row-name")?.textContent ?? "");

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(RECORDED_AT);
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  chair.openChairWindow.mockReset();
});
afterEach(() => {
  vi.useRealTimers();
});

describe("Today is one page (Betterment daily D4), on the recorded week", () => {
  it("with no press: the one number, the top rows of Needs you, the next 1:1 with Prep, Since and This week", async () => {
    const { reads, posts } = replay();
    render(<TodayView />);
    expect(GETS["/api/desk/needs-you?fresh=1"].items).toEqual(expect.arrayContaining([
      expect.objectContaining({
        title: "Draft the rollback runbook",
        direction: "theirs",
        counted: false,
        owner: "Mira",
      }),
    ]));
    // The one number the bell and the Dock say.
    expect(await screen.findByTestId("today-needs-count")).toHaveTextContent(String(GETS["/api/desk/needs-you?fresh=1"].count));
    expect(screen.getByTestId("today-needs-count").textContent).toBe("4");
    // The same rows as the Needs-you window: his own work and what to decide;
    // a person's row only when it is late (Jun's freeze dates).
    await waitFor(() => expect(needsRows().length).toBeGreaterThan(0));
    expect(rowNames()).toEqual(expect.arrayContaining([
      "Email Dana about the cutover window", "Review design doc on settlement retries",
      "Do it", "Talk about the staff path in our next one-on-one",
    ]));
    expect(rowNames()).toHaveLength(5);
    // W2: every counted row is listed, so no "N more in Needs you" row (no zero).
    expect(screen.queryByTestId("today-needs-more")).toBeNull();
    expect(rowNames()).toContain("Confirm the vendor freeze dates");
    for (const later of ["Draft the rollback runbook", "Profile the reconciliation job", "Write up alert rule changes"]) {
      expect(rowNames()).not.toContain(later);
    }
    // One verb per row, by direction (D2): Done on his own, Decide on a decision.
    const dana = needsRows().find((li) => li.textContent?.includes("Email Dana"))!;
    expect(within(dana).getByRole("button", { name: /^Done/ })).toBeTruthy();
    // The day: the next meeting is the 1:1 with Mira, with Prep.
    const next = await screen.findByTestId("today-next");
    expect(within(next).getByText("1:1 with Mira")).toBeTruthy();
    expect(within(next).getByRole("button", { name: "Prep" })).toBeTruthy();
    // Since yesterday: folded to one line of counts, made with no press.
    const since = await screen.findByTestId("today-since");
    // The complete Tuesday producer recording excludes Friday's meetings.
    expect(within(since).getByTestId("today-since-counts").textContent).toBe("2 decisions · 1 promise · 2 more");
    expect(within(since).getByTestId("today-since-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(reads).toContain("/api/brief/latest?ensure=1");
    expect(posts.some((p) => p.url.startsWith("/api/brief/generate"))).toBe(false);
    // This week: a count per day, folded.
    expect(screen.getByTestId("today-week-counts").textContent).toMatch(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d+/);
    // No wings, no Generate, no second list of what waits. (Window grammar
    // 2026-10-24: Refresh is back as a quiet toolbar verb; it re-reads the
    // calendar, which sends no desk change.)
    for (const gone of ["Generate", "Acknowledge", "Follow-through", "Brief"]) {
      expect(screen.queryByRole("button", { name: gone })).toBeNull();
    }
    expect(screen.queryByTestId("today-decide")).toBeNull();
    expect(screen.queryByTestId("today-owed")).toBeNull();
  });

  it("All opens the Needs-you window; Prep opens Mira's prep", async () => {
    replay();
    const opened: unknown[] = [];
    const onPerson = (e: Event) => opened.push((e as CustomEvent).detail);
    window.addEventListener(PERSON_OPEN_EVENT, onPerson);
    try {
      render(<TodayView />);
      fireEvent.click(await screen.findByTestId("today-needs-all"));
      expect(chair.openChairWindow).toHaveBeenCalledWith("chair:needs");
      fireEvent.click(await screen.findByTestId("today-open-prep"));
      const mira = (GETS["/api/door"].upcoming as Array<{ title: string; person_relationship_id?: string }>)
        .find((e) => e.title === "1:1 with Mira")!;
      expect(opened).toEqual([expect.objectContaining({ relationshipId: mira.person_relationship_id, lens: "prep" })]);
    } finally {
      window.removeEventListener(PERSON_OPEN_EVENT, onPerson);
    }
  });

  it("Since yesterday unfolds to what changed (not what waits) and links Decisions", async () => {
    replay();
    render(<TodayView />);
    fireEvent.click(await screen.findByTestId("today-since-toggle"));
    const rows = await screen.findByTestId("today-since-rows");
    const texts = [...rows.querySelectorAll("[data-testid='brief-sf-row']")].map((r) => r.textContent ?? "");
    expect(texts.some((t) => t.includes("Adopt idempotent retries with a dedupe key"))).toBe(true);
    expect(texts.some((t) => t.includes("Freeze ledger writes during the cutover"))).toBe(true);
    expect(texts.some((t) => t.includes("Draft the rollback runbook"))).toBe(false);
    // The brief's waiting rows are Needs you's, above: never listed twice.
    expect(texts.some((t) => t.startsWith("Email Dana about the cutover window"))).toBe(false);
    expect(within(rows).getByTestId("today-since-decisions")).toHaveTextContent("Decisions");
  });

  it("the Decisions door opens the Decisions window, not a page in Today (the owner, 2026-10-25)", async () => {
    replay();
    const { useDesk } = await import("../store");
    useDesk.setState({ windowsById: {} });
    const asked: unknown[] = [];
    const listen = (event: Event) => asked.push((event as CustomEvent).detail);
    window.addEventListener("holdspeak:intelligence-navigate", listen);
    try {
      render(<TodayView />);
      fireEvent.click(await screen.findByTestId("today-since-toggle"));
      fireEvent.click(await screen.findByTestId("today-since-decisions"));
      expect(useDesk.getState().windowsById["surface-decisions"]).toBeTruthy();
      expect(useDesk.getState().windowsById["surface-decisions"]?.scope ?? null).toBeNull();
      await new Promise((resolve) => setTimeout(resolve, 0));
      expect(asked).toEqual([]);
    } finally {
      window.removeEventListener("holdspeak:intelligence-navigate", listen);
    }
  });

  it("Done on a row is the Needs-you verb: the same write, and the row's Undo in Today's foot", async () => {
    const { posts } = replay();
    render(<TodayView />);
    await waitFor(() => expect(needsRows().length).toBeGreaterThan(0));
    const dana = needsRows().find((li) => li.textContent?.includes("Email Dana"))!;
    await act(async () => { fireEvent.click(within(dana).getByRole("button", { name: /^Done/ })); });
    await waitFor(() => expect(posts.some((p) => p.url === "/api/follow-through/complete")).toBe(true));
  });

  it("an empty desk is one line: No meetings and no calendar yet, with Connect calendar", async () => {
    // A fresh hub's own answers (no calendar, no meeting, nothing waits).
    vi.setSystemTime(new Date(String(EMPTY.recordedAt)));
    replay(EMPTY.gets as Gets);
    render(<TodayView />);
    const line = await screen.findByTestId("today-empty-desk");
    expect(line.textContent).toContain("No meetings and no calendar yet.");
    expect(within(line).getByRole("button", { name: "Connect calendar" })).toBeTruthy();
    expect(screen.getByTestId("today-record-now")).toBeTruthy();
    expect(screen.queryByTestId("today-needs-count")).toBeNull();
  });
});

// ── Betterment daily D6: a People read that failed is one line, Today stays ──
import PEOPLE_LOCKED from "./fixtures/daily-week/needs-you-people-locked.json";

describe("Today when People could not be read (Betterment D6)", () => {
  it("draws one line in Needs you with Try again; the day still draws", async () => {
    const { reads } = replay({ ...GETS, "/api/desk/needs-you?fresh=1": (PEOPLE_LOCKED.gets as Gets)["/api/desk/needs-you?fresh=1"] });
    render(<TodayView />);
    const line = await screen.findByTestId("today-people-read-failed");
    expect(line.textContent).toContain("People could not be read");
    expect(within(line).getByRole("button", { name: "Try again" })).toBeTruthy();
    expect(screen.getByTestId("today-needs")).toBeTruthy();
    fireEvent.click(within(line).getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(reads.at(-1)).toBe("/api/desk/needs-you?fresh=1"));
  });

  it("the Needs you read failure Retry forces a fresh read", async () => {
    const { reads } = replay();
    const base = api.fetch.getMockImplementation()!;
    let failed = true;
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      if (failed && String(url).startsWith("/api/desk/needs-you")) throw new Error("read failed");
      return base(url, init);
    });
    render(<TodayView />);
    const failedLine = await screen.findByTestId("today-needs-failed");
    failed = false;
    fireEvent.click(within(failedLine).getByRole("button", { name: "Retry" }));
    await waitFor(() => expect(reads.at(-1)).toBe("/api/desk/needs-you?fresh=1"));
  });

  it("the recorded week (People readable) draws no such line", async () => {
    replay();
    render(<TodayView />);
    await screen.findByTestId("today-needs-count");
    expect(screen.queryByTestId("today-people-read-failed")).toBeNull();
  });
});

// ── Betterment daily D7: the 1:1 prep, one press from Today ──
import PREP_WEEK from "./fixtures/daily-week/one-on-one-prep.json";
import { cleanup } from "@testing-library/react";
import { PersonWindowBody } from "../../pages/cores/PeopleCore";

describe("Today's Prep opens the 1:1 prep (Betterment D7), on one recorded boot", () => {
  /** tests/integration/test_desk_people.py::test_one_on_one_prep_wire: Today's
   *  reads and Mira's prep reads, her 1:1 in 90 minutes. */
  const gets = PREP_WEEK.gets as Gets;

  it("NEXT card Prep opens Mira's prep: her promise with Nudge, I owe Mira, To raise, Last time, the next 1:1 time", async () => {
    vi.setSystemTime(new Date(String(PREP_WEEK.recordedAt)));
    const { posts } = replay(gets);
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      if (init?.method && init.method !== "GET") {
        posts.push({ url: String(url), json: init.json });
        return String(url) === "/api/notes" ? { note: { id: "note-nudge" } } : {};
      }
      return recordedGet(gets, String(url));
    });
    const opened: Array<{ relationshipId: string; lens: string }> = [];
    const onPerson = (e: Event) => opened.push((e as CustomEvent).detail);
    window.addEventListener(PERSON_OPEN_EVENT, onPerson);
    try {
      render(<TodayView />);
      fireEvent.click(await screen.findByTestId("today-open-prep"));
    } finally {
      window.removeEventListener(PERSON_OPEN_EVENT, onPerson);
    }
    expect(opened).toEqual([expect.objectContaining({ relationshipId: "rel-mira", lens: "prep" })]);
    cleanup();

    render(<PersonWindowBody relationshipId={opened[0].relationshipId} />);
    const owes = await screen.findByTestId("people-they-owe", {}, { timeout: 5000 });
    expect(owes.querySelector("h3")!.textContent).toBe("Mira owes me1");
    expect(owes.textContent).toContain("Draft the rollback runbook");
    expect(screen.getByTestId("people-you-owe").querySelector("h3")!.textContent).toBe("I owe Mira");
    expect(screen.getByTestId("prep-to-raise")).toBeTruthy();
    // The next 1:1 time, from her linked series.
    expect(screen.getByTestId("people-next-1on1").textContent).toMatch(/in 1 h 30 min|in 90 min|in 1 h 29 min/);
    expect(screen.queryByRole("button", { name: "Pick from calendar" })).toBeNull();
    // Last time: the last meeting she was in, its points and its decision.
    const last = screen.getByTestId("prep-last");
    expect(within(last).getByTestId("prep-last-title").textContent).toMatch(/^Payments platform sync on /);
    expect(within(last).getByTestId("prep-last-facts").textContent).toBe("4 points · 1 decision");
    expect(last.textContent).toContain("Freeze ledger writes during the cutover");
    // Nudge drafts a message to her; he presses Send in the well.
    fireEvent.click(within(owes).getByRole("button", { name: "Nudge" }));
    expect((await screen.findByTestId("prep-nudge-text")).textContent).toMatch(/^Mira, is "Draft the rollback runbook" on track for /);
    await waitFor(() => expect(posts.some((p) => p.url === "/api/notes")).toBe(true));
    expect(await screen.findByTestId("note-send-wells")).toBeTruthy();
    expect(posts.filter((p) => p.url.startsWith("/api/channels"))).toEqual([]);
  });
});

describe("I owe Theo (Betterment D7), on the same recorded boot", () => {
  it("what I said I would do in our 1:1 is under I owe Theo, with Done", async () => {
    vi.setSystemTime(new Date(String(PREP_WEEK.recordedAt)));
    const gets = PREP_WEEK.gets as Gets;
    replay(gets);
    render(<PersonWindowBody relationshipId="rel-theo" />);
    const mine = await screen.findByTestId("people-you-owe", {}, { timeout: 5000 });
    expect(mine.querySelector("h3")!.textContent).toBe("I owe Theo1");
    const row = within(mine).getByTestId("prep-i-owe-action");
    expect(row.textContent).toContain("Review design doc on settlement retries");
    expect(row.textContent).toContain("from 1:1 with Theo");
    expect(within(row).getByRole("button", { name: "Done" })).toBeTruthy();
    expect(within(screen.getByTestId("prep-last")).getByTestId("prep-last-title").textContent).toMatch(/^1:1 on /);
  });
});

// ── Betterment A6: an automation's NEW result is a row in Today ─────────────
// The new-result rows are the hub's own answers from
// tests/integration/test_desk_workbenches.py
// (test_put_it_in_files_a_fresh_desk_inbox_and_new_results_show_until_opened):
// put-new holds one NEW result of "Friday team update"; put-opened, the same
// automation after the result was opened.
import PUT_NEW from "./fixtures/automation-hub/put-new.json";
import PUT_OPENED from "./fixtures/automation-hub/put-opened.json";
import { useDesk } from "../store";

describe("Today names an automation's NEW result (Betterment A6)", () => {
  const news = (step: { gets: Gets }) => ({ "/api/automations/new": step.gets["/api/automations/new"] });

  it("says '<name> has a new result' with Open, which opens the automation window", async () => {
    vi.setSystemTime(new Date(String(EMPTY.recordedAt)));
    replay({ ...(EMPTY.gets as Gets), ...news(PUT_NEW as { gets: Gets }) });
    const openWorkbenchWindow = vi.fn();
    const before = useDesk.getState().openWorkbenchWindow;
    useDesk.setState({ openWorkbenchWindow });
    try {
      render(<TodayView />);
      const row = await screen.findByTestId("today-new-result");
      expect(row).toHaveTextContent("Friday team update has a new result");
      // A desk with a NEW result is not an empty desk.
      expect(screen.queryByTestId("today-empty-desk")).toBeNull();
      fireEvent.click(within(row).getByRole("button", { name: "Open Friday team update" }));
      expect(openWorkbenchWindow).toHaveBeenCalledWith((PUT_NEW as { workbench_id: string }).workbench_id);
      expect(row.textContent).not.toMatch(/wb-|artifact_/);
    } finally {
      useDesk.setState({ openWorkbenchWindow: before });
    }
  });

  it("once the result is opened, the row is gone", async () => {
    vi.setSystemTime(new Date(String(EMPTY.recordedAt)));
    replay({ ...(EMPTY.gets as Gets), ...news(PUT_OPENED as { gets: Gets }) });
    render(<TodayView />);
    await screen.findByTestId("today-empty-desk");
    expect(screen.queryByTestId("today-new-result")).toBeNull();
  });
});

// ── Betterment daily D9: Morning prep fills Today's Prepared block ─────────
// fixtures/daily-week/today-prepared.json holds a real hub's reads after
// Prepare now ran Morning prep on the recon's week (the 1:1 with Mira in 90
// minutes), with Claude Code (the fake CLI replaying its tool plan over MCP)
// as the engine: tests/integration/test_desk_morning_prep.py.
import PREPARED from "./fixtures/daily-week/today-prepared.json";

describe("Today's Prepared block (Betterment daily D9), on the recorded run", () => {
  const gets = PREPARED.gets as Gets;
  const read = gets["/api/automations/prepared"] as { prepared: { engine: string; workbench_id: string } };

  it("shows the block with the engine's name, a card for the 1:1 with Mira, and what it looked at", async () => {
    vi.setSystemTime(new Date(String(PREPARED.recordedAt)));
    replay(gets);
    render(<TodayView />);
    const block = await screen.findByTestId("today-prepared");
    expect(read.prepared.engine).toBeTruthy();
    expect(within(block).getByTestId("today-prepared-by").textContent).toContain(read.prepared.engine);
    expect(within(block).getByTestId("today-prepared-new")).toHaveTextContent("NEW");
    const cards = within(block).getAllByTestId("today-prepared-card");
    const mira = cards.find((card) => card.textContent?.includes("1:1 with Mira"))!;
    expect(mira).toBeTruthy();
    expect(mira.textContent).toContain(String(PREPARED.miraAt));
    expect(mira.textContent).toContain("Mira owes: Draft the rollback runbook");
    // Her card opens her prep (the event on the calendar names her).
    expect(within(mira).getByRole("button", { name: "Prep" })).toBeTruthy();
    expect(within(block).getByTestId("today-prepared-mine").textContent).toContain("Email Dana about the cutover window");
    expect(within(block).getByTestId("today-prepared-nudges").textContent).toContain("Theo:");
    expect(within(block).getByTestId("today-prepared-looked").textContent).toContain("Payments platform sync");
    // Prepare now runs it once more.
    expect(screen.getByTestId("today-prepare-now")).toBeTruthy();
  });

  it("Add on a suggested point puts it on Mira's 1:1 agenda (the prep's own writes)", async () => {
    vi.setSystemTime(new Date(String(PREPARED.recordedAt)));
    const { posts } = replay(gets);
    api.fetch.mockImplementation(async (url: string, init?: { method?: string; json?: unknown }) => {
      if (init?.method && init.method !== "GET") {
        posts.push({ url: String(url), json: init.json });
        return String(url).endsWith("/one-on-ones") ? { one_on_one: { id: "1on1-new" } } : {};
      }
      return recordedGet(gets, String(url));
    });
    render(<TodayView />);
    const raise = (await screen.findAllByTestId("today-prepared-raise"))[0];
    expect(raise.textContent).toContain("Suggested");
    await act(async () => { fireEvent.click(within(raise).getByRole("button", { name: /^Add to the agenda:/ })); });
    await waitFor(() => expect(posts.some((p) => p.url.endsWith("/agenda"))).toBe(true));
    const agenda = posts.find((p) => p.url.endsWith("/agenda"))!;
    expect(agenda.url).toMatch(/^\/api\/people\/one-on-ones\/[^/]+\/agenda$/);
    expect(agenda.json).toEqual(expect.objectContaining({ body: "Who owns read-only vs archive for the old ledger?", state: "open" }));
    expect(await within(raise).findByText("On the agenda")).toBeTruthy();
  });

  it("Prepare now runs Morning prep (Run now on its automation)", async () => {
    vi.setSystemTime(new Date(String(PREPARED.recordedAt)));
    const { posts } = replay(gets);
    render(<TodayView />);
    const prepare = await screen.findByTestId("today-prepare-now");
    await act(async () => { fireEvent.click(prepare); });
    await waitFor(() => expect(posts.map((p) => p.url)).toContain(`/api/workbenches/${read.prepared.workbench_id}/run`));
  });

  it("with no Morning prep result there is no block (the recorded week before any run)", async () => {
    replay();
    render(<TodayView />);
    await screen.findByTestId("today-needs-count");
    expect(screen.queryByTestId("today-prepared")).toBeNull();
    expect(screen.queryByTestId("today-prepare-now")).toBeNull();
  });
});

/* Betterment AG9: Today's Agents line and a card per finished turn he has
 * not opened, on the hub's recorded fleet (agents.app.test's fixtures/
 * agents-ag8: two agents need him, one finished and is New). */
import AG8 from "./fixtures/agents-ag8/coders-sessions.wire.json";

describe("agents in Today (Betterment AG9)", () => {
  it("says 2 agents need you · 1 finished, and the finished turn is a card with Open", async () => {
    const { reads } = replay();
    const base = api.fetch.getMockImplementation()!;
    api.fetch.mockImplementation(async (url: string, init?: { method?: string }) =>
      String(url).startsWith("/api/coders/sessions") ? (AG8 as { wire: unknown }).wire : base(url, init));
    render(<TodayView />);
    expect(await screen.findByTestId("today-agents")).toHaveTextContent("2 agents need you · 1 finished");
    const cards = await screen.findAllByTestId("today-agent-result");
    expect(cards).toHaveLength(1);
    expect(cards[0]).toHaveTextContent("Claude Code finished Draft test scaffolding for flags");
    expect(within(cards[0]).getByRole("button", { name: /^Open/ })).toBeTruthy();
    expect(reads.some((url) => url.startsWith("/api/door"))).toBe(true);
  });
});

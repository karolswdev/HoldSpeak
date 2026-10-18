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
    expect(within(since).getByTestId("today-since-counts").textContent).toBe("2 decisions · 5 promises · 2 more");
    expect(within(since).getByTestId("today-since-toggle")).toHaveAttribute("aria-expanded", "false");
    expect(reads).toContain("/api/brief/latest?ensure=1");
    expect(posts.some((p) => p.url.startsWith("/api/brief/generate"))).toBe(false);
    // This week: a count per day, folded.
    expect(screen.getByTestId("today-week-counts").textContent).toMatch(/^(Mon|Tue|Wed|Thu|Fri|Sat|Sun) \d+/);
    // No wings, no Generate, no Refresh, no second list of what waits.
    for (const gone of ["Generate", "Refresh", "Acknowledge", "Follow-through", "Brief"]) {
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
    expect(texts.some((t) => t.includes("Draft the rollback runbook"))).toBe(true);
    // The brief's waiting rows are Needs you's, above: never listed twice.
    expect(texts.some((t) => t.startsWith("Email Dana about the cutover window"))).toBe(false);
    expect(within(rows).getByTestId("today-since-decisions")).toHaveTextContent("Decisions");
  });

  it("Done on a row is the Needs-you verb: the same write, and the row's Undo in Today's foot", async () => {
    const { posts } = replay();
    render(<TodayView />);
    await waitFor(() => expect(needsRows().length).toBeGreaterThan(0));
    const dana = needsRows().find((li) => li.textContent?.includes("Email Dana"))!;
    await act(async () => { fireEvent.click(within(dana).getByRole("button", { name: /^Done/ })); });
    await waitFor(() => expect(posts.some((p) => p.url === "/api/follow-through/complete")).toBe(true));
  });

  it("an empty desk is one line: Your meetings and calendar fill this, with Connect calendar", async () => {
    // A fresh hub's own answers (no calendar, no meeting, nothing waits).
    vi.setSystemTime(new Date(String(EMPTY.recordedAt)));
    replay(EMPTY.gets as Gets);
    render(<TodayView />);
    const line = await screen.findByTestId("today-empty-desk");
    expect(line.textContent).toContain("Your meetings and calendar fill this.");
    expect(within(line).getByRole("button", { name: "Connect calendar" })).toBeTruthy();
    expect(screen.getByTestId("today-record-now")).toBeTruthy();
    expect(screen.queryByTestId("today-needs-count")).toBeNull();
  });
});

// ── Betterment daily D6: a People read that failed is one line, Today stays ──
import PEOPLE_LOCKED from "./fixtures/daily-week/needs-you-people-locked.json";

describe("Today when People could not be read (Betterment D6)", () => {
  it("draws one line in Needs you with Try again; the day still draws", async () => {
    replay({ ...GETS, "/api/desk/needs-you?fresh=1": (PEOPLE_LOCKED.gets as Gets)["/api/desk/needs-you?fresh=1"] });
    render(<TodayView />);
    const line = await screen.findByTestId("today-people-read-failed");
    expect(line.textContent).toContain("People could not be read");
    expect(within(line).getByRole("button", { name: "Try again" })).toBeTruthy();
    expect(screen.getByTestId("today-needs")).toBeTruthy();
  });

  it("the recorded week (People readable) draws no such line", async () => {
    replay();
    render(<TodayView />);
    await screen.findByTestId("today-needs-count");
    expect(screen.queryByTestId("today-people-read-failed")).toBeNull();
  });
});

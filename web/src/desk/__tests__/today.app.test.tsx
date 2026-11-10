/** Real hub recordings from test_desk_brief, test_desk_morning_prep and
 * test_desk_today. Only transport and window openers are doubled. */
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { recordedGet, type Gets } from "../../test/recordedHub";
import TODAY from "./fixtures/daily-week/today.json";
import EMPTY from "./fixtures/daily-week/today-empty.json";
import PREPARED from "./fixtures/daily-week/today-prepared.json";
import SUMMARY from "./fixtures/meetings-hub/hs170.json";
import ACTIVITY from "./fixtures/today-hub/since-morning.programs.json";
const api = vi.hoisted(() => ({ fetch: vi.fn() }));
const chair = vi.hoisted(() => ({ openChairWindow: vi.fn() }));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: api.fetch,
}));
vi.mock("../chair/chairWindows", async (original) => ({
  ...(await original<typeof import("../chair/chairWindows")>()),
  openChairWindow: chair.openChairWindow,
}));
vi.mock("../documentSendsLazy", () => ({
  BriefSendWells: () => <div data-testid="brief-send-wells" />,
}));
import { TodayView } from "../pullouts/views/TodayView";
import { WindowIdContext } from "../components/window/windowIdContext";
import { ApplicationMenu } from "../components/DeskMenuBar";
import { appWalk } from "../walk/appWalks";
import { PERSON_OPEN_EVENT } from "../objectWindows";
const gets = TODAY.gets as Gets;
function replay(answers: Gets = gets) {
  api.fetch.mockImplementation(async (path: string) =>
    recordedGet(answers, path),
  );
}
beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(TODAY.recordedAt));
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  api.fetch.mockReset();
  chair.openChairWindow.mockReset();
  replay();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
});
const pick = (id: string) =>
  fireEvent.click(
    within(screen.getByTestId("today-rail")).getByRole("option", { name: id }),
  );
const settled = () =>
  waitFor(() =>
    expect(screen.getByTestId("today-body")).not.toHaveAttribute(
      "aria-busy",
      "true",
    ),
  );
describe("Today is a native app", () => {
  it("keeps answers in Needs you; its one plate opens that window", async () => {
    render(<TodayView />);
    await settled();
    expect(screen.getByTestId("today-needs-count")).toHaveTextContent(
      String(gets["/api/desk/needs-you?fresh=1"].count),
    );
    expect(
      screen.queryByText("Email Dana about the cutover window"),
    ).toBeNull();
    expect(document.querySelector(".needs-row")).toBeNull();
    fireEvent.click(screen.getByTestId("today-needs-all"));
    expect(chair.openChairWindow).toHaveBeenCalledWith("chair:needs");
  });
  it("a rail press renders the recorded brief without another gather", async () => {
    render(<TodayView />);
    await settled();
    pick("Brief");
    expect(await screen.findByTestId("today-since-rows")).toHaveTextContent(
      "Adopt idempotent retries with a dedupe key",
    );
    expect(screen.queryByTestId("today-next")).toBeNull();
    expect(
      api.fetch.mock.calls.filter(
        ([path]) => path === "/api/brief/latest?ensure=1",
      ),
    ).toHaveLength(1);
    expect(
      api.fetch.mock.calls.some(
        ([path, init]) =>
          path.includes("brief/generate") || init?.method === "POST",
      ),
    ).toBe(false);
  });
  it("Prep still opens the person named by the hub", async () => {
    const opened: unknown[] = [];
    const listen = (event: Event) => opened.push((event as CustomEvent).detail);
    window.addEventListener(PERSON_OPEN_EVENT, listen);
    try {
      render(<TodayView />);
      await settled();
      fireEvent.click(screen.getByTestId("today-open-prep"));
      const next = gets["/api/door"].upcoming.find(
        (event: { title: string }) => event.title === "1:1 with Mira",
      );
      expect(opened).toEqual([
        expect.objectContaining({
          relationshipId: next.person_relationship_id,
          lens: "prep",
        }),
      ]);
    } finally {
      window.removeEventListener(PERSON_OPEN_EVENT, listen);
    }
  });
  it("a failed brief read stays named and Retry renders the answer", async () => {
    let fail = true;
    api.fetch.mockImplementation(async (path: string) => {
      if (fail && path === "/api/brief/latest?ensure=1")
        throw new Error("Unavailable");
      return recordedGet(gets, path);
    });
    render(<TodayView />);
    await settled();
    pick("Brief");
    const failure = await screen.findByTestId("today-since-failed");
    fail = false;
    fireEvent.click(within(failure).getByRole("button", { name: "Retry" }));
    expect(await screen.findByTestId("today-since-rows")).toHaveTextContent(
      "Adopt idempotent retries",
    );
    expect(screen.queryByTestId("today-since-failed")).toBeNull();
  });
  it("Prepared is picked in place and retains the real result", async () => {
    vi.setSystemTime(new Date(PREPARED.recordedAt));
    replay(PREPARED.gets as Gets);
    render(<TodayView />);
    await settled();
    pick("Prepared");
    expect(await screen.findByTestId("today-prepared")).toHaveTextContent(
      "1:1 with Mira",
    );
    expect(screen.getByTestId("today-prepared-by")).toHaveTextContent(
      (PREPARED.gets as Gets)["/api/automations/prepared"].prepared.engine,
    );
  });
  it("a failed Prepared read offers Retry and recovers the recorded work", async () => {
    const answers = PREPARED.gets as Gets;
    vi.setSystemTime(new Date(PREPARED.recordedAt));
    let fail = true;
    api.fetch.mockImplementation(async (path: string) => {
      if (fail && path === "/api/automations/prepared")
        throw new Error("Unavailable");
      return recordedGet(answers, path);
    });
    render(<TodayView />);
    await settled();
    pick("Prepared");
    const failure = await screen.findByTestId("today-prepared-failed");
    fail = false;
    fireEvent.click(within(failure).getByRole("button", { name: "Retry" }));
    expect(await screen.findByTestId("today-prepared")).toHaveTextContent(
      "1:1 with Mira",
    );
    expect(screen.queryByTestId("today-prepared-failed")).toBeNull();
  });
  it("a refresh failure keeps the last brief visible and names the stale read", async () => {
    render(<TodayView />);
    await settled();
    pick("Brief");
    api.fetch.mockImplementation(async (path: string) => {
      if (path === "/api/brief/latest?ensure=1") throw new Error("Unavailable");
      return recordedGet(gets, path);
    });
    fireEvent.click(screen.getByTestId("today-refresh"));
    expect(await screen.findByTestId("today-brief-stale")).toHaveTextContent(
      "Could not read the latest brief",
    );
    expect(screen.getByTestId("today-since-rows")).toHaveTextContent(
      "Adopt idempotent retries",
    );
  });
  it("an activity failure stays named instead of reporting an empty day", async () => {
    api.fetch.mockImplementation(async (path: string) => {
      if (path === "/api/today/since-morning") throw new Error("Unavailable");
      return recordedGet(gets, path);
    });
    render(<TodayView />);
    await settled();
    pick("Activity");
    expect(await screen.findByTestId("today-done-failed")).toHaveTextContent(
      "Could not read today's work",
    );
    expect(screen.queryByText("Nothing done yet")).toBeNull();
  });
  it("Activity renders the hub's account of Programs since the last visit", async () => {
    replay({ ...gets, ...ACTIVITY });
    render(<TodayView />);
    await settled();
    pick("Activity");
    const read = ACTIVITY["/api/today/since-morning"];
    expect(await screen.findByTestId("today-since-last")).toHaveTextContent(
      read.since_last_here.lines[0].title,
    );
    expect(screen.getByTestId("today-since-last")).toHaveTextContent(
      read.since_last_here.lines[0].line,
    );
  });
  it("an empty day has no raised plate and offers the calendar", async () => {
    vi.setSystemTime(new Date(EMPTY.recordedAt));
    replay(EMPTY.gets as Gets);
    render(<TodayView />);
    await settled();
    expect(screen.getByTestId("today-empty-desk")).toHaveTextContent(
      "No meetings and no calendar yet",
    );
    expect(document.querySelector(".today-plate")).toBeNull();
    expect(
      screen.getByRole("button", { name: "Connect calendar" }),
    ).toBeTruthy();
  });
  it("Make the summary keeps the acknowledged queue receipt on screen", async () => {
    vi.setSystemTime(new Date(SUMMARY._now));
    // The recorded list has fewer than 40 rows, so it is also the Today page.
    const answers = {
      ...gets,
      "/api/meetings?limit=40": SUMMARY["/api/meetings?limit=100"],
    };
    const path = "/api/meetings/m-off-words/intelligence/run";
    api.fetch.mockImplementation(
      async (url: string, init?: { method?: string }) =>
        url === path && init?.method === "POST"
          ? structuredClone(
              SUMMARY["POST /api/meetings/m-off-words/intelligence/run"],
            )
          : recordedGet(answers, url),
    );
    render(<TodayView />);
    await settled();
    const row = screen
      .getAllByTestId("today-finish")
      .find((item) => item.textContent?.includes("Census standup"))!;
    fireEvent.click(
      within(row).getByRole("button", { name: "Make the summary" }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent("Queued at"),
    );
    expect(api.fetch).toHaveBeenCalledWith(path, {
      method: "POST",
      json: {
        expected_selection_hash:
          SUMMARY["POST /api/meetings/m-off-words/intelligence/run"]
            .planned_route.selection_hash,
      },
    });
  });
  it("a refused summary press keeps the meeting and a retry receipt", async () => {
    vi.setSystemTime(new Date(SUMMARY._now));
    const answers = {
      ...gets,
      "/api/meetings?limit=40": SUMMARY["/api/meetings?limit=100"],
    };
    api.fetch.mockImplementation(
      async (url: string, init?: { method?: string }) => {
        if (init?.method === "POST") throw new Error("Unavailable");
        return recordedGet(answers, url);
      },
    );
    render(<TodayView />);
    await settled();
    const row = screen
      .getAllByTestId("today-finish")
      .find((item) => item.textContent?.includes("Census standup"))!;
    fireEvent.click(
      within(row).getByRole("button", { name: "Make the summary" }),
    );
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent(
        "Summary did not start",
      ),
    );
    expect(
      within(row).getByRole("button", { name: "Make the summary" }),
    ).toBeEnabled();
    expect(row).toHaveTextContent("Census standup");
  });
  it("carries an in-place walk of real, stable face targets", async () => {
    render(<WindowIdContext.Provider value="pullout:intelligence:desk"><ApplicationMenu windowId="pullout:intelligence:desk" /><TodayView /></WindowIdContext.Provider>);
    await settled();
    const walk = appWalk("open-intelligence");
    expect(walk).toBeTruthy();
    expect(walk?.open.app).toBe("pullout:intelligence:desk");
    for (const step of walk?.steps ?? []) {
      if (step.highlight?.target)
        expect(screen.getByTestId(step.highlight.target)).toBeTruthy();
    }
    fireEvent.click(within(screen.getByTestId("desk-screen-title")).getByRole("button"));
    expect(screen.getByRole("menuitem", { name: "Show me" })).toBeVisible();
  });
});

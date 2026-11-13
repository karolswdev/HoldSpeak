/** Presses replay answers recorded by the real Today HTTP producer. */
import {
  act,
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
import MORE from "./fixtures/today-hub/today-more.json";
import EMPTY from "./fixtures/daily-week/today-empty.json";
import PREPARED from "./fixtures/daily-week/today-prepared.json";
import NOTHING from "./fixtures/daily-week/today-prepared-nothing.json";
import PAGES from "../../test/wire/memory.desk-pages.wire.json";
import SUMMARY from "./fixtures/meetings-hub/hs170.json";
import UNAVAILABLE from "./fixtures/meetings-hub/list-app.json";
import ACTIVITY from "./fixtures/today-hub/since-morning.programs.json";
const io = vi.hoisted(() => ({
  fetch: vi.fn(),
  chair: vi.fn(),
  surface: vi.fn(),
  changed: null as null | (() => void),
}));
vi.mock("../../lib/api", async (original) => ({
  ...(await original<typeof import("../../lib/api")>()),
  apiFetch: io.fetch,
}));
vi.mock("../chair/chairWindows", () => ({ openChairWindow: io.chair }));
vi.mock("../shell", async (original) => ({
  ...(await original<typeof import("../shell")>()),
  openSurfaceOr: io.surface,
}));
vi.mock("../useDeskChangedRefresh", async (original) => ({
  ...(await original<typeof import("../useDeskChangedRefresh")>()),
  useOnDeskChanged: (callback: () => void, kinds?: readonly string[]) => {
    if (!kinds) io.changed = callback;
  },
}));
vi.mock("../documentSendsLazy", () => ({
  BriefSendWells: ({ brief }: { brief: { id: string } }) => (
    <div data-testid="brief-send-wells" data-brief-id={brief.id}>
      Send preview
    </div>
  ),
}));
import { TodayView } from "../pullouts/views/TodayView";
import { needNameOf, tierOf, tierWord } from "../needs/needsFace";
import { useDesk } from "../store";
import { PERSON_OPEN_EVENT } from "../objectWindows";
import { appWalk } from "../walk/appWalks";
const gets = TODAY.gets as Gets;
function replay(answers: Gets = gets) {
  io.fetch.mockImplementation(async (path: string) =>
    recordedGet(answers, path),
  );
}
const settled = () =>
  waitFor(() =>
    expect(screen.getByTestId("today-body")).not.toHaveAttribute(
      "aria-busy",
      "true",
    ),
  );
function view(name: string) {
  fireEvent.click(screen.getByRole("button", { name: "Today view" }));
  fireEvent.click(
    within(screen.getByRole("menu", { name: "Today view" })).getByText(name, {
      exact: true,
    }),
  );
}
function row(name: string) {
  return screen
    .getAllByRole("row")
    .find((row) => row.textContent?.includes(name))!;
}
const verb = (name: string) => {
  const toolbar = screen.getByTestId("today-toolbar");
  const direct = within(toolbar).queryByRole("button", { name });
  if (direct) return direct;
  if (!screen.queryByRole("menu"))
    fireEvent.click(within(toolbar).getByRole("button", { name: "Actions ▾" }));
  return within(screen.getByRole("menu")).getByRole("menuitem", { name });
};

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(TODAY.recordedAt));
  io.fetch.mockReset();
  io.chair.mockReset();
  io.surface.mockReset();
  io.changed = null;
  replay();
});
afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.restoreAllMocks();
});
describe("Today selection and inspector", () => {
  it("accounts for every waiting item and opens the remaining work from the group", async () => {
    vi.setSystemTime(new Date(MORE.recordedAt));
    replay({ ...gets, ...MORE.gets });
    render(<TodayView />);
    await settled();
    const group = screen.getByRole("rowgroup", { name: "Waits on you" });
    const shown = within(group).getAllByRole("row");
    const count = MORE.gets["/api/today"].needs_you.count;
    const remaining = count - shown.length;
    expect(remaining).toBeGreaterThan(0);
    expect(group.querySelector(".object-list-group-label")).toHaveTextContent(String(count));
    const more = within(group).getByRole("button", { name: `Open Needs you (${remaining} more)` });
    expect(more).toBeEnabled();
    expect(more.closest(".object-list-row")).toBeNull();
    expect(group.lastElementChild).toContainElement(more);
    fireEvent.click(more);
    expect(io.chair).toHaveBeenCalledWith("chair:needs");
  });
  it("shows no remaining-work row when the waiting rows cover the full count", async () => {
    render(<TodayView />);
    await settled();
    expect(screen.queryByRole("button", { name: /Open Needs you \(\d+ more\)/ })).not.toBeInTheDocument();
  });
  it("round 2 item 3: a waiting row names its work, person and source in sentence case", async () => {
    render(<TodayView />);
    await settled();
    const item = gets["/api/desk/needs-you?fresh=1"].items.find(
      (r: any) => r.counted && r.person_name,
    );
    const shown = row(item.title);
    expect(shown).toBeTruthy();
    expect(shown).toHaveTextContent(item.person_name);
    expect(shown.querySelector(".object-list-detail")).toHaveTextContent(
      item.projectName,
    );
    expect(shown.querySelector(".object-list-detail")?.textContent).not.toMatch(
      /DUE TODAY|OVERDUE/,
    );
  });
  it("round 2 item 6: a waiting inspector names its person, project and due date", async () => {
    render(<TodayView />);
    await settled();
    const item = gets["/api/desk/needs-you?fresh=1"].items.find(
      (r: any) => r.counted && r.person_name,
    );
    fireEvent.click(row(item.title));
    const inspector = screen.getByTestId("today-inspector");
    expect(inspector).toHaveTextContent(item.person_name);
    expect(inspector).toHaveTextContent(item.projectName);
    expect(within(inspector).getByText("Due", { exact: true })).toBeTruthy();
    expect(
      within(inspector).getByText(
        item.direction === "mine" ? "You owe" : "They owe",
        { exact: true },
      ),
    ).toBeTruthy();
  });
  it("round 2 item 9: the day fills the inspector before a selection", async () => {
    render(<TodayView />);
    await settled();
    view("Brief");
    view("The day");
    expect(screen.getByTestId("today-inspector")).not.toHaveTextContent(
      "Select an item",
    );
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(
      "1:1 with Mira",
    );
  });
  it("round 2 item 11: the installed automation opens before its first result", async () => {
    const tape = PREPARED as unknown as {
      gets: Gets;
      beforePrepared: { gets: Gets };
    };
    replay({ ...tape.gets, ...tape.beforePrepared.gets });
    render(<TodayView />);
    await settled();
    view("Prepared");
    expect(verb("Prepare now")).toBeEnabled();
    expect(verb("Open the automation")).toBeEnabled();
    const open = vi.spyOn(useDesk.getState(), "openWorkbenchWindow");
    fireEvent.click(verb("Open the automation"));
    expect(open).toHaveBeenCalledWith(
      tape.beforePrepared.gets["/api/today"].prepared.automation.id,
    );
  });
  it("reads the canonical first attention rows and removes the rail, headline, cards and row buttons", async () => {
    render(<TodayView />);
    await settled();
    const expected = gets["/api/today"].needs_you.top;
    for (const item of expected) expect(row(item.title)).toBeTruthy();
    expect(screen.getByText("Waits on you")).toBeTruthy();
    expect(screen.getByText("Ahead")).toBeTruthy();
    expect(
      document.querySelector(".today-plate, .surface-rail, .surface-mast"),
    ).toBeNull();
    for (const element of screen.getAllByRole("row"))
      expect(within(element).queryByRole("button")).toBeNull();
    expect(screen.queryByText("Your move")).toBeNull();
    expect(screen.queryByText(/Tuesday morning/)).toBeNull();
    fireEvent.click(row(expected[0].title));
    fireEvent.click(verb("Open"));
    expect(io.chair).toHaveBeenCalledWith("chair:needs");
  });
  it("keeps collection verbs live without a row and selection verbs dead", async () => {
    render(<TodayView />);
    await settled();
    expect(verb("Record now")).toBeEnabled();
    view("Brief");
    expect(verb("Open source")).toBeDisabled();
    fireEvent.click(verb("Record now"));
    expect(io.surface).toHaveBeenCalledWith("record-live", "/live");
  });
  it("View renders the recorded Brief without another gather; selection reads its facts", async () => {
    render(<TodayView />);
    await settled();
    view("Brief");
    const item =
      gets["/api/today"].since_yesterday.sections.decisions?.[0] ||
      gets["/api/today"].since_yesterday.sections.changed[0];
    const name = item.text.includes(": ")
      ? item.text.split(": ").slice(1).join(": ")
      : item.text;
    fireEvent.click(row(name));
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(name);
    expect(
      io.fetch.mock.calls.filter(([path]) => path === "/api/today"),
    ).toHaveLength(1);
    expect(
      io.fetch.mock.calls.some(([path]) =>
        String(path).includes("brief/generate"),
      ),
    ).toBe(false);
  });
  it("Prep opens the person named by the hub from the selected meeting", async () => {
    const opened: unknown[] = [];
    const listener = (event: Event) =>
      opened.push((event as CustomEvent).detail);
    window.addEventListener(PERSON_OPEN_EVENT, listener);
    try {
      render(<TodayView />);
      await settled();
      fireEvent.click(row("1:1 with Mira"));
      fireEvent.click(verb("Prep"));
      const next = gets["/api/today"].day.upcoming.find(
        (event: { title: string }) => event.title === "1:1 with Mira",
      );
      expect(opened).toEqual([
        expect.objectContaining({
          relationshipId: next.person_relationship_id,
          lens: "prep",
        }),
      ]);
    } finally {
      window.removeEventListener(PERSON_OPEN_EVENT, listener);
    }
  });
  it("names a waiting item as Needs you does: the weight prefix is not the name", async () => {
    // The shape of an agent-written title on the owner's desk (invented
    // words). Today kept the prefix in the name and the fitter cut after it,
    // so two rows read only "Must fix…" and "Should fix…".
    const titles = [
      "Must fix: `path/to/file.py::Name` is dead; park it at `parked/path/to/file.py` and add a row",
      "Should fix: path/to/other_module.py:57 imports a name that nothing reads",
    ];
    const answer = structuredClone(gets["/api/today"]);
    answer.needs_you.top = answer.needs_you.top.slice(0, 2).map((item: any, i: number) => ({ ...item, title: titles[i] }));
    replay({ ...gets, "/api/today": answer });
    render(<TodayView />);
    await settled();
    const group = screen.getByRole("rowgroup", { name: "Waits on you" });
    for (const title of titles) {
      const named = needNameOf(title);
      const shown = within(group).getAllByRole("row").find((r) => r.textContent?.includes(named.name));
      expect(shown, named.name).toBeTruthy();
      expect(shown!.textContent).not.toMatch(/(Must|Should) fix:/);
      expect(shown!.textContent).toContain(tierWord(named.tier!));
    }
    // The same reading as a Needs you row: one function, not two parsers.
    expect(needNameOf(titles[0])).toEqual({ name: tierOf(titles[0])!.name, tier: "must" });
  });
  it("Return opens the selected source and arrows move selection", async () => {
    render(<TodayView />);
    await settled();
    const item = gets["/api/today"].needs_you.top[0];
    const selected = row(item.title);
    fireEvent.click(selected);
    fireEvent.keyDown(selected, { key: "Enter" });
    expect(io.chair).toHaveBeenCalledWith("chair:needs");
    fireEvent.keyDown(selected, { key: "ArrowDown" });
    expect(selected).toHaveAttribute("aria-selected", "false");
  });
  it("a failed read keeps the failure and Retry renders the recorded rows", async () => {
    let fail = true;
    io.fetch.mockImplementation(async (path: string) => {
      if (fail && path === "/api/today") throw new Error("Unavailable");
      return recordedGet(gets, path);
    });
    render(<TodayView />);
    await settled();
    expect(screen.getByTestId("today-read-failed")).toHaveTextContent(
      "Could not read Today",
    );
    fail = false;
    fireEvent.click(
      within(screen.getByTestId("today-read-failed")).getByRole("button", {
        name: "Try again",
      }),
    );
    await waitFor(() =>
      expect(screen.queryByTestId("today-read-failed")).toBeNull(),
    );
    expect(row(gets["/api/today"].needs_you.top[0].title)).toBeTruthy();
  });
  it("a failed refresh retains selected work", async () => {
    render(<TodayView />);
    await settled();
    const item = gets["/api/today"].needs_you.top[0];
    fireEvent.click(row(item.title));
    io.fetch.mockImplementation(async (path: string) => {
      if (path === "/api/today") throw new Error("Unavailable");
      return recordedGet(gets, path);
    });
    // Domain frames use the same read; remount is not needed to test retention.
    act(() => io.changed?.());
    await screen.findByTestId("today-read-failed");
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(item.title);
  });
  it("Prepared keeps the recorded work, engine and suggested agenda point", async () => {
    vi.setSystemTime(new Date(PREPARED.recordedAt));
    replay(PREPARED.gets as Gets);
    render(<TodayView />);
    await settled();
    view("Prepared");
    fireEvent.click(row("1:1 with Mira"));
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(
      (PREPARED.gets as Gets)["/api/today"].prepared.prepared.engine,
    );
    const suggestion = screen
      .getAllByRole("row")
      .find((element) => element.textContent?.includes("To add"));
    expect(suggestion).toBeTruthy();
    fireEvent.click(suggestion!);
    expect(verb("Add to the agenda")).toBeEnabled();
  });
  it("adds the recorded suggestion once and keeps the receipt", async () => {
    const tape = PREPARED as unknown as {
      recordedAt: string;
      gets: Gets;
      presses: Gets;
    };
    vi.setSystemTime(new Date(tape.recordedAt));
    io.fetch.mockImplementation(
      async (path: string, init?: { method?: string }) =>
        init?.method
          ? recordedGet(tape.presses, `${init.method} ${path}`)
          : recordedGet(tape.gets, path),
    );
    render(<TodayView />);
    await settled();
    view("Prepared");
    fireEvent.click(
      screen
        .getAllByRole("row")
        .find((row) => row.textContent?.includes("To add"))!,
    );
    fireEvent.click(verb("Add to the agenda"));
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent(
        "On the agenda",
      ),
    );
    expect(verb("Add to the agenda")).toBeDisabled();
    expect(
      io.fetch.mock.calls.filter(([, init]) => init?.method === "POST"),
    ).toHaveLength(2);
  });
  it("agenda failure retains its suggestion and allows retry", async () => {
    vi.setSystemTime(new Date(PREPARED.recordedAt));
    replay(PREPARED.gets as Gets);
    render(<TodayView />);
    await settled();
    view("Prepared");
    const suggestion = screen
      .getAllByRole("row")
      .find((element) => element.textContent?.includes("To add"))!;
    fireEvent.click(suggestion);
    io.fetch.mockImplementation(
      async (path: string, init?: { method?: string }) => {
        if (init?.method) throw new Error("Unavailable");
        return recordedGet(PREPARED.gets as Gets, path);
      },
    );
    fireEvent.click(verb("Add to the agenda"));
    await waitFor(() =>
      expect(screen.getByTestId("today-action-failed")).toHaveTextContent(
        "Not added",
      ),
    );
    expect(verb("Add to the agenda")).toBeEnabled();
    expect(suggestion).toHaveAttribute("aria-selected", "true");
  });
  it("a result that prepared nothing has its recorded reason without a raw id", async () => {
    vi.setSystemTime(new Date(NOTHING.recordedAt));
    replay(NOTHING.gets as Gets);
    render(<TodayView />);
    await settled();
    view("Prepared");
    expect(screen.getByText(/The automation prepared nothing:/)).toBeTruthy();
    expect(screen.queryByText(/c4e978fc/)).toBeNull();
  });
  it("Brief Send opens its preview in the same inspector and Hide returns", async () => {
    render(<TodayView />);
    await settled();
    view("Brief");
    fireEvent.click(verb("Send…"));
    expect(screen.getByTestId("brief-send-wells")).toBeTruthy();
    fireEvent.click(verb("Hide send"));
    expect(screen.queryByTestId("brief-send-wells")).toBeNull();
  });
  it("an open Send keeps its brief identity through a background read", async () => {
    render(<TodayView />);
    await settled();
    view("Brief");
    fireEvent.click(verb("Send…"));
    const id = gets["/api/today"].since_yesterday.id;
    expect(screen.getByTestId("brief-send-wells")).toHaveAttribute(
      "data-brief-id",
      id,
    );
    replay(PREPARED.gets as Gets);
    act(() => io.changed?.());
    await waitFor(() =>
      expect(
        io.fetch.mock.calls.filter(([path]) => path === "/api/today"),
      ).toHaveLength(2),
    );
    expect(screen.getByTestId("brief-send-wells")).toHaveAttribute(
      "data-brief-id",
      id,
    );
    fireEvent.click(verb("Hide send"));
    fireEvent.click(verb("Send…"));
    expect(screen.getByTestId("brief-send-wells")).toHaveAttribute(
      "data-brief-id",
      (PREPARED.gets as Gets)["/api/today"].since_yesterday.id,
    );
  });
  it("Activity shows Programs since the last visit", async () => {
    replay({ ...gets, ...ACTIVITY });
    render(<TodayView />);
    await settled();
    view("Activity");
    const read = ACTIVITY["/api/today/since-morning"];
    const item = row(read.since_last_here.lines[0].title);
    fireEvent.click(item);
    expect(item).toHaveTextContent(read.since_last_here.lines[0].line);
    expect(screen.getByTestId("today-inspector")).not.toHaveTextContent(read.since_last_here.lines[0].line);
  });
  it("an activity failure stays named and Retry renders its recorded work", async () => {
    let fail = true;
    io.fetch.mockImplementation(async (path: string) => {
      if (fail && path === "/api/today/since-morning")
        throw new Error("Unavailable");
      return recordedGet({ ...gets, ...ACTIVITY }, path);
    });
    render(<TodayView />);
    await settled();
    view("Activity");
    expect(screen.getByTestId("today-done-failed")).toHaveTextContent(
      "Could not read today's work",
    );
    fail = false;
    fireEvent.click(
      within(screen.getByTestId("today-done-failed")).getByRole("button", {
        name: "Try again",
      }),
    );
    await waitFor(() =>
      expect(screen.queryByTestId("today-done-failed")).toBeNull(),
    );
  });
  it("an empty day offers the calendar and Record now", async () => {
    vi.setSystemTime(new Date(EMPTY.recordedAt));
    replay(EMPTY.gets as Gets);
    render(<TodayView />);
    await settled();
    expect(screen.getByText("No meetings and no calendar yet")).toBeTruthy();
    fireEvent.click(verb("Connect calendar"));
    expect(io.surface).toHaveBeenCalledWith(
      "configure-settings",
      "/settings",
      "integration:calendar",
    );
  });
  it("arms the selected event through the recorded HTTP answer", async () => {
    const tape = TODAY as unknown as {
      gets: Gets;
      presses: Gets;
      afterArm: { gets: Gets };
    };
    let armed = false;
    io.fetch.mockImplementation(
      async (path: string, init?: { method?: string }) => {
        if (path === "/api/scheduled-recordings" && init?.method === "POST") {
          armed = true;
          return recordedGet(tape.presses, `POST ${path}`);
        }
        return recordedGet(
          armed ? { ...tape.gets, ...tape.afterArm.gets } : tape.gets,
          path,
        );
      },
    );
    render(<TodayView />);
    await settled();
    fireEvent.click(row("1:1 with Mira"));
    fireEvent.click(verb("Record when it starts"));
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent(
        "Recording armed",
      ),
    );
    expect(screen.getByTestId("today-inspector")).toHaveTextContent("Armed");
    expect(verb("Record when it starts")).toBeDisabled();
    expect(io.fetch).toHaveBeenCalledWith("/api/scheduled-recordings", {
      method: "POST",
      json: {
        calendar_event_id: tape.gets["/api/today"].day.upcoming.find(
          (event: { title: string }) => event.title === "1:1 with Mira",
        ).id,
      },
    });
  });
  it("retains the target after an arm failure", async () => {
    vi.spyOn(useDesk.getState(), "armEventRecording").mockResolvedValue(false);
    render(<TodayView />);
    await settled();
    fireEvent.click(row("1:1 with Mira"));
    fireEvent.click(verb("Record when it starts"));
    await waitFor(() =>
      expect(screen.getByTestId("today-action-failed")).toHaveTextContent(
        "Could not arm recording",
      ),
    );
    expect(verb("Record when it starts")).toBeEnabled();
  });
  it("queues the selected summary with the route that was shown", async () => {
    vi.setSystemTime(new Date(SUMMARY._now));
    const today = structuredClone(gets["/api/today"]);
    // Both sections are real producer recordings; only the transport is doubled.
    today.day.meetings = SUMMARY["/api/meetings?limit=100"].meetings;
    const path = "/api/meetings/m-off-words/intelligence/run";
    io.fetch.mockImplementation(
      async (url: string, init?: { method?: string }) =>
        url === path && init?.method === "POST"
          ? structuredClone(
              SUMMARY["POST /api/meetings/m-off-words/intelligence/run"],
            )
          : recordedGet({ ...gets, "/api/today": today }, url),
    );
    render(<TodayView />);
    await settled();
    fireEvent.click(row("Census standup"));
    fireEvent.click(verb("Make the summary"));
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent("Queued at"),
    );
    expect(io.fetch).toHaveBeenCalledWith(path, {
      method: "POST",
      json: {
        expected_selection_hash:
          SUMMARY["POST /api/meetings/m-off-words/intelligence/run"]
            .planned_route.selection_hash,
      },
    });
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(
      "Census standup",
    );
  });
  it("a summary refusal keeps the meeting and its retry verb", async () => {
    vi.setSystemTime(new Date(SUMMARY._now));
    const today = structuredClone(gets["/api/today"]);
    today.day.meetings = SUMMARY["/api/meetings?limit=100"].meetings;
    io.fetch.mockImplementation(
      async (url: string, init?: { method?: string }) => {
        if (init?.method === "POST") throw new Error("Unavailable");
        return recordedGet({ ...gets, "/api/today": today }, url);
      },
    );
    render(<TodayView />);
    await settled();
    fireEvent.click(row("Census standup"));
    fireEvent.click(verb("Make the summary"));
    await waitFor(() =>
      expect(screen.getByTestId("today-summary-failed")).toHaveTextContent(
        "Summary did not start",
      ),
    );
    expect(verb("Make the summary")).toBeEnabled();
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(
      "Census standup",
    );
  });
  it("a failed summary with no route keeps its failure and opens Choose engine", async () => {
    const today = structuredClone(gets["/api/today"]);
    today.day.meetings = UNAVAILABLE["/api/meetings?limit=100"].meetings;
    vi.setSystemTime(new Date(today.day.meetings[0].started_at));
    replay({ ...gets, "/api/today": today });
    render(<TodayView />);
    await settled();
    expect(row("Vendor call, Woodward")).toHaveTextContent("Failed");
    fireEvent.click(row("Vendor call, Woodward"));
    expect(verb("Make the summary")).toBeDisabled();
    fireEvent.click(verb("Choose engine"));
    expect(io.surface).toHaveBeenCalledWith(
      "open-concierge",
      "/models",
      "meetings",
    );
  });
  it("keeps This week in the selection list", async () => {
    render(<TodayView />);
    await settled();
    fireEvent.click(verb("This week"));
    expect(verb("Today only")).toBeEnabled();
    const expected = gets["/api/today"].day.week.days.find(
      (day: { count: number }) => day.count > 0,
    );
    expect(screen.getByRole("rowgroup",{name:`Ahead · ${new Intl.DateTimeFormat(undefined,{weekday:"long"}).format(new Date(expected.date+"T12:00:00"))}`})).toBeTruthy();
    expect(row(`${expected.dow} · ${expected.count}`)).toBeUndefined();
    fireEvent.click(verb("Today only"));
    expect(verb("This week")).toBeEnabled();
  });
  it("Prepare now uses the recorded run answer and keeps its start receipt", async () => {
    const tape = PREPARED as unknown as {
      recordedAt: string;
      gets: Gets;
      presses: Gets;
    };
    vi.setSystemTime(new Date(tape.recordedAt));
    io.fetch.mockImplementation(
      async (path: string, init?: { method?: string }) =>
        init?.method
          ? recordedGet(tape.presses, `${init.method} ${path}`)
          : recordedGet(tape.gets, path),
    );
    render(<TodayView />);
    await settled();
    view("Prepared");
    fireEvent.click(verb("Prepare now"));
    await waitFor(() =>
      expect(screen.getByTestId("today-status")).toHaveTextContent(
        "Preparation started",
      ),
    );
    expect(io.fetch).toHaveBeenCalledWith(
      `/api/workbenches/${tape.gets["/api/today"].prepared.automation.id}/run`,
      { method: "POST", json: {} },
    );
  });
  it("Brief opens the source named by its recorded row", async () => {
    render(<TodayView />);
    await settled();
    view("Brief");
    const item = gets["/api/today"].since_yesterday.sections.changed.find(
      (item: { source_ref: string }) => item.source_ref.startsWith("meeting:"),
    );
    const name = item.text.slice(item.text.indexOf(": ") + 2);
    fireEvent.click(row(name));
    fireEvent.click(verb("Open source"));
    expect(io.surface).toHaveBeenCalledWith(
      "review-meetings",
      "/history",
      item.source_ref,
    );
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(name);
    expect(screen.queryByRole("button", { name: "Acknowledge" })).toBeNull();
  });
  it("Brief selects the desk's recorded pages and reads their sentences", async () => {
    replay({ ...gets, "/api/memory/pages?scope=desk": PAGES.pages });
    render(<TodayView />);
    await settled();
    view("Brief");
    fireEvent.click(await screen.findByRole("row", { name: /What I owe/ }));
    expect(screen.getByTestId("today-inspector")).toHaveTextContent(
      PAGES.pages.pages[0].sentences[0].text,
    );
    expect(screen.getByText("Desk pages")).toBeTruthy();
    expect(row("Confirm the vendor freeze dates").querySelector(".object-list-detail")).toHaveTextContent("Commitment due Oct 17");
    fireEvent.keyDown(screen.getByRole("row", { name: /What I owe/ }), { key: "Enter" });
    fireEvent.click(
      within(screen.getByRole("menu")).getByText("Meeting 09-19 · 10:00", {
        exact: true,
      }),
    );
    expect(io.surface).toHaveBeenCalledWith(
      "review-meetings",
      "/history",
      "meeting:m-mira-1on1",
    );
  });
  it("has a walk of the current parts", async () => {
    render(<TodayView />);
    await settled();
    for (const step of appWalk("open-intelligence")?.steps ?? [])
      expect(step.highlight?.target).not.toContain("rail");
  });
});

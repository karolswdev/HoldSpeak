/* The Programs app (T2), the Programs window (the language, 2026-11-08:
 * the window is the Program): the rail, the pick, the keys, the night, the
 * status bar, the families.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  historyFixture, historyListFixture, familyFixture,
  mocks, ProgramsCore, ProgramBody, stationsOf, DESK_APPLICATIONS, emit, list, running, done, yourTurn, clone,
  calls, hub, status, stepRow, openSteps, type Program, type ProgramList,
  type ProgramStep, board,
} from "./programs.test-setup";
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

describe("the manifest", () => {
  it("Programs is an application beside Agents, on ⌃7, wearing the program sprite", () => {
    const app = DESK_APPLICATIONS.find((row) => row.windowId === "surface-programs")!;
    expect(app).toMatchObject({ action: "open-programs", label: "Programs", shortcut: "⌃7", go: { group: "daily" } });
    expect(app.surface?.sprite).toBe("program");
  });
});

/** The rail reads "done this week" against the clock: the recorded list's day. */
const onRecordedDay = () => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date("2026-11-03T12:00:00Z"));
};
const tiles = () => screen.getAllByTestId("programs-rail-tile");
const tileOf = (id: string) => tiles().find((tile) => tile.getAttribute("data-program") === id)!;
/** The recorded detail, as the Program the rail picks. */
const detailOf = (id: string, title: string): Program => ({ ...clone(yourTurn), id, title });

describe("the Programs window (the language, 2026-11-08: the window is the Program)", () => {
  afterEach(() => vi.useRealTimers());

  it("the rail: New program, then the active Programs waiting first, a rule, the ones done this week; each tile says its name and state", async () => {
    onRecordedDay();
    const first = list.programs[0];
    hub({ "GET /api/programs": list, [`GET /api/programs/${first.id}`]: detailOf(first.id, first.title) });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-rail-tile");
    const rail = screen.getByTestId("programs-rail");
    expect(rail.firstElementChild?.contains(screen.getByTestId("programs-new"))).toBe(true);
    expect(screen.getByTestId("programs-new").textContent).toBe("New program");
    // Waiting, then drafting, then parked (a Program parked as a proof is done with: no tile); then done.
    const active = list.programs.filter((row) => row.state !== "done" && !row.parked_as);
    const order = ["waiting", "failed", "running", "drafting", "parked"];
    const expected = [...active].sort((a, b) => order.indexOf(a.state) - order.indexOf(b.state) || String(b.updated_at).localeCompare(String(a.updated_at)))
      .map((row) => row.id).concat(list.programs.filter((row) => row.state === "done").map((row) => row.id));
    expect(tiles().map((tile) => tile.getAttribute("data-program"))).toEqual(expected);
    expect(within(rail).getByRole("group", { name: "In progress" })).toBeTruthy();
    expect(within(rail).getByRole("group", { name: "Done this week" })).toBeTruthy();
    // Hover and focus say the name and the state.
    const waiting = tileOf(first.id);
    expect(waiting.getAttribute("aria-label")).toBe(`${first.title}, waits on you`);
    expect(waiting.getAttribute("title")).toBe(`${first.title}, waits on you`);
    // A draft is a dashed tile with no sprite and no dot; the others wear the program sprite and a state dot.
    const draft = tileOf(list.programs.find((row) => row.state === "drafting")!.id);
    expect(draft.textContent).toContain("drafting");
    expect(waiting.querySelector("img")!.getAttribute("src")).toContain("program");
    expect(waiting.querySelector("[data-state]")!.getAttribute("data-state")).toBe("waiting");
    // The first waiting Program is picked: ringed, and the pane is that Program.
    expect(waiting.getAttribute("aria-current")).toBe("true");
    expect(await screen.findByTestId("programs-mast")).toBeTruthy();
    expect(screen.getByTestId("programs-pane").getAttribute("data-program")).toBe(first.id);
    // The status bar: the counts that are not zero, in mono.
    expect(status().textContent).toContain(`${list.programs.length} programs`);
    expect(status().textContent).toContain("2 wait on you");
    expect(status().textContent).not.toMatch(/\b0 /);
    // No night on this hub: no night tile, no tonight words.
    expect(screen.queryByTestId("programs-rail-night")).toBeNull();
    expect(status().textContent).not.toContain("tonight");
  });

  it("a tile press picks its Program; ↑ and ↓ move along the tiles and Enter picks", async () => {
    onRecordedDay();
    const [first, second] = list.programs;
    hub({
      "GET /api/programs": list,
      [`GET /api/programs/${first.id}`]: detailOf(first.id, first.title),
      [`GET /api/programs/${second.id}`]: detailOf(second.id, second.title),
    });
    render(<ProgramsCore />);
    await screen.findByTestId("programs-mast");
    fireEvent.click(tileOf(second.id));
    await waitFor(() => expect(screen.getByTestId("programs-pane").getAttribute("data-program")).toBe(second.id));
    expect(within(await screen.findByTestId("programs-mast")).getByRole("heading").textContent).toBe(second.title);
    expect(tileOf(second.id).getAttribute("aria-current")).toBe("true");
    // Keys: the focus moves, the pick waits for Enter (the Button's own press).
    tileOf(second.id).focus();
    fireEvent.keyDown(tileOf(second.id), { key: "ArrowUp" });
    expect(document.activeElement).toBe(tileOf(first.id));
    expect(screen.getByTestId("programs-pane").getAttribute("data-program")).toBe(second.id);
    fireEvent.keyDown(tileOf(first.id), { key: "ArrowDown" });
    expect(document.activeElement).toBe(tileOf(second.id));
  });

  it("the night tile and the status bar's tonight words, when the hub names a night", async () => {
    onRecordedDay();
    const first = list.programs[0];
    const night = { ...list, night: { program_id: first.id, start: "23:00", queued: 3 } } as ProgramList;
    hub({ "GET /api/programs": night, [`GET /api/programs/${first.id}`]: detailOf(first.id, first.title) });
    render(<ProgramsCore />);
    const tile = await screen.findByTestId("programs-rail-night");
    expect(tile.textContent).toContain("Tonight 23:00");
    expect(tile.textContent).toContain("3");
    expect(tile.getAttribute("aria-label")).toBe("Tonight 23:00, 3 queued");
    expect(status().textContent).toContain("tonight 23:00");
    expect(status().textContent).toContain("3 queued");
    // "tonight 23:00 · 3 queued": the two words side by side at the bar's end.
    const words = [...status().querySelectorAll(".kit-statusbar-item")].map((item) => item.textContent);
    expect(words.slice(-2)).toEqual(["tonight 23:00", "3 queued"]);
  });

  it("the night tile opens the night Program in the pane; a night with no Program to open draws no tile", async () => {
    onRecordedDay();
    const first = list.programs[0];
    const other = list.programs.find((row) => row.id !== first.id && row.state !== "drafting")!;
    const night = { ...list, night: { program_id: other.id, start: "23:00", queued: 3 } } as ProgramList;
    hub({ "GET /api/programs": night, [`GET /api/programs/${first.id}`]: detailOf(first.id, first.title),
      [`GET /api/programs/${other.id}`]: detailOf(other.id, other.title) });
    render(<ProgramsCore />);
    const tile = await screen.findByTestId("programs-rail-night");
    await waitFor(() => expect(screen.getByTestId("programs-pane").getAttribute("data-program")).toBe(first.id));
    fireEvent.click(tile);
    await waitFor(() => expect(screen.getByTestId("programs-pane").getAttribute("data-program")).toBe(other.id));
    cleanup();
    hub({ "GET /api/programs": { ...list, night: { program_id: null, start: "23:00", queued: 3 } } as ProgramList,
      [`GET /api/programs/${first.id}`]: detailOf(first.id, first.title) });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-rail-tile");
    expect(screen.queryByTestId("programs-rail-night")).toBeNull();
  });

  it("a hub without Programs draws the empty object with one Button, and no count of zero", async () => {
    hub({});
    render(<ProgramsCore />);
    expect(await screen.findByText("No program yet")).toBeTruthy();
    expect(screen.getByText("A program is a goal cut into steps. An agent does each step.")).toBeTruthy();
    expect(within(screen.getByTestId("programs-pane")).getAllByRole("button").map((node) => node.textContent)).toEqual(["New program"]);
    expect(screen.queryByTestId("programs-rail-tile")).toBeNull();
    expect(screen.queryByTestId("programs-status")).toBeNull();
  });

  it("re-reads on a program_changed frame, never on a windows-only desk frame", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-rail-tile");
    const reads = () => calls.filter((call) => call === "GET /api/programs").length;
    const before = reads();
    emit("desk_changed", { kind: "windows", id: "surface-programs", op: "update" });
    expect(reads()).toBe(before);
    emit("program_changed", { program_id: running.id, state: "running", your_turn: 0 });
    await waitFor(() => expect(reads()).toBe(before + 1));
    emit("desk_changed", { kind: "program", id: running.id, op: "step" });
    await waitFor(() => expect(reads()).toBe(before + 2));
  });
});

describe("PG17: a Program made from PRs that merged already (recorded through the real routes)", () => {
  const history = historyFixture as unknown as Program;
  const historyList = historyListFixture as unknown as ProgramList;

  it("the Programs window picks it: a done tile, and the plate says Done with Merged n PRs and the dates", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(Date.parse(historyList.programs[0].updated_at) + 60_000));
    hub({ "GET /api/programs": historyList, [`GET /api/programs/${history.id}`]: history });
    render(<ProgramsCore />);
    const [tile] = await screen.findAllByTestId("programs-rail-tile");
    expect(tile.getAttribute("data-state")).toBe("done");
    expect(history.history!.words).toMatch(/^Merged 3 PRs · \d+ Oct/);
    const plate = await screen.findByTestId("programs-plate");
    expect(within(plate).getByTestId("programs-plate-head").textContent).toBe(`Done · ${history.history!.words}`);
    expect(screen.getAllByTestId("programs-spine-step")).toHaveLength(3);
    vi.useRealTimers();
  });

  it("the board: every station lit, the PR number and the merge time on each row, no agent; the fold says Imported from PR #n", async () => {
    hub({ [`GET /api/programs/${history.id}`]: history });
    render(<ProgramBody programId={history.id} />);
    await screen.findByTestId("programs-mast");
    openSteps();
    await board();
    const rows = screen.getAllByTestId("programs-step");
    expect(rows).toHaveLength(3);
    expect(rows.every((row) => row.hasAttribute("data-history"))).toBe(true);
    expect(screen.getAllByTestId("programs-step-pr").map((cell) => cell.textContent)).toEqual(["PR #1584", "PR #1585", "PR #1598"]);
    for (const step of history.steps) {
      const merge = stationsOf(step as ProgramStep).at(-1)!;
      expect(merge).toMatchObject({ key: "merge", tone: "ok", sub: `#${step.pr!.number}` });
    }
    expect(within(stepRow(1)).getByTestId("programs-step-word").textContent).toBe("Done");
    expect(stepRow(1).querySelector(".pg-step-when")!.textContent).toMatch(/^28 Oct \d\d:\d\d$/);
    expect(stepRow(1).querySelector(".pg-step-agent")!.textContent).toBe("");
    expect(screen.queryByTestId("programs-step-open")).toBeNull();
    expect(status().textContent).toContain(`Done · ${history.history!.words}`);
    // No fold until he picks a step; the picked step's fold names its PR.
    expect(screen.queryByTestId("programs-history-brief")).toBeNull();
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-select"));
    const brief = await screen.findByTestId("programs-history-brief");
    expect(brief.textContent).toContain("Imported from PR #1584");
    expect(brief.textContent).toMatch(/merged 28 Oct \d\d:\d\d/);
    expect(screen.queryByTestId("programs-gate-verdict")).toBeNull();
  });
});

describe("PG-IMPORT IMP7: the forest (recorded: scripts/record_program_fixtures.py, family.row.json)", () => {
  const family = familyFixture as unknown as { program: Program; child: Program; list: ProgramList };

  it("the window lists the Programs it made as plain rows; a press opens that Program", async () => {
    const program = family.program;
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    fireEvent.click(await screen.findByTestId("program-earlier"));
    const section = await screen.findByTestId("programs-family");
    expect(within(section).queryByTestId("programs-family-parent")).toBeNull();
    const rows = within(within(section).getByTestId("programs-family-children")).getAllByTestId("programs-family-row");
    expect(rows.map((row) => row.getAttribute("data-program"))).toEqual(program.family!.children.map((row) => row.id));
    const done = program.family!.children.find((row) => row.ending === "finished")!;
    const doneRow = rows.find((row) => row.getAttribute("data-program") === done.id)!;
    expect(doneRow.textContent).toContain(`${done.name}${done.state_word} · finished${done.line}`);
    expect(doneRow.querySelector(".kit-chip, .kit-badge")).toBeNull();
    fireEvent.click(within(doneRow).getByTestId("programs-family-open"));
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${done.id}`);
  });

  it("a child names the Program it came from; a Program with no family draws nothing", async () => {
    hub({ [`GET /api/programs/${family.child.id}`]: family.child });
    render(<ProgramBody programId={family.child.id} />);
    fireEvent.click(await screen.findByTestId("program-earlier"));
    const parent = await screen.findByTestId("programs-family-parent");
    expect(parent.textContent).toContain(family.program.title);
    fireEvent.click(within(parent).getByTestId("programs-family-open"));
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${family.program.id}`);
    cleanup();
    hub({ [`GET /api/programs/${done.id}`]: done });
    render(<ProgramBody programId={done.id} />);
    fireEvent.click(await screen.findByTestId("program-earlier"));
    await board();
    expect(screen.queryByTestId("programs-family")).toBeNull();
  });

  it("on the rail each Program of a family is its own tile", async () => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(new Date(Math.max(...family.list.programs.map((row) => Date.parse(row.updated_at))) + 60_000));
    hub({ "GET /api/programs": family.list });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-rail-tile");
    const shown = tiles().map((tile) => tile.getAttribute("data-program")).sort();
    expect(shown).toEqual(family.list.programs.filter((row) => !row.parked_as).map((row) => row.id).sort());
    vi.useRealTimers();
  });
});


describe("an automation's runs (2026-11-08: each run is a Program of one prompt step)", () => {
  it("the rail keeps one tile per automation, its latest run", async () => {
    const { railGroups } = await import("../ProgramRail");
    const recorded = clone(list).programs;
    const [first, second, ...rest] = recorded;
    const older = { ...first, automation_id: "workbench-morning-prep", created_at: "2026-11-02T07:30:00Z", state: "done" as const, updated_at: "2026-11-02T07:31:00Z" };
    const newer = { ...second, automation_id: "workbench-morning-prep", created_at: "2026-11-03T07:30:00Z", state: "done" as const, updated_at: "2026-11-03T07:31:00Z" };
    const groups = railGroups([older, newer, ...rest], Date.parse("2026-11-03T12:00:00Z"));
    const ids = [...groups.active, ...groups.done].map((row) => row.id);
    expect(ids).toContain(newer.id);
    expect(ids).not.toContain(older.id);
  });
});

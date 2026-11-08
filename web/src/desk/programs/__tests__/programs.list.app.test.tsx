/* The Programs app (T2), the Programs list window: the rows, the bands,
 * Find, Project, Person, Group, the status bar, the families and the chains.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  historyFixture, historyListFixture, filteredListFixture, familyFixture, chainedListFixture,
  mocks, ProgramsCore, ProgramBody, stationsOf, DESK_APPLICATIONS, emit, list, running, done,
  calls, hub, status, stepRow, menuWords, menuItem, type Program, type ProgramList,
  type ProgramStep,
} from "./programs.test-setup";
import { describe, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

describe("the manifest", () => {
  it("Programs is an application beside Agents, on ⌃7, wearing the program sprite", () => {
    const app = DESK_APPLICATIONS.find((row) => row.windowId === "surface-programs")!;
    expect(app).toMatchObject({ action: "open-programs", label: "Programs", shortcut: "⌃7", go: { group: "daily" } });
    expect(app.surface?.sprite).toBe("program");
  });
});

describe("the Programs window", () => {
  it("lists the recorded Programs waiting first, in bands, with the counts that are not zero", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    const bands = await screen.findAllByTestId("programs-band");
    expect(bands.map((band) => within(band).getByRole("heading").textContent)).toEqual(["Your turn", "Drafting", "Done", "Parked"]);
    expect(within(bands[0]).getAllByTestId("programs-row").map((row) => row.getAttribute("data-program")))
      .toEqual(list.programs.filter((row) => row.state === "waiting").map((row) => row.id));
    // PG-WINDOW List: each row reads like a line from a chief of staff (the hub's words), with its mini track.
    for (const row of list.programs) {
      const node = screen.getAllByTestId("programs-row").find((candidate) => candidate.getAttribute("data-program") === row.id)!;
      expect(within(node).getByTestId("programs-row-state").textContent).toBe(row.line);
      expect(node.querySelectorAll(".pg-station")).toHaveLength(row.track!.length);
    }
    expect(list.programs.find((row) => row.state === "waiting")!.line).toMatch(/^Step \d+ of \d+ waits on you since \d\d:\d\d$/);
    const doneRow = within(bands[2]).getByTestId("programs-row");
    expect(doneRow.textContent).toMatch(/Done, 1 PR, \d+ \w{3}/);
    // No column heads.
    expect(document.querySelector(".pg-list-head")).toBeNull();
    // A finished program's row keeps its green (Done is a fact).
    expect(doneRow.hasAttribute("data-all-done")).toBe(true);
    // #1707: the programs he parked as proofs fold under one line (Show · Hide); the rest stay rows.
    const proofs = list.programs.filter((row) => row.parked_as === "proof");
    const fold = screen.getByTestId("programs-parked-fold");
    expect(fold.querySelector("summary")!.textContent).toContain(`${proofs.length} parked proofs`);
    expect(within(fold).getAllByTestId("programs-row").map((row) => row.getAttribute("data-program")).sort()).toEqual(proofs.map((row) => row.id).sort());
    expect(status().textContent).toContain("Your turn");
    expect(status().textContent).toContain("2 wait on you");
    expect(status().textContent).not.toMatch(/\b0 /);
    // A row press opens the Program window.
    fireEvent.click(within(bands[0]).getAllByTestId("programs-row-open")[0]);
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${list.programs[0].id}`);
  });

  it("a hub without Programs draws the empty object with one Button, and no count of zero", async () => {
    hub({});
    render(<ProgramsCore />);
    expect(await screen.findByText("No program yet")).toBeTruthy();
    expect(screen.getByText("A program is a goal cut into steps. An agent does each step.")).toBeTruthy();
    expect(screen.queryByTestId("programs-status")).toBeNull();
  });

  it("re-reads on a program_changed frame, never on a windows-only desk frame", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
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

  it("the Programs window lists it under Done with Merged n PRs and the dates", async () => {
    hub({ "GET /api/programs": historyList });
    render(<ProgramsCore />);
    const bands = await screen.findAllByTestId("programs-band");
    expect(bands.map((band) => within(band).getByRole("heading").textContent)).toEqual(["Done"]);
    const row = within(bands[0]).getByTestId("programs-row");
    expect(within(row).getByTestId("programs-row-state").textContent).toMatch(/^Done, merged 3 PRs, \d+ Oct/);
    expect(history.history!.words).toMatch(/^Merged 3 PRs · \d+ Oct/);
    expect(row.querySelectorAll(".pg-station")).toHaveLength(3);
    expect(row.textContent).not.toContain("Done in");
  });

  it("the board: every station lit, the PR number and the merge time on each row, no agent; the fold says Imported from PR #n", async () => {
    hub({ [`GET /api/programs/${history.id}`]: history });
    render(<ProgramBody programId={history.id} />);
    await screen.findByTestId("programs-board");
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

describe("REQ9: the Programs list (Find, Project ▾, Person ▾, Group, Met)", () => {
  it("Find: a typed word narrows the rows; the status bar says how many of all and the word, and no count of zero", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    expect(screen.getAllByTestId("programs-row")).toHaveLength(list.programs.length);
    fireEvent.change(within(screen.getByTestId("programs-find")).getByRole("searchbox", { name: "Find a program" }), { target: { value: "stalling" } });
    const rows = screen.getAllByTestId("programs-row");
    expect(rows.map((row) => row.textContent)).toEqual([expect.stringContaining("The hub stops stalling")]);
    expect(screen.getByTestId("programs-status-shown").textContent).toBe(`1 of ${list.programs.length} programs`);
    expect(status().textContent).toContain("“stalling”");
    expect(status().textContent).toContain("1 waits on you");
    expect(status().textContent).not.toMatch(/\b0 /);
    // The words match the step titles too (search_words), and no row: one line, one verb.
    fireEvent.change(screen.getByRole("searchbox", { name: "Find a program" }), { target: { value: "nothing-like-this" } });
    expect(screen.getByText("No program matches")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Clear the filter" }));
    expect(screen.getAllByTestId("programs-row")).toHaveLength(list.programs.length);
  });

  it("Project ▾ lists only the projects that have a program (and No project); Person ▾ narrows; Group: Project bands by name, No project last", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-project"));
    await screen.findAllByRole("menuitemradio");
    expect(menuWords()).toEqual(["Any project", "HoldSpeak", "No project"]);
    fireEvent.click(menuItem("HoldSpeak"));
    expect(screen.getByTestId("programs-project").textContent).toContain("Project: HoldSpeak");
    const shown = list.programs.filter((row) => row.project?.id === "proj-holdspeak");
    expect(screen.getAllByTestId("programs-row").map((row) => row.getAttribute("data-program")).sort()).toEqual(shown.map((row) => row.id).sort());
    expect(status().textContent).toContain(`${shown.length} of ${list.programs.length} programs`);
    expect(status().textContent).toContain("HoldSpeak");
    // Person ▾: only Alice has a program.
    fireEvent.click(screen.getByTestId("programs-person"));
    await screen.findAllByRole("menuitemradio");
    expect(menuWords()).toEqual(["Anyone", "Alice"]);
    fireEvent.click(menuItem("Alice"));
    expect(screen.getAllByTestId("programs-row").map((row) => row.textContent)).toEqual([expect.stringContaining("The hub stops stalling")]);
    expect(status().textContent).toContain("Alice");
    // Clear both; group by project.
    fireEvent.click(screen.getByTestId("programs-project"));
    await screen.findAllByRole("menuitem");
    fireEvent.click(menuItem("Any project"));
    fireEvent.click(screen.getByTestId("programs-person"));
    await screen.findAllByRole("menuitem");
    fireEvent.click(menuItem("Anyone"));
    fireEvent.click(screen.getByTestId("programs-group"));
    await screen.findAllByRole("menuitem");
    fireEvent.click(menuItem("Project"));
    const bands = screen.getAllByTestId("programs-band");
    expect(bands.map((band) => within(band).getByRole("heading").textContent)).toEqual([`HoldSpeak · ${shown.length}`,
      `No project · ${list.programs.filter((row) => !(row.project?.id ?? row.project_id)).length}`]);
    // Inside a band: the worst state first (Your turn before Drafting before Done).
    const states = within(bands[0]).getAllByTestId("programs-row").map((row) => row.getAttribute("data-state"));
    expect(states).toEqual([...states].sort((a, b) => ["waiting", "running", "drafting", "done", "parked"].indexOf(a!) - ["waiting", "running", "drafting", "done", "parked"].indexOf(b!)));
    expect(screen.getByTestId("programs-group").textContent).toContain("Group: Project");
  });

  it("the Met column: “4 of 6 met”; “4 requirements” while none is judged (never “0 of 4 met”); nothing when there is none; an ember dot and the waived count in the title", async () => {
    hub({ "GET /api/programs": list });
    const { unmount } = render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    const met = (title: string) => within(screen.getAllByTestId("programs-row").find((row) => row.textContent?.includes(title))!).getByTestId("programs-row-met");
    expect(met("The words wave").textContent).toBe("4 of 6 met");
    expect(met("Calls on the home box").textContent).toBe("4 requirements");
    expect(met("Wave 6 of the atlas").textContent).toBe("");
    expect(screen.getByTestId("programs-list").textContent).not.toMatch(/\b0 of \d+ met/);
    unmount();
    const filtered = filteredListFixture as unknown as ProgramList;
    hub({ "GET /api/programs": filtered });
    render(<ProgramsCore />);
    const cell = await screen.findByTestId("programs-row-met");
    const counted = filtered.programs[0].requirements_met!;
    expect(cell.textContent).toBe(`${counted.met} of ${counted.total} met`);
    expect(cell.querySelector(".kit-dot")!.getAttribute("data-tone")).toBe("ask");
    expect(cell.getAttribute("title")).toBe(`${counted.waived} waived`);
  });
});

describe("PG-IMPORT IMP7: the forest (recorded: scripts/record_program_fixtures.py, family.row.json)", () => {
  const family = familyFixture as unknown as { program: Program; child: Program; list: ProgramList };

  it("the window lists the Programs it made as plain rows; a press opens that Program", async () => {
    const program = family.program;
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
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
    const parent = await screen.findByTestId("programs-family-parent");
    expect(parent.textContent).toContain(family.program.title);
    fireEvent.click(within(parent).getByTestId("programs-family-open"));
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${family.program.id}`);
    cleanup();
    hub({ [`GET /api/programs/${done.id}`]: done });
    render(<ProgramBody programId={done.id} />);
    await screen.findByTestId("programs-board");
    expect(screen.queryByTestId("programs-family")).toBeNull();
  });

  it("on the list the family folds under its first Program, whose line carries the family's worst state", async () => {
    hub({ "GET /api/programs": family.list });
    render(<ProgramsCore />);
    const fold = await screen.findByTestId("programs-family-fold");
    const parent = family.list.programs.find((row) => row.kin)!;
    expect(fold.getAttribute("data-parent")).toBe(parent.id);
    expect(fold.textContent).toContain("2 programs it made");
    const kids = within(fold).getAllByTestId("programs-row").map((row) => row.getAttribute("data-program"));
    expect(kids.sort()).toEqual(family.list.programs.filter((row) => row.parent_id === parent.id).map((row) => row.id).sort());
    // Each child is drawn once: under its parent, never also in its own band.
    expect(screen.getAllByTestId("programs-row").filter((row) => kids.includes(row.getAttribute("data-program")))).toHaveLength(kids.length);
    const parentRow = screen.getAllByTestId("programs-row").find((row) => row.getAttribute("data-program") === parent.id)!;
    expect(within(parentRow).getByTestId("programs-row-kin").textContent).toBe(`· its programs: ${parent.kin!.worst_word}`);
  });
});

describe("a split chain in the list", () => {
  it("a chained Program's row reads Starts after <name> while it waits", async () => {
    const chained = chainedListFixture as unknown as ProgramList;
    hub({ "GET /api/programs": chained });
    render(<ProgramsCore />);
    await screen.findByTestId("programs-list");
    const waiting = chained.programs.filter((row) => (row.line ?? "").startsWith("Starts after "));
    expect(waiting).toHaveLength(2);
    for (const row of waiting) {
      const node = screen.getAllByTestId("programs-row").find((el) => el.getAttribute("data-program") === row.id)!;
      expect(within(node).getByTestId("programs-row-state").textContent).toContain(row.line!);
    }
  });
});

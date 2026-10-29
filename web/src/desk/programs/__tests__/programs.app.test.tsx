/* The Programs app (T2; PROGRAMS-DESIGN-2026-10-28 §4, §6, §9, §9b; canvas
 * docs/internal/betterment/programs/canvases/programs-2026-10-28.html,
 * direction C "the ledger").
 *
 * Every answer is a RECORDED hub answer (web/src/desk/programs/__fixtures__/,
 * recorded through the real routes by scripts/record_program_fixtures.py).
 * The answer to a press is the recorded Program with the change the hub
 * makes applied to it (the item leaves `your_turn_items`, the decision gets
 * its `overturned_at`), so each press is driven through to the rendered
 * outcome: the row leaves the well, the status bar count drops, the row
 * reads Overturned. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import listFixture from "../__fixtures__/programs.list.json";
import runningFixture from "../__fixtures__/program.running.json";
import yourTurnFixture from "../__fixtures__/program.your_turn.json";
import doneFixture from "../__fixtures__/program.done.json";
import parkedFixture from "../__fixtures__/program.parked.json";
import draftingFixture from "../__fixtures__/program.drafting.json";
import needsFixture from "../__fixtures__/needs_you.program.json";
import roomFixture from "../__fixtures__/room.programs.json";
import personFixture from "../__fixtures__/person.programs.json";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  openRef: vi.fn(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
  openPullout: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../openObject")>()),
  openRef: mocks.openRef,
}));
vi.mock("../../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../shell")>()),
  openSurfaceOr: mocks.openSurfaceOr,
  openProjectRoom: mocks.openProjectRoom,
}));
vi.mock("../open", () => ({ openProgram: (id: string) => mocks.openPullout(`program:${id}`) }));

import { ApiError } from "../../../lib/api";
import { ProgramsCore } from "../ProgramsWindow";
import { ProgramBody } from "../ProgramWindow";
import { RoomPrograms } from "../RoomPrograms";
import { PersonPrograms, personProgramsOf } from "../PersonPrograms";
import { ProgramStepLine, flightProgramOf } from "../StepLine";
import { programsLampOf, programsTodayLine, worseLamp } from "../lamp";
import { runNoteAsProgram } from "../fromNote";
import { stationsOf } from "../model";
import type { Program, ProgramList, ProgramStep } from "../types";
import { needFace } from "../../needs/needsFace";
import type { NeedsYouRoomItem } from "../../needsYou";
import { DESK_APPLICATIONS } from "../../applications";

function subscribe(type: string, listener: (frame: Frame) => void) {
  const set = mocks.listeners.get(type) ?? new Set<(frame: Frame) => void>();
  set.add(listener);
  mocks.listeners.set(type, set);
  return () => set.delete(listener);
}
function emit(type: string, data: unknown) {
  act(() => {
    for (const listener of [...(mocks.listeners.get(type) ?? [])]) listener({ type, data });
  });
}

const clone = <T,>(value: T): T => structuredClone(value);
const list = listFixture as unknown as ProgramList;
const running = runningFixture as unknown as Program;
const yourTurn = yourTurnFixture as unknown as Program;
const done = doneFixture as unknown as Program;
const parked = parkedFixture as unknown as Program;
const drafting = draftingFixture as unknown as Program;
let calls: string[];

function hub(table: Record<string, Answer>) {
  mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
    const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
    calls.push(init?.json !== undefined ? `${key} ${JSON.stringify(init.json)}` : key);
    if (!(key in table)) throw new ApiError(404, "Not Found", { detail: "Not Found" });
    const answer = table[key];
    return clone(typeof answer === "function" ? (answer as (i?: typeof init) => unknown)(init) : answer);
  });
}

beforeEach(() => {
  calls = [];
  mocks.listeners.clear();
  mocks.apiFetch.mockReset();
  mocks.openRef.mockReset();
  mocks.openSurfaceOr.mockReset();
  mocks.openProjectRoom.mockReset();
  mocks.openPullout.mockReset();
});
afterEach(() => cleanup());

const status = () => screen.getByTestId(/program(s)?-status$/);
const stepRow = (ordinal: number) => screen.getAllByTestId("programs-step")
  .find((row) => within(row).getByTestId("programs-step-select").textContent?.startsWith(String(ordinal)))!;

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
    // A finished Program says how long it took, in ok ink.
    const doneRow = within(bands[2]).getByTestId("programs-row");
    expect(doneRow.textContent).toContain("Done in under a minute");
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

  it("New program makes a Fast cycle Program and opens its window", async () => {
    hub({
      "GET /api/programs": list,
      "POST /api/programs": drafting,
    });
    render(<ProgramsCore />);
    await screen.findAllByTestId("programs-band");
    fireEvent.click(screen.getByTestId("programs-new"));
    await waitFor(() => expect(mocks.openPullout).toHaveBeenCalledWith(`program:${drafting.id}`));
    expect(calls).toContain(`POST /api/programs ${JSON.stringify({ title: "New program", template: "fast-cycle" })}`);
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

describe("the Program window (direction C, the ledger)", () => {
  it("YOLO with a question: the board draws every step state, pi on qwen and the held step", async () => {
    hub({ [`GET /api/programs/${running.id}`]: running });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-board");
    const words = screen.getAllByTestId("programs-step").map((row) => within(row).getByTestId("programs-step-word").textContent);
    expect(words).toEqual(["Done", "PR open", "Check failed · log", "Asks you", "Ready · waiting for qwen", "Planned", "Working"]);
    // The pi step names its engine beside the sprite.
    expect(stepRow(5).textContent).toContain("pi · qwen3.8-27b on karol");
    // The question is in the well with Answer (it opens the step's lane).
    const well = screen.getByTestId("programs-your-turn");
    fireEvent.click(within(well).getByTestId("programs-turn-answer"));
    expect(mocks.openRef).toHaveBeenCalledWith("launch:L4");
    // At YOLO the well holds no merge row (the hub sends none).
    expect(within(well).queryByTestId("programs-turn-merge")).toBeNull();
    // The toolbar and the status bar say the ladder's word.
    expect(screen.getByTestId("program-control").textContent).toContain("Control: YOLO");
    expect(status().textContent).toContain("control YOLO");
    expect(status().textContent).toContain("1 of 7 done");
    // The place line: Project ▸ HoldSpeak · For Alice.
    fireEvent.click(within(screen.getByTestId("programs-place-project")).getByRole("button"));
    expect(mocks.openProjectRoom).toHaveBeenCalledWith("proj-holdspeak");
    expect(screen.getByTestId("programs-place-person").textContent).toBe("For Alice");
  });

  it("the Gate fold of the red step: the verdict the verifier read and the red section", async () => {
    hub({ [`GET /api/programs/${running.id}`]: running });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(within(stepRow(3)).getByTestId("programs-step-select"));
    const gate = await screen.findByTestId("programs-gate");
    expect(within(gate).getByTestId("programs-gate-verdict").textContent).toMatch(/^Check failed/);
    const sections = within(gate).getAllByTestId("programs-gate-section");
    expect(sections.find((node) => node.getAttribute("data-tone") === "fail")?.textContent).toMatch(/^Pytest/);
    expect(within(gate).getByTestId("programs-gate-track").getAttribute("aria-label")).toBe("At Check log");
  });

  it("Decided for you: Overturn presses through to the hub and the row reads Overturned", async () => {
    const row = running.decided_for_you!.find((item) => item.overturnable)!;
    const after = clone(running);
    after.decided_for_you = after.decided_for_you!.map((item) => item.id === row.id ? { ...item, overturned_at: "2026-10-28T17:51:00+00:00", overturnable: false } : item);
    hub({
      [`GET /api/programs/${running.id}`]: running,
      [`POST /api/programs/${running.id}/decisions/${row.id}/overturn`]: { program: after },
    });
    render(<ProgramBody programId={running.id} />);
    const decided = await screen.findByTestId("programs-decided");
    const rows = within(decided).getAllByTestId("programs-decided-row");
    expect(rows).toHaveLength(running.decided_for_you!.length);
    // Only the decision that can still be undone has the verb.
    expect(within(decided).getAllByTestId("programs-overturn")).toHaveLength(running.decided_for_you!.filter((item) => item.overturnable).length);
    const target = rows.find((node) => node.getAttribute("data-decision") === String(row.id))!;
    expect(target.textContent).toContain(row.rule!);
    fireEvent.click(within(target).getByTestId("programs-overturn"));
    await waitFor(() => expect(within(target).getByTestId("programs-decided-overturned").textContent).toBe("Overturned"));
    expect(calls).toContain(`POST /api/programs/${running.id}/decisions/${row.id}/overturn {}`);
  });

  it("Secure, your turn: Merge leaves the well and the status bar count drops", async () => {
    const merge = yourTurn.your_turn_items.find((item) => item.kind === "merge")!;
    const after = clone(yourTurn);
    after.your_turn_items = after.your_turn_items.filter((item) => item.id !== merge.id);
    after.your_turn = yourTurn.your_turn - 1;
    hub({
      [`GET /api/programs/${yourTurn.id}`]: yourTurn,
      [`POST /api/programs/${yourTurn.id}/steps/${merge.step_id}/decide`]: { program: after },
    });
    render(<ProgramBody programId={yourTurn.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    expect(within(well).getAllByTestId("programs-turn-item").map((node) => node.getAttribute("data-kind"))).toEqual(["merge", "finding", "finding", "core"]);
    expect(status().textContent).toContain("4 wait on you");
    expect(status().textContent).toContain("control Secure");
    // The core question has its own verbs.
    const core = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "core")!;
    expect(within(core).getByTestId("programs-turn-go-on").textContent).toBe("Go on");
    const mergeRow = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "merge")!;
    fireEvent.click(within(mergeRow).getByTestId("programs-turn-merge"));
    await waitFor(() => expect(within(screen.getByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")).toHaveLength(3));
    expect(status().textContent).toContain("3 wait on you");
    expect(calls).toContain(`POST /api/programs/${yourTurn.id}/steps/${merge.step_id}/decide ${JSON.stringify({ kind: "merge", choice: "merge" })}`);
  });

  it("a finding's Later sends its finding id", async () => {
    const finding = yourTurn.your_turn_items.find((item) => item.kind === "finding")!;
    const after = clone(yourTurn);
    after.your_turn_items = after.your_turn_items.filter((item) => item.id !== finding.id);
    hub({
      [`GET /api/programs/${yourTurn.id}`]: yourTurn,
      [`POST /api/programs/${yourTurn.id}/steps/${finding.step_id}/decide`]: { program: after },
    });
    render(<ProgramBody programId={yourTurn.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const row = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-item") === finding.id)!;
    fireEvent.click(within(row).getByTestId("programs-turn-later"));
    await waitFor(() => expect(screen.queryAllByTestId("programs-turn-item").some((node) => node.getAttribute("data-item") === finding.id)).toBe(false));
    expect(calls).toContain(`POST /api/programs/${yourTurn.id}/steps/${finding.step_id}/decide ${JSON.stringify({ kind: "finding", choice: "later", finding_id: finding.finding_id })}`);
  });

  it("a refused press says what failed, what is kept and what to do", async () => {
    const merge = yourTurn.your_turn_items.find((item) => item.kind === "merge")!;
    hub({ [`GET /api/programs/${yourTurn.id}`]: yourTurn });
    render(<ProgramBody programId={yourTurn.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const mergeRow = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-item") === merge.id)!;
    fireEvent.click(within(mergeRow).getByTestId("programs-turn-merge"));
    expect((await screen.findByTestId("programs-turn-failure")).textContent)
      .toBe("Your answer did not reach the program · The step is unchanged · Try again");
    expect(within(screen.getByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")).toHaveLength(4);
  });

  it("Done: Open note in place of Start, the MERGE station lit green with the PR number", async () => {
    hub({ [`GET /api/programs/${done.id}`]: done });
    render(<ProgramBody programId={done.id} />);
    await screen.findByTestId("programs-board");
    expect(screen.queryByTestId("program-start")).toBeNull();
    expect(screen.queryByTestId("program-park")).toBeNull();
    fireEvent.click(screen.getByTestId("program-open-note"));
    expect(mocks.openRef).toHaveBeenCalledWith(`note:${done.note_id}`);
    const merge = stationsOf(done.steps[0] as ProgramStep).at(-1)!;
    expect(merge).toMatchObject({ key: "merge", state: "current", tone: "ok", sub: `#${done.steps[0].pr!.number}`, live: false });
    expect(within(stepRow(1)).getByTestId("programs-step-word").textContent).toBe(`Done`);
    expect(status().textContent).toContain("Done in under a minute");
  });

  it("Parked: Resume brings it back", async () => {
    hub({
      [`GET /api/programs/${parked.id}`]: parked,
      [`POST /api/programs/${parked.id}/resume`]: { ...clone(parked), state: "running", state_word: "Running" },
    });
    render(<ProgramBody programId={parked.id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(screen.getByTestId("program-resume"));
    await waitFor(() => expect(screen.getByTestId("program-window").getAttribute("data-state")).toBe("running"));
    expect(screen.getByTestId("program-park")).toBeTruthy();
  });

  it("Drafting: the steps are fields with mics, the goal is a pad, Start is the primary", async () => {
    hub({ [`GET /api/programs/${drafting.id}`]: drafting });
    render(<ProgramBody programId={drafting.id} />);
    const rows = await screen.findAllByTestId("programs-draft-step");
    expect(rows).toHaveLength(drafting.steps.length);
    expect((within(rows[0]).getByRole("textbox", { name: "Step 1 title" }) as HTMLInputElement).value).toBe(drafting.steps[0].title);
    expect(within(rows[0]).getByRole("button", { name: /Speak Step 1 title/ })).toBeTruthy();
    expect((screen.getByRole("textbox", { name: "Goal" }) as HTMLTextAreaElement).value).toBe(drafting.goal);
    expect(screen.getByTestId("program-start").className).toMatch(/primary/);
  });
});

describe("the seams", () => {
  it("Needs you: a recorded Program row is a decide row with its verbs and its Program group", () => {
    const item = (needsFixture as { items: NeedsYouRoomItem[] }).items[0];
    const face = needFace({ ref: String(item.ref), kind: "attention", item } as never, { now: new Date(), sessions: [], flights: [] } as never);
    expect(face.kind).toBe("program");
    expect(face.direction).toBe("decide");
    expect(face.openRef).toBe(`program:${(item.program as { programId: string }).programId}`);
    expect(face.verbs).toMatchObject({ kind: "program", choices: ["fix_now", "later", "skip"], itemKind: "finding", findingId: "f1" });
    expect(face.fact).toContain("The words wave");
  });

  it("the Room's Programs fold: one row per recorded Program, the your-turn word only when not zero", () => {
    render(<RoomPrograms programs={roomFixture.programs} />);
    const rows = screen.getAllByTestId("room-program-row");
    expect(rows).toHaveLength(roomFixture.programs.length);
    expect(rows[0].textContent).toContain("0 of 3");
    expect(rows[0].textContent).toContain("4 wait on you");
    expect(rows[1].textContent).not.toContain("wait on you");
    fireEvent.click(within(rows[0]).getByTestId("room-program-open"));
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${roomFixture.programs[0].id}`);
  });

  it("the person's room: the Programs line and To show them", () => {
    render(<PersonPrograms programs={personProgramsOf(personFixture)} name="Alice" />);
    expect(screen.getByTestId("person-program-row").textContent).toContain("The hub stops stalling · 1 of 7");
    expect(screen.getByTestId("person-programs-show").textContent).toContain("Indexes · Merged #101");
    expect(screen.queryByTestId("person-programs-ask")).toBeNull();
  });

  it("Agents: a flight that belongs to a step says Step n of the Program and opens it", () => {
    const program = flightProgramOf({ id: running.id, title: running.title, step_id: running.steps[3].id, step_ordinal: 4 });
    render(<ProgramStepLine program={program} />);
    const line = screen.getByTestId("agent-program-step");
    expect(line.textContent).toBe("Step 4 of The hub stops stalling");
    fireEvent.click(line);
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${running.id}`);
  });

  it("Today and the Dock: one Since this morning line, and the worst Program state on the Agents lamp", () => {
    const now = new Date(list.programs[0].updated_at);
    expect(programsTodayLine(list.programs, now)).toBe("Programs: 2 wait on you, 1 done");
    expect(programsTodayLine(list.programs, new Date(now.getTime() + 3 * 86_400_000))).toBe("");
    const lamp = programsLampOf(list.worst, list.counts);
    expect(lamp).toEqual({ lamp: "ask", words: "2 programs wait on you" });
    expect(worseLamp("work", lamp.lamp)).toBe("ask");
  });

  it("the Note's Run as a program makes a Program with the note as its origin", async () => {
    hub({ "POST /api/programs": drafting });
    const failed = await runNoteAsProgram({ id: "n1", title: "", body: "# Calls on the home box\nThe runner and the window.", projectId: "proj-holdspeak" });
    expect(failed).toBeNull();
    expect(calls).toContain(`POST /api/programs ${JSON.stringify({
      title: "Calls on the home box", goal: "# Calls on the home box\nThe runner and the window.", template: "fast-cycle",
      origin_ref: "note:n1", project_id: "proj-holdspeak",
    })}`);
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${drafting.id}`);
  });
});

describe("Phone: the Reach line under Decided for you (PHONE-DESIGN §9)", () => {
  it("draws the newest reach row (its line and rule); Open thread asks for the Phone wing", async () => {
    // The recorded Program with one more Decided for you row in the shape
    // ProgramService.engine_decision writes for a reach (kind "reach", the
    // phone's line "Reached you: a call", the rule).
    const reached = clone(running);
    reached.may_call = true;
    reached.decided_for_you = [...(running.decided_for_you ?? []), {
      id: 9001, at: "2026-10-28T12:12:00+00:00", step_id: null, kind: "reach", choice: "call",
      line: "Reached you: a call", rule: "YOLO: a core question calls at once when the program may call",
      overturnable: false, overturned_at: null,
    }];
    hub({ [`GET /api/programs/${running.id}`]: reached });
    const { usePhoneFocus } = await import("../../calls/phoneFocus");
    render(<ProgramBody programId={running.id} />);
    const line = await screen.findByTestId("programs-reach");
    expect(line.textContent).toContain("Reached you: a call · YOLO: a core question calls at once when the program may call · it may call you");
    expect(line.getAttribute("data-channel")).toBe("call");
    fireEvent.click(within(line).getByTestId("programs-reach-open"));
    expect(usePhoneFocus.getState().pending).toBe(true);
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("open-calls", "/");
  });

  it("no reach, no line", async () => {
    hub({ [`GET /api/programs/${running.id}`]: running });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-decided");
    expect(screen.queryByTestId("programs-reach")).toBeNull();
  });
});

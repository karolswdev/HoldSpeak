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
import limitedFixture from "../__fixtures__/program.limited.json";
import raceFixture from "../__fixtures__/program.race.json";
import needsFixture from "../__fixtures__/needs_you.program.json";
import roomFixture from "../__fixtures__/room.programs.json";
import personFixture from "../__fixtures__/person.programs.json";
import skipDecisionFixture from "../__fixtures__/program.skip_decision.json";
import roomProposedFixture from "../__fixtures__/room.decisions.proposed.json";
import startFromFixture from "../__fixtures__/program.start_from.json";
import historyFixture from "../__fixtures__/program.history.json";
import historyListFixture from "../__fixtures__/programs.history.list.json";
import sinceMorningPrograms from "../../__tests__/fixtures/today-hub/since-morning.programs.json";
// PG-REQ (PROGRAMS-REQUIREMENTS-2026-10-31): recorded through the real routes,
// with the hub's answers to his presses on the same records.
import filteredListFixture from "../__fixtures__/programs.filtered.list.json";
import requirementsFixture from "../__fixtures__/program.requirements.json";
import sendBackFixture from "../__fixtures__/program.requirements.send_back.json";
import waivedFixture from "../__fixtures__/program.requirements.waived.json";
import waiveRefusedFixture from "../__fixtures__/program.requirements.waive_refused.json";
import addedFixture from "../__fixtures__/program.requirements.added.json";
import evidenceFixture from "../__fixtures__/program.requirements.evidence.json";
import wordFixture from "../__fixtures__/program.requirement_word.json";
import wordMetFixture from "../__fixtures__/program.requirement_word.met.json";
import needsRequirementsFixture from "../__fixtures__/needs_you.requirements.json";
import adjustFixture from "../__fixtures__/program.adjust.json";
import movedFixture from "../__fixtures__/program.adjust.moved.json";
import insertedFixture from "../__fixtures__/program.adjust.inserted.json";
import amendedFixture from "../__fixtures__/program.adjust.amended.json";
import titledFixture from "../__fixtures__/program.adjust.titled.json";
import proposalsFixture from "../__fixtures__/program.proposals.json";
import proposalsAddedFixture from "../__fixtures__/program.proposals.added.json";
// PG-LANG LANG2: the Program text (GET) and a preview then an apply of a
// changed text (a refused brief, control up the ladder, a new step, a merge
// on his press, a + line), recorded through the real routes.
import textFixture from "../__fixtures__/program.text.json";
import textApplyFixture from "../__fixtures__/program.text_apply.json";
// PG-LANG LANG3/4: a sentence shaped by the REAL qwen3.8-27b replies
// (tests/fixtures/program_shape_reply.json) replayed through the hub's runner,
// recorded through the real routes (tests/integration/test_desk_program_shape.py).
import shapeFixture from "../__fixtures__/program.shape.json";

type Frame = { type: string; data: unknown };
type Answer = unknown | ((init?: { method?: string; json?: unknown }) => unknown);

const mocks = vi.hoisted(() => ({
  listeners: new Map<string, Set<(frame: Frame) => void>>(),
  apiFetch: vi.fn(),
  apiBlob: vi.fn(),
  openRef: vi.fn(),
  openSurfaceOr: vi.fn(),
  openProjectRoom: vi.fn(),
  openPullout: vi.fn(),
  openDecisionRecord: vi.fn(),
}));

vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiFetch: mocks.apiFetch,
  apiBlob: mocks.apiBlob,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useOptionalRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe }),
  useRuntimeFrame: () => null,
}));
vi.mock("../../openObject", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../openObject")>()),
  openRef: mocks.openRef,
  openDecisionRecord: mocks.openDecisionRecord,
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
import { RoomDecisions } from "../RoomDecisions";
import { decodeRoomSnapshot } from "../../../features/project-room/model";
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
const limited = limitedFixture as unknown as Program;
const raced = raceFixture as unknown as Program;
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
  mocks.apiBlob.mockReset();
  mocks.openRef.mockReset();
  mocks.openSurfaceOr.mockReset();
  mocks.openProjectRoom.mockReset();
  mocks.openPullout.mockReset();
  mocks.openDecisionRecord.mockReset();
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

describe("a race of 2 (the recorded race: Codex wins in 34 min)", () => {
  it("the contender is indented under the step, the loser says Lost the race to Codex · 34 min, Open lane on each", async () => {
    hub({ [`GET /api/programs/${raced.id}`]: raced });
    render(<ProgramBody programId={raced.id} />);
    await screen.findByTestId("programs-board");
    const lead = stepRow(1);
    expect(within(lead).getByTestId("programs-step-word").textContent).toBe("Race of 2");
    // The step's own agent lost: its line and its time.
    expect(lead.textContent).toContain("Claude Code");
    expect(lead.textContent).toContain("“Lost the race to Codex”");
    expect(lead.querySelector(".pg-step-when")?.textContent).toBe("34 min");
    expect(lead.querySelector(".pg-step-meta")?.textContent).toBe("Claude Code · 34 min · “Lost the race to Codex”");
    // The contender row comes right after the step, indented, and names its agent.
    const [contender] = screen.getAllByTestId("programs-contender");
    expect(lead.nextElementSibling).toBe(contender);
    expect(contender.hasAttribute("data-contender")).toBe(true);
    expect(within(contender).getByTestId("programs-step-select").textContent).toContain("Codex");
    expect(within(contender).getByTestId("programs-step-word").textContent).toBe("Done");
    expect(contender.textContent).toContain("Merged #101");
    // Open lane on each: the loser's lane and the winner's.
    fireEvent.click(within(lead).getByTestId("programs-step-open"));
    fireEvent.click(within(contender).getByTestId("programs-step-open"));
    expect(mocks.openRef.mock.calls).toEqual([["launch:L1"], ["launch:L2"]]);
    // The engine's choice is under Decided for you.
    expect(screen.getByTestId("programs-decided").textContent).toContain("Codex won the race in 34 min");
  });
});

describe("PG19: when an agent runs out (canvas handoff-2026-10-28)", () => {
  it("the limited step reads Limited until … · continuing in Codex, and Continue in Codex presses through", async () => {
    const item = limited.your_turn_items.find((row) => row.kind === "limited")!;
    const after = clone(limited);
    after.your_turn_items = after.your_turn_items.filter((row) => row.id !== item.id);
    after.your_turn = 0;
    hub({
      [`GET /api/programs/${limited.id}`]: limited,
      [`POST /api/programs/${limited.id}/steps/${item.step_id}/decide`]: { program: after },
    });
    render(<ProgramBody programId={limited.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const row = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "limited")!;
    expect(row.textContent).toContain(`Claude Code is at its limit until ${item.until_words}: continue in Codex now, or wait?`);
    expect(within(row).getByTestId("programs-turn-continue").textContent).toBe("Continue in Codex");
    expect(within(row).getByTestId("programs-turn-continue").className).toMatch(/primary/);
    expect(within(row).getByTestId("programs-turn-wait").textContent).toBe("Wait");
    const word = within(stepRow(2)).getByTestId("programs-step-word");
    expect(word.textContent).toBe(`Limited until ${item.until_words}`);
    expect(word.getAttribute("title")).toBe(`Limited until ${item.until_words} · continuing in Codex`);
    expect(word.getAttribute("data-tone")).toBe("warn");
    // The toolbar names the order.
    expect(screen.getByTestId("program-runs-on").textContent).toContain("Agent: Claude Code, then Codex");
    fireEvent.click(within(row).getByTestId("programs-turn-continue"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(calls).toContain(`POST /api/programs/${limited.id}/steps/${item.step_id}/decide ${JSON.stringify({ kind: "limited", choice: "continue" })}`);
  });

  it("the Checkpoints fold: the handoff divider, and View brief shows the brief, what was redacted and the earlier turns", async () => {
    hub({ [`GET /api/programs/${limited.id}`]: limited });
    render(<ProgramBody programId={limited.id} />);
    const [line] = await screen.findAllByTestId("programs-handoff");
    expect(line.textContent).toContain("Step 1 · Handed to Codex · usage limit");
    expect(screen.queryByTestId("programs-handoff-brief")).toBeNull();
    fireEvent.click(within(line).getByTestId("programs-view-brief"));
    const sheet = within(line).getByTestId("programs-handoff-brief");
    const entry = limited.steps[0].handoffs![0];
    expect(sheet.textContent).toContain("Claude Code to Codex");
    expect(within(sheet).getByTestId("programs-handoff-redacted").textContent).toBe(`Redacted: ${entry.redacted_words}`);
    expect(entry.redacted_words).toBe("1 key, 1 token");
    expect(sheet.textContent).toContain("1 earlier turn, not included");
    expect(sheet.querySelector("pre")!.textContent).toBe(entry.brief);
    expect(entry.brief).not.toMatch(/sk-demo|ghp_demo/);
    expect(within(line).getByTestId("programs-view-brief").textContent).toBe("Hide brief");
  });

  it("Drafting: Allowed agents and the then rows of the Agent picker write the Program", async () => {
    const patched = clone(drafting);
    hub({
      [`GET /api/programs/${drafting.id}`]: drafting,
      [`PATCH /api/programs/${drafting.id}`]: { program: patched },
    });
    render(<ProgramBody programId={drafting.id} />);
    const allowed = await screen.findByTestId("programs-allowed");
    fireEvent.click(within(allowed).getByLabelText("Codex"));
    await waitFor(() => expect(calls).toContain(
      `PATCH /api/programs/${drafting.id} ${JSON.stringify({ allowed_profiles: ["claude-default", "pi-default"] })}`));
    fireEvent.click(screen.getByTestId("program-runs-on"));
    fireEvent.click(await screen.findByRole("menuitemcheckbox", { name: /then Codex/ }));
    const first = { profile: drafting.default.profile, engine: drafting.default.engine?.id ?? null };
    await waitFor(() => expect(calls).toContain(
      `PATCH /api/programs/${drafting.id} ${JSON.stringify({ runs_on: [first, { profile: "codex-default", engine: null }] })}`));
  });
});

describe("PG20: hidden-ref checkpoints (recorded on the rig's real git)", () => {
  const started = startFromFixture as unknown as Program;

  it("a pinned row shows its commit and Start from here; a line with no pin shows neither", async () => {
    hub({ [`GET /api/programs/${started.id}`]: started });
    render(<ProgramBody programId={started.id} />);
    const ledger = await screen.findByTestId("programs-checkpoints");
    const rows = within(ledger).getAllByRole("listitem");
    const half = rows.find((row) => row.textContent?.includes("Half way: the words are plain"))!;
    const pinned = started.checkpoints.find((row) => row.line === "Half way: the words are plain")!;
    const pin = within(half).getByTestId("programs-checkpoint-ref");
    expect(pin.getAttribute("data-ref")).toBe(pinned.ref);
    expect(pinned.ref).toMatch(/^refs\/holdspeak\/checkpoints\/step-[0-9a-f]+\/2$/);
    expect(pin.querySelector("code")!.textContent).toBe(pinned.ref_commit!.slice(0, 7));
    expect(pin.querySelector("code")!.getAttribute("title")).toBe(pinned.ref);
    expect(within(half).getByTestId("programs-start-from").textContent).toBe("Start from here");
    const program = rows.find((row) => row.textContent?.includes("Started the program"))!;
    expect(within(program).queryByTestId("programs-start-from")).toBeNull();
    const noted = rows.find((row) => row.textContent?.includes("Started step 2 from"))!;
    expect(within(noted).queryByTestId("programs-checkpoint-ref")).toBeNull();
  });

  it("Start from here posts the checkpoint and draws the new step from the hub's answer", async () => {
    const before = clone(started);
    const added = started.steps.find((step) => step.ordinal === 2)!;
    before.steps = before.steps.filter((step) => step.id !== added.id);
    before.checkpoints = before.checkpoints.filter((row) => row.step_id !== added.id);
    const pinned = started.checkpoints.find((row) => row.line === "Half way: the words are plain")!;
    hub({
      [`GET /api/programs/${started.id}`]: before,
      [`POST /api/programs/${started.id}/checkpoints/${pinned.id}/start-from`]: { step_id: added.id, ref: pinned.ref, program: started },
    });
    render(<ProgramBody programId={started.id} />);
    const ledger = await screen.findByTestId("programs-checkpoints");
    expect(screen.getAllByTestId("programs-step")).toHaveLength(1);
    const half = within(ledger).getAllByRole("listitem").find((row) => row.textContent?.includes("Half way"))!;
    fireEvent.click(within(half).getByTestId("programs-start-from"));
    await waitFor(() => expect(screen.getAllByTestId("programs-step")).toHaveLength(2));
    expect(calls).toContain(`POST /api/programs/${started.id}/checkpoints/${pinned.id}/start-from {}`);
    expect(stepRow(2).textContent).toContain("Dock words (from checkpoint 2)");
    expect(screen.getByTestId("programs-checkpoints").textContent).toContain(`Started step 2 from ${pinned.ref}`);
  });

  it("View brief names the ref the next agent continues from", async () => {
    hub({ [`GET /api/programs/${limited.id}`]: limited });
    render(<ProgramBody programId={limited.id} />);
    const [line] = await screen.findAllByTestId("programs-handoff");
    fireEvent.click(within(line).getByTestId("programs-view-brief"));
    const entry = limited.steps[0].handoffs![0];
    expect(entry.continues_from).toMatch(/^refs\/holdspeak\/checkpoints\/step-[0-9a-f]+\/\d+$/);
    expect(within(line).getByTestId("programs-handoff-ref").textContent).toBe(`Continues from ${entry.continues_from}`);
    expect(entry.brief).toContain(`- Continues from: \`${entry.continues_from}\``);
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
    // The hub's block (`ProgramService.since_morning`, recorded through the Today route).
    const block = (sinceMorningPrograms as { "/api/today/since-morning": { programs: Parameters<typeof programsTodayLine>[0] } })
      ["/api/today/since-morning"].programs;
    expect(programsTodayLine(block)).toBe("Programs: 1 running, 1 waits on you, 1 PR merged");
    expect(programsTodayLine({ moved: 0, running: 0, waiting: 0, done: 0, merged: 0 })).toBe("");
    expect(programsTodayLine(null)).toBe("");
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

describe("PG16: decisions from a Program (the recorded Skip)", () => {
  const skipped = skipDecisionFixture as unknown as Program;

  it("the checkpoint row of his Skip says Proposed as a decision; an overturned row does not", async () => {
    hub({ [`GET /api/programs/${skipped.id}`]: skipped });
    render(<ProgramBody programId={skipped.id} />);
    const checks = await screen.findByTestId("programs-checkpoints");
    const rows = within(checks).getAllByRole("listitem");
    const skip = rows.find((row) => row.textContent?.startsWith("You") && row.textContent.includes("Skip: sentence case the title"))!;
    expect(within(skip).getByTestId("programs-proposed-decision").textContent).toBe("Proposed as a decision");
    const plain = rows.find((row) => row.textContent?.includes("Opened PR #"))!;
    expect(within(plain).queryByTestId("programs-proposed-decision")).toBeNull();
    // The engine's NOTE Skip was overturned: no word on its Decided for you row.
    const decided = screen.getByTestId("programs-decided");
    const overturned = within(decided).getAllByTestId("programs-decided-row").find((row) => row.hasAttribute("data-overturned"))!;
    expect(within(overturned).queryByTestId("programs-proposed-decision")).toBeNull();
  });

  it("the Room's proposed decisions: each Skip with its Program and PR; Open opens the record", () => {
    const room = decodeRoomSnapshot({ decisions: roomProposedFixture } as Record<string, unknown>);
    if (room.decisions.state !== "ok") throw new Error("decisions not read");
    const proposed = room.decisions.proposed ?? [];
    render(<RoomDecisions proposed={proposed} />);
    const rows = screen.getAllByTestId("room-proposed-decision");
    expect(rows).toHaveLength(roomProposedFixture.proposed.length);
    expect(rows[0].textContent).toContain("Skip: sentence case the title");
    expect(rows[0].textContent).toContain("Proposed");
    expect(within(rows[0]).getByTestId("room-proposed-from").textContent).toBe("The words wave · PR #101");
    fireEvent.click(within(rows[0]).getByTestId("room-proposed-open"));
    expect(mocks.openDecisionRecord).toHaveBeenCalledWith(roomProposedFixture.proposed[0].id);
  });

  it("no proposed decision, no fold", () => {
    const { container } = render(<RoomDecisions proposed={[]} />);
    expect(container.textContent).toBe("");
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
    expect(row.textContent).toContain("3 of 3 steps");
    expect(row.textContent).toContain(history.history!.words);
    expect(history.history!.words).toMatch(/^Merged 3 PRs · \d+ Oct/);
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


/* ── PG-REQ: requirements, browse and adjust (REQ9 to REQ12) ─────────── */

const reqProgram = requirementsFixture as unknown as Program;
const adjust = (adjustFixture as unknown as Program);
type Answered = { program: Program; requirement_id?: string };
const reqRow = (label: string) => screen.getAllByTestId("programs-req").find((row) => row.getAttribute("data-label") === label)!;
const allRequirements = (program: Program) => [...(program.requirements ?? []), ...program.steps.flatMap((step) => step.requirements ?? [])];
const idOf = (program: Program, label: string) => allRequirements(program).find((row) => row.label === label)!.id;
const decidePath = (program: Program, label: string) => `POST /api/programs/${program.id}/requirements/${idOf(program, label)}/decide`;
/** The open menu's items (a WorkMenu radio is checked only on its choice). */
const menuWords = () => [...document.querySelectorAll("[role=menuitem],[role=menuitemradio]")].map((node) => node.textContent);
const menuItem = (name: string) => [...document.querySelectorAll<HTMLElement>("[role=menuitem],[role=menuitemradio]")].find((node) => node.textContent === name)!;

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
    expect(bands.map((band) => within(band).getByRole("heading").textContent)).toEqual([`HoldSpeak · ${shown.length}`, "No project · 1"]);
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

describe("REQ10: the Requirements board (direction A, the checklist)", () => {
  it("draws every requirement from the recording: grouped, its state, its kind, where, its proof; open while one is Unmet", async () => {
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    const board = await screen.findByTestId("programs-requirements");
    expect(board.closest("details")!.open).toBe(true);
    const met = reqProgram.requirements_met!;
    expect(board.closest("details")!.querySelector("summary")!.textContent).toContain(`${met.met} of ${met.total} met · ${met.his} waits on you`);
    expect([...board.querySelectorAll("[data-band]")].map((band) => band.getAttribute("data-band"))).toEqual(["program", "every", "own"]);
    const word = (label: string) => within(reqRow(label)).getByTestId("programs-req-state").textContent;
    // Each state, and its tone.
    expect(word("R2")).toBe("Met");
    expect(reqRow("R2").getAttribute("data-tone")).toBe("ok");
    expect(word("R3")).toBe("Unmet");
    expect(reqRow("R3").getAttribute("data-tone")).toBe("fail");
    expect(word("R4")).toBe("Waits for you");
    expect(reqRow("R4").getAttribute("data-tone")).toBe("ask");
    expect(word("R6")).toBe("Waived");
    expect(reqRow("R6").getAttribute("data-state")).toBe("waived");
    expect(word("R7")).toBe("Not yet");
    // The kinds as Tokens.
    expect(["R1", "R2", "R3", "R4"].map((label) => reqRow(label).querySelector(".pg-kind")!.textContent)).toEqual(["Check", "Shot", "Review", "Your word"]);
    // Every step: six dots and "4 of 6 steps"; the Program's own: after the last step.
    const every = allRequirements(reqProgram).find((row) => row.scope === "every_step")!;
    expect(reqRow("R1").querySelectorAll(".pg-req-dot")).toHaveLength(6);
    const metCopies = every.steps!.filter((copy) => copy.state === "met" || copy.state === "waived").length;
    expect(within(reqRow("R1")).getByTestId("programs-req-where").textContent).toBe(`${metCopies} of 6 steps`);
    expect(within(reqRow("R7")).getByTestId("programs-req-proof").textContent).toBe("after the last step");
    // The proof one press away: the reviewer's line; Open log; Open shot.
    const r3 = allRequirements(reqProgram).find((row) => row.label === "R3")!;
    expect(within(reqRow("R3")).getByTestId("programs-req-proof").textContent).toBe(`“${r3.evidence.line}” · round 1`);
    expect(within(reqRow("R5")).getByTestId("programs-req-open-log")).toBeTruthy();
    expect(within(reqRow("R2")).getByTestId("programs-req-open-shot")).toBeTruthy();
    // The verbs his state allows: Met / Unmet on his word; Send back / Waive when Unmet; none on a Met row.
    expect(within(reqRow("R4")).getAllByRole("button").map((b) => b.textContent).filter((t) => t === "Met" || t === "Unmet")).toEqual(["Met", "Unmet"]);
    expect(within(reqRow("R3")).getByTestId("programs-req-send-back").textContent).toBe("Send back");
    expect(within(reqRow("R3")).getByTestId("programs-req-waive").textContent).toBe("Waive");
    expect(within(reqRow("R2")).queryByTestId("programs-req-waive")).toBeNull();
    // The status bar counts what is met.
    expect(screen.getByTestId("programs-status-met").textContent).toBe(`${met.met} of ${met.total} met`);
  });

  it("Send back presses through: the hub's answer puts the step back to work, and the ledger says it", async () => {
    const after = (sendBackFixture as unknown as Answered).program;
    hub({
      [`GET /api/programs/${reqProgram.id}`]: reqProgram,
      [decidePath(reqProgram, "R3")]: sendBackFixture,
    });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-requirements");
    expect(within(stepRow(2)).getByTestId("programs-step-word").textContent).toBe("Findings");
    fireEvent.click(within(reqRow("R3")).getByTestId("programs-req-send-back"));
    await waitFor(() => expect(within(stepRow(2)).getByTestId("programs-step-word").textContent).toBe("Working"));
    expect(calls).toContain(`${decidePath(reqProgram, "R3")} ${JSON.stringify({ choice: "send_back" })}`);
    expect(after.checkpoints.some((row) => row.line === "Sent R3 back to the agent")).toBe(true);
    expect(screen.getByTestId("programs-checkpoints").textContent).toContain("Sent R3 back to the agent");
  });

  it("Waive asks one line in place (Waive is withheld until he writes it); the row then reads Waived, struck, with his line", async () => {
    hub({
      [`GET /api/programs/${reqProgram.id}`]: reqProgram,
      [decidePath(reqProgram, "R5")]: waivedFixture,
    });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-requirements");
    fireEvent.click(within(reqRow("R5")).getByTestId("programs-req-waive"));
    const ask = within(reqRow("R5")).getByTestId("programs-req-ask");
    expect((within(ask).getByTestId("programs-req-ask-send") as HTMLButtonElement).disabled).toBe(true);
    fireEvent.change(within(ask).getByRole("textbox", { name: "Why you waive it" }), { target: { value: "The rig has no routes" } });
    fireEvent.click(within(ask).getByTestId("programs-req-ask-send"));
    await waitFor(() => expect(reqRow("R5").getAttribute("data-state")).toBe("waived"));
    expect(calls).toContain(`${decidePath(reqProgram, "R5")} ${JSON.stringify({ choice: "waive", line: "The rig has no routes" })}`);
    expect(within(reqRow("R5")).getByTestId("programs-req-state").textContent).toBe("Waived");
    expect(within(reqRow("R5")).getByTestId("programs-req-proof").textContent).toBe("You · “The rig has no routes”");
    expect(within(reqRow("R5")).queryByTestId("programs-req-ask")).toBeNull();
  });

  it("a refused Waive (the hub's 400) says what failed and what is kept; the row stays Unmet", async () => {
    const refused = waiveRefusedFixture as { status: number; body: unknown };
    hub({
      [`GET /api/programs/${reqProgram.id}`]: reqProgram,
      [decidePath(reqProgram, "R5")]: () => { throw new ApiError(refused.status, "Bad Request", refused.body); },
    });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-requirements");
    fireEvent.click(within(reqRow("R5")).getByTestId("programs-req-waive"));
    fireEvent.change(within(reqRow("R5")).getByRole("textbox", { name: "Why you waive it" }), { target: { value: "x" } });
    fireEvent.click(within(reqRow("R5")).getByTestId("programs-req-ask-send"));
    expect((await within(reqRow("R5")).findByTestId("programs-req-failure")).textContent).toBe("R5 was not waived · R5 is unchanged · Try again");
    expect(reqRow("R5").getAttribute("data-state")).toBe("unmet");
  });

  it("Open log shows the log the engine wrote, in a well under the row", async () => {
    const r5 = allRequirements(reqProgram).find((row) => row.label === "R5")!;
    hub({
      [`GET /api/programs/${reqProgram.id}`]: reqProgram,
      [`GET ${r5.evidence.url}`]: evidenceFixture.log.text,
    });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-requirements");
    fireEvent.click(within(reqRow("R5")).getByTestId("programs-req-open-log"));
    const log = await within(reqRow("R5")).findByTestId("programs-req-log");
    expect(log.textContent).toContain("program-check: exit 1");
    expect(log.textContent).toContain("1 failed, 30 passed");
  });

  it("his word in Your turn: Met presses through the requirement's route and the row leaves the well", async () => {
    const word = wordFixture as unknown as Program;
    const item = word.your_turn_items[0];
    hub({
      [`GET /api/programs/${word.id}`]: word,
      [`POST /api/programs/${word.id}/requirements/${item.requirement_id}/decide`]: wordMetFixture,
    });
    render(<ProgramBody programId={word.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const row = within(well).getByTestId("programs-turn-item");
    expect(row.getAttribute("data-kind")).toBe("requirement_word");
    expect(row.querySelector("b")!.textContent).toBe(`Step ${item.ordinal} · ${item.step_title}:`);
    expect(row.textContent).toContain("Your word · holds the merge");
    expect(within(row).getByTestId("programs-turn-met").className).toMatch(/primary/);
    fireEvent.click(within(row).getByTestId("programs-turn-met"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(calls).toContain(`POST /api/programs/${word.id}/requirements/${item.requirement_id}/decide ${JSON.stringify({ choice: "met" })}`);
    const r1 = within(screen.getByTestId("programs-requirements")).getAllByTestId("programs-req").find((node) => node.getAttribute("data-label") === "R1")!;
    expect(within(r1).getByTestId("programs-req-state").textContent).toBe("Met");
  });

  it("Unmet in Your turn asks one line, then sends it", async () => {
    const word = wordFixture as unknown as Program;
    const item = word.your_turn_items[0];
    hub({
      [`GET /api/programs/${word.id}`]: word,
      [`POST /api/programs/${word.id}/requirements/${item.requirement_id}/decide`]: wordMetFixture,
    });
    render(<ProgramBody programId={word.id} />);
    const row = within(await screen.findByTestId("programs-your-turn")).getByTestId("programs-turn-item");
    fireEvent.click(within(row).getByTestId("programs-turn-unmet"));
    const ask = within(row).getByTestId("programs-turn-ask");
    fireEvent.change(within(ask).getByRole("textbox", { name: "What is missing" }), { target: { value: "The lamp stays dark" } });
    fireEvent.click(within(ask).getByTestId("programs-turn-ask-send"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${word.id}/requirements/${item.requirement_id}/decide ${JSON.stringify({ choice: "unmet", line: "The lamp stays dark" })}`));
  });

  it("what an agent proposes: Add, Apply and Send each go to the proposal's route; Add draws the new requirement", async () => {
    const proposals = proposalsFixture as unknown as Program;
    const item = proposals.your_turn_items.find((row) => row.kind === "requirement_proposed")!;
    hub({
      [`GET /api/programs/${proposals.id}`]: proposals,
      [`POST /api/programs/${proposals.id}/proposals/${item.proposal_id}/decide`]: proposalsAddedFixture,
    });
    render(<ProgramBody programId={proposals.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const kinds = within(well).getAllByTestId("programs-turn-item").map((node) => node.getAttribute("data-kind"));
    expect(kinds.sort()).toEqual(["requirement_proposed", "step_amend", "step_change"]);
    const words = (kind: string) => [...within(within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === kind)!)
      .getAllByRole("button")].map((button) => button.textContent);
    expect(words("step_change")).toEqual(["Apply", "Skip"]);
    expect(words("step_amend")).toEqual(["Send", "Skip"]);
    const row = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "requirement_proposed")!;
    expect(row.textContent).toContain("The line answers in two rings");
    fireEvent.click(within(row).getByTestId("programs-turn-add"));
    await waitFor(() => expect(within(screen.getByTestId("programs-requirements")).getAllByTestId("programs-req").map((node) => node.textContent))
      .toEqual([expect.stringContaining("The line answers in two rings")]));
    expect(calls).toContain(`POST /api/programs/${proposals.id}/proposals/${item.proposal_id}/decide ${JSON.stringify({ choice: "add" })}`);
    expect(within(screen.getByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")).toHaveLength(2);
  });

  it("Add requirement: the kind follows the rule as he types (backticks are a Check, a window at 393 is a Shot); Add posts it and the row draws", async () => {
    const added = addedFixture as unknown as Answered;
    const step5 = reqProgram.steps.find((step) => step.ordinal === 5)!;
    hub({
      [`GET /api/programs/${reqProgram.id}`]: reqProgram,
      [`POST /api/programs/${reqProgram.id}/requirements`]: added,
    });
    render(<ProgramBody programId={reqProgram.id} />);
    const add = within(await screen.findByTestId("programs-requirements")).getByTestId("programs-req-add");
    const sentence = within(add).getByRole("textbox", { name: "Add a requirement" });
    expect(within(add).getByRole("button", { name: /Speak Add a requirement/ })).toBeTruthy();
    const kind = within(add).getByRole("combobox", { name: "Kind" }) as HTMLSelectElement;
    fireEvent.change(sentence, { target: { value: "`uv run pytest -q tests/unit/test_hub_loop_budget.py` is green" } });
    expect(kind.value).toBe("check");
    expect((within(add).getByRole("textbox", { name: "Command" }) as HTMLInputElement).value).toBe("uv run pytest -q tests/unit/test_hub_loop_budget.py");
    fireEvent.change(sentence, { target: { value: "The Programs window at 393 has no clipped text" } });
    expect(kind.value).toBe("shot");
    expect((within(add).getByRole("combobox", { name: "Window" }) as HTMLSelectElement).value).toBe("programs");
    expect((within(add).getByRole("combobox", { name: "Width" }) as HTMLSelectElement).value).toBe("393");
    fireEvent.change(within(add).getByRole("combobox", { name: "Where" }), { target: { value: step5.id } });
    fireEvent.click(within(add).getByTestId("programs-req-add-verb"));
    await waitFor(() => expect(screen.getAllByTestId("programs-req").some((row) => row.getAttribute("data-req") === added.requirement_id)).toBe(true));
    expect(calls).toContain(`POST /api/programs/${reqProgram.id}/requirements ${JSON.stringify({
      text: "The Programs window at 393 has no clipped text", kind: "shot", required: true, step_id: step5.id, spec: { case: "programs", width: 393 },
    })}`);
    const row = screen.getAllByTestId("programs-req").find((node) => node.getAttribute("data-req") === added.requirement_id)!;
    expect(within(row).getByTestId("programs-req-where").textContent).toBe("Step 5");
    expect(row.querySelector(".pg-kind")!.textContent).toBe("Shot");
    expect((within(within(screen.getByTestId("programs-requirements")).getByTestId("programs-req-add")).getByRole("textbox", { name: "Add a requirement" }) as HTMLInputElement).value).toBe("");
  });

  it("a Shot in a repository with no shot command withholds Add and says why", async () => {
    hub({ [`GET /api/programs/${adjust.id}`]: adjust });
    render(<ProgramBody programId={adjust.id} />);
    const add = within(await screen.findByTestId("programs-requirements")).getByTestId("programs-req-add");
    fireEvent.change(within(add).getByRole("textbox", { name: "Add a requirement" }), { target: { value: "The Calls window at 393 has no clipped text" } });
    expect((within(add).getByTestId("programs-req-add-verb") as HTMLButtonElement).disabled).toBe(true);
    expect(within(add).getByTestId("programs-req-add-why").textContent).toBe(adjust.can_prove!.shot_reason);
  });

  it("Needs you: his word is a decide row on the requirement's route, grouped by the Program", () => {
    const rows = (needsRequirementsFixture as { items: unknown[] }).items as NeedsYouRoomItem[];
    const face = needFace({ ref: String((rows[0] as { ref?: string }).ref), kind: "attention", item: rows[0] } as never,
      { now: new Date(), sessions: [], flights: [] } as never);
    expect(face.kind).toBe("program");
    expect(face.verbs).toMatchObject({ kind: "program", choices: ["met", "unmet"] });
    expect((face.verbs as { decide: string }).decide).toMatch(/\/requirements\/req-[0-9a-f]+\/decide$/);
    expect(face.fact).toContain(String((rows[0] as { group?: string }).group));
  });
});

describe("REQ11: the step fold, the ledger per step, the Met column, adjust in place", () => {
  it("the board's Met column: “1 of 2” with its tone, “1 to meet” while none is met, ok ink when all are met", async () => {
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-board");
    const cell = (n: number) => within(stepRow(n)).getByTestId("programs-step-met");
    expect(cell(1).textContent).toBe("2 of 2");
    expect(cell(1).hasAttribute("data-all")).toBe(true);
    expect(cell(2).textContent).toBe("1 of 2");
    expect(cell(2).getAttribute("data-tone")).toBe("fail");
    expect(cell(3).getAttribute("data-tone")).toBe("ask");
    expect(cell(6).textContent).toBe("1 to meet");
  });

  it("the step fold: FilterTokens with only what has something behind it; the first token is the one his eye needs", async () => {
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(within(stepRow(4)).getByTestId("programs-step-select"));
    const fold = await screen.findByTestId("programs-step-fold");
    // A red check: Gate first.
    expect(fold.getAttribute("data-part")).toBe("gate");
    expect(within(fold).getByTestId("programs-gate")).toBeTruthy();
    const tokens = within(within(fold).getByRole("group", { name: "Step 4" })).getAllByRole("button").map((button) => button.textContent);
    expect(tokens).toContain("Requirements");
    expect(tokens).not.toContain("Handoffs");
    fireEvent.click(within(fold).getByRole("button", { name: "Requirements" }));
    expect(within(fold).getAllByTestId("programs-req").map((row) => row.getAttribute("data-label"))).toEqual(["R1", "R5"]);
    fireEvent.click(within(fold).getByRole("button", { name: "Ledger" }));
    expect(within(fold).getByTestId("programs-step-ledger").textContent).toContain("R5");
    // An Unmet review: Requirements first.
    fireEvent.click(within(stepRow(2)).getByTestId("programs-step-select"));
    await waitFor(() => expect(screen.getByTestId("programs-step-fold").getAttribute("data-part")).toBe("requirements"));
  });

  it("the ledger, folded per step: the Program's own lines first, then one fold per step with its count and its last time", async () => {
    hub({ [`GET /api/programs/${adjust.id}`]: adjust });
    render(<ProgramBody programId={adjust.id} />);
    const ledger = await screen.findByTestId("programs-checkpoints");
    const heads = [...ledger.querySelectorAll(":scope > details > summary")].map((node) => node.textContent);
    expect(heads[0]).toMatch(/^The program · \d+ lines · last /);
    const runner = adjust.steps[0];
    const lines = adjust.checkpoints.filter((row) => row.step_id === runner.id).length;
    expect(heads.some((head) => head?.startsWith(`Step 1 · ${runner.title} · ${lines} lines · last `))).toBe(true);
  });

  it("a started step: its brief as it was sent, his additions under it, frozen fields as text with their reason; Amend brief presses through", async () => {
    const runner = adjust.steps[0];
    hub({
      [`GET /api/programs/${adjust.id}`]: adjust,
      [`POST /api/programs/${adjust.id}/steps/${runner.id}/amend`]: amendedFixture,
    });
    render(<ProgramBody programId={adjust.id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-select"));
    const fold = await screen.findByTestId("programs-step-fold");
    expect(within(fold).getByTestId("programs-step-brieftext").textContent).toContain(runner.brief);
    const amendments = within(fold).getAllByTestId("programs-step-amendment");
    expect(amendments.map((node) => node.textContent)).toEqual([
      expect.stringMatching(/^Added by you · \d\d:\d\d · typed at \d\d:\d\dKeep the 14-day rule$/),
      expect.stringMatching(/^Added by you · \d\d:\d\d · waits for the next turnUse the new index$/),
    ]);
    expect(within(fold).getByTestId("programs-frozen-owns").getAttribute("title")).toBe(runner.frozen!.owns);
    expect(within(fold).getByTestId("programs-frozen-effort").getAttribute("title")).toBe("The worktree and the agent are set");
    expect(within(within(fold).getByTestId("programs-step-frozen")).getByText("Frozen · the agent has read it").getAttribute("title")).toBe("The agent has read it");
    // No Move or Insert on a started step; Amend brief and Hand off.
    expect(within(fold).queryByTestId("programs-step-up")).toBeNull();
    expect(within(fold).getByTestId("programs-step-hand-off")).toBeTruthy();
    fireEvent.change(within(fold).getByRole("textbox", { name: "Add to the brief" }), { target: { value: "Log each turn" } });
    fireEvent.click(within(fold).getByTestId("programs-step-amend-send"));
    await waitFor(() => expect(within(screen.getByTestId("programs-step-fold")).getAllByTestId("programs-step-amendment")).toHaveLength(3));
    expect(calls).toContain(`POST /api/programs/${adjust.id}/steps/${runner.id}/amend ${JSON.stringify({ line: "Log each turn" })}`);
  });

  it("a planned step: its fields in place; Move up and Insert before press through and the board follows the hub's order", async () => {
    const third = adjust.steps.find((step) => step.ordinal === 3)!;
    const second = adjust.steps.find((step) => step.ordinal === 2)!;
    const fourth = adjust.steps.find((step) => step.ordinal === 4)!;
    hub({
      [`GET /api/programs/${adjust.id}`]: adjust,
      [`PATCH /api/programs/${adjust.id}/steps/${third.id}`]: movedFixture,
      [`POST /api/programs/${adjust.id}/plan`]: insertedFixture,
    });
    render(<ProgramBody programId={adjust.id} />);
    await screen.findByTestId("programs-board");
    const titles = () => screen.getAllByTestId("programs-step").map((row) => row.querySelector(".pg-step-name")!.textContent);
    expect(titles()).toEqual(["The call runner", "The phone route", "The calls window", "The loop watch", "The ring timer"]);
    fireEvent.click(within(stepRow(3)).getByTestId("programs-step-select"));
    const fold = await screen.findByTestId("programs-step-fold");
    expect(within(fold).getByTestId("programs-step-brief").hasAttribute("data-planned")).toBe(true);
    expect((within(fold).getByRole("textbox", { name: "Step 3 title" }) as HTMLInputElement).value).toBe(third.title);
    fireEvent.click(within(fold).getByTestId("programs-step-up"));
    await waitFor(() => expect(titles()).toEqual(["The call runner", "The calls window", "The phone route", "The loop watch", "The ring timer"]));
    expect(calls).toContain(`PATCH /api/programs/${adjust.id}/steps/${third.id} ${JSON.stringify({ before: second.id })}`);
    // Insert before the loop watch: a new Planned step at its place; "4 waits" is on.
    fireEvent.click(within(stepRow(4)).getByTestId("programs-step-select"));
    await waitFor(() => expect(screen.getByTestId("programs-step-fold").getAttribute("data-step")).toBe(fourth.id));
    fireEvent.click(screen.getByTestId("programs-step-insert-before"));
    const insert = screen.getByTestId("programs-step-insert");
    expect((within(insert).getByRole("checkbox", { name: "4 waits" }) as HTMLInputElement).checked).toBe(true);
    fireEvent.change(within(insert).getByRole("textbox", { name: "The new step's title" }), { target: { value: "The retry" } });
    expect(within(insert).getByTestId("programs-step-insert-send").textContent).toBe("Insert as step 4");
    fireEvent.click(within(insert).getByTestId("programs-step-insert-send"));
    await waitFor(() => expect(titles()).toEqual(["The call runner", "The calls window", "The phone route", "The retry", "The loop watch", "The ring timer"]));
    expect(calls.find((call) => call.startsWith(`POST /api/programs/${adjust.id}/plan`))).toContain(`"before":"${fourth.id}","waits":true`);
    expect(within(stepRow(5)).getByTestId("programs-step-select").textContent).toContain("after 1, 4");
  });

  it("a planned step's title saves on blur; a move above a step it comes after is refused before it is sent", async () => {
    const ring = adjust.steps.find((step) => step.ordinal === 5)!;
    hub({
      [`GET /api/programs/${adjust.id}`]: adjust,
      [`PATCH /api/programs/${adjust.id}/steps/${ring.id}`]: titledFixture,
    });
    render(<ProgramBody programId={adjust.id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(within(stepRow(5)).getByTestId("programs-step-select"));
    const fold = await screen.findByTestId("programs-step-fold");
    // The ring timer comes after step 4: Move up is refused with its reason, nothing is sent.
    fireEvent.click(within(fold).getByTestId("programs-step-up"));
    expect((await within(fold).findByTestId("programs-step-failure")).textContent).toBe("Step 5 comes after step 4 · It keeps its place");
    expect(calls.some((call) => call.startsWith("PATCH"))).toBe(false);
    const title = within(fold).getByRole("textbox", { name: "Step 5 title" });
    fireEvent.change(title, { target: { value: "The ring timer, ten minutes" } });
    fireEvent.blur(title);
    await waitFor(() => expect(screen.getAllByTestId("programs-step").map((row) => row.querySelector(".pg-step-name")!.textContent))
      .toContain("The ring timer, ten minutes"));
    expect(calls).toContain(`PATCH /api/programs/${adjust.id}/steps/${ring.id} ${JSON.stringify({ title: "The ring timer, ten minutes" })}`);
  });
});

describe("REQ12: the shot (pullout:program-shot) and the evidence thumbnail", () => {
  it("the selected Shot row draws its thumbnail from the evidence route; Open shot opens the shot's own window", async () => {
    const r2 = allRequirements(reqProgram).find((row) => row.label === "R2")!;
    mocks.apiBlob.mockResolvedValue(new Blob(["png"], { type: evidenceFixture.shot.type }));
    const made = vi.fn(() => "blob:shot-r2");
    Object.assign(URL, { createObjectURL: made, revokeObjectURL: vi.fn() });
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-requirements");
    fireEvent.click(within(reqRow("R2")).getByTestId("programs-req-select"));
    const thumb = await within(reqRow("R2")).findByTestId("programs-req-thumb");
    expect(thumb.getAttribute("src")).toBe("blob:shot-r2");
    expect(thumb.getAttribute("width")).toBe("240");
    expect(mocks.apiBlob).toHaveBeenCalledWith(r2.evidence.url);
    const { useDesk } = await import("../../store");
    fireEvent.click(within(reqRow("R2")).getByTestId("programs-req-open-shot"));
    expect(useDesk.getState().pullouts.map((pullout) => pullout.id)).toContain(`program-shot:${reqProgram.id}:${r2.id}`);
  });

  it("the shot window: the image whole, its state, the step and the commit in the status bar", async () => {
    const r2 = allRequirements(reqProgram).find((row) => row.label === "R2")!;
    mocks.apiBlob.mockResolvedValue(new Blob(["png"], { type: "image/png" }));
    Object.assign(URL, { createObjectURL: vi.fn(() => "blob:shot-window"), revokeObjectURL: vi.fn() });
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    const { ProgramShotBody } = await import("../ProgramShot");
    render(<ProgramShotBody id={`${reqProgram.id}:${r2.id}`} />);
    const image = await screen.findByTestId("program-shot-image");
    expect(image.getAttribute("src")).toBe("blob:shot-window");
    const bar = screen.getByTestId("program-shot-status").textContent!;
    expect(bar).toContain("Met");
    expect(bar).toContain("Step 1 · Indexes");
    expect(bar).toContain(`on ${r2.evidence.commit!.slice(0, 7)}`);
    fireEvent.click(screen.getByTestId("program-shot-open-program"));
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${reqProgram.id}`);
  });
});

describe("LANG2: the Text view beside the board, the change well and diff rows (PROGRAM-LANGUAGE §9.1, §9.2, §14)", () => {
  type Answer = import("../types").TextApplyAnswer;
  const dry = textApplyFixture.dry_run as unknown as Answer;
  const done = textApplyFixture.applied as unknown as Answer;
  const after = done.program as Program;
  // The recorded Program before the apply: the applied wire with the apply's
  // own writes taken back (the new step, the + line, the control, the ledger
  // lines of the apply). Its id, steps and states are the recorded ones.
  const before = (() => {
    const program = clone(after);
    program.steps = program.steps.filter((step) => step.title !== "The loop watch")
      .map((step, index) => ({ ...step, ordinal: index + 1, amendments: [] }));
    program.control = "normal";
    program.control_word = "Normal";
    program.total = 3;
    program.revision = textFixture.revision;
    program.checkpoints = program.checkpoints.filter((row) => Number(row.id) <= 10);
    program.status_line = "Running · 0 of 3 done · check: fake_program_check.sh · control Normal";
    return program;
  })();
  const id = before.id;
  const posts = () => calls.filter((call) => call.startsWith(`POST /api/programs/${id}/text`))
    .map((call) => JSON.parse(call.slice(call.indexOf("{"))) as Record<string, unknown>);
  const line = (n: number) => screen.getByRole("textbox", { name: `Program text, line ${n}` }) as HTMLTextAreaElement;
  // Read from the recorded answers, so a re-record moves these with it.
  const controlLine = textFixture.text.split("\n").indexOf("  control normal") + 1;
  const refusedRow = dry.changes.find((row) => row.id === "step-2.brief")!;
  const blocked = (rows: Answer["changes"]) => rows.filter((row) => row.verdict === "refused" || row.verdict === "conflict").length;
  const applyWords = (rows: Answer["changes"]) => `Apply ${rows.length - blocked(rows)}`;
  const ledgerLine = after.checkpoints.find((row) => String(row.line).startsWith("Changed by the text: "))!.line as string;

  async function openText() {
    hub({
      [`GET /api/programs/${id}`]: before,
      [`GET /api/programs/${id}/text`]: textFixture,
      [`POST /api/programs/${id}/text`]: (init?: { json?: unknown }) => ((init?.json as { dry_run?: boolean })?.dry_run === false ? done : dry),
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(within(screen.getByRole("group", { name: "View" })).getByRole("button", { name: "Text" }));
    await screen.findByTestId("programs-text");
  }

  it("Text: the recorded text in the pane, each lamp at its line end (never in the line), the pick kept for this window", async () => {
    await openText();
    const { useDesk } = await import("../../store");
    expect(useDesk.getState().places[`program/view/${id}`]).toBe("text");
    expect(screen.queryByTestId("programs-board")).toBeNull();
    const lines = screen.getAllByTestId("kit-textpane-line");
    expect(lines).toHaveLength(textFixture.text.split("\n").length);
    expect(lines[0]).toHaveAttribute("data-readonly");
    expect(line(2).value).toBe("program The hub stops stalling");
    expect(lines[1].querySelector(".kit-textpane-lamp")?.textContent).toBe("Running · 0 of 3 done");
    expect(lines[1].querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("info");
    // Step 3 is Planned: the grey dot; his > lines read in the body face.
    const fanOut = lines.find((row) => row.querySelector("textarea")?.value === "step 3 The fan-out")!;
    expect(fanOut.querySelector(".kit-textpane-lamp")?.textContent).toBe("Planned");
    expect(lines[3]).toHaveAttribute("data-words");
    // Nothing changed: no Preview.
    expect(screen.queryByTestId("program-text-preview")).toBeNull();
  });

  it("edit, Preview: the recorded rows in the well (the refused one with its line and reason, the one that lowers the bar); Apply waits for its own press", async () => {
    await openText();
    fireEvent.change(line(controlLine), { target: { value: "  control yolo" } });
    expect(screen.getAllByTestId("kit-textpane-line")[controlLine - 1]).toHaveAttribute("data-mark", "~");
    fireEvent.click(screen.getByTestId("program-text-preview"));
    const well = await screen.findByTestId("programs-change-well");
    const sent = posts()[0];
    expect(sent.dry_run).toBe(true);
    expect(sent.base).toBe(textFixture.text);
    expect(sent.text).toContain("  control yolo");
    expect(sent.text).not.toContain("# Running");
    const rows = within(well).getAllByTestId("programs-diff-row");
    expect(rows).toHaveLength(dry.changes.length);
    const refused = rows.find((row) => row.getAttribute("data-row") === "step-2.brief")!;
    expect(within(refused).getByTestId("kit-diffrow-verdict").textContent).toBe("Refused");
    expect(within(refused).getByTestId("kit-diffrow-reason").textContent).toBe(`Line ${refusedRow.line}${refusedRow.reason}`);
    expect(refusedRow.reason).toBe("Step 2 · brief: The agent has read it. Add a line with + instead.");
    const lowers = rows.find((row) => row.getAttribute("data-row") === "program.control")!;
    expect(within(lowers).getByTestId("kit-diffrow-verdict").textContent).toBe("Lowers the bar");
    const lowering = dry.changes.filter((row) => row.verdict === "lowers").length;
    expect(within(well).getByText(`${dry.changes.length} changes · ${blocked(dry.changes)} refused · ${lowering} lowers the bar`)).toBeInTheDocument();
    // The refused line is marked in the text, its reason as the title.
    expect(screen.getAllByTestId("kit-textpane-line")[refusedRow.line - 1]).toHaveAttribute("data-mark", "!");
    const apply = within(well).getByTestId("programs-well-apply");
    expect(apply.textContent).toBe(applyWords(dry.changes));
    expect(apply).toBeDisabled();
    fireEvent.click(within(lowers).getByRole("button", { name: "Apply this" }));
    expect(within(lowers).getByTestId("kit-diffrow-verdict").textContent).toBe("Allowed by you");
    expect(apply).toBeEnabled();
  });

  it("Apply sends the allowed text and only the row he pressed; the board comes back with the new step, YOLO, and the ledger line", async () => {
    await openText();
    fireEvent.change(line(controlLine), { target: { value: "  control yolo" } });
    fireEvent.click(screen.getByTestId("program-text-preview"));
    const well = await screen.findByTestId("programs-change-well");
    const lowers = within(well).getAllByTestId("programs-diff-row").find((row) => row.getAttribute("data-row") === "program.control")!;
    fireEvent.click(within(lowers).getByRole("button", { name: "Apply this" }));
    fireEvent.click(within(well).getByTestId("programs-well-apply"));
    await screen.findByTestId("programs-board");
    const sent = posts()[1];
    expect(sent).toEqual({ text: dry.allowed_text, base: textFixture.text, dry_run: false, allow_lower: ["program.control"] });
    // The rows landed: the new step on the board, in its place, marked born.
    const born = stepRow(3);
    expect(within(born).getByTestId("programs-step-select").textContent).toContain("The loop watch");
    expect(born).toHaveAttribute("data-landed", "born");
    expect(stepRow(4)).toHaveAttribute("data-landed", "changed");
    expect(within(status()).getByTestId("programs-status-control").textContent).toBe("control YOLO");
    expect(within(screen.getByTestId("programs-checkpoints")).getByText(ledgerLine)).toBeInTheDocument();
    const { useDesk } = await import("../../store");
    expect(useDesk.getState().places[`program/view/${id}`] ?? "").toBe("");
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
  });

  it("Not this closes the well and puts the text back as it was read", async () => {
    await openText();
    fireEvent.change(line(controlLine), { target: { value: "  control yolo" } });
    fireEvent.click(screen.getByTestId("program-text-preview"));
    const well = await screen.findByTestId("programs-change-well");
    fireEvent.click(within(well).getByTestId("programs-well-not-this"));
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    expect(line(controlLine).value).toBe("  control normal");
    expect(posts()).toHaveLength(1);
  });

  it("a conflict (the base moved) reads the text again and says so", async () => {
    // The recorded preview with its agent row as the hub words a conflict
    // (program_service.text_apply: verdict conflict, code text_conflict).
    const conflict = clone(dry);
    conflict.changes = conflict.changes.map((row) => (row.id === "step-3.merge"
      ? { ...row, verdict: "conflict" as const, code: "text_conflict", reason: "Step 3's merge changed since you read it: now owner." } : row));
    await openText();
    const read = calls.length;
    hub({
      [`GET /api/programs/${id}`]: before,
      [`GET /api/programs/${id}/text`]: textFixture,
      [`POST /api/programs/${id}/text`]: conflict,
    });
    fireEvent.change(line(controlLine), { target: { value: "  control yolo" } });
    fireEvent.click(screen.getByTestId("program-text-preview"));
    const well = await screen.findByTestId("programs-change-well");
    expect(within(well).getByText("Changed since you read it", { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(within(well).getByText(/^Read again at /)).toBeInTheDocument();
    expect(calls.slice(read).filter((call) => call === `GET /api/programs/${id}/text`)).toHaveLength(1);
    expect(within(well).getByTestId("programs-well-apply").textContent).toBe(applyWords(conflict.changes));
    // His text is kept.
    expect(line(controlLine).value).toBe("  control yolo");
  });

  it("at 393 the view switch is in More ▾", async () => {
    hub({ [`GET /api/programs/${id}`]: before, [`GET /api/programs/${id}/text`]: textFixture });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    fireEvent.click(screen.getByTestId("program-more"));
    fireEvent.click(await screen.findByRole("menuitem", { name: "Text" }));
    await screen.findByTestId("programs-text");
  });
});


describe("LANG4: shaping by a typed sentence (PROGRAM-LANGUAGE §4, §9.2, §14)", () => {
  type Shape = import("../types").ShapeAnswer;
  type Applied = import("../types").TextApplyAnswer;
  const normal = shapeFixture.normal as unknown as { program: Program; shape: Shape; applied: Applied };
  const yolo = shapeFixture.yolo as unknown as { program: Program; shape: Shape; overturned: { program: Program } };
  const none = shapeFixture.no_engine as unknown as { program: Program; status: number; body: Record<string, unknown>; engine: unknown };
  const question = shapeFixture.question as unknown as Shape;
  const posts = (id: string, tail: string) => calls.filter((call) => call.startsWith(`POST /api/programs/${id}/${tail}`))
    .map((call) => JSON.parse(call.slice(call.indexOf("{"))) as Record<string, unknown>);
  const bar = () => screen.getByTestId("program-shape-bar");
  const say = (words: string) => {
    fireEvent.change(within(bar()).getByRole("textbox", { name: "Change the program" }), { target: { value: words } });
    fireEvent.click(within(bar()).getByTestId("program-shape"));
  };

  it("a typed sentence: the engine's rows in the well with its words, name and time; the row that lowers the bar waits; Apply lands the new step", async () => {
    const id = normal.program.id;
    hub({
      [`GET /api/programs/${id}`]: normal.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: normal.shape,
      [`POST /api/programs/${id}/text`]: normal.applied,
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    say(normal.shape.sentence);
    const well = await screen.findByTestId("programs-change-well");
    // Normal: nothing applies at once.
    expect(posts(id, "shape")[0]).toEqual({ sentence: normal.shape.sentence, apply: false });
    expect(within(well).getByText(normal.shape.say, { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(within(well).getByText(/^qwen3\.8-27b · under 1 s · 5 changes · 1 lowers the bar$/)).toBeInTheDocument();
    const rows = within(well).getAllByTestId("programs-diff-row");
    expect(rows.map((row) => row.getAttribute("data-row"))).toEqual(normal.shape.changes.map((row) => row.id));
    const control = rows.find((row) => row.getAttribute("data-row") === "program.control")!;
    expect(within(control).getByTestId("kit-diffrow-verdict").textContent).toBe("Lowers the bar");
    const apply = within(well).getByTestId("programs-well-apply");
    expect(apply).toBeDisabled();
    fireEvent.click(within(control).getByRole("button", { name: "Apply this" }));
    fireEvent.click(apply);
    await waitFor(() => expect(posts(id, "text")).toHaveLength(1));
    expect(posts(id, "text")[0]).toEqual({ text: normal.shape.proposed_text, base: normal.shape.base, dry_run: false,
      allow_lower: ["program.control"] });
    // The rows landed: the Program is in Drafting, so the board is its
    // draft rows; the loop watch is step 3, before the fan-out.
    await waitFor(() => expect((screen.getByRole("textbox", { name: "Step 3 title" }) as HTMLInputElement).value).toBe("Loop watch"));
    expect((screen.getByRole("textbox", { name: "Step 4 title" }) as HTMLInputElement).value).toBe("The fan-out");
    expect(within(status()).getByTestId("programs-status-control").textContent).toBe("control YOLO");
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
    // The bar is empty again, ready for the next sentence.
    expect((within(bar()).getByRole("textbox", { name: "Change the program" }) as HTMLInputElement).value).toBe("");
  });

  it("while the engine reads, the bar names it with a breathing lamp", async () => {
    const id = normal.program.id;
    let answer: (value: unknown) => void = () => undefined;
    hub({
      [`GET /api/programs/${id}`]: normal.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
    });
    const table = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path: string, init?: { method?: string; json?: unknown }) =>
      (init?.method === "POST" && path.endsWith("/shape") ? new Promise((resolve) => { answer = resolve; }) : table(path, init)));
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    say("put step 2 on Codex");
    const reading = await screen.findByTestId("program-shape-reading");
    await waitFor(() => expect(reading.textContent).toBe("Reading the program · Home Engine"));
    expect(reading.querySelector(".kit-dot")).toHaveAttribute("data-live");
    // The window stays usable: the board is there.
    expect(screen.getByTestId("programs-board")).toBeInTheDocument();
    await act(async () => answer(clone(normal.shape)));
    await screen.findByTestId("programs-change-well");
    expect(screen.queryByTestId("program-shape-reading")).toBeNull();
  });

  it("at YOLO the allowed row lands at once with Overturn; the row that lowers the bar still waits in the well", async () => {
    const id = yolo.program.id;
    hub({
      [`GET /api/programs/${id}`]: yolo.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: yolo.shape,
      [`POST /api/programs/${id}/decisions/${yolo.shape.decision!.id}/overturn`]: yolo.overturned,
      [`GET /api/programs/${id}/text`]: { program_id: id, text: yolo.shape.text, revision: yolo.shape.revision, version: 1 },
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    say(yolo.shape.sentence);
    const shaped = await screen.findByTestId("programs-shaped-well");
    expect(posts(id, "shape")[0]).toEqual({ sentence: yolo.shape.sentence, apply: true });
    expect(within(shaped).getByText(`Shaped: ${yolo.shape.say}`)).toBeInTheDocument();
    expect(within(shaped).getAllByTestId("programs-shaped-row").map((row) => row.getAttribute("data-row"))).toEqual(["step-1.agents"]);
    const waiting = screen.getByTestId("programs-change-well");
    const depth = within(waiting).getAllByTestId("programs-diff-row");
    expect(depth.map((row) => row.getAttribute("data-row"))).toEqual(["step-1.depth"]);
    expect(within(depth[0]).getByTestId("kit-diffrow-verdict").textContent).toBe("Lowers the bar");
    // The hub wrote the Decided for you row Overturn reads.
    expect(yolo.shape.program!.decided_for_you!.at(-1)!.line).toMatch(/^Shaped by a sentence: /);
    fireEvent.click(within(shaped).getByTestId("programs-shaped-overturn"));
    await waitFor(() => expect(screen.queryByTestId("programs-shaped-well")).toBeNull());
    expect(calls).toContain(`POST /api/programs/${id}/decisions/${yolo.shape.decision!.id}/overturn {}`);
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
  });

  it("no engine: the refusal in place of the lamp, with Open Engines and Open text; nothing is guessed", async () => {
    const id = none.program.id;
    hub({
      [`GET /api/programs/${id}`]: none.program,
      [`GET /api/programs/${id}/shape`]: none.engine,
      [`POST /api/programs/${id}/shape`]: () => { throw new ApiError(none.status, String(none.body.detail), none.body); },
      [`GET /api/programs/${id}/text`]: { program_id: id, text: normal.shape.base, revision: 1, version: 1 },
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    say("put step 2 on Codex");
    const refusal = await screen.findByTestId("program-shape-refusal");
    // The hub said no engine shapes here: the sentence is not sent.
    expect(posts(id, "shape")).toHaveLength(0);
    expect(refusal.textContent).toContain("No engine is set for planning");
    expect(refusal).toHaveAttribute("title", "No engine is set for planning. The program is unchanged. Choose one in Engines.");
    // The sentence is kept.
    expect((within(bar()).getByRole("textbox", { name: "Change the program" }) as HTMLInputElement).value).toBe("put step 2 on Codex");
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    fireEvent.click(within(refusal).getByTestId("program-shape-engines"));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
    fireEvent.click(within(refusal).getByTestId("program-shape-text"));
    await screen.findByTestId("programs-text");
  });

  it("a question back is one line; his next sentence answers it, sent with the first one", async () => {
    const id = yolo.program.id;
    hub({
      [`GET /api/programs/${id}`]: yolo.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: question,
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    say(question.sentence);
    const asked = await screen.findByTestId("program-shape-question");
    expect(asked.textContent).toBe(question.question);
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    say("step 3 before step 2");
    await waitFor(() => expect(posts(id, "shape")).toHaveLength(2));
    expect(posts(id, "shape")[1]).toEqual({ sentence: `${question.sentence} step 3 before step 2`, apply: true });
  });
});

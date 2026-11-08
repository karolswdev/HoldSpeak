/* The Programs app (T2), the Programs on the rest of the desk: the Needs you
 * rows, the Room, a Person, Agents, Today, the Dock and the Note.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  needsFixture, roomFixture, personFixture, skipDecisionFixture, roomProposedFixture,
  sinceMorningPrograms, mocks, ProgramBody, RoomPrograms, RoomDecisions, decodeRoomSnapshot,
  PersonPrograms, personProgramsOf, ProgramStepLine, flightProgramOf, programsLampOf,
  programsTodayLine, worseLamp, runNoteAsProgram, needFace, list, running, done, drafting, calls,
  hub, type NeedsYouRoomItem, type Program, type RoomProgram,
} from "./programs.test-setup";
import { describe, expect, it } from "vitest";
import { fireEvent, render, screen, within } from "@testing-library/react";

describe("the seams", () => {
  it("Needs you: a recorded Program row is a decide row with its verbs and its Program group", () => {
    const item = (needsFixture as { items: NeedsYouRoomItem[] }).items[0];
    const face = needFace({ ref: String(item.ref), kind: "attention", item } as never, { now: new Date(), sessions: [], flights: [] } as never);
    expect(face.kind).toBe("program");
    expect(face.direction).toBe("decide");
    // The step travels: the row opens the Program at its step.
    const named = item.program as { programId: string; stepId: string };
    expect(face.openRef).toBe(`program:${named.programId}:${named.stepId}`);
    // #1854: the row is the Program (its title), the quiet word Decide and
    // one verb Decide; the choices are its context menu, each still pressed
    // on the step's decide route.
    expect(face.name).toBe("The words wave");
    expect(face.name).toBe(String(item.group));
    expect(face.lamp.label).toBe("Decide");
    expect(face.verbs).toMatchObject({ kind: "program", ask: "decide", choices: ["fix_now", "later", "skip"], itemKind: "finding", findingId: "f1" });
    expect((face.verbs as { decide: string }).decide).toMatch(/\/steps\/step-[0-9a-f]+\/decide$/);
  });

  it("the Room's Programs fold: one row per recorded Program, its state word and the list's step dots", () => {
    render(<RoomPrograms programs={roomFixture.programs as RoomProgram[]} />);
    const rows = screen.getAllByTestId("room-program-row");
    expect(rows).toHaveLength(roomFixture.programs.length);
    expect(rows[0].textContent).toContain(roomFixture.programs[0].state_word);
    const track = within(rows[0]).getByTestId("room-program-track");
    expect(track.getAttribute("aria-label")).toBe("0 of 3 done");
    expect(track.querySelectorAll(".pg-station")).toHaveLength(roomFixture.programs[0].track.length);
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

describe("PG16: decisions from a Program (the recorded Skip)", () => {
  const skipped = skipDecisionFixture as unknown as Program;

  it("the checkpoint row of his Skip says Proposed as a decision; an overturned row does not", async () => {
    hub({ [`GET /api/programs/${skipped.id}`]: skipped });
    render(<ProgramBody programId={skipped.id} />);
    const checks = await screen.findByTestId("programs-checkpoints");
    const rows = within(checks).getAllByRole("listitem");
    const skip = rows.find((row) => row.textContent?.startsWith("You") && row.textContent.includes("Skip: sentence case the title"))!;
    const proposed = within(skip).getByTestId("programs-proposed-decision");
    expect(proposed.textContent).toBe("Proposed as a decision");
    // One press opens the record in the Decisions window.
    const record = skipped.checkpoints.find((row) => row.by === "owner" && row.line.includes("Skip: sentence case the title"))!.decision_record_id;
    fireEvent.click(proposed);
    expect(mocks.openDecisionRecord).toHaveBeenCalledWith(record);
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

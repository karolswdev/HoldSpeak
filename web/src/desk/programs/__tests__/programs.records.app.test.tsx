import { useState } from "react";
import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  roomFixture,
  personFixture,
  roomProposedFixture,
  skipDecisionFixture,
  sinceMorningPrograms,
  needsFixture,
  pageNoneFixture,
  pageOpenFixture,
  reachPackageFixture,
  reachRevokedFixture,
  running,
  done,
  drafting,
  list,
  limited,
  historyFixture,
  familyFixture,
  auditBoardFixture,
  startFromFixture,
  mocks,
  hub,
  clone,
  ProgramsCore,
  RoomPrograms,
  PersonPrograms,
  RoomDecisions,
  ProgramStepLine,
  flightProgramOf,
  programsLampOf,
  programsTodayLine,
  worseLamp,
  runNoteAsProgram,
  needFace,
  type Program,
  type RoomProgram,
  type NeedsYouRoomItem,
} from "./programs.seats.test-setup";
import { ProgramLedger } from "../Ledger";
import {
  ProgramContext,
  ProgramHandoffs,
  ProgramRace,
} from "../ProgramRecords";
import { ProgramBriefing } from "../ProgramBriefing";
const tab = (name: string) =>
  fireEvent.click(screen.getByRole("tab", { name }));
const press = (name: string) =>
  fireEvent.click(screen.getByRole("button", { name }));
const pick = (grid: string, id: string) =>
  fireEvent.click(
    screen
      .getByRole("grid", { name: grid })
      .querySelector(`[data-object-id="${id}"]`)!,
  );
const props = { onApplied: vi.fn(), onError: vi.fn() };
describe("The Programs companion seats", () => {
  it("Room Programs keeps the recorded progress and opens the selected program by Return", () => {
    render(<RoomPrograms programs={roomFixture.programs as RoomProgram[]} />);
    const grid = screen.getByRole("grid", { name: "Programs" });
    const row = grid.querySelector(
      `[data-object-id="${roomFixture.programs[0].id}"]`,
    )!;
    fireEvent.click(row);
    expect(row.querySelector(".surface-meter")).toBeTruthy();
    fireEvent.keyDown(row, { key: "Enter" });
    expect(mocks.openPullout).toHaveBeenCalledWith(
      `program:${roomFixture.programs[0].id}`,
    );
  });
  it("People keeps Programs, To show them and To ask in the same list", () => {
    render(
      <PersonPrograms
        programs={personFixture.programs as never}
        name="Alice"
      />,
    );
    const grid = screen.getByRole("grid", { name: "Programs" });
    expect(
      within(grid).getByRole("rowgroup", { name: "To show them" }).textContent,
    ).toContain("Indexes");
    expect(grid.textContent).toContain("Merged #101");
  });
  it("Agents names the step and opens the same Programs window", async () => {
    render(
      <ProgramStepLine
        program={flightProgramOf({
          id: running.id,
          title: running.title,
          step_id: running.steps[3].id,
          step_ordinal: 4,
        })}
      />,
    );
    press(`Step 4 of ${running.title}`);
    await waitFor(() =>
      expect(mocks.openPullout).toHaveBeenCalledWith(`program:${running.id}`),
    );
  });
  it("Today and the Dock keep their recorded facts", () => {
    const block = (sinceMorningPrograms as any)["/api/today/since-morning"]
      .programs;
    expect(programsTodayLine(block)).toBe(
      "Programs: 1 running, 1 waits on you, 1 PR merged",
    );
    expect(programsTodayLine(null)).toBe("");
    expect(
      worseLamp("work", programsLampOf(list.worst, list.counts).lamp),
    ).toBe("ask");
  });
  it("Needs you keeps the exact step and the finding id", () => {
    const item = (needsFixture as { items: NeedsYouRoomItem[] }).items[0];
    const face = needFace(
      { ref: String(item.ref), kind: "attention", item } as never,
      { now: new Date(), sessions: [], flights: [] } as never,
    );
    expect(face.verbs).toMatchObject({
      kind: "program",
      findingId: "f1",
      choices: ["fix_now", "later", "skip"],
    });
    expect(face.openRef).toContain((item.program as { stepId: string }).stepId);
  });
  it("a note still creates and opens its program with the origin attached", async () => {
    hub({ "POST /api/programs": drafting });
    expect(
      await runNoteAsProgram({
        id: "n1",
        title: "A note",
        body: "Keep the note.",
        projectId: "proj-holdspeak",
      }),
    ).toBeNull();
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      "/api/programs",
      expect.objectContaining({
        json: expect.objectContaining({ origin_ref: "note:n1" }),
      }),
    );
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${drafting.id}`);
  });
  it("Room decisions select and open the recorded decision; an empty group draws nothing", () => {
    const { rerender, container } = render(
      <RoomDecisions proposed={roomProposedFixture.proposed as never} />,
    );
    const grid = screen.getByRole("grid", { name: "Proposed decisions" });
    const row = grid.querySelector(
      `[data-object-id="${roomProposedFixture.proposed[0].id}"]`,
    )!;
    fireEvent.click(row);
    press("Open decision");
    expect(mocks.openDecisionRecord).toHaveBeenCalledWith(
      roomProposedFixture.proposed[0].id,
    );
    rerender(<RoomDecisions proposed={[]} />);
    expect(container.textContent).toBe("");
  });
});
describe("Ledger, context and handoff readers", () => {
  it("a proposed decision opens its Decisions record from the selected checkpoint", () => {
    const p = skipDecisionFixture as unknown as Program;
    render(<ProgramLedger program={p} {...props} />);
    const cp = p.checkpoints.find(
      (cp) => cp.decision_record_id && !cp.overturned_at,
    )!;
    pick("Program ledger", String(cp.id));
    expect(screen.getByText("Proposed as a decision")).toBeTruthy();
    press("Open decision");
    expect(mocks.openDecisionRecord).toHaveBeenCalledWith(
      cp.decision_record_id,
    );
  });
  it("a finding opens its Door task and keeps the evidence in facts", () => {
    const p = auditBoardFixture as unknown as Program;
    render(<ProgramLedger program={p} {...props} />);
    tab("Findings");
    const row = p.findings_board!.rows.find((row) => row.task_id)!;
    pick("Program ledger", row.key);
    press("Open Door task");
    expect(mocks.openRef).toHaveBeenCalledWith(`action:${row.task_id}`);
    expect(screen.getByText(row.evidence.join(" · "))).toBeTruthy();
  });
  it("family rows open the selected parent or child", () => {
    const p = familyFixture.program as unknown as Program;
    render(<ProgramLedger program={p} {...props} />);
    tab("Family");
    const family = [p.family?.parent, ...(p.family?.children ?? [])].find(
      Boolean,
    )!;
    pick("Program ledger", family.id);
    press("Open program");
    expect(mocks.openRef).toHaveBeenCalledWith(`program:${family.id}`);
  });
  it("a handoff reader shows redaction, earlier turns, continuation and the redacted brief", () => {
    const p = limited;
    const step = p.steps.find((s) => s.handoffs?.length)!;
    render(<ProgramHandoffs program={p} step={step} />);
    const row = step.handoffs![0];
    tab("Facts");
    expect(screen.getByText(row.redacted_words || "Nothing redacted")).toBeTruthy();
    tab("Brief");
    expect(
      screen.getByRole("group", { name: "Handoff brief" }),
    ).toHaveAttribute("data-feedback-redact", "true");
    expect(
      screen.getByRole("group", { name: "Handoff brief" }).textContent,
    ).toContain(row.brief.split("\n").find(Boolean));
  });
  it("Context opens its selected Door without a second program window", () => {
    render(<ProgramContext program={running} onError={() => {}} />);
    const id = running.place.project
      ? `project:${running.place.project.id}`
      : running.place.origin!.ref;
    pick("Context doors", id);
    press("Open context");
    expect(mocks.openRef).toHaveBeenCalledWith(id);
  });
  it("Copy page link uses the held item's ref; Revoke asks and leaves the question held", async () => {
    const p = pageNoneFixture as unknown as Program;
    const item = p.your_turn_items[0];
    hub({
      "POST /api/reach/packages": reachPackageFixture,
      [`POST /api/reach/packages/${reachPackageFixture.id}/revoke`]:
        reachRevokedFixture,
    });
    Object.assign(navigator, {
      clipboard: { writeText: vi.fn().mockResolvedValue(undefined) },
    });
    render(<ProgramBriefing program={p} item={item} onError={() => {}} />);
    press("Copy page link");
    await screen.findByRole("button", { name: "Revoke link" });
    expect(navigator.clipboard.writeText).toHaveBeenCalledWith(
      expect.stringContaining("/b/"),
    );
    press("Revoke link");
    expect(screen.getByRole("button", { name: "Cancel" })).toBeTruthy();
    fireEvent.click(
      within(document.querySelector<HTMLElement>("[data-question]")!).getByRole(
        "button",
        { name: "Revoke link" },
      ),
    );
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Revoke link" })).toBeNull(),
    );
    expect(p.your_turn_items).toContain(item);
  });
});

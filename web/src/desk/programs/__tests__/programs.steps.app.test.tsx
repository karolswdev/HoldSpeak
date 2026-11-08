/* The Programs app (T2), the steps of a Program: the requirements, the step
 * fold, the step report, the to-do, the wait and the lane.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  sendBackFixture, waivedFixture, waiveRefusedFixture, addedFixture, evidenceFixture, wordFixture,
  wordMetFixture, needsRequirementsFixture, movedFixture, insertedFixture, amendedFixture,
  titledFixture, proposalsFixture, proposalsAddedFixture, deliveryMergeFixture, todoFixture,
  todoDoneFixture, laneFixture, laneTakenFixture, laneBackFixture, mocks, ApiError, ProgramsCore,
  ProgramBody, needFace, useDesk, list, done, calls, hub, status, stepRow, openStep, doneWhen,
  reqProgram, adjust, reqRow, allRequirements, decidePath, type Answered, type NeedsYouRoomItem,
  type Program,
} from "./programs.test-setup";
import { describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

describe("REQ10: the Requirements board (direction A, the checklist)", () => {
  it("PG-WINDOW: each step carries its own as lines with a lamp; Done when holds the program's own and the every-step ones", async () => {
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-board");
    const met = reqProgram.requirements_met!;
    // No board above the steps: Done when is the last row.
    expect(screen.queryByTestId("programs-requirements-board")).toBeNull();
    const done = doneWhen();
    expect(within(done).getAllByTestId("programs-req").map((row) => row.getAttribute("data-label"))).toEqual(["R1", "R7", "R8"]);
    expect(done.textContent).toContain("judged after the last step");
    const inDone = (label: string) => within(done).getAllByTestId("programs-req").find((row) => row.getAttribute("data-label") === label)!;
    // Every step: six dots and "4 of 6 steps"; the Program's own: after the last step.
    const every = allRequirements(reqProgram).find((row) => row.scope === "every_step")!;
    expect(inDone("R1").querySelectorAll(".pg-req-dot")).toHaveLength(6);
    const metCopies = every.steps!.filter((copy) => copy.state === "met" || copy.state === "waived").length;
    expect(within(inDone("R1")).getByTestId("programs-req-where").textContent).toBe(`${metCopies} of 6 steps`);
    expect(within(inDone("R7")).getByTestId("programs-req-proof").textContent).toBe("after the last step");
    expect(within(inDone("R7")).getByTestId("programs-req-state").textContent).toBe("Not yet");
    const word = (label: string) => within(reqRow(label)).getByTestId("programs-req-state").textContent;
    // His step (3): his word, Met / Unmet.
    let fold = openStep(3);
    expect(within(fold).getAllByTestId("programs-req").map((row) => row.getAttribute("data-label"))).toEqual(["R1", "R4"]);
    expect(word("R4")).toBe("Waits for you");
    expect(reqRow("R4").getAttribute("data-tone")).toBe("ask");
    expect(within(reqRow("R4")).getAllByRole("button").map((b) => b.textContent).filter((t) => t === "Met" || t === "Unmet")).toEqual(["Met", "Unmet"]);
    // Step 1: a Met shot, Open shot one press away; no Waive on a Met row.
    fold = openStep(1);
    expect(word("R2")).toBe("Met");
    expect(reqRow("R2").getAttribute("data-tone")).toBe("ok");
    expect(reqRow("R2").querySelector(".pg-kind")!.textContent).toBe("Shot");
    expect(within(reqRow("R2")).getByTestId("programs-req-open-shot")).toBeTruthy();
    expect(within(reqRow("R2")).queryByTestId("programs-req-waive")).toBeNull();
    // Step 2: an Unmet review, the reviewer's line, Send back / Waive.
    openStep(2);
    const r3 = allRequirements(reqProgram).find((row) => row.label === "R3")!;
    expect(word("R3")).toBe("Unmet");
    expect(reqRow("R3").getAttribute("data-tone")).toBe("fail");
    expect(reqRow("R3").querySelector(".pg-kind")!.textContent).toBe("Review");
    expect(within(reqRow("R3")).getByTestId("programs-req-proof").textContent).toBe(`“${r3.evidence.line}” · round 1`);
    expect(within(reqRow("R3")).getByTestId("programs-req-send-back").textContent).toBe("Send back");
    expect(within(reqRow("R3")).getByTestId("programs-req-waive").textContent).toBe("Waive");
    // Step 4: Open log; step 5: Waived.
    openStep(4);
    expect(within(reqRow("R5")).getByTestId("programs-req-open-log")).toBeTruthy();
    openStep(5);
    expect(word("R6")).toBe("Waived");
    expect(reqRow("R6").getAttribute("data-state")).toBe("waived");
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
    await screen.findByTestId("programs-board");
    expect(within(stepRow(2)).getByTestId("programs-step-word").textContent).toBe("Findings");
    openStep(2);
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
    await screen.findByTestId("programs-board");
    openStep(4);
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
    await screen.findByTestId("programs-board");
    openStep(4);
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
    await screen.findByTestId("programs-board");
    openStep(4);
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
    // PG-WINDOW: the headline: the kind line, the hub's question and what happened.
    expect(row.textContent).toContain(`Your word · holds the merge· Step ${item.ordinal}, ${item.step_title}`);
    expect(within(row).getByTestId("programs-brief-question").textContent).toBe(item.brief!.question);
    expect(within(row).getByTestId("programs-brief-happened").textContent).toBe(item.brief!.happened);
    // Each choice says what it does.
    expect(within(row).getAllByTestId("programs-turn-consequence").map((node) => node.textContent))
      .toEqual(["met", "unmet"].map((choice) => item.brief!.consequences[choice]));
    expect(within(row).getByTestId("programs-turn-met").className).toMatch(/primary/);
    fireEvent.click(within(row).getByTestId("programs-turn-met"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(calls).toContain(`POST /api/programs/${word.id}/requirements/${item.requirement_id}/decide ${JSON.stringify({ choice: "met" })}`);
    const r1 = within(screen.getByTestId("programs-step-fold")).getAllByTestId("programs-req").find((node) => node.getAttribute("data-label") === "R1")!;
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
    // PG-DIRECTION DIR3: each also makes its briefing page (Copy page link).
    // PG-WINDOW: the headline's Copy page link is on its words row, not in the tray.
    expect(words("step_change").filter((word) => !["Brief", "Program text"].includes(word ?? ""))).toEqual(["Apply", "Skip", "Copy page link"]);
    expect(words("step_amend").filter((word) => !["Brief", "Program text"].includes(word ?? ""))).toEqual(["Send", "Skip", "Copy page link"]);
    const row = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "requirement_proposed")!;
    expect(row.textContent).toContain("The line answers in two rings");
    fireEvent.click(within(row).getByTestId("programs-turn-add"));
    // PG-WINDOW: the new requirement is a line in its step.
    await waitFor(() => expect(within(openStep(1)).getAllByTestId("programs-req").map((node) => node.textContent))
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
    // PG-WINDOW: Add a requirement is a verb on Done when (Where: The program) and on each step.
    await screen.findByTestId("programs-board");
    fireEvent.click(within(doneWhen()).getByTestId("programs-done-add-requirement"));
    const add = within(doneWhen()).getByTestId("programs-req-add");
    expect((within(add).getByRole("combobox", { name: "Where" }) as HTMLSelectElement).value).toBe("program");
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
    await waitFor(() => expect(calls.some((call) => call.startsWith(`POST /api/programs/${reqProgram.id}/requirements `))).toBe(true));
    openStep(5);
    await waitFor(() => expect(screen.getAllByTestId("programs-req").some((row) => row.getAttribute("data-req") === added.requirement_id)).toBe(true));
    expect(calls).toContain(`POST /api/programs/${reqProgram.id}/requirements ${JSON.stringify({
      text: "The Programs window at 393 has no clipped text", kind: "shot", required: true, step_id: step5.id, spec: { case: "programs", width: 393 },
    })}`);
    const row = screen.getAllByTestId("programs-req").find((node) => node.getAttribute("data-req") === added.requirement_id)!;
    expect(within(row).getByTestId("programs-req-where").textContent).toBe("Step 5");
    expect(row.querySelector(".pg-kind")!.textContent).toBe("Shot");
    expect((within(within(doneWhen()).getByTestId("programs-req-add")).getByRole("textbox", { name: "Add a requirement" }) as HTMLInputElement).value).toBe("");
  });

  it("a Shot in a repository with no shot command withholds Add and says why", async () => {
    hub({ [`GET /api/programs/${adjust.id}`]: adjust });
    render(<ProgramBody programId={adjust.id} />);
    await screen.findByTestId("programs-board");
    // The step's own Add a requirement: its Where is the step.
    const fold = openStep(1);
    fireEvent.click(within(fold).getByTestId("programs-step-add-requirement"));
    const add = within(fold).getByTestId("programs-req-add");
    expect((within(add).getByRole("combobox", { name: "Where" }) as HTMLSelectElement).value).toBe(adjust.steps[0].id);
    fireEvent.change(within(add).getByRole("textbox", { name: "Add a requirement" }), { target: { value: "The Calls window at 393 has no clipped text" } });
    expect((within(add).getByTestId("programs-req-add-verb") as HTMLButtonElement).disabled).toBe(true);
    expect(within(add).getByTestId("programs-req-add-why").textContent).toBe(adjust.can_prove!.shot_reason);
  });

  it("Needs you: his word is a decide row on the requirement's route, grouped by the Program", () => {
    const rows = (needsRequirementsFixture as { items: unknown[] }).items as NeedsYouRoomItem[];
    const face = needFace({ ref: String((rows[0] as { ref?: string }).ref), kind: "attention", item: rows[0] } as never,
      { now: new Date(), sessions: [], flights: [] } as never);
    expect(face.kind).toBe("program");
    expect(face.direction).toBe("decide");
    // #1854: named by its Program; his word (TO CONFIRM) is a decision: the
    // quiet word Decide, one verb Decide; Met and Unmet are its context menu,
    // each pressed on the requirement's route.
    expect(face.name).toBe(String((rows[0] as { group?: string }).group));
    expect(face.lamp.label).toBe("Decide");
    expect(face.verbs).toMatchObject({ kind: "program", ask: "decide", choices: ["met", "unmet"] });
    expect((face.verbs as { decide: string }).decide).toMatch(/\/requirements\/req-[0-9a-f]+\/decide$/);
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

  it("the open step: what it must prove first, then the parts with only what has something behind it; Gate opens on a red check", async () => {
    hub({ [`GET /api/programs/${reqProgram.id}`]: reqProgram });
    render(<ProgramBody programId={reqProgram.id} />);
    await screen.findByTestId("programs-board");
    const fold = openStep(4);
    // The open step sits under its row (no fold head).
    expect(fold.closest("li")!.previousElementSibling).toBe(stepRow(4));
    // Its requirements are lines, always shown, first.
    expect(within(within(fold).getByTestId("programs-step-requirements")).getAllByTestId("programs-req").map((row) => row.getAttribute("data-label")))
      .toEqual(["R1", "R5"]);
    // A red check: Gate open.
    expect(fold.getAttribute("data-part")).toBe("gate");
    expect(within(fold).getByTestId("programs-gate")).toBeTruthy();
    const tokens = within(within(fold).getByRole("group", { name: "Step 4" })).getAllByRole("button").map((button) => button.textContent);
    expect(tokens).not.toContain("Requirements");
    expect(tokens).not.toContain("Handoffs");
    fireEvent.click(within(fold).getByRole("button", { name: "Ledger" }));
    expect(within(fold).getByTestId("programs-step-ledger").textContent).toContain("R5");
    // A press on the open token closes it; a press on the open row closes the step.
    fireEvent.click(within(fold).getByRole("button", { name: "Ledger" }));
    expect(within(fold).queryByTestId("programs-step-ledger")).toBeNull();
    fireEvent.click(within(stepRow(4)).getByTestId("programs-step-select"));
    expect(screen.queryByTestId("programs-step-fold")).toBeNull();
    // Findings open Findings; the Unmet review is a line that says so.
    openStep(2);
    expect(screen.getByTestId("programs-step-fold").getAttribute("data-part")).toBe("findings");
    expect(within(reqRow("R3")).getByTestId("programs-req-state").textContent).toBe("Unmet");
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
    const fold = openStep(1);
    fireEvent.click(within(fold).getByRole("button", { name: "Brief" }));
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
    await screen.findByTestId("programs-board");
    openStep(1);
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

describe("PG-IMPORT IMP1: the step report and the second mark (recorded: scripts/record_program_fixtures.py, test_program_delivery.py)", () => {
  it("a Done step's open row reads its report in four registers, in order, as plain labels", async () => {
    hub({ [`GET /api/programs/${done.id}`]: done });
    render(<ProgramBody programId={done.id} />);
    await screen.findByTestId("programs-board");
    const fold = openStep(1);
    const report = within(fold).getByTestId("programs-step-report");
    // The registers in BroCrew's order; each a plain label, no chip or badge.
    expect([...report.querySelectorAll(".pg-sf-cap")].map((node) => node.textContent))
      .toEqual(["Checked:", "The agent says:", "Files:"]);
    expect(report.querySelector(".kit-chip, .kit-badge, .kit-token")).toBeNull();
    const step = done.steps[0];
    const lines = (key: string) => [...within(report).getByTestId(`programs-report-${key}`).querySelectorAll("li")].map((node) => node.textContent);
    expect(lines("observed")).toEqual(step.report!.observed.map((row) => row.line));
    expect(lines("observed").some((line) => /^PR #\d+ merged$/.test(line ?? ""))).toBe(true);
    expect(lines("claimed")).toContain("Cited every anchor in the atlas once.");
    // Every Checked line cites a checkpoint the engine wrote.
    const engine = new Set(done.checkpoints.filter((row) => row.by === "engine").map((row) => row.id));
    for (const row of step.report!.observed) expect(engine.has(row.checkpoint as number)).toBe(true);
    expect(within(report).getByTestId("programs-report-files").textContent).toContain(step.report!.files[0]);
    // A finished step reads its report, not the running story.
    expect(within(fold).queryByTestId("programs-step-story")).toBeNull();
  });

  it("a Done program that needs nothing says finished; one that raised a decision says so, never the ask lamp", async () => {
    hub({ [`GET /api/programs/${done.id}`]: done });
    render(<ProgramBody programId={done.id} />);
    expect((await screen.findByTestId("programs-line-finished")).textContent).toBe("finished");
    cleanup();
    const waiting = deliveryMergeFixture as unknown as Program;
    expect(waiting.state).toBe("done");
    hub({ [`GET /api/programs/${waiting.id}`]: waiting });
    render(<ProgramBody programId={waiting.id} />);
    const mark = await screen.findByTestId("programs-line-finished");
    expect(mark.textContent).toBe("finished · needs a decision");
    expect(mark.closest("[data-tone]")).toBeNull();
    expect(mark.querySelector(".kit-dot")).toBeNull();
  });

  it("the list's Done row carries the mark in place of its last line", async () => {
    hub({ "GET /api/programs": list });
    render(<ProgramsCore />);
    const row = (await screen.findAllByTestId("programs-row")).find((node) => node.getAttribute("data-state") === "done")!;
    const summary = list.programs.find((item) => item.id === row.getAttribute("data-program"))!;
    expect(summary.finished_words).toBe("finished");
    expect(within(row).getByTestId("programs-row-finished").textContent).toBe("finished");
    expect(within(row).getByTestId("programs-row-state").textContent).toContain(summary.state_word);
  });
});

describe("PG-IMPORT IMP2: the to-do row and the ending word (recorded: scripts/record_program_fixtures.py)", () => {
  it("a walk is a to-do: who asks, the walk, Done and Can't do it, an optional note that reaches the hub", async () => {
    const todo = todoFixture as unknown as Program;
    const item = todo.your_turn_items.find((row) => row.kind === "todo")!;
    hub({
      [`GET /api/programs/${todo.id}`]: todo,
      [`POST /api/programs/${todo.id}/requirements/${item.requirement_id}/decide`]: todoDoneFixture,
    });
    render(<ProgramBody programId={todo.id} />);
    await screen.findByTestId("programs-your-turn");
    const row = screen.getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-item") === item.id)!;
    expect(row.getAttribute("data-kind")).toBe("todo");
    expect(row.textContent).toContain(item.brief!.happened);
    expect(item.head).toBe("Claude Code asks you to do this · step 1");
    expect(within(row).getAllByRole("button").map((button) => button.textContent)).toEqual(
      expect.arrayContaining(["Done", "Can't do it"]));
    fireEvent.change(within(row).getByRole("textbox", { name: "Add a note (optional)" }), { target: { value: "Looks right on my phone" } });
    fireEvent.click(within(row).getByTestId("programs-turn-done"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${todo.id}/requirements/${item.requirement_id}/decide {"choice":"done","line":"Looks right on my phone"}`));
    // The hub's answer: the to-do is gone; the requirement is Met by his word.
    await waitFor(() => expect(screen.queryAllByTestId("programs-turn-item").some((node) => node.getAttribute("data-kind") === "todo")).toBe(false));
  });

  it("a cut-off lane says so beside its state", async () => {
    const todo = todoFixture as unknown as Program;
    hub({ [`GET /api/programs/${todo.id}`]: todo });
    render(<ProgramBody programId={todo.id} />);
    await screen.findByTestId("programs-board");
    const cut = todo.steps.find((step) => step.ending === "interrupted")!;
    expect(stepRow(cut.ordinal).textContent).toContain("Parked · interrupted");
  });
});

describe("PG-IMPORT IMP3: what a step waits on (recorded: scripts/record_program_fixtures.py)", () => {
  it("a step after one that ended says so on its row, in the hub's words", async () => {
    const todo = todoFixture as unknown as Program;
    hub({ [`GET /api/programs/${todo.id}`]: todo });
    render(<ProgramBody programId={todo.id} />);
    await screen.findByTestId("programs-board");
    const waiting = todo.steps.find((step) => step.wait?.cause === "target_ended")!;
    expect(waiting.wait!.line).toBe(`Step ${waiting.ordinal} with Claude Code is waiting on something that has ended.`);
    expect(stepRow(waiting.ordinal).textContent).toContain(waiting.wait!.line);
  });
});

describe("PG-IMPORT IMP6: take it over, hand it back (recorded: scripts/record_program_fixtures.py)", () => {
  it("Take it over opens the lane and the row says he has it; Hand it back gives it back; no confirmation", async () => {
    const lane = laneFixture as unknown as Program;
    const step = lane.steps[0];
    hub({
      [`GET /api/programs/${lane.id}`]: lane,
      [`POST /api/programs/${lane.id}/steps/${step.id}/take`]: laneTakenFixture,
      [`POST /api/programs/${lane.id}/steps/${step.id}/hand-back`]: laneBackFixture,
    });
    render(<ProgramBody programId={lane.id} />);
    await screen.findByTestId("programs-board");
    expect(within(stepRow(1)).queryByTestId("programs-step-hand-back")).toBeNull();
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-take"));
    await waitFor(() => expect(stepRow(1).textContent).toContain("You have the lane"));
    expect(calls).toContain(`POST /api/programs/${lane.id}/steps/${step.id}/take {}`);
    expect(mocks.openRef).toHaveBeenCalledWith(`launch:${step.launch_id}`);
    expect(within(stepRow(1)).getByTestId("programs-step-open").textContent).toBe("Open lane");
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-hand-back"));
    await waitFor(() => expect(within(stepRow(1)).queryByTestId("programs-step-take")).not.toBeNull());
    expect(stepRow(1).textContent).not.toContain("You have the lane");
    expect(screen.queryByRole("dialog")).toBeNull();
  });
});

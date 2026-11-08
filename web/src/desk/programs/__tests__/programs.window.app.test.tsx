/* The Programs app (T2), the Program window: the board, Your turn, the
 * delivery, the race, the handoff, the checkpoints and the briefing page.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  yourTurnFixture, startFromFixture, pageNoneFixture, pageOpenFixture, revokeOpenFixture,
  pageRevokedFixture, reachPackageFixture, reachRevokedFixture, deliveryFailedFixture,
  deliveryMergeFixture, deliveryMergedFixture, deliveryCheckFixture, deliveryCheckedOpenFixture,
  deliveryUnknownFixture, deliveryQueuedFixture, deliveryLegacyFixture, auditBoardFixture,
  raceParkedFixture, raceResumedFixture, raceWonFixture, raceRoundFixture,
  raceRoundAnsweredFixture, raceRoundNextFixture, auditSecureFixture, auditFiledFixture,
  auditFixFixture, lessonProgramFixture, lessonKeptFixture, parkedStepsFixture, mocks, ApiError,
  ProgramBody, stationsOf, clone, running, yourTurn, done, parked, drafting, limited, raced, calls,
  hub, status, stepRow, openStep, type Program, type ProgramStep,
} from "./programs.test-setup";
import { describe, expect, it, vi } from "vitest";
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

describe("the Program window (direction C, the ledger)", () => {
  it("YOLO with a question: the board draws every step state, pi on qwen and the held step", async () => {
    hub({ [`GET /api/programs/${running.id}`]: running });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-board");
    const words = screen.getAllByTestId("programs-step").map((row) => within(row).getByTestId("programs-step-word").textContent);
    expect(words).toEqual(["Done", "PR open", "Check failed · log", "Asks you", "Ready · waiting for qwen", "Planned", "Working"]);
    // PG-IMPORT IMP6: Take it over only where the lane is alive (a working step), never on a done one.
    const working = running.steps.find((step) => step.state === "working" && step.launch_id);
    if (working) expect(within(stepRow(working.ordinal)).getByTestId("programs-step-take")).toBeTruthy();
    expect(within(stepRow(1)).queryByTestId("programs-step-take")).toBeNull();
    expect(within(stepRow(1)).queryByTestId("programs-step-open")).toBeNull();
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

  // HS-S24 (D20/G24): the hub's spend note is one mono fact; never "limit" or "cap".
  it("the spend note: one mono fact in the status bar, absent when he set none", async () => {
    const noted = { ...clone(running), spend_limit_usd: 40, spend_note: "spend note · 40 USD" };
    hub({ [`GET /api/programs/${running.id}`]: noted });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-board");
    const fact = within(status()).getByTestId("programs-status-spend");
    expect(fact.textContent).toBe("spend note · 40 USD");
    expect(fact.querySelector(".pg-ref")).toBeTruthy();
    expect(status().textContent).not.toMatch(/limit|cap/i);
    cleanup();
    hub({ [`GET /api/programs/${running.id}`]: running });
    render(<ProgramBody programId={running.id} />);
    await screen.findByTestId("programs-board");
    expect(within(status()).queryByTestId("programs-status-spend")).toBeNull();
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

  it("Drafting (PG-WINDOW A): one row per step that opens in place to its fields with mics; the goal is the headline; Start says what it checks", async () => {
    hub({ [`GET /api/programs/${drafting.id}`]: drafting });
    render(<ProgramBody programId={drafting.id} />);
    await screen.findByTestId("programs-board");
    // No spreadsheet: one row per step, none open, every step in view.
    expect(screen.queryByTestId("programs-draft-step")).toBeNull();
    expect(screen.getAllByTestId("programs-step")).toHaveLength(drafting.steps.length);
    expect(screen.queryByTestId("programs-step-fold")).toBeNull();
    // The line: one planned station per step.
    expect(within(screen.getByTestId("programs-line")).getAllByRole("listitem").filter((node) => node.getAttribute("data-station") !== "end"))
      .toHaveLength(drafting.steps.length);
    // The headline: the goal in his words, edited in place; Start, with what it checks, in the tray.
    expect(within(screen.getByTestId("programs-draft-goal")).getByText(drafting.goal.split("\n")[0], { exact: false })).toBeTruthy();
    const tray = screen.getByTestId("programs-tray");
    expect(within(tray).getByTestId("program-start").className).toMatch(/primary/);
    // One thing in the tray: Start and the step count (no sentence, no Plan it beside it).
    expect(within(tray).queryByTestId("program-plan-it")).toBeNull();
    expect(within(tray).getByTestId("programs-start-words").textContent).toBe(`${drafting.steps.length} steps`);
    expect(within(screen.getByTestId("program-toolbar")).queryByTestId("program-start")).toBeNull();
    // A press opens the step in place: its title with its mic, its gate as plain words with the pickers.
    const fold = openStep(1);
    expect((within(fold).getByRole("textbox", { name: "Step 1 title" }) as HTMLInputElement).value).toBe(drafting.steps[0].title);
    expect(within(fold).getByRole("button", { name: /Speak Step 1 title/ })).toBeTruthy();
    expect(within(fold).getByRole("group", { name: "Step 1 gate" })).toBeTruthy();
    // What it must prove: its lines, and Add a requirement at the step.
    const prove = within(fold).getByTestId("programs-step-requirements");
    expect(within(prove).getAllByTestId("programs-req")).toHaveLength(drafting.steps[0].requirements!.length);
    expect(within(prove).getByTestId("programs-step-add-requirement").textContent).toBe("Add a requirement");
  });

  it("no empty section: a step with nothing to prove shows Add a requirement alone", async () => {
    const bare = clone(drafting);
    bare.steps = bare.steps.map((step) => ({ ...step, requirements: [] }));
    hub({ [`GET /api/programs/${bare.id}`]: bare });
    render(<ProgramBody programId={bare.id} />);
    await screen.findByTestId("programs-board");
    const prove = within(openStep(1)).getByTestId("programs-step-requirements");
    expect(prove.querySelector(".pg-sf-cap")).toBeNull();
    expect(prove.textContent).toBe("Add a requirement");
  });
});

describe("PG-WINDOW: the Program window as one object (canvas program-window-2026-10-31, direction A)", () => {
  const held = yourTurnFixture as unknown as Program;
  it("the line lights the held step; the held item is the headline in his terms with the tray; the rest are one line each", async () => {
    hub({ [`GET /api/programs/${held.id}`]: held });
    render(<ProgramBody programId={held.id} />);
    await screen.findByTestId("programs-board");
    const first = held.your_turn_items[0];
    // The line: one station per step, the held one current and breathing.
    const line = screen.getByTestId("programs-line");
    const stations = [...line.querySelectorAll("[data-station]")].filter((node) => node.getAttribute("data-station") !== "end");
    expect(stations.map((node) => node.getAttribute("data-station"))).toEqual(held.steps.filter((step) => !step.race_of).map((step) => step.id));
    const here = line.querySelector("[aria-current=step]")!;
    expect(here.getAttribute("data-station")).toBe(first.step_id);
    expect(here.querySelector("[data-live]")).not.toBeNull();
    expect(line.textContent).toContain(`Goal: ${held.goal}`);
    // The headline: the kind line, the question, the step, what happened; no tinted box.
    const well = screen.getByTestId("programs-your-turn");
    const [headline, ...rest] = within(well).getAllByTestId("programs-turn-item");
    expect(headline.tagName).toBe("ARTICLE");
    expect(within(headline).getByTestId("programs-brief-question").textContent).toBe(first.brief!.question);
    expect(headline.textContent).toContain(first.brief!.doing);
    expect(within(headline).getByTestId("programs-brief-happened").textContent).toBe(first.brief!.happened);
    // The tray: each choice a library Button with its consequence under it.
    const tray = within(headline).getByTestId("programs-tray");
    expect([...tray.querySelectorAll("[data-choice]")].map((node) => node.getAttribute("data-choice"))).toEqual(["merge", "not_yet"]);
    expect(within(tray).getAllByTestId("programs-turn-consequence").map((node) => node.textContent))
      .toEqual(["merge", "not_yet"].map((choice) => first.brief!.consequences[choice]));
    expect(within(tray).getByTestId("programs-turn-merge").className).toMatch(/primary/);
    // The others: one line each, with the hub's question.
    expect(rest).toHaveLength(held.your_turn_items.length - 1);
    expect(rest[0].textContent).toContain(held.your_turn_items[1].brief!.question);
  });

  it("no step opens by itself while one waits on him (every step in view); Brief opens the held one; rows say the story, never a raw note", async () => {
    hub({ [`GET /api/programs/${held.id}`]: held });
    render(<ProgramBody programId={held.id} />);
    await screen.findByTestId("programs-board");
    const first = held.your_turn_items[0];
    const step = held.steps.find((row) => row.id === first.step_id)!;
    expect(screen.queryByTestId("programs-step-fold")).toBeNull();
    expect(screen.getAllByTestId("programs-step")).toHaveLength(held.steps.filter((row) => !row.race_of).length);
    // The fence of the briefing page holds for every row.
    for (const row of screen.getAllByTestId("programs-step")) expect(row.textContent).not.toMatch(/fatal:|error:|\/\w|\bgit \w|\b[0-9a-f]{7,}\b/);
    // The held row says what happened in the hub's words.
    expect(stepRow(step.ordinal).textContent).toContain(first.brief!.happened);
    // Copy page link is not a choice: it is on the words row under the tray.
    const headline = within(screen.getByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    expect(within(within(headline).getByTestId("programs-tray")).queryByTestId("programs-turn-copy-link")).toBeNull();
    const row = within(headline).getByTestId("programs-turn-words");
    expect(within(row).getAllByRole("button").map((button) => button.textContent)).toEqual(["Brief", "Program text", "Copy page link"]);
    fireEvent.click(within(row).getByTestId("programs-turn-brief"));
    const fold = screen.getByTestId("programs-step-fold");
    expect(fold.getAttribute("data-part")).toBe("brief");
    expect(fold.getAttribute("data-step")).toBe(step.id);
    const story = within(fold).getByTestId("programs-step-story");
    expect([...story.querySelectorAll(".pg-sf-story-words")].map((node) => node.textContent)).toEqual(step.story!.map((row) => row.line));
    // No line of the story holds a path, a command or a hash.
    for (const row of step.story!) expect(row.line).not.toMatch(/fatal:|error:|\/|\b[0-9a-f]{7,}\b/);
    // The composer: after the body, before the status bar.
    const bar = screen.getByTestId("program-shape-bar");
    expect(bar.previousElementSibling?.className).toContain("pg-body");
    expect((within(bar).getByRole("textbox", { name: "Change the program" }) as HTMLInputElement).placeholder).toBe("Tell the program what to change");
  });
});

describe("LANG13: the delivery at Done (recorded on the rig: tests/integration/test_program_delivery.py)", () => {
  it("a failed delivery is the headline in his words, with Retry and Skip and what each does", async () => {
    const failed = deliveryFailedFixture as unknown as Program;
    const item = failed.your_turn_items[0];
    hub({ [`GET /api/programs/${failed.id}`]: failed });
    render(<ProgramBody programId={failed.id} />);
    const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    expect(headline.getAttribute("data-kind")).toBe("delivery");
    expect(within(headline).getByTestId("programs-brief-question").textContent).toBe("Try the delivery again, or skip it?");
    expect(within(headline).getByTestId("programs-brief-happened").textContent).toBe(item.brief!.happened);
    const tray = within(headline).getByTestId("programs-tray");
    expect(within(tray).getAllByRole("button").map((button) => button.textContent)).toEqual(["Retry", "Skip"]);
    expect(within(tray).getAllByTestId("programs-turn-consequence").map((node) => node.textContent))
      .toEqual(["Try the delivery again.", "Skip it. The program stays Done, not delivered."]);
    expect(headline.textContent).toContain("Not delivered");
  });

  it("at Secure, Merge presses through and the Done window settles to Delivered to dw app/1 (PR #n)", async () => {
    const waiting = deliveryMergeFixture as unknown as Program;
    const merged = (deliveryMergedFixture as unknown as { program: Program }).program;
    hub({
      [`GET /api/programs/${waiting.id}`]: waiting,
      [`POST /api/programs/${waiting.id}/steps/program/decide`]: deliveryMergedFixture,
    });
    render(<ProgramBody programId={waiting.id} />);
    const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    expect(within(headline).getByTestId("programs-brief-question").textContent).toBe("Merge the delivery pull request, or skip the delivery?");
    expect(within(headline).getAllByTestId("programs-turn-consequence")[0].textContent)
      .toBe("Merge the delivery pull request. HoldSpeak then reads the result on GitHub.");
    // HS-S32: "PR #n open" beside Merge, Check and Skip.
    const item = waiting.your_turn_items[0];
    expect(headline.textContent).toContain(`PR #${item.pr!.number} open`);
    expect(within(within(headline).getByTestId("programs-tray")).getAllByRole("button").map((button) => button.textContent))
      .toEqual(["Merge", "Check", "Skip"]);
    expect(screen.queryByTestId("programs-delivered")).toBeNull();
    fireEvent.click(within(headline).getByTestId("programs-turn-merge"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(calls).toContain(`POST /api/programs/${waiting.id}/steps/program/decide ${JSON.stringify({
      kind: "delivery", choice: "merge", expected_delivery_checkpoint_id: item.expected_delivery_checkpoint_id })}`);
    const pr = merged.checkpoints.find((row) => row.kind === "delivery" && row.choice === "delivered")!;
    expect(screen.getByTestId("programs-delivered").textContent).toBe(pr.line);
    expect(pr.line).toMatch(/^Delivered to dw app\/1 \(PR #\d+\)( · phase closed)?$/);
  });
});

describe("HS-S32: a known delivery PR is checked, never made again (recorded: tests/integration/test_program_delivery.py)", () => {
  const tray = (headline: HTMLElement) =>
    within(within(headline).getByTestId("programs-tray")).getAllByRole("button").map((button) => button.textContent);

  it("a merge that GitHub did not confirm offers Check and Skip, never Retry or Merge", async () => {
    const program = deliveryCheckFixture as unknown as Program;
    const item = program.your_turn_items[0];
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    expect(tray(headline)).toEqual(["Check", "Skip"]);
    expect(headline.textContent).toContain(`PR #${item.pr!.number} · Not confirmed`);
    expect(within(headline).getByTestId("programs-brief-question").textContent)
      .toBe("Check the delivery pull request on GitHub, or skip the delivery?");
    expect(within(headline).getByTestId("programs-brief-happened").textContent)
      .toBe(`A merge of the delivery PR #${item.pr!.number} is requested. GitHub has not confirmed it.`);
    expect(screen.queryByTestId("programs-delivered")).toBeNull();  // Done is not delivered
  });

  it("Check sends the line it shows; an open PR comes back with Merge, Check and Skip", async () => {
    const waiting = deliveryMergeFixture as unknown as Program;
    const answer = deliveryCheckedOpenFixture as unknown as { program: Program };
    const item = waiting.your_turn_items[0];
    hub({
      [`GET /api/programs/${waiting.id}`]: waiting,
      [`POST /api/programs/${waiting.id}/steps/program/decide`]: deliveryCheckedOpenFixture,
    });
    render(<ProgramBody programId={waiting.id} />);
    const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    fireEvent.click(within(headline).getByTestId("programs-turn-check"));
    await waitFor(() => expect(calls).toContain(`POST /api/programs/${waiting.id}/steps/program/decide ${JSON.stringify({
      kind: "delivery", choice: "check", expected_delivery_checkpoint_id: item.expected_delivery_checkpoint_id })}`));
    const next = answer.program.your_turn_items[0];
    expect(next.expected_delivery_checkpoint_id).not.toBe(item.expected_delivery_checkpoint_id);
    await waitFor(() => expect(screen.getAllByTestId("programs-turn-item")[0].textContent).toContain(`PR #${next.pr!.number} open`));
    expect(tray(screen.getAllByTestId("programs-turn-item")[0])).toEqual(["Merge", "Check", "Skip"]);
  });

  it("a queued merge and a closed PR stay Not confirmed with Check and Skip", async () => {
    for (const fixture of [deliveryQueuedFixture, deliveryUnknownFixture]) {
      const program = fixture as unknown as Program;
      hub({ [`GET /api/programs/${program.id}`]: program });
      render(<ProgramBody programId={program.id} />);
      const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
      expect(tray(headline)).toEqual(["Check", "Skip"]);
      expect(headline.textContent).toContain(`PR #${program.your_turn_items[0].pr!.number} · Not confirmed`);
      expect(within(headline).getAllByTestId("programs-turn-consequence").map((node) => node.textContent).at(-1))
        .toBe("Skip it. The program stays Done. The delivery stays not confirmed.");
      cleanup();
    }
  });

  it("an old delivery line is shown, with Skip only", async () => {
    const program = deliveryLegacyFixture as unknown as Program;
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    const headline = within(await screen.findByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")[0];
    expect(tray(headline)).toEqual(["Skip"]);
    expect(headline.textContent).toContain("Not confirmed");
    expect(within(headline).getByTestId("programs-brief-question").textContent).toBe("Skip the delivery? HoldSpeak cannot confirm it.");
  });
});

describe("a race of 2 (the recorded race: Codex wins in 34 min)", () => {
  it("the contender is indented under the step, the loser says Lost the race to Codex · 34 min, no Open lane on an ended lane", async () => {
    hub({ [`GET /api/programs/${raced.id}`]: raced });
    render(<ProgramBody programId={raced.id} />);
    await screen.findByTestId("programs-board");
    const lead = stepRow(1);
    expect(within(lead).getByTestId("programs-step-word").textContent).toBe("Race of 2");
    // The step's own agent lost: its line and its time.
    expect(lead.textContent).toContain("Claude Code");
    // PG-WINDOW: the row's line is the step's story, in the hub's words.
    expect(lead.textContent).toContain("Lost the race to Codex.");
    expect(lead.querySelector(".pg-step-when")?.textContent).toBe("34 min");
    expect(lead.querySelector(".pg-step-meta")?.textContent).toBe("Claude Code · 34 min · Lost the race to Codex.");
    // The contender row comes right after the step, indented, and names its agent.
    const [contender] = screen.getAllByTestId("programs-contender");
    expect(lead.nextElementSibling).toBe(contender);
    expect(contender.hasAttribute("data-contender")).toBe(true);
    expect(within(contender).getByTestId("programs-step-select").textContent).toContain("Codex");
    expect(within(contender).getByTestId("programs-step-word").textContent).toBe("Done");
    expect(contender.textContent).toContain("Merged #101");
    // Both lanes ended (the loser parked, the winner merged): Open lane is a
    // dead verb then, so neither row draws it (owner catch 2026-11-01).
    expect(within(lead).queryByTestId("programs-step-open")).toBeNull();
    expect(within(contender).queryByTestId("programs-step-open")).toBeNull();
    // The engine's choice is under Decided for you.
    expect(screen.getByTestId("programs-decided").textContent).toContain("Codex won the race · 34 min");
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
    // PG-WINDOW: the hub's brief in his terms (what happened, the question).
    expect(row.textContent).toContain(`Claude Code is at its usage limit until ${item.until_words}.`);
    expect(row.textContent).toContain("Continue in Codex now, or wait for the reset?");
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
    // The recording also holds step 1's commit (#1677); only the limited item leaves.
    await waitFor(() => expect(screen.queryAllByTestId("programs-turn-item").some((node) => node.getAttribute("data-kind") === "limited")).toBe(false));
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

describe("the briefing page link (PG-DIRECTION DIR3)", () => {
  it("Copy page link makes the page, copies its link, and the row says the page is open", async () => {
    const before = pageNoneFixture as unknown as Program;
    const after = pageOpenFixture as unknown as Program;
    const core = before.your_turn_items.find((item) => item.kind === "core")!;
    const writeText = vi.fn(async () => undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    let made = false;
    hub({
      [`GET /api/programs/${before.id}`]: () => (made ? after : before),
      "POST /api/reach/packages": () => { made = true; return reachPackageFixture; },
    });
    render(<ProgramBody programId={before.id} />);
    const well = await screen.findByTestId("programs-your-turn");
    const row = within(well).getAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === "core")!;
    expect(within(row).queryByTestId("programs-turn-page")).toBeNull();
    fireEvent.click(within(row).getByTestId("programs-turn-copy-link"));
    await waitFor(() => expect(screen.getByTestId("programs-turn-page").textContent).toMatch(/^Page link copied · open until \d\d:\d\d$/));
    expect(calls).toContain(`POST /api/reach/packages ${JSON.stringify({ refs: [`program:${before.id}:${core.id}`] })}`);
    expect(writeText).toHaveBeenCalledWith(`${window.location.origin}${reachPackageFixture.path}`);
    expect(screen.getByTestId("programs-turn-revoke").textContent).toBe("Revoke");
    expect(screen.queryByTestId("programs-turn-copy-link")).toBeNull();
    // No chip: the page is said in the row's line.
    expect(within(screen.getByTestId("programs-your-turn")).queryAllByText(/^(Telegram|Page)$/)).toHaveLength(0);
  });

  it("Revoke ends the page and the item stays in Your turn", async () => {
    const open = revokeOpenFixture as unknown as Program;
    const after = pageRevokedFixture as unknown as Program;
    const core = open.your_turn_items.find((item) => item.kind === "core")!;
    let revoked = false;
    hub({
      [`GET /api/programs/${open.id}`]: () => (revoked ? after : open),
      [`POST /api/reach/packages/${core.page!.package_id}/revoke`]: () => { revoked = true; return reachRevokedFixture; },
    });
    render(<ProgramBody programId={open.id} />);
    expect((await screen.findByTestId("programs-turn-page")).textContent).toMatch(/^Page open until \d\d:\d\d$/);
    fireEvent.click(screen.getByTestId("programs-turn-revoke"));
    await waitFor(() => expect(screen.queryByTestId("programs-turn-page")).toBeNull());
    expect(screen.getByTestId("programs-turn-copy-link").textContent).toBe("Copy page link");
    expect(within(screen.getByTestId("programs-your-turn")).getAllByTestId("programs-turn-item")
      .some((node) => node.getAttribute("data-kind") === "core")).toBe(true);
  });
});

describe("PG-JOURNEYS J5: the race in the Program window (recorded: test_program_race.py)", () => {
  it("both contenders red: one Parked row names each contender's log; Resume sends them all back", async () => {
    const race = raceParkedFixture as unknown as Program;
    const item = race.your_turn_items.find((row) => row.kind === "parked")!;
    hub({
      [`GET /api/programs/${race.id}`]: race,
      [`POST /api/programs/${race.id}/steps/${item.step_id}/decide`]: raceResumedFixture,
    });
    render(<ProgramBody programId={race.id} />);
    await screen.findByTestId("programs-your-turn");
    expect(screen.getAllByTestId("programs-turn-item")).toHaveLength(1);
    // The hub says the race failed as one step: the row reads Parked first.
    expect(race.steps[0].race_both_red).toBe(true);
    expect(within(stepRow(1)).getByTestId("programs-step-word").textContent).toBe("Parked · race of 2");
    const logs = screen.getByTestId("programs-race-logs");
    expect([...logs.querySelectorAll(".pg-race-agent")].map((node) => node.textContent)).toEqual(["Claude Code", "Codex"]);
    fireEvent.click(within(logs).getByRole("button", { name: "Open Codex's log" }));
    expect(mocks.openRef).toHaveBeenCalledWith(`note:${item.logs![1].log}`);
    fireEvent.click(screen.getByTestId("programs-turn-resume"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${race.id}/steps/${item.step_id}/decide {"kind":"parked","choice":"resume"}`));
    await waitFor(() => expect(screen.queryByTestId("programs-race-logs")).toBeNull());
    const after = (raceResumedFixture as unknown as { program: Program }).program ?? (raceResumedFixture as unknown as Program);
    expect(after.your_turn_items.filter((row) => row.kind === "parked")).toEqual([]);
  });

  it("the winner: Decided for you says who won and how long, with its rule and no Overturn", async () => {
    const race = raceWonFixture as unknown as Program;
    const row = race.decided_for_you!.find((entry) => entry.kind === "race_winner")!;
    hub({ [`GET /api/programs/${race.id}`]: race });
    render(<ProgramBody programId={race.id} />);
    await screen.findByTestId("programs-board");
    const fold = screen.getAllByRole("button").find((button) => button.textContent?.startsWith("Decided for you"));
    if (fold && fold.getAttribute("aria-expanded") === "false") fireEvent.click(fold);
    const line = (await screen.findAllByTestId("programs-decided-row")).find((node) => node.getAttribute("data-decision") === String(row.id))!;
    expect(line.textContent).toContain(row.line);
    expect(row.line).toMatch(/^Codex won the race · /);
    expect(line.textContent).toContain(`· ${row.rule}`);
    expect(within(line).queryByTestId("programs-overturn")).toBeNull();
  });

  it("the Verification round asks by rule: Each reviews the other turns the race's review on", async () => {
    const race = raceRoundFixture as unknown as Program;
    const round = race.rounds!.find((entry) => entry.name === "Verification")!;
    const question = round.questions[0];
    hub({
      [`GET /api/programs/${race.id}`]: race,
      [`POST /api/programs/${race.id}/rounds/Verification/answer`]: raceRoundAnsweredFixture,
      // The hub's recorded refusal of the next Ask (the rig has no planning engine).
      [`POST /api/programs/${race.id}/rounds/Verification/next`]: () => { throw new ApiError(409, "Conflict", raceRoundNextFixture); },
    });
    render(<ProgramBody programId={race.id} />);
    const asked = await screen.findByTestId("program-question");
    expect(within(asked).getByText("Review each contender?")).toBeInTheDocument();
    const choices = within(asked).getAllByTestId("kit-question-choice");
    expect(choices.map((node) => node.textContent)).toEqual(["Each reviews the other", "No review"]);
    fireEvent.click(choices[0]);
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${race.id}/rounds/Verification/answer ${JSON.stringify({ question_id: question.id, option: "Each reviews the other", apply: false })}`));
    const fold = await screen.findByTestId("program-round-fold");
    expect(fold.textContent).toContain("→ step 1 review");
  });
});

describe("PG-LANG JRN9 to JRN11: File, Make, and a lesson in Your turn (recorded)", () => {
  const turnRow = (kind: string) => screen.queryAllByTestId("programs-turn-item").find((node) => node.getAttribute("data-kind") === kind);

  it("Secure: File the findings is a row of the program; File files them and the board says Open Door task", async () => {
    const audit = auditSecureFixture as unknown as Program;
    const item = audit.your_turn_items.find((row) => row.kind === "audit_file")!;
    hub({
      [`GET /api/programs/${audit.id}`]: audit,
      [`POST /api/programs/${audit.id}/steps/${item.step_id}/decide`]: auditFiledFixture,
    });
    render(<ProgramBody programId={audit.id} />);
    await screen.findByTestId("programs-your-turn");
    const row = turnRow("audit_file")!;
    // Close is asked last (the live walk): File the findings is the headline.
    expect(row.textContent).toContain(item.brief!.question);
    expect(screen.getAllByTestId("programs-turn-item").map((node) => node.getAttribute("data-kind"))).toEqual(["audit_file", "fix_program", "close"]);
    expect(within(row).getAllByRole("button").map((button) => button.textContent).slice(0, 2)).toEqual(["File", "Skip"]);
    expect(within(screen.getByTestId("programs-findings")).queryAllByTestId("programs-finding-task")).toHaveLength(0);
    fireEvent.click(within(row).getByTestId("programs-turn-file"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${audit.id}/steps/${item.step_id}/decide {"kind":"audit_file","choice":"file"}`));
    await waitFor(() => expect(turnRow("audit_file")).toBeUndefined());
    expect(within(screen.getByTestId("programs-findings")).getAllByTestId("programs-finding-task")).toHaveLength(3);
    expect(turnRow("fix_program")).toBeDefined();
  });

  it("a done audit: Make makes the fix program; the row settles to Open the fix program", async () => {
    const audit = auditBoardFixture as unknown as Program;
    const item = audit.your_turn_items.find((row) => row.kind === "fix_program")!;
    hub({
      [`GET /api/programs/${audit.id}`]: audit,
      [`POST /api/programs/${audit.id}/steps/${item.step_id}/decide`]: auditFixFixture,
    });
    render(<ProgramBody programId={audit.id} />);
    await screen.findByTestId("programs-your-turn");
    // The headline: the brief's question, the program as its place, Make and Skip with their consequences.
    expect(screen.getByTestId("programs-brief-question").textContent).toBe("Make a fix program from the MUST findings?");
    const row = turnRow("fix_program")!;
    expect(row.textContent).toContain("· The program");
    expect(within(screen.getByTestId("programs-tray")).getAllByRole("button").map((button) => button.textContent)).toEqual(["Make", "Skip"]);
    expect(within(row).getAllByTestId("programs-turn-consequence").map((node) => node.textContent))
      .toEqual([item.brief!.consequences.make, item.brief!.consequences.skip]);
    expect(screen.queryByTestId("programs-findings-fix")).toBeNull();
    fireEvent.click(within(row).getByTestId("programs-turn-make"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${audit.id}/steps/${item.step_id}/decide {"kind":"fix_program","choice":"make"}`));
    const open = await screen.findByTestId("programs-findings-fix");
    expect(turnRow("fix_program")).toBeUndefined();
    expect(open.textContent).toBe("Open the fix program");
    fireEvent.click(open);
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${(auditFixFixture as { fix_program_id: string }).fix_program_id}`);
  });

  it("a lesson: Keep for this program · Keep for HoldSpeak · Skip; the press names its lesson", async () => {
    const program = lessonProgramFixture as unknown as Program;
    const item = program.your_turn_items.find((row) => row.kind === "lesson")!;
    hub({
      [`GET /api/programs/${program.id}`]: program,
      [`POST /api/programs/${program.id}/steps/${item.step_id}/decide`]: lessonKeptFixture,
    });
    render(<ProgramBody programId={program.id} />);
    await screen.findByTestId("programs-your-turn");
    const row = turnRow("lesson")!;
    expect(screen.getByTestId("programs-brief-question").textContent).toBe("Keep this lesson, and where?");
    expect(row.textContent).toContain(item.brief!.happened);
    // About the whole program: the doing line is its status line, never "Step N".
    expect(item.brief!.doing).toMatch(/^The program: Running · /);
    expect(row.textContent).toContain(item.brief!.doing);
    expect(row.textContent).not.toMatch(/Step \d/);
    expect(within(screen.getByTestId("programs-tray")).getAllByRole("button").map((button) => button.textContent))
      .toEqual(["Keep for this program", "Keep for HoldSpeak", "Skip"]);
    // The briefing page takes it too (the hub's BRIEFABLE): Copy page link under the tray.
    expect(within(row).getByTestId("programs-turn-copy-link").textContent).toBe("Copy page link");
    fireEvent.click(within(row).getByTestId("programs-turn-keep-program"));
    await waitFor(() => expect(calls).toContain(
      `POST /api/programs/${program.id}/steps/${item.step_id}/decide {"kind":"lesson","choice":"keep_program","lesson_id":${item.lesson_id}}`));
    await waitFor(() => expect(turnRow("lesson")).toBeUndefined());
  });
});

describe("park stops the steps (the live walk's finding)", () => {
  it("each open step of a parked Program reads one wait sentence; no breathing dot, no Take it over", async () => {
    const parked = parkedStepsFixture as unknown as Program;
    hub({ [`GET /api/programs/${parked.id}`]: parked });
    render(<ProgramBody programId={parked.id} />);
    await screen.findByTestId("programs-board");
    expect(parked.state).toBe("parked");
    for (const ordinal of [2, 3]) {
      const row = stepRow(ordinal);
      expect(row.getAttribute("data-state")).toBe("parked");
      expect(within(row).getByTestId("programs-step-words").textContent)
        .toBe(`Step ${ordinal} with Claude Code is parked with the program.`);
      expect(row.querySelector("[data-live]")).toBeNull();
      expect(within(row).queryByTestId("programs-step-take")).toBeNull();
      expect(within(row).queryByTestId("programs-step-open")).toBeNull();
    }
    expect(screen.queryByTestId("programs-your-turn")).toBeNull();
  });
});

// Glue 2026-11-08: a Needs you row that names a step opens the Program window
// at that step (`program:<id>:<step>`); `program:<id>` opens it as before.
describe("the step travels to the Program window", () => {
  const core = yourTurn.your_turn_items.find((item) => item.kind === "core")!;
  const ordinal = yourTurn.steps.find((step) => step.id === core.step_id)!.ordinal;

  it("a `program:<id>:<step>` open selects that step when the window mounts", async () => {
    const { refOpener } = await import("../../openObject");
    hub({ [`GET /api/programs/${yourTurn.id}`]: yourTurn });
    refOpener(`program:${yourTurn.id}:${core.step_id}`)!();
    render(<ProgramBody programId={yourTurn.id} />);
    await screen.findByTestId("programs-your-turn");
    await waitFor(() => expect(stepRow(ordinal).hasAttribute("data-selected")).toBe(true));
    expect(screen.getAllByTestId("programs-step").filter((row) => row.hasAttribute("data-selected"))).toHaveLength(1);
  });

  it("an open window moves to the step asked for; `program:<id>` leaves the selection as it is", async () => {
    const { refOpener } = await import("../../openObject");
    hub({ [`GET /api/programs/${yourTurn.id}`]: yourTurn });
    render(<ProgramBody programId={yourTurn.id} />);
    await screen.findByTestId("programs-your-turn");
    // What waits on him is the headline: no step opens by itself.
    expect(screen.getAllByTestId("programs-step").some((row) => row.hasAttribute("data-selected"))).toBe(false);
    act(() => refOpener(`program:${yourTurn.id}`)!());
    expect(screen.getAllByTestId("programs-step").some((row) => row.hasAttribute("data-selected"))).toBe(false);
    act(() => refOpener(`program:${yourTurn.id}:${core.step_id}`)!());
    await waitFor(() => expect(stepRow(ordinal).hasAttribute("data-selected")).toBe(true));
  });
});

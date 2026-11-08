/* The Programs app (T2), planning in Drafting: the Drafting tray, the
 * planning draft, the rounds, the split into Programs, the audit and the
 * action binding.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  planningFixture, plannedFixture, notPlannedFixture, planFixture, splitFixture, roundsFixture,
  bindingUnboundFixture, bindingBoundFixture, auditDraftingFixture, auditBoardFixture, mocks,
  ApiError, ProgramBody, clone, done, drafting, calls, hub, status, stepRow, openStep,
  type Program, board,
} from "./programs.test-setup";
import { describe, expect, it } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

describe("Create plans itself (#1878): the Drafting tray reads the Program's state (recorded, test_desk_programs.py)", () => {
  const trayVerbs = () => within(screen.getByTestId("programs-tray")).queryAllByRole("button").map((node) => node.textContent);
  // No sentence under a verb: every text in the tray is a verb, a count or the ledger's own line.
  const noProse = () => {
    const tray = screen.getByTestId("programs-tray");
    expect(tray.querySelectorAll(".pg-choice-cons").length).toBeLessThanOrEqual(1);
    expect(tray.textContent).not.toMatch(/The engine drafts|Five rounds of questions|Start will check|Then the first steps/);
  };

  it("planning: the working row with the ledger's line, no verb", async () => {
    const program = planningFixture as unknown as Program;
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    await board();
    const tray = screen.getByTestId("programs-tray");
    expect(tray.getAttribute("data-tray")).toBe("planning");
    expect(trayVerbs()).toEqual([]);
    const row = within(tray).getByTestId("programs-planning");
    expect(row.textContent).toBe("Planning the steps from the goal");
    expect(row.querySelector("[data-live]") ?? row.closest("[data-live]")).toBeTruthy();
    noProse();
  });

  it("planned at normal: Start is the one brass verb, \"4 steps\" the quiet fact", async () => {
    const program = plannedFixture as unknown as Program;
    expect(program.control).toBe("normal");
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    await board();
    expect(trayVerbs()).toEqual(["Start"]);
    expect(screen.getByTestId("program-start").className).toMatch(/brass/);
    expect(screen.getByTestId("programs-start-words").textContent).toBe("4 steps");
    noProse();
  });

  it("not planned: the ledger's line as the notice and Plan it as the one verb", async () => {
    const program = notPlannedFixture as unknown as Program;
    const line = program.checkpoints.find((row) => row.kind === "plan_goal")!.line;
    expect(line).toMatch(/^The steps were not planned · /);
    hub({ [`GET /api/programs/${program.id}`]: program });
    render(<ProgramBody programId={program.id} />);
    await board();
    expect(within(screen.getByTestId("programs-plan-claim")).getByRole("status").textContent).toBe(line);
    expect(trayVerbs()).toEqual(["Plan it"]);
    expect(screen.getByTestId("program-plan-it").className).toMatch(/brass/);
    noProse();
  });
});

describe("JRN1: the draft proposes several Programs (the REAL qwen reply to a three-goal paste)", () => {
  type Plan = import("../types").PlanAnswer;
  const split = splitFixture as unknown as {
    program: Program; draft: Plan; applied: { program: Program; made: { id: string; title: string }[] }; second: Program;
    start_refused: { status: number; body: { detail: string } };
  };

  it("one row per proposed Program with its goal and steps; Apply all makes this the first and links the others", async () => {
    const id = split.program.id;
    hub({
      [`GET /api/programs/${id}`]: split.program,
      [`GET /api/programs/${id}/shape`]: planFixture.engine,
      [`POST /api/programs/${id}/plan/draft`]: split.draft,
      [`POST /api/programs/${id}/plan/programs`]: split.applied,
    });
    render(<ProgramBody programId={id} />);
    await board();
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    fireEvent.click(screen.getByTestId("program-plan-it"));
    const well = await screen.findByTestId("programs-split-well");
    const programs = split.draft.programs!;
    expect(well.textContent).toContain(`Split into ${programs.length} programs`);
    const rows = within(well).getAllByTestId("programs-split-row");
    expect(rows.map((row) => row.querySelector(".pg-split-title")!.textContent)).toEqual(programs.map((row) => row.title));
    expect(rows.map((row) => within(row).getByTestId("programs-split-steps").textContent))
      .toEqual(programs.map((row) => `${row.steps.length} ${row.steps.length === 1 ? "step" : "steps"}`));
    expect(rows[0].querySelectorAll(".pg-station")).toHaveLength(programs[0].steps.length);
    // No diff rows for a split: the well is the programs.
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    fireEvent.click(within(well).getByTestId("programs-split-apply-all"));
    await waitFor(() => expect(within(screen.getByTestId("programs-split-made")).getAllByRole("button").map((b) => b.textContent))
      .toEqual(split.applied.made.map((row) => `Open ${row.title}`)));
    const sent = calls.find((call) => call.startsWith(`POST /api/programs/${id}/plan/programs `))!;
    const body = JSON.parse(sent.slice(sent.indexOf("{")));
    expect(body.which).toBe("all");
    expect(body.programs.map((row: { title: string }) => row.title)).toEqual(programs.map((row) => row.title));
    // The window is now the first program, with its steps.
    await waitFor(() => expect(screen.getAllByTestId("programs-step")).toHaveLength(split.applied.program.steps.length));
  });

  it("a later Program waits on the one before it: Start says so", async () => {
    const second = split.second;
    hub({ [`GET /api/programs/${second.id}`]: second });
    render(<ProgramBody programId={second.id} />);
    await board();
    expect(screen.getByTestId("programs-start-words").textContent).toBe(`After ${split.draft.programs![0].title}`);
    expect(split.start_refused.body.detail).toBe(`It starts after ${split.draft.programs![0].title} is done.`);
  });
});

describe("LANG7: the planning draft (PROGRAM-LANGUAGE §5, §9.3, §9.7)", () => {
  type Plan = import("../types").PlanAnswer;
  type Applied = import("../types").TextApplyAnswer;
  const j1 = planFixture.j1 as unknown as { program: Program; draft: Plan; applied: Applied };
  const big = planFixture.big_file as unknown as { program: Program; draft: Plan; split: Plan };
  const none = planFixture.no_engine as unknown as { program: Program; status: number; body: Record<string, unknown>; engine: unknown };
  const posts = (id: string, tail: string) => calls.filter((call) => call.startsWith(`POST /api/programs/${id}/${tail} `))
    .map((call) => JSON.parse(call.slice(call.indexOf("{"))) as Record<string, unknown>);

  it("Plan it: the draft's rows in the well with their size lamps; Apply writes the steps, born on the board with their sizes", async () => {
    const id = j1.program.id;
    hub({
      [`GET /api/programs/${id}`]: j1.program,
      [`GET /api/programs/${id}/shape`]: planFixture.engine,
      [`POST /api/programs/${id}/plan/draft`]: j1.draft,
      [`POST /api/programs/${id}/text`]: j1.applied,
    });
    render(<ProgramBody programId={id} />);
    await board();
    // Drafting with no steps: Plan it is the primary verb; Start waits for steps.
    const planIt = screen.getByTestId("program-plan-it");
    expect(planIt.className).toMatch(/brass/);
    expect(screen.queryByTestId("program-start")).toBeNull();
    fireEvent.click(planIt);
    const well = await screen.findByTestId("programs-change-well");
    // The goal is the Program's: the hub reads it (and the budget) itself.
    expect(posts(id, "plan/draft")).toEqual([{}]);
    expect(within(well).getByText("4 steps · 6 requirements", { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(within(well).getByText(/^qwen3\.8-27b · under 1 s · 11 changes · 1 refused$/)).toBeInTheDocument();
    const rows = within(well).getAllByTestId("programs-diff-row");
    expect(rows.map((row) => row.getAttribute("data-row"))).toEqual(j1.draft.changes.map((row) => row.id));
    const sized = rows.filter((row) => within(row).queryByTestId("kit-diffrow-aside"));
    expect(sized.map((row) => within(row).getByTestId("kit-diffrow-aside").textContent)).toEqual(
      ["7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]);
    // The rig has no Alice in People: that row is refused by name; Apply applies the rest.
    const alice = rows.find((row) => row.getAttribute("data-row") === "program.for-person")!;
    expect(within(alice).getByTestId("kit-diffrow-verdict").textContent).toBe("Refused");
    expect(within(alice).getByTestId("kit-diffrow-reason").textContent).toContain("There is no person 'Alice' in People.");
    expect(within(well).queryByTestId("programs-diff-split")).toBeNull();
    const apply = within(well).getByTestId("programs-well-apply");
    expect(apply.textContent).toBe("Apply 10");
    fireEvent.click(apply);
    await waitFor(() => expect(posts(id, "text")).toHaveLength(1));
    expect(posts(id, "text")[0]).toEqual({ text: j1.draft.allowed_text, base: j1.draft.base, dry_run: false, allow_lower: [] });
    // The rows land: four drafted steps, each with its size lamp, born one after the other.
    await waitFor(() => expect(screen.getAllByTestId("programs-step")).toHaveLength(4));
    const drafted = screen.getAllByTestId("programs-step");
    expect(drafted.map((row) => within(row).getByTestId("programs-draft-size").textContent)).toEqual(
      ["7k of 32k", "4k of 32k", "5k of 32k", "3k of 32k"]);
    expect(within(stepRow(1)).getByTestId("programs-step-select").textContent).toContain(j1.applied.program!.steps[0].title);
    expect(drafted.every((row) => row.getAttribute("data-landed") === "born")).toBe(true);
    expect(drafted[2].style.getPropertyValue("--i")).toBe("2");
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
    // Steps exist now: Start is the one verb in the tray, with the step count.
    expect(screen.getByTestId("program-start")).not.toBeDisabled();
    expect(screen.queryByTestId("program-plan-it")).toBeNull();
    expect(screen.getByTestId("programs-start-words").textContent).toBe("4 steps");
  });

  it("while the engine plans, one line and the status bar name it; the window stays usable", async () => {
    const id = j1.program.id;
    let answer: (value: unknown) => void = () => undefined;
    hub({
      [`GET /api/programs/${id}`]: j1.program,
      [`GET /api/programs/${id}/shape`]: planFixture.engine,
    });
    const table = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path: string, init?: { method?: string; json?: unknown }) =>
      (init?.method === "POST" && path.endsWith("/plan/draft") ? new Promise((resolve) => { answer = resolve; }) : table(path, init)));
    render(<ProgramBody programId={id} />);
    await board();
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    fireEvent.click(screen.getByTestId("program-plan-it"));
    const reading = await screen.findByTestId("program-plan-reading");
    await waitFor(() => expect(reading.textContent).toBe("Planning · Home Engine"));
    expect(reading.querySelector(".kit-dot")).toHaveAttribute("data-live");
    expect(within(status()).getByTestId("programs-status-planning").textContent).toBe("Planning · Home Engine");
    expect(screen.getByRole("button", { name: "Edit Goal" })).not.toBeDisabled();
    await act(async () => answer(clone(j1.draft)));
    await screen.findByTestId("programs-change-well");
    expect(screen.queryByTestId("program-plan-reading")).toBeNull();
    expect(within(status()).queryByTestId("programs-status-planning")).toBeNull();
  });

  it("the goal is the headline, edited in place; Plan it plans the goal he wrote", async () => {
    const id = j1.program.id;
    hub({
      [`GET /api/programs/${id}`]: j1.program,
      [`GET /api/programs/${id}/shape`]: planFixture.engine,
      [`PATCH /api/programs/${id}`]: j1.program,
      [`POST /api/programs/${id}/plan/draft`]: j1.draft,
    });
    render(<ProgramBody programId={id} />);
    await board();
    // Words until he presses them: no textarea on the face.
    expect(screen.queryByRole("textbox", { name: "Goal" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Edit Goal" }));
    const pad = screen.getByRole("textbox", { name: "Goal" });
    fireEvent.change(pad, { target: { value: "Recap each meeting in its Note." } });
    fireEvent.blur(pad);
    await waitFor(() => expect(calls.some((call) => call.startsWith(`PATCH /api/programs/${id} `))).toBe(true));
    fireEvent.click(screen.getByTestId("program-plan-it"));
    await screen.findByTestId("programs-change-well");
    expect(posts(id, "plan/draft")).toEqual([{ goal: "Recap each meeting in its Note." }]);
  });

  it("a step too big for its engine says so with Split; Split sends the draft and the step's place, the well shows the parts", async () => {
    const id = big.program.id;
    hub({
      [`GET /api/programs/${id}`]: big.program,
      [`GET /api/programs/${id}/shape`]: { ...planFixture.engine, program_id: id },
      [`POST /api/programs/${id}/plan/draft`]: (init?: { json?: { split?: number } }) => (init?.json?.split ? big.split : big.draft),
    });
    render(<ProgramBody programId={id} />);
    await board();
    fireEvent.click(screen.getByTestId("program-plan-it"));
    const well = await screen.findByTestId("programs-change-well");
    expect(within(well).getByText("2 steps · 1 requirement · 1 too big", { selector: ".kit-changewell-say" })).toBeInTheDocument();
    const tooBig = within(well).getAllByTestId("programs-diff-row").find((row) => row.getAttribute("data-row") === "step-2.add")!;
    const aside = within(tooBig).getByTestId("kit-diffrow-aside");
    expect(aside.textContent).toBe("Too big for Claude Code · 61k of 32k");
    expect(aside).toHaveAttribute("data-tone", "fail");
    // It is still a row he may apply (the runner holds it at hand time).
    expect(within(tooBig).getByTestId("kit-diffrow-verdict").textContent).toBe("Allowed");
    fireEvent.click(within(tooBig).getByTestId("programs-diff-split"));
    await waitFor(() => expect(posts(id, "plan/draft")).toHaveLength(2));
    expect(posts(id, "plan/draft")[1]).toEqual({ text: big.draft.proposed_text, split: 2 });
    await waitFor(() => expect(within(screen.getByTestId("programs-change-well")).getAllByTestId("kit-diffrow-aside")
      .map((node) => node.textContent)).toEqual(
      ["1k of 32k", "Too big for Claude Code · 61k of 32k", "Too big for Claude Code · 61k of 32k"]));
  });

  it("no engine: the refusal in place of the lamp, with Open Engines and Open text; nothing is sent", async () => {
    const id = none.program.id;
    hub({
      [`GET /api/programs/${id}`]: none.program,
      [`GET /api/programs/${id}/shape`]: none.engine,
      [`POST /api/programs/${id}/plan/draft`]: () => { throw new ApiError(none.status, String(none.body.detail), none.body); },
      [`GET /api/programs/${id}/text`]: { program_id: id, text: j1.draft.base, revision: 1, version: 1 },
    });
    render(<ProgramBody programId={id} />);
    await board();
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    fireEvent.click(screen.getByTestId("program-plan-it"));
    const refusal = await screen.findByTestId("program-plan-refusal");
    expect(posts(id, "plan/draft")).toHaveLength(0);
    expect(refusal.textContent).toContain("No engine is set for planning");
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    fireEvent.click(within(refusal).getByTestId("program-plan-engines"));
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
    fireEvent.click(within(refusal).getByTestId("program-plan-text"));
    await screen.findByTestId("programs-text");
  });

  it("a press before the engine's read lands reads it first: nothing is sent, the refusal is the same (the sweep's 409)", async () => {
    const id = none.program.id;
    let release: (() => void) | null = null;
    const held = new Promise<void>((resolve) => { release = resolve; });
    let reads = 0;
    hub({
      [`GET /api/programs/${id}`]: none.program,
      // The first read is slow (still out when he presses); the press reads again.
      [`GET /api/programs/${id}/shape`]: () => { reads += 1; return reads === 1 ? held.then(() => none.engine) : none.engine; },
      [`POST /api/programs/${id}/plan/draft`]: () => { throw new ApiError(none.status, String(none.body.detail), none.body); },
    });
    render(<ProgramBody programId={id} />);
    await board();
    fireEvent.click(screen.getByTestId("program-plan-it"));
    const refusal = await screen.findByTestId("program-plan-refusal");
    expect(refusal.textContent).toContain("No engine is set for planning");
    expect(posts(id, "plan/draft")).toHaveLength(0);
    release!();
  });
});

describe("LANG10: the interview rounds, one question in place (PROGRAM-LANGUAGE §6.2, §9.4 R-A)", () => {
  type Pressed = import("../types").RoundPressed;
  type Asked = import("../types").RoundAsked;
  type RoundAnswer = import("../types").RoundAnswer;
  type Applied = import("../types").TextApplyAnswer;
  const fx = roundsFixture as unknown as {
    program: Program; engine: unknown; draft: import("../types").PlanAnswer; applied: Applied; opened: Pressed;
    started: Program; reopened: Pressed; ask_failed: { status: number; body: Record<string, unknown> };
    steps: {
      "architecture.next": Asked; "architecture.answer": RoundAnswer; "architecture.next2": Asked; "architecture.apply": Applied;
      "architecture.skip_question": Pressed; "architecture.done": Pressed; "product.next": Asked; "product.skip": Pressed;
      "stack.next": Asked;
    };
  };
  const steps = fx.steps;
  const id = fx.program.id;
  const posts = (tail: string) => calls.filter((call) => call.startsWith(`POST /api/programs/${id}/${tail} `))
    .map((call) => JSON.parse(call.slice(call.indexOf("{"))) as Record<string, unknown>);
  const token = (name: string) => within(screen.getByTestId("program-round-strip")).getByRole("button", { name: new RegExp(`^${name} · `) });

  function walkHub() {
    let asked = 0;
    hub({
      [`GET /api/programs/${id}`]: fx.program,
      [`GET /api/programs/${id}/shape`]: fx.engine,
      [`POST /api/programs/${id}/plan/draft`]: fx.draft,
      [`POST /api/programs/${id}/text`]: (init?: { json?: { text?: string } }) =>
        (init?.json?.text === fx.draft.allowed_text ? fx.applied : steps["architecture.apply"]),
      [`POST /api/programs/${id}/rounds`]: fx.opened,
      [`POST /api/programs/${id}/rounds/Architecture/next`]: () => (asked++ ? steps["architecture.next2"] : steps["architecture.next"]),
      [`POST /api/programs/${id}/rounds/Architecture/answer`]: (init?: { json?: { skip?: boolean } }) =>
        (init?.json?.skip ? steps["architecture.skip_question"] : steps["architecture.answer"]),
      [`POST /api/programs/${id}/rounds/Architecture/decide`]: steps["architecture.done"],
      [`POST /api/programs/${id}/rounds/Product/next`]: steps["product.next"],
      [`POST /api/programs/${id}/rounds/Product/decide`]: steps["product.skip"],
      [`POST /api/programs/${id}/rounds/Stack/next`]: steps["stack.next"],
    });
  }

  it("Plan it, then Ask me first: the draft lands, the five rounds open, Architecture asks one question", async () => {
    walkHub();
    render(<ProgramBody programId={id} />);
    await board();
    // No strip before the rounds open; Ask me first sits beside Plan it.
    expect(screen.queryByTestId("program-round-strip")).toBeNull();
    expect(screen.getByTestId("program-ask-first").textContent).toBe("Ask me first");
    fireEvent.click(screen.getByTestId("program-plan-it"));
    await screen.findByTestId("programs-change-well");
    fireEvent.click(screen.getByTestId("program-ask-first"));
    const question = await screen.findByTestId("program-question");
    // The draft's allowed rows applied first, then the rounds, then one question.
    expect(posts("text")).toEqual([{ text: fx.draft.allowed_text, base: fx.draft.base, dry_run: false, allow_lower: [] }]);
    expect(posts("rounds")).toEqual([{}]);
    expect(posts("rounds/Architecture/next")).toEqual([{}]);
    const q1 = steps["architecture.next"].question!;
    expect(within(question).getByText(q1.text)).toHaveClass("kit-question-text");
    expect(within(question).getByText(q1.why!)).toHaveClass("kit-question-why");
    expect(within(question).getAllByTestId("kit-question-choice").map((node) => node.textContent)).toEqual(q1.choices);
    expect(within(question).getByRole("textbox", { name: "Your answer" })).toBeInTheDocument();
    expect(within(question).getByTestId("kit-question-skip").textContent).toBe("Skip question");
    // The strip: five tokens, Architecture on and breathing, the others open (hollow).
    const strip = screen.getByTestId("program-round-strip");
    expect(within(strip).getAllByRole("button").filter((node) => node.classList.contains("surface-filter-token"))
      .map((node) => node.getAttribute("aria-label"))).toEqual([
      "Architecture · asking", "Product · open", "Stack · open", "Verification · open", "Delivery · open"]);
    expect(token("Architecture")).toHaveAttribute("data-filter-active");
    expect(token("Architecture").querySelector(".surface-filter-lamp")).toHaveAttribute("data-live");
    expect(token("Product").querySelector(".surface-filter-lamp")).toHaveAttribute("data-tone", "idle");
    // Done with Architecture waits while a question waits; Skip round is always there.
    const done = screen.getByTestId("program-round-done");
    expect(done.textContent).toBe("Done with Architecture");
    expect(done).toBeDisabled();
    expect(done).toHaveAttribute("title", "A question waits");
    expect(screen.getByTestId("program-round-skip")).not.toBeDisabled();
    // Steps exist now: Ask me first has done its work.
    expect(screen.queryByTestId("program-ask-first")).toBeNull();
  });

  it("an offered answer becomes rows in the well, the question folds, the next one rises; Apply lands step 3", async () => {
    walkHub();
    render(<ProgramBody programId={id} />);
    await board();
    fireEvent.click(screen.getByTestId("program-ask-first"));
    const question = await screen.findByTestId("program-question");
    const q1 = steps["architecture.next"].question!;
    fireEvent.click(within(question).getAllByTestId("kit-question-choice")[0]);
    const well = await screen.findByTestId("programs-change-well");
    expect(posts("rounds/Architecture/answer")).toEqual([{ question_id: q1.id, option: q1.choices[0], apply: false }]);
    const answered = steps["architecture.answer"];
    expect(within(well).getByText(answered.say, { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(within(well).getAllByTestId("programs-diff-row").map((row) => row.getAttribute("data-row"))).toEqual(
      answered.changes.map((row) => row.id));
    // The answered question folds to one line with what it became; the next question rises in.
    await waitFor(() => expect(posts("rounds/Architecture/next")).toHaveLength(2));
    const fold = await screen.findByTestId("program-round-fold");
    expect(fold.textContent).toBe(`?${q1.text}= ${q1.choices[0]}→ step 3 brief`);
    const q2 = steps["architecture.next2"].question!;
    await waitFor(() => expect(within(screen.getByTestId("program-question")).getByText(q2.text)).toBeInTheDocument());
    // Apply: the answer's rows land; step 3 changed on the board.
    fireEvent.click(within(screen.getByTestId("programs-change-well")).getByTestId("programs-well-apply"));
    await waitFor(() => expect(posts("text")).toHaveLength(1));
    expect(posts("text")[0]).toEqual({ text: answered.proposed_text, base: answered.base, dry_run: false, allow_lower: [] });
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
    const drafted = screen.getAllByTestId("programs-step");
    expect(drafted[2]).toHaveAttribute("data-landed", "changed");
  });

  it("Skip question, Done with Architecture (it keeps its count), Product asks; Skip round strikes it and Stack asks", async () => {
    walkHub();
    render(<ProgramBody programId={id} />);
    await board();
    fireEvent.click(screen.getByTestId("program-ask-first"));
    let question = await screen.findByTestId("program-question");
    fireEvent.click(within(question).getAllByTestId("kit-question-choice")[0]);
    const q2 = steps["architecture.next2"].question!;
    await waitFor(() => expect(within(screen.getByTestId("program-question")).getByText(q2.text)).toBeInTheDocument());
    fireEvent.click(within(screen.getByTestId("programs-change-well")).getByTestId("programs-well-apply"));
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
    // Skip question: nothing waits; Done with Architecture is free, and Next question is there.
    fireEvent.click(within(screen.getByTestId("program-question")).getByTestId("kit-question-skip"));
    await waitFor(() => expect(screen.queryByTestId("program-question")).toBeNull());
    expect(posts("rounds/Architecture/answer")[1]).toEqual({ question_id: q2.id, skip: true });
    expect(screen.getByTestId("program-round-next").textContent).toBe("Next question");
    expect(screen.getAllByTestId("program-round-fold").map((node) => node.textContent)).toEqual([
      expect.stringContaining("→ step 3 brief"), `?${q2.text}Skipped`]);
    const done = screen.getByTestId("program-round-done");
    expect(done).not.toBeDisabled();
    fireEvent.click(done);
    // The round closes: its token turns ok and keeps "1 change"; Product asks next.
    question = await screen.findByTestId("program-question");
    expect(posts("rounds/Architecture/decide")).toEqual([{ choice: "done" }]);
    expect(posts("rounds/Product/next")).toEqual([{}]);
    expect(within(question).getByText(steps["product.next"].question!.text)).toBeInTheDocument();
    expect(token("Architecture").querySelector(".surface-filter-lamp")).toHaveAttribute("data-tone", "ok");
    expect(within(token("Architecture")).getByText("· 1 change")).toHaveClass("surface-filter-aside");
    expect(token("Product")).toHaveAttribute("data-filter-active");
    fireEvent.click(screen.getByTestId("program-round-skip"));
    await waitFor(() => expect(posts("rounds/Stack/next")).toEqual([{}]));
    expect(posts("rounds/Product/decide")).toEqual([{ choice: "skip" }]);
    await waitFor(() => expect(within(screen.getByTestId("program-question")).getByText(steps["stack.next"].question!.text)).toBeInTheDocument());
    expect(within(token("Product")).getByText("Product")).toHaveClass("surface-filter-struck");
  });

  it("while it runs, the strip stays; a done round has Ask more; an engine that fails says so", async () => {
    const started = fx.started;
    hub({
      [`GET /api/programs/${id}`]: started,
      [`GET /api/programs/${id}/shape`]: fx.engine,
      [`POST /api/programs/${id}/rounds/Architecture/decide`]: fx.reopened,
      [`POST /api/programs/${id}/rounds/Architecture/next`]: () => { throw new ApiError(fx.ask_failed.status, String(fx.ask_failed.body.detail), fx.ask_failed.body); },
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("program-round-strip");
    expect(screen.queryByTestId("program-ask-first")).toBeNull();
    // Nothing waits: no question row; he picks the done round.
    expect(screen.queryByTestId("program-question")).toBeNull();
    fireEvent.click(token("Architecture"));
    const more = await screen.findByTestId("program-round-ask-more");
    fireEvent.click(more);
    await waitFor(() => expect(posts("rounds/Architecture/decide")).toEqual([{ choice: "reopen" }]));
    const failure = await screen.findByTestId("program-round-failure");
    expect(failure.textContent).toBe(String(fx.ask_failed.body.detail));
    expect(token("Architecture").querySelector(".surface-filter-lamp")).toHaveAttribute("data-tone", "idle");
  });
});

describe("PG-LANG JRN8 to JRN10: an audit in the Program window (recorded: test_desk_program_audit.py)", () => {
  it("in Drafting it says it writes nothing, and each step names the surface it reads", async () => {
    const audit = auditDraftingFixture as unknown as Program;
    hub({ [`GET /api/programs/${audit.id}`]: audit });
    render(<ProgramBody programId={audit.id} />);
    await board();
    expect(screen.getByTestId("programs-audit-line").textContent).toBe("Reviewer only: nothing is written");
    expect(within(stepRow(1)).getByTestId("programs-step-words").textContent).toBe("Reads web/src/desk/notes/");
    expect(within(stepRow(2)).getByTestId("programs-step-words").textContent).toBe("Reads web/src/desk/programs/");
    // The step's fold says Reads, not Owns.
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-select"));
    expect((await screen.findByTestId("programs-step-owns")).textContent).toBe("Readsweb/src/desk/notes/");
    // No board before a report.
    expect(screen.queryByTestId("programs-findings")).toBeNull();
    // The owner, 2026-11-01: with no requirement, no empty Done when section;
    // only Add a requirement, on its own line. The goal is drawn once.
    expect(audit.requirements ?? []).toEqual([]);
    const done = screen.getByTestId("programs-done-when");
    expect(done.textContent).toBe("Add a requirement");
    expect(done.querySelector(".pg-done-when-mark")).toBeNull();
    expect(screen.getAllByText(audit.goal)).toHaveLength(1);
    fireEvent.click(within(done).getByTestId("programs-done-add-requirement"));
    expect(within(screen.getByTestId("programs-done-when")).getByText("Done when")).toBeTruthy();
  });

  it("a done audit: its track ends at File, and its findings are rows in the window, filed ones open their Door task", async () => {
    const audit = auditBoardFixture as unknown as Program;
    hub({ [`GET /api/programs/${audit.id}`]: audit });
    render(<ProgramBody programId={audit.id} />);
    await board();
    expect(screen.queryByTestId("programs-audit-line")).toBeNull();
    const findings = screen.getByTestId("programs-findings");
    expect(within(findings).getByRole("heading").textContent).toBe("Findings · 4 findings · 2 MUST");
    const rows = within(findings).getAllByTestId("programs-finding");
    expect(rows.map((row) => row.querySelector(".pg-finding-text")!.textContent)).toEqual([
      "Must fix: The Notes toolbar wraps at 520",
      "Must fix: The Programs list cuts the title at 393",
      "Should fix: The Notes title is grey on grey",
      "Noted: Notes is fine at 393",
    ]);
    expect(rows[0].textContent).toContain(
      "Steps 1 and 2 · Evidence: .tmp/evidence-shots/notes-520.png, .tmp/evidence-shots/programs-notes.png");
    expect(rows[3].textContent).toContain("Step 1");
    expect(rows[3].textContent).not.toContain("Evidence");
    fireEvent.click(within(rows[1]).getByTestId("programs-finding-task"));
    expect(mocks.openRef).toHaveBeenCalledWith(`action:${audit.findings_board!.rows[1].task_id}`);
    // The step's track: Brief · Work · Review · File; nothing is merged.
    fireEvent.click(within(stepRow(1)).getByTestId("programs-step-select"));
    fireEvent.click(within(await screen.findByTestId("programs-step-fold")).getByRole("button", { name: "Gate" }));
    const track = within(await screen.findByTestId("programs-gate")).getByTestId("programs-gate-track");
    expect(track.textContent).toContain("File");
    expect(track.textContent).toContain("Review");
    expect(track.textContent).not.toContain("Merge");
    expect(track.textContent).not.toContain("Check");
  });
});

describe("HS-S21: Add binds the action to one new step (D14/G21 = A)", () => {
  const unbound = bindingUnboundFixture as unknown as Program;
  const bound = bindingBoundFixture as unknown as Program;
  const plans = () => calls.filter((call) => call.startsWith(`POST /api/programs/`) && call.includes("/plan "));
  const newRow = (program: Program, extra: Record<string, unknown> = {}) => ({
    title: `Step ${program.steps.length + 1}`, brief: "", profile: program.default.profile, engine: program.default.engine?.id ?? null, ...extra,
  });

  it("Add in Drafting appends only the new row; the rows there are not sent again", async () => {
    hub({ [`GET /api/programs/${drafting.id}`]: drafting, [`POST /api/programs/${drafting.id}/plan`]: { program: drafting } });
    render(<ProgramBody programId={drafting.id} />);
    fireEvent.click(await screen.findByTestId("program-add-step"));
    // No action: no well, one press appends.
    expect(screen.queryByTestId("program-add-well")).toBeNull();
    await waitFor(() => expect(plans()).toHaveLength(1));
    expect(plans()[0]).toBe(`POST /api/programs/${drafting.id}/plan ${JSON.stringify({ steps: [newRow(drafting)], replace: false, size: null })}`);
  });

  it("a Program made from an action: the choice is off, Cancel sends nothing, the bound Add carries only the new row", async () => {
    hub({ [`GET /api/programs/${unbound.id}`]: unbound, [`POST /api/programs/${unbound.id}/plan`]: { program: bound } });
    render(<ProgramBody programId={unbound.id} />);
    fireEvent.click(await screen.findByTestId("program-add-step"));
    const well = screen.getByTestId("program-add-well");
    const title = unbound.place.origin!.title;
    const box = within(well).getByLabelText(`This step carries the action ${title}`) as HTMLInputElement;
    expect(box.checked).toBe(false);
    expect(within(well).getByTestId("program-add-words").textContent).toBe("The step does not carry the action.");
    fireEvent.click(within(well).getByTestId("program-add-cancel"));
    expect(screen.queryByTestId("program-add-well")).toBeNull();
    expect(plans()).toEqual([]);

    fireEvent.click(screen.getByTestId("program-add-step"));
    fireEvent.click(screen.getByLabelText(`This step carries the action ${title}`));
    expect(screen.getByTestId("program-add-words").textContent).toBe("When this step is done, the action is done.");
    fireEvent.click(screen.getByTestId("program-add-confirm"));
    await waitFor(() => expect(screen.queryByTestId("program-add-well")).toBeNull());
    expect(plans()).toEqual([`POST /api/programs/${unbound.id}/plan ${JSON.stringify({
      steps: [newRow(unbound, { origin_ref: unbound.origin_ref })], replace: false, size: null })}`]);
    // The answer's rows: step 1 is as it was, step 2 says what it carries (words, no opener).
    expect(screen.getAllByTestId("programs-step")).toHaveLength(2);
    expect(within(openStep(1)).queryByTestId("programs-step-carries")).toBeNull();
    const line = within(openStep(2)).getByTestId("programs-step-carries");
    expect(line.textContent).toBe(`Carries the action ${title}`);
    expect(line.getAttribute("data-origin")).toBe(unbound.origin_ref);
    expect(within(line).queryByRole("button")).toBeNull();
    expect(line.textContent).not.toMatch(/done|closed/i);
    // A row carries it now: the next Add is ordinary (no second binding offered).
    fireEvent.click(screen.getByTestId("program-add-step"));
    expect(screen.queryByTestId("program-add-well")).toBeNull();
    await waitFor(() => expect(plans()).toHaveLength(2));
    expect(plans()[1]).toBe(`POST /api/programs/${unbound.id}/plan ${JSON.stringify({ steps: [newRow(bound)], replace: false, size: null })}`);
  });

  it("the bulk agent change holds a Program that carries an action; no plan is sent", async () => {
    hub({ [`GET /api/programs/${bound.id}`]: bound });
    render(<ProgramBody programId={bound.id} />);
    fireEvent.click(await screen.findByTestId("program-runs-on"));
    fireEvent.click(await screen.findByText("Codex · Ready"));
    const failure = await screen.findByTestId("program-failure");
    expect(failure.textContent).toBe("The steps carry an action · No step changed · Change the agent in each step's brief");
    expect(plans()).toEqual([]);
    // The step's own agent stays a per-step change.
    const fold = openStep(2);
    expect(within(fold).getByLabelText("Step 2 agent")).toBeTruthy();
  });

  it("the bulk agent change reads the Program first; a failed read or a new action row sends no plan", async () => {
    let reads = 0;
    hub({
      [`GET /api/programs/${drafting.id}`]: () => {
        reads += 1;
        if (reads === 2) throw new ApiError(503, "Service Unavailable", {});
        if (reads === 3) {
          const now = clone(drafting);
          now.steps[1].origin_ref = "action:ai_elsewhere";
          return now;
        }
        return drafting;
      },
      [`POST /api/programs/${drafting.id}/plan`]: { program: drafting },
    });
    render(<ProgramBody programId={drafting.id} />);
    fireEvent.click(await screen.findByTestId("program-runs-on"));
    fireEvent.click(await screen.findByText("Codex · Ready"));
    expect((await screen.findByTestId("program-failure")).textContent).toMatch(/^The agent was not changed · No step changed/);
    fireEvent.click(screen.getByTestId("program-runs-on"));
    fireEvent.click(await screen.findByText("Codex · Ready"));
    await waitFor(() => expect(screen.getByTestId("program-failure").textContent).toMatch(/^The steps carry an action/));
    expect(plans()).toEqual([]);
  });

  it("an Add the hub refused says so; an Add with no answer reads the steps and is not sent again", async () => {
    let posts = 0;
    hub({
      [`GET /api/programs/${unbound.id}`]: unbound,
      [`POST /api/programs/${unbound.id}/plan`]: () => {
        posts += 1;
        if (posts === 1) throw new ApiError(409, "Conflict", { detail: "Steps that started cannot be replaced." });
        throw new TypeError("Failed to fetch");
      },
    });
    render(<ProgramBody programId={unbound.id} />);
    fireEvent.click(await screen.findByTestId("program-add-step"));
    fireEvent.click(screen.getByTestId("program-add-confirm"));
    expect((await screen.findByTestId("program-failure")).textContent).toMatch(/^The step was not added · The program is unchanged/);
    // The well stays, with his choice, for a deliberate press.
    expect(screen.getByTestId("program-add-well")).toBeTruthy();
    const readsBefore = calls.filter((call) => call === `GET /api/programs/${unbound.id}`).length;
    fireEvent.click(screen.getByTestId("program-add-confirm"));
    await waitFor(() => expect(screen.getByTestId("program-failure").textContent).toMatch(/^The hub did not confirm the step · It can be on the program/));
    await waitFor(() => expect(calls.filter((call) => call === `GET /api/programs/${unbound.id}`).length).toBe(readsBefore + 1));
    expect(posts).toBe(2);
  });
});

/* The Programs app (T2), the Program text and the shaping bar: the Text
 * view, a typed sentence and the voice.
 *
 * The mocks, the recorded hub answers and the helpers are in
 * programs.test-setup.tsx, shared by every programs.*.app.test.tsx. */
import {
  textFixture, textApplyFixture, shapeFixture, mocks, mic, ApiError, ProgramBody, useDesk, clone,
  done, calls, hub, status, stepRow, type Answer, type Program,
} from "./programs.test-setup";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";

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
    expect(screen.getAllByTestId("kit-textpane-line")[refusedRow.line! - 1]).toHaveAttribute("data-mark", "!");
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
    await waitFor(() => expect(within(stepRow(3)).getByTestId("programs-step-select").textContent).toContain("Loop watch"));
    expect(within(stepRow(4)).getByTestId("programs-step-select").textContent).toContain("The fan-out");
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

describe("LANG5: shaping by voice (PROGRAM-LANGUAGE §4.2, §10; PROGRAM-JOURNEYS J3)", () => {
  type Shape = import("../types").ShapeAnswer;
  type Applied = import("../types").TextApplyAnswer;
  const voice = shapeFixture.voice as unknown as { program: Program; shapes: Shape[]; applied: Applied };
  const yolo = shapeFixture.yolo as unknown as { program: Program };
  const question = shapeFixture.question as unknown as Shape;
  const later = shapeFixture.call_later as unknown as { program: Program; dropped: Program };
  const posts = (id: string, tail: string) => calls.filter((call) => call.startsWith(`POST /api/programs/${id}/${tail}`))
    .map((call) => JSON.parse(call.slice(call.indexOf("{"))) as Record<string, unknown>);
  const bar = () => screen.getByTestId("program-shape-bar");
  const field = () => within(bar()).getByRole("textbox", { name: "Change the program" }) as HTMLInputElement;
  /** He presses the bar's mic, says the words, presses it again: the capture's end. */
  const speak = async (words: string, micName = "Speak a change to the program") => {
    mic.startStreamSession.mockResolvedValueOnce({ stop: vi.fn().mockResolvedValue(words), cancel: vi.fn() });
    fireEvent.click(within(bar()).getByRole("button", { name: micName }));
    const stop = await within(bar()).findByRole("button", { name: "Stop listening" });
    fireEvent.click(stop);
  };
  beforeEach(() => { mic.supported = true; });

  it("the end of a dictation sends the sentence at once; the bar says what it heard while the engine reads; the rows land", async () => {
    const id = voice.program.id;
    let answer: (value: unknown) => void = () => undefined;
    hub({
      [`GET /api/programs/${id}`]: voice.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
    });
    const table = mocks.apiFetch.getMockImplementation()!;
    mocks.apiFetch.mockImplementation((path: string, init?: { method?: string; json?: unknown }) => {
      if (init?.method === "POST" && path.endsWith("/shape")) {
        calls.push(`POST ${path} ${JSON.stringify(init.json)}`);
        return new Promise((resolve) => { answer = resolve; });
      }
      return table(path, init);
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    await speak(voice.shapes[0].sentence);
    // No Shape press: the capture's end sent it.
    await waitFor(() => expect(posts(id, "shape")).toHaveLength(1));
    expect(posts(id, "shape")[0]).toEqual({ sentence: voice.shapes[0].sentence, apply: false });
    expect(field().value).toBe(voice.shapes[0].sentence);
    expect(bar()).toHaveAttribute("data-settle");
    expect(screen.getByTestId("program-shape-heard").textContent).toBe(`Heard: ${voice.shapes[0].sentence}`);
    expect(screen.getByTestId("program-shape-reading").textContent).toBe("Reading the program · Home Engine");
    await act(async () => answer(clone(voice.shapes[0])));
    const well = await screen.findByTestId("programs-change-well");
    expect(screen.queryByTestId("program-shape-heard")).toBeNull();
    expect(within(well).getAllByTestId("programs-diff-row").map((row) => row.getAttribute("data-row")))
      .toEqual(voice.shapes[0].changes.map((row) => row.id));
    expect(within(well).getByText(voice.shapes[0].say, { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(field().value).toBe("");
  });

  it("\"program: …\" is the shape intent: the address is read off by rule and the sentence goes to the hub", async () => {
    const id = voice.program.id;
    hub({
      [`GET /api/programs/${id}`]: voice.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: () => clone(voice.shapes[0]),
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    await speak(`Program: ${voice.shapes[0].sentence}`);
    await waitFor(() => expect(posts(id, "shape")).toHaveLength(1));
    expect(posts(id, "shape")[0]).toEqual({ sentence: voice.shapes[0].sentence, apply: false });
    await screen.findByTestId("programs-change-well");
  });

  it("three sentences in a row: each goes with the rows that wait; the one well holds all three; one Apply lands them", async () => {
    const id = voice.program.id;
    let turn = 0;
    hub({
      [`GET /api/programs/${id}`]: voice.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: () => voice.shapes[turn++],
      [`POST /api/programs/${id}/text`]: voice.applied,
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    for (const [index, shape] of voice.shapes.entries()) {
      await speak(shape.sentence);
      await waitFor(() => expect(posts(id, "shape")).toHaveLength(index + 1));
      await waitFor(() => expect(within(screen.getByTestId("programs-change-well")).getAllByTestId("programs-diff-row"))
        .toHaveLength(shape.changes.length));
    }
    const bodies = posts(id, "shape");
    expect(bodies[0]).toEqual({ sentence: voice.shapes[0].sentence, apply: false });
    expect(bodies[1]).toEqual({ sentence: voice.shapes[1].sentence, apply: false, pending: voice.shapes[0].proposed_text });
    expect(bodies[2]).toEqual({ sentence: voice.shapes[2].sentence, apply: false, pending: voice.shapes[1].proposed_text });
    const well = screen.getByTestId("programs-change-well");
    // Every sentence's rows, against the text as it is now, and each sentence's line.
    expect(within(well).getAllByTestId("programs-diff-row").map((row) => row.getAttribute("data-row")))
      .toEqual(voice.shapes[2].changes.map((row) => row.id));
    expect(within(well).getByText(voice.shapes.map((shape) => shape.say).join("; "), { selector: ".kit-changewell-say" }))
      .toBeInTheDocument();
    // The engine wrote "R4" for the new ruff requirement: refused by name; Apply lands the rest.
    const refused = within(well).getAllByTestId("programs-diff-row").find((row) => row.getAttribute("data-row") === "R4.unknown")!;
    expect(within(refused).getByTestId("kit-diffrow-verdict").textContent).toBe("Refused");
    const apply = within(well).getByTestId("programs-well-apply");
    expect(apply.textContent).toBe(`Apply ${voice.shapes[2].changes.length - 1}`);
    fireEvent.click(apply);
    await waitFor(() => expect(posts(id, "text")).toHaveLength(1));
    expect(posts(id, "text")[0]).toEqual({ text: voice.shapes[2].allowed_text, base: voice.shapes[2].base, dry_run: false,
      allow_lower: [] });
    await waitFor(() => expect(within(stepRow(3)).getByTestId("programs-step-select").textContent).toContain("Loop watch"));
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
  });

  it("a question back after a spoken sentence: the question in place, the mic named for the answer; the answer goes with the first", async () => {
    const id = yolo.program.id;
    hub({
      [`GET /api/programs/${id}`]: yolo.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`POST /api/programs/${id}/shape`]: question,
    });
    render(<ProgramBody programId={id} />);
    await screen.findByTestId("programs-board");
    await waitFor(() => expect(calls).toContain(`GET /api/programs/${id}/shape`));
    await speak(question.sentence);
    const asked = await screen.findByTestId("program-shape-question");
    expect(asked.textContent).toBe(question.question);
    expect(screen.queryByTestId("programs-change-well")).toBeNull();
    await speak("step 3 before step 2", "Speak your answer");
    await waitFor(() => expect(posts(id, "shape")).toHaveLength(2));
    expect(posts(id, "shape")[1]).toEqual({ sentence: `${question.sentence} step 3 before step 2`, apply: true });
  });

  it("rows a call left for his press open the well; Not this drops them on the hub", async () => {
    const id = later.program.id;
    const held = later.program.held_shape!;
    hub({
      [`GET /api/programs/${id}`]: later.program,
      [`GET /api/programs/${id}/shape`]: shapeFixture.engine,
      [`DELETE /api/programs/${id}/shape/held`]: later.dropped,
    });
    render(<ProgramBody programId={id} />);
    const well = await screen.findByTestId("programs-change-well");
    expect(within(well).getByText(held.say, { selector: ".kit-changewell-say" })).toBeInTheDocument();
    expect(within(well).getByText(/^On a call · qwen3\.8-27b · under 1 s · /)).toBeInTheDocument();
    expect(within(well).getAllByTestId("programs-diff-row").map((row) => row.getAttribute("data-row")))
      .toEqual(held.changes.map((row) => row.id));
    fireEvent.click(within(well).getByTestId("programs-well-not-this"));
    await waitFor(() => expect(calls).toContain(`DELETE /api/programs/${id}/shape/held`));
    await waitFor(() => expect(screen.queryByTestId("programs-change-well")).toBeNull());
  });
});

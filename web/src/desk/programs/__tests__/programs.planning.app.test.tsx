import { useState } from "react";
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import {
  shapeFixture,
  planFixture,
  splitFixture,
  textFixture,
  roundsFixture,
  mocks,
  mic,
  hub,
  clone,
  ApiError,
  type Program,
} from "./programs.seats.test-setup";
import { ProgramForm } from "../ProgramForm";
import { ProgramDetail } from "../ProgramWindow";
import { ProgramInterview } from "../ProgramInterview";
import { useProgram } from "../api";
import type { ShapeAnswer, PlanAnswer, TextApplyAnswer } from "../types";
const normal = shapeFixture.normal as unknown as {
  program: Program;
  shape: ShapeAnswer;
  applied: TextApplyAnswer;
};
const yolo = shapeFixture.yolo as unknown as {
  program: Program;
  shape: ShapeAnswer;
  overturned: Program;
};
const voice = shapeFixture.voice as unknown as {
  program: Program;
  shapes: ShapeAnswer[];
  applied: TextApplyAnswer;
};
const big = planFixture.big_file as unknown as {
  program: Program;
  draft: PlanAnswer;
  split: PlanAnswer;
};
const split = splitFixture as unknown as {
  program: Program;
  draft: PlanAnswer;
  applied: { program: Program; made: { id: string; title: string }[] };
};
const tab = (name: string) =>
  fireEvent.click(screen.getByRole("tab", { name }));
const press = (name: string) => {
  const q = document.querySelector<HTMLElement>("[data-question]");
  fireEvent.click(
    q
      ? (within(q).queryByRole("button", { name }) ??
          screen.getByRole("button", { name }))
      : screen.getByRole("button", { name }),
  );
};
const type = (name: string, value: string) =>
  fireEvent.change(screen.getByLabelText(name), { target: { value } });
function Form({ initial }: { initial: Program }) {
  const query = useProgram(initial.id),
    [done, setDone] = useState(false);
  const p = query.program ?? initial;
  return done ? (
    <ProgramDetail
      program={p}
      loading={false}
      error={null}
      reload={query.reload}
      onError={() => {}}
      onApplied={query.apply}
    />
  ) : (
    <ProgramForm
      kind="amend"
      program={p}
      onCancel={() => setDone(true)}
      onApplied={(p) => {
        query.apply(p);
        setDone(true);
      }}
    />
  );
}
function base(p: Program, extra: Record<string, unknown> = {}) {
  hub({
    [`GET /api/programs/${p.id}`]: p,
    [`GET /api/programs/${p.id}/shape`]: shapeFixture.engine,
    ...extra,
  });
}
async function preview(words: string) {
  type("Program change", words);
  press("Preview");
  await screen.findByRole("grid", { name: "Text changes" });
}
function selectChange(id: string) {
  fireEvent.click(
    screen
      .getByRole("grid", { name: "Text changes" })
      .querySelector(`[data-object-id="${id}"]`)!,
  );
}
describe("Amend and planning seats on the recorded engine tape", () => {
  it("a typed sentence previews the recorded changes, permits a lowering row by press and applies with the binding", async () => {
    base(normal.program, {
      [`POST /api/programs/${normal.program.id}/shape`]: normal.shape,
      [`POST /api/programs/${normal.program.id}/text`]: normal.applied,
    });
    render(<Form initial={normal.program} />);
    await preview(normal.shape.sentence);
    selectChange("program.control");
    fireEvent.click(
      screen.getByRole("checkbox", { name: "Allow this change" }),
    );
    press("Apply");
    press("Apply");
    await screen.findByRole("tab", { name: "Now" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/text"),
      expect.objectContaining({
        json: expect.objectContaining({
          dry_run: false,
          allow_lower: ["program.control"],
          base: normal.shape.base,
          binding: expect.objectContaining({ program_id: normal.program.id }),
        }),
      }),
    );
    tab("Steps");
    expect(screen.getByRole("grid", { name: "Steps" }).textContent).toContain(
      "Loop watch",
    );
  });
  it("a question back combines his next sentence with the first before it previews", async () => {
    let at = 0;
    const question = shapeFixture.question as unknown as ShapeAnswer;
    base(normal.program, {
      [`POST /api/programs/${normal.program.id}/shape`]: () =>
        at++ ? normal.shape : question,
    });
    render(<Form initial={normal.program} />);
    type("Program change", question.sentence);
    press("Preview");
    await screen.findByText(question.question!);
    type("Program change", "Use the saved reason.");
    press("Preview");
    await screen.findByRole("grid", { name: "Text changes" });
    expect(mocks.apiFetch).toHaveBeenLastCalledWith(
      expect.stringContaining("/shape"),
      expect.objectContaining({
        json: expect.objectContaining({
          sentence: `${question.sentence} Use the saved reason.`,
        }),
      }),
    );
  });
  it("three accumulated sentences keep the pending text and one Apply renders all three changes", async () => {
    let at = 0;
    base(voice.program, {
      [`POST /api/programs/${voice.program.id}/shape`]: () =>
        voice.shapes[at++],
      [`POST /api/programs/${voice.program.id}/text`]: voice.applied,
    });
    render(<Form initial={voice.program} />);
    await preview(voice.shapes[0].sentence);
    for (const shape of voice.shapes.slice(1)) {
      tab("Add a sentence");
      type("Next program change", shape.sentence);
      press("Add sentence");
      await screen.findByRole("grid", { name: "Text changes" });
    }
    const posts = mocks.apiFetch.mock.calls.filter(
      ([path, init]) => path.endsWith("/shape") && init?.method === "POST",
    );
    expect(posts[1][1].json.pending).toBe(voice.shapes[0].proposed_text);
    expect(posts[2][1].json.pending).toBe(voice.shapes[1].proposed_text);
    press("Apply");
    press("Apply");
    await screen.findByRole("tab", { name: "Now" });
    expect(
      mocks.apiFetch.mock.calls.filter(
        ([path, init]) => path.endsWith("/text") && init?.method === "POST",
      ),
    ).toHaveLength(1);
  });
  it("YOLO keeps its applied changes beside pending lowerings and Overturn draws the hub's result", async () => {
    base(yolo.program, {
      [`POST /api/programs/${yolo.program.id}/shape`]: yolo.shape,
      [`POST /api/programs/${yolo.program.id}/decisions/${yolo.shape.decision!.id}/overturn`]:
        yolo.overturned,
    });
    render(<Form initial={yolo.program} />);
    await preview(yolo.shape.sentence);
    tab("Applied");
    expect(
      screen.getByRole("grid", { name: "Applied changes" }).textContent,
    ).toContain(yolo.shape.applied_rows[0].say);
    press("Overturn");
    await screen.findByRole("tab", { name: "Now" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/overturn"),
      expect.objectContaining({ method: "POST" }),
    );
  });
  it("call-held rows open in review and Cancel drops the held proposal on the hub", async () => {
    const later = shapeFixture.call_later as unknown as {
      program: Program;
      dropped: Program;
    };
    base(later.program, {
      [`DELETE /api/programs/${later.program.id}/shape/held`]: later.dropped,
    });
    render(<Form initial={later.program} />);
    await screen.findByRole("grid", { name: "Text changes" });
    press("Cancel");
    await screen.findByRole("tab", { name: "Now" });
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      expect.stringContaining("/shape/held"),
      { method: "DELETE" },
    );
  });
  it("no engine offers both repair verbs without sending a shape", async () => {
    base(normal.program, {
      [`GET /api/programs/${normal.program.id}/shape`]:
        shapeFixture.no_engine.engine,
    });
    const openText = vi.fn();
    render(
      <ProgramForm
        kind="amend"
        program={normal.program}
        onCancel={() => {}}
        onApplied={() => {}}
        onOpenText={openText}
      />,
    );
    type("Program change", "Keep it.");
    press("Preview");
    await screen.findByRole("button", { name: "Open Engines" });
    press("Open Engines");
    expect(mocks.openSurfaceOr).toHaveBeenCalledWith(
      "configure-runs-on",
      "/settings",
      "models",
    );
    press("Open text");
    expect(openText).toHaveBeenCalledOnce();
    expect(
      mocks.apiFetch.mock.calls.some(([, init]) => init?.method === "POST"),
    ).toBe(false);
  });
  it("a large step splits through the draft operation and renders the split rows", async () => {
    base(big.program, {
      [`POST /api/programs/${big.program.id}/plan/draft`]: (init?: {
        json?: { split?: number };
      }) => (init?.json?.split ? big.split : big.draft),
    });
    render(<Form initial={big.program} />);
    type("Change method", "plan");
    type("Program change", big.program.goal);
    press("Preview");
    await screen.findByRole("grid", { name: "Text changes" });
    const row = big.draft.changes.find(
      (row) => row.size?.code === "step_too_big",
    )!;
    selectChange(row.id);
    press("Split large step");
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith(
        expect.stringContaining("/plan/draft"),
        expect.objectContaining({
          json: { text: big.draft.proposed_text, split: row.size!.place },
        }),
      ),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("grid", { name: "Text changes" }).textContent,
      ).toContain(big.split.changes.at(-1)!.say),
    );
  });
  it("a goal with several programs has selection, Apply all, made programs and their Open verb", async () => {
    base(split.program, {
      [`POST /api/programs/${split.program.id}/plan/draft`]: split.draft,
      [`POST /api/programs/${split.program.id}/plan/programs`]: split.applied,
    });
    render(<Form initial={split.program} />);
    type("Change method", "plan");
    type("Program change", split.program.goal);
    press("Preview");
    const grid = await screen.findByRole("grid", { name: "Planned programs" });
    fireEvent.click(within(grid).getByText(split.draft.programs![0].title));
    if (split.draft.programs![0].hands)
      expect(screen.getByText(split.draft.programs![0].hands)).toBeTruthy();
    press("Apply all");
    await screen.findAllByText("Created");
    const made = split.applied.made[0];
    fireEvent.click(
      grid.querySelector(`[data-object-id="program:${made.id}"]`)!,
    );
    press("Open program");
    expect(mocks.openPullout).toHaveBeenCalledWith(`program:${made.id}`);
  });
});

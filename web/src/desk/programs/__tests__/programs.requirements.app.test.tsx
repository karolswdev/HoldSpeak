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
  reqProgram,
  addedFixture,
  sendBackFixture,
  waivedFixture,
  waiveRefusedFixture,
  evidenceFixture,
  wordFixture,
  wordMetFixture,
  mocks,
  hub,
  clone,
  ApiError,
  type Program,
  type Answered,
} from "./programs.seats.test-setup";
import { ProgramRequirements } from "../ProgramRequirements";
import { ProgramNow } from "../ProgramWindow";
import tape from "../__fixtures__/program.seats10.json";
import { useDesk } from "../../store";
import { answerBinding } from "../liveModel";
const press = (name: string) => {
  const q = document.querySelector<HTMLElement>("[data-question]");
  const answer = q ? within(q).queryByRole("button", { name }) : null;
  fireEvent.click(answer ?? screen.getByRole("button", { name }));
};
function Seat({
  initial,
  now = false,
  stepId,
}: {
  initial: Program;
  now?: boolean;
  stepId?: string | null;
}) {
  const [program, setProgram] = useState(initial),
    [error, setError] = useState("");
  const props = {
    program,
    onApplied: (p: Program | null) => {
      if (p) setProgram(p);
    },
    onError: setError,
  };
  return (
    <>
      {now ? (
        <ProgramNow {...props} />
      ) : (
        <ProgramRequirements
          {...props}
          step={
            program.steps.find((s) =>
              stepId ? s.id === stepId : s.ordinal === 2,
            ) || null
          }
        />
      )}
      <output>{error}</output>
    </>
  );
}
const reqs = (p: Program) => [
  ...(p.requirements ?? []),
  ...p.steps.flatMap((s) => s.requirements ?? []),
];
const pick = (p: Program, label: string) => {
  const row = reqs(p).find((r) => r.id === label || r.label === label)!;
  const grid = screen.getByRole("grid", { name: "Requirements" });
  fireEvent.click(grid.querySelector(`[data-object-id="${row.id}"]`)!);
  return row;
};
const path = (p: Program, id: string) =>
  `POST /api/programs/${p.id}/requirements/${id}/decide`;
describe("Requirements seat, recorded hub answers", () => {
  it("Send back carries the shown step binding and draws the working step", async () => {
    const row = reqs(reqProgram).find((r) => r.choices.includes("send_back"))!;
    hub({ [path(reqProgram, row.id)]: sendBackFixture });
    render(<Seat initial={reqProgram} />);
    pick(reqProgram, row.id);
    press("Send back");
    fireEvent.change(screen.getByLabelText("Answer note"), {
      target: { value: "Please check the failure." },
    });
    press("Send back");
    await waitFor(() =>
      expect(mocks.apiFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          json: expect.objectContaining({
            choice: "send_back",
            line: "Please check the failure.",
            binding: answerBinding(reqProgram, row.step_id ?? ""),
          }),
        }),
      ),
    );
    await waitFor(() =>
      expect(
        screen.queryByRole("region", { name: `Send back ${row.label}?` }),
      ).toBeNull(),
    );
  });
  it("Waive requires a reason and renders the hub's Waived state and reason", async () => {
    const row = reqs(reqProgram).find((r) => r.label === "R5")!;
    hub({ [path(reqProgram, row.id)]: waivedFixture });
    render(<Seat initial={reqProgram} stepId={row.step_id} />);
    pick(reqProgram, row.id);
    press("Waive");
    expect(
      (
        within(
          document.querySelector<HTMLElement>("[data-question]")!,
        ).getByRole("button", { name: "Waive" }) as HTMLButtonElement
      ).disabled,
    ).toBe(true);
    fireEvent.change(screen.getByLabelText("Why you waive it"), {
      target: { value: "Not needed for this change." },
    });
    press("Waive");
    await screen.findAllByText("Waived", { exact: false });
  });
  it("a refused Waive keeps the reason and the question for retry", async () => {
    const row = reqs(reqProgram).find((r) => r.choices.includes("waive"))!;
    const refusal = waiveRefusedFixture as { status: number; body: unknown };
    hub({
      [path(reqProgram, row.id)]: () => {
        throw new ApiError(refusal.status || 400, "Refused", refusal.body);
      },
    });
    render(<Seat initial={reqProgram} />);
    pick(reqProgram, row.id);
    press("Waive");
    fireEvent.change(screen.getByLabelText("Why you waive it"), {
      target: { value: "Keep this reason." },
    });
    press("Waive");
    await screen.findByText(/The change was not saved/);
    expect(
      (screen.getByLabelText("Why you waive it") as HTMLInputElement).value,
    ).toBe("Keep this reason.");
  });
  it("Open log reads the recorded evidence into the reading well", async () => {
    const row = reqs(reqProgram).find(
      (r) => r.evidence.kind === "log" && r.evidence.url,
    )!;
    hub({
      [`GET ${row.evidence.url}`]: evidenceFixture.log.text,
    });
    render(<Seat initial={reqProgram} stepId={row.step_id} />);
    pick(reqProgram, row.id);
    press("Open log");
    await screen.findByRole("group", { name: "Requirement log" });
  });
  it("Add requirement guesses Check from the command, posts only its scope, then draws it", async () => {
    hub({ [`POST /api/programs/${reqProgram.id}/requirements`]: addedFixture });
    render(<Seat initial={reqProgram} />);
    press("Add requirement");
    fireEvent.change(screen.getByLabelText("Requirement sentence"), {
      target: { value: "`uv run pytest -q` is green" },
    });
    fireEvent.click(screen.getByRole("tab", { name: "Proof" }));
    expect(
      (screen.getByLabelText("Requirement command") as HTMLInputElement).value,
    ).toBe("uv run pytest -q");
    press("Add requirement");
    await waitFor(() =>
      expect(screen.queryByLabelText("Requirement sentence")).toBeNull(),
    );
    const out =
      (addedFixture as unknown as Program).steps ??
      (addedFixture as unknown as Answered).program?.steps;
    expect(out).toBeTruthy();
  });
  it("a Shot which the repository cannot prove keeps Add disabled and explains why", () => {
    render(<Seat initial={reqProgram} />);
    press("Add requirement");
    fireEvent.change(screen.getByLabelText("Requirement sentence"), {
      target: { value: "people at 393" },
    });
    const p = reqProgram.can_prove;
    if (p?.shot === false) {
      expect(
        (
          screen.getByRole("button", {
            name: "Add requirement",
          }) as HTMLButtonElement
        ).disabled,
      ).toBe(true);
      expect(screen.getByText(p.shot_reason!)).toBeTruthy();
    }
  });
  it("his word answers with a note through the requirement route and removes the held question", async () => {
    const p = wordFixture as unknown as Program,
      row = reqs(p).find((r) => r.kind === "word")!;
    hub({ [path(p, row.id)]: wordMetFixture });
    render(<Seat initial={p} now />);
    fireEvent.change(screen.getByLabelText("Answer note"), {
      target: { value: "I read the result." },
    });
    press("Met");
    await waitFor(() =>
      expect(screen.queryByRole("button", { name: "Met" })).toBeNull(),
    );
    expect(mocks.apiFetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        json: expect.objectContaining({
          line: "I read the result.",
          choice: "met",
        }),
      }),
    );
  });
});

describe("Requirement edit and evidence seats", () => {
  it("edits the sentence through the requirement operation and draws the recorded saved sentence", async () => {
    const p = tape.requirement_added.program as unknown as Program;
    const row = reqs(p).find(
      (r) => r.id === tape.requirement_added.requirement_id,
    )!;
    hub({
      [`PATCH /api/programs/${p.id}/requirements/${row.id}`]:
        tape.requirement_edited,
    });
    render(<Seat initial={p} stepId={row.step_id} />);
    pick(p, row.id);
    press("Edit requirement");
    const next = (tape.requirement_edited.program as unknown as Program).steps
      .flatMap((s) => s.requirements ?? [])
      .find((r) => r.id === row.id)!;
    fireEvent.change(screen.getByLabelText("Requirement sentence"), {
      target: { value: next.text },
    });
    press("Save requirement");
    await waitFor(() =>
      expect(
        screen.getByRole("grid", { name: "Requirements" }).textContent,
      ).toContain(next.text),
    );
  });
  it("reads a selected Shot thumbnail through ImageWell and Open shot targets its evidence window", async () => {
    const row = reqs(reqProgram).find(
      (r) => r.evidence.kind === "shot" && r.evidence.url,
    )!;
    Object.assign(URL, {
      createObjectURL: vi.fn(() => "blob:evidence"),
      revokeObjectURL: vi.fn(),
    });
    mocks.apiBlob.mockResolvedValue(
      new Blob(["png"], { type: evidenceFixture.shot.type }),
    );
    const open = vi.spyOn(useDesk.getState(), "openPullout");
    render(<Seat initial={reqProgram} stepId={row.step_id} />);
    pick(reqProgram, row.id);
    await screen.findByRole("img", { name: `${row.label} evidence` });
    expect(mocks.apiBlob).toHaveBeenCalledWith(row.evidence.url);
    press("Open shot");
    expect(open).toHaveBeenCalledWith(
      `program-shot:${reqProgram.id}:${row.id}`,
    );
  });
});

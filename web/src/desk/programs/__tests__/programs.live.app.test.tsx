import {
  act,
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { deskQueryClient } from "../../../lib/queryClient";
import tape from "../__fixtures__/program.live10.json";
import listWire from "../__fixtures__/programs.list.json";
import runningWire from "../__fixtures__/program.running.json";
import askedWire from "../__fixtures__/program.your_turn.json";
import parkedWire from "../__fixtures__/program.parked.json";
import doneWire from "../__fixtures__/program.done.json";
import textWire from "../__fixtures__/program.text.json";
import textApplyWire from "../__fixtures__/program.text_apply.json";
import movedWire from "../__fixtures__/program.adjust.moved.json";
import adjustWire from "../__fixtures__/program.adjust.json";
import projectWire from "../__fixtures__/program.create_projects.json";
import createWire from "../__fixtures__/program.create_project.json";
import type { Program, TextApplyAnswer } from "../types";
const mock = vi.hoisted(() => ({
  apiFetch: vi.fn(),
  listeners: new Map<string, Set<(frame: unknown) => void>>(),
}));
vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: mock.apiFetch,
}));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useOptionalRuntimeBus: () => ({
    subscribe: (type: string, fn: (frame: unknown) => void) => {
      const set = mock.listeners.get(type) ?? new Set();
      set.add(fn);
      mock.listeners.set(type, set);
      return () => set.delete(fn);
    },
  }),
}));
import { ApiError } from "../../../lib/api";
import { ProgramsCore } from "../ProgramsWindow";
import { ProgramNow } from "../ProgramWindow";
import { ProgramSteps } from "../ProgramSteps";
import { ProgramForm } from "../ProgramForm";
import { ProgramText, TextChanges } from "../ProgramText";
import { ProgramLedger } from "../Ledger";
import { answerBinding, bindingId, currentStep } from "../liveModel";
import { useDesk } from "../../store";
const clone = <T,>(x: T): T => structuredClone(x);
const running = tape.running as unknown as Program,
  asked = tape.waiting as unknown as Program,
  parked = tape.parked as unknown as Program;
const error = vi.fn(),
  applied = vi.fn();
function hub(table: Record<string, unknown>) {
  mock.apiFetch.mockImplementation(
    async (path: string, init?: { method?: string; json?: unknown }) => {
      const key = `${init?.method || "GET"} ${path}`;
      if (!(key in table)) throw new ApiError(404, "Missing", { detail: key });
      const answer = table[key];
      return typeof answer === "function"
        ? (answer as Function)(init)
        : clone(answer);
    },
  );
}
beforeEach(() => {
  mock.apiFetch.mockReset();
  mock.apiFetch.mockRejectedValue(new ApiError(404, "Missing", {}));
  mock.listeners.clear();
  deskQueryClient.clear();
  applied.mockReset();
  error.mockReset();
  useDesk.setState({ places: {} });
});
afterEach(cleanup);
const props = { onApplied: applied, onError: error };

describe("Programs master", () => {
  it("groups the recorded programs and selects without answering", async () => {
    hub({
      "GET /api/programs": tape.running_list,
      [`GET /api/programs/${running.id}`]: running,
    });
    render(<ProgramsCore />);
    const grid = await screen.findByRole("grid", { name: "Programs" });
    fireEvent.click(within(grid).getByText(running.title));
    await screen.findByRole("tab", { name: "Now" });
    expect(
      within(grid).getByRole("rowgroup", { name: "Running" }),
    ).toBeTruthy();
    expect(
      grid
        .querySelector(`[data-object-id="${running.id}"]`)
        ?.getAttribute("aria-selected"),
    ).toBe("true");
    expect(
      mock.apiFetch.mock.calls.filter(
        ([, init]) => init?.method && init.method !== "GET",
      ),
    ).toEqual([]);
  });
  it("parks the selected program with its revision and shows the acknowledged result", async () => {
    const source = clone(tape.running_list);
    hub({
      "GET /api/programs": source,
      [`GET /api/programs/${running.id}`]: running,
      [`POST /api/programs/${running.id}/park`]: parked,
    });
    render(<ProgramsCore />);
    await screen.findByRole("tab", { name: "Now" });
    fireEvent.click(screen.getByRole("button", { name: "Park" }));
    await waitFor(() =>
      expect(
        screen.getAllByRole("button", { name: "Resume" }).length,
      ).toBeGreaterThan(0),
    );
    expect(mock.apiFetch).toHaveBeenCalledWith(
      `/api/programs/${running.id}/park`,
      expect.objectContaining({
        json: { binding: answerBinding(running, currentStep(running)?.id) },
      }),
    );
  });
});
describe("Programs Now", () => {
  it("renders step-owned events in the well and recap figures at Done", () => {
    const { rerender } = render(<ProgramNow program={running} {...props} />);
    const well = screen.getByRole("log");
    expect(well.textContent).toContain(
      running.checkpoints
        .filter((row) => row.step_id === currentStep(running)?.id)
        .at(-1)?.line,
    );
    rerender(
      <ProgramNow program={tape.done as unknown as Program} {...props} />,
    );
    expect(screen.getByText("steps done")).toBeTruthy();
    expect(screen.queryByRole("log")).toBeNull();
  });
  it("binds Go on to the shown question and disarms when its revision changes", async () => {
    const core = clone(asked);
    core.your_turn_items = core.your_turn_items.filter(
      (row) => row.kind === "core",
    );
    hub({
      [`POST /api/programs/${core.id}/steps/${core.your_turn_items[0].step_id}/decide`]:
        { program: running },
    });
    const { rerender } = render(<ProgramNow program={core} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Go on" }));
    await waitFor(() => expect(applied).toHaveBeenCalledWith(running));
    expect(mock.apiFetch.mock.calls[0][1].json.binding).toEqual(
      answerBinding(core, core.your_turn_items[0].step_id),
    );
    const next = clone(core);
    next.revision++;
    rerender(<ProgramNow program={next} {...props} />);
    expect(screen.queryByRole("button", { name: "Go on" })).toBeNull();
    expect(
      screen.getByRole("button", { name: "Read the new question" }),
    ).toBeTruthy();
    expect(mock.apiFetch.mock.calls.length).toBe(1);
  });
  it("parks the whole program from the shown question and sends that question binding", async () => {
    hub({ [`POST /api/programs/${asked.id}/park`]: parked });
    render(<ProgramNow program={asked} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Park" }));
    await waitFor(() => expect(applied).toHaveBeenCalledWith(parked));
    expect(mock.apiFetch).toHaveBeenCalledWith(
      `/api/programs/${asked.id}/park`,
      expect.objectContaining({
        json: {
          binding: answerBinding(asked, asked.your_turn_items[0].step_id || ""),
        },
      }),
    );
  });
  it("names the queued night window without calling it active work", () => {
    render(
      <ProgramNow program={tape.tonight as unknown as Program} {...props} />,
    );
    expect(
      screen.getByRole("region", {
        name: `Starts tonight at ${tape.tonight.night.start}`,
      }),
    ).toBeTruthy();
    expect(screen.getByText(tape.tonight.night.line)).toBeTruthy();
    expect(screen.queryByRole("log")).toBeNull();
  });
  it("keeps a refused answer visible for retry", async () => {
    const core = clone(asked);
    core.your_turn_items = core.your_turn_items.filter(
      (row) => row.kind === "core",
    );
    mock.apiFetch.mockRejectedValue(
      new ApiError(409, "Changed", {
        detail: "This program changed. Read it again before you answer.",
      }),
    );
    render(<ProgramNow program={core} {...props} />);
    fireEvent.click(screen.getByRole("button", { name: "Go on" }));
    await waitFor(() => expect(error).toHaveBeenCalled());
    expect(screen.getByRole("button", { name: "Go on" })).toBeTruthy();
  });
});
describe("Programs Steps, Text, Ledger and forms", () => {
  it("moves a selected planned step and reads the acknowledged order", async () => {
    const program = adjustWire as unknown as Program;
    const step = program.steps.find(
      (row) => row.editable?.includes("position") && row.ordinal === 3,
    )!;
    hub({
      [`PATCH /api/programs/${program.id}/steps/${step.id}`]: {
        program: movedWire,
      },
    });
    render(
      <ProgramSteps
        program={program}
        selected={step.id}
        onSelect={() => {}}
        {...props}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Move up" }));
    await waitFor(() => expect(applied).toHaveBeenCalledWith(movedWire));
  });
  it("reads program text in the filling editor", async () => {
    hub({ [`GET /api/programs/${running.id}/text`]: tape.running_text });
    render(<ProgramText program={running} {...props} />);
    await screen.findByTestId("programs-text");
    expect(screen.getAllByRole("textbox").length).toBeGreaterThan(1);
  });
  it("asks before a text apply, sends the frozen binding, and renders its result", async () => {
    const answer = tape.text_preview as unknown as TextApplyAnswer;
    const program = tape.drafting as unknown as Program;
    const binding = answerBinding(program);
    hub({ [`POST /api/programs/${program.id}/text`]: tape.text_applied });
    render(
      <TextChanges
        program={program}
        proposal={{
          answer,
          text: answer.allowed_text,
          base: tape.drafting_text.text,
          binding,
          target: bindingId(program, binding.step_id),
        }}
        onCancel={() => {}}
        {...props}
      />,
    );
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    fireEvent.click(
      within(
        screen.getByRole("region", { name: "Apply these changes?" }),
      ).getByRole("button", { name: "Apply" }),
    );
    await waitFor(() =>
      expect(applied).toHaveBeenCalledWith(tape.text_applied.program),
    );
    expect(mock.apiFetch.mock.calls[0][1].json.binding).toEqual(binding);
  });
  it("reads an entry selected from the ledger", () => {
    render(<ProgramLedger program={running} {...props} />);
    fireEvent.click(screen.getByText(running.checkpoints[0].line));
    expect(screen.getByRole("region", { name: "Entry" })).toBeTruthy();
  });
  it("creates in the inspector and shows the hub result", async () => {
    hub({
      "GET /api/projects": projectWire.response.body,
      "POST /api/programs": createWire.response.body,
    });
    render(
      <ProgramForm
        kind="new"
        program={null}
        onCancel={() => {}}
        onApplied={applied}
      />,
    );
    fireEvent.change(screen.getByRole("textbox", { name: "Program name" }), {
      target: { value: "New program" },
    });
    await waitFor(() =>
      expect(
        screen
          .getByRole("combobox", { name: "Project" })
          .getAttribute("value") !== "",
      ),
    );
    fireEvent.change(screen.getByRole("combobox", { name: "Project" }), {
      target: { value: "proj-holdspeak" },
    });
    fireEvent.click(screen.getByRole("tab", { name: "Work" }));
    expect(screen.getByRole("combobox", { name: "Control" })).toBeTruthy();
    fireEvent.click(screen.getByRole("tab", { name: "Program" }));
    expect(screen.getByRole("textbox", { name: "Program name" })).toHaveValue(
      "New program",
    );
    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    await waitFor(() =>
      expect(applied).toHaveBeenCalledWith(createWire.response.body),
    );
  });
});

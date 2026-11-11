/* HS-S14: the Program detail readers share one keyed read (the desk's
 * query cache, `deskResourceKey("program", id)`).
 *
 * The identity transitions, on RECORDED hub answers (programs.test-setup.tsx):
 * two windows on one Program (the Program window and a Shot window of its
 * requirement), a press in one, a change frame, a frame for another Program,
 * an old read that lands after a press, two Programs side by side, and the
 * list beside the window. Each case counts the GETs of the Program and reads
 * what each window draws. */
import { act, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  wordFixture, wordMetFixture, mocks, ApiError, ProgramBody, ProgramsCore, clone, calls, emit, hub,
  done, list, yourTurn, createProjectFixture, deliveryMergeFixture, deliveryMergedFixture, type Program, board,
} from "./programs.test-setup";
import { createProgram } from "../api";
import { ProgramShotBody } from "../ProgramShot";

const word = wordFixture as unknown as Program;
const met = (wordMetFixture as unknown as { program: Program }).program;
const item = word.your_turn_items[0];
const r1 = item.requirement_id!;
const detailGets = (id: string) => calls.filter((call) => call === `GET /api/programs/${id}`).length;
const shotWord = () => screen.getByTestId("program-shot-status").textContent ?? "";
const decide = `POST /api/programs/${word.id}/requirements/${r1}/decide`;

async function openBoth() {
  mocks.apiBlob.mockResolvedValue(new Blob(["png"], { type: "image/png" }));
  Object.assign(URL, { createObjectURL: vi.fn(() => "blob:shot"), revokeObjectURL: vi.fn() });
  render(<><ProgramBody programId={word.id} /><ProgramShotBody id={`${word.id}:${r1}`} /></>);
  await screen.findByTestId("programs-your-turn");
  await screen.findByTestId("program-shot-status");
}

describe("HS-S14: one Program, one keyed read", () => {
  it("two windows on one Program read it once at open and draw the same state", async () => {
    hub({ [`GET /api/programs/${word.id}`]: word });
    await openBoth();
    expect(detailGets(word.id)).toBe(1);
    expect(shotWord()).toContain("Waits for you");
  });

  it("a press in the Program window is drawn at once in the Shot window, with no read", async () => {
    hub({ [`GET /api/programs/${word.id}`]: word, [decide]: wordMetFixture });
    await openBoth();
    fireEvent.click(within(screen.getByTestId("programs-turn-item")).getByTestId("programs-turn-met"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(shotWord()).toContain("Met");
    expect(shotWord()).not.toContain("Waits for you");
    expect(detailGets(word.id)).toBe(1);
  });

  it("a change frame for the Program: one read, and both windows draw the change", async () => {
    let answer: Program = word;
    hub({ [`GET /api/programs/${word.id}`]: () => answer });
    await openBoth();
    answer = met;
    emit("program_changed", { program_id: word.id });
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    await waitFor(() => expect(shotWord()).toContain("Met"));
    expect(detailGets(word.id)).toBe(2);
  });

  it("a frame for another Program reads nothing; a frame that names no Program reads each open one once", async () => {
    hub({ [`GET /api/programs/${word.id}`]: word });
    await openBoth();
    emit("program_changed", { program_id: "program-other" });
    emit("desk_changed", { changes: [{ kind: "note", id: "n1" }] });
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(detailGets(word.id)).toBe(1);
    emit("program_changed", {});
    await waitFor(() => expect(detailGets(word.id)).toBe(2));
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(detailGets(word.id)).toBe(2);
  });

  it("an old read that lands after a press never draws the old state again", async () => {
    const held: Array<(value: Program) => void> = [];
    let hold = false;
    mocks.apiFetch.mockImplementation(async (path: string, init?: { method?: string; json?: unknown }) => {
      const key = `${(init?.method ?? "GET").toUpperCase()} ${path}`;
      calls.push(key);
      if (key === `GET /api/programs/${word.id}`) {
        // The reads at open answer; a read after open waits for the test.
        if (!hold) return clone(word);
        return new Promise<Program>((resolve) => { held.push(resolve); });
      }
      if (key === decide) return clone(wordMetFixture);
      throw new ApiError(404, "Not Found", { detail: "Not Found" });
    });
    await openBoth();
    hold = true;
    emit("program_changed", { program_id: word.id });
    await waitFor(() => expect(held.length).toBeGreaterThan(0));
    fireEvent.click(within(screen.getByTestId("programs-turn-item")).getByTestId("programs-turn-met"));
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    // The reads that started before the press answer with the state before it.
    await act(async () => { for (const resolve of held) resolve(clone(word)); await new Promise((resolve) => setTimeout(resolve, 20)); });
    expect(screen.queryByTestId("programs-your-turn")).toBeNull();
    expect(shotWord()).toContain("Met");
  });

  it("two Programs side by side never share a read", async () => {
    hub({ [`GET /api/programs/${word.id}`]: word, [`GET /api/programs/${done.id}`]: done });
    render(<><ProgramBody programId={word.id} /><ProgramBody programId={done.id} /></>);
    await waitFor(() => expect(screen.getAllByTestId("programs-mast")).toHaveLength(2));
    expect(detailGets(word.id)).toBe(1);
    expect(detailGets(done.id)).toBe(1);
    expect(screen.getAllByTestId("programs-your-turn")).toHaveLength(1);
  });

  it("the list and the window are two reads; a frame for the Program reads each once", async () => {
    hub({ "GET /api/programs": list, [`GET /api/programs/${yourTurn.id}`]: yourTurn });
    render(<><ProgramsCore /><ProgramBody programId={yourTurn.id} /></>);
    await screen.findAllByTestId("programs-mast");
    await waitFor(() => expect(screen.getAllByTestId("programs-rail-tile").length).toBeGreaterThan(0));
    expect(calls.filter((call) => call === "GET /api/programs")).toHaveLength(1);
    expect(detailGets(yourTurn.id)).toBe(1);
    emit("program_changed", { program_id: yourTurn.id });
    await waitFor(() => expect(detailGets(yourTurn.id)).toBe(2));
    await waitFor(() => expect(calls.filter((call) => call === "GET /api/programs")).toHaveLength(2));
  });

  it("a window opened again reads the Program again", async () => {
    hub({ [`GET /api/programs/${word.id}`]: word });
    const first = render(<ProgramBody programId={word.id} />);
    await board();
    first.unmount();
    render(<ProgramBody programId={word.id} />);
    await board();
    await waitFor(() => expect(detailGets(word.id)).toBe(2));
  });

  it("a Program made in the wizard opens drawn from the hub's answer, then reads once", async () => {
    const recorded = createProjectFixture as unknown as { request: { json: unknown }; response: { body: Program } };
    const made = recorded.response.body;
    hub({ "POST /api/programs": made, [`GET /api/programs/${made.id}`]: made });
    await act(async () => { await createProgram(recorded.request.json as Parameters<typeof createProgram>[0]); });
    render(<ProgramBody programId={made.id} />);
    // No loading frame: the board is there on the first draw.
    expect(screen.getByTestId("programs-board")).toBeTruthy();
    await waitFor(() => expect(detailGets(made.id)).toBe(1));
  });

  it("its step merges: the frame's one read takes the merge row off the window", async () => {
    const merge = deliveryMergeFixture as unknown as Program;
    const merged = (deliveryMergedFixture as unknown as { program: Program }).program;
    let answer = merge;
    hub({ [`GET /api/programs/${merge.id}`]: () => answer });
    render(<ProgramBody programId={merge.id} />);
    await screen.findByTestId("programs-your-turn");
    answer = merged;
    emit("program_changed", { program_id: merge.id });
    await waitFor(() => expect(screen.queryByTestId("programs-your-turn")).toBeNull());
    expect(screen.getByTestId("program-status").textContent).toContain("Done");
    expect(detailGets(merge.id)).toBe(2);
  });
});

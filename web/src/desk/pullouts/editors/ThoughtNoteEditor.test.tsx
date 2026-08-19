import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../../lib/api";
import { useDesk } from "../../store";
import { ThoughtNoteEditor } from "./ThoughtNoteEditor";
import { saveThoughtWorking } from "../../thoughts";

vi.mock("../../components/DeskEditor", () => ({
  DeskEditor: ({ value, onChange }: { value: string; onChange: (value: string) => void }) =>
    <textarea aria-label="Body" value={value} onChange={(event) => onChange(event.target.value)} />,
}));
vi.mock("../../surface/gadgets", () => ({
  StringGadget: ({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) =>
    <label>{label}<input value={value} onChange={(event) => onChange(event.target.value)} /></label>,
}));
vi.mock("../../thoughts", () => ({ saveThoughtWorking: vi.fn() }));

const base = {
  id: "thought-1", source: { kind: "typed" as const }, raw_captured_at: "2026-01-01T00:00:00Z",
  state: "working" as const, aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1,
  attachment_revision: 1, filing_status: "missing" as const,
  working_note: { id: "note-1", title: "Before", body_markdown: "Before body", tags: ["before"] },
};

afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); });

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((ok, no) => { resolve = ok; reject = no; });
  return { promise, resolve, reject };
}

describe("ThoughtNoteEditor", () => {
  it("serializes B behind successful A and sends B with A's advanced cursors", async () => {
    vi.useFakeTimers();
    useDesk.setState({ refresh: vi.fn() });
    const first = deferred<typeof base>();
    const afterA = { ...base, aggregate_revision: 2, working_revision: 2,
      working_note: { ...base.working_note, title: "A", body_markdown: "Before body", tags: ["before"] } };
    const afterB = { ...afterA, aggregate_revision: 3, working_revision: 3,
      working_note: { ...afterA.working_note, title: "B" } };
    vi.mocked(saveThoughtWorking).mockReturnValueOnce(first.promise).mockResolvedValueOnce(afterB);
    const onThought = vi.fn();
    render(<ThoughtNoteEditor thought={base} onThought={onThought} />);

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });
    expect(saveThoughtWorking).toHaveBeenCalledTimes(1);
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "B" } });
    await act(async () => { first.resolve(afterA); await Promise.resolve(); await vi.advanceTimersByTimeAsync(1); });

    expect(saveThoughtWorking).toHaveBeenCalledTimes(2);
    expect(saveThoughtWorking.mock.calls[1][0]).toMatchObject({ aggregate_revision: 2, working_revision: 2 });
    expect(saveThoughtWorking.mock.calls[1][1]).toMatchObject({ title: "B" });
    expect(screen.getByLabelText("Title")).toHaveValue("B");
    expect(onThought).toHaveBeenLastCalledWith(afterB);
  });

  it("installs conflict current and never replays B queued behind A", async () => {
    vi.useFakeTimers();
    useDesk.setState({ refresh: vi.fn() });
    const first = deferred<typeof base>();
    const current = { ...base, aggregate_revision: 2, working_revision: 2,
      working_note: { ...base.working_note, title: "Current", body_markdown: "Current body", tags: ["current"] } };
    vi.mocked(saveThoughtWorking).mockReturnValueOnce(first.promise);
    const onThought = vi.fn();
    render(<ThoughtNoteEditor thought={base} onThought={onThought} />);

    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "B" } });
    await act(async () => { first.reject(new ApiError(409, "conflict", { context: { current } })); await Promise.resolve(); await vi.runAllTimersAsync(); });

    expect(screen.getByLabelText("Title")).toHaveValue("Current");
    expect(screen.getByLabelText("Body")).toHaveValue("Current body");
    expect(screen.getByLabelText("Tags")).toHaveValue("current");
    expect(screen.getByRole("status")).toHaveTextContent("latest version is shown");
    expect(onThought).toHaveBeenCalledWith(current);
    expect(saveThoughtWorking).toHaveBeenCalledTimes(1);
  });

  it("discards a delayed A response after a newer parent authority epoch", async () => {
    vi.useFakeTimers();
    useDesk.setState({ refresh: vi.fn() });
    const first = deferred<typeof base>();
    const staleA = { ...base, aggregate_revision: 2, working_revision: 2,
      working_note: { ...base.working_note, title: "A" } };
    const parentCurrent = { ...base, aggregate_revision: 3, working_revision: 3,
      working_note: { ...base.working_note, title: "Parent", body_markdown: "Parent body", tags: ["parent"] } };
    vi.mocked(saveThoughtWorking).mockReturnValueOnce(first.promise);
    const onThought = vi.fn();
    const view = render(<ThoughtNoteEditor thought={base} onThought={onThought} />);
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });

    await act(async () => { view.rerender(<ThoughtNoteEditor thought={parentCurrent} onThought={onThought} />); });
    await act(async () => { first.resolve(staleA); await Promise.resolve(); await vi.runAllTimersAsync(); });

    expect(screen.getByLabelText("Title")).toHaveValue("Parent");
    expect(screen.getByLabelText("Body")).toHaveValue("Parent body");
    expect(screen.getByLabelText("Tags")).toHaveValue("parent");
    expect(onThought).not.toHaveBeenCalled();
    expect(saveThoughtWorking).toHaveBeenCalledTimes(1);
  });

  it("discards an older conflict current after a newer parent authority epoch", async () => {
    vi.useFakeTimers();
    useDesk.setState({ refresh: vi.fn() });
    const first = deferred<typeof base>();
    const olderConflict = { ...base, aggregate_revision: 2, working_revision: 2,
      working_note: { ...base.working_note, title: "Older conflict" } };
    const parentCurrent = { ...base, aggregate_revision: 3, working_revision: 3,
      working_note: { ...base.working_note, title: "Parent", body_markdown: "Parent body", tags: ["parent"] } };
    vi.mocked(saveThoughtWorking).mockReturnValueOnce(first.promise);
    const onThought = vi.fn();
    const view = render(<ThoughtNoteEditor thought={base} onThought={onThought} />);
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "A" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(500); });

    await act(async () => { view.rerender(<ThoughtNoteEditor thought={parentCurrent} onThought={onThought} />); });
    await act(async () => { first.reject(new ApiError(409, "conflict", { current: olderConflict })); await Promise.resolve(); await vi.runAllTimersAsync(); });

    expect(screen.getByLabelText("Title")).toHaveValue("Parent");
    expect(screen.getByLabelText("Body")).toHaveValue("Parent body");
    expect(screen.getByLabelText("Tags")).toHaveValue("parent");
    expect(screen.queryByRole("status")).not.toBeInTheDocument();
    expect(onThought).not.toHaveBeenCalled();
    expect(saveThoughtWorking).toHaveBeenCalledTimes(1);
  });
});

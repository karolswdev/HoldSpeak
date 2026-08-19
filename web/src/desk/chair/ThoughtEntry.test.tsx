import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThoughtEntry } from "./ThoughtEntry";
import { useDesk } from "../store";
import { createThought, unfinishedThoughts } from "../thoughts";

vi.mock("../thoughts", () => ({
  createThought: vi.fn(), unfinishedThoughts: vi.fn(), sourceLabel: (kind: string) => kind,
}));
vi.mock("../shell", () => ({ openSurfaceOr: vi.fn() }));
vi.mock("../../lib/micStreamSession", () => ({
  micStreamSupported: () => false, startStreamSession: vi.fn(),
}));

const thought = {
  id: "thought-1", source: { kind: "typed" as const }, raw_captured_at: "2026-01-01T00:00:00Z",
  state: "working" as const, aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1,
  attachment_revision: 1, filing_status: "missing" as const,
  working_note: { id: "note-1", title: "A thought", body_markdown: "A thought", tags: [] },
};

beforeEach(() => {
  sessionStorage.clear();
  vi.mocked(unfinishedThoughts).mockResolvedValue({ items: [], next_cursor: null });
  useDesk.setState({ refresh: vi.fn().mockResolvedValue(undefined), openPullout: vi.fn(), openEditor: vi.fn() });
});
afterEach(() => vi.clearAllMocks());

describe("ThoughtEntry", () => {
  it("collapses the composer before opening a newly created thought", async () => {
    vi.mocked(createThought).mockResolvedValue(thought);
    render(<ThoughtEntry />);
    fireEvent.click(screen.getByRole("button", { name: "Develop a thought" }));
    fireEvent.change(screen.getByLabelText("What are you working through?"), { target: { value: "A thought" } });
    fireEvent.click(screen.getByRole("button", { name: "Start developing" }));

    await waitFor(() => expect(screen.queryByRole("button", { name: "Start developing" })).toBeNull());
    expect(screen.queryByRole("button", { name: "Cancel" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Dictate" })).toBeNull();
    expect(screen.getByRole("button", { name: "Develop a thought" })).toBeInTheDocument();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:note-1");
    expect(useDesk.getState().openEditor).toHaveBeenCalledWith("note-1");
  });

  it("collapses Resume before opening its thought", async () => {
    vi.mocked(unfinishedThoughts).mockResolvedValue({ items: [{
      id: "thought-resume", working_note_id: "note-resume", source_kind: "typed",
      title: "Resume me", body_preview: "Draft", updated_at: "2026-01-01T00:00:00Z", filing_status: "missing",
    }], next_cursor: null });
    render(<ThoughtEntry />);
    const resume = await screen.findByRole("button", { name: "Resume unfinished thoughts" });
    fireEvent.click(resume);
    expect(screen.getByRole("list")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("listitem", { name: /Resume me/ }));

    expect(screen.queryByRole("list")).toBeNull();
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:note-resume");
  });
});

import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ThoughtEntry } from "./ThoughtEntry";
import { useDesk } from "../store";
import { createThought } from "../thoughts";

vi.mock("../thoughts", () => ({
  createThought: vi.fn(),
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
  useDesk.setState({ refresh: vi.fn().mockResolvedValue(undefined), openPullout: vi.fn(), openEditor: vi.fn() });
});
afterEach(() => vi.clearAllMocks());

describe("ThoughtEntry", () => {
  it("collapses the composer before opening a newly created thought", async () => {
    vi.mocked(createThought).mockResolvedValue({ thought, default_context_receipt: {
      id: "default-app-1", action: "apply_default_context", scope: "this_thought", thought_id: "thought-1",
      default_revision: 0, default_configuration_sha256: "empty", status: "empty",
      attachment_zero_sha256: "zero", attachment_revision: 0, attachment_sha256: "zero", attachments: [],
    } });
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
    expect(JSON.parse(sessionStorage.getItem("hs.thought.default-context-receipt.thought-1") || "null")).toMatchObject({ status: "empty" });
  });

  it("keeps advanced capture behind More", () => {
    render(<ThoughtEntry />);
    expect(screen.queryByRole("button", { name: "Open advanced capture" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More capture options" }));
    expect(screen.getByRole("button", { name: "Open advanced capture" })).toBeInTheDocument();
  });
});

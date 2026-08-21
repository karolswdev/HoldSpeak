import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { originalThought, type Thought } from "../thoughts";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";

vi.mock("../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../thoughts")>()),
  originalThought: vi.fn(),
}));

const original: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", raw_text: "SECRET ORIGINAL BYTES",
  state: "working", aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 0,
  working_note: { id: "note-1", title: "Working", body_markdown: "Changed", tags: [] }, filing_status: "filed",
};

afterEach(() => vi.clearAllMocks());

describe("ThoughtDocumentPane Original disclosure", () => {
  it("does not fetch or render raw capture until Info, then closes back to Info focus", async () => {
    vi.mocked(originalThought).mockResolvedValue(original);
    render(<ThoughtDocumentPane thoughtId="thought-1" draft={{ title: "Working", body: "Changed", tags: "" }} onEdit={vi.fn()} disabled={false} message="" onRetry={vi.fn()} />);

    const formatting = screen.getByRole("toolbar", { name: "Markdown formatting" });
    expect(formatting).toBeVisible();
    expect(formatting).toHaveTextContent("B");
    expect(screen.getByRole("button", { name: "Underline" })).toBeVisible();
    expect(screen.queryByText("SECRET ORIGINAL BYTES")).not.toBeInTheDocument();
    expect(originalThought).not.toHaveBeenCalled();
    const info = screen.getByRole("button", { name: "Info" });
    fireEvent.click(info);
    expect(await screen.findByRole("region", { name: "Original kept" })).toHaveTextContent("SECRET ORIGINAL BYTES");
    expect(originalThought).toHaveBeenCalledWith("thought-1");
    fireEvent.keyDown(window, { key: "Escape" });
    expect(screen.queryByText("SECRET ORIGINAL BYTES")).not.toBeInTheDocument();
    await waitFor(() => expect(info).toHaveFocus());
  });
});

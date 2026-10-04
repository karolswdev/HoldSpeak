// HS-111-05 — the citation token species (the ONE openable "grounded
// on" rendering, promoted out of ProjectMemoryCore): a smoke lock on
// its label grammar, its open verb, and the honest match arithmetic.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CitationChips, NO_WINDOW_REF_KINDS, groundedMatchCount, openSourceRef, refOpensWindow } from "../citations";

vi.mock("../../shell", () => ({
  openPrimitive: vi.fn(),
  openSurfaceOr: vi.fn(),
}));

describe("the citation token species", () => {
  it("renders one openable token per source ref", () => {
    const onOpen = vi.fn();
    render(
      <CitationChips refs={["meeting:m1", "decision:d1"]} onOpen={onOpen} />,
    );
    const meeting = screen.getByRole("button", { name: "Meeting · m1" });
    expect(screen.getByRole("button", { name: "Decision · d1" })).toBeTruthy();
    fireEvent.click(meeting);
    expect(onOpen).toHaveBeenCalledWith("meeting:m1");
  });

  // Astra's finding on PR #786: an Ask citation of a memory kind with no
  // window was a dead click (`openPullout: unknown id`). It is plain text.
  it.each([
    ["send:csend_1", "Send · csend_1"],
    ["project_update:u1", "Project update · u1"],
    ["prep_brief:b1", "Prep brief · b1"],
    ["calendar_event:e1", "Calendar event · e1"],
  ])("%s is plain text, never a button; the default open does nothing", async (ref, label) => {
    const shell = await import("../../shell");
    vi.mocked(shell.openPrimitive).mockClear();
    render(<CitationChips refs={[ref, "meeting:m1"]} />);
    expect(screen.getByTestId("citation-plain").textContent).toBe(label);
    expect(screen.queryByRole("button", { name: label })).toBeNull();
    expect(screen.getByRole("button", { name: "Meeting · m1" })).toBeTruthy();
    openSourceRef(ref);
    expect(shell.openPrimitive).not.toHaveBeenCalled();
    expect(refOpensWindow(ref)).toBe(false);
    expect(NO_WINDOW_REF_KINDS).toContain(ref.split(":")[0]);
  });

  it("renders nothing for an empty receipt (no zero-theater)", () => {
    const { container } = render(<CitationChips refs={[]} />);
    expect(container.innerHTML).toBe("");
  });

  it("derives the honest grounded-on count: matches minus overflow", () => {
    expect(groundedMatchCount({ matchedCount: 47, overflowCount: 35 })).toBe(
      12,
    );
    expect(groundedMatchCount(null)).toBe(0);
  });
});

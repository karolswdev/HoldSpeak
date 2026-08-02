// HS-111-05 — the citation token species (the ONE openable "grounded
// on" rendering, promoted out of ProjectMemoryCore): a smoke lock on
// its label grammar, its open verb, and the honest match arithmetic.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CitationChips, groundedMatchCount } from "../citations";

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

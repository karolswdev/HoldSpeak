// Phase 16 — the interior kit: AskWell (the voice law: a mic on every input).
// The kit's well IS the StringGadget well (sunken paper, the mic a Steel plate
// on its right edge); the AskWell question species holds the same well.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AskWell, StringGadget } from "..";

vi.mock("../../components/MicButton", () => ({
  MicButton: (props: { label?: string }) => <span data-testid="mic" data-label={props.label} />,
}));

describe("AskWell (Phase 16 kit)", () => {
  it("the input is the well; the mic is its last child (the right edge)", () => {
    const { container } = render(
      <StringGadget label="Ask this project" value="" onChange={() => undefined} placeholder="Ask this project…" />,
    );
    const well = container.querySelector(".gadget-string") as HTMLElement;
    expect(well.firstElementChild).toBe(screen.getByRole("textbox", { name: "Ask this project" }));
    expect(well.lastElementChild).toBe(screen.getByTestId("mic"));
    expect(screen.getByTestId("mic").getAttribute("data-label")).toBe("Speak Ask this project");
  });

  it("the question plate holds the same well for its answer", () => {
    const { container } = render(
      <AskWell agent="Claude Code" question="Jordan or Avery?" value="" onChange={() => undefined} onAnswer={() => undefined} />,
    );
    expect(container.querySelector(".ask-well-answer > .gadget-string")).toBeTruthy();
  });
});

describe("PHILO-17 AskWell primary={false}", () => {
  it("draws Answer as the quieter steel verb; the default stays the filled primary", () => {
    const props = { agent: "codex", question: "Ship it?", value: "", onChange: () => {}, onAnswer: () => {} };
    const { unmount } = render(<AskWell {...props} />);
    expect(screen.getByRole("button", { name: "Answer" }).className).toContain("btn--primary");
    unmount();
    render(<AskWell {...props} primary={false} />);
    const answer = screen.getByRole("button", { name: "Answer" });
    expect(answer.className).toContain("btn--secondary");
    expect(answer.className).not.toContain("btn--primary");
  });
});

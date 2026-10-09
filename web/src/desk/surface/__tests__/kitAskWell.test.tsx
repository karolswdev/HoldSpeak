// Phase 16 — the interior kit: AskWell (the voice law: a mic on every input).
// The kit's well IS the StringGadget well (sunken paper, the mic a Steel plate
// on its right edge); the AskWell question species holds the same well.
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
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

  it("the well is sunken paper; the mic plate is raised Steel on its right edge", () => {
    const css = readFileSync(resolve(__dirname, "../gadgets.css"), "utf8");
    expect(css).toMatch(/\.gadget-string \{[^}]*border: 1px solid var\(--wb-ink\);[^}]*background: var\(--wb-well\);[^}]*box-shadow: var\(--wb-sunken\);/);
    expect(css).toMatch(/\.desk-next \.gadget-string \.desk-mic \{[^}]*align-self: stretch;[^}]*background: var\(--wb-steel\);[^}]*box-shadow: inset 1px 0 0 var\(--wb-ink\)/);
  });
});

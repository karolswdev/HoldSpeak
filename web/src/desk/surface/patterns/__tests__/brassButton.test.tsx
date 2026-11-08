// The brass Button (the language, 2026-11-08): the one verb that waits on
// him. A plated variant: the plate classes, the brass marker, the species.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "../../../../components/signal/Button";
import globalCss from "../../../../styles/global.css?raw";

describe("Button variant brass", () => {
  it("wears the plate and the brass marker", () => {
    render(<Button variant="brass">Decide</Button>);
    const verb = screen.getByRole("button", { name: "Decide" });
    expect(verb.className).toMatch(/\bbtn\b/);
    expect(verb.className).toContain("btn--brass");
    expect(verb.getAttribute("type")).toBe("button");
  });

  it("draws the deep brass plate, the dark brass edge and white words", () => {
    const rule = globalCss.slice(globalCss.indexOf(":where(.btn--brass) {"));
    expect(rule).toMatch(/border-color:\s*var\(--hs-brass-ink\)/);
    expect(rule).toMatch(/background:\s*var\(--hs-brass-deep\)/);
    expect(rule).toMatch(/color:\s*var\(--white\)/);
  });
});

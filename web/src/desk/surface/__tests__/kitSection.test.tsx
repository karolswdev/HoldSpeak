// Phase 16 — the interior kit: Section (SurfaceSection `count`). The caption
// reads `Name · count`; a zero is never said (UX-CANON A.8); the verbs sit
// after the caption, the hairline after them (`::after`, surface.css).
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { SurfaceSection } from "..";
import { Button } from "../../../components/signal/Signal";

describe("Section (Phase 16 kit)", () => {
  it("says `Name · count`", () => {
    render(<SurfaceSection label="Sources" count={2}><p>x</p></SurfaceSection>);
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("Sources · 2");
  });

  it("never says a zero", () => {
    render(<SurfaceSection label="Decisions" count={0}><p>x</p></SurfaceSection>);
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("Decisions");
  });

  it("a string count is drawn as given (`5 of 6`)", () => {
    render(<SurfaceSection label="Actions" count="5 of 6"><p>x</p></SurfaceSection>);
    expect(screen.getByRole("heading", { level: 3 }).textContent).toBe("Actions · 5 of 6");
  });

  it("the verbs follow the caption; a Section may be a head alone (`1 more · Show all`)", () => {
    const { container } = render(
      <SurfaceSection label="1 more" actions={<Button dense variant="ghost">Show all</Button>} data-testid="more" />,
    );
    const head = container.querySelector(".surface-section-head") as HTMLElement;
    expect([...head.children].map((c) => c.textContent)).toEqual(["1 more", "Show all"]);
    expect(screen.getByTestId("more")).toBeTruthy();
  });

  it("the caption is mono 11 upper with the hairline to the right edge", () => {
    const css = readFileSync(resolve(__dirname, "../surface.css"), "utf8");
    expect(css).toMatch(/\.surface-section-head::after \{[^}]*flex: 1 1 12px;[^}]*height: 1px;/);
    expect(css).toMatch(/\.surface-section-head h3 \{[^}]*font-size: 11px;[^}]*font-weight: 700;[^}]*letter-spacing: 0\.06em;[^}]*text-transform: uppercase;/);
  });
});

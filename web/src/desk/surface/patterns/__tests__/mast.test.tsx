// Mast (the language, 2026-11-08): the desk's sprite for the kind, the title
// in the display face, the mono facts line, the verbs slot; the title steps
// down by a container query on the mast, never by the viewport.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Button } from "../../../../components/signal/Button";
import { Mast } from "../Mast";
import mastCss from "../mast.css?raw";

describe("Mast", () => {
  it("draws the kind's 32 px illustrated sprite, never a coloured block", () => {
    render(<Mast kind="project" title="HoldSpeak" data-testid="mast" />);
    const glyph = screen.getByTestId("mast").querySelector("img.surface-mast-glyph") as HTMLImageElement;
    expect(glyph).not.toBeNull();
    expect(glyph.getAttribute("src")).toMatch(/desk\/sprites\/32\/project-drawer\.png$/);
    expect(glyph.width).toBe(32);
    expect(glyph.getAttribute("alt")).toBe("");
  });

  it("picks the agent sprite for an agent and the zone hue by id", () => {
    render(<>
      <Mast kind="agent" agent="codex" title="Codex" data-testid="agent" />
      <Mast kind="directory" id="hs-seed-work" title="Work" data-testid="zone" />
    </>);
    expect(screen.getByTestId("agent").querySelector("img")!.getAttribute("src")).toMatch(/32\/agent-codex\.png$/);
    expect(screen.getByTestId("zone").querySelector("img")!.getAttribute("src")).toMatch(/32\/zone-drawer-teal\.png$/);
  });

  it("says the title as a heading, the facts once, and the verbs as library Buttons", () => {
    render(
      <Mast kind="program" title="The night" facts="4 steps · 2 done" data-testid="mast">
        <Button variant="brass">Decide</Button>
      </Mast>,
    );
    expect(screen.getByRole("heading", { name: "The night" }).className).toBe("surface-mast-title");
    expect(screen.getByText("4 steps · 2 done").className).toBe("surface-mast-facts");
    const verb = screen.getByRole("button", { name: "Decide" });
    expect(verb.className).toContain("btn--brass");
    expect(verb.closest(".surface-mast-verbs")).not.toBeNull();
  });

  it("draws no empty facts line or verbs slot", () => {
    render(<Mast kind="note" title="A note" data-testid="mast" />);
    const mast = screen.getByTestId("mast");
    expect(mast.querySelector(".surface-mast-facts")).toBeNull();
    expect(mast.querySelector(".surface-mast-verbs")).toBeNull();
    expect(mast.getAttribute("data-kind")).toBe("note");
  });

  it("steps the title 24/28 to 20/24 on its own container, never the viewport", () => {
    expect(mastCss).toMatch(/\.surface-mast\s*\{[^}]*container:\s*mast\s*\/\s*inline-size/);
    expect(mastCss).toMatch(/\.surface-mast-title\s*\{[^}]*font:\s*600 24px \/ 28px var\(--font-display\)/);
    expect(mastCss).toMatch(/\.surface-mast-title\s*\{[^}]*letter-spacing:\s*var\(--letter-spacing-tight\)/);
    const narrow = mastCss.slice(mastCss.indexOf("@container mast (max-width: 559.9px)"));
    expect(narrow).toMatch(/font-size:\s*20px;\s*line-height:\s*24px/);
    expect(mastCss).not.toMatch(/@media/);
    expect(mastCss).toMatch(/\.surface-mast-facts\s*\{[^}]*font:\s*400 12px \/ 16px var\(--font-mono\)/);
  });
});

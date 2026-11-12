// One object Mast; material type steps with its frame, never the viewport.
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

  it("uses the material type tokens and compacts on the frame container", () => {
    expect(mastCss).toMatch(/font: var\(--material-title-weight\) var\(--material-title-size\)/);
    expect(mastCss).toContain("@container window-frame (max-width: 559.9px)");
    expect(mastCss).toContain("font-size: var(--material-title-compact-size)");
    expect(mastCss).not.toContain("var(--font-mono)");
    expect(mastCss).not.toMatch(/@media/);
  });
});

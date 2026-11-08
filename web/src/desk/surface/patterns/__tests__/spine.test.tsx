// Spine (the language, 2026-11-08): a 4 px bar in the six meaning tones,
// from segments or from one tone and a fill.
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Spine, spineSegments } from "../Spine";
import spineCss from "../spine.css?raw";

function parts(testId: string): { tone: string | null; grow: string }[] {
  return Array.from(screen.getByTestId(testId).querySelectorAll<HTMLElement>(".surface-spine-part"))
    .map((part) => ({ tone: part.getAttribute("data-tone"), grow: part.style.flexGrow }));
}

describe("Spine", () => {
  it("draws one part a segment, in its tone and share", () => {
    render(<Spine data-testid="spine" segments={[
      { tone: "moss", share: 2 },
      { tone: "steel", share: 1 },
      { tone: "brass", share: 1 },
      { tone: "coral", share: 0 },
    ]} />);
    expect(parts("spine")).toEqual([
      { tone: "moss", grow: "2" },
      { tone: "steel", grow: "1" },
      { tone: "brass", grow: "1" },
    ]);
    expect(screen.getByTestId("spine").getAttribute("data-mode")).toBe("segments");
  });

  it("draws one tone and a fill, the rest idle", () => {
    render(<>
      <Spine data-testid="part" tone="steel" fill={0.25} />
      <Spine data-testid="full" tone="moss" fill={1} />
      <Spine data-testid="none" tone="coral" fill={-3} />
    </>);
    expect(parts("part")).toEqual([{ tone: "steel", grow: "0.25" }, { tone: "idle", grow: "0.75" }]);
    expect(parts("full")).toEqual([{ tone: "moss", grow: "1" }]);
    expect(parts("none")).toEqual([{ tone: "idle", grow: "1" }]);
    expect(screen.getByTestId("part").getAttribute("data-mode")).toBe("fill");
  });

  it("says its label as one image, and hides itself without one", () => {
    render(<>
      <Spine data-testid="named" tone="steel" fill={0.5} label="2 of 4 done" />
      <Spine data-testid="quiet" tone="steel" fill={0.5} />
    </>);
    expect(screen.getByRole("img", { name: "2 of 4 done" })).toBe(screen.getByTestId("named"));
    expect(screen.getByTestId("quiet").getAttribute("aria-hidden")).toBe("true");
  });

  it("takes every tone from the language tokens, 4 px high", () => {
    for (const tone of ["steel", "brass", "moss", "coral", "graphite"])
      expect(spineCss).toContain(`[data-tone="${tone}"] { background: var(--hs-${tone}); }`);
    expect(spineCss).toMatch(/\.surface-spine\s*\{[^}]*height:\s*4px/);
    expect(spineCss).not.toMatch(/#[0-9a-f]{3,8}\b/i);
  });

  it("defaults a bare spine to a full steel bar", () => {
    expect(spineSegments({})).toEqual([{ tone: "steel", share: 1 }]);
  });
});

/* First run, option A "One screen" (owner ratified 2026-10-05) — the
   three species it added to the library: ReadyStrip, StartVerb, and the
   lit state on ChoiceCardShell (no motion when reduced). */
import { render, screen, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import { ChoiceCardShell, ReadyStrip, StartVerb, StartVerbs } from "..";

const css = (name: string) => readFileSync(resolve(__dirname, "../patterns", name), "utf8");

describe("ReadyStrip", () => {
  it("one success chip per step, in order; an empty label gives no chip", () => {
    render(
      <ReadyStrip
        items={[
          { key: "a", label: "LOCAL AI · ON DEVICE" },
          { key: "b", label: "" },
          { key: "c", label: "HEARD · 8 WORDS" },
        ]}
      />,
    );
    const strip = screen.getByRole("list", { name: "Ready" });
    const chips = within(strip).getAllByRole("status");
    expect(chips.map((c) => c.getAttribute("aria-label"))).toEqual(["LOCAL AI · ON DEVICE", "HEARD · 8 WORDS"]);
    expect(chips.every((c) => c.getAttribute("data-state") === "success")).toBe(true);
    expect(chips[0].textContent).toBe("✓LOCAL AI · ON DEVICE");
  });

  it("no items, no strip (no empty section)", () => {
    const { container } = render(<ReadyStrip items={[{ key: "a", label: " " }]} />);
    expect(container.innerHTML).toBe("");
  });
});

describe("StartVerb", () => {
  it("is the library Button: glyph over word, the glyph hidden from the reader", () => {
    const press = vi.fn();
    render(
      <StartVerbs>
        <StartVerb glyph="◉" variant="primary" onClick={press}>
          Record Atlas weekly · 10:30
        </StartVerb>
        <StartVerb glyph="◖">Dictate</StartVerb>
      </StartVerbs>,
    );
    const group = screen.getByRole("group", { name: "Start" });
    const [record, dictate] = within(group).getAllByRole("button");
    expect(record.className).toContain("btn btn--primary");
    expect(record.className).toContain("surface-start-verb");
    expect(dictate.className).toContain("btn--secondary");
    expect(record.querySelector(".surface-start-verb-glyph")?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.getByRole("button", { name: "Record Atlas weekly · 10:30" })).toBe(record);
    record.click();
    expect(press).toHaveBeenCalledTimes(1);
  });

  it("the plate is 72 px tall and the set stacks at the narrow container", () => {
    const sheet = css("start-verb.css");
    expect(sheet).toMatch(/\.surface-start-verb\.btn\s*{[^}]*min-height:\s*72px/);
    expect(sheet).toMatch(/@container surface \(max-width: 720px\)\s*{\s*\.surface-start-verbs\s*{\s*grid-auto-flow:\s*row/);
  });
});

describe("ChoiceCardShell lit", () => {
  it("stamps data-lit only when lit", () => {
    const { rerender } = render(<ChoiceCardShell data-testid="card" label="Calendar" lit />);
    expect(screen.getByTestId("card").getAttribute("data-lit")).toBe("true");
    rerender(<ChoiceCardShell data-testid="card" label="Calendar" />);
    expect(screen.getByTestId("card").getAttribute("data-lit")).toBeNull();
  });

  it("the ring is the library's, and reduced motion turns its fade off", () => {
    const sheet = css("choice-card.css");
    expect(sheet).toMatch(/\.surface-choice-card\[data-lit\]\s*{[^}]*border-color:[^}]*var\(--ok\)/);
    expect(sheet).toMatch(
      /@media \(prefers-reduced-motion: reduce\)\s*{\s*\.surface-choice-card\[data-lit\]\s*{\s*animation:\s*none/,
    );
  });
});

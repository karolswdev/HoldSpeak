// THE FOLD (owner 2026-11-01: "that left chevron something: fuck off";
// canvas docs/internal/betterment/canvases/fold-2026-11-01.html, direction
// B). A section that opens in place says Show or Hide at the right; no
// triangle or chevron is drawn by the kit's folds or by Today's.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { FoldGadget } from "../fold";
import { Disclosure } from "../patterns/Disclosure";

const css = (path: string) => readFileSync(resolve(__dirname, "..", "..", path), "utf8");

describe("the fold grammar", () => {
  it("FoldGadget and Disclosure draw no triangle; the open state is aria and the verb", () => {
    const { container } = render(
      <>
        <FoldGadget title="Decided for you" token="2" open>{"rows"}</FoldGadget>
        <Disclosure label="Sources">{"body"}</Disclosure>
      </>,
    );
    expect(container.textContent).not.toMatch(/[▸▾▴▶›]/);
    expect(screen.getByRole("button", { name: "Sources" })).toHaveAttribute("aria-expanded", "false");
  });

  it("the CSS says Show and Hide, and no fold draws a triangle", () => {
    const gadgets = css("surface/gadgets.css");
    expect(gadgets).toMatch(/\.gadget-fold > summary::after \{\s*content: "Show"/);
    expect(gadgets).toMatch(/\.gadget-fold\[open\] > summary::after \{\s*content: "Hide"/);
    const disclosure = css("surface/patterns/disclosure.css");
    expect(disclosure).toContain('content: "Show"');
    expect(disclosure).toContain('content: "Hide"');
    const today = css("pullouts/views/today.css");
    expect(today).toContain('.today-fold-head[aria-expanded="true"]::after { content: "Hide"; }');
    for (const sheet of [gadgets, disclosure, today]) expect(sheet).not.toMatch(/content: "[▸▾▴▶›]"/);
  });
});

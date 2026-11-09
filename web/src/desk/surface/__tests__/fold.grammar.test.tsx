// THE FOLD (owner 2026-11-01: "that left chevron something: fuck off";
// canvas docs/internal/betterment/canvases/fold-2026-11-01.html, direction
// B). A section that opens in place says Show or Hide at the right; no
// triangle or chevron is drawn by the kit's folds or by Today's.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fireEvent, render, screen } from "@testing-library/react";
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
    // The word (Show, Hide) is CSS on the trigger; the button keeps its
    // heading's name, folded and open (the stylesheets load: css: true).
    fireEvent.click(screen.getByRole("button", { name: "Sources" }));
    expect(screen.getByRole("button", { name: "Sources" })).toHaveAttribute("aria-expanded", "true");
  });

  it("the CSS says Show and Hide, and no fold draws a triangle", () => {
    const gadgets = css("surface/gadgets.css");
    expect(gadgets).toMatch(/\.gadget-fold > summary::after \{\s*content: "Show"/);
    expect(gadgets).toMatch(/\.gadget-fold\[open\] > summary::after \{\s*content: "Hide"/);
    const disclosure = css("surface/patterns/disclosure.css");
    expect(disclosure).toContain('content: "Show"');
    expect(disclosure).toContain('content: "Hide"');
    // The word rides the hit-face pseudo; it is a flex item, never the
    // absolute layer over the label (fix forward #2070).
    expect(disclosure).toMatch(/trigger::after \{\s*content: "Show";[^}]*position: static;/);
    const today = css("pullouts/views/today.css");
    // Today's word is the ::before: the library Button's ::after is its hit
    // face (#1757), so the fold word cannot ride it.
    expect(today).toContain('.today-fold-head[aria-expanded="true"]::before { content: "Hide"; }');
    for (const sheet of [gadgets, disclosure, today]) expect(sheet).not.toMatch(/content: "[▸▾▴▶›]"/);
  });
});

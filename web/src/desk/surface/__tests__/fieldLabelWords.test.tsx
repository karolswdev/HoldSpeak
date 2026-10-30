/** FIELD-LABELS-WORDS (2026-10-30): the field and check-box labels draw
 *  in sentence case at the species. The StringGadget caption, the token
 *  check, the check and its word, and the group legend have no caps
 *  transform and no mono face (the Window grammar: a label is sans in
 *  sentence case; sections are never mono uppercase). The caption step's
 *  caps (UX-CANON C) stays for the eyebrow species only. */
import { describe, expect, it } from "vitest";
import { render } from "@testing-library/react";
import { CheckGadget, GadgetGroup, GadgetRow, StringGadget } from "../gadgets";
import gadgetsCss from "../gadgets.css?raw";
import surfaceCss from "../surface.css?raw";

const rule = (css: string, selector: string) =>
  new RegExp(`\\n${selector.replace(/[.]/g, "\\.")} \\{([^}]*)\\}`).exec(css)?.[1] ?? "";

describe("field and check-box labels draw sentence case", () => {
  it("a StringGadget caption, a token check, a group legend and a row label carry no caps transform", () => {
    const { container } = render(
      <GadgetGroup label="Where it runs">
        <GadgetRow label="Server address">
          <StringGadget label="Server address" caption value="" onChange={() => undefined} mic={false} />
        </GadgetRow>
        <CheckGadget variant="token" label="My server" checked={false} onChange={() => undefined} />
        <CheckGadget variant="token" label="My server" checked onChange={() => undefined} />
      </GadgetGroup>,
    );
    const faces = [
      ".gadget-string-caption",
      ".gadget-check-token-face",
      ".gadget-group-label",
      ".gadget-row-label",
    ].map((selector) => {
      const el = container.querySelector(selector);
      expect(el, selector).not.toBeNull();
      return [selector, getComputedStyle(el!).textTransform] as const;
    });
    for (const [selector, transform] of faces) expect(transform, selector).not.toBe("uppercase");
    expect(container.querySelector(".gadget-string-caption")?.textContent).toBe("Server address");
    expect(container.querySelector(".gadget-check-token.is-off .gadget-check-token-face")?.textContent).toBe("My server");
    expect(container.querySelector(".gadget-check-token.is-on .gadget-check-token-face")?.textContent).toBe("✓ My server");
  });

  it.each([".gadget-string-caption", ".gadget-check-token-face", ".gadget-checkline-word", ".gadget-group-label"])(
    "the species rule %s is sans, no caps, no wide tracking",
    (selector) => {
      const body = rule(gadgetsCss, selector);
      expect(body, selector).not.toBe("");
      expect(body).not.toMatch(/text-transform:\s*uppercase/);
      expect(body).not.toMatch(/--font-mono/);
      expect(body).toMatch(/letter-spacing:\s*0;/);
      expect(body).toMatch(/var\(--font-sans\)/);
    },
  );

  it("the eyebrow keeps the caption step's caps (UX-CANON C), and the cascade is read", () => {
    expect(rule(surfaceCss, ".surface-eyebrow")).toMatch(/text-transform:\s*uppercase/);
    // The control for the first case: the same computed read sees a caps rule.
    const { container } = render(<span className="surface-eyebrow">Drawers</span>);
    expect(getComputedStyle(container.firstElementChild!).textTransform).toBe("uppercase");
  });
});

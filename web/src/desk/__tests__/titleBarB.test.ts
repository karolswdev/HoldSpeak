// PHILO-13-11 — title bar B, "Workbench refined" (the owner's pick, 2026-10-03:
// "B"; boards pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/titlebar-canvas/,
// design/workbench-look.md §3). The static fence for the rule: stripes on the
// FRONT bar only, inactive bars flat, the title on the bar (a cut-out in the
// front bar's own blue, no contrasting plate), one gadget grid, every colour a
// --wb-* token. The glass proof is tests/e2e/test_philo13_11_titlebar_glass.py.
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const WEB = resolve(__dirname, "../../..");
const chrome = readFileSync(resolve(WEB, "src/desk/components/window-chrome.css"), "utf-8");
const tokens = readFileSync(resolve(WEB, "src/styles/tokens.css"), "utf-8");

/** The declaration block of the rule whose selector list is exactly `selector`. */
function rule(selector: string): string {
  const at = chrome.indexOf(`\n${selector} {`);
  expect(at, selector).toBeGreaterThan(-1);
  return chrome.slice(at, chrome.indexOf("}", at));
}
const decl = (block: string, prop: string) => {
  const m = block.match(new RegExp(`\\n\\s*${prop}:\\s*([^;]+);`));
  return m ? m[1].trim() : null;
};

const BAR = ".desk-next .desk-window-shell > .desk-pullout-head";
const FRONT_BAR = ".desk-next .desk-window-shell.is-front > .desk-pullout-head";
const TITLE = `${BAR} .desk-pullout-title`;
const FRONT_TITLE = `${FRONT_BAR} .desk-pullout-title`;
const INACTIVE_TITLE = ".desk-next .desk-window-shell:not(.is-front) > .desk-pullout-head .desk-pullout-title";

describe("title bar B: the tokens", () => {
  it("defines the four B tokens once", () => {
    for (const [name, value] of Object.entries({
      "--wb-stipple-fine": "repeating-linear-gradient(180deg, transparent 0 2px, rgba(11, 12, 16, 0.07) 2px 3px)",
      "--wb-ink-dim": "#2a2e36",
      "--wb-rule": "rgba(11, 12, 16, 0.45)",
      "--wb-raised-soft": "inset 1px 1px 0 rgba(255, 255, 255, 0.36), inset -1px -1px 0 rgba(0, 0, 0, 0.25)",
    })) {
      const hits = tokens.match(new RegExp(`^\\s*${name}:\\s*([^;]+);`, "gm")) ?? [];
      expect(hits, name).toHaveLength(1);
      expect(hits[0]).toContain(value);
    }
  });
});

describe("title bar B: the rule", () => {
  it("inactive bars are flat: steel, no stripes, no bevel; the ink rule under the bar stays", () => {
    const bar = rule(BAR);
    expect(decl(bar, "background")).toBe("var(--wb-steel)");
    expect(decl(bar, "box-shadow")).toBe("inset 0 -1px 0 var(--wb-ink)");
  });

  it("only the front bar carries stripes: the fine stipple on the front pen", () => {
    expect(decl(rule(FRONT_BAR), "background")).toBe("var(--wb-stipple-fine), var(--wb-blue)");
    // no other rule in the chrome paints a stipple
    const stipples = chrome.match(/var\(--wb-stipple(-fine)?\)/g) ?? [];
    expect(stipples).toEqual(["var(--wb-stipple-fine)"]);
  });

  it("the title sits on the bar: no plate when inactive, a cut-out in the bar's own blue in front", () => {
    const title = rule(TITLE);
    expect(decl(title, "background")).toBe("transparent");
    expect(decl(title, "font")).toBe("700 12px/calc(var(--wb-bar-h) - 2px) var(--font-mono)");
    expect(decl(title, "margin")).toBe("0 6px 1px");
    expect(decl(rule(FRONT_TITLE), "background")).toBe("var(--wb-blue)");
    expect(decl(rule(INACTIVE_TITLE), "color")).toBe("var(--wb-ink-dim)");
  });

  it("one gadget grid: cells the gadget width by the bar's full height, one hairline, a half-strength bevel", () => {
    const g = rule(".desk-next .desk-pullout-head .desk-gadget");
    expect(decl(g, "width")).toBe("var(--wb-gadget-w)");
    expect(decl(g, "height")).toBe("100%");
    expect(decl(g, "box-shadow")).toBe("var(--wb-raised-soft)");
    expect(decl(rule(".desk-next .desk-gadgets-left .desk-gadget"), "border-right")).toBe("1px solid var(--wb-rule)");
    // the right cells draw their hairline as an inset shadow (HS-101 rule 6: no left rail)
    expect(decl(rule(".desk-next .desk-gadgets-right .desk-gadget"), "box-shadow")).toBe("inset 1px 0 0 var(--wb-rule), var(--wb-raised-soft)");
    expect(decl(rule(`${FRONT_BAR} .desk-gadget`), "background")).toBe("var(--wb-blue)");
  });

  it("393 keeps 44 px: the phone sizes are untouched", () => {
    const pullout = readFileSync(resolve(WEB, "src/desk/components/pullout.css"), "utf-8");
    expect(pullout).toMatch(/--wb-bar-h: 44px;/);
    expect(pullout).toMatch(/--wb-gadget-w: 44px;/);
  });

  it("no one-off colour in the title bar rules: every colour is a --wb-* token", () => {
    const start = chrome.indexOf(`\n${BAR} {`);
    const end = chrome.indexOf("/* the wing tabs in a title bar");
    expect(end).toBeGreaterThan(start);
    const block = chrome.slice(start, end).replace(/\/\*[\s\S]*?\*\//g, "");
    expect(block).not.toMatch(/#[0-9a-f]{3,8}\b|rgba?\(/i);
  });
});

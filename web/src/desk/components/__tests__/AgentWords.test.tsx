// Phase 16 — AgentWords: the subset, the safety, the compact cut.
// Canvas: docs/internal/philo/phase-16/02-canvas/agent-words.html.
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  AgentWords,
  agentWordsPlain,
  askOf,
  compactUnits,
  compactWords,
  cutAtWord,
  fitCount,
  parseAgentWords,
  parseInline,
} from "../AgentWords";
import { OWNER_TEXT, noLiteralMarks } from "./fixtures.agentWords";

function draw(text: string, compact = false) {
  const { container } = render(<AgentWords text={text} compact={compact} data-testid="aw" />);
  return container.querySelector("[data-testid='aw']") as HTMLElement;
}

describe("AgentWords: the subset", () => {
  it("draws the owner's text: a list of three, bold, code, no marks as text", () => {
    const el = draw(OWNER_TEXT);
    const ol = el.querySelector("ol")!;
    expect(ol.querySelectorAll(":scope > li")).toHaveLength(3);
    expect([...el.querySelectorAll("strong")].map((s) => s.textContent)).toContain("project.list");
    expect([...el.querySelectorAll("code")].map((c) => c.textContent)).toEqual(
      expect.arrayContaining(["hosts: not read", "45e2b1a"]),
    );
    expect(el.querySelectorAll("p")).toHaveLength(3);
    noLiteralMarks(el.textContent ?? "");
  });

  it("bold holds code: the question's branch is code inside the bold line", () => {
    const el = draw("**May I open a PR for `hs/x` now?**");
    const strong = el.querySelector("strong")!;
    expect(strong.querySelector("code")?.textContent).toBe("hs/x");
    expect(strong.textContent).toBe("May I open a PR for hs/x now?");
  });

  it("italic with * and _; snake_case stays a name", () => {
    const el = draw("an *a* and _b_ in my_var_name");
    expect([...el.querySelectorAll("em")].map((e) => e.textContent)).toEqual(["a", "b"]);
    expect(el.textContent).toContain("my_var_name");
  });

  it("a fenced block: monospace, its language as a token, the text kept", () => {
    const el = draw("Run:\n\n```bash\nls -la\n**not bold**\n```\nDone.");
    const pre = el.querySelector("pre")!;
    expect(pre.querySelector(".aw-lang")?.textContent).toBe("BASH");
    expect(pre.querySelector("code")?.textContent).toBe("ls -la\n**not bold**");
    expect(el.querySelector("p:last-child")?.textContent).toBe("Done.");
  });

  it("a bulleted list nested one level; a heading is a bold line, no heading tag", () => {
    const el = draw("# Plan\n- one\n  - one a\n- two");
    expect(el.querySelector("h1,h2,h3,h4,h5,h6")).toBeNull();
    expect(el.querySelector("strong.aw-h")?.textContent).toBe("Plan");
    const top = el.querySelector("ul")!;
    expect(top.querySelectorAll(":scope > li")).toHaveLength(2);
    expect(top.querySelector("li > ul > li")?.textContent).toBe("one a");
  });

  it("an ordered list keeps its start", () => {
    const el = draw("3. three\n4. four");
    expect(el.querySelector("ol")?.getAttribute("start")).toBe("3");
  });

  it("line breaks inside a paragraph are kept", () => {
    const el = draw("line one\nline two");
    expect(el.querySelectorAll("p br")).toHaveLength(1);
  });

  it("a link is its text and then its address, never an anchor", () => {
    const el = draw("See [the docs](https://example.com/docs) and <https://x.dev>.");
    expect(el.querySelector("a")).toBeNull();
    expect(el.textContent).toBe("See the docs https://example.com/docs and https://x.dev.");
  });

  it("an image is its alt text in brackets", () => {
    expect(draw("![diagram](d.png)").textContent).toBe("[diagram]");
  });

  it("HTML is text: no element is made from it", () => {
    const el = draw('<script>alert(1)</script> <img src=x onerror="alert(2)"> <b>x</b>');
    expect(el.querySelector("script,img,b")).toBeNull();
    expect(el.textContent).toContain("<script>alert(1)</script>");
    expect(el.textContent).toContain("<b>x</b>");
  });

  it("long tokens break after / _ - .", () => {
    const el = draw("`hs/project_item-pitem_d25d3fc020be4d8cbc90269fc17da3f7`");
    expect(el.querySelectorAll("code wbr").length).toBeGreaterThanOrEqual(4);
    expect(el.querySelector("code")?.textContent).toBe("hs/project_item-pitem_d25d3fc020be4d8cbc90269fc17da3f7");
  });

  it("an empty text draws nothing", () => {
    const { container } = render(<AgentWords text="   " />);
    expect(container.innerHTML).toBe("");
  });

  it("parses the block and inline models", () => {
    expect(parseAgentWords("a\n\nb").map((b) => b.kind)).toEqual(["p", "p"]);
    expect(parseInline("**a `b`**")).toEqual([{ t: "strong", c: [{ t: "text", v: "a " }, { t: "code", v: "b" }] }]);
    expect(parseInline("2 * 3 * 4")).toEqual([{ t: "text", v: "2 * 3 * 4" }]);
  });
});

describe("AgentWords: compact", () => {
  it("one line with no ask: blocks joined with ·, marks kept, no list markers", () => {
    const steps = "Steps done:\n\n1. **project.list** called\n2. `NOTES.md` written";
    const el = draw(steps, true);
    expect(el.classList.contains("is-compact")).toBe(true);
    expect(el.querySelector("p,ol,ul,pre")).toBeNull();
    expect(el.querySelector("strong")?.textContent?.trim()).toBe("project.list");
    expect(el.textContent).toBe("Steps done: · project.list called · NOTES.md written");
    noLiteralMarks(el.textContent ?? "");
  });

  it("the ask leads (ruling 2026-10-08): the last paragraph that ends with ? is the line", () => {
    const el = draw(OWNER_TEXT, true);
    expect(el.textContent?.startsWith("May I open a pull request for branch hs/project_item-")).toBe(true);
    expect(el.textContent).toContain("(naming project_item:pitem_d25d3fc020be4d8cbc90269fc17da3f7 in the body)?");
    expect([...el.querySelectorAll("strong")].map((s) => s.textContent).join("")).toContain("hs/project_item-");
    expect(el.querySelector("strong code")).not.toBeNull();
    noLiteralMarks(el.textContent ?? "");
    // The LAST asking paragraph; a list item or a heading can be it too.
    expect(askOf("Ready?\n\nDone.\n\nShall I push?")).toBe("Shall I push?");
    expect(askOf("- one\n- **may I merge?**")).toBe("**may I merge?**");
    expect(askOf("No question here.")).toBeNull();
    // Not an agent's turn (the SENT line): the start, as before.
    const sent = render(<AgentWords compact ask={false} text={"Brief.\n\nMay I?"} data-testid="s" />).container;
    expect(sent.querySelector("[data-testid='s']")?.textContent).toBe("Brief. · May I?");
  });

  it("the plain words carry the full text on hover (title), marks removed", () => {
    const el = draw("**May** I `push`?", true);
    expect(el.getAttribute("title")).toBe("May I push?");
    // The hover holds the whole words, not only the ask.
    expect(draw(OWNER_TEXT, true).getAttribute("title")?.startsWith("Steps 1–3 complete: · project.list")).toBe(true);
  });

  it("a long text is cut at a whole word with …", () => {
    const { words, cut } = compactWords(OWNER_TEXT, 60);
    expect(cut).toBe(true);
    const shown = words.map((w) => w.map((p) => p.v).join("")).join("");
    const whole = agentWordsPlain(OWNER_TEXT, 10_000);
    expect(whole.startsWith(shown.trimEnd())).toBe(true);
    // The next character in the whole text is a space: the cut is between words.
    expect(whole[shown.trimEnd().length]).toBe(" ");
  });

  it("cutAtWord never ends inside a word", () => {
    const out = cutAtWord(OWNER_TEXT, 50);
    expect(out.endsWith(" …")).toBe(true);
    const kept = out.slice(0, -2);
    expect(OWNER_TEXT.replace(/\s+/g, " ").startsWith(kept)).toBe(true);
    expect(OWNER_TEXT.replace(/\s+/g, " ")[kept.length]).toBe(" ");
  });

  it("a long token is many cut units (after / _ - .); a short word is one", () => {
    const { words } = compactWords("branch `hs/project_item-pitem_d25d3f` now");
    const units = compactUnits(words).map((u) => u.word.map((p) => p.v).join(""));
    expect(units).toEqual(["branch ", "hs/", "project_", "item-", "pitem_", "d25d3f ", "now"]);
    expect(compactUnits(words).filter((u) => u.joined)).toHaveLength(4);
  });

  it("fitCount: all fit is null; else the last word that leaves room for …", () => {
    const box = { right: 100, bottom: 20 };
    const row = (rights: number[]) => rights.map((right) => ({ right, bottom: 18 }));
    expect(fitCount(row([20, 40, 60]), box, 10)).toBeNull();
    // The 4th word overflows; the 3rd ends at 95, no room for a 10px …: 2 words.
    expect(fitCount(row([20, 40, 95, 130]), box, 10)).toBe(2);
    // Two lines: a word on line 2 below the box overflows.
    expect(fitCount([{ right: 50, bottom: 18 }, { right: 30, bottom: 38 }], box, 10)).toBe(1);
  });

  it("agentWordsPlain flattens and cuts for an attribute", () => {
    expect(agentWordsPlain("# Title\n- **a**\n- `b`")).toBe("Title · a · b");
    expect(agentWordsPlain(OWNER_TEXT, 40).endsWith(" …")).toBe(true);
  });
});

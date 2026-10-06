/** ⌘K memory results, option B "Two-line hit" (canvas YDTpkaJqFs3hyrZ4g581Mx
 * §3, owner ratified 2026-10-05).
 *
 * Under the hit's title: the snippet with the match marked, a FoundBy token
 * (the real `retrieval_origin`) and the day. The selected row's plate reads
 * ≥ 4.5:1 (computed from the tokens). Real store, real palette; the hub
 * transport is the double. */
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import chromeMenusCss from "../components/chrome-menus.css?raw";
import tokensCss from "../../styles/tokens.css?raw";

const apiFetch = vi.fn();
vi.mock("../../lib/api", async () => {
  const actual = await vi.importActual<typeof import("../../lib/api")>("../../lib/api");
  return { ...actual, apiFetch: (...args: unknown[]) => apiFetch(...args) };
});
vi.mock("../shell", async () => {
  const actual = await vi.importActual<typeof import("../shell")>("../shell");
  return { ...actual, openSurface: () => true, openSurfaceOr: () => {} };
});

import { EMPTY_ITEMS, __resetHeldObjects } from "../api";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { DeskToolShelf, MEMORY_DEBOUNCE_MS } from "../components/DeskToolShelf";
import { snippetParts } from "../components/paletteHit";
import { foundByDay } from "../surface";

let hits: Array<Record<string, unknown>> = [];
const YEAR = new Date().getFullYear();

beforeEach(() => {
  __resetHeldObjects();
  localStorage.clear();
  hits = [];
  usePalette.setState({ open: false });
  apiFetch.mockReset();
  apiFetch.mockImplementation((path: string) =>
    Promise.resolve(path.startsWith("/api/memory/search?") ? { hits } : {}),
  );
  useDesk.setState({
    items: { ...EMPTY_ITEMS },
    projects: [],
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    refresh: vi.fn().mockResolvedValue(undefined),
    openToolInspector: vi.fn(),
    diveInto: vi.fn(),
  });
});

async function settle(ms = 0) {
  await act(async () => { await new Promise((r) => setTimeout(r, ms)); });
}

async function search(q: string) {
  render(<MemoryRouter><DeskToolShelf /></MemoryRouter>);
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  await settle();
  fireEvent.change(screen.getByRole("combobox", { name: "Search tools and Desk items" }), { target: { value: q } });
  await settle(MEMORY_DEBOUNCE_MS + 60);
}

const row = (name: RegExp) => screen.getByRole("option", { name });
const marks = (el: HTMLElement) => [...el.querySelectorAll("mark.desk-deck-mark")].map((m) => m.textContent);

describe("⌘K two-line hit", () => {
  it("draws the title, then the snippet line, then FoundBy and the day", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:m-1", title: "Atlas weekly",
      snippet: "Priya takes the <mark>rollback</mark> plan; Marek reviews it on Thursday.",
      retrieval_origin: "lexical", occurred_at: `${YEAR}-10-01T09:30:00` }];
    await search("rollback");
    const option = row(/Atlas weekly/);
    const label = option.querySelector(".desk-deck-label") as HTMLElement;
    // Line one: the title, as the first text of the label.
    expect(label.firstChild?.textContent).toBe("Atlas weekly");
    const line = within(label).getByText((_, el) => el?.classList.contains("desk-deck-hit") ?? false);
    const snippet = line.querySelector(".desk-deck-snippet") as HTMLElement;
    expect(snippet.textContent).toBe("Priya takes the rollback plan; Marek reviews it on Thursday.");
    expect(option.textContent).not.toContain("<mark>");
    expect(option.textContent).not.toContain(" · Priya");
    const meta = line.querySelector(".desk-deck-hit-meta") as HTMLElement;
    expect(meta.querySelector(".surface-foundby")?.textContent).toBe("KEYWORD");
    expect(meta.querySelector(".desk-deck-day")?.textContent).toBe("10-01");
    expect(option.getAttribute("data-wrap")).not.toBeNull();
  });

  it("marks the server's own match", async () => {
    hits = [{ kind: "note", source_ref: "note:n-1", title: "Runbook",
      snippet: "the <mark>rollbacks</mark> step, then the <mark>rolled</mark> check", retrieval_origin: "lexical" }];
    await search("rollback");
    // The server's stemmed match, as it marked it (the question's word alone
    // would mark `rollback` inside `rollbacks` and never `rolled`).
    expect(marks(row(/Runbook/))).toEqual(["rollbacks", "rolled"]);
  });

  it("a snippet the server cut again (a secret, no marks) marks the question's words and never the [redacted] marker", async () => {
    hits = [{ kind: "note", source_ref: "note:n-2", title: "Deploy keys",
      snippet: "the rollback key is [redacted] until the redacted window ends", retrieval_origin: "lexical" }];
    await search("rollback redacted");
    const option = row(/Deploy keys/);
    expect(marks(option)).toEqual(["rollback", "redacted"]);
    const redacted = option.querySelector(".desk-deck-redacted") as HTMLElement;
    expect(redacted.textContent).toBe("[redacted]");
    expect(redacted.closest("mark")).toBeNull();
    expect(option.querySelector(".desk-deck-snippet")?.textContent)
      .toBe("the rollback key is [redacted] until the redacted window ends");
  });

  it("a mark never cuts a [redacted] marker the server wrapped", () => {
    const parts = snippetParts("x <mark>a [redacted] b</mark> y", "zz");
    expect(parts.map((p) => [p.text, !!p.mark, !!p.redacted])).toEqual([
      ["x ", false, false], ["a ", true, false], ["[redacted]", false, true], [" b", true, false], [" y", false, false],
    ]);
  });

  it("a word is marked only at its start, never inside another word", () => {
    const parts = snippetParts("unrollback and rollbacks", "rollback");
    expect(parts.filter((p) => p.mark).map((p) => p.text)).toEqual(["rollback"]);
    expect(parts.map((p) => p.text).join("")).toBe("unrollback and rollbacks");
  });

  it("a chunk that opens with its title draws the title once (line one), not again on line two", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:m-9", title: "1:1 Marek",
      snippet: "1:1 Marek Marek: Marek asks who owns the fallback for Atlas.", retrieval_origin: "vector" }];
    await search("rollback");
    expect(row(/1:1 Marek/).querySelector(".desk-deck-snippet")?.textContent)
      .toBe("Marek: Marek asks who owns the fallback for Atlas.");
    // A title inside a word is not a lead: `Atlas weekly` does not cut `Atlas weeklyish`.
    expect(snippetParts("Atlas weeklyish plan", "zz", "Atlas weekly").map((p) => p.text).join("")).toBe("Atlas weeklyish plan");
  });

  it.each([
    ["lexical", "KEYWORD"],
    ["vector", "MEANING"],
    ["time", "TIME"],
    ["entity", "NAME"],
    ["relationship", "LINK"],
  ])("FoundBy: %s shows %s", async (origin, word) => {
    hits = [{ kind: "note", source_ref: "note:n-3", title: "Cutover", snippet: "go back to the old cluster",
      retrieval_origin: origin, occurred_at: `${YEAR}-09-29` }];
    await search("rollback");
    const tokens = [...row(/Cutover/).querySelectorAll(".surface-foundby")];
    expect(tokens.map((t) => t.textContent)).toEqual([word]);
    expect(tokens[0].getAttribute("data-by")).toBe(word);
  });

  it("an origin with no word shows no token (never a guess)", async () => {
    hits = [{ kind: "note", source_ref: "note:n-4", title: "Seen", snippet: "watch it", retrieval_origin: "observation",
      occurred_at: `${YEAR}-09-29` }];
    await search("watch");
    const option = row(/Seen/);
    expect(option.querySelector(".surface-foundby")).toBeNull();
    expect(option.querySelector(".desk-deck-day")?.textContent).toBe("09-29");
  });

  it("the day: MM-DD this year, the year when it is another", () => {
    const now = new Date(2026, 9, 5);
    expect(foundByDay("2026-10-01", now)).toBe("10-01");
    expect(foundByDay("2025-10-01", now)).toBe("2025-10-01");
    expect(foundByDay("", now)).toBe("");
    expect(foundByDay("junk", now)).toBe("");
  });

  it("a hit with no snippet, no origin word and no day is its title alone: no empty line, no empty token", async () => {
    hits = [{ kind: "note", source_ref: "note:n-5", title: "Bare" }];
    await search("bare");
    const option = row(/Bare/);
    expect(option.querySelector(".desk-deck-snippet")).toBeNull();
    expect(option.querySelector(".desk-deck-hit-meta")).toBeNull();
    expect(option.querySelector(".surface-token")).toBeNull();
  });

  it("empty: no hits shows no MEMORY band and no FoundBy", async () => {
    hits = [];
    await search("rollback");
    expect([...document.querySelectorAll(".desk-deck-band")].map((b) => b.textContent)).not.toContain("MEMORY");
    expect(document.querySelector(".surface-foundby")).toBeNull();
    expect(screen.getByText("No matching tools or Desk items.")).toBeTruthy();
  });
});

/* ── the selected row's contrast, computed from the tokens ── */
function token(name: string): string {
  const m = new RegExp(`${name}:\\s*(#[0-9a-fA-F]{6})\\b`).exec(tokensCss);
  if (!m) throw new Error(`token ${name} has no hex value`);
  return m[1];
}
function luminance(hex: string): number {
  const c = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255)
    .map((x) => (x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4));
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}
function contrast(a: string, b: string): number {
  const [x, y] = [luminance(a), luminance(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}
function ruleDecl(selectorStart: string, prop: string): string {
  const at = chromeMenusCss.indexOf(selectorStart);
  expect(at).toBeGreaterThanOrEqual(0);
  const block = chromeMenusCss.slice(chromeMenusCss.indexOf("{", at), chromeMenusCss.indexOf("}", at));
  const m = new RegExp(`(?:^|[;\\s{])${prop}:\\s*var\\((--[\\w-]+)\\)`).exec(block);
  if (!m) throw new Error(`${selectorStart} has no ${prop}: var(...)`);
  return m[1];
}

describe("the selected palette row reads ≥ 4.5:1", () => {
  it("the selected plate and its ink, from tokens.css", () => {
    const plate = ruleDecl(".desk-next .desk-deck-row.is-selected,\n", "background");
    const ink = ruleDecl(".desk-next .desk-deck-row.is-selected,\n", "color");
    expect(contrast(token(plate), token(ink))).toBeGreaterThanOrEqual(4.5);
  });

  it("the snippet ink on the selected plate, and the mark on its own plate", () => {
    const plate = ruleDecl(".desk-next .desk-deck-row.is-selected,\n", "background");
    const snippetInk = ruleDecl(".desk-next .desk-deck-row.is-selected .desk-deck-snippet", "color");
    expect(contrast(token(plate), token(snippetInk))).toBeGreaterThanOrEqual(4.5);
    expect(contrast(token(ruleDecl(".desk-next .desk-deck-mark", "background")),
      token(ruleDecl(".desk-next .desk-deck-mark", "color")))).toBeGreaterThanOrEqual(4.5);
  });

  it("the snippet on the plain row reads ≥ 4.5:1 on the shelf plate", () => {
    const ink = ruleDecl(".desk-next .desk-deck-snippet {", "color");
    expect(contrast(token("--surface-3"), token(ink))).toBeGreaterThanOrEqual(4.5);
  });
});

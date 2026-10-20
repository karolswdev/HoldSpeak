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
  fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: q } });
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
    // Betterment Q3: how it was found, in plain words (no chip).
    expect(meta.querySelector(".desk-deck-found")?.textContent).toBe("in the transcript");
    expect(meta.querySelector(".surface-foundby")).toBeNull();
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

  // Betterment Q3: only three ways read as words; any other shows nothing.
  it.each([
    ["lexical", "meeting", "meeting:m-3", ["in the transcript"]],
    ["lexical", "note", "note:n-3", ["in a note"]],
    ["vector", "note", "note:n-3", ["by meaning"]],
    ["vector", "meeting", "meeting:m-3", ["by meaning"]],
    ["lexical", "decision", "decision:d-3", []],
    ["time", "note", "note:n-3", []],
    ["entity", "note", "note:n-3", []],
    ["relationship", "note", "note:n-3", []],
  ])("found by %s in a %s shows %j", async (origin, kind, ref, words) => {
    hits = [{ kind, source_ref: ref, title: "Cutover", snippet: "go back to the old cluster",
      retrieval_origin: origin, occurred_at: `${YEAR}-09-29` }];
    await search("rollback");
    const option = row(/Cutover/);
    expect([...option.querySelectorAll(".desk-deck-found")].map((t) => t.textContent)).toEqual(words);
    expect(option.querySelector(".surface-foundby")).toBeNull();
    expect(option.textContent).not.toMatch(/KEYWORD|MEANING|LINK|NAME/);
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
    expect(document.querySelector(".desk-deck-found")).toBeNull();
    // Betterment Q3: with nothing found, Search still offers to ask.
    expect(screen.getAllByRole("option").map((o) => o.textContent)).toEqual(['✦Ask "rollback"Ask']);
  });
});

/* ── Astra's review of #882 (2026-10-05): four repros, each a fence ── */
const partsOf = (snippet: string, query: string, title = "") =>
  snippetParts(snippet, query, title).map((p) => [p.text, p.mark ? "mark" : p.redacted ? "redacted" : ""]);

describe("#882 review 1: only the title and its separator leave the snippet", () => {
  it("her repro: `Atlas: -5%` keeps the minus", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:review-negative", title: "Atlas",
      snippet: "Atlas: -5% <mark>rollback</mark> capacity.", retrieval_origin: "lexical" }];
    await search("rollback");
    expect(row(/Atlas/).querySelector(".desk-deck-snippet")?.textContent).toBe("-5% rollback capacity.");
  });

  it.each([
    ["Atlas -5% drop", "-5% drop"],
    ["Atlas — -3 days", "-3 days"],
    ["Atlas: .5 of the budget", ".5 of the budget"],
    ["Atlas, Priya and Marek", "Atlas, Priya and Marek"], // not a separator: whole
    ["Atlas.", "Atlas."],                                 // nothing after: whole
  ])("%s → %s", (snippet, shown) => {
    expect(snippetParts(snippet, "zz", "Atlas").map((p) => p.text).join("")).toBe(shown);
  });
});

describe("#882 review 3: a [redacted] marker is whole and never marked", () => {
  it("her repro: the server marked the marker's inside", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:review-redacted", title: "Imported transcript",
      snippet: "The [<mark>redacted</mark>] plan is approved.", retrieval_origin: "lexical" }];
    await search("redacted");
    const option = row(/Imported transcript/);
    expect(marks(option)).toEqual([]);
    expect([...option.querySelectorAll(".desk-deck-redacted")].map((r) => r.textContent)).toEqual(["[redacted]"]);
    expect(option.querySelector(".desk-deck-snippet")?.textContent).toBe("The [redacted] plan is approved.");
  });

  it("a server mark only inside a marker counts as no mark: the question's words outside are marked", () => {
    expect(partsOf("The [<mark>redacted</mark>] rollback plan", "redacted rollback")).toEqual([
      ["The ", ""], ["[redacted]", "redacted"], [" ", ""], ["rollback", "mark"], [" plan", ""],
    ]);
  });

  it("a server mark across a marker keeps its words outside the marker only", () => {
    expect(partsOf("x <mark>key [redac</mark>ted] y", "zz")).toEqual([
      ["x ", ""], ["key ", "mark"], ["[redacted]", "redacted"], [" y", ""],
    ]);
  });
});

describe("#882 review 4: a length-changing case never shifts a mark", () => {
  it("her repro: `İ rollback` marks exactly `rollback`", async () => {
    hits = [{ kind: "meeting", source_ref: "meeting:review-unicode", title: "Deploy window",
      snippet: "Owner: İ rollback plan; password=reviewSecret882", retrieval_origin: "lexical" }];
    await search("rollback");
    expect(marks(row(/Deploy window/))).toEqual(["rollback"]);
  });

  it.each(["ß", "ẞ", "ﬁ", "İİ"])("%s before the word: the mark is the word", (lead) => {
    const parts = snippetParts(`${lead} rollback plan`, "rollback");
    expect(parts.filter((p) => p.mark).map((p) => p.text)).toEqual(["rollback"]);
    expect(parts.map((p) => p.text).join("")).toBe(`${lead} rollback plan`);
  });

  it("a query in another case marks the original letters", () => {
    expect(partsOf("Die Maße sind ROLLBACK", "maße rollback").filter(([, k]) => k === "mark").map(([t]) => t))
      .toEqual(["Maße", "ROLLBACK"]);
  });
});

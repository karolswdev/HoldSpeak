/** Search (⌘K), Betterment Q3 "Search asks": the face half.
 *
 * The hub half is tests/unit/test_desk_search.py. It records the search for
 * "what did we decide about the freeze?" on the honest-faces seed plus a note
 * written in markdown and two threads, one never answered
 * (web/src/test/wire/memory-search.freeze-question.wire.json), and the Ask
 * answers come from tests/unit/test_desk_ask.py (ask.thread.wire.json).
 * Here fetch replays those answers; the palette, the store and the Ask window
 * are real. */
import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../shell", async () => {
  const actual = await vi.importActual<typeof import("../../shell")>("../../shell");
  return { ...actual, openSurface: () => true, openSurfaceOr: () => {} };
});
vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

import { EMPTY_ITEMS, __resetHeldObjects } from "../../api";
import type { Meeting, Note } from "../../../lib/primitives";
import { useDesk } from "../../store";
import { usePalette } from "../../chromeState";
import { clearEngineCache } from "../../hooks/useEngine";
import { DeskToolShelf, MEMORY_DEBOUNCE_MS, oneBandPerSection, readsLikeQuestion } from "../DeskToolShelf";
import { AskPanel } from "../AskPanel";
import FREEZE from "../../../test/wire/memory-search.freeze-question.wire.json";
import THREAD from "../../../test/wire/ask.thread.wire.json";

const QUESTION = "what did we decide about the freeze?";

type Call = { url: string; method: string; body: Record<string, unknown> | undefined };
let calls: Call[] = [];
let hits: unknown[] = FREEZE.wire.hits;

function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  __resetHeldObjects();
  localStorage.clear();
  clearEngineCache();
  calls = [];
  hits = FREEZE.wire.hits;
  usePalette.setState({ open: false });
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (url.startsWith("/api/memory/search?")) return Promise.resolve(reply({ ...FREEZE.wire, hits }));
    if (method === "POST" && url.endsWith("/api/ask")) return Promise.resolve(reply(THREAD.first));
    return Promise.resolve(reply({}));
  }));
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [
        { kind: "note", id: "n-freeze", title: "Freeze plan", bodyMarkdown: "", tags: [], createdAt: "" } as Note,
        { kind: "note", id: "n-ledger", title: "Ledger freeze checklist", bodyMarkdown: "", tags: [], createdAt: "" } as Note,
      ],
      meeting: [{ kind: "meeting", id: "m-freeze", title: "Freeze review" } as Meeting],
    },
    projects: [],
    inferenceTargets: [],
    models: [],
    setup: null,
    selectedIds: [],
    openPullout: vi.fn(),
    refresh: vi.fn().mockResolvedValue(undefined),
    askOpen: false,
    askThread: null,
    pullouts: [],
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

function Desk() {
  const askOpen = useDesk((s) => s.askOpen);
  return <MemoryRouter><DeskToolShelf />{askOpen ? <AskPanel /> : null}</MemoryRouter>;
}

async function settle(ms = 0) {
  await act(async () => { await new Promise((r) => setTimeout(r, ms)); });
}

async function search(text: string) {
  render(<Desk />);
  fireEvent.click(screen.getByRole("button", { name: /Search/ }));
  await settle();
  const input = screen.getByRole("combobox", { name: "Find, open or ask" });
  fireEvent.change(input, { target: { value: text } });
  await settle(MEMORY_DEBOUNCE_MS + 650);
  return input;
}

const options = () => screen.queryAllByRole("option");
const bands = () => [...document.querySelectorAll(".desk-deck-band")].map((b) => b.textContent);

describe("Betterment Q3: Search asks", () => {
  it("a question puts Ask \"…\" first and selected; Enter opens Ask with the text and shows the answer", async () => {
    const input = await search(QUESTION);
    const first = options()[0];
    expect(first.textContent).toContain(`Ask "${QUESTION}"`);
    expect(first.getAttribute("aria-selected")).toBe("true");

    fireEvent.keyDown(input, { key: "Enter" });
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
    // The palette closed; the Ask window asked the question as typed, as a new thread.
    expect(usePalette.getState().open).toBe(false);
    const asks = calls.filter((c) => c.method === "POST" && c.url.endsWith("/api/ask"));
    expect(asks).toHaveLength(1);
    expect(asks[0].body?.prompt).toBe(QUESTION);
    expect(asks[0].body?.thread).toBe(true);
    expect(screen.getByText(QUESTION, { selector: ".desk-ask-question-text" })).toBeInTheDocument();
  });

  it("text that is not a question puts Ask \"…\" last, and Enter opens the object", async () => {
    hits = [];
    const input = await search("freeze plan");
    const rows = options();
    expect(rows[rows.length - 1].textContent).toContain('Ask "freeze plan"');
    expect(rows[0].textContent).toContain("Freeze plan");
    fireEvent.keyDown(input, { key: "Enter" });
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:n-freeze");
    expect(calls.some((c) => c.url.endsWith("/api/ask"))).toBe(false);
  });

  it("text that is not a question puts Ask \"…\" above the MEMORY band, which lands later below it", async () => {
    await search("freeze");
    const rows = options();
    const ask = rows.findIndex((o) => o.textContent?.includes('Ask "freeze"'));
    const firstMemory = rows.findIndex((o) => o.querySelector(".desk-deck-hit"));
    expect(ask).toBeGreaterThan(0);
    expect(firstMemory).toBe(ask + 1);
  });

  it("reads like a question: a question mark, or a question word first", () => {
    for (const text of ["freeze?", "Who owns the cutover", "did we ship", "Is it frozen", "how", "which one"])
      expect(readsLikeQuestion(text), text).toBe(true);
    for (const text of ["freeze plan", "Mira", "rollback runbook", "whoever", ""])
      expect(readsLikeQuestion(text), text).toBe(false);
  });

  it("each kind is one section and uses the sentence-case kind words", async () => {
    await search("freeze");
    const drawn = bands();
    expect(new Set(drawn).size).toBe(drawn.length);
    expect(drawn).toEqual(expect.arrayContaining(["Note", "Meeting", "Ask"]));
    expect(oneBandPerSection([
      { section: "OBJECTS", id: 1 }, { section: "MEETINGS", id: 2 }, { section: "OBJECTS", id: 3 }, { section: "MEMORY", id: 4 }, { section: "MEETINGS", id: 5 },
    ]).map((r) => r.id)).toEqual([1, 3, 2, 5, 4]);
  });

  it("memory rows read as plain words: no markdown marks, no empty [], no raw ids, no unanswered thread", async () => {
    await search(QUESTION);
    const memory = options().filter((o) => o.querySelector(".desk-deck-hit") || o.textContent?.includes("THREAD"));
    expect(memory.length).toBeGreaterThan(0);
    for (const row of options()) {
      const text = row.textContent ?? "";
      expect(text).not.toContain("**");
      expect(text).not.toContain("[]");
      expect(text).not.toMatch(/\b(th|tm|note|record)_[0-9a-f]{8,}/);
    }
    // The recorded answer holds the answered thread only.
    expect(options().some((o) => o.textContent?.includes("Why the freeze?"))).toBe(true);
    expect(options().some((o) => o.textContent?.includes("When is the freeze?"))).toBe(false);
  });

  it("how a hit was found is plain words: in the transcript, in a note", async () => {
    await search(QUESTION);
    const found = [...document.querySelectorAll(".desk-deck-found")].map((el) => el.textContent);
    expect(found).toEqual(expect.arrayContaining(["in the transcript", "in a note"]));
    expect(document.querySelector(".surface-foundby")).toBeNull();
    for (const word of found) expect(["in the transcript", "in a note", "by meaning"]).toContain(word);
  });

  it("a title that is an id is never a row label", async () => {
    hits = [{ kind: "thread", source_ref: "thread:th_28a810d95cf5", title: "th_28a810d95cf5", snippet: "", retrieval_origin: "relationship" }];
    await search("rollback");
    expect(options().some((o) => /th_28a810d95cf5/.test(o.textContent ?? ""))).toBe(false);
  });
  // A tap on a memory row at 393 is a real touch: tests/e2e/test_desk_search_touch.py (jsdom carries no pointerType).
});

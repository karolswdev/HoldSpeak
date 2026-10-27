/** About in Ask, Betterment Q6 "The About picker": the one picker (the
 * Automations' About uses the same one, Betterment A5).
 *
 * + opens one name field. It finds meetings (also by the people in them),
 * notes, people, projects, decisions and drawers by name, grouped, newest
 * first; before he types it offers the shortcuts: My whole desk, This week's
 * meetings, each person, each project. A pick is a chip; a desk object
 * dropped on the Ask window is a chip. It never lists modes, threads, results
 * or repository roadmaps. People are the hub's recorded answer
 * (fixtures/people-wire/relationships.json, tests/integration/test_desk_chair.py);
 * the Ask answer is ask.thread.wire.json (tests/unit/test_desk_ask.py). */
import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

import { EMPTY_ITEMS } from "../../../api";
import { useDesk } from "../../../store";
import { AskPanel } from "../../AskPanel";
import { clearEngineCache } from "../../../hooks/useEngine";
import { HAND_MIME } from "../../../hand/drag";
import { aboutMatches, type AboutCandidate } from "../AboutPicker";
import PEOPLE from "../../../__tests__/fixtures/people-wire/relationships.json";
import THREAD from "../../../../test/wire/ask.thread.wire.json";

const AVERY = PEOPLE.relationships.find((r) => r.display_name === "Avery Chen")!;
const thisWeek = new Date();
const older = new Date(thisWeek.getTime() - 30 * 24 * 3600 * 1000);

let asked: Array<Record<string, unknown>> = [];
function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  clearEngineCache();
  asked = [];
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    if (method === "GET" && url.startsWith("/api/people/relationships")) return Promise.resolve(reply(PEOPLE));
    if (method === "POST" && url.endsWith("/api/ask")) {
      asked.push(JSON.parse(String(init.body)));
      return Promise.resolve(reply(THREAD.first));
    }
    return Promise.resolve(reply({}));
  }));
  useDesk.setState({
    items: {
      ...EMPTY_ITEMS,
      note: [
        { kind: "note", id: "n-avery", title: "1:1 with Avery", bodyMarkdown: "", tags: [], createdAt: thisWeek.toISOString() },
        { kind: "note", id: "n-old", title: "Avery onboarding plan", bodyMarkdown: "", tags: [], createdAt: older.toISOString() },
      ],
      meeting: [
        { kind: "meeting", id: "m-new", title: "Ledger cutover sync", startedAt: thisWeek.toISOString(), attendees: ["Avery Chen", "Me"] },
        { kind: "meeting", id: "m-old", title: "Hiring loop", startedAt: older.toISOString(), attendees: ["Avery Chen"] },
      ],
      decision: [{ kind: "decision", id: "d1", title: "Freeze the ledger on Nov 5", createdAt: older.toISOString() }],
      directory: [{ kind: "directory", id: "z1", name: "Cutover", memberIds: [] }],
      recipe: [{ kind: "recipe", id: "r1", name: "Avery mode" }],
      thread: [{ kind: "thread", id: "th1", title: "Avery question" }],
      artifact: [{ kind: "artifact", id: "a1", title: "Avery summary" }],
      roadmap: [{ kind: "roadmap", id: "rm1", title: "Avery roadmap" }],
    } as never,
    projects: [{ id: "p1", name: "Ledger migration" }],
    selectedIds: [],
    askOpen: true,
    askThread: null,
    pullouts: [],
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
  } as never);
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

// Ask D1: the scope word ▾ opens the menu; each match is a row with its kind.
const matches = () => screen.queryAllByTestId("about-match").map((m) => (m.querySelector(".desk-menu-label")?.textContent ?? ""));
const matchKinds = () => screen.queryAllByTestId("about-match").map((m) => m.getAttribute("data-kind") ?? "");

async function openPicker() {
  render(<AskPanel />);
  await waitFor(() => expect(vi.mocked(fetch).mock.calls.some(([u]) => String(u).startsWith("/api/people/relationships"))).toBe(true));
  fireEvent.click(screen.getByTestId("ask-context"));
  return screen.getByRole("textbox", { name: "Find a meeting, note, person" });
}

describe("Betterment Q6 + Ask D1: the scope menu in Ask", () => {
  it("before he types: My whole desk, This week's meetings, each person, each project", async () => {
    await openPicker();
    await waitFor(() => expect(matches()).toContain("Avery Chen"));
    expect(screen.getByRole("menuitemradio", { name: /My whole desk/ })).toHaveAttribute("aria-checked", "true");
    const shown = matches();
    expect(shown).toEqual(expect.arrayContaining([
      "This week's meetings",
      ...PEOPLE.relationships.map((p) => p.display_name),
      "Ledger migration",
    ]));
  });

  it("then \"Avery\": Avery, the 1:1 and her meetings, grouped, newest first; never a mode, a thread, a result or a roadmap", async () => {
    const field = await openPicker();
    fireEvent.change(field, { target: { value: "Avery" } });
    await waitFor(() => expect(matches()).toContain("Avery Chen"));
    const shown = matches();
    expect(shown).toEqual(expect.arrayContaining(["Avery Chen", "1:1 with Avery", "Ledger cutover sync", "Hiring loop"]));
    // Grouped: each kind's rows sit together; inside a group, newest first.
    const kinds = matchKinds();
    expect(kinds.filter((k, i) => i === 0 || k !== kinds[i - 1])).toEqual([...new Set(kinds)]);
    expect(shown.indexOf("Ledger cutover sync")).toBeLessThan(shown.indexOf("Hiring loop"));
    expect(shown.indexOf("1:1 with Avery")).toBeLessThan(shown.indexOf("Avery onboarding plan"));
    for (const never of ["Avery mode", "Avery question", "Avery summary", "Avery roadmap"])
      expect(shown.some((m) => m.startsWith(never))).toBe(false);
  });

  it("one pick changes the word; Ask asks with it; ✕ takes it out; My whole desk clears it", async () => {
    const field = await openPicker();
    fireEvent.change(field, { target: { value: "Avery" } });
    await waitFor(() => expect(matches()).toContain("Avery Chen"));
    fireEvent.click(screen.getAllByTestId("about-match").find((m) => m.textContent?.includes("Avery Chen"))!);
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Avery Chen");

    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What does Avery owe?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
    expect(asked[0].context).toEqual([
      { id: AVERY.id, kind: "people", title: "Avery Chen", ref: `people:${AVERY.id}` },
    ]);

    // A second pick replaces the first.
    fireEvent.click(screen.getByTestId("ask-context"));
    fireEvent.change(screen.getByRole("textbox", { name: "Find a meeting, note, person" }), { target: { value: "Ledger cutover" } });
    await waitFor(() => expect(matches()).toContain("Ledger cutover sync"));
    fireEvent.click(screen.getAllByTestId("about-match").find((m) => m.textContent?.includes("Ledger cutover sync"))!);
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Ledger cutover sync");

    fireEvent.click(screen.getByTestId("ask-context"));
    expect(screen.getAllByTestId("ask-about-chip").map((c) => c.textContent)).toEqual(["✓Ledger cutover sync✕"]);
    fireEvent.click(screen.getByRole("button", { name: "Remove Ledger cutover sync" }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("My whole desk");
    fireEvent.click(screen.getByRole("menuitemradio", { name: /My whole desk/ }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("My whole desk");
  });

  it("This week's meetings asks about this week's meetings only", async () => {
    await openPicker();
    await waitFor(() => expect(matches()).toContain("This week's meetings"));
    fireEvent.click(screen.getAllByTestId("about-match").find((m) => m.textContent?.startsWith("This week's meetings"))!);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What changed?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
    expect(asked[0].context).toEqual([{ id: "m-new", kind: "meeting", title: "Ledger cutover sync", ref: "meeting:m-new" }]);
  });

  it("a desk object dropped on the Ask window joins the scope", async () => {
    render(<AskPanel />);
    const body = screen.getByTestId("ask-body");
    const data = { types: [HAND_MIME], getData: (type: string) => (type === HAND_MIME ? "note:n-avery" : ""), dropEffect: "none" };
    fireEvent.dragOver(body, { dataTransfer: data });
    fireEvent.drop(body, { dataTransfer: data });
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Avery");
    fireEvent.click(screen.getByTestId("ask-context"));
    expect(screen.getAllByTestId("ask-about-chip").map((c) => c.textContent)).toEqual(["✓1:1 with Avery✕"]);
  });

  it("matches are grouped by kind (the best match's group first), newest first inside a group", () => {
    const c: AboutCandidate[] = [
      { ref: "meeting:a", kind: "meeting", label: "Avery old", at: "2026-01-01" },
      { ref: "person:x", kind: "person", label: "Avery" },
      { ref: "meeting:b", kind: "meeting", label: "Avery new", at: "2026-10-01" },
      { ref: "note:n", kind: "note", label: "Avery note", at: "2026-05-01" },
    ];
    expect(aboutMatches(c, "avery").map((m) => m.ref)).toEqual(["person:x", "meeting:b", "meeting:a", "note:n"]);
  });
});

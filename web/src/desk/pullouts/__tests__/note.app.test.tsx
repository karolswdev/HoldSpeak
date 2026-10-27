/** The note app, face half (Betterment Q8 "One note").
 *
 * A note is one thing with one window, the sticky. Every note opens there
 * (the hub adopts a plain note on open; no "Develop" press), and its foot is
 * Ask about this, Project ▾, Send… and Done. In Ask opened from a note, Add
 * to note appends the answer to the note, with Undo.
 *
 * The hub half is tests/unit/test_desk_note.py. It records the window's open,
 * its workbench read, and Add to note and Undo on the same note
 * (web/src/test/wire/note.one-note.wire.json; HOLDSPEAK_WIRE_WRITE=1
 * rewrites it). The Ask answer is ask.thread.wire.json's (tests/unit/
 * test_desk_ask.py). Here fetch answers with those recorded answers, and
 * every press is driven to what the window draws. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MemoryRouter } from "react-router-dom";
import { Pullout } from "../../components/Pullout";
import { AskPanel } from "../../components/AskPanel";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { latchAskSelection } from "../../ask";
import { clearEngineCache } from "../../hooks/useEngine";
import { NOTE_GREW_EVENT } from "../../thoughts";
import NOTE from "../../../test/wire/note.one-note.wire.json";
import THREAD from "../../../test/wire/ask.thread.wire.json";

vi.mock("../../../runtime/RuntimeBus", () => {
  const value = { state: "connected", lastFrame: null, subscribe: () => () => undefined };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

type Call = { url: string; method: string; body: Record<string, unknown> | undefined };
let calls: Call[] = [];
const THOUGHT_ID = NOTE.open.thought.id;
const NOTE_REF = `note:${NOTE.note_id}`;

function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

/** The recorded hub: the window's open and read, then Add to note and Undo
 *  (each an open, then the thought write), in the order the hub answered.
 *  `windowOpen` false: the window did not open first (Ask from an icon). */
function recordedHub(windowOpen = true) {
  const opens = [...(windowOpen ? [NOTE.open] : []), NOTE.add.open, NOTE.undo.open];
  const writes = [NOTE.add.answer, NOTE.undo.answer];
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "POST" && url.endsWith("/api/thoughts/open-note")) return Promise.resolve(reply(opens.shift() ?? NOTE.undo.open));
    if (method === "GET" && url.endsWith(`/api/thoughts/${THOUGHT_ID}/workbench`)) return Promise.resolve(reply(NOTE.workbench));
    if (method === "PATCH" && url.endsWith(`/api/thoughts/${THOUGHT_ID}/working`)) return Promise.resolve(reply(writes.shift()));
    if (method === "POST" && url.endsWith("/api/ask")) return Promise.resolve(reply(THREAD.first));
    return Promise.resolve(reply({}));
  }));
}

const noteObject = {
  kind: "note", id: NOTE.note_id, title: NOTE.title,
  ref: { kind: "note", title: NOTE.title, bodyMarkdown: NOTE.open.thought.working_note.body_markdown },
} as never;

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  sessionStorage.clear();
  clearEngineCache();
  latchAskSelection(null);
  calls = [];
  recordedHub();
  useDesk.setState({
    items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: NOTE.note_id, title: NOTE.title, bodyMarkdown: "", tags: [], createdAt: "" }] },
    selectedIds: [], askOpen: false, askThread: null, pullouts: [], projects: [], profiles: [],
    panelRects: {}, panelSaved: [], panelOrder: [],
  });
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("Betterment Q8: every note opens in the one note window", () => {
  it("a plain note opens in the sticky, its text intact, with no Develop press", async () => {
    const { container } = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /></MemoryRouter>);

    await waitFor(() => expect(container.querySelector(".thought-workspace-window")).not.toBeNull());
    expect(calls.find((c) => c.url.endsWith("/api/thoughts/open-note"))).toMatchObject({ method: "POST", body: { note_id: NOTE.note_id } });
    // The note's own words, as the hub keeps them.
    await waitFor(() => expect(container.textContent).toContain("Theo could own the handbook."));
    expect(screen.queryByRole("button", { name: "Develop this thought" })).toBeNull();
    expect(container.querySelector(`[id="pullout:${NOTE_REF}"]`)?.getAttribute("aria-label")).toBe(NOTE.title);

    // The toolbar: Done, Ask about this, Find the tasks (Q9) and Send…
    // (Project ▾ shows when he has a project). No Finish, Resume, Task, Copy
    // or Add a note.
    // Window grammar (2026-10-24): the verbs are the toolbar's, Done first.
    const toolbar = container.querySelector(".thought-note-toolbar .kit-toolbar-verbs") as HTMLElement;
    const verbs = within(toolbar).getAllByRole("button").map((b) => b.textContent);
    expect(verbs).toEqual(["Done", "Ask about this", "Find the tasks", "Send…"]);
    // The open wrote nothing but the open itself.
    expect(calls.filter((c) => c.method !== "GET").map((c) => `${c.method} ${c.url}`)).toEqual(["POST /api/thoughts/open-note"]);
  });

  it("Ask about this opens Ask with the note in About", async () => {
    const { container } = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /></MemoryRouter>);
    await waitFor(() => expect(container.querySelector(".thought-note-toolbar")).not.toBeNull());
    fireEvent.click(screen.getByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(useDesk.getState().askOpen).toBe(true));
    expect(useDesk.getState().askThread?.about).toEqual([{ id: NOTE.note_id, kind: "note", ref: NOTE_REF, title: NOTE.title }]);
  });
});

describe("Betterment Q8: Add to note, in Ask opened from a note", () => {
  async function askFromNote() {
    recordedHub(false);
    act(() => { useDesk.getState().askAbout([{ id: NOTE.note_id, kind: "note", ref: NOTE_REF, title: NOTE.title }]); });
    render(<AskPanel />);
    expect(screen.getByTestId("ask-context")).toHaveTextContent(`About${NOTE.title}`);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What should I do about Jun?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
  }

  it("appends the answer to the note, says where it went, and Undo puts the note back", async () => {
    const grew: string[] = [];
    const onGrew = (event: Event) => grew.push(String((event as CustomEvent<{ noteId: string }>).detail.noteId));
    window.addEventListener(NOTE_GREW_EVENT, onGrew);
    try {
      await askFromNote();
      fireEvent.click(screen.getByRole("button", { name: "Add to note" }));

      const added = await screen.findByTestId("ask-added");
      expect(added).toHaveTextContent(`Added to ${NOTE.title}`);
      const patches = () => calls.filter((c) => c.method === "PATCH");
      expect(patches()).toHaveLength(1);
      // The write is the recorded one: the note's body, a blank line, the answer.
      expect(patches()[0].body).toEqual(NOTE.add.request);
      expect(grew).toEqual([NOTE.note_id]);
      expect(screen.queryByRole("button", { name: "Add to note" })).toBeNull();

      fireEvent.click(within(added).getByRole("button", { name: "Undo" }));
      await waitFor(() => expect(screen.queryByTestId("ask-added")).toBeNull());
      expect(patches()).toHaveLength(2);
      expect(patches()[1].body).toEqual(NOTE.undo.request);
      expect(grew).toEqual([NOTE.note_id, NOTE.note_id]);
      expect(screen.getByRole("button", { name: "Add to note" })).toBeInTheDocument();
    } finally {
      window.removeEventListener(NOTE_GREW_EVENT, onGrew);
    }
  });

  it("an Ask not opened from a note offers no Add to note", async () => {
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What should I do about Jun?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText(THREAD.first.output)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Add to note" })).toBeNull();
  });
});

/* Betterment Q9 "Find the tasks": the hub half is
 * tests/unit/test_desk_note_outcomes.py. It runs the meeting's extraction on
 * the Jun note with a REAL recorded LAN engine reply, and records the reads
 * and presses this window makes (web/src/test/wire/note.find-tasks.wire.json). */
import FIND from "../../../test/wire/note.find-tasks.wire.json";

describe("Betterment Q9: Find the tasks on a note", () => {
  function hubWithFind({ refuse = false } = {}) {
    const opens = [NOTE.open];
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      if (method === "POST" && url.endsWith("/api/thoughts/open-note")) return Promise.resolve(reply(opens[0]));
      if (method === "GET" && url.endsWith(`/api/thoughts/${THOUGHT_ID}/workbench`)) return Promise.resolve(reply(NOTE.workbench));
      if (method === "GET" && url.endsWith("/outcomes")) return Promise.resolve(reply(FIND.before));
      if (method === "POST" && url.endsWith("/outcomes/find")) {
        return Promise.resolve(refuse ? reply(FIND.refused.body, FIND.refused.status) : reply(FIND.found));
      }
      if (method === "POST" && url.endsWith("/confirm")) return Promise.resolve(reply(FIND.confirmed));
      if (method === "POST" && url.endsWith("/edit")) return Promise.resolve(reply(FIND.edited));
      if (method === "POST" && url.endsWith("/dismiss")) return Promise.resolve(reply(FIND.dismissed));
      return Promise.resolve(reply({}));
    }));
  }

  async function openNote() {
    const view = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /></MemoryRouter>);
    await waitFor(() => expect(view.container.querySelector(".thought-note-toolbar")).not.toBeNull());
    await waitFor(() => expect(view.container.textContent).toContain("Theo could own the handbook."));
    return view;
  }

  it("one press shows the meeting's rows: the tasks with owners, and the proposed decision", async () => {
    hubWithFind();
    const { container } = await openNote();
    expect(within(container.querySelector(".thought-note-toolbar .kit-toolbar-verbs") as HTMLElement).getAllByRole("button").map((b) => b.textContent))
      .toEqual(["Done", "Ask about this", "Find the tasks", "Send…"]);
    // The rows stay with the note: the window reads them when it opens.
    expect(calls.some((c) => c.method === "GET" && c.url === `/api/notes/${NOTE.note_id}/outcomes`)).toBe(true);
    expect(screen.queryByTestId("note-outcomes")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    const tasks = await screen.findAllByTestId("note-commitments-row");
    // The note is saved first (nothing unsaved here), then the hub runs the extraction.
    expect(calls.some((c) => c.method === "POST" && c.url === `/api/notes/${NOTE.note_id}/outcomes/find`)).toBe(true);
    expect(tasks.map((row) => row.textContent)).toEqual([
      expect.stringContaining("Pair Jun with Mira on call for the cutover weekend"),
      expect.stringContaining("Write the on-call handbook"),
    ]);
    // Direction A (2026-10-27): the rows are in the margin. The owner is a
    // pill of initials; the owner and date are its hover words.
    expect(screen.getByTestId("note-margin")).toContainElement(tasks[0]);
    expect(tasks[0].querySelector(".note-margin-who")).toHaveTextContent("Me");
    expect(tasks[0].querySelector(".note-margin-who")).toHaveAttribute("title", "Me · no date");
    expect(tasks[1].querySelector(".note-margin-who")).toHaveTextContent("TP");
    expect(tasks[1].querySelector(".note-margin-who")).toHaveAttribute("title", "Theo Park · no date");
    const decisions = screen.getAllByTestId("note-decisions-row");
    expect(decisions.map((row) => row.textContent)).toEqual([expect.stringContaining("Theo owns the on-call handbook")]);
  });

  it("Confirm makes the task with one press; the row says so and loses its Confirm", async () => {
    hubWithFind();
    await openNote();
    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    fireEvent.click(await screen.findByRole("button", { name: "Confirm: Write the on-call handbook" }));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Confirm: Write the on-call handbook" })).toBeNull());
    expect(calls.find((c) => c.url.endsWith("/confirm"))).toMatchObject({
      method: "POST", url: `/api/notes/${NOTE.note_id}/outcomes/${FIND.confirm_row}/confirm`,
    });
    const theo = screen.getAllByTestId("note-commitments-row").find((row) => row.textContent?.includes("Write the on-call handbook"))!;
    expect(theo).toHaveTextContent("Done");
    expect(theo.querySelector(".note-margin-who")).toHaveAttribute("title", "Theo Park · Confirmed");
  });

  it("Edit changes a proposed row's words, owner and date before Confirm (as a meeting's rows)", async () => {
    hubWithFind();
    await openNote();
    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    fireEvent.click(await screen.findByRole("button", { name: "More for Pair Jun with Mira on call for the cutover weekend" }));
    fireEvent.click(await screen.findByRole("menuitem", { name: "Edit" }));
    const editor = await screen.findByTestId("note-outcome-edit");
    fireEvent.change(within(editor).getByRole("textbox", { name: "Task" }), { target: { value: FIND.edit_request.text } });
    fireEvent.change(within(editor).getByRole("textbox", { name: "When?" }), { target: { value: FIND.edit_request.due } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(screen.queryByTestId("note-outcome-edit")).toBeNull());
    expect(calls.find((c) => c.url.endsWith("/edit"))).toMatchObject({
      method: "POST", url: `/api/notes/${NOTE.note_id}/outcomes/${FIND.edit_row}/edit`, body: FIND.edit_request,
    });
    const mine = screen.getAllByTestId("note-commitments-row").find((row) => row.textContent?.includes(FIND.edit_request.text))!;
    expect(mine.querySelector(".note-margin-who")).toHaveAttribute("title", "Me · by Friday");
    expect(screen.getByRole("button", { name: `Confirm: ${FIND.edit_request.text}` })).toBeInTheDocument();
  });

  it("Dismiss takes a proposed row away", async () => {
    hubWithFind();
    await openNote();
    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    fireEvent.click(await screen.findByRole("button", { name: "More for Theo owns the on-call handbook" }));
    fireEvent.click(await screen.findByRole("menuitem", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByText("Theo owns the on-call handbook")).toBeNull());
    expect(calls.find((c) => c.url.endsWith("/dismiss"))).toMatchObject({
      method: "POST", url: `/api/notes/${NOTE.note_id}/outcomes/${FIND.dismiss_row}/dismiss`,
    });
  });

  it("a refusal says why in the hub's words, with Try again", async () => {
    hubWithFind({ refuse: true });
    await openNote();
    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    expect(await screen.findByText(FIND.refused.body.message)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Try again" })).toBeInTheDocument();
    expect(screen.queryByTestId("note-outcomes")).toBeNull();
  });
});

/* Direction A, step 2 (owner pick 2026-10-27, "The page and its margin"):
 * what comes back lands in the note's margin, beside the text; the editor
 * never moves. Ask's answer is ask.thread.wire.json's; the found rows are
 * note.find-tasks.wire.json's (both the hub's own recorded answers). */
import { resetMarginAsks } from "../../thought-workspace/marginAsks";
import { decisionLines, findLine, peopleNamed } from "../../thought-workspace/marginText";

describe("Direction A: the note's margin", () => {
  beforeEach(() => {
    resetMarginAsks();
  });
  afterEach(() => resetMarginAsks());

  it("an Ask about this note lands as a card in the note's margin; Dismiss takes it away", async () => {
    const { container } = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /><AskPanel /></MemoryRouter>);
    await waitFor(() => expect(container.querySelector(".thought-note-toolbar")).not.toBeNull());
    await waitFor(() => expect(container.textContent).toContain("Theo could own the handbook."));
    // Closed: nothing in the margin, the editor takes the whole width.
    expect(screen.queryByTestId("note-margin")).toBeNull();
    expect(container.querySelector(".thought-note-document")).not.toHaveClass("has-margin");

    fireEvent.click(within(container.querySelector(".thought-note-toolbar") as HTMLElement).getByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(screen.getByTestId("ask-context")).toHaveTextContent(`About${NOTE.title}`));
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What should I do about Jun?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));

    const card = await screen.findByTestId("note-margin-ask");
    const margin = screen.getByTestId("note-margin");
    expect(margin).toContainElement(card);
    expect(within(margin).getByText("In the margin")).toBeInTheDocument();
    expect(container.querySelector(".thought-note-document")).toHaveClass("has-margin");
    expect(card).toHaveTextContent("Ask: What should I do about Jun?");
    await waitFor(() => expect(card).toHaveTextContent(THREAD.first.output.slice(0, 40)));
    expect(within(card).getAllByRole("button").map((b) => b.textContent)).toEqual(["Add to note", "Dismiss"]);
    // No band under the toolbar: the old question band left the flow.
    expect(container.querySelector(".thought-note-window > .thought-note-ask")).toBeNull();

    fireEvent.click(within(card).getByRole("button", { name: "Dismiss" }));
    await waitFor(() => expect(screen.queryByTestId("note-margin-ask")).toBeNull());
    expect(screen.queryByTestId("note-margin")).toBeNull();
  });

  it("Add to note in the margin appends the answer through the note's own writer", async () => {
    const { container } = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /><AskPanel /></MemoryRouter>);
    await waitFor(() => expect(container.textContent).toContain("Theo could own the handbook."));
    fireEvent.click(within(container.querySelector(".thought-note-toolbar") as HTMLElement).getByRole("button", { name: "Ask about this" }));
    await waitFor(() => expect(screen.getByTestId("ask-context")).toHaveTextContent(`About${NOTE.title}`));
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What should I do about Jun?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const card = await screen.findByTestId("note-margin-ask");
    await waitFor(() => expect(within(card).getByRole("button", { name: "Add to note" })).toBeEnabled());
    const before = calls.length;
    fireEvent.click(within(card).getByRole("button", { name: "Add to note" }));
    await waitFor(() => expect(screen.queryByTestId("note-margin-ask")).toBeNull());
    const writes = calls.slice(before).filter((c) => c.method === "PATCH");
    expect(writes).toHaveLength(1);
    expect(JSON.stringify(writes[0].body)).toContain(JSON.stringify(THREAD.first.output.slice(0, 30)).slice(1, -1));
  });

  it("Find the tasks puts its rows in the margin, one by one, each with one verb; close is kept for the window", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      if (method === "POST" && url.endsWith("/api/thoughts/open-note")) return Promise.resolve(reply(NOTE.open));
      if (method === "GET" && url.endsWith(`/api/thoughts/${THOUGHT_ID}/workbench`)) return Promise.resolve(reply(NOTE.workbench));
      if (method === "GET" && url.endsWith("/outcomes")) return Promise.resolve(reply(FIND.before));
      if (method === "POST" && url.endsWith("/outcomes/find")) return Promise.resolve(reply(FIND.found));
      return Promise.resolve(reply({}));
    }));
    const view = render(<MemoryRouter><Pullout o={noteObject} pulloutId={NOTE_REF} /></MemoryRouter>);
    await waitFor(() => expect(view.container.textContent).toContain("Theo could own the handbook."));
    fireEvent.click(screen.getByRole("button", { name: "Find the tasks" }));
    const rows = await screen.findAllByTestId("note-commitments-row");
    const margin = screen.getByTestId("note-margin");
    expect(within(margin).getByText("Found in this note")).toBeInTheDocument();
    // The delight: a 120 ms stagger, opacity only (CSS reads --arrive).
    expect(rows.map((row) => row.style.getPropertyValue("--arrive"))).toEqual(["0ms", "120ms"]);
    // One verb at rest; More (Edit, Dismiss) is the row's quiet second key.
    expect(within(rows[0]).getByRole("button", { name: `Confirm: ${FIND.found.rows[0].text}` })).toBeInTheDocument();
    // A row whose words are on a line of the note is tied to it (press goes there).
    const tied = rows.find((row) => row.textContent?.includes("Write the on-call handbook"))!;
    expect(tied).toHaveAttribute("data-tied");
    expect(within(tied).getByRole("button", { name: "Go to: Write the on-call handbook" })).toBeEnabled();
    expect(screen.getAllByTestId("note-decisions-row")).toHaveLength(1);
    // The status bar's right end names the note's relations (a zero is no item).
    const foot = view.container.querySelector(".kit-statusbar-trailing");
    expect(foot).toHaveTextContent("1 decision");

    fireEvent.click(within(margin).getByRole("button", { name: "Close the margin" }));
    expect(screen.queryByTestId("note-margin")).toBeNull();
    expect(Object.keys(localStorage).some((key) => key.startsWith("hs.note-margin.") && localStorage.getItem(key) === "closed")).toBe(true);
    fireEvent.click(screen.getByRole("button", { name: "Show the margin" }));
    expect(screen.getByTestId("note-margin")).toBeInTheDocument();
  });

  it("ties rows to lines by their words, and reads decision lines and people from the text", () => {
    const body = "We move the ledger on Nov 14. @Priya owns the rollback.\n- [ ] Review PR #1482 with Marcus\nDecision: the old ledger stays read-only for 30 days.\n**Decision:** keep the shim\nAsk [Marcus](people:p-marcus) and @Priya.";
    const from = body.indexOf("- [ ] Review");
    const line = { from, to: body.indexOf("\n", from) };
    expect(findLine(body, "Review PR #1482 with Marcus")).toEqual(line);
    expect(findLine(body, "review the PR 1482 with marcus")).toEqual(line);
    expect(findLine(body, "Write the handbook")).toBeNull();
    expect(decisionLines(body).map((line) => line.text)).toEqual(["the old ledger stays read-only for 30 days.", "keep the shim"]);
    expect(peopleNamed(body)).toBe(2);
  });
});

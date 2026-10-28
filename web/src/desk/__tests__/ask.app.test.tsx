/** The Ask window (AskPanel), Betterment Q2 "Ask goes first": the face half.
 *
 * The hub half is tests/integration/test_desk_ask_priority.py. It records the
 * `ask_progress` frame the hub sends when meeting analysis holds the LAN
 * engine 5 s into an Ask, and that Ask's answer
 * (web/src/test/wire/ask.busy.wire.json; HOLDSPEAK_WIRE_WRITE=1 rewrites it).
 * Here the frame is delivered through the runtime bus, as the hub broadcasts
 * it, and fetch answers with the recorded answer. */
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AskBar, AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { ASK_RETURN_EVENT, takeAskReturn } from "../thought-workspace/askReturn";
import { clearEngineCache } from "../hooks/useEngine";
import BUSY from "../../test/wire/ask.busy.wire.json";
import RETRY from "../../test/wire/ask.retry.wire.json";
import THREAD from "../../test/wire/ask.thread.wire.json";
import NOTE_WIRE from "../../test/wire/notes-create.wire.json";
import TOOLS from "../../test/wire/ask.tools.wire.json";
import HOLD from "../../test/wire/ask.hold.wire.json";
import STREAM from "../../test/wire/ask.stream.wire.json";
import NO_ENGINE from "../../test/wire/ask.no-engine.wire.json";
import { verbById } from "../verbRegistry";
import { durableDraftKey } from "../../lib/durableDraft";

const bus = vi.hoisted(() => ({ handlers: new Map<string, Set<(frame: unknown) => void>>() }));
vi.mock("../../runtime/RuntimeBus", () => {
  const value = {
    state: "connected",
    lastFrame: null,
    subscribe: (type: string, handler: (frame: unknown) => void) => {
      const set = bus.handlers.get(type) ?? new Set();
      set.add(handler);
      bus.handlers.set(type, set);
      return () => set.delete(handler);
    },
  };
  return { useRuntimeBus: () => value, useOptionalRuntimeBus: () => value, useRuntimeFrame: () => null };
});

function deliver(type: string, data: unknown) {
  for (const handler of bus.handlers.get(type) ?? []) handler({ type, data });
}

type Call = { url: string; method: string; body: Record<string, unknown> | undefined };
let calls: Call[] = [];
let answerAsk: (() => void) | null = null;

function reply(body: unknown, status = 200): Response {
  return { ok: status < 400, status, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  localStorage.clear();
  clearEngineCache();
  latchAskSelection(null);
  bus.handlers.clear();
  calls = [];
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  // The recorded Ask's identity: the face mints `ask_<uuid without dashes>`.
  vi.spyOn(crypto, "randomUUID").mockReturnValue("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa");
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "POST" && url.endsWith("/api/ask")) {
      // The engine is busy: the answer comes when the test says so.
      return new Promise<Response>((resolve) => { answerAsk = () => resolve(reply(BUSY.answer)); });
    }
    return Promise.resolve(reply({}));
  }));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  answerAsk = null;
});

it("refuses an unsupported repository selection without opening whole Desk Ask or losing selection", () => {
  useDesk.setState({ selectedIds: ["repository:repo-1"], askOpen: false });
  render(<AskBar />);
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(screen.getByRole("status")).toHaveTextContent("Source unsupported");
  expect(useDesk.getState().askOpen).toBe(false);
  expect(useDesk.getState().selectedIds).toEqual(["repository:repo-1"]);
});

it("opens AskBar with its exact supported source and leaves floor selection alone", () => {
  useDesk.setState({
    items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n1", title: "API note", bodyMarkdown: "", tags: [], createdAt: "" }] },
    selectedIds: ["note:n1"], askOpen: false,
  });
  render(<AskBar />);
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(useDesk.getState().askThread?.about?.map((source) => source.ref)).toEqual(["note:n1"]);
  expect(useDesk.getState().selectedIds).toEqual(["note:n1"]);
});

async function askMira() {
  render(<AskPanel />);
  fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "What do I owe Mira this week?" } });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  await waitFor(() => expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/api/ask"))).toBe(true));
}

describe("Betterment Q2: an Ask on a busy engine says so, and offers another engine", () => {
  it("duplicate Enter while pending does not submit or clear a new draft", async () => {
    await askMira();
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "A follow-up typed while waiting" } });
    fireEvent.keyDown(prompt, { key: "Enter" });

    expect(calls.filter((call) => call.method === "POST" && call.url.endsWith("/api/ask"))).toHaveLength(1);
    expect(prompt).toHaveValue("A follow-up typed while waiting");
  });

  it("Shift+Enter and IME Enter keep an unsent draft", () => {
    render(<AskPanel />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "A multiline draft" } });
    fireEvent.keyDown(prompt, { key: "Enter", shiftKey: true });
    fireEvent.keyDown(prompt, { key: "Enter", isComposing: true });

    expect(calls.filter((call) => call.method === "POST" && call.url.endsWith("/api/ask"))).toHaveLength(0);
    expect(prompt).toHaveValue("A multiline draft");
  });

  it("acceptance clears the durable editor while completion keeps a newer draft", async () => {
    await askMira();
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });

    expect(prompt).toHaveValue("");
    expect(localStorage.getItem(durableDraftKey("desk-ask"))).toBeNull();
    expect(screen.getByText("What do I owe Mira this week?")).toBeInTheDocument();

    fireEvent.change(prompt, { target: { value: "Follow up after the answer" } });
    fireEvent.keyDown(prompt, { key: "Enter", isComposing: true });
    expect(calls.filter((call) => call.method === "POST" && call.url.endsWith("/api/ask"))).toHaveLength(1);
    expect(calls.find((call) => call.method === "POST" && call.url.endsWith("/api/ask"))?.body?.lens).toBe("Ask");

    await act(async () => { answerAsk?.(); });
    await screen.findByText(BUSY.answer.output);
    expect(prompt).toHaveValue("Follow up after the answer");
    expect(JSON.parse(localStorage.getItem(durableDraftKey("desk-ask"))!).text).toBe("Follow up after the answer");
  });

  it("the recorded busy frame reads 'Waiting for the LAN engine, busy with meeting analysis' and the answer still lands", async () => {
    await askMira();
    // The Ask goes out under the identity the frame names.
    const sent = calls.find((c) => c.url.endsWith("/api/ask"))!;
    expect(sent.body?.invocation_id).toBe(BUSY.busy.invocation_id);

    act(() => deliver("ask_progress", BUSY.busy));
    const line = await screen.findByTestId("run-line");
    expect(line.textContent).toContain("Waiting for the LAN engine, busy with meeting analysis");
    expect(screen.getByRole("button", { name: "Use Glass Local for this one" })).toBeInTheDocument();

    await act(async () => { answerAsk?.(); });
    expect(await screen.findByText(BUSY.answer.output)).toBeInTheDocument();
    expect(screen.queryByText(/busy with meeting analysis/)).toBeNull();
  });

  it("a frame for another Ask changes nothing here", async () => {
    await askMira();
    act(() => deliver("ask_progress", { ...BUSY.busy, invocation_id: "ask_someone_else" }));
    expect((await screen.findByTestId("run-line")).textContent).not.toContain("Waiting for");
  });

  it("Use … for this one runs this Ask on that engine under a one-run assignment", async () => {
    await askMira();
    act(() => deliver("ask_progress", BUSY.busy));
    vi.mocked(crypto.randomUUID).mockReturnValue("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    fireEvent.click(await screen.findByRole("button", { name: "Use Glass Local for this one" }));

    await waitFor(() => expect(calls.filter((c) => c.url.endsWith("/api/ask"))).toHaveLength(2));
    const next = "ask_" + "b".repeat(32);
    expect(calls.some((c) => c.url === `/api/ask/${BUSY.busy.invocation_id}/cancel` && c.method === "POST")).toBe(true);
    const set = calls.find((c) => c.url.endsWith("/api/inference/assignments/set"))!;
    expect(set.body).toEqual({
      command_id: `ask-elsewhere-${next}`,
      expected_revision: 0,
      scope: { kind: "invocation", invocation_id: next, capability_id: "ask.answer" },
      entries: [{ profile_id: "glass-local", profile_revision: 1 }],
    });
    const asks = calls.filter((c) => c.url.endsWith("/api/ask"));
    expect(asks[1].body?.invocation_id).toBe(next);
    expect(calls.indexOf(set)).toBeLessThan(calls.indexOf(asks[1]));
  });

  it("a second attempt is said: 'Trying again, 1 of N'", async () => {
    await askMira();
    act(() => deliver("ask_progress", RETRY.retry));
    expect((await screen.findByTestId("run-line")).textContent).toContain(`Trying again, 1 of ${RETRY.retry.of}`);
  });
});

/* ── Betterment Q4: one Ask window over a kept thread ─────────────────────
 *
 * The hub half is tests/unit/test_desk_ask.py. It records an Ask about a
 * note, its follow-up, the thread read and the Recent list
 * (web/src/test/wire/ask.thread.wire.json; HOLDSPEAK_WIRE_WRITE=1 rewrites
 * it). Here fetch answers with those recorded answers. */

const TID = THREAD.first.thread_id;
const NOTE_REF = "note:n-mira";

type Deferred<T> = {
  promise: Promise<T>;
  resolve(value: T): void;
  reject(reason?: unknown): void;
};

function deferred<T>(): Deferred<T> {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((done, fail) => {
    resolve = done;
    reject = fail;
  });
  return { promise, resolve, reject };
}

function delayedThreadDetail(id: string, answer: string, aboutTitle: string) {
  return {
    id,
    title: id,
    messages: [
      {
        id: `${id}-question`,
        thread_id: id,
        role: "user",
        parts: [{ kind: "text", text: `Question ${id}`, ordinal: 0 }],
      },
      {
        id: `${id}-answer`,
        thread_id: id,
        role: "assistant",
        parts: [{ kind: "text", text: answer, ordinal: 0 }],
      },
    ],
    refs: [{
      id: `${id}-ref`,
      thread_id: id,
      message_id: `${id}-question`,
      ref_kind: "note",
      ref_id: `${id}-note`,
      frozen_json: { title: aboutTitle },
      origin: "reference",
    }],
  };
}

function recentThreadRows(ids: string[]) {
  return {
    threads: ids.map((id) => ({
      id,
      title: `Thread ${id}`,
      recipe_id: null,
      profile_override: null,
      directory_id: null,
      parent_thread_id: null,
      status_line: null,
      call_mode: 0,
      mode: null,
      token_in: 0,
      token_out: 0,
      created_at: "2026-10-23T00:00:00Z",
      updated_at: "2026-10-23T00:00:00Z",
      last_turn_at: "2026-10-23T00:00:00Z",
    })),
  };
}

function delayedThreadFetch(
  ids: string[],
  reads: Record<string, Deferred<Response> | Deferred<Response>[]>,
) {
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "GET" && url.endsWith("/api/threads")) return Promise.resolve(reply(recentThreadRows(ids)));
    const match = url.match(/\/api\/threads\/([^/]+)$/);
    if (method === "GET" && match && reads[match[1]]) {
      const read = reads[match[1]];
      return Array.isArray(read) ? read.shift()!.promise : read.promise;
    }
    return Promise.resolve(reply({}));
  }));
}

function hubWithThread() {
  let asks = 0;
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "POST" && url.endsWith("/api/ask")) {
      asks += 1;
      return Promise.resolve(reply(asks === 1 ? THREAD.first : THREAD.second));
    }
    if (method === "GET" && url.endsWith("/api/threads")) return Promise.resolve(reply(THREAD.recent));
    if (method === "GET" && url.endsWith(`/api/threads/${TID}`)) return Promise.resolve(reply(THREAD.thread));
    if (method === "POST" && url.endsWith("/api/notes")) return Promise.resolve(reply(NOTE_WIRE.wire, 201));
    return Promise.resolve(reply({}));
  }));
}

function askBox() {
  return screen.getByRole("textbox", { name: "Ask about your work" });
}

// Ask D1: the Recent rail is open at a desk width; its rows are buttons.
async function openRecentThread(id: string) {
  const row = await screen.findByRole("button", { name: new RegExp(`^Thread ${id}\\b`) });
  fireEvent.click(row);
}

async function askText(text: string, answer: string) {
  fireEvent.change(askBox(), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  expect(await screen.findByText(answer)).toBeInTheDocument();
}

describe("Betterment Q4: one Ask window, every Ask kept as a thread", () => {
  beforeEach(() => {
    hubWithThread();
    useDesk.setState({
      items: { ...EMPTY_ITEMS, note: [{ kind: "note", id: "n-mira", title: "1:1 with Mira", bodyMarkdown: "", tags: [], createdAt: "" }] },
      selectedIds: [NOTE_REF], askThread: null,
    });
  });

  it("ask, read, follow up, read the second answer: one window, one thread", async () => {
    render(<AskPanel />);
    // Ask D1: the scope word names what the question is about.
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Mira");
    await askText("What do I owe Mira this week?", THREAD.first.output);

    const first = calls.filter((c) => c.url.endsWith("/api/ask"))[0];
    expect(first.body?.thread).toBe(true);
    // Ask D1: References name the note as an object row that opens it.
    const refs = screen.getByTestId("ask-looked-at");
    expect(refs).toHaveTextContent("References");
    expect(within(refs).getByRole("button", { name: /1:1 with Mira/ })).toBeInTheDocument();
    // The box is a follow-up box now, and starts empty.
    expect(screen.getByPlaceholderText("Ask a follow-up")).toHaveValue("");

    await askText("When should I tell her?", THREAD.second.output);
    const second = calls.filter((c) => c.url.endsWith("/api/ask"))[1];
    expect(second.body?.thread_id).toBe(TID);
    expect(second.body?.thread).toBeUndefined();
    const turns = screen.getAllByTestId("ask-turn");
    expect(turns).toHaveLength(2);
    expect(turns[0]).toHaveTextContent("What do I owe Mira this week?");
    expect(turns[1]).toHaveTextContent("When should I tell her?");
  });

  it("Recent lists the kept asks; a row reopens the thread in the same window", async () => {
    useDesk.setState({ selectedIds: [] });
    render(<AskPanel />);
    const row = await within(await screen.findByTestId("ask-recent")).findByRole("button", { name: /What do I owe Mira this week\?/ });
    fireEvent.click(row);

    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    expect(screen.getByText(THREAD.first.output)).toBeInTheDocument();
    expect(screen.getByText(THREAD.second.output)).toBeInTheDocument();
    // The thread's About comes back with it.
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Mira");
    // The rail stays, with the open ask selected.
    expect(within(screen.getByTestId("ask-recent")).getByRole("button", { name: /What do I owe Mira this week\?/ })).toHaveAttribute("aria-current", "true");
    // A follow-up continues that thread and carries its About.
    await askText("Anything else?", THREAD.first.output);
    const sent = calls.filter((c) => c.url.endsWith("/api/ask")).at(-1)!;
    expect(sent.body?.thread_id).toBe(TID);
    expect((sent.body?.grounding as { refs?: string[] }).refs).toContain(NOTE_REF);
  });

  it("a thread opened anywhere opens in Ask; the Thread window is parked", async () => {
    useDesk.setState({ askOpen: false });
    useDesk.getState().openPullout(`thread:${TID}`);
    expect(useDesk.getState().askOpen).toBe(true);
    expect(useDesk.getState().askThread?.threadId).toBe(TID);
    expect(useDesk.getState().pullouts.some((p) => p.id.startsWith("thread:"))).toBe(false);
    render(<AskPanel />);
    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));

    // Desk ▸ New Thread opens a new Ask, not a thread window.
    verbById("desk.new-thread")!.run({} as never);
    await waitFor(() => expect(screen.queryAllByTestId("ask-turn")).toHaveLength(0));
    expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/api/threads"))).toBe(false);
  });

  it("carries an explicit Project return through a saved thread's source door, then clears it on ordinary thread Open", async () => {
    const projectReturn = { projectId: "project-a", resourceRef: "note:n-mira" as const };
    render(<AskPanel />);
    act(() => useDesk.getState().openPullout(`thread:${TID}`, undefined, { projectReturn }));
    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    const sourceDoor = screen.getAllByTestId("ask-looked-at")[0].querySelector("button")!;
    fireEvent.click(sourceDoor);
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === "note:n-mira")?.projectReturn).toEqual(projectReturn));

    act(() => useDesk.getState().openPullout(`thread:${TID}`));
    await waitFor(() => expect(useDesk.getState().askThread?.navigation?.projectReturn).toBeNull());
    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    fireEvent.click(screen.getAllByTestId("ask-looked-at")[0].querySelector("button")!);
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === "note:n-mira")?.projectReturn).toBeNull());
  });

  it("Save as note makes a note titled by the question, with the answer and what it looked at", async () => {
    render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    fireEvent.click(screen.getByRole("button", { name: "Save as note" }));
    expect(await screen.findByText("Saved to your desk")).toBeInTheDocument();
    const note = calls.find((c) => c.method === "POST" && c.url.endsWith("/api/notes"))!;
    expect(note.body?.title).toBe("What do I owe Mira this week?");
    expect(String(note.body?.body_markdown)).toContain(THREAD.first.output);
    expect(String(note.body?.body_markdown)).toContain("Looked at: [1:1 with Mira](note:n-mira)");
    expect(String(note.body?.body_markdown)).toContain(`From: [Ask thread](thread:${TID})`);
    expect(screen.getByRole("button", { name: "Open note" })).toBeInTheDocument();
    // Keep and Bin are gone.
    expect(screen.queryByRole("button", { name: "Keep" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Bin" })).toBeNull();
  });

  it("owns a Thought source after the floor selection changes and keeps that selection on close", async () => {
    useDesk.setState({ selectedIds: ["note:other"] });
    const source = {
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" },
    };
    latchAskSelection(source);
    useDesk.setState({ pullouts: [{ id: "note:n-mira", origin: null }] });
    render(<AskPanel />);
    useDesk.setState({ selectedIds: [] });
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Mira");
    fireEvent.change(askBox(), { target: { value: "Who owns review?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith("/api/ask"))).toBe(true));
    const sent = calls.find((call) => call.url.endsWith("/api/ask"))!;
    expect(sent.body?.context).toEqual([{ id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }]);
    expect(sent.body?.prompt).toContain("Mira owns review");
    expect(screen.getByRole("button", { name: "Back to note" }).closest("details")).toBeNull();
    const returned: unknown[] = [];
    const onReturn = (event: Event) => returned.push((event as CustomEvent).detail);
    window.addEventListener(ASK_RETURN_EVENT, onReturn);
    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    window.removeEventListener(ASK_RETURN_EVENT, onReturn);
    expect(returned).toEqual([source]);
    useDesk.setState({ selectedIds: ["note:other"] });
    fireEvent.click(screen.getByRole("button", { name: "Close Ask" }));
    expect(useDesk.getState().selectedIds).toEqual(["note:other"]);
  });

  it("reopens a closed Thought window before consuming its captured return", async () => {
    const source = {
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" },
    };
    useDesk.setState({ pullouts: [], selectedIds: ["note:n-mira"] });
    latchAskSelection(source);
    render(<AskPanel />);
    const observed: boolean[] = [];
    const onReturn = () => observed.push(useDesk.getState().pullouts.some((entry) => entry.id === "note:n-mira"));
    window.addEventListener(ASK_RETURN_EVENT, onReturn);
    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    window.removeEventListener(ASK_RETURN_EVENT, onReturn);
    expect(observed).toEqual([false]);
    expect(screen.getByText("Source window closed")).toBeInTheDocument();
    await waitFor(() => expect(useDesk.getState().pullouts.some((entry) => entry.id === "note:n-mira")).toBe(true));
    expect(takeAskReturn(source.windowId, source.noteRef)).toEqual(source);
    expect(takeAskReturn(source.windowId, source.noteRef)).toBeNull();
    expect(useDesk.getState().selectedIds).toEqual(["note:n-mira"]);
  });

  it("keeps Project A through a later Project B open, saved Note, and bare-key source reopen", async () => {
    const fromA = { projectId: "project-a", resourceRef: "note:n-mira" as const };
    const fromB = { projectId: "project-b", resourceRef: "note:n-mira" as const };
    const sourceSnapshot = { ref: "note:n-mira", thought_id: "thought-mira", working_revision: 4, body_sha256: "a".repeat(64) };
    const source = {
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" },
      sourceSnapshot, projectReturn: fromA,
    };
    // A previously opened bare-key window keeps its key, geometry and body.
    // The owner can then explicitly open that same Note from another Project.
    useDesk.getState().openPullout("n-mira", { x: 18, y: 27 }, { projectReturn: fromB });
    expect(useDesk.getState().pullouts[0].sourceRef).toBe("note:n-mira");
    latchAskSelection(source);
    render(<AskPanel />);
    await askText("Who owns review?", THREAD.first.output);
    const sent = calls.find((call) => call.method === "POST" && call.url.endsWith("/api/ask"))!;
    expect(sent.body?.source_snapshot).toEqual(sourceSnapshot);
    expect(sent.body?.context).toEqual([source.source]);
    expect(JSON.stringify(sent.body)).not.toContain("project-a");

    fireEvent.click(screen.getByRole("button", { name: "Save as note" }));
    expect(await screen.findByText("Saved to your desk")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open note" }));
    const savedRef = `note:${NOTE_WIRE.wire.note.id}`;
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === savedRef)?.projectReturn).toEqual(fromA));

    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === "n-mira")).toMatchObject({
      origin: { x: 18, y: 27 }, projectReturn: fromA,
    }));
    expect(takeAskReturn("pullout:n-mira", source.noteRef)).toMatchObject({
      range: source.range, sourceSnapshot, projectReturn: fromA,
    });

    useDesk.getState().closePullout("n-mira");
    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === source.noteRef)?.projectReturn).toEqual(fromA));
    expect(takeAskReturn("pullout:n-mira", source.noteRef)).toBeNull();
    expect(takeAskReturn(`pullout:${source.noteRef}`, source.noteRef)).toMatchObject({
      range: source.range, sourceSnapshot, projectReturn: fromA,
    });

    useDesk.getState().openPullout(source.noteRef);
    expect(useDesk.getState().pullouts.find((row) => row.id === source.noteRef)?.projectReturn).toBeNull();
  });

  it("returns an unconfirmed bare source window to the canonical Note without changing that window", async () => {
    const projectReturn = { projectId: "project-a", resourceRef: "note:n-mira" as const };
    const raw = { id: "n-mira", origin: { x: 18, y: 27 }, projectReturn: null };
    useDesk.setState({ items: EMPTY_ITEMS, pullouts: [raw] });
    latchAskSelection({
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }, projectReturn,
    });
    render(<AskPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === "note:n-mira")?.projectReturn).toEqual(projectReturn));
    expect(useDesk.getState().pullouts.find((row) => row.id === "n-mira")).toBe(raw);
    expect(takeAskReturn("pullout:n-mira", "note:n-mira")).toBeNull();
    expect(takeAskReturn("pullout:note:n-mira", "note:n-mira")?.projectReturn).toEqual(projectReturn);
  });

  it("removes Note inference scope without losing the Project return door", async () => {
    const projectReturn = { projectId: "project-a", resourceRef: "note:n-mira" as const };
    useDesk.setState({ projects: [] });
    latchAskSelection({
      noteRef: "note:n-mira", text: "", body: "Mira owns review",
      range: { from: 5, to: 5, text: "" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" },
      sourceSnapshot: { ref: "note:n-mira", thought_id: "thought-mira", working_revision: 4, body_sha256: "a".repeat(64) }, requestNonce: 1,
      projectReturn,
    });
    render(<AskPanel />);
    act(() => useDesk.getState().askAbout([{ id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }], { handoffNonce: 1 }));
    // Ask D1: the scope menu lists what is chosen, each with its ✕.
    fireEvent.click(screen.getByTestId("ask-context"));
    fireEvent.click(screen.getByRole("button", { name: "Remove 1:1 with Mira" }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("My whole desk");
    expect(screen.getByRole("button", { name: "Return to Project" })).toBeInTheDocument();
    await askText("What needs attention?", THREAD.first.output);
    const sent = calls.find((call) => call.method === "POST" && call.url.endsWith("/api/ask"))!;
    expect(sent.body?.context).toEqual([]);
    expect(sent.body?.source_snapshot).toBeUndefined();
    expect(JSON.stringify(sent.body)).not.toContain("project-a");
  });

  it("keeps a Note handoff only for its exact new Ask, even when an ordinary About names the same Note", async () => {
    const projectReturn = { projectId: "project-a", resourceRef: "note:n-mira" as const };
    const sourceSnapshot = { ref: "note:n-mira", thought_id: "thought-mira", working_revision: 4, body_sha256: "a".repeat(64) };
    const about = [{ id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }];
    latchAskSelection({
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: about[0], sourceSnapshot, projectReturn, requestNonce: 1,
    });
    render(<AskPanel />);
    act(() => useDesk.getState().askAbout(about, { handoffNonce: 1 }));
    expect(screen.getByRole("button", { name: "Back to note" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Return to Project" })).toBeInTheDocument();

    // The floor's ordinary Ask about this has the same ref but no handoff.
    act(() => useDesk.getState().askAbout(about));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Back to note" })).toBeNull());
    expect(screen.queryByRole("button", { name: "Return to Project" })).toBeNull();
    await askText("Who owns review?", THREAD.first.output);
    const sent = calls.find((call) => call.method === "POST" && call.url.endsWith("/api/ask"))!;
    expect(sent.body?.context).toEqual(about);
    expect(sent.body?.source_snapshot).toBeUndefined();
    expect(String(sent.body?.prompt)).not.toContain("Mira owns review");
    expect(JSON.stringify(sent.body)).not.toContain("project-a");
  });

  it("clears only the quote while keeping the owned Note source and Back", async () => {
    const sourceSnapshot = { ref: "note:n-mira", thought_id: "thought-mira", working_revision: 4, body_sha256: "a".repeat(64) };
    latchAskSelection({
      noteRef: "note:n-mira", text: "Mira owns review", body: "Mira owns review",
      range: { from: 0, to: 16, text: "Mira owns review" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" },
      sourceSnapshot,
    });
    render(<AskPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Clear quote" }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Mira");
    expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("Source");
    expect(screen.getByRole("button", { name: "Back to note" }).closest("details")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back to note" }));
    expect(takeAskReturn("pullout:note:n-mira", "note:n-mira")?.range).toEqual({ from: 0, to: 16, text: "Mira owns review" });
    await askText("Who owns review?", THREAD.first.output);
    const sent = calls.find((call) => call.url.endsWith("/api/ask"))!;
    expect(sent.body?.context).toEqual([{ id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }]);
    expect(sent.body?.prompt).toBe("Who owns review?");
    expect(sent.body?.source_snapshot).toEqual(sourceSnapshot);
  });

  it("names a changed pinned source and never offers a same-snapshot retry", async () => {
    const sourceSnapshot = { ref: "note:n-mira", thought_id: "thought-mira", working_revision: 4, body_sha256: "a".repeat(64) };
    latchAskSelection({ noteRef: "note:n-mira", text: "", body: "Current source", range: { from: 6, to: 6, text: "" }, windowId: "pullout:note:n-mira", scrollTop: 24,
      source: { id: "n-mira", kind: "note", title: "1:1 with Mira", ref: "note:n-mira" }, sourceSnapshot });
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      return Promise.resolve(method === "POST" && url.endsWith("/api/ask")
        ? reply({ error: "Selected Note changed. Select it again.", reason: "source_changed" }, 409)
        : reply({}));
    }));
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What changed?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(await screen.findByText("Source changed. Select it again")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Ask again" })).toBeNull();
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    expect(screen.getByRole("button", { name: "Back to note" })).toBeInTheDocument();
    expect(calls.filter((call) => call.url.endsWith("/api/ask"))).toHaveLength(1);
    expect(calls.find((call) => call.url.endsWith("/api/ask"))?.body?.source_snapshot).toEqual(sourceSnapshot);
  });

  it("Forget hides the ask with Undo; Undo brings it back and deletes nothing", async () => {
    render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    // Ask D1: Forget is in the answer's ⋯ menu (Undo keeps it safe).
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    fireEvent.click(screen.getByRole("button", { name: "Forget" }));
    expect(screen.getByText("Forgotten: What do I owe Mira this week?")).toBeInTheDocument();
    expect(screen.queryAllByTestId("ask-turn")).toHaveLength(0);

    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    expect(calls.some((c) => c.method === "DELETE")).toBe(false);
  });

  it("a Forget still deletes the thread when the window closes before Undo", async () => {
    const view = render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    // Ask D1: Forget is in the answer's ⋯ menu (Undo keeps it safe).
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    fireEvent.click(screen.getByRole("button", { name: "Forget" }));
    view.unmount();
    expect(calls.some((c) => c.method === "DELETE" && c.url.endsWith(`/api/threads/${TID}`))).toBe(true);
  });

  it("the window shows no raw id, no host string and no grounding receipt", async () => {
    const { container } = render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    await askText("When should I tell her?", THREAD.second.output);
    const text = container.textContent ?? "";
    expect(text).not.toMatch(/\bth_[0-9a-f]+/);
    expect(text).not.toContain("192.168.1.43");
    expect(text).not.toContain("GROUNDED");
    expect(text).not.toContain("RECEIPT");
  });
});

describe("saved Ask thread reads keep the latest selection authoritative", () => {
  beforeEach(() => {
    useDesk.setState({ selectedIds: [], askThread: null });
  });

  it("keeps B's turns and About when A resolves after B, and follows up on B", async () => {
    const readA = deferred<Response>();
    const readB = deferred<Response>();
    delayedThreadFetch(["A", "B"], { A: readA, B: readB });
    render(<AskPanel />);

    await openRecentThread("A");
    await openRecentThread("B");
    await act(async () => { readB.resolve(reply(delayedThreadDetail("B", "Answer B", "Note B"))); });
    expect(screen.getByText("Answer B")).toBeInTheDocument();
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Note B");

    await act(async () => { readA.resolve(reply(delayedThreadDetail("A", "Answer A", "Note A"))); });
    expect(screen.getByText("Answer B")).toBeInTheDocument();
    expect(screen.queryByText("Answer A")).toBeNull();
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Note B");

    fireEvent.change(askBox(), { target: { value: "A B follow-up" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(calls.some((call) => call.method === "POST" && call.url.endsWith("/api/ask"))).toBe(true));
    const followUp = calls.find((call) => call.method === "POST" && call.url.endsWith("/api/ask"));
    expect(followUp?.body?.thread_id).toBe("B");
  });

  it("does not let A's rejection replace B's loading state", async () => {
    const readA = deferred<Response>();
    const readB = deferred<Response>();
    delayedThreadFetch(["A", "B"], { A: readA, B: readB });
    render(<AskPanel />);
    await openRecentThread("A");
    await openRecentThread("B");

    await act(async () => { readA.reject(new Error("A failed")); });
    expect(screen.getByTestId("run-line")).toHaveTextContent("Opening");
    expect(screen.queryByText("This ask was not read")).toBeNull();

    await act(async () => { readB.resolve(reply(delayedThreadDetail("B", "Answer B", "Note B"))); });
    expect(screen.getByText("Answer B")).toBeInTheDocument();
  });

  it("does not let A's late success replace B's read error", async () => {
    const readA = deferred<Response>();
    const readB = deferred<Response>();
    delayedThreadFetch(["A", "B"], { A: readA, B: readB });
    render(<AskPanel />);
    await openRecentThread("A");
    await openRecentThread("B");

    await act(async () => { readB.reject(new Error("B failed")); });
    expect(await screen.findByText("This ask was not read")).toBeInTheDocument();
    await act(async () => { readA.resolve(reply(delayedThreadDetail("A", "Answer A", "Note A"))); });
    expect(screen.getByText("This ask was not read")).toBeInTheDocument();
    expect(screen.queryByText("Answer A")).toBeNull();
  });

  it("does not let A's late rejection replace B's loaded answer", async () => {
    const readA = deferred<Response>();
    const readB = deferred<Response>();
    delayedThreadFetch(["A", "B"], { A: readA, B: readB });
    render(<AskPanel />);
    await openRecentThread("A");
    await openRecentThread("B");

    await act(async () => { readB.resolve(reply(delayedThreadDetail("B", "Answer B", "Note B"))); });
    await act(async () => { readA.reject(new Error("A failed")); });
    expect(screen.getByText("Answer B")).toBeInTheDocument();
    expect(screen.queryByText("This ask was not read")).toBeNull();
  });

  it("New Thread invalidates a pending saved-thread read", async () => {
    const readA = deferred<Response>();
    delayedThreadFetch(["A"], { A: readA });
    render(<AskPanel />);
    await openRecentThread("A");
    verbById("desk.new-thread")!.run({} as never);
    await act(async () => { readA.resolve(reply(delayedThreadDetail("A", "Answer A", "Note A"))); });
    expect(screen.queryByText("Answer A")).toBeNull();
    expect(screen.queryByTestId("ask-turn")).toBeNull();
  });

  it("closing Ask invalidates a pending saved-thread read", async () => {
    const readA = deferred<Response>();
    delayedThreadFetch(["A"], { A: readA });
    render(<AskPanel />);
    await openRecentThread("A");
    fireEvent.click(screen.getByRole("button", { name: "Close Ask" }));
    await act(async () => { readA.resolve(reply(delayedThreadDetail("A", "Answer A", "Note A"))); });
    expect(screen.queryByText("Answer A")).toBeNull();
    expect(screen.queryByTestId("ask-turn")).toBeNull();
  });

  it("same-id reopen keeps only the latest read", async () => {
    const first = deferred<Response>();
    const second = deferred<Response>();
    delayedThreadFetch(["A"], { A: [first, second] });
    render(<AskPanel />);
    await openRecentThread("A");
    await openRecentThread("A");

    await act(async () => { second.resolve(reply(delayedThreadDetail("A", "Latest A", "Latest note A"))); });
    await act(async () => { first.resolve(reply(delayedThreadDetail("A", "Old A", "Old note A"))); });
    expect(screen.getByText("Latest A")).toBeInTheDocument();
    expect(screen.queryByText("Old A")).toBeNull();
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Latest note A");
  });
});

describe("Betterment Q4: Stop while a question runs", () => {
  it("Stop in the status bar tells the hub, and leaves the question marked stopped with Ask again", async () => {
    await askMira();
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "Keep this while the first answer stops" } });
    // Window grammar: Stop is the status bar's verb while a turn runs; Ask waits.
    expect(screen.getByRole("button", { name: "Ask" })).toBeDisabled();
    // Ask D1: the status bar says what runs, with its seconds.
    expect(screen.getByTestId("ask-status")).toHaveTextContent("Writing the answer");
    fireEvent.click(within(screen.getByTestId("ask-status")).getByRole("button", { name: "Stop" }));
    expect(calls.some((c) => c.method === "POST" && c.url === `/api/ask/${BUSY.busy.invocation_id}/cancel`)).toBe(true);
    const line = await screen.findByTestId("ask-not-answered");
    expect(line.dataset.reason).toBe("stopped");
    expect(line).toHaveTextContent("Stopped");
    expect(within(line).getByRole("button", { name: "Ask again" })).toBeInTheDocument();
    expect(screen.getByTestId("ask-status")).toHaveTextContent("Stopped · your question is kept");
    expect(prompt).toHaveValue("Keep this while the first answer stops");
  });

  it("retry operates on the sent question and keeps a newer draft", async () => {
    let attempts = 0;
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      if (method === "POST" && url.endsWith("/api/ask")) {
        attempts += 1;
        return attempts === 1
          ? Promise.resolve(reply({ error: "No answer", reason: "did_not_answer" }, 503))
          : Promise.resolve(reply(BUSY.answer));
      }
      return Promise.resolve(reply({}));
    }));

    render(<AskPanel />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "The sent question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByRole("button", { name: "Try again" });

    fireEvent.change(prompt, { target: { value: "A draft for after retry" } });
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByText(BUSY.answer.output);
    const askCalls = calls.filter((call) => call.method === "POST" && call.url.endsWith("/api/ask"));
    expect(askCalls).toHaveLength(2);
    expect(askCalls[1].body?.prompt).toBe("The sent question");
    expect(prompt).toHaveValue("A draft for after retry");
  });
});

/* ── Betterment Q7: Ask my whole desk ─────────────────────────────────────
 *
 * The hub half is tests/integration/test_desk_ask_tools.py. Its tool engine
 * replays the LAN engine's real reply (tests/fixtures/ask_tool_turn_lan.json):
 * it reads the 1:1 and adds the task. It records the Ask's answer, the
 * thread read, a Make it a task write and a held call's frame
 * (web/src/test/wire/ask.tools.wire.json, ask.hold.wire.json;
 * HOLDSPEAK_WIRE_WRITE=1 rewrites them). */

const TOOL_TID = TOOLS.answer.thread_id;

function hubWithTools(askAnswer: () => Promise<Response> = () => Promise.resolve(reply(TOOLS.answer))) {
  vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
    const url = String(input);
    const method = String(init.method ?? "GET");
    calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
    if (method === "GET" && url.endsWith("/api/ask/engine")) return Promise.resolve(reply(TOOLS.engine));
    if (method === "GET" && url.endsWith("/api/inference/assignments")) return Promise.resolve(reply(TOOLS.assignments));
    if (method === "POST" && url.endsWith("/api/ask")) return askAnswer();
    if (method === "GET" && url.endsWith("/api/threads")) return Promise.resolve(reply({ threads: [{ id: TOOL_TID, title: "What do I owe Mira this week?" }] }));
    if (method === "GET" && url.endsWith(`/api/threads/${TOOL_TID}`)) return Promise.resolve(reply(TOOLS.thread));
    if (method === "POST" && url.endsWith(`/api/threads/${TOOL_TID}/todo`)) return Promise.resolve(reply(TOOLS.todo));
    if (method === "POST" && url.endsWith("/decide")) return Promise.resolve(reply(HOLD.decided));
    if (method === "PATCH" && url.includes("/api/all-action-items/")) return Promise.resolve(reply({ success: true }));
    return Promise.resolve(reply({}));
  }));
}

async function askTool(text: string) {
  fireEvent.change(askBox(), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Ask" }));
  await screen.findByTestId("ask-turn");
}

describe("Betterment Q7: Ask my whole desk", () => {
  beforeEach(() => {
    useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askThread: null });
  });

  it("the engine line says it can use the desk", async () => {
    hubWithTools();
    render(<AskPanel />);
    // Ask D1: the engine is a dot and its name; what it can do is its hover title.
    const line = await screen.findByTestId("engine-line");
    await waitFor(() => expect(line).toHaveAttribute("title",
      "Can use your desk: reads meetings, people, projects, Jira, GitHub; writes notes and drafts; never sends"));
    expect(line).not.toHaveTextContent("Can use your desk");
  });

  it("the answer shows Looked at (the 1:1) and Wrote (the task, with Undo); Undo sets the task aside", async () => {
    hubWithTools();
    render(<AskPanel />);
    await askTool("What do I owe Mira this week?");
    expect(screen.getByTestId("ask-looked-at")).toHaveTextContent("1:1 with Mira");
    const wrote = screen.getByTestId("ask-wrote");
    const [task] = TOOLS.answer.used.wrote;
    expect(wrote).toHaveTextContent(task.label);
    expect(screen.getByText("Wrote").closest("details")?.textContent).toContain("1 task");
    expect(screen.queryByTestId("ask-prepared")).toBeNull();
    // The agent made the task: Make it a task is not offered twice.
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    expect(screen.queryByRole("button", { name: "Make it a task" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More" }));

    fireEvent.click(screen.getByTestId("ask-wrote-undo"));
    const id = task.ref.slice("action_item:".length);
    await waitFor(() => expect(calls.some((c) => c.method === "PATCH" && c.url === `/api/all-action-items/${id}`)).toBe(true));
    const patch = calls.find((c) => c.method === "PATCH")!;
    expect(patch.body).toEqual({ status: "dismissed" });
    expect(screen.queryByTestId("ask-wrote-undo")).toBeNull();
    expect(screen.getByText("Undone")).toBeInTheDocument();
  });

  it("Make it a task makes the agent's own write and shows it under Wrote", async () => {
    hubWithTools(() => Promise.resolve(reply({ ...TOOLS.answer, used: { looked_at: [], wrote: [], prepared: [] } })));
    render(<AskPanel />);
    await askTool("What do I owe Mira this week?");
    expect(screen.queryByTestId("ask-wrote")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    fireEvent.click(screen.getByRole("button", { name: "Make it a task" }));
    await waitFor(() => expect(screen.getByTestId("ask-wrote")).toBeInTheDocument());
    const todo = calls.find((c) => c.method === "POST" && c.url.endsWith(`/api/threads/${TOOL_TID}/todo`))!;
    expect(String(todo.body?.text)).not.toMatch(/^[#*-]/);
    expect(screen.getByTestId("ask-wrote-undo")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "More" }));
    expect(screen.queryByRole("button", { name: "Make it a task" })).toBeNull();
  });

  it("a reopened thread draws Wrote from the hub's record", async () => {
    hubWithTools();
    render(<AskPanel />);
    fireEvent.click(await within(screen.getByTestId("ask-recent")).findByRole("button", { name: /What do I owe Mira this week\?/ }));
    await screen.findByTestId("ask-wrote");
    expect(screen.getByTestId("ask-wrote")).toHaveTextContent(TOOLS.answer.used.wrote[0].label);
    expect(screen.getByTestId("ask-looked-at")).toHaveTextContent("1:1 with Mira");
  });

  it("a held call waits with Allow once and Deny; Deny goes to the thread's decide", async () => {
    vi.mocked(crypto.randomUUID).mockReturnValue("cccccccc-cccc-cccc-cccc-cccccccccccc");
    let answer: (() => void) | null = null;
    hubWithTools(() => new Promise<Response>((resolve) => { answer = () => resolve(reply(HOLD.answer)); }));
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira this week?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(calls.some((c) => c.url.endsWith("/api/ask"))).toBe(true));
    expect(calls.find((c) => c.url.endsWith("/api/ask"))!.body?.invocation_id).toBe(HOLD.hold.invocation_id);

    act(() => deliver("ask_progress", HOLD.hold));
    const hold = await screen.findByTestId("ask-hold");
    expect(hold).toHaveTextContent(`${HOLD.hold.holds[0].words}?`);
    expect(screen.getByRole("button", { name: "Allow once" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Deny" }));
    await waitFor(() => expect(screen.queryByTestId("ask-hold")).toBeNull());
    const decide = calls.find((c) => c.url.endsWith(`/api/threads/${HOLD.hold.thread_id}/decide`))!;
    expect(decide.body).toEqual({ call_id: HOLD.hold.holds[0].call_id, decision: "deny" });

    await act(async () => { answer?.(); });
    await screen.findByTestId("ask-turn");
    expect(screen.queryByTestId("ask-wrote")).toBeNull();
  });
});

/* ── Ask D1 "The question at the top" (canvas ask-direction-2026-10-27) ──
 *
 * The composer is the toolbar row, the answer is a document with its
 * References as rows that open, a fresh Ask offers questions from this
 * desk, an Ask that did not answer says why in one line with one verb, and
 * the Recent rail folds. The answers are the recorded thread wire
 * (ask.thread.wire.json); the no-engine refusal is the hub's recorded 409
 * (ask.no-engine.wire.json). */
describe("Ask D1: the question at the top", () => {
  beforeEach(() => {
    hubWithThread();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n-mira", title: "1:1 with Mira", bodyMarkdown: "", tags: [], createdAt: "2026-10-24T09:00:00Z" }],
        decision: [{
          kind: "decision", id: "d-freeze", title: "Freeze the old ledger on Nov 5", status: "accepted", deciders: [],
          contextMarkdown: "", decisionMarkdown: "", alternatives: [], consequencesMarkdown: "", tags: ["the ledger cutover"],
          createdAt: "2026-10-27T08:00:00Z",
        }],
      },
      selectedIds: [], askThread: null,
    });
  });

  it("the composer is the toolbar row: rail, scope word, field, mic, engine, Ask", () => {
    render(<AskPanel />);
    const row = screen.getByRole("toolbar", { name: "Ask" });
    expect(within(row).getByRole("button", { name: "Recent" })).toHaveAttribute("aria-pressed", "true");
    expect(within(row).getByTestId("ask-context")).toHaveTextContent("My whole desk");
    expect(within(row).getByRole("textbox", { name: "Ask about your work" })).toBeInTheDocument();
    expect(within(row).getByTestId("engine-line")).toBeInTheDocument();
    expect(within(row).getByRole("button", { name: "Ask" })).toBeDisabled();
    // No New ask in the row: it is the rail's first row.
    expect(within(row).queryByRole("button", { name: /New ask/ })).toBeNull();
    expect(within(screen.getByTestId("ask-recent")).getByRole("button", { name: /New ask/ })).toBeInTheDocument();
  });

  it("an empty Ask offers questions from this desk; a press fills the composer and does not send", () => {
    render(<AskPanel />);
    const empty = screen.getByTestId("ask-empty");
    expect(empty).toHaveTextContent("From your desk now");
    expect(empty.querySelector("img[src*='/64/'], .desk-ask-empty-sprite")).toBeNull();
    const decision = within(empty).getByRole("button", { name: "What did we decide about the ledger cutover?" });
    fireEvent.click(decision);
    expect(askBox()).toHaveValue("What did we decide about the ledger cutover?");
    expect(document.activeElement).toBe(askBox());
    expect(calls.some((c) => c.method === "POST" && c.url.endsWith("/api/ask"))).toBe(false);
    // The status bar says what My whole desk covers (no count of zero).
    expect(screen.getByTestId("ask-status-scope")).toHaveTextContent("My whole desk: 1 decision");
  });

  it("an answer is a document: the question as its heading, References as rows that open their windows", async () => {
    render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    const turn = screen.getByTestId("ask-turn");
    expect(within(turn).getByRole("heading", { name: /What do I owe Mira this week\?/ })).toBeInTheDocument();
    const refs = within(turn).getByTestId("ask-looked-at");
    const row = within(refs).getByRole("button", { name: /1:1 with Mira/ });
    expect(row).toHaveTextContent("Note ·");
    fireEvent.click(row);
    await waitFor(() => expect(useDesk.getState().pullouts.some((p) => p.id === NOTE_REF)).toBe(true));
    // The verbs on the answer.
    for (const name of ["Save as note", "Copy", "Ask again", "Send…", "More"]) {
      expect(within(turn).getByRole("button", { name })).toBeInTheDocument();
    }
  });

  it("a follow-up appends below, and Ask again sends the same question as a new turn", async () => {
    render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    fireEvent.click(within(screen.getByTestId("ask-turn")).getByRole("button", { name: "Ask again" }));
    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    const asks = calls.filter((c) => c.method === "POST" && c.url.endsWith("/api/ask"));
    expect(asks[1].body?.prompt).toBe("What do I owe Mira this week?");
    expect(asks[1].body?.thread_id).toBe(TID);
  });

  it("not answered: one line that says why and the one verb that fixes it; the question is kept", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      return Promise.resolve(method === "POST" && url.endsWith("/api/ask")
        ? reply(NO_ENGINE.refusal, NO_ENGINE.status)
        : reply({}));
    }));
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What needs my attention today?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const line = await screen.findByTestId("ask-not-answered");
    expect(line).toHaveTextContent("No engine answers Ask yet.");
    expect(within(line).getAllByRole("button")).toHaveLength(1);
    expect(within(line).getByRole("button", { name: "Choose engine" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /What needs my attention today\?/ })).toBeInTheDocument();
    expect(screen.getByTestId("ask-status")).toHaveTextContent("Not answered · your question is kept");
    expect(line.closest("[data-testid=run-line]")).toBeNull();
  });

  it("the scope word opens a menu under it; one pick changes the word", async () => {
    useDesk.setState({ projects: [{ id: "p-ledger", name: "Payments ledger cutover" }] as never });
    render(<AskPanel />);
    fireEvent.click(screen.getByTestId("ask-context"));
    const menu = screen.getByTestId("ask-scope-menu");
    expect(within(menu).getByRole("menuitemradio", { name: /My whole desk/ })).toHaveAttribute("aria-checked", "true");
    fireEvent.click(within(menu).getByRole("menuitemradio", { name: /Payments ledger cutover/ }));
    expect(screen.queryByTestId("ask-scope-menu")).toBeNull();
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Payments ledger cutover");
    await askText("What is left before the freeze?", THREAD.first.output);
    const sent = calls.find((c) => c.method === "POST" && c.url.endsWith("/api/ask"))!;
    expect((sent.body?.context as Array<{ ref: string }>).map((c) => c.ref)).toEqual(["project:p-ledger"]);
  });

  it("the rail folds with the row's first button, and the fold is kept", async () => {
    const view = render(<AskPanel />);
    expect(await within(screen.getByTestId("ask-recent")).findByRole("button", { name: /What do I owe Mira this week\?/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Recent" }));
    expect(screen.queryByTestId("ask-recent")).toBeNull();
    expect(screen.getByRole("button", { name: "Recent" })).toHaveAttribute("aria-pressed", "false");
    view.unmount();
    render(<AskPanel />);
    expect(screen.queryByTestId("ask-recent")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Recent" }));
    expect(screen.getByTestId("ask-recent")).toBeInTheDocument();
  });

  it("the rail lists only asks: an interview or a specialist thread is not one", async () => {
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: undefined });
      if (method === "GET" && url.endsWith("/api/threads")) {
        const [row] = THREAD.recent.threads;
        return Promise.resolve(reply({ threads: [
          row,
          { ...row, id: "th_mode", title: "A specialist chat", mode: { id: "m", name: "Reviewer", avatar: "" } },
          { ...row, id: "th_recipe", title: "A recipe run", recipe_id: "recipe-1" },
        ] }));
      }
      return Promise.resolve(reply({}));
    }));
    render(<AskPanel />);
    const rail = screen.getByTestId("ask-recent");
    expect(await within(rail).findByRole("button", { name: /What do I owe Mira this week\?/ })).toBeInTheDocument();
    expect(within(rail).queryByRole("button", { name: /A specialist chat/ })).toBeNull();
    expect(within(rail).queryByRole("button", { name: /A recipe run/ })).toBeNull();
  });
});

/* ── Ask hub gaps (canvas ask-direction-2026-10-27) ───────────────────────
 *
 * The hub half is tests/unit/test_desk_ask.py
 * ::test_an_answer_arrives_as_text_frames_and_a_closed_window_claims_it_back.
 * It records the `ask_text` frames as the engine writes, the run while it
 * writes, the answer with its references' facts and its claims by record, the
 * run once answered and the thread read (web/src/test/wire/ask.stream.wire.json;
 * HOLDSPEAK_WIRE_WRITE=1 rewrites it). */
describe("Ask hub gaps: words arrive, references say their facts, claims are kept, a slow ask comes back", () => {
  const INVOCATION = STREAM.running.runs[0].invocation_id;
  const STREAM_TID = STREAM.answer.thread_id;
  let runsReplies: unknown[] = [];

  function hubWithStream(askAnswer: () => Promise<Response> = () => new Promise<Response>((resolve) => { answerAsk = () => resolve(reply(STREAM.answer)); })) {
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: init.body ? JSON.parse(String(init.body)) : undefined });
      if (method === "POST" && url.endsWith("/api/ask")) return askAnswer();
      if (method === "GET" && url.includes("/api/ask/runs")) return Promise.resolve(reply(runsReplies.length > 1 ? runsReplies.shift() : runsReplies[0] ?? { runs: [] }));
      if (method === "GET" && url.endsWith("/api/threads")) return Promise.resolve(reply({ threads: [] }));
      if (method === "GET" && url.endsWith(`/api/threads/${STREAM_TID}`)) return Promise.resolve(reply(STREAM.thread));
      return Promise.resolve(reply({}));
    }));
  }

  beforeEach(() => {
    runsReplies = [];
    vi.spyOn(crypto, "randomUUID").mockReturnValue("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb");
    useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askThread: null });
  });

  it("the answer's words arrive under the question while the status bar counts with Stop", async () => {
    hubWithStream();
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira, and when is the freeze?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(answerAsk).not.toBeNull());
    expect(screen.getByTestId("run-line")).toHaveTextContent("Reading your desk");
    act(() => deliver("ask_text", STREAM.frames[0]));
    const arriving = screen.getByTestId("ask-arriving");
    expect(arriving).toHaveTextContent("You owe Mira feedback on her cutover design doc, due Friday.");
    expect(screen.queryByTestId("run-line")).toBeNull();
    expect(screen.getByTestId("ask-status")).toHaveTextContent("Writing the answer");
    expect(within(screen.getByTestId("ask-status")).getByRole("button", { name: "Stop" })).toBeInTheDocument();
    // A frame of another ask changes nothing here.
    act(() => deliver("ask_text", { invocation_id: "ask_other", text: "Not this one" }));
    expect(screen.getByTestId("ask-arriving")).not.toHaveTextContent("Not this one");
    await act(async () => { answerAsk?.(); });
    await screen.findByTestId("ask-turn");
    expect(screen.queryByTestId("ask-arriving")).toBeNull();
  });

  it("references say the hub's facts: the decision's state, the note's time", async () => {
    hubWithStream(() => Promise.resolve(reply(STREAM.answer)));
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira, and when is the freeze?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const refs = within(await screen.findByTestId("ask-turn")).getByTestId("ask-looked-at");
    expect(within(refs).getByRole("button", { name: /Freeze the old ledger on Nov 5/ })).toHaveTextContent("Accepted");
    expect(within(refs).getByRole("button", { name: /1:1 with Mira/ })).toHaveTextContent(/Note · /);
  });

  it("'Grounded in 2 records' opens the claims and the record that supports each", async () => {
    hubWithStream(() => Promise.resolve(reply(STREAM.answer)));
    render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira, and when is the freeze?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const turn = await screen.findByTestId("ask-turn");
    const word = within(turn).getByRole("button", { name: "Grounded in 2 records" });
    expect(word).toHaveAttribute("aria-expanded", "false");
    expect(within(turn).queryByTestId("ask-claims")).toBeNull();
    fireEvent.click(word);
    const claims = within(turn).getByTestId("ask-claims");
    const rows = within(claims).getAllByRole("listitem");
    expect(rows).toHaveLength(2);
    expect(rows[0]).toHaveTextContent("You owe Mira feedback on her cutover design doc, due Friday.");
    expect(within(rows[0]).getByRole("button", { name: /1:1 with Mira/ })).toBeInTheDocument();
    expect(within(rows[1]).getByRole("button", { name: /Freeze the old ledger on Nov 5/ })).toBeInTheDocument();
  });

  it("closing the window leaves the ask running; Recent shows it Writing…, and its answer lands", async () => {
    hubWithStream();
    const first = render(<AskPanel />);
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira, and when is the freeze?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(answerAsk).not.toBeNull());
    first.unmount();
    // The hub is not told to stop: only Stop ends a run.
    expect(calls.some((c) => c.url.endsWith("/cancel"))).toBe(false);

    vi.useFakeTimers({ shouldAdvanceTime: true });
    try {
      runsReplies = [STREAM.running, STREAM.answered];
      render(<AskPanel />);
      const rail = screen.getByTestId("ask-recent");
      const row = await within(rail).findByRole("button", { name: /What do I owe Mira, and when is the freeze\?/ });
      expect(row).toHaveTextContent("Writing…");
      fireEvent.click(row);
      expect(screen.getByTestId("ask-arriving")).toHaveTextContent("You owe Mira feedback");
      expect(screen.getByTestId("ask-status")).toHaveTextContent("Writing the answer");
      await act(async () => { await vi.advanceTimersByTimeAsync(2100); });
      // Answered: the thread the hub kept opens here, with its claims kept.
      const turn = await screen.findByTestId("ask-turn");
      expect(turn).toHaveTextContent("We freeze the old ledger on Nov 5");
      expect(within(turn).getByRole("button", { name: "Grounded in 2 records" })).toBeInTheDocument();
      expect(within(turn).getByRole("button", { name: /Freeze the old ledger on Nov 5/ })).toHaveTextContent("Accepted");
      expect(within(screen.getByTestId("ask-recent")).queryByText("Writing…")).toBeNull();
      expect(localStorage.getItem("holdspeak.ask.pending")).toBe("[]");
    } finally {
      vi.useRealTimers();
    }
  });

  it("an ask the hub could not answer reads as the one-line not answered", async () => {
    localStorage.setItem("holdspeak.ask.pending", JSON.stringify([{ invocationId: INVOCATION, question: "What do I owe Mira, and when is the freeze?", threadId: "", startedAt: Date.now() - 5000 }]));
    // The hub was restarted: it does not hold this run.
    runsReplies = [{ runs: [{ invocation_id: INVOCATION, state: "unknown", reason: "did_not_answer" }] }];
    hubWithStream();
    render(<AskPanel />);
    const row = await within(screen.getByTestId("ask-recent")).findByRole("button", { name: /What do I owe Mira/ });
    await waitFor(() => expect(row).toHaveTextContent("Not answered"));
    fireEvent.click(row);
    const line = await screen.findByTestId("ask-not-answered");
    expect(line).toHaveTextContent("The engine did not answer.");
    expect(within(line).getAllByRole("button")).toHaveLength(1);
    expect(within(screen.getByTestId("ask-recent")).queryByRole("button", { name: /What do I owe Mira/ })).toBeNull();
  });
});

/* ── Window pass 2 (WINDOW-ATLAS-2026-10-27, Ask 12) ──────────────────────
 *
 * The prompt never shows a ref; Recent is one row per question; References
 * are one row per record; the toolbar's engine dot says when the engine did
 * not answer; the answered face keeps its status bar. The reference rows
 * below are the hub's own looked_at for one Ask on the desk sweep's seed
 * (the W4-ASK rig, 2026-10-27): a calendar entry and its meeting, a Friday
 * update kept as a workbench item and as its artifact, two kept asks of the
 * same question. */
describe("Window pass 2: Ask says one thing once", () => {
  beforeEach(() => {
    useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askThread: null });
  });

  it("a decision tagged with a ref is asked about by its title, never the ref", () => {
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        decision: [{
          kind: "decision", id: "d-gw", title: "Keep the legacy gateway read-only until March", status: "proposed", deciders: [],
          contextMarkdown: "", decisionMarkdown: "", alternatives: [], consequencesMarkdown: "", tags: ["project:proj-6d2a82a5e2dc"],
          createdAt: "2026-10-27T08:00:00Z",
        }],
      },
    });
    render(<AskPanel />);
    const empty = screen.getByTestId("ask-empty");
    expect(empty).not.toHaveTextContent("project:");
    expect(within(empty).getByRole("button", { name: "What did we decide about “Keep the legacy gateway read-only until March”?" })).toBeInTheDocument();
  });

  it("Recent lists a question asked three times as one row", async () => {
    const [row] = THREAD.recent.threads;
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => {
      const url = String(input);
      const method = String(init.method ?? "GET");
      calls.push({ url, method, body: undefined });
      if (method === "GET" && url.endsWith("/api/threads")) {
        return Promise.resolve(reply({ threads: [
          { ...row, id: "th_3", title: "Is the ledger cutover still on track for Nov 14?" },
          { ...row, id: "th_2", title: "Is the ledger cutover still on track for Nov 14?" },
          { ...row, id: "th_1", title: "Is the ledger cutover  still on track for Nov 14?" },
          row,
        ] }));
      }
      return Promise.resolve(reply({}));
    }));
    render(<AskPanel />);
    const rail = screen.getByTestId("ask-recent");
    expect(await within(rail).findByRole("button", { name: /What do I owe Mira this week\?/ })).toBeInTheDocument();
    expect(within(rail).getAllByRole("button", { name: /Is the ledger cutover/ })).toHaveLength(1);
  });

  it("references that read the same are one row: the one that opens and says the most", async () => {
    const { dedupeReferenceRows } = await import("../components/AskPanel");
    const open = () => {};
    const rows = dedupeReferenceRows([
      { ref: "calendar_event:ce_7fff", title: "Ledger cutover sync", kind: "meeting", meta: "Meeting" },
      { ref: "workbench_item:wbocc_sweep_new", title: "Friday team update, Fri 16 Oct 2026", kind: "note" },
      { ref: "thread:th_fea2620e5be6", title: "Is the ledger cutover still on track for Nov 14?", kind: "thread", meta: "Earlier ask", onOpen: open },
      { ref: "artifact:artifact_sweep_friday", title: "Friday team update, Fri 16 Oct 2026", kind: "note", meta: "New", onOpen: open },
      { ref: "meeting:m-standup", title: "Ledger cutover sync", kind: "meeting", meta: "Meeting · 2h ago", onOpen: open },
      { ref: "thread:th_61f89d3ee5ce", title: "Is the ledger cutover still on track for Nov 14?", kind: "thread", meta: "Earlier ask", onOpen: open },
      { ref: "meeting:m-avery", title: "1:1 Avery", kind: "meeting", meta: "Meeting · 2d ago", onOpen: open },
      { ref: "meeting:m-avery", title: "1:1 Avery", kind: "meeting", meta: "Meeting · 2d ago", onOpen: open },
    ]);
    expect(rows.map((row) => row.ref)).toEqual([
      "meeting:m-standup", "artifact:artifact_sweep_friday", "thread:th_fea2620e5be6", "meeting:m-avery",
    ]);
  });

  it("W6-B (defect 5): a decision cited as Proposed and as Active is one row, the one that opens", async () => {
    const { dedupeReferenceRows } = await import("../components/AskPanel");
    const open = () => {};
    const rows = dedupeReferenceRows([
      { ref: "decision:dd_freeze", title: "Freeze the ledger schema on Nov 12", kind: "decision", meta: "Proposed", lamp: "info", onOpen: open },
      { ref: "decision_record:dr_freeze", title: "Freeze the ledger schema on Nov 12", kind: "decision", meta: "Active", lamp: "ok" },
    ]);
    expect(rows.map((row) => row.ref)).toEqual(["decision:dd_freeze"]);
  });

  it("W6-B (defect 6): an answer never cites an earlier ask", async () => {
    const { citedRefs } = await import("../components/AskPanel");
    expect(citedRefs([
      { ref: "thread:th_fea2620e5be6" }, { ref: "meeting:m-standup" }, { ref: "thread:th_61f89d3ee5ce#msg_1" },
    ]).map((row) => row.ref)).toEqual(["meeting:m-standup"]);
  });

  it("two meetings of one name at different times stay two rows", async () => {
    const { dedupeReferenceRows } = await import("../components/AskPanel");
    const rows = dedupeReferenceRows([
      { ref: "meeting:m-1", title: "Ledger cutover sync", kind: "meeting", meta: "Meeting · 2h ago" },
      { ref: "meeting:m-2", title: "Ledger cutover sync", kind: "meeting", meta: "Meeting · 3d ago" },
    ]);
    expect(rows).toHaveLength(2);
  });

  it("the engine did not answer: the toolbar dot says Not answering and opens Engines; an answer clears it", async () => {
    let attempts = 0;
    hubWithTools(() => {
      attempts += 1;
      return Promise.resolve(attempts === 1 ? reply({ error: "No answer", reason: "did_not_answer" }, 503) : reply(TOOLS.answer));
    });
    render(<AskPanel />);
    const line = await screen.findByTestId("engine-line");
    await waitFor(() => expect(line).toHaveAttribute("data-state", "set"));
    fireEvent.change(askBox(), { target: { value: "What do I owe Mira this week?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const failed = await screen.findByTestId("ask-not-answered");
    expect(line).toHaveAttribute("data-state", "down");
    expect(line).toHaveTextContent("Not answering");
    expect(line.querySelector(".kit-dot, [data-tone]")?.getAttribute("data-tone")).toBe("fail");
    // W6-B (atlas pass 3, defect 7): the line under the question has the same
    // danger tone as the toolbar's lamp (393 drew it amber).
    expect(failed.querySelector(".kit-dot")?.getAttribute("data-tone")).toBe("fail");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await screen.findByTestId("ask-turn");
    expect(line).toHaveAttribute("data-state", "set");
    expect(line).toHaveTextContent("Glass Lan");
  });

  it("an engine whose last check did not reach it reads Not answering before any ask", async () => {
    const assignments = JSON.parse(JSON.stringify(TOOLS.assignments));
    const ask = assignments.task_overrides.find((row: { id: string }) => row.id === "ask.answer");
    // The hub writes `unavailable` when a check does not reach the engine
    // (holdspeak/services/model_profile_service.py, the readiness observation).
    ask.effective.assignment.entries[0].readiness = "unavailable";
    hubWithTools();
    const recorded = vi.mocked(fetch).getMockImplementation()!;
    vi.stubGlobal("fetch", vi.fn((input: string, init: RequestInit = {}) => (
      String(input).endsWith("/api/inference/assignments") && String(init.method ?? "GET") === "GET"
        ? Promise.resolve(reply(assignments))
        : recorded(input, init))));
    render(<AskPanel />);
    const line = await screen.findByTestId("engine-line");
    await waitFor(() => expect(line).toHaveAttribute("data-state", "down"));
  });

  it("the answered face keeps its status bar: Answered and the records it read", async () => {
    hubWithTools();
    render(<AskPanel />);
    await askTool("What do I owe Mira this week?");
    expect(screen.getByTestId("ask-status-answered")).toHaveTextContent(/^Answered · \d+ records?/);
  });

  it("a kept ask opened from Recent keeps its status bar", async () => {
    hubWithTools();
    render(<AskPanel />);
    fireEvent.click(await within(screen.getByTestId("ask-recent")).findByRole("button", { name: /What do I owe Mira this week\?/ }));
    await screen.findByTestId("ask-turn");
    expect(screen.getByTestId("ask-status-answered")).toHaveTextContent(/^Answered/);
  });
});

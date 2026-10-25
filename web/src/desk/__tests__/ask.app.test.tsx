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
  expect(screen.getByRole("status")).toHaveTextContent("SOURCE UNSUPPORTED");
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

async function openRecentThread(id: string) {
  fireEvent.click(screen.getByRole("button", { name: "Recent" }));
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
    expect(screen.getByTestId("ask-context")).toHaveTextContent("About1:1 with Mira");
    await askText("What do I owe Mira this week?", THREAD.first.output);

    const first = calls.filter((c) => c.url.endsWith("/api/ask"))[0];
    expect(first.body?.thread).toBe(true);
    // Looked at names the note, folded, as a link.
    const looked = screen.getByText("Looked at · 1:1 with Mira");
    expect(looked.closest("details")?.open).toBe(false);
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
    fireEvent.click(screen.getByRole("button", { name: "Recent" }));
    const row = await screen.findByRole("button", { name: /What do I owe Mira this week\?/ });
    fireEvent.click(row);

    await waitFor(() => expect(screen.getAllByTestId("ask-turn")).toHaveLength(2));
    expect(screen.getByText(THREAD.first.output)).toBeInTheDocument();
    expect(screen.getByText(THREAD.second.output)).toBeInTheDocument();
    // The thread's About comes back with it.
    expect(screen.getByTestId("ask-context")).toHaveTextContent("1:1 with Mira");
    expect(screen.queryByTestId("ask-recent")).toBeNull();
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
    expect(screen.getByRole("button", { name: "Back to Thought" }).closest("details")).toBeNull();
    const returned: unknown[] = [];
    const onReturn = (event: Event) => returned.push((event as CustomEvent).detail);
    window.addEventListener(ASK_RETURN_EVENT, onReturn);
    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
    window.removeEventListener(ASK_RETURN_EVENT, onReturn);
    expect(observed).toEqual([false]);
    expect(screen.getByText("SOURCE WINDOW CLOSED")).toBeInTheDocument();
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

    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
    await waitFor(() => expect(useDesk.getState().pullouts.find((row) => row.id === "n-mira")).toMatchObject({
      origin: { x: 18, y: 27 }, projectReturn: fromA,
    }));
    expect(takeAskReturn("pullout:n-mira", source.noteRef)).toMatchObject({
      range: source.range, sourceSnapshot, projectReturn: fromA,
    });

    useDesk.getState().closePullout("n-mira");
    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
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
    expect(screen.getByRole("button", { name: "Back to Thought" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Return to Project" })).toBeInTheDocument();

    // The floor's ordinary Ask about this has the same ref but no handoff.
    act(() => useDesk.getState().askAbout(about));
    await waitFor(() => expect(screen.queryByRole("button", { name: "Back to Thought" })).toBeNull());
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
    expect(screen.getByRole("button", { name: "Back to Thought" }).closest("details")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Back to Thought" }));
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
    expect(screen.getByRole("button", { name: "Back to Thought" })).toBeInTheDocument();
    expect(calls.filter((call) => call.url.endsWith("/api/ask"))).toHaveLength(1);
    expect(calls.find((call) => call.url.endsWith("/api/ask"))?.body?.source_snapshot).toEqual(sourceSnapshot);
  });

  it("Forget hides the ask with Undo; Undo brings it back and deletes nothing", async () => {
    render(<AskPanel />);
    await askText("What do I owe Mira this week?", THREAD.first.output);
    // Window grammar: Forget is a toolbar verb (Undo keeps it safe).
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
    // Window grammar: Forget is a toolbar verb (Undo keeps it safe).
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
    expect(screen.getByTestId("ask-status")).toHaveTextContent("Asking…");
    fireEvent.click(within(screen.getByTestId("ask-status")).getByRole("button", { name: "Stop" }));
    expect(calls.some((c) => c.method === "POST" && c.url === `/api/ask/${BUSY.busy.invocation_id}/cancel`)).toBe(true);
    const line = await screen.findByTestId("run-line");
    expect(line.dataset.state).toBe("failure");
    expect(line).toHaveTextContent("Stopped");
    expect(screen.getByRole("button", { name: "Ask again" })).toBeInTheDocument();
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
    const line = await screen.findByTestId("engine-line");
    await waitFor(() => expect(line).toHaveTextContent(
      "Can use your desk: reads meetings, people, projects, Jira, GitHub; writes notes and drafts; never sends"));
    expect(line).not.toHaveTextContent("reads only what is in About");
  });

  it("the answer shows Looked at (the 1:1) and Wrote (the task, with Undo); Undo sets the task aside", async () => {
    hubWithTools();
    render(<AskPanel />);
    await askTool("What do I owe Mira this week?");
    expect(screen.getByText(/Looked at/)).toHaveTextContent("1:1 with Mira");
    const wrote = screen.getByTestId("ask-wrote");
    const [task] = TOOLS.answer.used.wrote;
    expect(wrote).toHaveTextContent(task.label);
    expect(screen.getByText("Wrote").closest("details")?.textContent).toContain("1 task");
    expect(screen.queryByTestId("ask-prepared")).toBeNull();
    // The agent made the task: Make it a task is not offered twice.
    expect(screen.queryByRole("button", { name: "Make it a task" })).toBeNull();

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
    fireEvent.click(screen.getByRole("button", { name: "Make it a task" }));
    await waitFor(() => expect(screen.getByTestId("ask-wrote")).toBeInTheDocument());
    const todo = calls.find((c) => c.method === "POST" && c.url.endsWith(`/api/threads/${TOOL_TID}/todo`))!;
    expect(String(todo.body?.text)).not.toMatch(/^[#*-]/);
    expect(screen.getByTestId("ask-wrote-undo")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Make it a task" })).toBeNull();
  });

  it("a reopened thread draws Wrote from the hub's record", async () => {
    hubWithTools();
    render(<AskPanel />);
    fireEvent.click(screen.getByRole("button", { name: "Recent" }));
    fireEvent.click(await screen.findByRole("button", { name: /What do I owe Mira this week\?/ }));
    await screen.findByTestId("ask-wrote");
    expect(screen.getByTestId("ask-wrote")).toHaveTextContent(TOOLS.answer.used.wrote[0].label);
    expect(screen.getByText(/Looked at/)).toHaveTextContent("1:1 with Mira");
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

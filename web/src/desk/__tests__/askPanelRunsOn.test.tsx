// Phase 17: the live Ask face names its effective engine and sends engine
// setup to the shared Runs on surface.
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { durableDraftKey } from "../../lib/durableDraft";

const shell = vi.hoisted(() => ({ openSurfaceOr: vi.fn() }));
vi.mock("../shell", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../shell")>()),
  openSurfaceOr: shell.openSurfaceOr,
}));

const scope = { kind: "capability", capability_id: "ask.answer" };
const entry = { ordinal: 1, profile_id: "quick", profile_revision: 4, label: "Quick Qwen", boundary: "local", readiness: "ready" };
const editor = {
  schema: "AssignmentEditorProjection@1",
  scope,
  selected_capability: { id: "ask.answer", revision: 8, label: "Ask", group: { id: "thoughts_notes", label: "Thoughts & notes" }, allowed_boundaries: ["local"], fallback_dispositions: [] },
  draft_base_revision: 1,
  configured_assignment: null,
  effective: { status: "assigned", inherited_from: "global", assignment: { id: "a1", revision: 1, scope, entries: [entry], retry_policy_id: null, issues: [] }, repair: null },
  candidates: [],
  retry_policy: { permitted_ids: [], default_id: "retry.standard" },
};

const note = { kind: "note", id: "note-1", title: "Canonical note", bodyMarkdown: "First line\nSelected passage", tags: [], createdAt: "2026-10-13T00:00:00Z" } as any;
const otherNote = { kind: "note", id: "note-2", title: "Other note", bodyMarkdown: "Other body", tags: [], createdAt: "2026-10-13T00:00:00Z" } as any;

function response(body: unknown, ok = true): Response {
  return { ok, status: ok ? 200 : 500, headers: { get: () => "application/json" }, json: () => Promise.resolve(body), text: () => Promise.resolve(JSON.stringify(body)) } as unknown as Response;
}

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

beforeEach(() => {
  Element.prototype.scrollIntoView = () => {};
  shell.openSurfaceOr.mockReset();
  localStorage.clear();
  latchAskSelection(null);
  useDesk.setState({ items: EMPTY_ITEMS, selectedIds: [], askOpen: true, pullouts: [], panelRects: {}, panelSaved: [], panelOrder: [] });
  vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve({
    ok: true,
    status: 200,
    headers: { get: () => "application/json" },
    json: () => Promise.resolve(String(url).includes("/api/inference/assignments/editor") ? editor : {}),
  })));
});

afterEach(() => {
  latchAskSelection(null);
  cleanup();
  vi.unstubAllGlobals();
});

describe("AskPanel's engine line", () => {
  it("Choose engine opens Runs on, never the parked assignment sheet", async () => {
    render(<AskPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Choose engine" }));
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
    expect(screen.queryByRole("button", { name: "Save assignment" })).toBeNull();
  });
});

describe("AskPanel's Note passage handoff", () => {
  it("recovers the question, shows the selected text, and Remove keeps it out of the request", async () => {
    localStorage.setItem(durableDraftKey("desk-ask"), JSON.stringify({ version: 1, text: "Recovered question", updatedAt: "2026-10-13T00:00:00Z" }));
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] }, selectedIds: ["note:note-1"], askOpen: true });
    latchAskSelection({ noteRef: "note:note-1", text: "Selected passage" });
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      requests.push({ url, init });
      return Promise.resolve(response(url.endsWith("/api/inference/assignments/editor") ? editor : {}));
    }));

    render(<AskPanel />);
    const prompt = await screen.findByPlaceholderText("Ask about your work");
    expect(prompt).toHaveValue("Recovered question");
    expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("Selected passage");
    fireEvent.click(screen.getByRole("button", { name: "Remove" }));
    expect(screen.queryByTestId("ask-selected-passage")).toBeNull();

    // Remove clears the module latch as well as this mounted panel; a later
    // ordinary open must not replay the quote.
    cleanup();
    render(<AskPanel />);
    const remountedPrompt = await screen.findByPlaceholderText("Ask about your work");
    expect(remountedPrompt).toHaveValue("Recovered question");
    expect(screen.queryByTestId("ask-selected-passage")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "ASK" }));
    await waitFor(() => expect(requests.some((request) => request.url.endsWith("/api/ask"))).toBe(true));
    const askRequest = requests.find((request) => request.url.endsWith("/api/ask"));
    const payload = JSON.parse(String(askRequest?.init?.body));
    expect(payload.prompt).toBe("Recovered question");
    expect(payload.prompt).not.toContain("Selected text:");
    expect(payload.context).toEqual([expect.objectContaining({ ref: "note:note-1" })]);
  });

  it("sends the exact visible quote with the question and canonical Note context", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] }, selectedIds: ["note:note-1"], askOpen: true });
    latchAskSelection({ noteRef: "note:note-1", text: "Selected passage" });
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      requests.push({ url, init });
      return Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Answer" } : url.endsWith("/api/inference/assignments/editor") ? editor : {}));
    }));

    render(<AskPanel />);
    const prompt = await screen.findByPlaceholderText("Ask about your work");
    fireEvent.change(prompt, { target: { value: "What should I do?" } });
    expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("Selected passage");
    fireEvent.click(screen.getByRole("button", { name: "ASK" }));
    await waitFor(() => expect(requests.some((request) => request.url.endsWith("/api/ask"))).toBe(true));
    const askRequest = requests.find((request) => request.url.endsWith("/api/ask"));
    const payload = JSON.parse(String(askRequest?.init?.body));
    expect(payload.prompt).toBe("What should I do?\n\nSelected text:\n> Selected passage");
    expect(payload.context).toEqual([expect.objectContaining({ id: "note-1", kind: "note", ref: "note:note-1" })]);
  });

  it("pins the first quote for an in-flight run, then uses a new handoff in the next compose", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] }, selectedIds: ["note:note-1"], askOpen: true });
    latchAskSelection({ noteRef: "note:note-1", text: "First quote" });
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    const pending = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      requests.push({ url, init });
      if (url.endsWith("/api/ask")) return pending.promise;
      return Promise.resolve(response(url.endsWith("/api/inference/assignments/editor") ? editor : {}));
    }));

    render(<AskPanel />);
    const prompt = await screen.findByPlaceholderText("Ask about your work");
    fireEvent.change(prompt, { target: { value: "First question" } });
    fireEvent.click(screen.getByRole("button", { name: "ASK" }));
    await waitFor(() => expect(requests.filter((request) => request.url.endsWith("/api/ask"))).toHaveLength(1));
    expect(JSON.parse(String(requests.find((request) => request.url.endsWith("/api/ask"))?.init?.body)).prompt)
      .toBe("First question\n\nSelected text:\n> First quote");

    latchAskSelection({ noteRef: "note:note-1", text: "Second quote" });
    pending.resolve(response({ error: "offline", reason: "did_not_answer" }, false));
    await waitFor(() => expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("Second quote"));
    const sentTurn = [...document.querySelectorAll(".surface-traffic-text")].find((node) => node.textContent?.includes("First question"));
    expect(sentTurn).toHaveTextContent("First question Selected text: > First quote");
  });

  it("drops a handoff whose Note is missing from hydrated context", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [otherNote] }, selectedIds: ["note:note-2"], askOpen: true });
    latchAskSelection({ noteRef: "note:note-1", text: "Wrong source passage" });
    const requests: Array<{ url: string; init?: RequestInit }> = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      requests.push({ url, init });
      return Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Answer" } : url.endsWith("/api/inference/assignments/editor") ? editor : {}));
    }));

    render(<AskPanel />);
    const prompt = await screen.findByPlaceholderText("Ask about your work");
    await waitFor(() => expect(screen.queryByTestId("ask-selected-passage")).toBeNull());
    fireEvent.change(prompt, { target: { value: "Use only the current note" } });
    fireEvent.click(screen.getByRole("button", { name: "ASK" }));
    await waitFor(() => expect(requests.some((request) => request.url.endsWith("/api/ask"))).toBe(true));
    const payload = JSON.parse(String(requests.find((request) => request.url.endsWith("/api/ask"))?.init?.body));
    expect(payload.prompt).toBe("Use only the current note");
    expect(payload.prompt).not.toContain("Wrong source passage");
    expect(payload.context).toEqual([expect.objectContaining({ ref: "note:note-2" })]);
  });
});


describe("daily work: the question leads Ask", () => {
  it("keeps the draft while optional notes fold and states the selected source once", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] }, selectedIds: ["note:note-1"], askOpen: true });
    render(<AskPanel />);
    const prompt = await screen.findByPlaceholderText("Ask about your work");
    fireEvent.change(prompt, { target: { value: "Keep this question" } });
    expect(screen.getByTestId("ask-context")).toHaveTextContent("With:Canonical note");
    expect(screen.queryByText("USES ASSIGNMENT")).toBeNull();
    expect(screen.queryByRole("radiogroup", { name: "Lens" })).toBeNull();
    expect(screen.queryByText(/^Budget /)).toBeNull();
    const notes = screen.getByRole("button", { name: "Add notes" });
    expect(notes).toHaveAttribute("aria-expanded", "false");
    fireEvent.click(notes);
    expect(notes).toHaveAttribute("aria-expanded", "true");
    fireEvent.click(notes);
    expect(prompt).toHaveValue("Keep this question");
  });
});

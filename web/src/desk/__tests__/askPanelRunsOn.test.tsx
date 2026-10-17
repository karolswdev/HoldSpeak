// Phase 17: the live Ask face names its effective engine and sends engine
// setup to the shared Runs on surface.
import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AskPanel } from "../components/AskPanel";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { latchAskSelection } from "../ask";
import { durableDraftKey } from "../../lib/durableDraft";
import { RailsPicker } from "../components/RailsPicker";
import { useMissionControl } from "../missioncontrol";
import type { RailsPick } from "../grounding";
import { clearEngineCache } from "../hooks/useEngine";

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
  clearEngineCache();
  useMissionControl.setState({ repos: [] });
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
  vi.restoreAllMocks();
});

describe("AskPanel's engine line", () => {
  it("Choose engine opens Runs on, never the parked assignment sheet", async () => {
    render(<AskPanel />);
    fireEvent.click(await screen.findByRole("button", { name: "Choose engine" }));
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
    expect(screen.queryByRole("button", { name: "Save assignment" })).toBeNull();
  });
});

describe("AskPanel's grounding receipt", () => {
  it.each([
    { name: "no matches", matched: 0, overflow: 0, refs: [], label: "UNGROUNDED" },
    { name: "all matches overflowed", matched: 3, overflow: 3, refs: ["note:release-checks"], label: "UNGROUNDED" },
    { name: "overflow exceeds matches", matched: 2, overflow: 4, refs: ["note:release-checks"], label: "UNGROUNDED" },
    { name: "positive matches use the receipt denominator", matched: 5, overflow: 2, refs: ["note:release-checks", "note:release-owner"], label: "GROUNDED ON 3 OF 5" },
  ])("$name keeps citations, claims and answer actions", async ({ matched, overflow, refs, label }) => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/ask") ? {
      output: "Release answer",
      grounding: { matched_count: matched, overflow_count: overflow, source_refs: refs },
      grounding_claims: [{ text: "Release timing needs confirmation", label: "partial", flagged: true }],
    } : {}))));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Release checks?" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const receipt = (await screen.findByText(label)).closest<HTMLElement>(".desk-ask-receipt")!;
    expect(receipt).toHaveTextContent("Release timing needs confirmation");
    expect(within(receipt).queryAllByRole("button")).toHaveLength(refs.length);
    for (const ref of refs) expect(screen.getByRole("button", { name: `Note · ${ref.slice(5)}` })).toBeInTheDocument();
    expect(screen.queryByText(/GROUNDED ON 0/)).toBeNull();
    for (const name of ["Copy", "Keep", "Bin"]) expect(screen.getByRole("button", { name })).toBeInTheDocument();
  });

  it("an answer without a grounding receipt has no grounding label", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Context-free answer" } : {}))));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("Context-free answer");
    expect(screen.queryByText(/GROUNDED|UNGROUNDED/)).toBeNull();
  });
});

describe("AskPanel's success receipt", () => {
  it.each([
    [0, "Answered"],
    [499, "Answered"],
    [2600, "Answered in 3 s"],
  ])("%s ms has one footer success status and no zero-second phrase", async (elapsed, label) => {
    let now = 1000;
    vi.spyOn(Date, "now").mockImplementation(() => now);
    const pending = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn((url: string) => url.endsWith("/api/ask") ? pending.promise : Promise.resolve(response({}))));
    const { container } = render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    expect(screen.getByTestId("run-line")).toHaveAttribute("data-state", "running");
    now += elapsed;
    await act(async () => pending.resolve(response({ output: "Receipt answer" })));
    await screen.findByText("Receipt answer");
    expect(screen.getAllByText(label, { exact: true })).toHaveLength(1);
    expect(screen.getByText(label, { exact: true }).closest(".surface-footer")).not.toBeNull();
    expect(container.querySelector('.surface-run-line[data-state="success"]')).toBeNull();
    expect(screen.queryByText(/Answered in 0 s/)).toBeNull();
  });

  it("a routed answer keeps its route receipt in the footer", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/ask") ? {
      output: "Routed answer",
      route: { lamp: "lan", host: "studio.local", model: "Review model", receipt: "receipt-a91f" },
    } : {}))));
    const { container } = render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const receipt = await screen.findByText("LAST TURN · Review model · RECEIPT ··a91f");
    expect(receipt.closest(".surface-footer")).not.toBeNull();
    expect(container.querySelector('.surface-run-line[data-state="success"]')).toBeNull();
    expect(screen.getByText("studio.local · LAN")).toBeInTheDocument();
  });
});

describe("AskPanel's Note passage handoff", () => {
  it.each(["Exact saved passage", ""])("retains an explicit saved Note handoff when the floor drops its selection (quote: %s)", async (text) => {
    const source = { id: "note-1", kind: "note", ref: "note:note-1", title: "Saved window note" };
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [otherNote] }, selectedIds: [source.ref] });
    latchAskSelection({ noteRef: source.ref, text, source });
    const requests: any[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/api/ask")) requests.push(JSON.parse(String(init?.body)));
      return Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Saved source answer" } : {}));
    }));
    render(<AskPanel />);
    act(() => useDesk.setState({ selectedIds: [], items: { ...EMPTY_ITEMS, note: [{ ...otherNote, title: "Refreshed floor note" }] } }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Saved window note");
    if (text) expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent(text);
    else expect(screen.queryByTestId("ask-selected-passage")).toBeNull();
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question from the note" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("Saved source answer");
    expect(requests[0]).toMatchObject({
      prompt: text ? `Question from the note\n\nSelected text:\n> ${text}` : "Question from the note",
      context: [source],
    });
    expect(screen.getByTestId("ask-answer-sources")).toHaveTextContent("Saved window note");
    fireEvent.click(screen.getByRole("button", { name: "Edit question" }));
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Saved window note");
    if (text) {
      fireEvent.click(screen.getByText("Selected text").closest("summary")!);
      await screen.findByRole("button", { name: "Remove" });
      fireEvent.click(screen.getByRole("button", { name: "Remove" }));
      expect(screen.queryByTestId("ask-selected-passage")).toBeNull();
      expect(screen.getByTestId("ask-context")).toHaveTextContent("Saved window note");
    }
  });

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

    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
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
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
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
    expect(screen.getByTestId("ask-context")).toHaveTextContent("Question sources:Canonical note");
    expect(screen.queryByText("USES ASSIGNMENT")).toBeNull();
    expect(screen.queryByRole("radiogroup", { name: "Lens" })).toBeNull();
    expect(screen.queryByText(/^Budget /)).toBeNull();
    expect(screen.queryByText("Ground this ask")).toBeNull();
    expect(screen.getAllByText("Add notes")).toHaveLength(1);
    const notes = screen.getByText("Add notes").closest("details")!;
    expect(notes.open).toBe(false);
    fireEvent.click(notes.querySelector("summary")!);
    await waitFor(() => expect(notes.open).toBe(true));
    expect(notes.querySelector("details")).toBeNull();
    fireEvent.click(notes.querySelector("summary")!);
    expect(prompt).toHaveValue("Keep this question");
  });
});

describe("Ask's sent request", () => {
  it("Retry and Keep use the complete sent snapshot while a newer draft and selection survive", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note, otherNote] }, selectedIds: ["note:note-1"] });
    useMissionControl.setState({ repos: [{ name: "HoldSpeak", status: "live", projects: [{ slug: "desk", currentPhase: null, stories: [] }] }] as any });
    latchAskSelection({ noteRef: "note:note-1", text: "Original quote" });
    const calls: Array<{ url: string; init?: RequestInit }> = [];
    const retried = deferred<Response>();
    let asks = 0;
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      calls.push({ url, init });
      if (url.endsWith("/api/ask")) {
        asks += 1;
        return asks === 1 ? Promise.resolve(response({ reason: "did_not_answer" }, false)) : retried.promise;
      }
      if (url.endsWith("/api/grounding/resolve")) return Promise.resolve(response({ titles: ["Other note"], chars: 200 }));
      if (url.endsWith("/api/missioncontrol/rails/size")) return Promise.resolve(response({ sizes: [{ kind: "roadmap", id: "desk", chars: 120 }] }));
      if (url.endsWith("/api/ask/keep")) return Promise.resolve(response({ artifact_id: "kept-answer" }));
      return Promise.resolve(response({}));
    }));

    render(<AskPanel />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "Original question" } });
    fireEvent.click(screen.getByText("Add notes").closest("summary")!);
    const groundingPick = await screen.findByRole("checkbox", { name: "Other note" });
    fireEvent.click(groundingPick);
    await waitFor(() => expect(groundingPick).toBeChecked());
    fireEvent.click(screen.getByText("Ground on the rails").closest("summary")!);
    const railPick = await screen.findByRole("checkbox", { name: "desk: roadmap" });
    fireEvent.click(railPick);
    await waitFor(() => expect(railPick).toBeChecked());
    expect(screen.queryByText(/Grounded on/)).toBeNull();
    expect(screen.queryByText(/\/.*tok/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const retry = await screen.findByRole("button", { name: "Try again" });
    const first = JSON.parse(String(calls.find((call) => call.url.endsWith("/api/ask"))?.init?.body));
    expect(first).toMatchObject({
      prompt: "Original question\n\nSelected text:\n> Original quote",
      lens: "Summarize",
      context: [{ id: "note-1", kind: "note", ref: "note:note-1", title: "Canonical note" }],
      grounding: { refs: ["note:note-2"], rails: [{ repo: "HoldSpeak", project: "desk", kind: "roadmap", id: "desk" }] },
    });

    fireEvent.change(prompt, { target: { value: "Newer question" } });
    fireEvent.click(groundingPick);
    fireEvent.click(railPick);
    act(() => {
      useDesk.setState({ items: { ...EMPTY_ITEMS, note: [{ ...note, title: "Changed source" }, otherNote] }, selectedIds: ["note:note-2"] });
      latchAskSelection({ noteRef: "note:note-2", text: "Newer quote" });
    });
    expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("Newer quote");
    fireEvent.click(retry);
    await waitFor(() => expect(asks).toBe(2));
    const retriedCall = calls.filter((call) => call.url.endsWith("/api/ask"))[1];
    expect(JSON.parse(String(retriedCall.init?.body))).toEqual(first);
    expect(prompt).toHaveValue("Newer question");
    expect(JSON.parse(localStorage.getItem(durableDraftKey("desk-ask"))!).text).toBe("Newer question");
    await act(async () => { retried.resolve(response({ output: "Original answer" })); });
    fireEvent.click(await screen.findByRole("button", { name: "Keep" }));
    await waitFor(() => expect(calls.some((call) => call.url.endsWith("/api/ask/keep"))).toBe(true));
    const keep = JSON.parse(String(calls.find((call) => call.url.endsWith("/api/ask/keep"))?.init?.body));
    expect(keep).toEqual({
      lens: first.lens,
      prompt: first.prompt,
      output: "Original answer",
      context: [first.context[0], { id: "note-2", kind: "Note", ref: "note:note-2", title: "Other note" }],
    });
    expect(JSON.parse(localStorage.getItem(durableDraftKey("desk-ask"))!).text).toBe("Newer question");
  });

  it("a fresh Ask builds from the edited draft and current selected passage", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note, otherNote] }, selectedIds: ["note:note-1"] });
    const payloads: any[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/api/ask")) {
        payloads.push(JSON.parse(String(init?.body)));
        return Promise.resolve(response({ reason: "did_not_answer" }, false));
      }
      return Promise.resolve(response({}));
    }));
    render(<AskPanel />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "First question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByRole("button", { name: "Try again" });
    fireEvent.change(prompt, { target: { value: "Current question" } });
    act(() => {
      useDesk.setState({ selectedIds: ["note:note-2"] });
      latchAskSelection({ noteRef: "note:note-2", text: "Current quote" });
    });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(payloads).toHaveLength(2));
    expect(payloads[1]).toMatchObject({ prompt: "Current question\n\nSelected text:\n> Current quote", context: [{ ref: "note:note-2" }] });
  });
});

describe("Ask view abandonment", () => {
  it.each(["Close", "Cancel", "Escape"])("%s abandons a pending view; a late answer cannot change the reopened Ask", async (action) => {
    const pending = deferred<Response>();
    const fresh = deferred<Response>();
    const transmissions: RequestInit[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/api/ask")) {
        transmissions.push(init!);
        return transmissions.length === 1 ? pending.promise : fresh.promise;
      }
      return Promise.resolve(response({}));
    }));
    function Host() {
      const open = useDesk((state) => state.askOpen);
      return open ? <AskPanel /> : null;
    }
    render(<Host />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    fireEvent.change(prompt, { target: { value: "Old request" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(transmissions).toHaveLength(1));
    fireEvent.change(prompt, { target: { value: "Newer durable draft" } });
    if (action === "Escape") fireEvent.keyDown(prompt, { key: "Escape" });
    else fireEvent.click(screen.getByRole("button", { name: action === "Close" ? "Close Ask AI" : "Cancel" }));
    await waitFor(() => expect(screen.queryByRole("textbox", { name: "Ask about your work" })).toBeNull());
    expect(transmissions[0].signal?.aborted).toBe(true);
    act(() => useDesk.setState({ askOpen: true }));
    expect(screen.getByRole("textbox", { name: "Ask about your work" })).toHaveValue("Newer durable draft");
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(transmissions).toHaveLength(2));
    await act(async () => { pending.resolve(response({ output: "Late old answer" })); });
    expect(screen.queryByText("Late old answer")).toBeNull();
    expect(screen.getByTestId("run-line")).toHaveAttribute("data-state", "running");
    await act(async () => { fresh.resolve(response({ output: "Fresh answer" })); });
    expect(await screen.findByText("Fresh answer")).toBeInTheDocument();
    expect(screen.queryByText("Late old answer")).toBeNull();
  });
});

describe("Ask's Workbench composition", () => {
  it.each([true, false])("opens a newer Note handoff and keeps it open across an earlier success (already answered: %s)", async (alreadyAnswered) => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note, otherNote] }, selectedIds: ["note:note-1"] });
    const answer = deferred<Response>();
    vi.stubGlobal("fetch", vi.fn((url: string) => url.endsWith("/api/ask") ? answer.promise : Promise.resolve(response({}))));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "First request" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    if (alreadyAnswered) await act(async () => { answer.resolve(response({ output: "First answer" })); });
    act(() => {
      useDesk.setState({ selectedIds: ["note:note-2"] });
      latchAskSelection({ noteRef: "note:note-2", text: "New note passage", source: { id: "note-2", kind: "note", ref: "note:note-2", title: "New saved note" } });
    });
    expect(screen.getByRole("textbox", { name: "Ask about your work" })).toBeInTheDocument();
    if (!alreadyAnswered) await act(async () => { answer.resolve(response({ output: "First answer" })); });
    expect(await screen.findByText("First answer")).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Ask about your work" })).toBeInTheDocument();
    expect(screen.getByTestId("ask-selected-passage")).toHaveTextContent("New note passage");
    expect(screen.getByTestId("ask-context")).toHaveTextContent("New saved note");
    expect(screen.getByTestId("ask-answer-sources")).toHaveTextContent("Canonical note");
    expect(screen.getByRole("button", { name: "Keep" })).toBeEnabled();
  });

  it("keeps the answer's sent sources distinct when the next question selects different material", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note, otherNote] }, selectedIds: ["note:note-1"] });
    const keeps: any[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/api/ask/keep")) {
        keeps.push(JSON.parse(String(init?.body)));
        return Promise.resolve(response({}, false));
      }
      return Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Answer from the first note" } : {}));
    }));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "First note question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("Answer from the first note");
    const answerSources = screen.getByTestId("ask-answer-sources");
    expect(within(answerSources).getByRole("button", { name: "Canonical note" })).toBeInTheDocument();
    expect(screen.queryByTestId("ask-context")).toBeNull();
    expect(screen.getAllByRole("button", { name: "Canonical note" })).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Edit question" }));
    act(() => useDesk.setState({ selectedIds: ["note:note-2"] }));
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Other note question" } });
    const questionSources = screen.getByTestId("ask-context");
    expect(questionSources).toHaveTextContent("Question sources:");
    expect(within(questionSources).getByRole("button", { name: "Other note" })).toBeInTheDocument();
    expect(within(questionSources).queryByRole("button", { name: "Canonical note" })).toBeNull();
    expect(within(answerSources).getByRole("button", { name: "Canonical note" })).toBeInTheDocument();
    expect(within(answerSources).queryByRole("button", { name: "Other note" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Keep" }));
    await screen.findByText("Not kept");
    expect(keeps[0]).toMatchObject({ prompt: "First note question", output: "Answer from the first note", context: [{ ref: "note:note-1", title: "Canonical note" }] });
  });

  it("Edit question retains the answer and Keep snapshot until a new Ask is sent", async () => {
    const requests: any[] = [];
    const nextAnswer = deferred<Response>();
    const kept: any[] = [];
    vi.stubGlobal("fetch", vi.fn((url: string, init?: RequestInit) => {
      if (url.endsWith("/api/ask")) {
        requests.push(JSON.parse(String(init?.body)));
        return requests.length === 1 ? Promise.resolve(response({ output: "First answer" })) : nextAnswer.promise;
      }
      if (url.endsWith("/api/ask/keep")) {
        kept.push(JSON.parse(String(init?.body)));
        return Promise.resolve(response({}, false));
      }
      return Promise.resolve(response({}));
    }));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "First question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("First answer");
    expect(screen.queryByRole("textbox", { name: "Ask about your work" })).toBeNull();
    const reading = screen.getByRole("region", { name: "Ask answer" });
    reading.scrollTop = 120;
    fireEvent.click(screen.getByRole("button", { name: "Edit question" }));
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    expect(prompt).toHaveValue("First question");
    expect(prompt).toHaveFocus();
    fireEvent.change(prompt, { target: { value: "Independent next question" } });
    expect(screen.getByText("First answer")).toBeInTheDocument();
    expect(reading.scrollTop).toBe(120);
    fireEvent.click(screen.getByRole("button", { name: "Keep" }));
    await screen.findByText("Not kept");
    expect(kept[0]).toMatchObject({ prompt: "First question", output: "First answer" });
    expect(prompt).toHaveValue("Independent next question");
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await waitFor(() => expect(requests).toHaveLength(2));
    expect(requests[1]).toMatchObject({ prompt: "Independent next question", context: [] });
    expect(JSON.stringify(requests[1])).not.toContain("First answer");
    expect(screen.queryByText("First answer")).toBeNull();
    await act(async () => { nextAnswer.resolve(response({ output: "Next answer" })); });
    expect(await screen.findByText("Next answer")).toBeInTheDocument();
  });

  it("keeps a picked source named after its picker folds", async () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, note: [note] } });
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/grounding/resolve") ? { titles: ["Canonical note"], chars: 200 } : {}))));
    render(<AskPanel />);
    fireEvent.click(screen.getByText("Add notes").closest("summary")!);
    fireEvent.click(await screen.findByRole("checkbox", { name: "Canonical note" }));
    const sources = await screen.findByTestId("ask-context");
    expect(within(sources).getByRole("button", { name: "Canonical note" })).toBeInTheDocument();
    fireEvent.click(screen.getByText("Add notes").closest("summary")!);
    await waitFor(() => expect(screen.queryByRole("checkbox", { name: "Canonical note" })).toBeNull());
    expect(within(sources).getByRole("button", { name: "Canonical note" })).toBeInTheDocument();
  });

  it("Keep stays pending until accepted and a failed keep can be tried again", async () => {
    const pendingKeep = deferred<Response>();
    let keeps = 0;
    vi.stubGlobal("fetch", vi.fn((url: string) => {
      if (url.endsWith("/api/ask/keep")) {
        keeps += 1;
        return pendingKeep.promise;
      }
      return Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Answer to keep" } : {}));
    }));
    render(<AskPanel />);
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    const keep = await screen.findByRole("button", { name: "Keep" });
    fireEvent.click(keep);
    await waitFor(() => expect(keeps).toBe(1));
    expect(keep).toHaveAttribute("aria-busy", "true");
    expect(keep).toBeDisabled();
    expect(screen.queryByRole("button", { name: "Kept" })).toBeNull();
    await act(async () => { pendingKeep.resolve(response({}, false)); });
    expect(await screen.findByText("Not kept")).toBeInTheDocument();
    expect(keep).toBeEnabled();
    expect(keep).not.toHaveAttribute("aria-busy");
    fireEvent.click(keep);
    await waitFor(() => expect(keeps).toBe(2));
  });

  it("uses the named Pad and gives Copy, Keep and Bin one home each", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/ask") ? { output: "Clear answer" } : {}))));
    render(<AskPanel />);
    const prompt = screen.getByRole("textbox", { name: "Ask about your work" });
    expect(prompt.closest(".gadget-pad")).not.toBeNull();
    fireEvent.change(prompt, { target: { value: "Clear question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByText("Clear answer");
    for (const name of ["Keep", "Bin", "Copy"]) expect(screen.getAllByRole("button", { name })).toHaveLength(1);
    expect(screen.getByRole("button", { name: "Keep" }).closest(".surface-footer")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Bin" }).closest(".surface-footer")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Copy" }).closest(".surface-traffic-turn")).not.toBeNull();
    expect(screen.queryByText(/SESSION|Summarize/)).toBeNull();
  });

  it("shows a no-engine failure and its engine action once", async () => {
    vi.stubGlobal("fetch", vi.fn((url: string) => Promise.resolve(response(url.endsWith("/api/ask") ? { reason: "no_engine" } : {}, !url.endsWith("/api/ask")))));
    render(<AskPanel />);
    await screen.findByRole("button", { name: "Choose engine" });
    fireEvent.change(screen.getByRole("textbox", { name: "Ask about your work" }), { target: { value: "Question" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask" }));
    await screen.findByRole("button", { name: "Choose an engine" });
    expect(screen.getAllByText("No engine for answers")).toHaveLength(1);
    expect(screen.queryByRole("button", { name: "Choose engine" })).toBeNull();
    expect(screen.getAllByRole("button", { name: /Choose.*engine/ })).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Choose an engine" }));
    expect(shell.openSurfaceOr).toHaveBeenCalledWith("configure-runs-on", "/settings", "models");
  });

  it("Rails has one keyboard checkbox per band and no enclosing button", async () => {
    useMissionControl.setState({ repos: [{ name: "HoldSpeak", status: "live", projects: [{ slug: "desk", currentPhase: null, stories: [] }] }] as any });
    const onChange = vi.fn();
    vi.stubGlobal("fetch", vi.fn(() => Promise.resolve(response({ sizes: [{ kind: "roadmap", id: "desk", chars: 120 }] }))));
    function Picker() {
      const [picks, setPicks] = useState<RailsPick[]>([]);
      return <RailsPicker picks={picks} onChange={(next) => { onChange(next); setPicks(next); }} limitTokens={16384} />;
    }
    render(<Picker />);
    fireEvent.click(screen.getByText("Ground on the rails").closest("summary")!);
    const checkbox = await screen.findByRole("checkbox", { name: "desk: roadmap" });
    const band = checkbox.closest(".desk-ground-line")!;
    expect(band.tagName).toBe("DIV");
    expect(checkbox.closest("button")).toBeNull();
    expect(band.querySelectorAll("input, button, [tabindex]")).toHaveLength(1);
    checkbox.focus();
    await userEvent.keyboard("[Space]");
    await waitFor(() => expect(checkbox).toBeChecked());
    expect(onChange).toHaveBeenCalledTimes(1);
    fireEvent.click(band.querySelector(".desk-ground-name")!);
    expect(checkbox).not.toBeChecked();
    expect(onChange).toHaveBeenCalledTimes(2);
  });
});

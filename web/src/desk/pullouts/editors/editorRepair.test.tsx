import { act, cleanup, fireEvent, render, renderHook, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";
import { keepDraft } from "../../deskMemory";
import { clearWriteFailure, reportWriteFailure } from "../../hooks/useWriteReceipt";
import { ApiError, apiFetch } from "../../../lib/api";
import { editorDraftKey, keptEditorPatch } from "./editorDraft";
import { useDebouncedSave, useEditorSession } from "./useDebouncedSave";
import { KbEditor } from "./KbEditor";
import { WorkflowEditor } from "./WorkflowEditor";
import { RecipeEditor } from "./RecipeEditor";

vi.mock("../../../lib/api", async (original) => ({ ...(await original<typeof import("../../../lib/api")>()), apiFetch: vi.fn() }));

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}

const note = { kind: "note", id: "repair-note", title: "Saved note", bodyMarkdown: "Saved material", tags: [] } as const;
const kb = { kind: "kb", id: "repair-kb", name: "Review context", memberIds: [], createdAt: "now" } as const;
const kbObject = { kind: "kb", id: kb.id, title: kb.name, ref: kb } as any;

function NoteHost({ close }: { close: () => void }) {
  const session = useEditorSession(close);
  const writer = useDebouncedSave("note", note.id, session.onWriter);
  return <><input aria-label="Body" onChange={(event) => writer({ body_markdown: event.target.value })} />{session.receipt}{session.verbs}</>;
}
function KnowledgeHost({ close = vi.fn() }: { close?: () => void }) {
  const session = useEditorSession(close);
  return <><KbEditor object={kbObject} onClose={() => void session.done()} onWriter={session.onWriter} />{session.receipt}{session.verbs}</>;
}
const recipe = { kind: "recipe", id: "review-agent", name: "Review agent", role: "Architect", systemPrompt: "Review the design", userTemplate: "Assess {input}", avatar: "A", tools: ["desk.list"], kbId: kb.id } as const;
function RecipeHost({ close }: { close: () => void }) {
  const session = useEditorSession(close);
  return <><RecipeEditor object={{ kind: "recipe", id: recipe.id, title: recipe.name, ref: recipe } as any} onClose={() => void session.done()} onWriter={session.onWriter} />{session.receipt}{session.verbs}</>;
}

beforeEach(() => {
  vi.useFakeTimers();
  clearWriteFailure();
  useDesk.setState({ drafts: {}, keptAt: { [note.id]: 123 }, refresh: vi.fn(async () => undefined), updatePrimitive: vi.fn(async () => true),
    items: { ...useDesk.getState().items, note: [note], kb: [kb], recipe: [], workflow: [], meeting: [], artifact: [], decision: [], chain: [], directory: [], coder: [], thread: [], repository: [], roadmap: [], story: [], project: [] } as any });
  vi.mocked(apiFetch).mockReset();
  vi.mocked(apiFetch).mockImplementation(async () => ({ members: [] }) as any);
});
afterEach(() => { cleanup(); vi.useRealTimers(); });

describe("editor repair save authority", () => {
  it("publishes a callable writer as state without invoking it, and Done waits for the current write", async () => {
    const pending = deferred<boolean>();
    const update = vi.fn(() => pending.promise);
    useDesk.setState({ updatePrimitive: update });
    const close = vi.fn();
    render(<NoteHost close={close} />);
    expect(update).not.toHaveBeenCalled();
    expect(keptEditorPatch("note", note.id)).toEqual({});
    expect(screen.queryByText(/Saved/)).not.toBeInTheDocument(); // the old keptAt is not this revision
    fireEvent.change(screen.getByRole("textbox", { name: "Body" }), { target: { value: "New revision" } });
    fireEvent.click(screen.getByRole("button", { name: "Done" }));
    expect(update).toHaveBeenCalledWith("note", note.id, { body_markdown: "New revision" });
    expect(close).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("Saving");
    await act(async () => { pending.resolve(true); });
    expect(close).toHaveBeenCalledTimes(1);
    expect(keptEditorPatch("note", note.id)).toEqual({});
  });

  it("refuses Done on failure, preserves the draft and retries the same current revision", async () => {
    const update = vi.fn().mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    useDesk.setState({ updatePrimitive: update });
    const close = vi.fn();
    render(<NoteHost close={close} />);
    fireEvent.change(screen.getByRole("textbox", { name: "Body" }), { target: { value: "Keep these words" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Done" })); });
    expect(close).not.toHaveBeenCalled();
    expect(screen.getByRole("status")).toHaveTextContent("Not saved");
    expect(keptEditorPatch("note", note.id)).toEqual({ body_markdown: "Keep these words" });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Retry" })); });
    expect(update).toHaveBeenNthCalledWith(2, "note", note.id, { body_markdown: "Keep these words" });
    expect(keptEditorPatch("note", note.id)).toEqual({});
    expect(close).not.toHaveBeenCalled();
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Done" })); });
    expect(close).toHaveBeenCalledTimes(1);
  });

  it("keeps a newer field value while an older write lands and serializes the next write", async () => {
    const first = deferred<boolean>();
    const second = deferred<boolean>();
    const update = vi.fn().mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    useDesk.setState({ updatePrimitive: update });
    const hook = renderHook(() => useDebouncedSave("note", note.id));
    act(() => hook.result.current({ body_markdown: "Old words" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    act(() => hook.result.current({ body_markdown: "New words" }));
    await act(async () => { first.resolve(true); });
    expect(update).toHaveBeenCalledTimes(2);
    expect(keptEditorPatch("note", note.id)).toEqual({ body_markdown: "New words" });
    await act(async () => { second.resolve(true); });
    expect(keptEditorPatch("note", note.id)).toEqual({});
  });

  it("an accepted newer value supersedes a refused value of the same field", async () => {
    const update = vi.fn().mockResolvedValueOnce(false).mockResolvedValueOnce(true);
    useDesk.setState({ updatePrimitive: update });
    const hook = renderHook(() => useDebouncedSave("note", note.id));
    act(() => hook.result.current({ title: "Refused title" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    act(() => hook.result.current({ title: "Corrected title" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(keptEditorPatch("note", note.id)).toEqual({});
    expect(hook.result.current.state).toBe("saved");
  });

  it("keeps the named cause for canonical Knowledge identity", async () => {
    useDesk.setState({ updatePrimitive: vi.fn(async () => {
      reportWriteFailure("SAVE", { status: 503 }, undefined, "knowledge:" + kb.id);
      return false;
    }) });
    const hook = renderHook(() => useDebouncedSave("kb", kb.id));
    act(() => hook.result.current({ name: "Unsaved context" }));
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(hook.result.current.reason).toBe("HTTP 503");
  });
});

describe("Knowledge and Workflow editors", () => {
  it("Knowledge has no body authoring and adds a real saved Note through the membership route", async () => {
    useDesk.setState({ items: { ...useDesk.getState().items, roadmap: [{ kind: "roadmap", id: "roadmap-1", title: "Architecture roadmap", name: "Architecture roadmap" }] } as any });
    render(<KnowledgeHost />);
    await act(async () => undefined);
    expect(screen.queryByRole("textbox", { name: "Body" })).not.toBeInTheDocument();
    expect(document.querySelector(".cm-content")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Add items" }));
    expect(screen.getByText("Roadmap")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Find items" }), { target: { value: "Saved note" } });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Add" })); });
    expect(apiFetch).toHaveBeenCalledWith("/api/kbs/repair-kb/members/note%3Arepair-note", { method: "PUT" });
    expect(screen.getByRole("button", { name: "Remove" })).toBeInTheDocument();
  });

  it("keeps unsupported Knowledge text across name saves and recovers it once after a partial failure", async () => {
    keepDraft(editorDraftKey("kb", kb.id), JSON.stringify({ body_markdown: "Recovered architecture text" }));
    let filing = 0;
    vi.mocked(apiFetch).mockImplementation(async (path, init) => {
      if (path === "/api/notes") return { note: { id: "recovered-note" } } as any;
      if (init?.method === "PUT" && ++filing === 1) throw new ApiError(503, "Filing unavailable", {});
      return { members: [] } as any;
    });
    render(<KnowledgeHost />);
    await act(async () => undefined);
    fireEvent.change(screen.getByRole("textbox", { name: "Knowledge name" }), { target: { value: "Updated context" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(useDesk.getState().updatePrimitive).toHaveBeenCalledWith("kb", kb.id, { name: "Updated context" });
    expect(keptEditorPatch("kb", kb.id)).toEqual({ body_markdown: "Recovered architecture text" });
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Save as Note" })); });
    expect(keptEditorPatch("kb", kb.id)).toEqual({ body_markdown: "Recovered architecture text", recovery_note_id: "recovered-note" });
    expect(screen.getByRole("status")).toHaveTextContent("Not saved");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Retry" })); });
    expect(vi.mocked(apiFetch).mock.calls.filter(([path]) => path === "/api/notes")).toHaveLength(1);
    expect(keptEditorPatch("kb", kb.id)).toEqual({});
    expect(screen.queryByRole("button", { name: "Save as Note" })).not.toBeInTheDocument();
  });

  it("edits a prompt-only Workflow through its existing prompt field", async () => {
    const object = { kind: "workflow", id: "prompt-flow", title: "Prompt review", ref: { kind: "workflow", id: "prompt-flow", name: "Prompt review", prompt: "Old prompt", graphJson: {} } } as any;
    render(<WorkflowEditor object={object} onClose={vi.fn()} />);
    fireEvent.change(screen.getByRole("textbox", { name: "Prompt" }), { target: { value: "Review the design risks\n{input}" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(useDesk.getState().updatePrimitive).toHaveBeenCalledWith("workflow", "prompt-flow", { prompt: "Review the design risks\n{input}" });
    expect(screen.queryByText(/iPad/)).not.toBeInTheDocument();
  });

  it("keeps a branching graph intact while its name is edited", async () => {
    const graph = { entry: "entry", nodes: [{ id: "entry", kind: { entry: {} } }], exec_edges: [{ from: { node: "entry" }, to: "a" }, { from: { node: "entry" }, to: "b" }], data_edges: [] };
    const object = { kind: "workflow", id: "branch-flow", title: "Branch review", ref: { kind: "workflow", id: "branch-flow", name: "Branch review", graphJson: graph } } as any;
    render(<WorkflowEditor object={object} onClose={vi.fn()} />);
    expect(screen.getByText("Graph editing · iPad")).toBeInTheDocument();
    fireEvent.change(screen.getByRole("textbox", { name: "Workflow name" }), { target: { value: "Renamed branch review" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(450); });
    expect(useDesk.getState().updatePrimitive).toHaveBeenCalledWith("workflow", "branch-flow", { name: "Renamed branch review" });
    expect(object.ref.graphJson).toEqual(graph);
  });
});

describe("Recipe editor control sheet", () => {
  it("names populated values, folds advanced fields both ways and preserves its writer", async () => {
    const close = vi.fn();
    const update = vi.fn(async () => true);
    useDesk.setState({ updatePrimitive: update, items: { ...useDesk.getState().items, recipe: [recipe] } as any });
    render(<RecipeHost close={close} />);
    for (const name of ["Name", "Role", "Instructions"]) expect(screen.getByText(name)).toBeVisible();
    expect(screen.getByRole("textbox", { name: "Instructions" })).toHaveValue("Review the design");
    const advanced = screen.getByText("Advanced").closest("details")!;
    expect(advanced).not.toHaveAttribute("open");
    fireEvent.click(advanced.querySelector("summary")!);
    for (const name of ["Avatar", "User template", "Tools", "Knowledge"]) expect(screen.getByText(name)).toBeVisible();
    fireEvent.change(screen.getByRole("textbox", { name: "Tools" }), { target: { value: " desk.list , desk.open , " } });
    fireEvent.change(screen.getByRole("textbox", { name: "Instructions" }), { target: { value: " Keep this spacing \n" } });
    fireEvent.click(advanced.querySelector("summary")!);
    expect(advanced).not.toHaveAttribute("open");
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Done" })); });
    expect(update).toHaveBeenCalledWith("recipe", recipe.id, { tools: ["desk.list", "desk.open"], system_prompt: " Keep this spacing \n" });
    expect(close).toHaveBeenCalledTimes(1);
  });
});

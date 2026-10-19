import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { useEffect, useRef } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { openNoteThought, type Thought } from "../thoughts";
import { useDesk } from "../store";
import { Pullout } from "./Pullout";
import type { RegisterCloseGuard } from "../pullouts/types";

const editorGuard = vi.hoisted(() => vi.fn(async () => true));

vi.mock("./DeskWindow", () => ({ DeskWindowFrame: ({ children, actions, onClose, beforeClose }: { children: React.ReactNode; actions?: React.ReactNode; onClose: () => void; beforeClose?: () => Promise<boolean> }) => {
  const waiting = useRef(false);
  return <section aria-label="Legacy window"><button onClick={async () => {
    if (waiting.current) return;
    waiting.current = true;
    try { if (!beforeClose || await beforeClose()) onClose(); } finally { waiting.current = false; }
  }}>Close window</button>{actions}{children}</section>;
} }));
vi.mock("../pullouts", () => ({ PULLOUT_CONTENT: { note: () => null, workflow: ({ object, registerClose }: { object: { id: string }; registerClose?: RegisterCloseGuard }) => {
  const editing = useDesk((s) => s.editingId === object.id);
  useEffect(() => editing ? registerClose?.(editorGuard) : undefined, [editing, registerClose]);
  return <div>Workflow editor</div>;
} } }));
vi.mock("../thought-workspace/ThoughtWorkspaceWindow", () => ({ ThoughtWorkspaceWindow: ({ thought }: { thought: Thought }) => <section aria-label="Thought Workbench">{thought.working_note.title}</section> }));
vi.mock("../sprites", () => ({ spriteUrl: () => "note.png", refAgent: () => undefined }));
vi.mock("../thoughts", async (importOriginal) => ({ ...(await importOriginal<typeof import("../thoughts")>()), openNoteThought: vi.fn() }));

const thought: Thought = {
  id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
  aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 0,
  working_note: { id: "note-1", title: "Owned Note", body_markdown: "Body", tags: [] }, filing_status: "filed",
};
const object = { kind: "note" as const, id: "note-1", title: "Owned Note", ref: { kind: "note", title: "Owned Note", bodyMarkdown: "Body" } } as never;

afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("Pullout: every note opens in the one note window (Betterment Q8)", () => {
  it("routes a note to exactly one sticky, with the thought the hub gives", async () => {
    useDesk.setState({ profiles: [], closePullout: vi.fn() });
    vi.mocked(openNoteThought).mockResolvedValue(thought);
    render(<Pullout o={object} />);

    expect(await screen.findByRole("region", { name: "Thought Workbench" })).toHaveTextContent("Owned Note");
    expect(screen.getAllByRole("region", { name: "Thought Workbench" })).toHaveLength(1);
    expect(openNoteThought).toHaveBeenCalledWith("note-1");
  });

  it("says so in words, with Try again, when the hub does not answer; the note is unchanged", async () => {
    useDesk.setState({ profiles: [], closePullout: vi.fn() });
    vi.mocked(openNoteThought).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(thought);
    render(<Pullout o={object} />);

    expect(await screen.findByText("Could not open this note on this hub. The note is unchanged.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("region", { name: "Thought Workbench" })).toHaveTextContent("Owned Note");
  });
});

describe("Pullout editor chrome close", () => {
  const workflow = { kind: "workflow", id: "workflow-guard", title: "Review", ref: { kind: "workflow" } } as never;
  it("awaits the local writer and keeps the actual pullout open after a refused flush", async () => {
    let resolve!: (value: boolean) => void;
    editorGuard.mockImplementationOnce(() => new Promise<boolean>((done) => { resolve = done; }));
    const closePullout = vi.fn();
    useDesk.setState({ profiles: [], editingId: "workflow-guard", closePullout });
    render(<Pullout o={workflow} pulloutId="workflow:workflow-guard" />);
    fireEvent.click(screen.getByRole("button", { name: "Close window" }));
    fireEvent.click(screen.getByRole("button", { name: "Close window" }));
    expect(editorGuard).toHaveBeenCalledTimes(1);
    expect(closePullout).not.toHaveBeenCalled();
    await act(async () => { resolve(false); });
    expect(closePullout).not.toHaveBeenCalled();
    editorGuard.mockResolvedValueOnce(true);
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Close window" })); });
    expect(closePullout).toHaveBeenCalledWith("workflow:workflow-guard");
  });

  it("removes the guard when its editor unmounts", async () => {
    editorGuard.mockResolvedValue(false);
    const closePullout = vi.fn();
    useDesk.setState({ profiles: [], editingId: "workflow-guard", closePullout });
    render(<Pullout o={workflow} />);
    act(() => useDesk.setState({ editingId: null }));
    await act(async () => { fireEvent.click(screen.getByRole("button", { name: "Close window" })); });
    expect(editorGuard).not.toHaveBeenCalled();
    expect(closePullout).toHaveBeenCalledWith("workflow-guard");
  });
});

describe("Workflow chrome editor action", () => {
  it("opens the current Workflow editor instead of the Workbenches application", () => {
    const openEditor = vi.fn();
    const openSurfaceWindow = vi.fn();
    const workflow = { kind: "workflow", id: "workflow-edit", title: "Review risks", ref: { kind: "workflow" } } as never;
    useDesk.setState({ profiles: [], editingId: null, openEditor, openSurfaceWindow });
    render(<Pullout o={workflow} />);
    fireEvent.click(screen.getByRole("button", { name: "Edit Workflow" }));
    expect(openEditor).toHaveBeenCalledWith("workflow-edit");
    expect(openSurfaceWindow).not.toHaveBeenCalled();
  });
});

// HS-129-07 — Article IV.1 census: every audited text well has a mic.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { buildLinearGraph } from "../graph";
import { DeskComposer } from "../components/DeskComposer";
import { KbEditor } from "../pullouts/editors/KbEditor";
import { NoteEditor } from "../pullouts/editors/NoteEditor";
import { WorkflowEditor } from "../pullouts/editors/WorkflowEditor";
import { DecisionsView } from "../pullouts/views/DecisionsView";

const save = vi.hoisted(() => vi.fn());
const apiFetch = vi.hoisted(() => vi.fn());

vi.mock("../components/MicButton", () => ({
  MicButton: ({ label = "Speak", onText }: { label?: string; onText: (text: string) => void }) => (
    <button type="button" data-mic onClick={() => onText("spoken")}>{label}</button>
  ),
}));

vi.mock("../store", () => ({
  useDesk: (selector: (state: { items: Record<string, unknown[]>; openPullout: () => void }) => unknown) =>
    selector({ items: { workflow: [], note: [], kb: [] }, openPullout: vi.fn() }),
}));

vi.mock("../pullouts/editors/useDebouncedSave", () => ({
  useDebouncedSave: () => save,
}));

vi.mock("../components/DeskEditor", () => ({
  DeskEditor: ({ value }: { value: string }) => <div data-testid="desk-editor">{value}</div>,
}));

vi.mock("../components/EditorAIBar", () => ({ EditorAIBar: () => null }));
vi.mock("../../lib/api", () => ({
  apiFetch,
  readableError: () => "Request failed",
}));

const workflow = {
  id: "workflow-1",
  kind: "workflow",
  ref: {
    id: "workflow-1",
    name: "Flow",
    graphJson: buildLinearGraph("workflow-1", "Flow", [
      { kind: "rewrite", tone: "Direct" },
      { kind: "keepIf", keyword: "ship" },
      { kind: "llm", prompt: "Make a plan" },
    ]),
  },
} as any;

const note = {
  id: "note-1",
  kind: "note",
  ref: { id: "note-1", title: "Note", bodyMarkdown: "body", tags: ["desk"] },
} as any;

const kb = {
  id: "kb-1",
  kind: "kb",
  ref: { id: "kb-1", name: "Knowledge", bodyMarkdown: "reference" },
} as any;

describe("HS-129-07 speakable desk", () => {
  it("census: the ten rendered audited text wells each carry a mic affordance", () => {
    apiFetch.mockResolvedValue([]);
    const { container } = render(
      <>
        <WorkflowEditor object={workflow} onClose={vi.fn()} />
        <NoteEditor object={note} onClose={vi.fn()} />
        <KbEditor object={kb} onClose={vi.fn()} />
        <DecisionsView />
        <DeskComposer value="" onChange={vi.fn()} actionLabel="Send" onAction={vi.fn()} />
        <DeskComposer multiline value="" onChange={vi.fn()} actionLabel="Send" onAction={vi.fn()} />
      </>,
    );

    const textWells = container.querySelectorAll('input:not([type="checkbox"]), textarea');
    expect(textWells).toHaveLength(10);
    textWells.forEach((well) => {
      expect(well.parentElement?.querySelector("[data-mic]") || well.parentElement?.parentElement?.querySelector("[data-mic]")).not.toBeNull();
    });
  });

  it("fills the Workflow, Note, and knowledge-base fields through their mics", () => {
    render(
      <>
        <WorkflowEditor object={workflow} onClose={vi.fn()} />
        <NoteEditor object={note} onClose={vi.fn()} />
        <KbEditor object={kb} onClose={vi.fn()} />
      </>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Speak Workflow name" }));
    expect(screen.getByRole("textbox", { name: "Workflow name" })).toHaveValue("spoken");

    fireEvent.click(screen.getByRole("button", { name: "Speak Title" }));
    expect(screen.getByRole("textbox", { name: "Title" })).toHaveValue("spoken");
    fireEvent.click(screen.getByRole("button", { name: "Speak Tags" }));
    expect(screen.getByRole("textbox", { name: "Tags" })).toHaveValue("spoken");

    fireEvent.click(screen.getByRole("button", { name: "Speak Knowledge base name" }));
    expect(screen.getByRole("textbox", { name: "Knowledge base name" })).toHaveValue("spoken");
    fireEvent.click(screen.getAllByRole("button", { name: "Speak" })[1]);
    expect(screen.getAllByTestId("desk-editor")[1]).toHaveTextContent("reference spoken");
  });

  it("fills receipt search and both composer variants through their mics", () => {
    apiFetch.mockResolvedValue([]);
    const onLineChange = vi.fn();
    const onPadChange = vi.fn();
    render(
      <>
        <DecisionsView />
        <DeskComposer value="" onChange={onLineChange} actionLabel="Send" onAction={vi.fn()} />
        <DeskComposer multiline value="" onChange={onPadChange} actionLabel="Send" onAction={vi.fn()} />
      </>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Speak Search decisions" }));
    expect(screen.getByRole("searchbox", { name: "Search decisions" })).toHaveValue("spoken");
    fireEvent.click(screen.getAllByRole("button", { name: "Speak" })[0]);
    fireEvent.click(screen.getAllByRole("button", { name: "Speak" })[1]);
    expect(onLineChange).toHaveBeenCalledWith("spoken");
    expect(onPadChange).toHaveBeenCalledWith("spoken");
  });
});

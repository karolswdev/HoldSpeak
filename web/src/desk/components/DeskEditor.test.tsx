import { act, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import type { EditorView } from "@codemirror/view";
import { utf8OffsetToIndex } from "../thought-workspace/ThoughtWorkspaceWindow";
import { DeskEditor, type DeskEditorHandle } from "./DeskEditor";
import { latchAskSelection, selectionPrompt, takeAskSelection } from "../ask";

describe("DeskEditor authoritative append reveal", () => {
  it("latches one Note passage and puts the same quote in the run prompt", () => {
    latchAskSelection({ noteRef: "note-1", text: "Keep this passage" });

    const selection = takeAskSelection();
    expect(selection).toEqual({ noteRef: "note-1", text: "Keep this passage" });
    expect(selectionPrompt("What should I do?", selection)).toBe(
      "What should I do?\n\nSelected text:\n> Keep this passage",
    );
    expect(takeAskSelection()).toBeNull();
  });

  it("reports the exact selected passage and exposes it through the handle", () => {
    const onSelectionChange = vi.fn();
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    render(
      <DeskEditor
        ref={ref}
        value="Keep this passage"
        onChange={vi.fn()}
        showToolbar={false}
        onViewChange={(next) => { view = next; }}
        onSelectionChange={onSelectionChange}
      />,
    );

    act(() => { view!.dispatch({ selection: { anchor: 5, head: 9 } }); });

    expect(onSelectionChange).toHaveBeenLastCalledWith({ from: 5, to: 9, text: "this" });
    expect(ref.current?.getSelection()).toEqual({ from: 5, to: 9, text: "this" });
  });

  it("exposes the document formatting rail and inserts a valid underline pair", () => {
    const onChange = vi.fn();
    render(<DeskEditor value="" onChange={onChange} />);

    expect(screen.getByRole("toolbar", { name: "Markdown formatting" })).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Underline" }));
    expect(onChange).toHaveBeenLastCalledWith("<u></u>");
  });

  it("does not report an authoritative prop replacement as an owner edit", () => {
    const onChange = vi.fn();
    const { rerender } = render(<DeskEditor value="Before" onChange={onChange} showToolbar={false} />);

    rerender(<DeskEditor value="Before\n\n## Clarification\nAnswer: Mina" onChange={onChange} showToolbar={false} />);

    expect(onChange).not.toHaveBeenCalled();
  });

  it("maps a multibyte UTF-8 receipt to the exact decoration and caret", () => {
    const value = "Intro\nAnswer: café 🚀\nTail";
    const prefix = "Intro\nAnswer: ";
    const appended = "café 🚀";
    const byteStart = new TextEncoder().encode(prefix).length;
    const byteEnd = new TextEncoder().encode(prefix + appended).length;
    const start = utf8OffsetToIndex(value, byteStart);
    const end = utf8OffsetToIndex(value, byteEnd);
    expect(start).toBe(prefix.length);
    expect(end).toBe(prefix.length + appended.length);

    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    const { container } = render(<DeskEditor ref={ref} value={value} onChange={vi.fn()} showToolbar={false} lineWrapping onViewChange={(next) => { view = next; }} />);
    act(() => { expect(ref.current?.revealRange(start!, end!)).toBe(true); });

    expect(container.querySelector(".cm-thought-answer-reveal")).toHaveTextContent(appended);
    expect(view!.state.selection.main.anchor).toBe(end);
    expect(document.activeElement).toHaveClass("cm-content");
  });
});

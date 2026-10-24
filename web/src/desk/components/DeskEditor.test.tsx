import { act, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import type { EditorView } from "@codemirror/view";
import { undo } from "@codemirror/commands";
import { utf8OffsetToIndex } from "../thought-workspace/ThoughtWorkspaceWindow";
import { DeskEditor, type DeskEditorHandle } from "./DeskEditor";
import { latchAskSelection, selectionPrompt, takeAskSelection } from "../ask";

describe("DeskEditor authoritative append reveal", () => {
  it("latches one Note passage and puts the same quote in the run prompt", () => {
    const source = { noteRef: "note:note-1", text: "Keep this passage", body: "Keep this passage",
      range: { from: 0, to: 17 }, windowId: "pullout:note:note-1", scrollTop: 16 };
    latchAskSelection(source);

    const selection = takeAskSelection();
    expect(selection).toEqual(source);
    expect(selectionPrompt("What should I do?", selection)).toBe(
      "What should I do?\n\nSelected text:\n> Keep this passage",
    );
    expect(takeAskSelection()).toBeNull();
  });

  it("restores a selected UTF-16 range and its captured scroll without editing the Note", () => {
    const value = "A 🚀 source B";
    const onChange = vi.fn();
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    render(<DeskEditor ref={ref} value={value} onChange={onChange} showToolbar={false} onViewChange={(next) => { view = next; }} />);
    view!.scrollDOM.scrollTop = 36;
    expect(ref.current?.getScrollTop()).toBe(36);
    act(() => { expect(ref.current?.restoreSelection(2, 11, { scrollTop: 36 })).toBe(true); });
    expect(ref.current?.getSelection()).toEqual({ from: 2, to: 11, text: "🚀 source" });
    expect(ref.current?.getScrollTop()).toBe(36);
    expect(document.activeElement).toHaveClass("cm-content");
    expect(onChange).not.toHaveBeenCalled();
    expect(ref.current?.restoreSelection(2, value.length + 1)).toBe(false);
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

describe("DeskEditor captured voice target", () => {
  it("replaces the captured selection after caret movement, without moving focus, in one undo", () => {
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    render(<DeskEditor ref={ref} value="one two three" onChange={vi.fn()} showToolbar={false}
      onViewChange={(next) => { view = next; }} />);
    act(() => { view!.dispatch({ selection: { anchor: 4, head: 7 } }); });
    const target = ref.current!.captureVoiceTarget()!;
    act(() => { view!.dispatch({ selection: { anchor: 13 } }); });
    const other = document.createElement("input");
    document.body.append(other);
    other.focus();
    act(() => { expect(ref.current!.insertAtCapturedTarget(target, "spoken")).toBe(true); });
    expect(view!.state.doc.toString()).toBe("one spoken three");
    expect(document.activeElement).toBe(other);
    act(() => { expect(undo(view!)).toBe(true); });
    expect(view!.state.doc.toString()).toBe("one two three");
    other.remove();
  });

  it("rejects a changed document, authoritative sync, read-only editor and destroyed view", () => {
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    const { rerender, unmount } = render(<DeskEditor ref={ref} value="first" onChange={vi.fn()}
      showToolbar={false} onViewChange={(next) => { view = next; }} />);
    const target = ref.current!.captureVoiceTarget()!;
    act(() => { view!.dispatch({ changes: { from: 5, insert: "!" } }); });
    expect(ref.current!.insertAtCapturedTarget(target, "late")).toBe(false);
    const second = ref.current!.captureVoiceTarget()!;
    rerender(<DeskEditor ref={ref} value="server" onChange={vi.fn()} showToolbar={false} />);
    expect(ref.current!.insertAtCapturedTarget(second, "late")).toBe(false);
    rerender(<DeskEditor ref={ref} value="server" onChange={vi.fn()} showToolbar={false} editable={false} />);
    expect(ref.current!.captureVoiceTarget()).toBeNull();
    unmount();
    expect(ref.current).toBeNull();
  });

  it("holds voice insertion while an IME composition is open", () => {
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    render(<DeskEditor ref={ref} value="draft" onChange={vi.fn()} showToolbar={false}
      onViewChange={(next) => { view = next; }} />);
    const target = ref.current!.captureVoiceTarget()!;
    fireEvent.compositionStart(view!.contentDOM);
    expect(ref.current!.captureVoiceTarget()).toBeNull();
    expect(ref.current!.insertAtCapturedTarget(target, "spoken")).toBe(false);
    fireEvent.compositionEnd(view!.contentDOM);
    expect(view!.state.doc.toString()).toBe("draft");
  });
});

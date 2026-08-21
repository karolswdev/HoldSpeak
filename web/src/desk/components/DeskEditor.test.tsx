import { act, fireEvent, render, screen } from "@testing-library/react";
import { createRef } from "react";
import { describe, expect, it, vi } from "vitest";
import type { EditorView } from "@codemirror/view";
import { utf8OffsetToIndex } from "../thought-workspace/ThoughtWorkspaceWindow";
import { DeskEditor, type DeskEditorHandle } from "./DeskEditor";

describe("DeskEditor authoritative append reveal", () => {
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

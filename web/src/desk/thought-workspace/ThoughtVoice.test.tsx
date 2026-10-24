import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { EditorView } from "@codemirror/view";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ThoughtDocumentPane } from "./ThoughtDocumentPane";
import { thoughtVoiceKey, type ThoughtVoiceDraftIO } from "./thoughtVoiceDraft";

let deliver: ((text: string) => void) | null = null;
vi.mock("../components/MicButton", () => ({
  MicButton: ({ bindText, disabled }: { bindText: () => (text: string) => void; disabled: boolean }) =>
    <button disabled={disabled} onClick={() => { deliver = bindText(); }}>Speak the note</button>,
}));

function memory(): ThoughtVoiceDraftIO & { values: Map<string, string> } {
  const values = new Map<string, string>();
  const listeners = new Set<() => void>();
  const changed = () => listeners.forEach((listener) => listener());
  return {
    values,
    get: (key) => values.get(key) ?? null,
    keep: (key, text) => { values.set(key, text); changed(); },
    forget: (key) => { values.delete(key); changed(); },
    subscribe: (listener) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
  };
}

const draft = (body: string) => ({ title: "Release review", body, tags: "" });
const editor = () => EditorView.findFromDOM(document.querySelector(".thought-note-body .cm-editor")! as HTMLElement)!;

describe("active Thought voice recovery", () => {
  beforeEach(() => { deliver = null; });

  it("uses the original selection even when the caret moves, and leaves another focused window alone", () => {
    const io = memory();
    const onEdit = vi.fn();
    render(<ThoughtDocumentPane noteId="note-1" draft={draft("one two three")} onEdit={onEdit}
      disabled={false} voiceDraftIO={io} />);
    const view = editor();
    act(() => { view.dispatch({ selection: { anchor: 4, head: 7 } }); });
    fireEvent.click(screen.getByRole("button", { name: "Speak the note" }));
    act(() => { view.dispatch({ selection: { anchor: 13 } }); });
    const other = document.createElement("input");
    document.body.append(other);
    other.focus();
    act(() => { deliver!("spoken"); });
    expect(view.state.doc.toString()).toBe("one spoken three");
    expect(document.activeElement).toBe(other);
    expect(io.get(thoughtVoiceKey("note-1"))).toBeNull();
    expect(onEdit).toHaveBeenCalledWith({ body: "one spoken three" });
    other.remove();
  });

  it("keeps multiple late results, reopens them under the same note, and inserts only on explicit action", () => {
    const io = memory();
    const { unmount } = render(<ThoughtDocumentPane noteId="note-1" draft={draft("first")} onEdit={vi.fn()}
      disabled={false} voiceDraftIO={io} />);
    const view = editor();
    fireEvent.click(screen.getByRole("button", { name: "Speak the note" }));
    act(() => { view.dispatch({ changes: { from: 5, insert: " newer" } }); });
    act(() => { deliver!("late one"); });
    fireEvent.click(screen.getByRole("button", { name: "Speak the note" }));
    unmount();
    act(() => { deliver!("late two"); });
    expect(io.get(thoughtVoiceKey("note-1"))).toBe("late one\n\nlate two");

    render(<ThoughtDocumentPane noteId="note-1" draft={draft("first newer")} onEdit={vi.fn()}
      disabled={false} voiceDraftIO={io} mic={false} />);
    expect(screen.getByText("NOT INSERTED")).toBeVisible();
    expect(screen.getByText(/late one\s+late two/)).toBeVisible();
    expect(screen.queryByText("AUDIO KEPT")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Insert at caret" }));
    expect(editor().state.doc.toString()).toContain("late one\n\nlate two");
    expect(io.get(thoughtVoiceKey("note-1"))).toBeNull();
  });

  it("cannot insert into a different note, and read-only recovery can still copy", () => {
    const io = memory();
    const { rerender } = render(<ThoughtDocumentPane noteId="note-1" draft={draft("same")}
      onEdit={vi.fn()} disabled={false} voiceDraftIO={io} />);
    fireEvent.click(screen.getByRole("button", { name: "Speak the note" }));
    rerender(<ThoughtDocumentPane noteId="note-2" draft={draft("same")}
      onEdit={vi.fn()} disabled voiceDraftIO={io} />);
    act(() => { deliver!("old note words"); });
    expect(editor().state.doc.toString()).toBe("same");
    expect(io.get(thoughtVoiceKey("note-1"))).toBe("old note words");
    expect(screen.queryByText("NOT INSERTED")).toBeNull();
    rerender(<ThoughtDocumentPane noteId="note-1" draft={draft("same")}
      onEdit={vi.fn()} disabled voiceDraftIO={io} mic={false} />);
    expect(screen.getByRole("button", { name: "Insert at caret" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Copy" })).toBeEnabled();
  });

  it("lets a fixture input use the same bound delivery and local recovery", () => {
    const io = memory();
    render(<ThoughtDocumentPane noteId="sample" draft={draft("start")} onEdit={vi.fn()}
      disabled={false} voiceDraftIO={io} mic={false}
      voiceInput={(bindText, disabled) => <button disabled={disabled}
        onClick={() => { deliver = bindText(); }}>Sample voice</button>} />);
    fireEvent.click(screen.getByRole("button", { name: "Sample voice" }));
    act(() => { editor().dispatch({ changes: { from: 5, insert: " edited" } }); });
    act(() => { deliver!("retained sample"); });
    expect(io.get(thoughtVoiceKey("sample"))).toBe("retained sample");
    expect(screen.getByText("NOT INSERTED")).toBeVisible();
  });

  it("retains late words when the same Thought becomes read-only", () => {
    const io = memory();
    const { rerender } = render(<ThoughtDocumentPane noteId="note-1" draft={draft("first")}
      onEdit={vi.fn()} disabled={false} voiceDraftIO={io} />);
    fireEvent.click(screen.getByRole("button", { name: "Speak the note" }));
    rerender(<ThoughtDocumentPane noteId="note-1" draft={draft("first")}
      onEdit={vi.fn()} disabled voiceDraftIO={io} />);
    act(() => { deliver!("late while locked"); });
    expect(editor().state.doc.toString()).toBe("first");
    expect(io.get(thoughtVoiceKey("note-1"))).toBe("late while locked");
    expect(screen.getByRole("button", { name: "Insert at caret" })).toBeDisabled();
  });

  it("keeps retained words on missing or refused clipboard and resets Copy after new words", async () => {
    const io = memory();
    io.keep(thoughtVoiceKey("note-1"), "first words");
    const priorClipboard = Object.getOwnPropertyDescriptor(navigator, "clipboard");
    const setClipboard = (value: unknown) => Object.defineProperty(navigator, "clipboard", {
      configurable: true, value,
    });
    try {
      render(<ThoughtDocumentPane noteId="note-1" draft={draft("body")} onEdit={vi.fn()}
        disabled voiceDraftIO={io} mic={false} />);
      setClipboard(undefined);
      fireEvent.click(screen.getByRole("button", { name: "Copy" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "Copy failed" })).toBeVisible());
      expect(io.get(thoughtVoiceKey("note-1"))).toBe("first words");

      setClipboard({ writeText: vi.fn().mockRejectedValue(new Error("blocked")) });
      fireEvent.click(screen.getByRole("button", { name: "Copy failed" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "Copy failed" })).toBeVisible());
      expect(io.get(thoughtVoiceKey("note-1"))).toBe("first words");

      setClipboard({ writeText: vi.fn().mockResolvedValue(undefined) });
      fireEvent.click(screen.getByRole("button", { name: "Copy failed" }));
      await waitFor(() => expect(screen.getByRole("button", { name: "Copied" })).toBeVisible());
      act(() => { io.keep(thoughtVoiceKey("note-1"), "first words\n\nnew words"); });
      expect(screen.getByRole("button", { name: "Copy" })).toBeVisible();
      expect(io.get(thoughtVoiceKey("note-1"))).toBe("first words\n\nnew words");
    } finally {
      if (priorClipboard) Object.defineProperty(navigator, "clipboard", priorClipboard);
      else Reflect.deleteProperty(navigator, "clipboard");
    }
  });
});

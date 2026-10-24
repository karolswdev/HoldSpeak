import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { undo } from "@codemirror/commands";
import { EditorView } from "@codemirror/view";
import { describe, expect, it, vi } from "vitest";
import { EditingReference } from "./EditingReference";

function editor(): EditorView {
  const element = document.querySelector(".reference-editing .cm-editor");
  if (!element) throw new Error("Thought editor was not rendered");
  const view = EditorView.findFromDOM(element as HTMLElement);
  if (!view) throw new Error("Thought CodeMirror view was not found");
  return view;
}

describe("Components editing specimen", () => {
  it("uses the live Thought captured selection and restores one insertion with Undo", () => {
    render(<EditingReference preset="ordinary" />);
    const view = editor();
    const original = view.state.doc.toString();
    const from = original.indexOf("source");
    act(() => view.dispatch({ selection: { anchor: from, head: from + "source".length } }));
    fireEvent.click(screen.getByRole("button", { name: "Capture target" }));
    act(() => view.dispatch({ selection: { anchor: original.length } }));

    const other = document.createElement("input");
    document.body.append(other);
    other.focus();
    fireEvent.click(screen.getByRole("button", { name: "Deliver local text" }));
    expect(view.state.doc.toString()).toBe(original.replace("source", "Confirm the boundary before rollout."));
    expect(screen.queryByText("NOT INSERTED")).not.toBeInTheDocument();
    act(() => expect(undo(view)).toBe(true));
    expect(view.state.doc.toString()).toBe(original);
    other.remove();
  });

  it("retains words after a newer edit, then inserts them only on the explicit recovery action", () => {
    render(<EditingReference preset="ordinary" />);
    const view = editor();
    const original = view.state.doc.toString();
    fireEvent.click(screen.getByRole("button", { name: "Capture target" }));
    act(() => view.dispatch({ changes: { from: original.length, insert: " Newer draft." } }));
    fireEvent.click(screen.getByRole("button", { name: "Deliver local text" }));

    expect(view.state.doc.toString()).toBe(`${original} Newer draft.`);
    expect(screen.getByText("NOT INSERTED")).toBeVisible();
    expect(screen.getByText("Confirm the boundary before rollout.")).toBeVisible();
    act(() => view.dispatch({ selection: { anchor: view.state.doc.length } }));
    fireEvent.click(screen.getByRole("button", { name: "Insert at caret" }));
    expect(view.state.doc.toString()).toBe(`${original} Newer draft.Confirm the boundary before rollout.`);
    expect(screen.queryByText("NOT INSERTED")).not.toBeInTheDocument();
    act(() => expect(undo(view)).toBe(true));
    expect(view.state.doc.toString()).toBe(`${original} Newer draft.`);
  });

  it("shows retained words without enabling insertion into a read-only Thought", async () => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", { configurable: true, value: { writeText } });
    render(<EditingReference preset="read-only" />);

    expect(screen.getByText("READ ONLY")).toBeVisible();
    expect(screen.getByText("NOT INSERTED")).toBeVisible();
    expect(screen.getByRole("button", { name: "Capture target" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Insert at caret" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Copy" }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith("Confirm the boundary before rollout."));
  });
});

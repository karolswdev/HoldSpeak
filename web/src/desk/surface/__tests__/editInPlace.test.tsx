// HS-101 B1 — EditInPlace: the presented text IS the editor
// (DESIGN_SYSTEM.md, "The interior canon", rule 1). Enter/blur
// commits, Escape reverts, a locked value names why.
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EditInPlace } from "../Surface";

describe("EditInPlace (canon rule 1)", () => {
  it("presents the value; click swaps to a same-value editor", () => {
    render(<EditInPlace value="Standup notes" label="block name" onCommit={() => {}} />);
    const presented = screen.getByRole("button", { name: "Edit block name" });
    expect(presented.textContent).toBe("Standup notes");
    fireEvent.click(presented);
    const editor = screen.getByRole("textbox", { name: "block name" });
    expect((editor as HTMLInputElement).value).toBe("Standup notes");
  });

  it("Enter commits the changed value", () => {
    const onCommit = vi.fn();
    render(<EditInPlace value="old" label="name" onCommit={onCommit} />);
    fireEvent.click(screen.getByRole("button"));
    const editor = screen.getByRole("textbox");
    fireEvent.change(editor, { target: { value: "new name" } });
    fireEvent.keyDown(editor, { key: "Enter" });
    expect(onCommit).toHaveBeenCalledWith("new name");
    expect(screen.queryByRole("textbox")).toBeNull();
  });

  it("Escape reverts without committing", () => {
    const onCommit = vi.fn();
    render(<EditInPlace value="kept" label="name" onCommit={onCommit} />);
    fireEvent.click(screen.getByRole("button"));
    const editor = screen.getByRole("textbox");
    fireEvent.change(editor, { target: { value: "discarded" } });
    fireEvent.keyDown(editor, { key: "Escape" });
    expect(onCommit).not.toHaveBeenCalled();
    expect(screen.getByRole("button").textContent).toBe("kept");
  });

  it("an unchanged or emptied value never commits", () => {
    const onCommit = vi.fn();
    render(<EditInPlace value="same" label="name" onCommit={onCommit} />);
    fireEvent.click(screen.getByRole("button"));
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    fireEvent.click(screen.getByRole("button"));
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "   " } });
    fireEvent.keyDown(screen.getByRole("textbox"), { key: "Enter" });
    expect(onCommit).not.toHaveBeenCalled();
  });

  it("a locked value stays presented and names why", () => {
    render(
      <EditInPlace
        value="qwen3-32b"
        label="model"
        disabledReason="managed by the mesh node"
        onCommit={() => {}}
      />,
    );
    expect(screen.queryByRole("button")).toBeNull();
    const locked = screen.getByTitle("managed by the mesh node");
    expect(locked.textContent).toBe("qwen3-32b");
  });

  it("multiline: Shift+Enter stays in the editor, Enter commits", () => {
    const onCommit = vi.fn();
    render(
      <EditInPlace value="line one" label="body" multiline onCommit={onCommit} />,
    );
    fireEvent.click(screen.getByRole("button"));
    const editor = screen.getByRole("textbox");
    fireEvent.change(editor, { target: { value: "line one\nline two" } });
    fireEvent.keyDown(editor, { key: "Enter", shiftKey: true });
    expect(onCommit).not.toHaveBeenCalled();
    fireEvent.keyDown(editor, { key: "Enter" });
    expect(onCommit).toHaveBeenCalledWith("line one\nline two");
  });
});

import { createRef } from "react";
import { fireEvent, render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EditorView } from "@codemirror/view";
import { undo } from "@codemirror/commands";

import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import { livePreview } from "./livePreview";

const NOTE = [
  "# Ledger cutover",
  "",
  "We freeze **writes** on Friday. See [the runbook](https://example.com/runbook) first.",
  "",
  "- [ ] Back up the ledger",
  "- [x] Tell Priya",
  "- plain item",
  "",
  "> Keep the old path for one week.",
  "",
  "| Step | Owner |",
  "|------|-------|",
  "| Freeze | Karol |",
  "",
  "The end.",
].join("\n");

function mount(value: string, options: Parameters<typeof livePreview>[0] = {}) {
  const ref = createRef<DeskEditorHandle>();
  const onChange = vi.fn();
  let view: EditorView | null = null;
  const result = render(<DeskEditor ref={ref} value={value} onChange={onChange} showToolbar={false}
    extensions={livePreview(options)} onViewChange={(v) => { view = v; }} />);
  const text = () => result.container.querySelector(".cm-content")?.textContent ?? "";
  return { ref, onChange, view: () => view!, text, ...result };
}

const END = NOTE.length;

describe("the Note in live preview", () => {
  it("hides the heading marks outside the caret and shows them on the caret's line, the caret unmoved", async () => {
    const { ref, container, text, view } = mount(NOTE);
    ref.current!.restoreSelection(END, END, { focus: false });
    await waitFor(() => expect(text()).not.toContain("# Ledger"));
    expect(text()).toContain("Ledger cutover");
    const heading = container.querySelector(".cm-line.cm-lp-h1");
    expect(heading?.textContent).toBe("Ledger cutover");

    const at = NOTE.indexOf("cutover");
    ref.current!.restoreSelection(at, at, { focus: false });
    await waitFor(() => expect(container.querySelector(".cm-line.cm-lp-h1")?.textContent).toBe("# Ledger cutover"));
    // The size stays (same line class) and the caret did not jump.
    expect(view().state.selection.main.head).toBe(at);
    expect(view().state.doc.toString()).toBe(NOTE);
  });

  it("hides emphasis marks and a link's url; the link text carries the url as its hover title", async () => {
    const { ref, container, text } = mount(NOTE);
    ref.current!.restoreSelection(END, END, { focus: false });
    await waitFor(() => expect(text()).not.toContain("**"));
    expect(text()).not.toContain("https://example.com/runbook");
    expect(text()).not.toContain("[the runbook]");
    const link = container.querySelector<HTMLElement>(".cm-lp-link");
    expect(link?.textContent).toBe("the runbook");
    expect(link?.getAttribute("title")).toBe("https://example.com/runbook");
    expect(container.querySelector(".cm-lp-strong")?.textContent).toBe("writes");
  });

  it("⌘-click on a link opens the url, and a desk ref through the desk opener", async () => {
    const openUrl = vi.fn();
    const openRef = vi.fn(() => true);
    const value = "Read [the runbook](https://example.com/runbook) and [the room](project:p-1).\n\nEnd.";
    const { ref, container } = mount(value, { openUrl, openRef });
    ref.current!.restoreSelection(value.length, value.length, { focus: false });
    await waitFor(() => expect(container.querySelectorAll(".cm-lp-link").length).toBe(2));
    const [web, room] = Array.from(container.querySelectorAll<HTMLElement>(".cm-lp-link"));
    fireEvent.mouseDown(web, { button: 0, metaKey: true });
    expect(openUrl).toHaveBeenCalledWith("https://example.com/runbook");
    fireEvent.mouseDown(room, { button: 0, metaKey: true });
    expect(openRef).toHaveBeenCalledWith("project:p-1");
  });

  it("a task is a checkbox that toggles the source, and the toggle undoes", async () => {
    const { ref, container, onChange, view } = mount(NOTE);
    ref.current!.restoreSelection(END, END, { focus: false });
    await waitFor(() => expect(container.querySelectorAll('[data-testid="note-task-box"]').length).toBe(2));
    const [open, done] = Array.from(container.querySelectorAll<HTMLInputElement>('[data-testid="note-task-box"]'));
    expect(open.checked).toBe(false);
    expect(done.checked).toBe(true);
    expect(container.querySelector(".cm-lp-done")?.textContent).toBe("Tell Priya");
    // The plain item is a bullet glyph, not a dash.
    expect(container.querySelector(".cm-lp-bullet")?.textContent).toBe("•");

    fireEvent.click(open);
    expect(view().state.doc.toString()).toContain("- [x] Back up the ledger");
    expect(onChange).toHaveBeenLastCalledWith(expect.stringContaining("- [x] Back up the ledger"));
    expect(view().state.selection.main.head).toBe(END);
    await waitFor(() => expect(container.querySelectorAll<HTMLInputElement>('[data-testid="note-task-box"]')[0].checked).toBe(true));

    undo(view());
    expect(view().state.doc.toString()).toBe(NOTE);
  });

  it("a table renders as a table outside the caret and as source inside it", async () => {
    const { ref, container, text } = mount(NOTE);
    ref.current!.restoreSelection(END, END, { focus: false });
    await waitFor(() => expect(container.querySelector('[data-testid="note-table"]')).not.toBeNull());
    const table = container.querySelector('[data-testid="note-table"] table')!;
    expect(Array.from(table.querySelectorAll("th")).map((th) => th.textContent)).toEqual(["Step", "Owner"]);
    expect(Array.from(table.querySelectorAll("td")).map((td) => td.textContent)).toEqual(["Freeze", "Karol"]);
    expect(text()).not.toContain("|------|");

    const inside = NOTE.indexOf("Freeze |");
    ref.current!.restoreSelection(inside, inside, { focus: false });
    await waitFor(() => expect(container.querySelector('[data-testid="note-table"]')).toBeNull());
    expect(text()).toContain("| Step | Owner |");
  });

  it("a code fence hides its marks and shows its language word; the quote mark hides", async () => {
    const value = "Intro\n\n```ts\nconst a = 1;\n```\n\n> A quote\n\nEnd.";
    const { ref, container, text } = mount(value);
    ref.current!.restoreSelection(value.length, value.length, { focus: false });
    await waitFor(() => expect(container.querySelector(".cm-lp-fence-label")?.textContent).toBe("ts"));
    expect(text()).not.toContain("```");
    expect(container.querySelectorAll(".cm-line.cm-lp-code").length).toBe(3);
    expect(container.querySelector(".cm-line.cm-lp-quote")?.textContent).toBe("A quote");
  });

  it("W1-DOORS: opens with the caret at the end and every line rendered until the editor takes focus", async () => {
    const TASKS = "- [ ] Freeze writes\n- [ ] Tell Priya";
    const ref = createRef<DeskEditorHandle>();
    let view: EditorView | null = null;
    const { container } = render(<DeskEditor ref={ref} value={TASKS} onChange={vi.fn()} showToolbar={false}
      initialCaret="end" extensions={livePreview({ renderUntilFocus: true })} onViewChange={(v) => { view = v; }} />);
    // The caret is the writer's: after the last character.
    expect(view!.state.selection.main.head).toBe(TASKS.length);
    // No line shows its source, the caret's line too: two real boxes.
    await waitFor(() => expect(container.querySelectorAll("input[type=checkbox]").length).toBe(2));
    expect(container.querySelector(".cm-content")?.textContent).not.toContain("[ ]");
    // The first press into the editor brings the caret's line source back.
    view!.focus();
    view!.dispatch({ effects: [] });
    await waitFor(() => expect(container.querySelector(".cm-content")?.textContent).toContain("- [ ] Tell Priya"));
  });
});


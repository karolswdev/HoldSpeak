import { createRef } from "react";
import { fireEvent, render, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { EditorView } from "@codemirror/view";
import { undo } from "@codemirror/commands";

import { DeskEditor, type DeskEditorHandle } from "../components/DeskEditor";
import { startCompletion } from "@codemirror/autocomplete";
import { livePreview } from "./livePreview";
import type { NoteObjects } from "./noteObjects";

/** Recorded-shape desk answers for the objects (the People roster rows and
 *  the Project summaries the store keeps). */
const OBJECTS: NoteObjects = {
  peek: (token) => token.kind === "person" ? { name: "Priya Shah", kind: "Person", fact: "Direct report" }
    : token.kind === "project" ? { name: "Payments ledger cutover", kind: "Project", fact: "Changed Oct 24" }
    : token.kind === "pr" ? { name: token.label, kind: "Pull request", fact: "acme/ledger" }
    : { name: token.label, kind: token.kind === "jira" ? "Jira issue" : "Object" },
  people: async () => [{ id: "p-priya", name: "Priya Shah", detail: "Direct report" }, { id: "p-marcus", name: "Marcus Chen" }],
  projects: () => [{ id: "proj-ledger", name: "Payments ledger cutover", detail: "Project" }],
};

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
    await waitFor(() => expect(container.querySelectorAll(".cm-lp-link").length).toBe(1));
    const web = container.querySelector<HTMLElement>(".cm-lp-link")!;
    fireEvent.mouseDown(web, { button: 0, metaKey: true });
    expect(openUrl).toHaveBeenCalledWith("https://example.com/runbook");
    // Step 4: a desk ref is an object token; a press opens it.
    const room = container.querySelector<HTMLElement>('[data-testid="note-object"]')!;
    fireEvent.mouseDown(room, { button: 0 });
    expect(openRef).toHaveBeenCalledWith("project:p-1");
    // On the caret's line the link shows its source, and ⌘-click still opens it.
    const at = value.indexOf("the room");
    ref.current!.restoreSelection(at, at, { focus: false });
    await waitFor(() => expect(container.querySelector('[data-testid="note-object"]')).toBeNull());
    openRef.mockClear();
    fireEvent.mouseDown(container.querySelector<HTMLElement>('.cm-lp-obj-ink[data-lp-href="project:p-1"]')!, { button: 0, metaKey: true });
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

  it("step 4: every object kind renders as glyph and ink with its peek card; a press opens it", async () => {
    const openRef = vi.fn(() => true);
    const openUrl = vi.fn();
    const value = [
      "The shim is in https://github.com/acme/ledger/pull/1482 and [@Priya](person:p-priya) owns the rollback.",
      "File it in [#Payments](project:proj-ledger); see [the choice](decision:d-1) from [Ledger sync](meeting:m-1).",
      "- [ ] Review #1482 and dry run PAY-311 (not UTF-8)",
      "",
      "End.",
    ].join("\n");
    const { ref, container, text } = mount(value, { openRef, openUrl, objects: OBJECTS });
    ref.current!.restoreSelection(value.length, value.length, { focus: false });
    await waitFor(() => expect(container.querySelectorAll('[data-testid="note-object"]').length).toBe(7));
    const tokens = Array.from(container.querySelectorAll<HTMLElement>('[data-testid="note-object"]'));
    expect(tokens.map((t) => [t.dataset.kind, t.querySelector(".cm-lp-obj-text")?.textContent])).toEqual([
      ["pr", "PR #1482"], ["person", "@Priya"], ["project", "#Payments"], ["decision", "the choice"],
      ["meeting", "Ledger sync"], ["pr", "#1482"], ["jira", "PAY-311"],
    ]);
    expect(text()).not.toContain("person:p-priya");
    expect(text()).not.toContain("UTF-8 ");
    // Each token carries its glyph and its peek card (name · kind · one fact).
    const person = tokens[1];
    expect(person.querySelector("img.cm-lp-obj-glyph")).not.toBeNull();
    expect(person.querySelector('[data-testid="note-object-peek"]')?.textContent).toBe("Priya ShahPerson · Direct report");
    // A press opens: the person through the desk opener, the PR in a tab;
    // the bare #1482 opens the same pull request the note links.
    fireEvent.mouseDown(person, { button: 0 });
    expect(openRef).toHaveBeenLastCalledWith("person:p-priya");
    fireEvent.mouseDown(tokens[0], { button: 0 });
    fireEvent.mouseDown(tokens[5], { button: 0 });
    expect(openUrl).toHaveBeenCalledTimes(2);
    expect(openUrl).toHaveBeenLastCalledWith("https://github.com/acme/ledger/pull/1482");
    // A Jira key has no window on the desk: it names, it does not open.
    expect(tokens[6].hasAttribute("data-opens")).toBe(false);
    expect(container.querySelector(".cm-content")?.textContent).not.toContain("(person:");
  });

  it("step 4: @ offers the people and # the Projects; ⏎ writes a plain Markdown link", async () => {
    const value = "Ask ";
    const { ref, view } = mount(value, { objects: OBJECTS });
    ref.current!.restoreSelection(value.length, value.length, { focus: true });
    view().dispatch({ changes: { from: value.length, insert: "@Pri" }, selection: { anchor: value.length + 4 }, userEvent: "input.type" });
    startCompletion(view());
    await waitFor(() => expect(document.querySelector(".cm-tooltip.cm-lp-complete")).not.toBeNull());
    const options = Array.from(document.querySelectorAll(".cm-lp-complete-option"));
    expect(options[0]?.textContent).toContain("Priya Shah");
    expect(options[0]?.querySelector("img.cm-lp-complete-glyph")).not.toBeNull();
    // CodeMirror takes ⏎ for a list once it has been open 75 ms (its interaction delay).
    await new Promise((done) => setTimeout(done, 120));
    fireEvent.keyDown(view().contentDOM, { key: "Enter" });
    await waitFor(() => expect(view().state.doc.toString()).toBe("Ask [@Priya Shah](person:p-priya)"));

    const end = view().state.doc.length;
    view().dispatch({ changes: { from: end, insert: " in #Pay" }, selection: { anchor: end + 8 }, userEvent: "input.type" });
    startCompletion(view());
    await waitFor(() => expect(document.querySelector(".cm-lp-complete-option")?.textContent).toContain("Payments ledger cutover"));
    // CodeMirror takes ⏎ for a list once it has been open 75 ms (its interaction delay).
    await new Promise((done) => setTimeout(done, 120));
    fireEvent.keyDown(view().contentDOM, { key: "Enter" });
    await waitFor(() => expect(view().state.doc.toString()).toBe("Ask [@Priya Shah](person:p-priya) in [#Payments ledger cutover](project:proj-ledger)"));
  });
});

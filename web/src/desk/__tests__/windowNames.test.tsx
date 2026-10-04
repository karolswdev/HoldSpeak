// A window's title is the name of the thing in it (owner ratified
// 2026-10-04). The real frame, the real registry, the real Dock and the
// real menu bar: one name on every face, the kind first only when two open
// windows have the same name, and the Window menu lists the open windows.
import { act, fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { DeskWindowFrame, Dock } from "../components/DeskWindow";
import { DeskMenuBar } from "../components/DeskMenuBar";
import { EditInPlace } from "../surface/Surface";
import { registrySnapshot, frontWindowId } from "../components/window/windowRegistry";
import { publishThoughtDraft, useThoughtDraftWords } from "../thoughtDrafts";
import { windowName } from "../windowName";
import { useDesk } from "../store";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {}, panelSaved: [], panelOrder: [], panelMin: [], panelMax: [],
    windowsById: {}, zoneWindows: [], zoneViewPrefs: {},
  });
});

function Win({ id, name, kind }: { id: string; name: string; kind?: string }) {
  return (
    <DeskWindowFrame id={id} title={name} label={name} kindWord={kind} icon={<span>◈</span>} open onClose={() => {}}>
      <p>{id}</p>
    </DeskWindowFrame>
  );
}
const titleOf = (id: string) =>
  screen.getByText(id).closest(".desk-window")?.querySelector(".desk-window-title")?.textContent?.trim();

describe("one name on every face", () => {
  it("different names: no kind word in the title bar, the registry or the Dock", () => {
    render(<><Win id="pullout:a" name="Ledger cutover: rollback plan" kind="Thought" /><Win id="pullout:b" name="New thought" kind="Thought" /><Dock /></>);
    expect(registrySnapshot.map((w) => w.label)).toEqual(["Ledger cutover: rollback plan", "New thought"]);
    expect(titleOf("pullout:a")).toBe("Ledger cutover: rollback plan");
    expect(titleOf("pullout:b")).toBe("New thought");
  });

  it("the same name in two open windows: each puts its kind first, on every face; the ids do not change", () => {
    const { rerender } = render(<><Win id="pullout:a" name="Ledger cutover: rollback plan" kind="Thought" /><Win id="pullout:b" name="Ledger cutover: rollback plan" kind="Note" /><Dock /></>);
    expect(registrySnapshot.map((w) => [w.id, w.label, w.name])).toEqual([
      ["pullout:a", "Thought · Ledger cutover: rollback plan", "Ledger cutover: rollback plan"],
      ["pullout:b", "Note · Ledger cutover: rollback plan", "Ledger cutover: rollback plan"],
    ]);
    expect(titleOf("pullout:a")).toBe("Thought · Ledger cutover: rollback plan");
    expect(titleOf("pullout:b")).toBe("Note · Ledger cutover: rollback plan");
    expect(screen.getByRole("region", { name: "Note · Ledger cutover: rollback plan" })).toBeTruthy();
    // The kind word leaves when the collision ends.
    rerender(<><Win id="pullout:a" name="Ledger cutover: rollback plan" kind="Thought" /><Dock /></>);
    expect(registrySnapshot.map((w) => w.label)).toEqual(["Ledger cutover: rollback plan"]);
    expect(titleOf("pullout:a")).toBe("Ledger cutover: rollback plan");
  });
});

describe("the Window menu lists the open windows", () => {
  it("lists every open window at the end, the front one checked; a pick fronts it", () => {
    render(<><Win id="pullout:a" name="Ledger cutover: rollback plan" kind="Thought" /><Win id="pullout:b" name="New thought" kind="Thought" /><DeskMenuBar /></>);
    act(() => useDesk.getState().focusPanel("pullout:a"));
    expect(frontWindowId()).toBe("pullout:a");
    fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Window menu" });
    const rows = within(menu).getAllByRole("menuitemcheckbox").filter((r) => /Ledger|New thought/.test(r.textContent ?? ""));
    expect(rows.map((r) => [r.textContent?.replace(/[^\w :·]/g, "").trim(), r.getAttribute("aria-checked")])).toEqual([
      ["Ledger cutover: rollback plan", "true"],
      ["New thought", "false"],
    ]);
    // The list is the END of the menu.
    const all = Array.from(menu.querySelectorAll('[role^="menuitem"]'));
    expect(all.slice(-2)).toEqual(rows);
    fireEvent.click(rows[1]);
    expect(frontWindowId()).toBe("pullout:b");
  });

  it("a minimized window comes back when it is picked", () => {
    render(<><Win id="pullout:a" name="Alpha" /><Win id="pullout:b" name="Beta" /><DeskMenuBar /></>);
    act(() => useDesk.getState().minimizePanel("pullout:a"));
    fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
    fireEvent.click(within(screen.getByRole("menu", { name: "Window menu" })).getByRole("menuitemcheckbox", { name: /Alpha/ }));
    expect(useDesk.getState().panelMin).not.toContain("pullout:a");
    expect(frontWindowId()).toBe("pullout:a");
  });

  it("no window open: no list and no trailing rule", () => {
    render(<DeskMenuBar />);
    fireEvent.click(screen.getByRole("button", { name: "Window" }), { detail: 0 });
    const menu = screen.getByRole("menu", { name: "Window menu" });
    expect(menu.lastElementChild?.getAttribute("role")).not.toBe("separator");
  });
});

describe("the thought's name follows the draft at once", () => {
  function Name({ noteId, kept }: { noteId: string; kept: { title: string; body_markdown: string } }) {
    const words = useThoughtDraftWords(noteId);
    return <output>{windowName({ kind: "thought", title: words?.title ?? kept.title, body: words?.body ?? kept.body_markdown, keptBody: kept.body_markdown })}</output>;
  }
  it("New thought, then the first words as they are typed, then the kept name again when the window closes", () => {
    render(<Name noteId="n1" kept={{ title: "Thought", body_markdown: "" }} />);
    expect(screen.getByRole("status")).toHaveTextContent("New thought");
    let withdraw = () => {};
    act(() => { withdraw = publishThoughtDraft("n1", { title: "Thought", body: "Ask Priya whether" }); });
    expect(screen.getByRole("status")).toHaveTextContent("Ask Priya whether");
    act(() => { publishThoughtDraft("n1", { title: "Cutover plan", body: "Ask Priya whether" }); });
    expect(screen.getByRole("status")).toHaveTextContent("Cutover plan");
    act(() => withdraw());
    expect(screen.getByRole("status")).toHaveTextContent("New thought");
  });
});

describe("EditInPlace placeholder: an empty title field", () => {
  it("shows the placeholder words for an empty value, and the editor starts empty", () => {
    const commits: string[] = [];
    render(<EditInPlace label="Title" value="" placeholder="New thought" onCommit={(v) => { commits.push(v); }} mic={false} />);
    const shown = screen.getByRole("button", { name: "Edit Title" });
    expect(shown).toHaveTextContent("New thought");
    expect(shown).toHaveClass("is-placeholder");
    fireEvent.click(shown);
    const field = screen.getByRole("textbox", { name: "Title" }) as HTMLInputElement;
    expect(field.value).toBe("");
    expect(field.placeholder).toBe("New thought");
    fireEvent.blur(field);
    expect(commits).toEqual([]);   // the placeholder is never saved as a name
  });
  it("a real value has no placeholder class", () => {
    render(<EditInPlace label="Title" value="Cutover plan" placeholder="New thought" onCommit={() => {}} mic={false} />);
    expect(screen.getByRole("button", { name: "Edit Title" })).not.toHaveClass("is-placeholder");
  });
});

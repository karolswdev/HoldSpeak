/** PHILO-13-16 (C6) — capture from anywhere: the pop-key verb and the
 * title from the first words. Red on main: no `desk.new-thought` verb, no
 * ⌃T, and every thought saved as `Thought`. */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { dispatchKey } from "../keymap";
import { menuVerbs, verbById } from "../verbRegistry";
import { firstWords, thoughtTitle, NEW_THOUGHT_TITLE } from "../thoughtTitle";
import { useThoughtNoteWriter } from "../pullouts/editors/useThoughtNoteWriter";
import { saveThoughtWorking, type Thought } from "../thoughts";
import { openNewThought } from "../newThought";

vi.mock("../newThought", () => ({ openNewThought: vi.fn().mockResolvedValue(undefined) }));
vi.mock("../thoughts", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../thoughts")>()),
  saveThoughtWorking: vi.fn(),
}));

const kd = (init: KeyboardEventInit) => new KeyboardEvent("keydown", { bubbles: true, cancelable: true, ...init });
const flush = () => new Promise((done) => setTimeout(done, 0));

beforeEach(() => vi.mocked(openNewThought).mockClear());
afterEach(() => { vi.useRealTimers(); vi.clearAllMocks(); document.body.innerHTML = ""; });

describe("the pop-key verb", () => {
  it("is one registered verb in the Desk menu, with ⌃T shown as its key", () => {
    const verb = verbById("desk.new-thought");
    expect(verb).toMatchObject({ label: "Write a thought", menu: "desk", key: "⌃T" });
    expect(menuVerbs("desk").map((v) => v.id)).toContain("desk.new-thought");
    expect(verb!.wide).toBeFalsy(); // offered at 393 too (no hardware key assumed)
  });

  it("⌃T from a window (focus off any field) opens a new thought", async () => {
    const pane = document.createElement("div");
    pane.tabIndex = 0;
    document.body.appendChild(pane);
    const event = kd({ key: "t", ctrlKey: true });
    Object.defineProperty(event, "target", { value: pane });
    expect(dispatchKey(event)?.id).toBe("desk.new-thought");
    expect(event.defaultPrevented).toBe(true);
    await flush();
    expect(openNewThought).toHaveBeenCalledTimes(1);
  });

  it("⌃T inside a text field belongs to the field", async () => {
    for (const tag of ["input", "textarea"]) {
      const field = document.createElement(tag);
      document.body.appendChild(field);
      const event = kd({ key: "t", ctrlKey: true });
      Object.defineProperty(event, "target", { value: field });
      expect(dispatchKey(event)).toBeNull();
      expect(event.defaultPrevented).toBe(false);
    }
    const editable = document.createElement("div");
    editable.setAttribute("contenteditable", "true");
    const inner = document.createElement("span");
    editable.appendChild(inner);
    document.body.appendChild(editable);
    const event = kd({ key: "t", ctrlKey: true });
    Object.defineProperty(event, "target", { value: inner });
    expect(dispatchKey(event)).toBeNull();
    await flush();
    expect(openNewThought).not.toHaveBeenCalled();
  });

  it("⌘T is not the pop-key (the browser keeps its new tab)", () => {
    expect(dispatchKey(kd({ key: "t", metaKey: true }))).toBeNull();
  });
});

describe("the title rule", () => {
  it("takes the first words of the first line with words", () => {
    expect(firstWords("\n\n# Ask Priya about the ADR\nmore")).toBe("Ask Priya about the ADR");
    expect(firstWords("- [ ] Hire a second SRE")).toBe("Hire a second SRE");
    expect(firstWords("")).toBe("");
    const long = "Move the billing service off the shared database before the quarter ends and tell the team";
    const title = firstWords(long);
    expect(title.length).toBeLessThanOrEqual(61);
    expect(title.endsWith("…")).toBe(true);
    expect(long.startsWith(title.slice(0, -1))).toBe(true);
  });

  it("three thoughts get three names", () => {
    const kept = { title: NEW_THOUGHT_TITLE, body_markdown: "" };
    const names = ["Ask Priya about the ADR", "Hire a second SRE", "Cut the Q4 scope"].map((body) => thoughtTitle(NEW_THOUGHT_TITLE, kept, body));
    expect(new Set(names).size).toBe(3);
    expect(names).not.toContain(NEW_THOUGHT_TITLE);
  });

  it("follows the first words while untitled; a title he typed is his", () => {
    expect(thoughtTitle("Ask Priya", { title: "Ask Priya", body_markdown: "Ask Priya" }, "Ask Priya about the ADR")).toBe("Ask Priya about the ADR");
    expect(thoughtTitle("My name", { title: "Thought", body_markdown: "" }, "Ask Priya")).toBe("My name");
    expect(thoughtTitle("Hiring", { title: "Hiring", body_markdown: "Ask Priya" }, "Ask Priya about it")).toBe("Hiring");
    expect(thoughtTitle("Thought", { title: "Thought", body_markdown: "" }, "")).toBe("Thought");
  });
});

describe("the writer saves an untitled thought under its first words", () => {
  const thought: Thought = {
    id: "thought-1", source: { kind: "typed" }, raw_captured_at: "now", state: "working",
    aggregate_revision: 1, lifecycle_revision: 1, working_revision: 1, attachment_revision: 1,
    working_note: { id: "note-1", title: "Thought", body_markdown: "", tags: [] }, filing_status: "filed",
  };
  function Harness() {
    const writer = useThoughtNoteWriter({ thought, onThought: vi.fn() });
    return <>
      <span data-testid="title">{writer.draft.title}</span>
      <textarea aria-label="Body" value={writer.draft.body} onChange={(e) => writer.edit({ body: e.target.value })} />
    </>;
  }

  it("sends the first words, and the window shows them", async () => {
    vi.useFakeTimers();
    vi.mocked(saveThoughtWorking).mockImplementation(async (current, patch) => ({
      ...current, aggregate_revision: 2, working_revision: 2,
      working_note: { ...current.working_note, ...patch, tags: patch.tags ?? [] },
    }) as Thought);
    render(<Harness />);
    fireEvent.change(screen.getByLabelText("Body"), { target: { value: "Ask Priya about the ADR\nShe owns it" } });
    await act(async () => { await vi.advanceTimersByTimeAsync(451); });
    expect(vi.mocked(saveThoughtWorking).mock.calls[0][1]).toMatchObject({ title: "Ask Priya about the ADR" });
    expect(screen.getByTestId("title").textContent).toBe("Ask Priya about the ADR");
  });
});

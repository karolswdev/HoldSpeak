/** Desk creation (the New verbs), app file — moved from the browser suite by
 * the test diet (2026-10-11).
 *
 * The fault it fences (inventory 2026-10-03, A-apps row 33): New Note /
 * Knowledge / Agent / Thread made the record and showed nothing until a full
 * desk read ended (2 to 5 s with a roadmap), so the press looked dead and
 * records piled up unseen. Now the window opens from the create answer, and
 * a second quick press makes no second record.
 *
 * Real store (createPrimitive, adoptCreated, the real refresh and loadAll),
 * real verbs (verbRegistry), real InlineEditor window, real palette; the hub
 * transport is the double. The desk read is slow: GET /api/roadmaps waits
 * until the test lets it go. Each create answer below is the hub's own
 * answer, copied from a run of the real routes on an isolated hub
 * (2026-10-11). The editor's content is a stand-in that keeps its own typed
 * name, as the real editors do (their fields are local state). */
import { act, fireEvent, render, screen } from "@testing-library/react";
import { useState } from "react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

const hub = vi.hoisted(() => ({
  notes: [] as Array<Record<string, unknown>>,
  kbs: [] as Array<Record<string, unknown>>,
  recipes: [] as Array<Record<string, unknown>>,
  threads: [] as Array<Record<string, unknown>>,
  posts: [] as string[],
  gated: [] as Array<() => void>,
  n: 0,
}));

const STAMP = "2026-10-11T15:31:33Z";
/* The hub's create answers (POST /api/notes, /api/kbs, /api/recipes,
 * /api/threads), field for field; only the id counts up. */
const wire = {
  note: (id: string) => ({ id, title: "", body_markdown: "", tags: [], created_at: STAMP, updated_at: STAMP,
    last_modified: STAMP, deleted: false }),
  kb: (id: string) => ({ id, name: "New Knowledge", member_ids: [], created_at: STAMP, last_modified: STAMP,
    deleted: false }),
  recipe: (id: string) => ({ id, name: "New Agent", avatar: "", role: "", system_prompt: "", user_template: "",
    tools: [], kb_id: null, profile_id: null, manual_context: "", use_zone_context: false, kind: "",
    created_at: STAMP, last_modified: STAMP, deleted: false,
    capability: { kind: "persona", input_schema: { type: "object", required: ["input"],
      properties: { input: { type: "string", help: "Material to work on." } } },
      input_help: "Choose or enter the material this capability should work on.",
      supported_placements: ["assignment:recipe"], effect_classes: ["creates_artifact"],
      readiness: { state: "ready", detail: "" }, action_label: "Ask New Agent", support: "supported" },
    placement: { source: "canonical_assignment", subject_kind: "recipe", subject_id: id } }),
  thread: (id: string) => ({ id, title: "", recipe_id: "", profile_override: "", directory_id: "", call_mode: 0,
    token_in: 0, token_out: 0, created_at: 1791732693.721954, updated_at: 1791732693.721954,
    last_turn_at: null, mode: null }),
};

vi.mock("../../lib/api", async (importOriginal) => {
  const real = await importOriginal<Record<string, unknown>>();
  const made = (bucket: "notes" | "kbs" | "recipes", key: "note" | "kb" | "recipe", path: string) => {
    hub.posts.push(path);
    const id = `${key}_${++hub.n}`;
    const record = wire[key](id);
    hub[bucket] = [...hub[bucket], record];
    return Promise.resolve({ ok: true, status: 201, json: () => Promise.resolve({ [key]: record }) });
  };
  return {
    ...real,
    apiRequest: vi.fn((url: string, init?: RequestInit) => {
      if (init?.method === "POST" && url === "/api/notes") return made("notes", "note", url);
      if (init?.method === "POST" && url === "/api/kbs") return made("kbs", "kb", url);
      if (init?.method === "POST" && url === "/api/recipes") return made("recipes", "recipe", url);
      return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({}) });
    }),
    apiFetch: vi.fn((url: string, init?: RequestInit) => {
      if (init?.method === "POST" && url === "/api/threads") {
        hub.posts.push(url);
        const thread = wire.thread(`th_${++hub.n}`);
        hub.threads = [...hub.threads, thread];
        return Promise.resolve(thread);
      }
      // The slow desk read: the roadmap read waits for the test.
      if (url === "/api/roadmaps")
        return new Promise((done) => { hub.gated.push(() => done({ roadmaps: [] })); });
      // Every other read answers at once with the hub as it is NOW.
      if (url === "/api/notes") return Promise.resolve({ notes: [...hub.notes] });
      if (url === "/api/kbs") return Promise.resolve({ kbs: [...hub.kbs] });
      if (url === "/api/recipes") return Promise.resolve({ recipes: [...hub.recipes] });
      if (url.split("?")[0] === "/api/threads") return Promise.resolve({ threads: [...hub.threads] });
      return Promise.resolve({});
    }),
  };
});
vi.mock("../setup", () => ({ loadSetup: vi.fn(() => Promise.resolve(null)) }));
vi.mock("../pullouts/editors", async (importOriginal) => {
  const real = await importOriginal<typeof import("../pullouts/editors")>();
  const Named = ({ object, autoFocusName }: { object: { kind: string; title?: string }; autoFocusName?: boolean }) => {
    const [name, setName] = useState(String(object.title ?? ""));
    return (
      <input aria-label="Name" data-testid={`name-${object.kind}`} data-autofocus={String(!!autoFocusName)}
        value={name} onChange={(e) => setName(e.target.value)} />
    );
  };
  return {
    ...real,
    INLINE_EDITOR_CONTENT: { ...real.INLINE_EDITOR_CONTENT, note: Named, kb: Named, recipe: Named },
  };
});

import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { objectByRef } from "../world";
import { InlineEditor } from "../components/InlineEditor";
import { DeskToolShelf } from "../components/DeskToolShelf";
import { VERBS } from "../verbRegistry";

/** The desk's own editor mount (DeskApp.tsx: editingId -> InlineEditor). */
function Desk() {
  const editingId = useDesk((s) => s.editingId);
  const items = useDesk((s) => s.items);
  const o = editingId ? objectByRef(items, editingId) : null;
  return o ? <InlineEditor key={o.id} o={o} u={{ x: 0.5, y: 0.4 }} /> : null;
}

const verb = (id: string) => VERBS.find((v) => v.id === id)!;
const press = (id: string) => verb(id).run({ selectedRef: null } as never);
async function settle(ms = 0) {
  await act(async () => { await new Promise((r) => setTimeout(r, ms)); });
}
async function letReadsLand() {
  for (let i = 0; i < 5; i++) {
    const waiting = hub.gated.splice(0);
    waiting.forEach((go) => go());
    await settle();
  }
}

beforeEach(() => {
  hub.notes = [wire.note("note_seed")].map((n) => ({ ...n, title: "Ledger cutover risks" }));
  hub.kbs = [];
  hub.recipes = [];
  hub.threads = [];
  hub.posts = [];
  hub.gated = [];
  usePalette.setState({ open: false });
  useDesk.setState({ pullouts: [], editingId: null, editorOrigin: null, newIds: [], panelOrder: [],
    panelMin: [], panelMax: [], panelRects: {} });
});

const EDITOR_VERBS = [
  ["desk.new-note", "/api/notes", "note"],
  ["desk.new-knowledge", "/api/kbs", "kb"],
  // Betterment AG1 (DECISIONS #3): New Agent left the Desk menu (parked).
] as const;

describe("a New verb opens its window at once, while the desk read is slow", () => {
  it.each(EDITOR_VERBS)("%s: one POST, the window is open before the read ends, the typed name stays", async (id, path, kind) => {
    // replaces: tests/e2e/test_new_verbs_open_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once
    render(<Desk />);
    // A desk read is already running (the roadmap read is slow).
    const before = useDesk.getState().refresh();
    await settle();
    await act(async () => { press(id); });
    await settle();
    expect(hub.posts).toEqual([path]);
    expect(hub.gated.length).toBeGreaterThan(0);          // no read has ended
    const made = useDesk.getState().editingId!;
    expect(made).toMatch(new RegExp(`^${kind}_`));
    const win = document.getElementById(`editor:${kind}:${made}`);
    expect(win).not.toBeNull();                           // its window is on the desk now
    const name = screen.getByTestId(`name-${kind}`) as HTMLInputElement;
    expect(name.dataset.autofocus).toBe("true");          // a new record's name field takes the keys
    fireEvent.change(name, { target: { value: `${name.value} ledger` } });

    await letReadsLand();                                 // the old read and the create's read land
    await before;
    expect(useDesk.getState().editingId).toBe(made);
    expect(document.getElementById(`editor:${kind}:${made}`)).not.toBeNull();
    expect((screen.getByTestId(`name-${kind}`) as HTMLInputElement).value).toMatch(/ ledger$/);
    expect(hub.posts).toEqual([path]);
  });

  it("New Thread opens a new Ask at once and makes no record (Betterment Q4)", async () => {
    // The thread is kept when its first question is answered (tests/unit/test_desk_ask.py).
    const before = useDesk.getState().refresh();
    await settle();
    await act(async () => { await press("desk.new-thread"); });
    expect(hub.posts).toEqual([]);
    expect(useDesk.getState().askOpen).toBe(true);
    expect(useDesk.getState().askThread?.threadId).toBeNull();
    expect(useDesk.getState().pullouts.some((p) => p.id.startsWith("thread:"))).toBe(false);
    await letReadsLand();
    await before;
  });

  it("the palette is the same door: New Knowledge, Enter, one POST and its window", async () => {
    // replaces: tests/e2e/test_new_verbs_open_glass.py::TestEveryNewVerbOpensItsWindow::test_a_new_verb_opens_its_window_at_once (the palette leg)
    render(<MemoryRouter><DeskToolShelf /><Desk /></MemoryRouter>);
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    await settle();
    const input = screen.getByRole("combobox", { name: "Search tools and Desk items" });
    fireEvent.change(input, { target: { value: "New Knowledge" } });
    await settle();
    const first = screen.getAllByRole("option").find((o) => o.className.includes("is-selected"));
    expect(first?.id).toBe("desk-palette-option-desk.new-knowledge");
    await act(async () => { fireEvent.keyDown(input, { key: "Enter" }); });
    await settle();
    expect(hub.posts).toEqual(["/api/kbs"]);
    const made = useDesk.getState().editingId!;
    expect(document.getElementById(`editor:kb:${made}`)).not.toBeNull();
    await letReadsLand();
  });
});

describe("two quick presses make one record", () => {
  it.each([
    ["desk.new-note", "/api/notes", "notes"],
    ["desk.new-knowledge", "/api/kbs", "kbs"],
  ] as const)("%s twice: one POST, one record, one window", async (id, path, bucket) => {
    // replaces: tests/e2e/test_new_verbs_open_glass.py::TestEveryNewVerbOpensItsWindow::test_two_quick_presses_make_one_record
    render(<Desk />);
    const kept = hub[bucket].length;
    await act(async () => { press(id); press(id); });
    await settle();
    await letReadsLand();
    expect(hub.posts).toEqual([path]);
    expect(hub[bucket].length).toBe(kept + 1);
    // A third press inside the NEW beat puts the same window in front: still one record.
    await act(async () => { press(id); });
    await settle();
    await letReadsLand();
    expect(hub.posts).toEqual([path]);
    const madeId = String(hub[bucket][hub[bucket].length - 1].id);
    expect(useDesk.getState().editingId).toBe(madeId);
    expect(document.querySelectorAll("[id^='editor:']")).toHaveLength(1);
  });
});

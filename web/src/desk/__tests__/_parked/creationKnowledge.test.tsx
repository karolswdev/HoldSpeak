/* PARKED (Betterment Q10 "Knowledge becomes drawers", 2026-10-19): the New
 * Knowledge tests of creation.app.test.tsx, as they were. New Knowledge left
 * the New list (desk/_parked/knowledge/newKnowledgeVerb.ts). Not compiled or
 * run (tsconfig and vitest exclude _parked). */
// @ts-nocheck
const EDITOR_VERBS = [["desk.new-knowledge", "/api/kbs", "kb"]] as const;
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

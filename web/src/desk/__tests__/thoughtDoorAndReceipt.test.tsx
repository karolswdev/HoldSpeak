/* HS-202-02 job 3 — `Write a thought` opens a note, and keeping one is
 * confirmed.
 *
 * 04-sober-eye.md Job 3 (PARTLY) and ranks 3 and 5:
 *  - "There is a button on the Desk labelled **Write a thought**. I clicked
 *    it. It does not open a place to write a thought. It opens the **Speak**
 *    window, which is a dictation-routing console"; the real door was
 *    `Desk → New Note`, nine moves away.
 *  - "**And nothing happened on screen.** No toast, no note object on the
 *    Desk … I only know it worked because I asked the API."
 */
import { afterEach, describe, expect, it, vi, beforeEach } from "vitest";
import { keptReceipt } from "../keptReceipt";
import { claimThoughtKeys, stopThoughtKeys } from "../thoughtKeys";

const apiFetch = vi.fn();
const openNoteThought = vi.fn();
const thoughtForNote = vi.fn();
const openPullout = vi.fn();
const refresh = vi.fn(async () => undefined);
const adoptCreated = vi.fn();
let storeNotes: Array<{ id: string; title: string; bodyMarkdown: string; createdAt: string }> = [];

const key = (k: string) => {
  const event = new KeyboardEvent("keydown", { key: k, bubbles: true, cancelable: true });
  document.body.dispatchEvent(event);
  return event;
};

vi.mock("../../lib/api", () => ({
  apiFetch: (...args: unknown[]) => apiFetch(...args),
  readableError: (e: unknown) => String(e),
}));
const reportWriteFailure = vi.fn();
const clearWriteFailure = vi.fn();
vi.mock("../hooks/useWriteReceipt", () => ({
  reportWriteFailure: (...args: unknown[]) => reportWriteFailure(...args),
  clearWriteFailure: (...args: unknown[]) => clearWriteFailure(...args),
}));
vi.mock("../thoughts", () => ({
  openNoteThought: (...args: unknown[]) => openNoteThought(...args),
  thoughtForNote: (...args: unknown[]) => thoughtForNote(...args),
}));
vi.mock("../store", () => ({
  useDesk: Object.assign(() => undefined, {
    getState: () => ({ openPullout, refresh, adoptCreated, items: { note: storeNotes } }),
  }),
}));

describe("New Note opens a note in the sticky (Betterment Q8: was Write a thought)", () => {
  beforeEach(() => {
    apiFetch.mockReset();
    openNoteThought.mockReset();
    thoughtForNote.mockReset();
    openPullout.mockReset();
    adoptCreated.mockReset();
    reportWriteFailure.mockReset();
    clearWriteFailure.mockReset();
    storeNotes = [];
  });

  afterEach(() => {
    vi.useRealTimers();
    stopThoughtKeys();
  });

  it("mints a note, opens it as a thought on the hub, and opens its window", async () => {
    apiFetch.mockResolvedValue({ note: { id: "note_1" } });
    openNoteThought.mockResolvedValue({ id: "th_1" });
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(apiFetch).toHaveBeenCalledWith(
      "/api/notes",
      expect.objectContaining({ method: "POST" }),
    );
    expect(openNoteThought).toHaveBeenCalledWith("note_1");
    expect(openPullout).toHaveBeenCalledWith("note:note_1");
    // The store takes the create answer first: the window does not wait
    // for a desk read (inventory 2026-10-03, A-apps row 31).
    expect(adoptCreated).toHaveBeenCalledWith("note", { id: "note_1" });
    expect(adoptCreated.mock.invocationCallOrder[0]).toBeLessThan(
      openPullout.mock.invocationCallOrder[0],
    );
  });

  /* Inventory 2026-10-03: "every press makes another note named Thought
     (six after one walk)". */
  it("uses the thought with no words again: no second note", async () => {
    storeNotes = [{ id: "note_empty", title: "Thought", bodyMarkdown: "", createdAt: "t1" }];
    thoughtForNote.mockResolvedValue({
      ownership: "thought",
      thought: { state: "working", working_note: { id: "note_empty", title: "Thought", body_markdown: "", tags: [] } },
    });
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(apiFetch).not.toHaveBeenCalled();
    expect(openPullout).toHaveBeenCalledWith("note:note_empty");
  });

  it("makes a new thought when the last one has words on the hub", async () => {
    // The store's copy is older than the save: the hub's record decides.
    storeNotes = [{ id: "note_old", title: "Thought", bodyMarkdown: "", createdAt: "t1" }];
    thoughtForNote.mockImplementation(async (id: string) => id === "note_old"
      ? { ownership: "thought", thought: { state: "working", working_note: { id, title: "Ask Priya", body_markdown: "Ask Priya", tags: [] } } }
      : { ownership: "ordinary", note: { id }, source_precondition: { content_sha256: "abc", last_modified: "t0" } });
    apiFetch.mockResolvedValue({ note: { id: "note_new" } });
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(apiFetch).toHaveBeenCalledTimes(1);
    expect(openPullout).toHaveBeenCalledWith("note:note_new");
  });

  /* Astra's condition on #790: `First thought`, at once Write a thought,
     `Second thought` gave one note `First thoughtSecond thought`. */
  it("saves a draft with unsaved words first and never uses it again", async () => {
    const { seatThoughtDraft } = await import("../thoughtDrafts");
    storeNotes = [{ id: "note_first", title: "Thought", bodyMarkdown: "", createdAt: "t1" }];
    const flush = vi.fn(async () => undefined);
    const release = seatThoughtDraft("note_first", { words: () => true, flush });
    // The hub still holds the empty record (the save is refused or late).
    thoughtForNote.mockImplementation(async (id: string) => id === "note_first"
      ? { ownership: "thought", thought: { state: "working", working_note: { id, title: "Thought", body_markdown: "", tags: [] } } }
      : { ownership: "ordinary", note: { id }, source_precondition: { content_sha256: "abc", last_modified: "t0" } });
    apiFetch.mockResolvedValue({ note: { id: "note_second" } });
    const { openNewThought } = await import("../newThought");

    await openNewThought();
    release();

    expect(flush).toHaveBeenCalledTimes(1);
    expect(flush.mock.invocationCallOrder[0]).toBeLessThan(apiFetch.mock.invocationCallOrder[0]);
    expect(openPullout).toHaveBeenCalledWith("note:note_second");
  });

  it("joins a second press to the one in flight: one note", async () => {
    apiFetch.mockResolvedValue({ note: { id: "note_once" } });
    thoughtForNote.mockRejectedValue(new Error("offline"));
    const { openNewThought } = await import("../newThought");

    await Promise.all([openNewThought(), openNewThought(), openNewThought()]);

    expect(apiFetch).toHaveBeenCalledTimes(1);
    expect(openPullout).toHaveBeenCalledTimes(1);
  });

  /* Astra's counsel finding 4 on PR #595: "Its catch returns without
     reporting anything… A refused POST therefore produces no visible
     result or retry." */
  it("names a refused create on the desk's failure channel, with a retry", async () => {
    apiFetch.mockRejectedValue(new Error("hub refused the write"));
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(reportWriteFailure).toHaveBeenCalledTimes(1);
    const [verb, cause, retry] = reportWriteFailure.mock.calls[0];
    expect(verb).toBe("New Note");
    expect(String(cause)).toContain("hub refused the write");
    expect(typeof retry).toBe("function");
    // Nothing is opened over a note that was never made.
    expect(openPullout).not.toHaveBeenCalled();
  });

  it("keeps the seed and in-flight keys through refusal, then claims the exact text once", async () => {
    let rejectCreate!: (cause: Error) => void;
    apiFetch.mockReturnValueOnce(new Promise((_resolve, reject) => { rejectCreate = reject; }));
    const take = vi.fn();
    const release = claimThoughtKeys("note_retry", take);
    const { openNewThought } = await import("../newThought");

    const attempt = openNewThought("First");
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    for (const character of " word") key(character);
    rejectCreate(new Error("hub refused the write"));
    await attempt;

    expect(reportWriteFailure).toHaveBeenCalledTimes(1);
    const retry = reportWriteFailure.mock.calls[0][2] as () => void;
    apiFetch.mockResolvedValueOnce({ note: { id: "note_retry" } });
    retry();
    retry();
    await vi.waitFor(() => expect(take).toHaveBeenCalledTimes(1));

    expect(take).toHaveBeenCalledWith("First word");
    expect(openPullout).toHaveBeenCalledWith("note:note_retry");
    expect(apiFetch).toHaveBeenCalledTimes(2);
    release();
  });

  it("restores the same text through a second refused retry", async () => {
    apiFetch
      .mockRejectedValueOnce(new Error("first refusal"))
      .mockRejectedValueOnce(new Error("second refusal"))
      .mockResolvedValueOnce({ note: { id: "note_again" } });
    const take = vi.fn();
    const release = claimThoughtKeys("note_again", take);
    const { openNewThought } = await import("../newThought");

    await openNewThought("Still here");
    expect(reportWriteFailure).toHaveBeenCalledTimes(1);
    (reportWriteFailure.mock.calls[0][2] as () => void)();
    await vi.waitFor(() => expect(reportWriteFailure).toHaveBeenCalledTimes(2));
    (reportWriteFailure.mock.calls[1][2] as () => void)();
    await vi.waitFor(() => expect(take).toHaveBeenCalledTimes(1));

    expect(take).toHaveBeenCalledWith("Still here");
    expect(apiFetch).toHaveBeenCalledTimes(3);
    release();
  });

  it("keeps the seed and captured gap keys when refusal arrives after the capture window", async () => {
    vi.useFakeTimers();
    let rejectCreate!: (cause: Error) => void;
    apiFetch.mockReturnValueOnce(new Promise((_resolve, reject) => { rejectCreate = reject; }));
    const take = vi.fn();
    const release = claimThoughtKeys("note_slow", take);
    const { openNewThought } = await import("../newThought");

    const attempt = openNewThought("Slow");
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    for (const character of " gap") key(character);
    vi.advanceTimersByTime(10_001);
    expect(key("late").defaultPrevented).toBe(false);

    rejectCreate(new Error("slow refusal"));
    await attempt;
    expect(reportWriteFailure).toHaveBeenCalledTimes(1);

    apiFetch.mockResolvedValueOnce({ note: { id: "note_slow" } });
    (reportWriteFailure.mock.calls[0][2] as () => void)();
    await vi.waitFor(() => expect(take).toHaveBeenCalledTimes(1));

    expect(take).toHaveBeenCalledWith("Slow gap");
    expect(openPullout).toHaveBeenCalledWith("note:note_slow");
    release();
  });

  it("delivers the captured text when success arrives after the capture window", async () => {
    vi.useFakeTimers();
    let resolveCreate!: (value: unknown) => void;
    apiFetch.mockReturnValueOnce(new Promise((resolve) => { resolveCreate = resolve; }));
    const take = vi.fn();
    const release = claimThoughtKeys("note_slow_success", take);
    const { openNewThought } = await import("../newThought");

    const attempt = openNewThought("Slow");
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    for (const character of " success") key(character);
    vi.advanceTimersByTime(10_001);
    expect(key("late").defaultPrevented).toBe(false);

    resolveCreate({ note: { id: "note_slow_success" } });
    await attempt;

    expect(reportWriteFailure).not.toHaveBeenCalled();
    expect(take).toHaveBeenCalledWith("Slow success");
    expect(openPullout).toHaveBeenCalledWith("note:note_slow_success");
    release();
  });

  it("keeps only the captured text when an editable field takes authority before refusal", async () => {
    let rejectCreate!: (cause: Error) => void;
    apiFetch.mockReturnValueOnce(new Promise((_resolve, reject) => { rejectCreate = reject; }));
    const take = vi.fn();
    const release = claimThoughtKeys("note_pointer", take);
    const input = document.createElement("input");
    document.body.append(input);
    const { openNewThought } = await import("../newThought");

    const attempt = openNewThought("Before");
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    for (const character of " gap") key(character);
    input.dispatchEvent(new Event("pointerdown", { bubbles: true }));
    for (const character of "other") {
      const event = new KeyboardEvent("keydown", { key: character, bubbles: true, cancelable: true });
      input.dispatchEvent(event);
      expect(event.defaultPrevented).toBe(false);
    }

    rejectCreate(new Error("pointer handoff refusal"));
    await attempt;
    apiFetch.mockResolvedValueOnce({ note: { id: "note_pointer" } });
    (reportWriteFailure.mock.calls[0][2] as () => void)();
    await vi.waitFor(() => expect(take).toHaveBeenCalledTimes(1));

    expect(take).toHaveBeenCalledWith("Before gap");
    expect(openPullout).toHaveBeenCalledWith("note:note_pointer");
    release();
  });

  it("delivers only pre-handoff text when an editable field takes authority before success", async () => {
    let resolveCreate!: (value: unknown) => void;
    apiFetch.mockReturnValueOnce(new Promise((resolve) => { resolveCreate = resolve; }));
    const take = vi.fn();
    const release = claimThoughtKeys("note_pointer_success", take);
    const input = document.createElement("input");
    document.body.append(input);
    const { openNewThought } = await import("../newThought");

    const attempt = openNewThought("Before");
    await vi.waitFor(() => expect(apiFetch).toHaveBeenCalledTimes(1));
    for (const character of " gap") key(character);
    input.dispatchEvent(new Event("pointerdown", { bubbles: true }));
    for (const character of "other") {
      const event = new KeyboardEvent("keydown", { key: character, bubbles: true, cancelable: true });
      input.dispatchEvent(event);
      expect(event.defaultPrevented).toBe(false);
    }

    resolveCreate({ note: { id: "note_pointer_success" } });
    await attempt;

    expect(reportWriteFailure).not.toHaveBeenCalled();
    expect(take).toHaveBeenCalledWith("Before gap");
    expect(openPullout).toHaveBeenCalledWith("note:note_pointer_success");
    release();
  });

  it("turns a successful response without a note id into a retryable failure", async () => {
    apiFetch
      .mockResolvedValueOnce({ note: { title: "Thought" } })
      .mockResolvedValueOnce({ note: { id: "note_recovered" } });
    const take = vi.fn();
    const release = claimThoughtKeys("note_recovered", take);
    const { openNewThought } = await import("../newThought");

    await openNewThought("Not dropped");
    expect(reportWriteFailure).toHaveBeenCalledTimes(1);
    expect(openPullout).not.toHaveBeenCalled();
    (reportWriteFailure.mock.calls[0][2] as () => void)();
    await vi.waitFor(() => expect(take).toHaveBeenCalledTimes(1));

    expect(take).toHaveBeenCalledWith("Not dropped");
    expect(openPullout).toHaveBeenCalledWith("note:note_recovered");
    expect(adoptCreated).toHaveBeenCalledTimes(1);
    release();
  });

  it("clears a standing failure once the create lands", async () => {
    clearWriteFailure.mockReset();
    apiFetch.mockResolvedValue({ note: { id: "note_3" } });
    thoughtForNote.mockRejectedValue(new Error("offline"));
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(clearWriteFailure).toHaveBeenCalled();
  });

  it("still opens the note when the adoption is refused", async () => {
    apiFetch.mockResolvedValue({ note: { id: "note_2" } });
    thoughtForNote.mockRejectedValue(new Error("offline"));
    const { openNewThought } = await import("../newThought");

    await openNewThought();

    expect(openPullout).toHaveBeenCalledWith("note:note_2");
  });
});

describe("keeping a note is confirmed (HS-202-02)", () => {
  it("states the time it was kept", () => {
    const at = new Date("2026-09-20T15:41:00").getTime();
    expect(keptReceipt(at)).toMatch(/^Kept · /);
    expect(keptReceipt(at)).toMatch(/\d/);
  });

  it("says nothing before the first keep", () => {
    expect(keptReceipt(undefined)).toBeNull();
    expect(keptReceipt(0)).toBeNull();
  });
});

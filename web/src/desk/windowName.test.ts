import { describe, expect, it } from "vitest";
import { kindWord, looksLikeId, shownNames, windowName } from "./windowName";

describe("windowName: the name of the thing in the window", () => {
  it("thought: the owner's title, else its first words, else New thought", () => {
    expect(windowName({ kind: "thought", title: "Ledger cutover: rollback plan", body: "Other words" }))
      .toBe("Ledger cutover: rollback plan");
    expect(windowName({ kind: "thought", title: "Thought", body: "# Ask Priya whether the ledger is frozen\nmore" }))
      .toBe("Ask Priya whether the ledger is frozen");
    expect(windowName({ kind: "thought", title: "", body: "" })).toBe("New thought");
    expect(windowName({ kind: "thought", title: "Thought", body: "" })).toBe("New thought");
  });

  it("thought: the title follows the draft while the kept title is only the kept first words", () => {
    expect(windowName({ kind: "thought", title: "Ask Priya", body: "Ask Priya about the freeze", keptBody: "Ask Priya" }))
      .toBe("Ask Priya about the freeze");
    // A title the owner typed stays, whatever the note says.
    expect(windowName({ kind: "thought", title: "My plan", body: "Ask Priya about the freeze", keptBody: "Ask Priya" }))
      .toBe("My plan");
  });

  it("note, thread, decision: the title, else first words, else New <kind>; never an id", () => {
    expect(windowName({ kind: "note", title: "Runbook", body: "x" })).toBe("Runbook");
    expect(windowName({ kind: "note", title: "", body: "- Check the queue depth" })).toBe("Check the queue depth");
    expect(windowName({ kind: "note", title: "", body: "" })).toBe("New note");
    expect(windowName({ kind: "note", title: "note-3f9a12bc77", body: "" }, "note-3f9a12bc77")).toBe("New note");
    expect(windowName({ kind: "thread", title: "", firstMessage: "What changed in the ledger?" }))
      .toBe("What changed in the ledger?");
    expect(windowName({ kind: "thread", title: "th_9f8a7b6c5d4e", firstMessage: "" })).toBe("New thread");
    expect(windowName({ kind: "thread", title: null })).toBe("New thread");
    expect(windowName({ kind: "decision", title: "", text: "Freeze the ledger on Friday" }))
      .toBe("Freeze the ledger on Friday");
    expect(windowName({ kind: "decision", title: "Use Postgres" })).toBe("Use Postgres");
  });

  it("meeting: its title, else Meeting and the local day and time", () => {
    expect(windowName({ kind: "meeting", title: "Ledger review", startedAt: "2026-10-03T21:06:00" })).toBe("Ledger review");
    expect(windowName({ kind: "meeting", title: "", startedAt: "2026-10-03T21:06:00" })).toBe("Meeting, Oct 3, 21:06");
    expect(windowName({ kind: "meeting", title: "", startedAt: null })).toBe("Meeting");
  });

  it("knowledge, project, session, settings, calendar, dossier", () => {
    expect(windowName({ kind: "knowledge", name: "" })).toBe("New knowledge base");
    expect(windowName({ kind: "knowledge", name: "kb_12ab34cd56" }, "kb_12ab34cd56")).toBe("New knowledge base");
    expect(windowName({ kind: "knowledge", name: "Payments docs" })).toBe("Payments docs");
    expect(windowName({ kind: "project", name: "Payments ledger" })).toBe("Payments ledger");
    expect(windowName({ kind: "session", task: "Fix the cutover script", project: "Payments ledger", agent: "claude" }))
      .toBe("Fix the cutover script");
    expect(windowName({ kind: "session", project: "Payments ledger", agent: "claude" })).toBe("Payments ledger");
    expect(windowName({ kind: "session", agent: "claude" })).toBe("claude");
    expect(windowName({ kind: "settings", section: "Connections" })).toBe("Settings · Connections");
    expect(windowName({ kind: "settings" })).toBe("Settings");
    expect(windowName({ kind: "calendar", name: "Work" })).toBe("Calendar snapshot · Work");
    expect(windowName({ kind: "calendar" })).toBe("Calendar snapshot");
    expect(windowName({ kind: "dossier", title: "The naming rule" })).toBe("The naming rule");
  });

  it("an id is not a name; words are", () => {
    expect(looksLikeId("th_9f8a7b6c5d4e")).toBe(true);
    expect(looksLikeId("note-3f9a12bc")).toBe(true);
    expect(looksLikeId("anything", "anything")).toBe(true);
    expect(looksLikeId("Ledger cutover")).toBe(false);
    expect(looksLikeId("follow-up")).toBe(false);
    expect(looksLikeId("Q3-planning")).toBe(false);
  });
});

describe("shownNames: the kind goes first only when names collide", () => {
  it("no collision: no kind word", () => {
    const shown = shownNames([
      { id: "a", name: "Ledger cutover: rollback plan", kind: "Thought" },
      { id: "b", name: "New thought", kind: "Thought" },
      { id: "c", name: "Delivery" },
    ]);
    expect([...shown.values()]).toEqual(["Ledger cutover: rollback plan", "New thought", "Delivery"]);
  });

  it("the same name in two open windows: each puts its kind first", () => {
    const shown = shownNames([
      { id: "a", name: "Ledger cutover: rollback plan", kind: "Thought" },
      { id: "b", name: "ledger cutover: rollback plan ", kind: "Note" },
      { id: "c", name: "Other", kind: "Note" },
    ]);
    expect(shown.get("a")).toBe("Thought · Ledger cutover: rollback plan");
    expect(shown.get("b")).toBe("Note · ledger cutover: rollback plan ");
    expect(shown.get("c")).toBe("Other");
  });

  it("kindWord reads as a word", () => {
    expect(kindWord("note")).toBe("Note");
    expect(kindWord("agent_session")).toBe("Agent session");
  });
});

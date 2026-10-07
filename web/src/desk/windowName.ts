/* A window's title is the name of the thing in it (owner ratified 2026-10-04).
 *
 * ONE function names every window family. The frame gives that one name to
 * the window registry, and the title bar, the Dock chip, the 393 screen
 * title, the switcher list, the Window menu and the swipe ring all read it.
 * Names are for display only: a window's id never changes with its name.
 *
 * - The owner's own title wins. With no title, the first words of the thing
 *   are its name. With no words, the name is `New <kind>`.
 * - A raw id is never a name.
 * - Two open windows with the same name put their kind first
 *   (`Thought · <name>`, `Note · <name>`). All other windows show no kind. */
import { firstWords, NEW_THOUGHT_TITLE } from "./thoughtTitle";
import { wireDayClock } from "./surface/format";

/** The record a window shows. Every field is optional text from the wire. */
export type WindowSubject =
  | { kind: "thought"; title?: string | null; body?: string | null; keptBody?: string | null }
  | { kind: "note"; title?: string | null; body?: string | null }
  | { kind: "thread"; title?: string | null; firstMessage?: string | null }
  | { kind: "meeting"; title?: string | null; startedAt?: unknown }
  | { kind: "decision"; title?: string | null; text?: string | null }
  | { kind: "knowledge"; name?: string | null }
  | { kind: "project"; name?: string | null }
  | { kind: "session"; project?: string | null; task?: string | null; agent?: string | null }
  /** PHILO-14 C2: a launched agent's lane, `<Agent>: <item>`. */
  | { kind: "lane"; agent?: string | null; item?: string | null }
  | { kind: "settings"; section?: string | null }
  | { kind: "calendar"; name?: string | null }
  | { kind: "dossier"; title?: string | null };

const text = (value: unknown): string => (typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "");

/** Text that is an id of a record, not a name a person gave. */
export function looksLikeId(value: string, id?: string | null): boolean {
  const v = value.trim();
  if (!v) return false;
  if (id && v === String(id).trim()) return true;
  // The hub's ids: `note_624495deb1f5`, `th_9f8a7b6c5d4e`, or a UUID.
  return /^[a-z]{1,12}_[0-9a-f]{8,}$/i.test(v)
    || /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(v);
}

/** The title a person gave: not empty and not the record's id. */
export function ownTitle(value: unknown, id?: string | null): string {
  const v = text(value);
  return v && !looksLikeId(v, id) ? v : "";
}

/** The name of the thing in a window. Never empty, never an id. */
export function windowName(subject: WindowSubject, id?: string | null): string {
  const named = (value: unknown): string => {
    const v = text(value);
    return v && !looksLikeId(v, id) ? v : "";
  };
  switch (subject.kind) {
    case "thought": {
      const title = named(subject.title);
      // `Thought` is the stored name of a thought with no title; the first
      // words of the kept note are a title the save rule gave, not the owner.
      const own = title && title !== NEW_THOUGHT_TITLE
        && (subject.keptBody == null || title !== firstWords(subject.keptBody));
      return own ? title : firstWords(subject.body ?? "") || "New thought";
    }
    case "note": {
      // A note that holds the stored word `Thought` is a thought with no
      // title of its own: the word is not a name.
      if (text(subject.title) === NEW_THOUGHT_TITLE)
        return firstWords(subject.body ?? "") || "New thought";
      return named(subject.title) || firstWords(subject.body ?? "") || "New note";
    }
    case "thread":
      return named(subject.title) || firstWords(subject.firstMessage ?? "") || "New thread";
    case "meeting": {
      const when = wireDayClock(subject.startedAt);
      return named(subject.title) || (when ? `Meeting, ${when}` : "Meeting");
    }
    case "decision":
      return named(subject.title) || firstWords(subject.text ?? "") || "New decision";
    case "knowledge":
      return named(subject.name) || "New knowledge base";
    case "project":
      return named(subject.name) || "Project";
    case "session":
      return named(subject.task) || named(subject.project) || named(subject.agent) || "Agent session";
    case "lane": {
      const agent = named(subject.agent) || "Agent";
      const item = named(subject.item);
      return item ? `${agent}: ${item}` : agent;
    }
    case "settings":
      return named(subject.section) ? `Settings · ${named(subject.section)}` : "Settings";
    case "calendar":
      return named(subject.name) ? `Calendar snapshot · ${named(subject.name)}` : "Calendar snapshot";
    case "dossier":
      return named(subject.title) || "Dossier";
  }
}

/** The name of a Desk primitive (a note, a thread, a meeting, …) from its
 * record: what its window, its palette row and its Floor object show. Never
 * empty, never the record's id. */
export function primitiveName(kind: string, record: unknown, id?: string | null, words?: string | null): string {
  const r = (record && typeof record === "object" ? record : {}) as Record<string, unknown>;
  const s = (key: string) => (typeof r[key] === "string" ? (r[key] as string) : "");
  switch (kind) {
    case "note": return windowName({ kind: "note", title: s("title"), body: s("bodyMarkdown") }, id);
    // An untitled thread's `title` is the name the mapper gave (`New
    // thread`), not a title: the first message names it when there is one.
    case "thread": return windowName({ kind: "thread", title: r.untitled === true ? "" : s("title"), firstMessage: words ?? "" }, id);
    case "meeting": return windowName({ kind: "meeting", title: s("title"), startedAt: r.startedAt }, id);
    case "decision": return windowName({ kind: "decision", title: s("title"), text: s("decisionMarkdown") }, id);
    case "kb": return windowName({ kind: "knowledge", name: s("name") || s("title") }, id);
    case "project": return windowName({ kind: "project", name: s("name") || s("title") }, id);
    default: {
      const own = text(s("title")) || text(s("name"));
      return own && own !== String(id ?? "").trim() ? own : kindWord(kind) || "Object";
    }
  }
}

/** The kind word that goes first when two windows have the same name. */
export function kindWord(kind: string): string {
  const k = kind.replace(/[_-]+/g, " ").trim();
  return k ? k.charAt(0).toUpperCase() + k.slice(1) : "";
}

/** The name each open window shows. A name that two or more open windows
 * have gets its kind first; a window with no kind word keeps its name. */
export function shownNames<T extends { id: string; name: string; kind?: string }>(
  windows: readonly T[],
): Map<string, string> {
  const key = (name: string) => name.trim().toLowerCase();
  const count = new Map<string, number>();
  for (const w of windows) count.set(key(w.name), (count.get(key(w.name)) ?? 0) + 1);
  const out = new Map<string, string>();
  for (const w of windows)
    out.set(w.id, w.kind && (count.get(key(w.name)) ?? 0) > 1 ? `${w.kind} · ${w.name}` : w.name);
  return out;
}

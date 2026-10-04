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
  | { kind: "settings"; section?: string | null }
  | { kind: "calendar"; name?: string | null }
  | { kind: "dossier"; title?: string | null };

const text = (value: unknown): string => (typeof value === "string" ? value.replace(/\s+/g, " ").trim() : "");

/** Text that is an id of a record, not a name a person gave. */
export function looksLikeId(value: string, id?: string | null): boolean {
  const v = value.trim();
  if (!v) return false;
  if (id && v === String(id).trim()) return true;
  return /^[a-z]{1,10}[_-][0-9a-z_-]{6,}$/i.test(v) && /\d/.test(v) && !/\s/.test(v);
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
    case "note":
      return named(subject.title) || firstWords(subject.body ?? "") || "New note";
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
    case "settings":
      return named(subject.section) ? `Settings · ${named(subject.section)}` : "Settings";
    case "calendar":
      return named(subject.name) ? `Calendar snapshot · ${named(subject.name)}` : "Calendar snapshot";
    case "dossier":
      return named(subject.title) || "Dossier";
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

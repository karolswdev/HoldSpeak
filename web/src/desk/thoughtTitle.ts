/* PHILO-13-16 (C6) — a thought is titled from its first words.
 *
 * Every new thought was born `Thought` (newThought.ts) and kept that name,
 * so the Chair showed `Thought ×3` and the palette five identical rows
 * (grounding/faces-jobs.md F8). The writer asks this rule on every save: an
 * untitled thought takes the first words of its note. A title the owner
 * typed himself is his, and the rule leaves it alone. */

/** The name a new thought carries before it has words. */
export const NEW_THOUGHT_TITLE = "Thought";

const MAX_TITLE = 60;
const LINE_MARK = /^\s*(?:#{1,6}\s+|[-*+>]\s+|\d+[.)]\s+|\[[ xX]\]\s+)*/;

/** The first words of a note: its first line with words, without the
 * Markdown mark that starts it, at most 60 characters (cut at a word). */
export function firstWords(body: string): string {
  const line = body
    .split(/\r?\n/)
    .map((raw) => raw.replace(LINE_MARK, "").replace(/\s+/g, " ").trim())
    .find(Boolean) ?? "";
  if (line.length <= MAX_TITLE) return line;
  const cut = line.slice(0, MAX_TITLE + 1);
  const space = cut.lastIndexOf(" ");
  return `${(space > MAX_TITLE / 3 ? cut.slice(0, space) : line.slice(0, MAX_TITLE)).trim()}…`;
}

/** The title a save sends. `title` is the draft's; `kept` is the note the hub
 * holds now. While the thought is untitled (its kept title is the new-thought
 * name, empty, or the first words of its kept note) and the owner has not
 * changed the title, the title is the first words of the note being saved. */
export function thoughtTitle(
  title: string,
  kept: { title: string; body_markdown: string },
  body: string,
): string {
  if (title !== kept.title) return title;
  const untitled =
    !kept.title.trim() ||
    kept.title === NEW_THOUGHT_TITLE ||
    kept.title === firstWords(kept.body_markdown);
  if (!untitled) return title;
  return firstWords(body) || title;
}

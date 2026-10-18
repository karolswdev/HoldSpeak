/** The palette's ranking (HS-111-07, HS-202-02, PHILO-13-14, Betterment A1),
 * shared by Search (DeskToolShelf) and the About picker (Betterment A5), so a
 * name is found the same way in both. Pure: no store, no DOM. */

/** One word, one form.
 *
 * HS-202-02 — a person types the plural the screen shows them ("Notes",
 * "Thoughts", "Meetings"); the row that carries the verb is singular
 * ("New Note", "New Thought"). Without this fold the typed word scored
 * ZERO against its own row, so `Notes` highlighted `Telegram control` and
 * `Thoughts` highlighted `Intelligence` — and Enter opened those
 * (03-interaction-walk.md finding 6: two of the five owner jobs could not
 * be started by keyboard). */
export function stem(word: string): string {
  if (word.length > 3 && word.endsWith("ies")) return `${word.slice(0, -3)}y`;
  if (word.length > 4 && /(s|x|z|ch|sh)es$/.test(word)) return word.slice(0, -2);
  if (word.length > 2 && word.endsWith("s") && !word.endsWith("ss"))
    return word.slice(0, -1);
  return word;
}

export function fuzzyScore(query: string, target: string): number {
  const q = query.toLowerCase();
  const t = target.toLowerCase();
  if (t === q) return 100;
  if (t.startsWith(q)) return 80;
  const words = t.split(/[\s\-_]+/);
  if (words.some((word) => word.startsWith(q))) return 60;
  // The fold is tried ONLY when the literal forms did not already meet at
  // a word boundary, so every rank the deck already proved is unchanged.
  const qs = stem(q);
  if (qs !== q || words.some((word) => stem(word) !== word)) {
    const stemmed = words.map(stem);
    const ts = stemmed.join(" ");
    if (ts === qs) return 90;
    if (ts.startsWith(qs)) return 75;
    if (qs.length > 2 && stemmed.some((word) => word.startsWith(qs))) return 65;
  }
  // The scattered-letter match stays inside ONE word (`mgs` finds
  // Meetings). Across words it found the letters of almost any long label:
  // `send` matched "Close window" (s-e in close, n-d in window) and a dozen
  // other rows that have nothing to do with sending (STATUS: noise rows).
  // A query of several words matches word by word ("payments cutover"
  // finds "Payments ledger cutover").
  const within = (part: string) => (word: string) => {
    let qi = 0;
    for (let ti = 0; ti < word.length && qi < part.length; ti++) {
      if (word[ti] === part[qi]) qi++;
    }
    return qi === part.length;
  };
  const parts = q.split(/\s+/).filter(Boolean);
  if (parts.length > 1 && parts.every((part) => words.some((word) => word.startsWith(part)))) return 55;
  if (parts.length > 0 && parts.every((part) => words.some(within(part)))) return 30;
  if (t.includes(q)) return 20;
  return 0;
}

/** PHILO-13-14 (C4) — a match inside a body: every query word starts a word
 * of the text (the plural fold applies). Never a scattered-letter or
 * mid-word match: over a long body those find almost everything. Below a
 * label's word match (60), so a title still leads. */
export function wordScore(query: string, text: string | undefined): number {
  const q = query.trim().toLocaleLowerCase();
  if (q.length < 3 || !text) return 0;
  const words = text.toLocaleLowerCase().split(/[^\p{L}\p{N}:']+/u).filter(Boolean);
  if (!words.length) return 0;
  const stems = words.map(stem);
  const hit = (w: string) =>
    words.some((x) => x.startsWith(w)) || (w.length > 2 && stems.some((x) => x.startsWith(stem(w))));
  return q.split(/\s+/).every(hit) ? 50 : 0;
}

/** Fuzzy relevance with a recency boost; 0 = no match. */
export function rankRow(
  row: { label: string; terms?: string; body?: string; name?: string; kindWord?: string },
  query: string,
  recent: boolean,
  recentBoostsEmpty = false,
): number {
  if (!query) return recent && recentBoostsEmpty ? 2 : 1;
  // Betterment A1: the name matches in either number ("automation" finds the
  // Automations program at 100, so the program leads the objects of that kind).
  const name = row.name?.toLocaleLowerCase();
  const asked = query.toLocaleLowerCase();
  const named = name && (name === asked || stem(name) === stem(asked)) ? 100 : 0;
  const score = Math.max(
    named,
    fuzzyScore(query, row.label),
    fuzzyScore(query, row.terms ?? ""),
    wordScore(query, row.body),
    // Betterment A1: an object's kind word ("automation") is a weak match,
    // below a word of its title, so the program of that name leads it.
    fuzzyScore(query, row.kindWord ?? "") ? 50 : 0,
  );
  return score ? score + (recent ? 10 : 0) : 0;
}

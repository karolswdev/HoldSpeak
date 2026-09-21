/* HS-202-02 job 3 — a keep says so.
 *
 * 04-sober-eye.md, rank 5: "The note saved correctly and the screen showed
 * nothing at all — no toast, no object, no arrival entry. I had to query
 * the API to learn it had worked."
 *
 * The inline editor writes through a 450 ms debounce
 * (`pullouts/editors/useDebouncedSave.ts`), so the note is kept as the
 * owner types. The foot states WHEN, in the word HS-201-12 settled for
 * this: "Kept".
 */
export function keptReceipt(at: number | undefined | null): string | null {
  if (!at) return null;
  const when = new Date(at);
  if (Number.isNaN(when.getTime())) return null;
  return `Kept · ${when.toLocaleTimeString([], {
    hour: "numeric",
    minute: "2-digit",
  })}`;
}

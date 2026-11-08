/** The Desk decision the Decisions window reader shows (2026-11-08): the one
 *  face of a decision is that reader, so the window's Object menu is that
 *  decision's (`objectMenu.ts` `windowObjectRef`). The reader sets it while a
 *  record made from a Desk decision is on screen and clears it after; a record
 *  a meeting made has no Desk decision and no Object menu. One Decisions
 *  window exists (`surface-decisions`), so one slot holds it. */
let shown: string | null = null;

/** The reader shows this Desk decision (its id), or none. */
export function setDecisionReaderObject(deskDecisionId: string | null): void {
  const id = String(deskDecisionId ?? "").trim();
  shown = id || null;
}

/** The desk ref (`decision:<id>`) of the Desk decision the reader shows. */
export function decisionReaderObject(): string | null {
  return shown ? `decision:${shown}` : null;
}

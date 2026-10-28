/** W6 (atlas pass 3, defect 18): the Decisions reader's Edit opens a Desk
 *  decision's own window in its editor. A request made before the window
 *  mounts is kept here (the window takes it as it mounts); an open window
 *  hears the event at once. */
const editRequests = new Set<string>();

export const DECISION_EDIT_EVENT = "holdspeak:decision-edit";

export function requestDecisionEdit(id: string): void {
  editRequests.add(id);
  if (typeof window !== "undefined") window.dispatchEvent(new CustomEvent(DECISION_EDIT_EVENT, { detail: id }));
}

/** True once per request: the window that takes it opens its editor. */
export function takeDecisionEditRequest(id: string): boolean {
  return editRequests.delete(id);
}

/** Whether a request waits for this window (the window's first draw). */
export function hasDecisionEditRequest(id: string): boolean {
  return editRequests.has(id);
}

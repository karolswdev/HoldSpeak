/** Return-to-task (HS-200-41) — the FOCUS half.
 *
 *  The state half already ships: a face holding unfinished work listens for
 *  `holdspeak:settings-updated` and re-reads its own readiness without a
 *  reload (`SpeakFace.tsx`, `ThoughtWorkspaceWindow.tsx`). What was missing
 *  is the other half of the ratified behaviour (design D2(a) "Focus
 *  return"): *"`Set up model` opens the Concierge window; on its `Apply` the
 *  window closes, the ask well refreshes readiness WITHOUT a reload, and
 *  focus returns to `Prepare`."*
 *
 *  Two precedents, and this module follows both rather than inventing a
 *  third: `Popover.tsx:30,33-44` saves `document.activeElement` and restores
 *  it, and `DeskMenu.tsx:33,47,112` establishes the `returnFocus?: () =>
 *  void` contract. Same spelling here.
 *
 *  ── The do-not-steal rule ──────────────────────────────────────────────
 *  Restoring focus is only correct while the owner is still *coming back*.
 *  If he has moved on — clicked into another field, started typing
 *  somewhere else — yanking the caret is a bug, not a courtesy. So a
 *  restore happens only when BOTH hold:
 *
 *  1. The remembered verb is still connected to the document and still
 *     focusable (not `disabled`, not `hidden`). A verb that unmounted while
 *     he was away is not a place to send him.
 *  2. Focus is UNCLAIMED at the moment of return: nothing is focused, or
 *     the body/root holds it (what an unmounting setup surface leaves
 *     behind), or the focused element has been detached, or focus still
 *     rests on the very control that finished the setup (`from`, captured
 *     synchronously when the setup verb was pressed — after an `await` it
 *     is already too late to tell his hand from the DOM's).
 *
 *  Anything else means he chose somewhere else, and the return is dropped.
 */

/** The one signal both halves ride. Faces holding an unfinished task
 *  re-read on it instead of reloading and losing the work. */
export const RETURN_TO_TASK_EVENT = "holdspeak:settings-updated";

/** The verb the owner left, and how long it stays worth returning to. */
const STALE_AFTER_MS = 10 * 60 * 1000;

let pending: { element: HTMLElement; at: number } | null = null;

function isFocusable(element: HTMLElement): boolean {
  if (!element.isConnected) return false;
  if (element.hasAttribute("disabled")) return false;
  if (element.getAttribute("aria-hidden") === "true") return false;
  if (element.hidden) return false;
  return typeof element.focus === "function";
}

/** Remember the verb the owner is leaving, before the handoff opens the
 *  setup surface. Call it from the handler that opens Models/Settings —
 *  synchronously, so `document.activeElement` is still his verb. */
export function rememberTaskFocus(element?: HTMLElement | null): void {
  if (typeof document === "undefined") return;
  const target =
    element ?? (document.activeElement as HTMLElement | null) ?? null;
  if (!target || target === document.body || !isFocusable(target)) {
    pending = null;
    return;
  }
  pending = { element: target, at: Date.now() };
}

/** Drop the pending return (the task itself went away). */
export function forgetTaskFocus(): void {
  pending = null;
}

/** Whether a return is currently owed — for a face that wants to say so. */
export function taskFocusPending(): boolean {
  return pending !== null;
}

/** True when nobody has laid claim to focus since the handoff. See the
 *  do-not-steal rule above; `from` is the control that finished setup. */
function focusIsUnclaimed(from?: HTMLElement | null): boolean {
  if (typeof document === "undefined") return false;
  const active = document.activeElement as HTMLElement | null;
  if (!active) return true;
  if (active === document.body || active === document.documentElement) return true;
  if (!active.isConnected) return true;
  if (from && (active === from || from.contains(active))) return true;
  return false;
}

/** Consume the pending return and put focus back on the verb the owner
 *  left. Idempotent: a second call after a restore does nothing. Returns
 *  whether focus actually moved, so a test can assert the refusal too. */
export function returnToTask(from?: HTMLElement | null): boolean {
  const owed = pending;
  if (!owed) return false;
  pending = null;
  if (Date.now() - owed.at > STALE_AFTER_MS) return false;
  if (!isFocusable(owed.element)) return false;
  if (!focusIsUnclaimed(from)) return false;
  owed.element.focus();
  return true;
}

/** The dispatcher's one call: announce that readiness changed, then hand
 *  focus back. The announcement is synchronous (every subscriber re-reads
 *  on it); the focus return waits a frame so the faces that re-render on
 *  the event — and the setup surface that closes on it — have settled
 *  before we look at who holds focus.
 *
 *  `from` is the control the owner pressed to finish setup, captured
 *  synchronously by the caller BEFORE its await. */
export function announceTaskReturn(from?: HTMLElement | null): void {
  if (typeof window === "undefined") return;
  try {
    window.dispatchEvent(new Event(RETURN_TO_TASK_EVENT));
  } catch {
    // A page without a working event target still applied the set.
  }
  const restore = () => {
    returnToTask(from);
  };
  if (typeof window.requestAnimationFrame === "function")
    window.requestAnimationFrame(restore);
  else window.setTimeout(restore, 0);
}

/** The consumer's one call: re-read on the signal. Returns the
 *  unsubscribe, so an effect can `return onReturnToTask(...)`. */
export function onReturnToTask(handler: () => void): () => void {
  if (typeof window === "undefined") return () => undefined;
  window.addEventListener(RETURN_TO_TASK_EVENT, handler);
  return () => window.removeEventListener(RETURN_TO_TASK_EVENT, handler);
}

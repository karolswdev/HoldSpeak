/* The keys typed between `Write a thought` and the Thought window.
 *
 * The press opens a window that is not there yet: the note is made (or the
 * empty one is found), then the window loads it. The owner types at once
 * (⌃T, then the words). Before, the keys of that gap went to the page and
 * were lost (inventory 2026-10-03, A-apps row 31).
 *
 * `startThoughtKeys` keeps the typed text from the press; the Thought
 * window's note field takes it when it is ready (`claimThoughtKeys`), with
 * the cursor after it, so the next key continues the same line. The keeping
 * stops when the field takes the text, when the owner presses in another
 * field, or after ten seconds. A field that only still has the focus from
 * before the press (the last thought's note, after the menu closed) does not
 * get the keys: the press asked for a new thought. */

const KEEP_MS = 10_000;

let kept: string | null = null;
let wanted: string | null = null;
let wantedText: string | null = null;
let timer: number | null = null;
let remember: ((text: string) => void) | null = null;
const fields = new Map<string, (text: string) => void>();

function keep(text: string): void {
  kept = text;
  remember?.(text);
}

function editable(target: EventTarget | null): boolean {
  return target instanceof HTMLElement &&
    target.matches("input, textarea, select, [contenteditable]:not([contenteditable=false])");
}

function onKeyDown(event: KeyboardEvent): void {
  if (kept === null || event.isComposing) return;
  if (event.metaKey || event.ctrlKey || event.altKey) return;
  let next: string;
  if (event.key.length === 1) next = kept + event.key;
  else if (event.key === "Enter") next = `${kept}\n`;
  else if (event.key === "Backspace") next = kept.slice(0, -1);
  else return;
  keep(next);
  event.preventDefault();
  event.stopPropagation();
}

/** The owner pressed in a field: the keys are that field's from now. */
function onPointerDown(event: PointerEvent): void {
  if (kept !== null && editable(event.target)) stopThoughtKeys();
}

function onKeyUp(event: KeyboardEvent): void {
  // A kept Space must not press the button that still has the focus.
  if (kept === null) return;
  if (event.key === " " || event.key === "Enter") {
    event.preventDefault();
    event.stopPropagation();
  }
}

/** Stop keeping keys; whatever was kept is dropped. */
export function stopThoughtKeys(): void {
  kept = null;
  wanted = null;
  wantedText = null;
  remember = null;
  if (timer !== null) window.clearTimeout(timer);
  timer = null;
  window.removeEventListener("keydown", onKeyDown, true);
  window.removeEventListener("keyup", onKeyUp, true);
  window.removeEventListener("pointerdown", onPointerDown, true);
}

/** Take the buffered text at an attempt boundary and stop intercepting keys.
 * The caller owns the returned text for that attempt's retry only. A caller
 * may supply its attempt snapshot when the ten-second window or an editable
 * pointerdown already stopped interception. */
export function takeThoughtKeys(snapshot = ""): string {
  const text = kept ?? snapshot;
  stopThoughtKeys();
  return text;
}

/** Keep every typed key from now (the press of `Write a thought`).
 *  `seed`: words already typed before the keeping began (Capture's New note
 *  makes its note on the first character, betterment C8). */
export function startThoughtKeys(seed = "", onText?: (text: string) => void): void {
  if (kept !== null) {
    if (seed) keep(seed + kept);
    return;
  }
  remember = onText ?? null;
  keep(seed);
  wanted = null;
  wantedText = null;
  window.addEventListener("keydown", onKeyDown, true);
  window.addEventListener("keyup", onKeyUp, true);
  window.addEventListener("pointerdown", onPointerDown, true);
  timer = window.setTimeout(stopThoughtKeys, KEEP_MS);
}

function deliver(noteId: string): boolean {
  const take = fields.get(noteId);
  if (!take || (kept === null && wantedText === null)) return false;
  const text = kept ?? wantedText ?? "";
  stopThoughtKeys();
  take(text);
  return true;
}

/** The thought's note is known: its field takes the kept keys, now or when
 * the window has loaded. A failed/expired capture may pass its attempt-local
 * snapshot for this note only; this never starts keyboard interception again. */
export function sendThoughtKeysTo(noteId: string, snapshot?: string): void {
  if (kept === null && snapshot === undefined) return;
  wanted = noteId;
  wantedText = snapshot ?? null;
  deliver(noteId);
}

/** The note field of an open Thought window. `take` gets the kept text
 * (it can be empty) and puts the cursor in the field. */
export function claimThoughtKeys(noteId: string, take: (text: string) => void): () => void {
  fields.set(noteId, take);
  if (wanted === noteId) deliver(noteId);
  return () => {
    if (fields.get(noteId) === take) fields.delete(noteId);
  };
}

/** HS-111-07 - the ONE key binder (doctrine P11): the registry's `key`
 * fields are the truth and this module is the only document-level
 * keydown that runs verbs. The hand-rolled listeners that lived in
 * DeskWindow (⌘1-4/⌘W/⌘M/⌘/, ⌃`) and DeskToolShelf (⌘K) are gone -
 * they were parallel binders over the same verbs. */
import { useEffect } from "react";
import { useDesk } from "./store";
import { VERBS, type Verb, type VerbContext } from "./verbRegistry";

export interface KeySpec {
  meta: boolean;
  ctrl: boolean;
  shift?: boolean;
  plain: boolean;
  key: string;
}

/** ⌘-notation → matchable spec. Display strings stay ⌘-notation; only
 * this module reads them as bindings. */
export function parseKey(cap: string): KeySpec | null {
  const meta = cap.startsWith("⌘");
  const ctrl = cap.startsWith("⌃");
  const plain = cap === "Delete";
  if (!meta && !ctrl && !plain) return null;
  const rest = plain ? cap : cap.slice(1);
  const shift = rest.startsWith("⇧");
  const chord = shift ? rest.slice(1) : rest;
  const key = chord === "↑" ? "ArrowUp" : chord.toLocaleLowerCase();
  if (!key) return null;
  return { meta, ctrl, plain, ...(shift ? { shift: true } : {}), key };
}

/** Plain-letter chords stay quiet while the user is typing (the HS-101
 * rule: ⌘W/⌘M never eat a word in a field). */
const TYPING_GUARDED = new Set(["w", "m"]);

function typing(target: EventTarget | null): boolean {
  const el = target as HTMLElement | null;
  return Boolean(
    el &&
      (el.tagName === "INPUT" ||
        el.tagName === "TEXTAREA" ||
        el.isContentEditable ||
        el.closest("[contenteditable='true']")),
  );
}

export function matchKey(e: KeyboardEvent, spec: KeySpec): boolean {
  // ⌘ means the PRIMARY modifier: meta on a Mac, ctrl elsewhere (the
  // pre-keymap ⌘K accepted both; the grammar keeps that reach).
  const primary =
    (e.metaKey || e.ctrlKey) && !(e.metaKey && e.ctrlKey) && !e.altKey;
  if (spec.meta && !primary) return false;
  if (spec.ctrl && !(e.ctrlKey && !e.metaKey && !e.altKey)) return false;
  if (spec.plain && (e.metaKey || e.ctrlKey || e.altKey)) return false;
  if (Boolean(spec.shift) !== e.shiftKey) return false;
  // Mac keyboards report their Delete key as Backspace; both invoke the
  // destructive verb only after its selection guard and confirmation.
  if (spec.key === "delete" && (e.key === "Delete" || e.key === "Backspace"))
    return true;
  if (e.key === spec.key) return true;
  return e.key.toLocaleLowerCase() === spec.key;
}

// Resolved LAZILY: keymap sits inside the verbRegistry/DeskWindow
// import cycle, so VERBS is not initialized at this module's init.
let boundCache: { verb: Verb; spec: KeySpec }[] | null = null;
function bound(): { verb: Verb; spec: KeySpec }[] {
  if (!boundCache)
    boundCache = VERBS.flatMap((verb) => {
      const spec = verb.key ? parseKey(verb.key) : null;
      return spec ? [{ verb, spec }] : [];
    });
  return boundCache;
}

export function keyContext(): VerbContext {
  const ids = useDesk.getState().selectedIds;
  return { selectedRef: ids.length === 1 ? ids[0] : null };
}

/** The one handler (exported for tests). Returns the verb it ran. */
export function dispatchKey(e: KeyboardEvent): Verb | null {
  for (const { verb, spec } of bound()) {
    if (!matchKey(e, spec)) continue;
    if ((TYPING_GUARDED.has(spec.key) || spec.plain) && typing(e.target))
      return null;
    const ctx = keyContext();
    if (verb.ghost(ctx)) return null; // a ghosted verb refuses quietly
    e.preventDefault();
    verb.run(ctx);
    return verb;
  }
  return null;
}

/** Refcounted singleton: the chrome and the dock both mount it, the
 * document carries EXACTLY ONE listener (a verb never runs twice). */
let installs = 0;
const onKey = (e: KeyboardEvent) => void dispatchKey(e);

export function useKeymap(): void {
  useEffect(() => {
    if (installs === 0) document.addEventListener("keydown", onKey);
    installs += 1;
    return () => {
      installs -= 1;
      if (installs === 0) document.removeEventListener("keydown", onKey);
    };
  }, []);
}

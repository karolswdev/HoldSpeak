/** HS-111-07 - the ONE key binder (doctrine P11): the registry's `key`
 * fields are the truth and this module is the only document-level
 * keydown that runs verbs. The hand-rolled listeners that lived in
 * DeskWindow (⌘1-4/⌘W/⌘M/⌘/, ⌃`) and DeskToolShelf (⌘K) are gone -
 * they were parallel binders over the same verbs. */
import { useEffect } from "react";
import { useDesk } from "./store";
import { VERBS, type Verb, type VerbContext } from "./verbRegistry";
import { useSettleState } from "./settleState";

export interface KeySpec {
  meta: boolean;
  ctrl: boolean;
  shift?: boolean;
  /** PHILO-16 — ⌥ (the Tile keys ⌘⌥← / ⌘⌥→). */
  alt?: boolean;
  plain: boolean;
  key: string;
}

/** Key caps that name a key by a symbol. */
const SYMBOL_KEYS: Record<string, string> = {
  "↑": "ArrowUp",
  "←": "ArrowLeft",
  "→": "ArrowRight",
  "⏎": "Enter",
  Esc: "escape",
};

/** ⌘-notation → matchable spec. Display strings stay ⌘-notation; only
 * this module reads them as bindings. Modifiers after ⌘/⌃: ⇧ and ⌥, in
 * either order. */
export function parseKey(cap: string): KeySpec | null {
  const meta = cap.startsWith("⌘");
  const ctrl = cap.startsWith("⌃");
  const plain = cap === "Delete" || cap === "Esc" || /^F\d+$/.test(cap);
  if (!meta && !ctrl && !plain) return null;
  let chord = plain ? cap : cap.slice(1);
  let shift = false;
  let alt = false;
  for (;;) {
    if (!plain && chord.startsWith("⇧")) {
      shift = true;
      chord = chord.slice(1);
    } else if (!plain && chord.startsWith("⌥")) {
      alt = true;
      chord = chord.slice(1);
    } else break;
  }
  const key = SYMBOL_KEYS[chord] ?? chord.toLocaleLowerCase();
  if (!key) return null;
  return { meta, ctrl, plain, ...(shift ? { shift: true } : {}), ...(alt ? { alt: true } : {}), key };
}

/** Plain-letter chords stay quiet while the user is typing (the HS-101
 * rule: ⌘W/⌘M never eat a word in a field). PHILO-13-16: ⌃T too — in a
 * field it is the field's own key (on a Mac it swaps two letters). */
const TYPING_GUARDED = new Set([
  "w", "m", "b", "t",
  // PHILO-16: the arrangement keys. In a field ⌘⇧Z is redo, ⌘⏎ sends a
  // composer, ⌘⌥←/→ and ⌘` belong to the field or the system.
  "z", "g", "e", "`", "ArrowLeft", "ArrowRight", "Enter",
]);

function typing(target: EventTarget | null): boolean {
  // A key sent to the document (no focused element) is not typing; the
  // document has no `closest`, so test for an element first.
  if (!(target instanceof Element)) return false;
  const el = target as HTMLElement;
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
  const alt = Boolean(spec.alt) === e.altKey;
  const primary =
    (e.metaKey || e.ctrlKey) && !(e.metaKey && e.ctrlKey) && alt;
  if (spec.meta && !primary) return false;
  if (spec.ctrl && !(e.ctrlKey && !e.metaKey && alt)) return false;
  if (spec.plain && (e.metaKey || e.ctrlKey || e.altKey)) return false;
  if (Boolean(spec.shift) !== e.shiftKey) return false;
  // ⇧` reports "~" on most layouts: the backquote binds by its key code.
  if (spec.key === "`" && e.code === "Backquote") return true;
  if (spec.key === "escape" && (e.key === "Escape" || e.key === "Esc")) return true;
  // Mac keyboards report their Delete key as Backspace; both invoke the
  // destructive verb only after its selection guard and confirmation.
  if (spec.key === "delete" && (e.key === "Delete" || e.key === "Backspace"))
    return true;
  if (e.key === spec.key) return true;
  return e.key.toLocaleLowerCase() === spec.key;
}

/** PHILO-13-12 (C2) — a literal ⌃ chord binds before a ⌘ chord: ⌘ also
 * accepts ctrl off the Mac, so ⌃M (Zoom) must win over ⌘M (Iconify) for the
 * ctrl key. On a Mac ⌘M stays Iconify. */
const BOUND_VERBS: { verb: Verb; spec: KeySpec }[] = VERBS.flatMap((verb) =>
  // PHILO-16: a verb's older keys (`altKeys`) stay bound one release.
  [verb.key, ...(verb.altKeys ?? [])].flatMap((cap) => {
    const spec = cap ? parseKey(cap) : null;
    return spec ? [{ verb, spec }] : [];
  }),
).sort((a, b) => Number(b.spec.ctrl) - Number(a.spec.ctrl));

export function keyContext(): VerbContext {
  const ids = useDesk.getState().selectedIds;
  return { selectedRef: ids.length === 1 ? ids[0] : null };
}

/** The one handler (exported for tests). Returns the verb it ran. */
export function dispatchKey(e: KeyboardEvent): Verb | null {
  if (e.repeat || e.defaultPrevented || e.isComposing) return null;
  for (const { verb, spec } of BOUND_VERBS) {
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
 * document carries one verb listener and one Escape-only dismissal guard
 * (a verb never runs twice, including when the shelf is quiet). */
let installs = 0;
const onKey = (e: KeyboardEvent) => void dispatchKey(e);

/** Escape first restores shell chrome. Capture phase protects an open editor
 * or window from also closing on the same keystroke. IME keeps its own Escape. */
export function dismissSettle(e: KeyboardEvent): boolean {
  if (e.key !== "Escape" || e.isComposing || !useSettleState.getState().settled)
    return false;
  e.preventDefault();
  e.stopImmediatePropagation();
  useSettleState.getState().setSettled(false);
  return true;
}
const onDismiss = (e: KeyboardEvent) => {
  dismissSettle(e);
};

export function useKeymap(): void {
  useEffect(() => {
    if (installs === 0) {
      document.addEventListener("keydown", onKey);
      document.addEventListener("keydown", onDismiss, true);
    }
    installs += 1;
    return () => {
      installs -= 1;
      if (installs === 0) {
        document.removeEventListener("keydown", onKey);
        document.removeEventListener("keydown", onDismiss, true);
      }
    };
  }, []);
}

// PHILO-13-07 (B2) — "the Desk remembers": a field's unsent text and a
// window's place live in the one workspace document (`hs.desk.workspace.v1`,
// `drafts` and `places`), so they survive a reload and a close.
//
// The key names the field AND its object (`people/1on1/<person>`), so a
// draft typed for one object never shows in another. The caller clears a
// draft when its write lands; restore only fills the field, it never saves
// or sends.
import { useCallback } from "react";
import { useDesk } from "./store";

/** The kept text for `key` ("" when none), its setter (an emptied field is
 * kept as "": Astra's B2 condition) and `forget` (the write landed). A null
 * key (no object yet) keeps nothing. */
export function useDeskDraft(
  key: string | null,
): [string, (text: string) => void, () => void] {
  const text = useDesk((s) => (key ? s.drafts[key] ?? "" : ""));
  const setText = useCallback(
    (next: string) => {
      if (key) useDesk.getState().setDraft(key, next);
    },
    [key],
  );
  const forget = useCallback(() => {
    if (key) useDesk.getState().setDraft(key, null);
  }, [key]);
  return [text, setText, forget];
}

/** Read one kept draft outside React: null when there is none, "" when he
 * emptied the field. */
export function keptDraft(key: string): string | null {
  const drafts = useDesk.getState().drafts;
  return key in drafts ? drafts[key] : null;
}

/** Keep one draft outside React ("" is an emptied field, kept as such). */
export function keepDraft(key: string, text: string): void {
  useDesk.getState().setDraft(key, text);
}

/** Forget one draft: its write landed, or it is superseded. */
export function forgetDraft(key: string): void {
  useDesk.getState().setDraft(key, null);
}

/** Read one kept place ("" when none). */
export function keptPlace(key: string): string {
  return useDesk.getState().places[key] ?? "";
}

/** Keep (or, with "", clear) one place. */
export function keepPlace(key: string, value: string): void {
  useDesk.getState().setPlace(key, value);
}

/** PHILO-13-07 (B2 slice two) — an open window family's record (its object
 * or target), kept as a place under `window/<family>`. `null` forgets it:
 * a closed window stays gone. */
export function rememberWindow(family: string, record: unknown): void {
  keepPlace(`window/${family}`, record == null ? "" : JSON.stringify(record));
}

/** The kept record of an open window family, or null. */
export function keptWindow<T>(family: string): T | null {
  const raw = keptPlace(`window/${family}`);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch {
    return null;
  }
}

// Tests share one module graph per file: a prior case's draft or place must
// not answer the next (called by src/test/setup.ts, the needs-you pattern).
// (A file that mocks the store module has no setState: nothing to reset.)
(globalThis as { __resetDeskMemory?: () => void }).__resetDeskMemory = () =>
  useDesk.setState?.({ drafts: {}, places: {} });

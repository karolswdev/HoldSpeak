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

/** The kept text for `key` ("" when none) and its setter ("" clears). A null
 * key (no object yet) keeps nothing. */
export function useDeskDraft(key: string | null): [string, (text: string) => void] {
  const text = useDesk((s) => (key ? s.drafts[key] ?? "" : ""));
  const setText = useCallback(
    (next: string) => {
      if (key) useDesk.getState().setDraft(key, next);
    },
    [key],
  );
  return [text, setText];
}

/** Read one kept draft outside React (a writer's first state). */
export function keptDraft(key: string): string {
  return useDesk.getState().drafts[key] ?? "";
}

/** Keep (or, with "", clear) one draft outside React. */
export function keepDraft(key: string, text: string): void {
  useDesk.getState().setDraft(key, text);
}

/** Read one kept place ("" when none). */
export function keptPlace(key: string): string {
  return useDesk.getState().places[key] ?? "";
}

/** Keep (or, with "", clear) one place. */
export function keepPlace(key: string, value: string): void {
  useDesk.getState().setPlace(key, value);
}

// Tests share one module graph per file: a prior case's draft or place must
// not answer the next (called by src/test/setup.ts, the needs-you pattern).
(globalThis as { __resetDeskMemory?: () => void }).__resetDeskMemory = () =>
  useDesk.setState({ drafts: {}, places: {} });

/* Memory on the Desk: a memory face follows the bus, and never draws a
 * withdrawn source while its re-read is in flight (Astra, PR #877 P1).
 *
 * A belief or a page sentence rests on sources. When a write changes a source
 * (a note deleted, a meeting edited), the hub sends one `desk_changed` frame
 * naming each change `{kind, id, op}`. The face:
 *
 *   1. HOLDS every ref the frame names, at once: a sentence or a belief whose
 *      evidence names a held id is not drawn;
 *   2. re-reads (debounced, as `useOnDeskChanged`);
 *   3. lets the hold go only when a re-read that STARTED after the change
 *      is ACCEPTED: `reload` resolves to anything but `false`, and its
 *      result is the one on the glass. A re-read that fails, or that a
 *      newer read superseded (`false`), keeps the hold.
 *
 * The match is on the id alone (a ref `note:n2`, `meeting:m1#seg-4` names id
 * `n2`, `m1`): a kind has several names (`action` / `action_item`,
 * `decision` / `desk_decision`), and holding one extra sentence for a moment
 * is the safe side.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { burstTimer } from "./burstTimer";
import { DESK_CHANGED_DEBOUNCE_MS, useBusSubscribe } from "./useDeskChangedRefresh";

interface Held {
  id: string;
  seq: number;
}

/** The ids one `desk_changed` frame names. */
export function changedIds(data: unknown): string[] {
  const d = (data && typeof data === "object" ? data : {}) as {
    id?: unknown;
    changes?: { id?: unknown }[];
  };
  const ids = [d.id, ...(Array.isArray(d.changes) ? d.changes.map((c) => c?.id) : [])]
    .map((v) => (typeof v === "string" ? v.trim() : ""))
    .filter(Boolean);
  return [...new Set(ids)];
}

/** The id a ref names: `note:n2` → `n2`, `thread:t1#m4` → `t1`. */
export function refId(ref: string): string {
  const rest = ref.includes(":") ? ref.slice(ref.indexOf(":") + 1) : ref;
  return rest.split("#", 1)[0];
}

/**
 * Follow the bus for a memory face. `reload` re-reads the face's data and
 * resolves when the new data is on the glass; it resolves `false` when its
 * answer was discarded (a newer read won) and rejects on a failed read.
 * Returns `held(refs)`: true while any ref names a changed source whose
 * re-read has not landed.
 */
export function useMemoryChanges(
  reload: () => Promise<unknown> | unknown,
  debounceMs: number = DESK_CHANGED_DEBOUNCE_MS,
): (refs: string[]) => boolean {
  const subscribe = useBusSubscribe();
  const [held, setHeld] = useState<Held[]>([]);
  const seq = useRef(0);
  const latest = useRef(reload);
  latest.current = reload;

  useEffect(() => {
    if (!subscribe) return;
    const burst = burstTimer(() => {
      const startedAt = seq.current;
      Promise.resolve()
        .then(() => latest.current())
        .then(
          // Only an ACCEPTED re-read that started after a change lets that
          // change go; a discarded one (`false`) releases nothing.
          (accepted) => {
            if (accepted === false) return;
            setHeld((prev) => prev.filter((h) => h.seq > startedAt));
          },
          () => undefined,
        );
    }, debounceMs);
    const unsubscribe = subscribe("desk_changed", (frame) => {
      const ids = changedIds(frame?.data);
      if (ids.length) {
        seq.current += 1;
        const at = seq.current;
        setHeld((prev) => [...prev, ...ids.map((id) => ({ id, seq: at }))]);
      }
      burst.bump();
    });
    return () => {
      burst.cancel();
      if (typeof unsubscribe === "function") unsubscribe();
    };
  }, [subscribe, debounceMs]);

  return useCallback(
    (refs: string[]) => {
      if (!held.length) return false;
      const ids = new Set(held.map((h) => h.id));
      return refs.some((ref) => ids.has(refId(ref)));
    },
    [held],
  );
}

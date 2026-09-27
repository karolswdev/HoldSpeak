import { createElement, useCallback, useEffect, useRef, useState } from "react";
import { OUTCOME_LINGER_MS } from "../linger";

interface UndoState {
  phase: "pending" | "committing" | "restored" | "committed";
  label: string;
  remaining: number;
  fire: Fire;
  revert: () => void;
}

/** A removal's commit. One result contract for every caller: it answers
 * nothing (a commit that cannot fail here) or a promise of a boolean —
 * `true` when the hub took it, `false` when it refused (the caller names
 * the failure on its write receipt). */
type Fire = () => void | Promise<boolean>;

/** PHILO-8-02 — a removal is never dropped. The receipt keeps ONE slot: a
 * second `remove()` COMMITS the pending one at once (its Undo goes away),
 * and an unmount COMMITS a pending one, so leaving the face inside the
 * window cannot keep an object the face said was removed. Only `undo()`
 * keeps it.
 *
 * Round three (Codex Astra, PR #672): a removal may carry its target's key.
 * A second request for the target already pending keeps that one entry (its
 * Undo still restores it); a request for a target already committed opens
 * nothing. So Undo only ever offers to restore what is still restorable.
 *
 * Round four (Codex Astra r2): "Removal committed" is said only after the
 * commit lands. While it is in flight the receipt keeps "Removed …" with no
 * Undo and no countdown; a refused commit clears the receipt (the failure
 * receipt speaks). A key guards only its window and its commit: it is freed
 * when the commit settles, so a re-created object can be deleted again. */
export function useUndoReceipt(window = 8) {
  const [state, setState] = useState<UndoState | null>(null);
  const deadlineRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const postRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  // The fire of the removal still inside its window; null once it fired or
  // was undone.
  const pendingRef = useRef<Fire | null>(null);
  const pendingKeyRef = useRef<string | null>(null);
  const committedKeysRef = useRef<Set<string>>(new Set());
  const entryRef = useRef(0);

  /** Run a commit. Its key is held only until the commit settles. When
   * `announce` is set, the receipt says "Removal committed" only on success
   * and clears on a refusal. */
  const run = useCallback(
    (fire: Fire, key: string | null, entry: number, announce: boolean) => {
      const committed = () => {
        if (!announce || entryRef.current !== entry) return;
        setState((previous) =>
          previous ? { ...previous, phase: "committed", remaining: 0 } : null,
        );
        clearTimeout(postRef.current);
        postRef.current = setTimeout(() => setState(null), OUTCOME_LINGER_MS);
      };
      if (key) committedKeysRef.current.add(key);
      const out = fire();
      if (!out || typeof (out as Promise<boolean>).then !== "function") {
        if (key) committedKeysRef.current.delete(key);
        committed();
        return;
      }
      if (announce)
        setState((previous) =>
          previous ? { ...previous, phase: "committing", remaining: 0 } : null,
        );
      const settle = (ok: boolean) => {
        if (key) committedKeysRef.current.delete(key);
        if (ok) return committed();
        if (!announce || entryRef.current !== entry) return;
        clearTimeout(postRef.current);
        setState(null);
      };
      void (out as Promise<boolean>).then(
        (ok) => settle(ok !== false),
        () => settle(false),
      );
    },
    [],
  );

  const cleanup = useCallback(() => {
    clearInterval(intervalRef.current);
    clearTimeout(postRef.current);
  }, []);

  /** Commit the pending removal now, if there is one. */
  const flush = useCallback(() => {
    const fire = pendingRef.current;
    if (!fire) return;
    const key = pendingKeyRef.current;
    pendingRef.current = null;
    pendingKeyRef.current = null;
    cleanup();
    run(fire, key, entryRef.current, true);
  }, [cleanup, run]);

  useEffect(
    () => () => {
      const fire = pendingRef.current;
      const key = pendingKeyRef.current;
      pendingRef.current = null;
      pendingKeyRef.current = null;
      cleanup();
      if (fire) run(fire, key, entryRef.current, false);
    },
    [cleanup, run],
  );

  const remove = useCallback(
    (label: string, fire: Fire, revert: () => void, key?: string) => {
      const target = key ?? null;
      // The same target again: keep its one entry, or open nothing if it
      // is already committed. Never a second Undo for one object.
      if (target && (pendingKeyRef.current === target || committedKeysRef.current.has(target)))
        return;
      flush();
      cleanup();
      entryRef.current += 1;
      pendingRef.current = fire;
      pendingKeyRef.current = target;
      deadlineRef.current = Date.now() + window * 1000;
      setState({ phase: "pending", label, remaining: window, fire, revert });

      intervalRef.current = setInterval(() => {
        const left = Math.max(
          0,
          Math.ceil((deadlineRef.current - Date.now()) / 1000),
        );
        if (left <= 0) {
          flush();
        } else {
          setState((previous) =>
            previous ? { ...previous, remaining: left } : null,
          );
        }
      }, 250);
    },
    [window, cleanup, flush],
  );

  const undo = useCallback(() => {
    if (!state || state.phase !== "pending" || !pendingRef.current) return;
    pendingRef.current = null;
    pendingKeyRef.current = null;
    cleanup();
    state.revert();
    setState({ ...state, phase: "restored", remaining: 0 });
    postRef.current = setTimeout(() => setState(null), OUTCOME_LINGER_MS);
  }, [state, cleanup]);

  const segments =
    state?.phase === "pending"
      ? Array.from({ length: window }, (_, index) => index < state.remaining)
      : [];

  const receipt =
    state === null
      ? null
      : createElement(
          "span",
          { className: `undo-receipt is-${state.phase}` },
          createElement("span", {
            className: `undo-receipt-lamp ${
              state.phase === "restored"
                ? "is-ok"
                : state.phase === "committed"
                  ? "is-off"
                  : "is-warn"
            }`,
          }),
          createElement(
            "span",
            { className: "undo-receipt-label" },
            state.phase === "restored"
              ? `Restored ${state.label}`
              : state.phase === "committed"
                ? "Removal committed"
                : `Removed ${state.label}`,
          ),
          state.phase === "pending"
            ? [
                createElement(
                  "button",
                  {
                    type: "button",
                    className: "desk-chip undo-receipt-btn",
                    onClick: undo,
                  },
                  "Undo",
                ),
                createElement(
                  "span",
                  { className: "undo-receipt-meter" },
                  segments.map((lit, index) =>
                    createElement("span", {
                      key: index,
                      className: `undo-receipt-seg ${lit ? "is-lit" : "is-dim"}`,
                    }),
                  ),
                ),
                createElement(
                  "span",
                  { className: "undo-receipt-time" },
                  `${String(state.remaining).padStart(2, "0")}s`,
                ),
              ]
            : null,
        );

  return { remove, undo, flush, receipt, phase: state?.phase ?? "idle" };
}

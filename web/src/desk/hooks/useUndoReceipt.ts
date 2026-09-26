import { createElement, useCallback, useEffect, useRef, useState } from "react";
import { OUTCOME_LINGER_MS } from "../linger";

interface UndoState {
  phase: "pending" | "restored" | "committed";
  label: string;
  remaining: number;
  fire: () => void;
  revert: () => void;
}

/** PHILO-8-02 — a removal is never dropped. The receipt keeps ONE slot: a
 * second `remove()` COMMITS the pending one at once (its Undo goes away),
 * and an unmount COMMITS a pending one, so leaving the face inside the
 * window cannot keep an object the face said was removed. Only `undo()`
 * keeps it. */
export function useUndoReceipt(window = 8) {
  const [state, setState] = useState<UndoState | null>(null);
  const deadlineRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const postRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  // The fire of the removal still inside its window; null once it fired or
  // was undone.
  const pendingRef = useRef<(() => void) | null>(null);

  const cleanup = useCallback(() => {
    clearInterval(intervalRef.current);
    clearTimeout(postRef.current);
  }, []);

  /** Commit the pending removal now, if there is one. */
  const flush = useCallback(() => {
    const fire = pendingRef.current;
    if (!fire) return;
    pendingRef.current = null;
    cleanup();
    setState((previous) =>
      previous ? { ...previous, phase: "committed", remaining: 0 } : null,
    );
    fire();
    postRef.current = setTimeout(() => setState(null), OUTCOME_LINGER_MS);
  }, [cleanup]);

  useEffect(
    () => () => {
      const fire = pendingRef.current;
      pendingRef.current = null;
      cleanup();
      fire?.();
    },
    [cleanup],
  );

  const remove = useCallback(
    (label: string, fire: () => void, revert: () => void) => {
      flush();
      cleanup();
      pendingRef.current = fire;
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
    if (!state || state.phase !== "pending") return;
    pendingRef.current = null;
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

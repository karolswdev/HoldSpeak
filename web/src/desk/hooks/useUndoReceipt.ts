import { createElement, useCallback, useEffect, useRef, useState } from "react";

interface UndoState {
  phase: "pending" | "restored" | "committed";
  label: string;
  remaining: number;
  fire: () => void;
  revert: () => void;
}

export function useUndoReceipt(window = 8) {
  const [state, setState] = useState<UndoState | null>(null);
  const deadlineRef = useRef<number>(0);
  const intervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined);
  const postRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const cleanup = useCallback(() => {
    clearInterval(intervalRef.current);
    clearTimeout(postRef.current);
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const remove = useCallback(
    (label: string, fire: () => void, revert: () => void) => {
      cleanup();
      deadlineRef.current = Date.now() + window * 1000;
      setState({ phase: "pending", label, remaining: window, fire, revert });

      intervalRef.current = setInterval(() => {
        const left = Math.max(
          0,
          Math.ceil((deadlineRef.current - Date.now()) / 1000),
        );
        if (left <= 0) {
          cleanup();
          setState((previous) =>
            previous
              ? { ...previous, phase: "committed", remaining: 0 }
              : null,
          );
          fire();
          postRef.current = setTimeout(() => setState(null), 1200);
        } else {
          setState((previous) =>
            previous ? { ...previous, remaining: left } : null,
          );
        }
      }, 250);
    },
    [window, cleanup],
  );

  const undo = useCallback(() => {
    if (!state || state.phase !== "pending") return;
    cleanup();
    state.revert();
    setState({ ...state, phase: "restored", remaining: 0 });
    postRef.current = setTimeout(() => setState(null), 1600);
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

  return { remove, undo, receipt, phase: state?.phase ?? "idle" };
}

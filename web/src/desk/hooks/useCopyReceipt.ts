import { createElement, useCallback, useRef, useState } from "react";

export function useCopyReceipt() {
  const [state, setState] = useState<"idle" | "copied" | "failed">("idle");
  const timerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  const copy = useCallback(async (text: string) => {
    clearTimeout(timerRef.current);
    try {
      await navigator.clipboard.writeText(text);
      setState("copied");
      timerRef.current = setTimeout(() => setState("idle"), 2000);
    } catch {
      setState("failed");
    }
  }, []);

  const dismiss = useCallback(() => {
    clearTimeout(timerRef.current);
    setState("idle");
  }, []);

  const receipt =
    state === "idle"
      ? null
      : createElement(
          "span",
          { className: `copy-receipt ${state === "failed" ? "is-failed" : ""}` },
          createElement("span", {
            className: `copy-receipt-lamp ${state === "copied" ? "is-ok" : "is-fail"}`,
          }),
          createElement(
            "span",
            { className: "copy-receipt-label" },
            state === "copied" ? "COPIED" : "COPY FAILED",
          ),
          state === "failed"
            ? createElement(
                "button",
                {
                  type: "button",
                  className: "desk-chip copy-receipt-dismiss",
                  onClick: dismiss,
                },
                "OK",
              )
            : null,
        );

  return { copy, receipt, state };
}

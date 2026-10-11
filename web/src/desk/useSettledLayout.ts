/** PHILO-17 (phonepass) — hold a face back until its reads stop moving it.
 *
 *  A window whose sections each make their own read grows in steps: a row
 *  lands above another row and pushes it down. At 393 a tap aimed at a row
 *  just before a read lands hits the row that moved under it (the owner's
 *  finger opened a meeting instead of `Draft update`). The face keeps its
 *  place in the layout but is not drawn (visibility: hidden, so no tap can
 *  hit it) until its height has been still for `quietMs`, or `maxMs` has
 *  passed. After that it is drawn and stays drawn. */
import { useEffect, useState } from "react";

export const SETTLE_QUIET_MS = 150;
export const SETTLE_MAX_MS = 1500;

export function useSettledLayout(
  el: HTMLElement | null,
  key: string,
  quietMs = SETTLE_QUIET_MS,
  maxMs = SETTLE_MAX_MS,
): boolean {
  const [settled, setSettled] = useState<string | null>(null);
  useEffect(() => {
    if (!el || settled === key) return;
    if (typeof ResizeObserver === "undefined") {
      setSettled(key);
      return;
    }
    let quiet = window.setTimeout(() => done(), quietMs);
    const cap = window.setTimeout(() => done(), maxMs);
    let last = -1;
    const observer = new ResizeObserver((entries) => {
      const height = Math.round(entries[entries.length - 1]?.contentRect.height ?? 0);
      if (height === last) return;
      last = height;
      window.clearTimeout(quiet);
      quiet = window.setTimeout(() => done(), quietMs);
    });
    function done() {
      observer.disconnect();
      window.clearTimeout(quiet);
      window.clearTimeout(cap);
      setSettled(key);
    }
    observer.observe(el);
    return () => {
      observer.disconnect();
      window.clearTimeout(quiet);
      window.clearTimeout(cap);
    };
  }, [el, key, quietMs, maxMs, settled]);
  return settled === key;
}

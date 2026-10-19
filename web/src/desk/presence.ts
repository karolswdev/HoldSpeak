// Betterment daily D8: the desk tells the hub which window is in front of the
// owner, so the heartbeat raises no notice about the window he is looking at
// (holdspeak/desk_presence.py). It reports while the page is visible and
// focused: on load, when the front window changes, on focus and blur, and once
// a minute. A report that fails is dropped; the next one replaces it.
import { useEffect } from "react";
import { apiFetch } from "../lib/api";
import { useDesk } from "./store";

/** The hub forgets a report after 150 s; the desk reports every 60 s. */
export const PRESENCE_EVERY_MS = 60_000;

/** The window registry, loaded on first use: imported at the top it changed
 * the desk's module order (the compositor's planes must load first). */
let frontWindowId: (() => string | null) | null = null;

export function presenceNow(): { front: string | null; visible: boolean } {
  const visible = typeof document !== "undefined"
    && document.visibilityState === "visible"
    && (typeof document.hasFocus !== "function" || document.hasFocus());
  return { front: frontWindowId ? frontWindowId() : null, visible };
}

export function useDeskPresence(): void {
  useEffect(() => {
    let last = "";
    let timer: number | undefined;
    const send = (force = false) => {
      const now = presenceNow();
      const key = `${now.front ?? ""}|${now.visible}`;
      if (!force && key === last) return;
      last = key;
      void apiFetch("/api/desk/presence", { method: "POST", json: now }).catch(() => undefined);
    };
    // A burst of stacking changes is one report.
    const soon = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => send(), 400);
    };
    void import("./components/window/windowRegistry").then((m) => {
      frontWindowId = m.frontWindowId;
      send(true);
    });
    const every = window.setInterval(() => send(true), PRESENCE_EVERY_MS);
    const unsubscribe = useDesk.subscribe((s, prev) => {
      if (s.panelOrder !== prev.panelOrder || s.panelMin !== prev.panelMin) soon();
    });
    window.addEventListener("focus", soon);
    window.addEventListener("blur", soon);
    document.addEventListener("visibilitychange", soon);
    return () => {
      window.clearTimeout(timer);
      window.clearInterval(every);
      unsubscribe();
      window.removeEventListener("focus", soon);
      window.removeEventListener("blur", soon);
      document.removeEventListener("visibilitychange", soon);
    };
  }, []);
}

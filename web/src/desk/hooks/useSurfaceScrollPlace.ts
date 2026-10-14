import { useCallback, useRef, type RefCallback } from "react";
import { keepPlace, keptPlace } from "../deskMemory";

const RESTORE_DEADLINE_MS = 8_000;

/** The Desk place for one hosted window and one of its scopes. */
export function surfaceScrollPlaceKey(windowId: string, scope?: string): string {
  return `surface-scroll/${JSON.stringify([windowId, scope ?? null])}`;
}

type RestoreCleanup = () => void;

/**
 * Keep the scroll position of a hosted surface body in Desk memory.
 *
 * The callback ref deliberately owns the body lifecycle. A refresh of a core
 * leaves the same body and therefore cannot replay an old place. Changing the
 * host scope gives the body a new place while preserving the window frame.
 */
export function useSurfaceScrollPlace(
  windowId: string,
  scope?: string,
): RefCallback<HTMLDivElement> {
  const placeKey = surfaceScrollPlaceKey(windowId, scope);
  const restoreCleanup = useRef<RestoreCleanup | null>(null);

  return useCallback(
    (body: HTMLDivElement | null) => {
      restoreCleanup.current?.();
      restoreCleanup.current = null;
      if (!body) return;

      let restoreCancelled = false;
      const rawTarget = Number(keptPlace(placeKey));
      const target = Number.isFinite(rawTarget) && rawTarget > 0 ? rawTarget : null;
      // A missing place is already ready for an owner's first scroll. A
      // saved place remains pending until the body can reach it (or input
      // cancels that pending restore).
      let restored = target === null;
      let restoring = false;
      let frame: number | null = null;
      let deadlineTimer: number | null = null;
      let canPersistZero = false;
      const schedule = (callback: () => void): number =>
        typeof window.requestAnimationFrame === "function"
          ? window.requestAnimationFrame(callback)
          : window.setTimeout(callback, 0);
      const cancel = (handle: number) => {
        if (typeof window.cancelAnimationFrame === "function") {
          window.cancelAnimationFrame(handle);
        } else {
          window.clearTimeout(handle);
        }
      };

      let resizeObserver: ResizeObserver | null = null;
      let mutationObserver: MutationObserver | null = null;

      const cancelRestore = () => {
        restoreCancelled = true;
        // Input gives the owner control of this body. Future real scrolls
        // must be allowed to write a new place even though no restore ran.
        restored = true;
        if (frame !== null) cancel(frame);
        frame = null;
        if (deadlineTimer !== null) window.clearTimeout(deadlineTimer);
        deadlineTimer = null;
        resizeObserver?.disconnect();
        mutationObserver?.disconnect();
      };

      const onUserInput = () => {
        if (target !== null && !restored) cancelRestore();
      };

      const onScroll = () => {
        // Initial layout and a pending restore both commonly report zero. A
        // zero here must not erase the last useful place. Once the owner has
        // reached a real place, zero is a valid future target only after the
        // restore has completed.
        if (restoring || (!restored && target !== null)) return;
        if (body.scrollTop > 0 || restored) {
          if (body.scrollTop > 0) canPersistZero = true;
          if (body.scrollTop > 0 || canPersistZero) {
            keepPlace(placeKey, String(Math.round(body.scrollTop)));
          }
        }
      };

      body.addEventListener("scroll", onScroll, { passive: true });
      body.addEventListener("wheel", onUserInput, { capture: true, passive: true });
      body.addEventListener("touchstart", onUserInput, { capture: true, passive: true });
      body.addEventListener("touchmove", onUserInput, { capture: true, passive: true });
      body.addEventListener("pointerdown", onUserInput, { capture: true, passive: true });
      body.addEventListener("keydown", onUserInput, { capture: true });

      const stopObservers = () => {
        if (frame !== null) cancel(frame);
        frame = null;
        if (deadlineTimer !== null) window.clearTimeout(deadlineTimer);
        deadlineTimer = null;
        resizeObserver?.disconnect();
        mutationObserver?.disconnect();
      };

      const tryRestore = (atDeadline = false) => {
        frame = null;
        if (restoreCancelled || restored || target === null) return;
        const maxScroll = Math.max(0, body.scrollHeight - body.clientHeight);
        const canReachTarget = maxScroll >= target;
        if (canReachTarget || atDeadline) {
          restoring = true;
          body.scrollTop = Math.min(target, maxScroll);
          restoring = false;
          restored = true;
          canPersistZero = true;
          stopObservers();
          return;
        }
      };

      const queueRestore = () => {
        if (restoreCancelled || restored || target === null || frame !== null) return;
        frame = schedule(() => tryRestore());
      };

      if (target !== null) {
        resizeObserver =
          typeof ResizeObserver === "function"
            ? new ResizeObserver(queueRestore)
            : null;
        resizeObserver?.observe(body);
        mutationObserver =
          typeof MutationObserver === "function"
            ? new MutationObserver(queueRestore)
            : null;
        mutationObserver?.observe(body, { childList: true, subtree: true });
        queueRestore();
        if (!restored && !restoreCancelled) {
          deadlineTimer = window.setTimeout(() => tryRestore(true), RESTORE_DEADLINE_MS);
        }
      }

      restoreCleanup.current = () => {
        cancelRestore();
        stopObservers();
        body.removeEventListener("scroll", onScroll);
        body.removeEventListener("wheel", onUserInput, true);
        body.removeEventListener("touchstart", onUserInput, true);
        body.removeEventListener("touchmove", onUserInput, true);
        body.removeEventListener("pointerdown", onUserInput, true);
        body.removeEventListener("keydown", onUserInput, true);
      };
    },
    [placeKey],
  );
}

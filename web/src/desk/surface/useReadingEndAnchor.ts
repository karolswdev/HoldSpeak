import { useLayoutEffect, type RefObject } from "react";

const END_EPSILON = 2;

function isAtEnd(element: HTMLElement): boolean {
  return element.scrollHeight - element.clientHeight - element.scrollTop <= END_EPSILON;
}

function scrollToEnd(element: HTMLElement): void {
  element.scrollTop = Math.max(0, element.scrollHeight - element.clientHeight);
}

/**
 * Keep a reading viewport on its bottom edge while its material changes.
 *
 * The hook records whether the owner was at the end before a resize or DOM
 * change. Only that state is allowed to move the viewport; a reader who has
 * scrolled up keeps the current position. `active` follows conditional
 * reading nodes such as Ask's empty/conversation branches.
 */
export function useReadingEndAnchor(
  scrollRef: RefObject<HTMLElement | null>,
  active: boolean,
): void {
  useLayoutEffect(() => {
    if (!active) return undefined;
    const reading = scrollRef.current;
    if (!reading) return undefined;

    let atEnd = true;
    let frame: number | null = null;
    let disposed = false;
    let pendingAnchor = false;
    let lastTop: number | null = null;
    let resizeObserver: ResizeObserver | null = null;

    const samplePosition = () => {
      const top = reading.scrollTop;
      if (lastTop === null || top === lastTop) return;
      atEnd = isAtEnd(reading);
      lastTop = top;
    };

    const schedule = () => {
      if (disposed) return;
      // Resize can change the geometry without changing scrollTop. Keep the
      // old end state in that case. A delayed/programmatic scrollTop write is
      // different: sample it before capturing the pending anchor.
      samplePosition();
      if (frame !== null) {
        pendingAnchor = atEnd;
        return;
      }
      pendingAnchor = atEnd;
      const run = () => {
        frame = null;
        samplePosition();
        const shouldAnchor = pendingAnchor;
        pendingAnchor = false;
        if (!disposed && shouldAnchor && atEnd) {
          scrollToEnd(reading);
          atEnd = true;
          lastTop = reading.scrollTop;
        }
      };
      frame = typeof window.requestAnimationFrame === "function"
        ? window.requestAnimationFrame(run)
        : window.setTimeout(run, 0);
    };

    const cancel = () => {
      if (frame === null) return;
      if (typeof window.cancelAnimationFrame === "function") window.cancelAnimationFrame(frame);
      else window.clearTimeout(frame);
      frame = null;
    };

    const onScroll = () => {
      samplePosition();
    };
    const observeContent = () => {
      if (!resizeObserver) return;
      resizeObserver.disconnect();
      resizeObserver.observe(reading);
      for (const child of Array.from(reading.children)) resizeObserver.observe(child);
    };

    reading.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", schedule);

    if (typeof ResizeObserver === "function") {
      resizeObserver = new ResizeObserver(schedule);
      observeContent();
    }

    const mutationObserver = typeof MutationObserver === "function"
      ? new MutationObserver(() => {
          observeContent();
          schedule();
        })
      : null;
    mutationObserver?.observe(reading, { childList: true, subtree: true, characterData: true });

    // Ask historically opens the newest answer at the end. This also gives
    // the resize/content observers a correct initial anchor state.
    scrollToEnd(reading);
    atEnd = true;
    lastTop = reading.scrollTop;

    return () => {
      disposed = true;
      cancel();
      mutationObserver?.disconnect();
      resizeObserver?.disconnect();
      reading.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", schedule);
    };
  }, [active, scrollRef]);
}


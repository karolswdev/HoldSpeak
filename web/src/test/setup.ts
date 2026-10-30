import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";
import { deskQueryClient } from "../lib/queryClient";

// The application intentionally shares one resource cache. Tests must not
// share it across cases, or a prior mocked response can satisfy a later
// window without exercising that test's API contract.
beforeEach(() => {
  deskQueryClient.clear();
  // PHILO-13-03: the one needs-you snapshot is shared; a prior case's read
  // must not answer the next (registered by desk/needsYou.ts, never imported
  // here, so a test's API mock still binds).
  (globalThis as { __resetNeedsYou?: () => void }).__resetNeedsYou?.();
  // PHILO-13-07 (B2): a prior case's kept draft or window place must not
  // answer the next (registered by desk/deskMemory.ts).
  (globalThis as { __resetDeskMemory?: () => void }).__resetDeskMemory?.();
});

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (!("ResizeObserver" in globalThis)) {
  Object.defineProperty(globalThis, "ResizeObserver", {
    value: ResizeObserverStub,
    configurable: true,
    writable: true,
  });
}

// jsdom has no matchMedia; motion's useReducedMotion (HS-93-08) needs one.
if (typeof window !== "undefined" && !window.matchMedia) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: () => {},
      removeListener: () => {},
      addEventListener: () => {},
      removeEventListener: () => {},
      dispatchEvent: () => false,
    }),
  });
}

// jsdom has no text layout: a Range has no client rects. CodeMirror measures
// them on its own frame after any view update (the note's live preview, a
// scroll into view), and threw an unhandled error between cases. An empty
// layout is the truth of jsdom.
if (typeof Range !== "undefined") {
  if (typeof Range.prototype.getClientRects !== "function") {
    Range.prototype.getClientRects = function getClientRects() {
      return Object.assign([], { item: () => null }) as unknown as DOMRectList;
    };
  }
  if (typeof Range.prototype.getBoundingClientRect !== "function") {
    Range.prototype.getBoundingClientRect = function getBoundingClientRect() {
      return new DOMRect();
    };
  }
}

// jsdom has no canvas: its getContext logs a "Not implemented" error with a
// full stack, then returns null. Return the same null without the log, so a
// face that measures text (DeskIcon, the mermaid preview) does not fill the
// vitest log. A test that needs a context still spies on the prototype.
if (typeof HTMLCanvasElement !== "undefined") {
  HTMLCanvasElement.prototype.getContext = function getContext() {
    return null;
  } as HTMLCanvasElement["getContext"];
}

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
});

class ResizeObserverStub {
  observe() {}
  unobserve() {}
  disconnect() {}
}

if (!("ResizeObserver" in globalThis)) {
  Object.defineProperty(globalThis, "ResizeObserver", {
    value: ResizeObserverStub,
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

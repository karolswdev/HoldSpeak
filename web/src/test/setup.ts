import "@testing-library/jest-dom/vitest";
import { beforeEach } from "vitest";
import { deskQueryClient } from "../lib/queryClient";

// The application intentionally shares one resource cache. Tests must not
// share it across cases, or a prior mocked response can satisfy a later
// window without exercising that test's API contract.
beforeEach(() => {
  deskQueryClient.clear();
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

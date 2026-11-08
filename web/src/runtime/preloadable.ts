import { lazy, type ComponentType } from "react";

export type LazyModule<P = Record<string, never>> = { default: ComponentType<P> };

/** A lazy component whose chunk can be read before it renders.
 *
 * React 19 reveals a Suspense boundary no sooner than 300 ms after its
 * fallback showed (react-dom's FALLBACK_THROTTLE_MS). The lazy Desk route
 * suspended on every open and was drawn about 300 ms after its chunk had
 * arrived (perf lane 2026-11-08). Read
 * first (`preload`), the lazy resolves at once: its thenable calls back at
 * once, so the render does not suspend and no fallback shows. */
export function preloadable<P = Record<string, never>>(load: () => Promise<LazyModule<P>>) {
  let module: LazyModule<P> | null = null;
  let pending: Promise<LazyModule<P>> | null = null;
  const preload = () => (pending ??= load().then((value) => (module = value)));
  const component = lazy(() =>
    module
      ? ({ then: (done: (value: LazyModule<P>) => void) => done(module as LazyModule<P>) } as unknown as Promise<LazyModule<P>>)
      : preload(),
  );
  return { component, preload, loaded: () => module !== null };
}

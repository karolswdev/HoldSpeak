// HS-200-02 (contract C1): the build this loaded page was made from.
//
// `__HOLDSPEAK_BUILD__` is compiled in by the Vite build (web/vite.config.ts),
// so the document identifies its own build without asking the backend. The
// server reads the same id from `build-id.json` beside the emitted assets, and
// captures it once at process start. When the two disagree, the process is
// serving a bundle it did not start with.

declare const __HOLDSPEAK_BUILD__: string | undefined;

/** The compiled-in build id, or "" when this code was not built by Vite. */
export function documentBuildId(): string {
  return typeof __HOLDSPEAK_BUILD__ === "string" ? __HOLDSPEAK_BUILD__ : "";
}

// Fresh build (owner 2026-10-28, "It doesn't even load for me"): a desk tab
// opened before a rebuild asks for chunks of its own build. The hub keeps the
// last three builds' assets (web/scripts/prune-builds.mjs), and this module
// reloads the tab once when the hub serves a newer build.
//
// The desk remembers the hub's build on boot. It reads it again when the
// runtime bus reconnects (the hub restarted) and when a lazy chunk fails to
// load (`vite:preloadError`, or a `load:` import through `watchChunk`). When
// the build differs it reloads once; an unsaved edit gets a Reload bar
// instead. A sessionStorage stamp of the build it reloaded for stops a loop.
import { apiFetch } from "../lib/api";
import { useDesk } from "../desk/store";

export type FreshBuildPhase = "idle" | "reloading" | "offer";

export interface FreshBuildDeps {
  /** The build the hub serves now ("" when unknown). */
  readBuild(): Promise<string>;
  reload(): void;
  /** True while a Note or an Ask holds an edit the hub has not kept. */
  hasUnsavedEdit(): boolean;
  storage: Pick<Storage, "getItem" | "setItem"> | null;
  onPhase(phase: FreshBuildPhase): void;
  /** How long the "reloading" word shows before the reload (ms). */
  delayMs?: number;
}

export const RELOAD_STAMP = "hs.freshBuild.reloadedFor";

export interface FreshBuild {
  start(): Promise<void>;
  check(): Promise<void>;
  reloadNow(): void;
  known(): string;
}

export function createFreshBuild(deps: FreshBuildDeps): FreshBuild {
  let known = "";
  let pending: string | null = null;
  let checking: Promise<void> | null = null;

  const stamp = (build: string) => {
    try {
      deps.storage?.setItem(RELOAD_STAMP, build);
    } catch {
      // No session storage: the reload still happens once per page.
    }
  };
  const stamped = () => {
    try {
      return deps.storage?.getItem(RELOAD_STAMP) ?? "";
    } catch {
      return "";
    }
  };
  const read = async () => {
    try {
      return (await deps.readBuild()) || "";
    } catch {
      return "";
    }
  };

  const run = async () => {
    const next = await read();
    if (!next || pending) return;
    if (!known) {
      known = next;
      return;
    }
    if (next === known) return;
    // A second reload for the same build is refused: the reload did not
    // bring the new build, so another one would only loop.
    if (stamped() === next) return;
    pending = next;
    if (deps.hasUnsavedEdit()) {
      deps.onPhase("offer");
      return;
    }
    stamp(next);
    deps.onPhase("reloading");
    window.setTimeout(() => deps.reload(), deps.delayMs ?? 600);
  };

  return {
    async start() {
      known = await read();
    },
    check() {
      // One read at a time: a burst of failed chunks asks the hub once.
      checking ??= run().finally(() => {
        checking = null;
      });
      return checking;
    },
    reloadNow() {
      if (pending) stamp(pending);
      deps.reload();
    },
    known: () => known,
  };
}

/* ---- the desk's one instance ---- */

const UNSAVED_DRAFT = /^(editor\/note\/|thought\/body\/)/;

/** A Note's unkept edit (its draft lives only until the hub keeps it), or a
 * focused text field that holds words (the Ask composer, a Note body). */
export function deskHasUnsavedEdit(): boolean {
  try {
    const drafts = useDesk.getState().drafts ?? {};
    if (Object.keys(drafts).some((key) => UNSAVED_DRAFT.test(key))) return true;
  } catch {
    // No store: fall through to the focused field.
  }
  const active = typeof document === "undefined" ? null : document.activeElement;
  if (!active) return false;
  if (active instanceof HTMLTextAreaElement) return active.value.trim() !== "";
  if (active instanceof HTMLInputElement)
    return ["text", "search", ""].includes(active.type) && active.value.trim() !== "";
  return (active as HTMLElement).isContentEditable === true && (active.textContent ?? "").trim() !== "";
}

export async function readHubBuild(): Promise<string> {
  const answer = await apiFetch<{ bundle_on_disk?: string; identity?: { frontend_build?: string } }>(
    "/api/system/identity",
  );
  return String(answer.bundle_on_disk || answer.identity?.frontend_build || "");
}

let instance: FreshBuild | null = null;

/** Start the desk's watcher once; `onPhase` draws the bar. */
export function startFreshBuild(
  onPhase: (phase: FreshBuildPhase) => void,
  overrides: Partial<FreshBuildDeps> = {},
): FreshBuild {
  if (instance) return instance;
  let storage: Storage | null = null;
  try {
    storage = window.sessionStorage;
  } catch {
    storage = null;
  }
  const fresh = createFreshBuild({
    readBuild: readHubBuild,
    reload: () => window.location.reload(),
    hasUnsavedEdit: deskHasUnsavedEdit,
    storage,
    onPhase,
    ...overrides,
  });
  instance = fresh;
  void fresh.start();
  window.addEventListener("vite:preloadError", () => void fresh.check());
  return fresh;
}

/** A failed chunk anywhere: read the hub's build again. */
export function noteChunkFailure(): void {
  void instance?.check();
}

/** Wrap a lazy `load:` import so its failure asks for a fresh build. The
 * error still reaches the caller. */
export function watchChunk<T>(load: () => Promise<T>): () => Promise<T> {
  return () =>
    load().catch((error: unknown) => {
      noteChunkFailure();
      throw error;
    });
}

/** Test seam only. */
export function resetFreshBuildForTests(): void {
  instance = null;
}

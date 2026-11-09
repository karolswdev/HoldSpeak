/** An app's own walk (owner, 2026-11-09: "Why is this not a standard thing
 * for each native app?"). An application names its walk in the manifest
 * (`walk` in applications.ts); the script is data in the bundle,
 * `desk/walks/<name>.walk.json`, in the Walk's own format, so an agent or a
 * Program can write one. `open` is the app to open first when the walk runs
 * in a linked sequence (`scripts/walk.py apps`); in place, the steps start in
 * the window of the mast he pressed.
 *
 * Show me runs it through the desk's one WalkRunner: the first press makes a
 * walk record on the hub (`POST /api/walks`), so his answers, his words and
 * the shots land in the feedback store through the same answer route as a
 * linked walk. One runner, one answer path. */
import { CHAIR_WALKS, DESK_APPLICATIONS } from "../applications";
import { createWalk, runLocalWalk, type WalkStep } from "./walk";

export interface AppWalkScript {
  title: string;
  open: { app: string; scope?: string };
  steps: WalkStep[];
}

const FILES = import.meta.glob<AppWalkScript>("../walks/*.walk.json", { eager: true, import: "default" });

/** Every walk in the bundle, by name (`programs` for programs.walk.json). */
export const APP_WALKS: Readonly<Record<string, AppWalkScript>> = Object.fromEntries(
  Object.entries(FILES).map(([path, script]) => [path.replace(/^.*\/|\.walk\.json$/g, ""), script]),
);

/** The walk an app declares (an application key, a window id or a Chair
 * window), or undefined. */
export function appWalkName(app: string | null | undefined): string | undefined {
  if (!app) return undefined;
  if (CHAIR_WALKS[app]) return CHAIR_WALKS[app];
  return DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app)?.walk;
}

/** The app's script, or null when it declares none (no Show me is drawn). */
export function appWalk(app: string | null | undefined): AppWalkScript | null {
  const name = appWalkName(app);
  return name ? APP_WALKS[name] ?? null : null;
}

// One record per app walk for the life of the page: a second press walks
// again and files into the same record (an earlier answer keeps its text).
const records = new Map<string, Promise<string>>();

/** Start the app's walk in place. False when the app declares none. */
export async function startAppWalk(app: string, origin?: string | null): Promise<boolean> {
  const name = appWalkName(app);
  const script = name ? APP_WALKS[name] : undefined;
  if (!name || !script) return false;
  let token = records.get(name);
  if (!token) {
    token = createWalk({ title: script.title, steps: script.steps }).then((made) => made.token);
    records.set(name, token);
    token.catch(() => records.delete(name));
  }
  runLocalWalk(await token, origin ?? undefined);
  return true;
}

/** Tests: forget the records this page made. */
export function forgetAppWalkRecords(): void {
  records.clear();
}

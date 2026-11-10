import { CHAIR_WALKS, DESK_APPLICATIONS } from "../applications";
import { runLocalWalk, type WalkStep } from "./walk";

export interface AppWalkScript {
  title: string;
  open: { app: string; scope?: string };
  steps: WalkStep[];
  review: {ref: string; question: string; choices: string[]};
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

/** Show me reads the bundled steps. Only linked walks use a hub record. */
export async function startAppWalk(app: string, origin?: string | null): Promise<boolean> {
  const script = appWalk(app);
  if (!script) return false;
  runLocalWalk(script, origin ?? app);
  return true;
}

/** Kept for callers that reset page-local walk state in tests. */
export function forgetAppWalkRecords(): void {}

/** The Walk (2026-11-07): a guided feedback walk on the desk from one link.
 *
 * The hub serves `/w/<token>` as the desk at `/?walk=<token>`. The token reads
 * ONLY its own walk and posts its answers (`/api/w/<token>`); it is no owner
 * session. A step opens windows through the desk's own openers (the surface
 * registry and the registry verbs the Dock and Go run), never a new path. */
import { apiFetch } from "../../lib/api";
import { DESK_APPLICATIONS, applicationVerbId } from "../applications";
import { openSurface, openSurfaceOr } from "../shell";

export interface WalkStep {
  open?: { app: string; scope?: string };
  verb?: { verb: string; window?: string };
  highlight?: { target: string; words?: string; window?: string };
  ask?: { ref: string; question: string; choices: string[] };
}

export interface WalkPage {
  title: string;
  steps: WalkStep[];
  answers: Record<string, { choice: string; words?: string; shot?: string; at?: string }>;
}

export interface WalkAnswer {
  ref: string;
  choice: string;
  words?: string;
  window_png?: string;
}

export class WalkError extends Error {
  constructor(public status: number, public code: string, detail: string) {
    super(detail || code);
  }
}

export const SKIP = "skip";

/** The walk token on this address (`?walk=`), or "". */
export function walkTokenFromLocation(): string {
  if (typeof window === "undefined") return "";
  const token = new URLSearchParams(window.location.search).get("walk") ?? "";
  return /^[A-Za-z0-9_-]{43}$/.test(token) ? token : "";
}

/** Take the walk off the address; the windows it opened stay. */
export function clearWalkFromLocation(): void {
  const url = new URL(window.location.href);
  url.searchParams.delete("walk");
  window.history.replaceState(window.history.state, "", url);
}

async function walkFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, { ...init, cache: "no-store", referrerPolicy: "no-referrer" });
  } catch {
    throw new WalkError(0, "unreachable", "The hub does not answer.");
  }
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new WalkError(response.status, String(body?.code ?? "walk_failed"), String(body?.detail ?? ""));
  return body as T;
}

export function readWalk(token: string): Promise<WalkPage> {
  return walkFetch<WalkPage>(`/api/w/${token}`);
}

export function postWalkAnswer(token: string, answer: WalkAnswer): Promise<{ ref: string; choice: string }> {
  return walkFetch(`/api/w/${token}/answer`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(answer),
  });
}

/** The window id an app key names: `chair:needs`, or the application's window. */
export function walkWindowId(app: string): string {
  if (app.startsWith("chair:")) return app;
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  return application?.windowId ?? app;
}

/** `@first-project` and `@first-meeting` name the first of his own; anything
 * else is the scope as written. `null`: there is none. */
export async function resolveWalkScope(scope: string | undefined): Promise<string | undefined | null> {
  if (scope === "@first-project") {
    const read = await apiFetch<{ projects?: Array<{ id?: string }> }>("/api/projects").catch(() => null);
    const id = read?.projects?.find((row) => row?.id)?.id;
    return id ? `project:${id}` : null;
  }
  if (scope === "@first-meeting") {
    const read = await apiFetch<{ meetings?: Array<{ id?: string }> }>("/api/meetings?limit=40").catch(() => null);
    const id = read?.meetings?.find((row) => row?.id)?.id;
    return id ? `meeting:${id}` : null;
  }
  return scope;
}

const CTX = { selectedRef: null };
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Open one app as the Dock and Go do. A surface the desk has not yet
 * registered is tried again for a few seconds before the legacy route. */
export async function openWalkApp(app: string, scope?: string): Promise<boolean> {
  // The registry loads on first use: it reads the window store at import.
  const { verbById } = await import("../verbRegistry");
  if (app.startsWith("chair:")) {
    const verb = verbById(`chair.window.${app.slice("chair:".length)}`);
    if (!verb) return false;
    verb.run(CTX);
    return true;
  }
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  if (!application) return false;
  if (!application.surface) {
    const verb = verbById(applicationVerbId(application));
    if (!verb || verb.ghost(CTX)) return false;
    verb.run(CTX);
    return true;
  }
  for (let attempt = 0; attempt < 30; attempt += 1) {
    if (openSurface(application.action, scope)) return true;
    await wait(200);
  }
  openSurfaceOr(application.action, application.href, scope);
  return true;
}

/** Run one registry verb (the Dock, Go and ⌘K run the same). */
export async function runWalkVerb(id: string): Promise<boolean> {
  const { verbById } = await import("../verbRegistry");
  const verb = verbById(id);
  if (!verb || verb.ghost(CTX)) return false;
  verb.run(CTX);
  return true;
}

function selectorFor(target: string): string {
  return /^[A-Za-z][A-Za-z0-9_-]*$/.test(target) ? `[data-testid="${target}"]` : target;
}

function zOf(element: Element): number {
  const z = Number.parseInt(getComputedStyle(element).zIndex, 10);
  return Number.isFinite(z) ? z : 0;
}

/** The target inside the newest window of the app (the front one first),
 * then in any window, then anywhere on the desk. */
export function findWalkTarget(target: string, app?: string): HTMLElement | null {
  const selector = selectorFor(target);
  const look = (root: ParentNode): HTMLElement | null => {
    try {
      return root.querySelector<HTMLElement>(selector);
    } catch {
      return null;
    }
  };
  const id = app ? walkWindowId(app) : "";
  const windows = Array.from(document.querySelectorAll<HTMLElement>("[data-layer='window']"))
    .sort((left, right) => zOf(right) - zOf(left));
  const own = windows.filter((element) => id && (element.id === id || element.id.startsWith(`${id}:`)));
  for (const root of [...own, ...windows]) {
    const found = look(root);
    if (found) return found;
  }
  const anywhere = look(document);
  return anywhere && !anywhere.closest("[data-walk]") ? anywhere : null;
}

/** Wait for the target: a window paints its core after a lazy load. */
export async function waitForWalkTarget(target: string, app: string | undefined, ms = 6000): Promise<HTMLElement | null> {
  const until = Date.now() + ms;
  for (;;) {
    const found = findWalkTarget(target, app);
    if (found || Date.now() >= until) return found;
    await wait(150);
  }
}

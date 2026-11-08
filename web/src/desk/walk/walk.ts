/** The Walk (2026-11-07): a guided feedback walk on the desk from one link.
 *
 * The hub serves `/w/<token>` as the desk at `/?walk=<token>`. The token reads
 * ONLY its own walk and posts its answers (`/api/w/<token>`); it is no owner
 * session. A step opens windows through the desk's own openers (the surface
 * registry and the registry verbs the Dock and Go run), never a new path. */
import { ApiError, apiFetch } from "../../lib/api";
import { DESK_APPLICATIONS, applicationVerbId } from "../applications";
import { hubSeeded } from "../compositor/hubWindows";
import { openSurface, openSurfaceOr } from "../shell";

/** One step. The keys run in this order: open, verb, press, scroll, say,
 * highlight, ask. `thing` names what the target is ("people rows"): when the
 * window holds none, the guide says "No <thing> here yet" and skips. */
export interface WalkStep {
  open?: { app: string; scope?: string };
  verb?: { verb: string; window?: string };
  /** The guide presses the target itself: the cursor travels, the ring
   * pulses, the real click lands, the face settles for 600 ms. */
  press?: { target: string; words?: string; window?: string; thing?: string };
  /** The guide scrolls the target into the clear area above the sheet. */
  scroll?: { target: string; window?: string; thing?: string };
  /** The guide speaks; nothing is dimmed. */
  say?: { words: string };
  highlight?: { target: string; words?: string; window?: string; thing?: string };
  ask?: { ref: string; question: string; choices: string[] };
}

/** What he saw when he answered: the viewport, its pixel ratio, the image
 * scale, the browser (platform and name only) and the step's part, so the
 * orchestrator can crop the shot. */
export interface WalkView {
  width: number;
  height: number;
  dpr: number;
  scale: number;
  agent: string;
  rect?: { left: number; top: number; width: number; height: number };
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
  view?: WalkView;
}

export class WalkError extends Error {
  constructor(public status: number, public code: string, detail: string) {
    super(detail || code);
  }
}

export const SKIP = "skip";
/** The answer's choice when he sends words and presses no choice. */
export const WORDS = "words";

/** The browser as platform and name only ("iPhone · Safari 26"): no build
 * numbers, no device model beyond the platform. */
export function walkAgent(ua: string): string {
  const platform = /iPhone/.test(ua) ? "iPhone"
    : /iPad/.test(ua) ? "iPad"
      : /Android/.test(ua) ? "Android"
        : /Mac OS X|Macintosh/.test(ua) ? "Mac"
          : /Windows/.test(ua) ? "Windows"
            : /Linux/.test(ua) ? "Linux" : "Other";
  const major = (pattern: RegExp) => ua.match(pattern)?.[1] ?? "";
  const browser = /Edg\//.test(ua) ? `Edge ${major(/Edg\/(\d+)/)}`
    : /Firefox\/|FxiOS\//.test(ua) ? `Firefox ${major(/(?:Firefox|FxiOS)\/(\d+)/)}`
      : /CriOS\/|Chrome\//.test(ua) ? `Chrome ${major(/(?:CriOS|Chrome)\/(\d+)/)}`
        : /Safari\//.test(ua) ? `Safari ${major(/Version\/(\d+)/)}`
          : "Browser";
  return `${platform} · ${browser.trim()}`;
}

/** The guide's words when the window holds no such part. */
export function noneWords(thing: string | undefined): string {
  const name = (thing ?? "").trim();
  return name ? `No ${name} here yet` : "This part is not here yet";
}

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
  // The walk runs inside the desk, so its wire is the typed client (the
  // null-read guard: only lib/api.ts calls fetch). The hub admits the token
  // in the path; an owner header beside it changes nothing.
  try {
    return await apiFetch<T>(path, { ...init, cache: "no-store", referrerPolicy: "no-referrer" });
  } catch (cause) {
    if (cause instanceof ApiError) {
      const body = (cause.payload ?? {}) as { code?: unknown; detail?: unknown };
      throw new WalkError(cause.status, String(body.code ?? "walk_failed"), String(body.detail ?? cause.message ?? ""));
    }
    throw new WalkError(0, "unreachable", "The hub does not answer.");
  }
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
    if (openSurface(application.action, scope)) {
      await showRoomProper(application.action, scope);
      return true;
    }
    await wait(200);
  }
  openSurfaceOr(application.action, application.href, scope);
  await showRoomProper(application.action, scope);
  return true;
}

/** A Project Room opens on the Room itself, never on the Update posture it
 * kept from an earlier visit (walk 2026-11-07: the Room opened on its update
 * document). The Room takes the request once, as its History verb does. */
async function showRoomProper(action: string, scope: string | undefined): Promise<void> {
  if (action !== "open-project-memory" || !scope?.startsWith("project:")) return;
  const { requestRoomAt } = await import("../openObject");
  requestRoomAt(scope.slice("project:".length), "room");
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

/** The window element of an app (the front one when it has several), or
 * null when that window is not open. */
export function findWalkWindow(app: string): HTMLElement | null {
  const id = walkWindowId(app);
  const own = Array.from(document.querySelectorAll<HTMLElement>("[data-layer='window']"))
    .filter((element) => element.id === id || element.id.startsWith(`${id}:`))
    .sort((left, right) => zOf(right) - zOf(left));
  return own[0] ?? null;
}

/** The window a step's part is in: the part's own `window`, else the app
 * the walk opened last. */
export function stepWindow(step: WalkStep, last: string | undefined): string | undefined {
  return step.highlight?.window ?? step.press?.window ?? step.scroll?.window ?? last;
}

export interface WalkPart {
  /** The step's window; null when the step names no app. */
  window: HTMLElement | null;
  target: HTMLElement | null;
}

/** The target ONLY inside the window of the step's app, never in another
 * window (first run 2026-11-07: "the newest window" was an Update draft).
 * A step with no app looks on the desk outside the walk. */
export function findWalkTarget(target: string, app?: string): WalkPart {
  const selector = selectorFor(target);
  const look = (root: ParentNode): HTMLElement | null => {
    try {
      return root.querySelector<HTMLElement>(selector);
    } catch {
      return null;
    }
  };
  if (!app) {
    const anywhere = look(document);
    return { window: null, target: anywhere && !anywhere.closest("[data-walk]") ? anywhere : null };
  }
  const root = findWalkWindow(app);
  return { window: root, target: root ? look(root) : null };
}

/** The ceiling of the target wait, and the ceiling while the step's window
 * still reads its first answers (its loading markers are on). */
export const TARGET_MS = 6000;
export const TARGET_LOADING_MS = 12000;

/** True while a part of the desk reads its first answer. The desk's own
 * marker: a region that reads says `aria-busy` (the loading face of the
 * kit, the Surface state, a pullout that opens a note); the desk sweep
 * settles on the same marker. */
export function walkLoading(root: ParentNode | null): boolean {
  return !!root?.querySelector("[aria-busy='true']");
}

/** The desk is ready for the guide (owner, 2026-11-07, on his iPhone: "the
 * click happened only shortly after the web page loaded… only launch when
 * all is loaded"). All four of the desk's own signals:
 * - the compositor restored its windows: the hub's window list landed
 *   (`hubSeeded`, the flag the Chair's mount rules read);
 * - the desk's first read landed: `#desk-next` is drawn and does not say
 *   `aria-busy` (the "Preparing HoldSpeak" face);
 * - the Dock has drawn (`.desk-dock` has a box);
 * - no window reads its first answer (no `aria-busy` in a window). */
export function deskReady(): boolean {
  if (typeof document === "undefined" || !hubSeeded()) return false;
  const desk = document.getElementById("desk-next");
  if (!desk || desk.getAttribute("aria-busy") === "true") return false;
  const dock = document.querySelector(".desk-dock");
  if (!dock || dock.getBoundingClientRect().height <= 0) return false;
  return !Array.from(document.querySelectorAll("[data-layer='window']")).some(walkLoading);
}

/** The one deliberate beat after the desk is ready: the eye lands before
 * the guide moves. */
export const READY_BEAT_MS = 900;
/** After this long without a ready desk the guide says so and waits. */
export const READY_CEILING_MS = 15000;
export const STILL_LOADING = "The desk is still loading";

/** Wait until the desk is ready; false when the ceiling came first. */
export async function waitForDeskReady(ms = READY_CEILING_MS): Promise<boolean> {
  const until = Date.now() + ms;
  for (;;) {
    if (deskReady()) return true;
    if (Date.now() >= until) return false;
    await wait(100);
  }
}

/** Wait for the target: a window paints its core after a lazy load and
 * reads its first answers after that. The target counts when it is there
 * and its window reads nothing, two looks in a row (a window that mounts
 * says `aria-busy` one frame after its toolbar). The ceiling is 6 s, and
 * 12 s while the window still reads; at the ceiling the part is taken as
 * it is. */
export async function waitForWalkTarget(target: string, app: string | undefined, ms = TARGET_MS,
  loadingMs = TARGET_LOADING_MS): Promise<WalkPart> {
  const start = Date.now();
  let calm = 0;
  for (;;) {
    const found = findWalkTarget(target, app);
    const loading = walkLoading(found.window);
    calm = found.target && !loading ? calm + 1 : 0;
    if (calm >= 2) return found;
    const spent = Date.now() - start;
    if (spent >= (loading ? Math.max(ms, loadingMs) : ms)) return found;
    await wait(150);
  }
}

/** The app's name for a plain line: "Meetings", "Needs you". The Chair
 * module loads on first use, as the registry does (it reads the store). */
export async function walkAppName(app: string): Promise<string> {
  if (app.startsWith("chair:")) {
    const { chairWindowSpec } = await import("../chair/chairWindows");
    return chairWindowSpec(app)?.title ?? app.slice("chair:".length);
  }
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  return application?.label ?? app;
}

/** Wait for the window of an app (a step that asks without a mark). */
export async function waitForWalkWindow(app: string, ms = 6000): Promise<HTMLElement | null> {
  const until = Date.now() + ms;
  for (;;) {
    const found = findWalkWindow(app);
    if (found || Date.now() >= until) return found;
    await wait(150);
  }
}

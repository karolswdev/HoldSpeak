/** One display protocol (2026-11-08): the ONE executor of a display request.
 *
 * The hub asks the desk to show something: `desk.mark`, `desk.press`,
 * `desk.say`, `desk.scroll` (holdspeak/desk_operations.py) arrive as one
 * `desk_request` frame `{request_id, op, args}`; `DeskRequests` runs them
 * here and posts `{done, reason?}` back. The Walk (desk/walk) runs its steps
 * through the same executor: open, verb, raise, mark, press, scroll and say
 * are one implementation, whoever asks. The caller's frame (the Walk's
 * cursor and bar, or the plain request layer) comes in as a `DeskStage`.
 *
 * Windows open through the desk's own openers (the surface registry and the
 * registry verbs the Dock and Go run), never a new path. A part is searched
 * ONLY in the window of its app, never in another window. */
import "./requests.css";
import { speak } from "../../lib/tts";
import { apiFetch } from "../../lib/api";
import { DESK_APPLICATIONS, applicationVerbId } from "../applications";
import { openSurface, openSurfaceOr } from "../shell";
import { frontWindow, isFrontWindow, loadingIn, lookIn, lookOnDesk, markPart, selectorFor } from "./dom";

export interface DeskRequest {
  op: string;
  args?: Record<string, unknown>;
}

/** A part of the desk: its window (null when the request names no app) and
 * the part itself (null when it is not there). */
export interface DeskPart {
  window: HTMLElement | null;
  target: HTMLElement | null;
}

export interface DeskResult {
  done: boolean;
  spoken?: boolean;
  reason?: string;
  /** What was missing: the step's window, or the part in it. */
  missing?: "window" | "part" | "scope";
  /** The part the request found (a mark, a press, a scroll). */
  part?: DeskPart;
}

/** The caller's frame. Each hook is optional; without it the plain desk
 * behaviour runs (an agent's request on the owner's desk). */
export interface DeskStage {
  /** Walk voice preference; captions still show when it is off. */
  voice?: boolean;
  /** False once the caller is gone (the Walk moved on): stop quietly. */
  alive?(): boolean;
  undo?(args: Record<string, unknown>): Promise<void> | void;
  /** Bring the found part into view (the Walk: into its clear band). */
  reveal?(part: DeskPart): Promise<void> | void;
  /** Everything before the click (the Walk: the cursor flight and the tap).
   * Default: the kit's pressed look for PRESS_LOOK_MS. */
  press?(target: HTMLElement): Promise<void>;
  /** The mark (the Walk holds its halo itself while it asks). Default: the
   * halo for MARK_MS. */
  mark?(part: DeskPart, words: string): Promise<void> | void;
  /** The words of a say, and of a mark, press or scroll that has words
   * (the Walk shows its words in its own frame; default: none shown). */
  say?(words: string): Promise<void> | void;
}

/** The pressed look of the guide's tap. */
export const PRESS_LOOK_MS = 120;
/** How long an agent's mark stays on the part. */
export const MARK_MS = 4000;
/** The ceiling of the part wait, and the ceiling while the part's window
 * still reads its first answers (its loading markers are on). */
export const TARGET_MS = 6000;
export const TARGET_LOADING_MS = 12000;

const CTX = { selectedRef: null };
const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
const text = (value: unknown): string => (typeof value === "string" ? value : "");

/** The words when the window holds no such part. */
export function noneWords(thing: string | undefined): string {
  const name = (thing ?? "").trim();
  return name ? `No ${name} here yet` : "This part is not here yet";
}

/** The window id an app key names: `chair:needs`, or the application's window. */
export function deskWindowId(app: string): string {
  if (app.startsWith("chair:")) return app;
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  return application?.windowId ?? app;
}

/** `@first-project` and `@first-meeting` name the first of his own; anything
 * else is the scope as written. `null`: there is none. */
export async function resolveScope(scope: string | undefined): Promise<string | undefined | null> {
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

/** Open one app as the Dock and Go do. A surface the desk has not yet
 * registered is tried again for a few seconds before the legacy route. */
export async function openDeskApp(app: string, scope?: string): Promise<boolean> {
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
export async function runDeskVerb(id: string): Promise<boolean> {
  const { verbById } = await import("../verbRegistry");
  const verb = verbById(id);
  if (!verb || verb.ghost(CTX)) return false;
  verb.run(CTX);
  return true;
}

/** The window element of an app (the front one when it has several), or
 * null when that window is not open. */
export function findDeskWindow(app: string): HTMLElement | null {
  const declared = frontWindow(deskWindowId(app));
  if (declared) return declared;
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  // Some retained hosts use the action as their mounted id. The mounted
  // frame is the display authority, including an app's own Show me origin.
  return frontWindow(app) ?? (application ? frontWindow(application.action) : null);
}

/** Bring a desk window to the front (the store's raise, the same the Dock
 * and the Window menu run). The store loads lazily: a static import makes a
 * cycle at module load, as hubWindows does. */
export async function raiseDeskWindow(element: HTMLElement): Promise<void> {
  try {
    const { useDesk } = await import("../store");
    useDesk.getState().focusPanel(element.id);
  } catch {
    // A page without the desk store has nothing to raise.
  }
}

/** The part ONLY inside the window of its app, never in another window
 * (first walk 2026-11-07: "the newest window" was an Update draft). A
 * request with no app looks on the desk outside the guide's layer. */
export function findPart(target: string, app?: string): DeskPart {
  const selector = selectorFor(target);
  if (!app) return { window: null, target: lookOnDesk(selector) };
  const root = findDeskWindow(app);
  return { window: root, target: root ? lookIn(root, selector) : null };
}

/** Wait for the part: a window paints its core after a lazy load and reads
 * its first answers after that. The part counts when it is there and its
 * window reads nothing, two looks in a row (a window that mounts says
 * `aria-busy` one frame after its toolbar). The ceiling is 6 s, and 12 s
 * while the window still reads; at the ceiling the part is taken as it is. */
export async function waitForPart(target: string, app: string | undefined, ms = TARGET_MS,
  loadingMs = TARGET_LOADING_MS): Promise<DeskPart> {
  const start = Date.now();
  let calm = 0;
  for (;;) {
    const found = findPart(target, app);
    const loading = loadingIn(found.window);
    calm = found.target && !loading ? calm + 1 : 0;
    if (calm >= 2) return found;
    const spent = Date.now() - start;
    if (spent >= (loading ? Math.max(ms, loadingMs) : ms)) return found;
    await wait(150);
  }
}

/** The app's name for a plain line: "Meetings", "Needs you". The Chair
 * module loads on first use, as the registry does (it reads the store). */
export async function deskAppName(app: string): Promise<string> {
  if (app.startsWith("chair:")) {
    const { chairWindowSpec } = await import("../chair/chairWindows");
    return chairWindowSpec(app)?.title ?? app.slice("chair:".length);
  }
  const application = DESK_APPLICATIONS.find((row) => row.action === app || row.windowId === app);
  return application?.label ?? app;
}

/** Wait for the window of an app (a Walk step that asks without a mark). */
export async function waitForDeskWindow(app: string, ms = 6000): Promise<HTMLElement | null> {
  const until = Date.now() + ms;
  for (;;) {
    const found = findDeskWindow(app);
    if (found || Date.now() >= until) return found;
    await wait(150);
  }
}

const STOPPED: DeskResult = { done: false, reason: "stopped" };

/** The request's part: in its window only, the window raised to the front
 * (on the phone Needs you opened behind Programs and the shot was
 * Programs), then revealed. A result when it is not there. */
async function partFor(args: Record<string, unknown>, stage: DeskStage): Promise<DeskPart | DeskResult> {
  const app = text(args.window) || undefined;
  const part = await waitForPart(text(args.target), app);
  if (stage.alive && !stage.alive()) return STOPPED;
  if (app && !part.window) {
    return { done: false, reason: `The ${await deskAppName(app)} window is not open`, missing: "window" };
  }
  if (!part.target) return { done: false, reason: noneWords(text(args.thing) || undefined), missing: "part" };
  if (part.window && !isFrontWindow(part.window)) {
    await raiseDeskWindow(part.window);
    await frame();
    await frame();
  }
  if (stage.reveal) await stage.reveal(part);
  else part.target.scrollIntoView?.({ block: "center", inline: "nearest" });
  await frame();
  return part;
}

const isResult = (value: DeskPart | DeskResult): value is DeskResult => "done" in value;

/** Run one display request; `{done, reason}` says what happened. */
export async function executeDeskRequest(request: DeskRequest, stage: DeskStage = {}): Promise<DeskResult> {
  const args = request.args ?? {};
  switch (request.op) {
    case "undo":
      await stage.undo?.(args);
      return { done: true };
    case "open": {
      const scope = await resolveScope(text(args.scope) || undefined);
      if (scope === null) {
        const none = args.scope === "@first-meeting" ? "No meeting yet" : "No project yet";
        return { done: false, reason: none, missing: "scope" };
      }
      if (stage.alive && !stage.alive()) return STOPPED;
      const app = text(args.app);
      return (await openDeskApp(app, scope)) ? { done: true } : { done: false, reason: `No ${app} here` };
    }
    case "verb":
      return (await runDeskVerb(text(args.verb))) ? { done: true } : { done: false, reason: "This verb is not here now" };
    case "raise": {
      const app = text(args.window);
      const found = findDeskWindow(app);
      if (!found) return { done: false, reason: `The ${await deskAppName(app)} window is not open`, missing: "window" };
      await raiseDeskWindow(found);
      return { done: true };
    }
    case "say": {
      const words = text(args.words);
      await stage.say?.(words);
      let spoken = false;
      if (stage.voice !== false) {
        try { spoken = (await speak(words)) === true; } catch { /* Words stay visible without a voice. */ }
      }
      return { done: true, spoken };
    }
    case "mark":
    case "press":
    case "scroll": {
      const part = await partFor(args, stage);
      if (isResult(part)) return part;
      const target = part.target as HTMLElement;
      if (text(args.words)) await stage.say?.(text(args.words));
      if (request.op === "mark") {
        if (stage.mark) await stage.mark(part, text(args.words));
        else {
          markPart(target, "halo", true);
          setTimeout(() => markPart(target, "halo", false), MARK_MS);
        }
      }
      if (request.op === "press") {
        if (stage.press) await stage.press(target);
        else {
          markPart(target, "pressed", true);
          await wait(PRESS_LOOK_MS);
          markPart(target, "pressed", false);
        }
        if (stage.alive && !stage.alive()) return STOPPED;
        target.click();
      }
      return { done: true, part };
    }
    default:
      return { done: false, reason: `No display request ${request.op}` };
  }
}

/** The compositor's answer to the hub. */
export function postDeskResult(requestId: string, result: DeskResult): Promise<unknown> {
  return apiFetch(`/api/desk/requests/${encodeURIComponent(requestId)}/result`, {
    method: "POST",
    json: { done: result.done, ...(result.spoken !== undefined ? { spoken: result.spoken } : {}), ...(result.reason ? { reason: result.reason } : {}) },
  });
}

/** The Walk (2026-11-07): a guided feedback walk on the desk from one link.
 *
 * The hub serves `/w/<token>` as the desk at `/?walk=<token>`. The token reads
 * ONLY its own walk and posts its answers (`/api/w/<token>`); it is no owner
 * session. A step runs through the desk's one executor of display requests
 * (compositor/requests.ts): the hub's desk.mark and a Walk step are one
 * implementation. */
import { ApiError, apiFetch } from "../../lib/api";
import { deskReady } from "../compositor/dom";

/** One step. The keys run in this order: open, verb, press, scroll, say,
 * highlight, ask. `thing` names what the target is ("people rows"): when the
 * window holds none, the guide says "No <thing> here yet" and skips. */
export interface WalkStep {
  open?: { app: string; scope?: string };
  verb?: { verb: string; window?: string };
  /** The guide presses the target itself: the cursor travels, hovers and
   * taps, the real click lands, the face settles for 600 ms. */
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

/** The owner makes a walk record (`POST /api/walks`): the same record a
 * linked walk has, so an app's own walk files its answers and shots in the
 * same feedback store, through the same answer route. */
export function createWalk(script: { title: string; steps: WalkStep[] }): Promise<{ id: string; token: string }> {
  return walkFetch(`/api/walks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(script),
  });
}

/** A walk that runs in place (an app's Show me): its record's token and the
 * window it starts in (the window of the mast he pressed). */
export interface LocalWalk {
  token: string;
  origin?: string;
  /** Counts the starts: a second press starts the walk again. */
  run: number;
}

const localListeners = new Set<(walk: LocalWalk) => void>();
let localRuns = 0;

/** Start a walk in place: the desk's one WalkRunner takes it. */
export function runLocalWalk(token: string, origin?: string): void {
  localRuns += 1;
  const walk = { token, origin, run: localRuns };
  localListeners.forEach((listener) => listener(walk));
}

export function onLocalWalk(listener: (walk: LocalWalk) => void): () => void {
  localListeners.add(listener);
  return () => { localListeners.delete(listener); };
}

/** The window a step's part is in: the part's own `window`, else the app
 * the walk opened last. */
export function stepWindow(step: WalkStep, last: string | undefined): string | undefined {
  return step.highlight?.window ?? step.press?.window ?? step.scroll?.window ?? last;
}

/** The desk is ready for the guide (owner, 2026-11-07, on his iPhone: "the
 * click happened only shortly after the web page loaded… only launch when
 * all is loaded"). All four of the desk's own signals:
 * - the compositor restored its windows: the hub's window list landed
 *   (`hubSeeded`, the flag the Chair's mount rules read);
 * - the desk's first read landed: `#desk-next` is drawn and does not say
 *   `aria-busy` (the "Preparing HoldSpeak" face);
 * - the Dock has drawn (`.desk-dock` has a box);
 * - no window reads its first answer (no `aria-busy` in a window).
 * `deskReady` (compositor/dom.ts) reads all four. */

/** The one deliberate beat after the desk is ready: the eye lands before
 * the guide moves. */
export const READY_BEAT_MS = 900;
/** After this long without a ready desk the guide says so and waits. */
export const READY_CEILING_MS = 15000;
export const STILL_LOADING = "The desk is still loading";

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/** Wait until the desk is ready; false when the ceiling came first. */
export async function waitForDeskReady(ms = READY_CEILING_MS): Promise<boolean> {
  const until = Date.now() + ms;
  for (;;) {
    if (deskReady()) return true;
    if (Date.now() >= until) return false;
    await wait(100);
  }
}

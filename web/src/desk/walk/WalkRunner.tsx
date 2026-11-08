/** The Walk (2026-11-07; hand-held 2026-11-08): the desk runs a walk script
 * step by step.
 *
 * For the whole walk a thin pixel frame marches around the viewport inside
 * the safe area, and the guide (the Dock's pixel robot) sits at its top-left
 * corner with one bubble that carries the step's words: the one constant
 * signal "the guide holds this" (owner, 2026-11-07, on his iPhone: "a lot
 * more obvious we are being hand-held, with a very thin pixely AI border").
 *
 * A step opens a window (the desk's own openers), runs a verb, PRESSES a
 * part itself (a pixel cursor travels to it, the ring pulses, the real click
 * lands), scrolls a part into the clear area, says words, marks one part
 * and asks one question. The mark is a dim of four rectangles around the
 * part (nothing over the part: it stays live) and a 2 px accent ring. A
 * part is searched ONLY in the window of the step's app; when the window is
 * not open, or holds no such part, the guide says so and the step is
 * skipped without a question. The question is a card beside the part, or
 * at phone width one sheet above the dock (Keep and Redo side by side, Say
 * more with the mic inline, Skip; swipe the handle down to skip). A choice
 * captures the WHOLE viewport as he sees it (the walk's chrome hidden for
 * that frame) with the viewport, the pixel ratio, the browser and the part's
 * box, posts the answer and goes on. Words never choose: Send with words and
 * no choice stores the choice "words". Esc skips.
 * The guide speaks its words and each question through the desk's one TTS
 * seam (lib/tts: the hub voice, else the browser voice). The voice is on by
 * default on a touch device and off on the desk (the sheet's speaker
 * toggle, kept per device); with the voice on, the walk waits for one tap
 * (iOS plays audio only after a gesture).
 * A token the hub refuses gives one plain line, then the desk as usual. */
import "./walk.css";
import {
  useCallback, useEffect, useLayoutEffect, useRef, useState,
  type CSSProperties, type KeyboardEvent as ReactKeyboardEvent, type PointerEvent as ReactPointerEvent,
} from "react";
import { Button } from "../../components/signal/Signal";
import { PadGadget } from "../surface/gadgets";
import { captureScale, captureViewportPng } from "../feedback/capture";
import { SYSTEM } from "../systemSprites";
import { VerbGlyph } from "../components/window/VerbGlyph";
import { onStateChange, speak, stop as stopVoice } from "../../lib/tts";
import { play } from "../../lib/sfx";
import { useCompactViewport } from "../useCompactViewport";
import {
  SKIP,
  WORDS,
  clearWalkFromLocation,
  noneWords,
  openWalkApp,
  postWalkAnswer,
  readWalk,
  resolveWalkScope,
  runWalkVerb,
  stepWindow,
  waitForWalkTarget,
  waitForWalkWindow,
  walkAgent,
  walkAppName,
  walkTokenFromLocation,
  type WalkPage,
  type WalkPart,
  type WalkView,
} from "./walk";

interface Rect { left: number; top: number; width: number; height: number }

interface Stage {
  ready: boolean;
  target: HTMLElement | null;
  /** The window of the step's app: the part is in it, the shot is of it. */
  window: HTMLElement | null;
  /** One plain line under the words: a missing part, a skipped step. */
  line: string;
}

const EMPTY: Stage = { ready: false, target: null, window: null, line: "" };

/** The guide's voice, kept per device. */
const VOICE_KEY = "hs:walk-voice";

function voiceDefault(): boolean {
  try {
    const kept = window.localStorage.getItem(VOICE_KEY);
    if (kept === "on" || kept === "off") return kept === "on";
  } catch {
    // No storage: the device default.
  }
  return typeof window.matchMedia === "function" && window.matchMedia("(pointer: coarse)").matches;
}

function keepVoice(on: boolean): void {
  try {
    window.localStorage.setItem(VOICE_KEY, on ? "on" : "off");
  } catch {
    // No storage: the choice holds for this walk only.
  }
}

interface Cursor { from: { x: number; y: number }; to: { x: number; y: number }; pressing: boolean }

/** The 16 x 16 pixel arrow the guide presses with (two px a pixel). It
 * travels from the bubble to the part on a slight arc in 500 ms, then
 * presses with a two-frame squash. */
function PixelCursor({ cursor }: { cursor: Cursor }) {
  const ref = useRef<SVGSVGElement | null>(null);
  const { from, to } = cursor;
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element || typeof element.animate !== "function") return;
    if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const lift = Math.min(80, Math.hypot(to.x - from.x, to.y - from.y) / 4);
    const at = (x: number, y: number) => `translate(${x}px, ${y}px)`;
    element.animate([
      { transform: at(from.x, from.y) },
      { transform: at((from.x + to.x) / 2 + lift / 2, (from.y + to.y) / 2 - lift), offset: 0.5 },
      { transform: at(to.x, to.y) },
    ], { duration: 500, easing: "cubic-bezier(0.16, 1, 0.3, 1)" });
  }, [from.x, from.y, to.x, to.y]);
  return (
    <svg ref={ref} className="walk-cursor" aria-hidden="true" data-testid="walk-cursor" viewBox="0 0 16 16"
      width="32" height="32" shapeRendering="crispEdges" data-pressing={cursor.pressing ? "" : undefined}
      style={{ transform: `translate(${to.x}px, ${to.y}px)` }}>
      <g className="walk-cursor-body">
        <path className="walk-cursor-edge"
          d="M0 0h2v1h1v1h1v1h1v1h1v1h1v1h1v1h1v1h1v1h1v2H8v1h1v2h1v2H8v-1H7v-2H6v-1H5v1H4v1H3v1H2v1H0z" />
        <path className="walk-cursor-fill"
          d="M1 2h1v1h1v1h1v1h1v1h1v1h1v1h1v1h1v1H7v1h1v2h1v1H8v-1H7v-2H6v-1H5v1H4v1H3v1H2v1H1z" />
      </g>
    </svg>
  );
}

/** The ring: an accent outline that draws itself in, breathes twice and
 * settles. The element is over no part: it only draws. */
function Ring({ box, press }: { box: Rect; press?: boolean }) {
  return (
    <div className="walk-ring" aria-hidden="true" data-press={press ? "" : undefined}
      data-testid={press ? "walk-press-ring" : "walk-ring"}
      style={{ left: box.left - RING, top: box.top - RING, width: box.width + RING * 2, height: box.height + RING * 2 }}>
      <svg className="walk-ring-line" width="100%" height="100%">
        <rect x="1" y="1" width="100%" height="100%" rx="8" pathLength={100} />
      </svg>
    </div>
  );
}

/** A tiny pixel mark on a choice: a check for Keep, a turn for Redo. */
function ChoiceGlyph({ tone }: { tone: string }) {
  const d = tone === "ok" ? "M1 4h1v1h1v1h1V5h1V4h1V3h1V2h1v2H7v1H6v1H5v1H4v1H3V7H2V6H1z"
    : tone === "warn" ? "M3 0h1v1h4v1h1v5H8v1H3V7h5V2H4v1H3V2H2V1h1z"
      : "M3 1h2v2h2v2H5v2H3V5H1V3h2z";
  return (
    <svg className="walk-choice-glyph" viewBox="0 0 9 9" width="18" height="18" shapeRendering="crispEdges"
      aria-hidden="true"><path d={d} /></svg>
  );
}

/** The hue of a choice: Keep confirms, Redo asks for attention. */
function choiceTone(choice: string): "ok" | "warn" | "accent" {
  const word = choice.trim().toLowerCase();
  if (["keep", "yes", "good", "ok"].includes(word)) return "ok";
  if (["redo", "no", "fix", "change"].includes(word)) return "warn";
  return "accent";
}

/** The frame: four pixel edges inside the safe area, marching calmly. */
function WalkFrame() {
  return (
    <div className="walk-frame" aria-hidden="true" data-testid="walk-frame">
      <span className="walk-frame-edge" data-edge="top" />
      <span className="walk-frame-edge" data-edge="right" />
      <span className="walk-frame-edge" data-edge="bottom" />
      <span className="walk-frame-edge" data-edge="left" />
    </div>
  );
}
/** The phone sheet: at this width or less (or at the desk's compact
 * breakpoint) the card is one full-width sheet at the bottom. */
export const SHEET_MAX_WIDTH = 480;
/** The sheet is at most this part of the viewport height. */
const SHEET_HEIGHT = 0.4;
const RING = 6;
const GAP = 16;

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
/** The cursor's travel and the face's settle after a press (the brief). */
const TRAVEL_MS = 500;
const SETTLE_MS = 600;
/** A swipe down on the sheet's handle this far skips the step. */
const SWIPE_PX = 48;

/** How long the guide speaks a `say` step: about a reading pace. */
function readingMs(words: string): number {
  return Math.min(4000, 1200 + words.length * 30);
}

/** The viewport as he sees it now, and the part's box (for the crop). */
function viewNow(target: HTMLElement | null): WalkView {
  const view: WalkView = {
    width: window.innerWidth,
    height: window.innerHeight,
    dpr: window.devicePixelRatio || 1,
    scale: captureScale(),
    agent: walkAgent(navigator.userAgent || ""),
  };
  if (target?.isConnected) {
    const box = rectOf(target);
    view.rect = { left: Math.round(box.left), top: Math.round(box.top),
      width: Math.round(box.width), height: Math.round(box.height) };
  }
  return view;
}

function rectOf(element: Element): Rect {
  const box = element.getBoundingClientRect();
  return { left: box.left, top: box.top, width: box.width, height: box.height };
}

function sameRect(a: Rect | null, b: Rect | null): boolean {
  return !!a && !!b && a.left === b.left && a.top === b.top && a.width === b.width && a.height === b.height;
}

/** The dim as four rectangles around the part (top, bottom, left, right).
 * No element is over the part, so it takes the pointer at once, also in the
 * frame it moves (first run 2026-11-07: a clip-path cut-out lagged its part
 * and took the press). Each side is clamped to the viewport. */
export function dimRects(rect: Rect, width: number, height: number): Record<"top" | "bottom" | "left" | "right", Rect> {
  const x = Math.max(0, Math.min(width, rect.left - RING));
  const y = Math.max(0, Math.min(height, rect.top - RING));
  const right = Math.max(x, Math.min(width, rect.left + rect.width + RING));
  const bottom = Math.max(y, Math.min(height, rect.top + rect.height + RING));
  return {
    top: { left: 0, top: 0, width, height: y },
    bottom: { left: 0, top: bottom, width, height: height - bottom },
    left: { left: 0, top: y, width: x, height: bottom - y },
    right: { left: right, top: y, width: width - right, height: bottom - y },
  };
}

/** Beside the part: right, else left, else under it, else over it. */
export function placeCard(rect: Rect, card: { width: number; height: number }, width: number, height: number):
  { left: number; top: number; side: "right" | "left" | "below" | "above" } {
  const clampTop = (top: number) => Math.max(8, Math.min(top, height - card.height - 8));
  const clampLeft = (left: number) => Math.max(8, Math.min(left, width - card.width - 8));
  const right = rect.left + rect.width + RING + GAP;
  if (right + card.width <= width - 8) return { left: right, top: clampTop(rect.top), side: "right" };
  const left = rect.left - RING - GAP - card.width;
  if (left >= 8) return { left, top: clampTop(rect.top), side: "left" };
  const below = rect.top + rect.height + RING + GAP;
  if (below + card.height <= height - 8) return { left: clampLeft(rect.left), top: below, side: "below" };
  return { left: clampLeft(rect.left), top: clampTop(rect.top - RING - GAP - card.height), side: "above" };
}

/** The nearest scrolling box of the part inside its window, or null. */
function scrollerOf(element: HTMLElement, root: HTMLElement | null): HTMLElement | null {
  for (let node = element.parentElement; node; node = node.parentElement) {
    const overflow = getComputedStyle(node).overflowY;
    if (overflow === "auto" || overflow === "scroll") return node;
    if (node === root) break;
  }
  return null;
}

/** Scroll the part into the clear band between `floor` (under the guide)
 * and `limit` (the sheet's top): centred in the band, or its top edge when
 * it is taller. A part already in the band does not move. */
export function revealAbove(target: HTMLElement, root: HTMLElement | null, limit: number, floor = 0): void {
  const box = target.getBoundingClientRect();
  const scroller = scrollerOf(target, root);
  const top = Math.max(scroller ? scroller.getBoundingClientRect().top : 0, floor, 0);
  if (box.top >= top + RING && box.bottom <= limit - RING) return;
  const room = limit - top;
  const want = box.height + RING * 2 > room ? top + RING : top + (room - box.height) / 2;
  const delta = Math.round(box.top - want);
  if (scroller) scroller.scrollTop += delta;
  else target.scrollIntoView?.({ block: "start", inline: "nearest" });
}

function dockHeight(): number {
  if (typeof document === "undefined") return 0;
  return parseFloat(getComputedStyle(document.documentElement).getPropertyValue("--desk-dock-h")) || 0;
}

function useViewport(): { width: number; height: number } {
  const read = () => ({ width: window.innerWidth, height: window.innerHeight });
  const [size, setSize] = useState(read);
  useEffect(() => {
    const onResize = () => setSize(read());
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  return size;
}

/** "Thanks · 7 answers"; no count of zero. */
function thanksWords(answered: number): string {
  if (!answered) return "Thanks";
  return answered === 1 ? "Thanks · 1 answer" : `Thanks · ${answered} answers`;
}

/** "3 of 7"; nothing when the step has no card. */
function stepCount(position: number, total: number): string {
  return position > 0 && total > 0 ? `${position} of ${total}` : "";
}

export function WalkRunner() {
  const [token] = useState(walkTokenFromLocation);
  return token ? <WalkSession token={token} /> : null;
}

function WalkSession({ token }: { token: string }) {
  const compact = useCompactViewport();
  const viewport = useViewport();
  const sheet = compact || viewport.width <= SHEET_MAX_WIDTH;
  // Read once per step: a resize does not run the step again.
  const sheetRef = useRef(sheet);
  sheetRef.current = sheet;
  const [page, setPage] = useState<WalkPage | null>(null);
  const [refused, setRefused] = useState("");
  const [index, setIndex] = useState(0);
  const [stage, setStage] = useState<Stage>(EMPTY);
  const [rect, setRect] = useState<Rect | null>(null);
  const [answered, setAnswered] = useState(0);
  const [closed, setClosed] = useState(false);
  const [busy, setBusy] = useState("");
  const [failure, setFailure] = useState("");
  const [sayMore, setSayMore] = useState(false);
  const [words, setWords] = useState("");
  const [cardSize, setCardSize] = useState({ width: 340, height: 220 });
  // The guide's words, its cursor and the ring of a press.
  const [spoken, setSpoken] = useState("");
  const [cursor, setCursor] = useState<Cursor | null>(null);
  const [talking, setTalking] = useState(false);
  // The steps he answered (the progress dots): index → choice.
  const [answeredAt, setAnsweredAt] = useState<Record<number, true>>({});
  const [pressed, setPressed] = useState<Rect | null>(null);
  // One frame without the walk's chrome: the shot is the screen he sees.
  const [capturing, setCapturing] = useState(false);
  // The voice, and (with the voice on) the one tap that lets it play.
  const [voice, setVoice] = useState(voiceDefault);
  const [begun, setBegun] = useState(() => !voiceDefault());
  const voiceRef = useRef(voice);
  voiceRef.current = voice;
  const saidRef = useRef("");
  const cardRef = useRef<HTMLElement | null>(null);
  const guideRef = useRef<HTMLDivElement | null>(null);
  const appRef = useRef<string | undefined>(undefined);
  const swipeRef = useRef<number | null>(null);

  useEffect(() => {
    let alive = true;
    readWalk(token).then(
      (read) => { if (alive) setPage(read); },
      () => {
        if (!alive) return;
        clearWalkFromLocation();
        setRefused("This walk link does not open. The desk is as usual.");
      },
    );
    return () => { alive = false; };
  }, [token]);

  // The refusal line gets out of the way.
  useEffect(() => {
    if (!refused) return;
    const timer = setTimeout(() => setClosed(true), 8000);
    return () => clearTimeout(timer);
  }, [refused]);

  const steps = page?.steps ?? [];
  const done = !!page && index >= steps.length;
  const step = page && !done && begun ? steps[index] : undefined;

  const advance = useCallback(() => {
    setStage(EMPTY);
    setRect(null);
    setFailure("");
    setSayMore(false);
    setWords("");
    setCursor(null);
    setPressed(null);
    setIndex((value) => value + 1);
  }, []);

  /** The top of the clear band: under the guide and its bubble. */
  const clearTop = () => {
    const guide = guideRef.current?.getBoundingClientRect();
    return guide && guide.height ? guide.bottom + GAP / 2 : 0;
  };
  /** The bottom of the clear band: the sheet's top (an estimate before it
   * is drawn), else the viewport's foot. */
  const clearBottom = () => {
    const height = window.innerHeight;
    if (!sheetRef.current) return height;
    const card = cardRef.current?.getBoundingClientRect();
    if (card && card.height) return card.top - GAP / 2;
    return height - dockHeight() - Math.floor(height * SHEET_HEIGHT) - GAP / 2;
  };

  // Run one step: open, verb, press, scroll, say, then find the part to mark.
  useEffect(() => {
    if (!step) return;
    let alive = true;
    /** The guide says why, and the step goes by without a question. */
    const skipWith = async (line: string) => {
      setSpoken("");
      setStage({ ready: true, target: null, window: null, line });
      await wait(1600);
      if (alive) advance();
    };
    /** The step's part, in the step's window only, scrolled into the clear
     * band; null after the guide said it is not there. */
    const partOf = async (target: string, app: string | undefined, thing?: string): Promise<WalkPart | null> => {
      const part = await waitForWalkTarget(target, app);
      if (!alive) return null;
      if (app && !part.window) {
        const name = await walkAppName(app);
        if (alive) await skipWith(`The ${name} window is not open · This step is skipped`);
        return null;
      }
      if (!part.target) {
        await skipWith(noneWords(thing));
        return null;
      }
      revealAbove(part.target, part.window, clearBottom(), clearTop());
      await frame();
      return part;
    };
    void (async () => {
      setSpoken(step.say?.words ?? step.press?.words ?? step.highlight?.words ?? "");
      if (step.open) {
        const scope = await resolveWalkScope(step.open.scope);
        if (!alive) return;
        if (scope === null) {
          const none = step.open.scope === "@first-meeting" ? "No meeting yet" : "No project yet";
          await skipWith(`${none} · This step is skipped`);
          return;
        }
        await openWalkApp(step.open.app, scope);
        appRef.current = step.open.app;
      }
      if (!alive) return;
      if (step.verb) {
        await runWalkVerb(step.verb.verb);
        if (step.verb.window) appRef.current = step.verb.window;
      }
      const app = stepWindow(step, appRef.current);
      if (step.press) {
        // The guide presses; he watches. The cursor leaves the bubble.
        const part = await partOf(step.press.target, step.press.window ?? appRef.current, step.press.thing);
        if (!part?.target || !alive) return;
        const guide = guideRef.current?.getBoundingClientRect();
        const from = guide ? { x: guide.left + 24, y: guide.top + 24 } : { x: 24, y: 24 };
        const box = rectOf(part.target);
        const to = { x: box.left + box.width / 2, y: box.top + box.height / 2 };
        setCursor({ from, to, pressing: false });
        await wait(TRAVEL_MS);
        if (!alive) return;
        setCursor({ from: to, to, pressing: true });
        setPressed(rectOf(part.target));
        part.target.click();
        await wait(SETTLE_MS);
        if (!alive) return;
        setCursor(null);
        setPressed(null);
      }
      if (step.scroll) {
        const part = await partOf(step.scroll.target, step.scroll.window ?? appRef.current, step.scroll.thing);
        if (!part || !alive) return;
        await wait(300);
      }
      if (!alive) return;
      if (step.highlight?.words) setSpoken(step.say?.words ?? step.highlight.words);
      if (!step.highlight && !step.ask) {
        await wait(step.say ? readingMs(step.say.words) : 400);
        if (alive) advance();
        return;
      }
      // The step's window: the mark's own, else the app the walk opened last.
      let part: WalkPart = { window: null, target: null };
      if (step.highlight) {
        const found = await partOf(step.highlight.target, app, step.highlight.thing);
        if (!found) return;
        part = found;
      } else if (app) {
        part = { window: await waitForWalkWindow(app), target: null };
        if (!alive) return;
        if (!part.window) {
          const name = await walkAppName(app);
          if (alive) await skipWith(`The ${name} window is not open · This step is skipped`);
          return;
        }
      }
      if (!alive) return;
      setStage({ ready: true, target: part.target, window: part.window, line: "" });
    })();
    return () => { alive = false; };
  }, [step, advance]);

  // Follow the part while windows move, scroll or resize.
  useEffect(() => {
    const target = stage.target;
    if (!target) return;
    let handle = 0;
    let last: Rect | null = null;
    const tick = () => {
      if (!target.isConnected) {
        setRect(null);
        return;
      }
      const next = rectOf(target);
      if (!sameRect(last, next)) {
        last = next;
        setRect(next);
      }
      handle = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(handle);
  }, [stage.target]);

  useLayoutEffect(() => {
    const card = cardRef.current;
    if (!card) return;
    const box = card.getBoundingClientRect();
    if (box.width && box.height && (box.width !== cardSize.width || box.height !== cardSize.height)) {
      setCardSize({ width: box.width, height: box.height });
    }
  });

  // The sheet: full width above the dock, at most 40 % of the height.
  const dock = sheet ? dockHeight() : 0;
  const sheetMax = Math.floor(viewport.height * SHEET_HEIGHT);
  const sheetTop = viewport.height - dock - Math.min(cardSize.height, sheetMax);

  // At phone width the part scrolls into the band above the sheet.
  useLayoutEffect(() => {
    const target = stage.target;
    if (!sheet || !target || !cardRef.current) return;
    revealAbove(target, stage.window, sheetTop - GAP / 2, clearTop());
  }, [sheet, stage.target, stage.window, sheetTop]);

  // Focus goes to the card when it asks; it never jumps out (Tab wraps).
  useEffect(() => {
    if (!stage.ready || stage.line) return;
    cardRef.current?.focus({ preventScroll: true });
  }, [stage.ready, stage.line, index]);

  const answer = useCallback(async (choice: string) => {
    const ask = step?.ask;
    stopVoice();
    if (!ask) {
      advance();
      return;
    }
    if (choice === SKIP) {
      // A skip is stored too, without a shot; the walk does not wait on it.
      void postWalkAnswer(token, { ref: ask.ref, choice: SKIP }).catch(() => undefined);
      advance();
      return;
    }
    const said = words.trim();
    if (choice === WORDS && !said) return;
    if (choice !== WORDS) navigator.vibrate?.(10);
    play("latch");
    setBusy(choice);
    setFailure("");
    // The shot is the whole viewport as he sees it: the walk's frame, guide,
    // dim and sheet step out for one frame, then come back.
    const view = viewNow(stage.target);
    setCapturing(true);
    await frame();
    await frame();
    const shot = await captureViewportPng().catch(() => undefined);
    setCapturing(false);
    try {
      await postWalkAnswer(token, {
        ref: ask.ref,
        choice,
        ...(said ? { words: said } : {}),
        ...(shot ? { window_png: shot } : {}),
        view,
      });
      setAnswered((value) => value + 1);
      setAnsweredAt((value) => ({ ...value, [index]: true }));
      advance();
    } catch {
      setFailure("The answer did not reach the hub. Try again.");
    } finally {
      setBusy("");
    }
  }, [step, token, stage.target, words, advance, index]);

  const skip = useCallback(() => { void answer(SKIP); }, [answer]);

  // Esc skips the step (the window under it does not close).
  useEffect(() => {
    if (!stage.ready || !step || busy) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      skip();
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [stage.ready, step, busy, skip]);

  /** Tab wraps inside the card: focus never leaves it while it asks. */
  const keepFocus = (event: ReactKeyboardEvent<HTMLElement>) => {
    if (event.key !== "Tab" || !cardRef.current) return;
    const focusable = Array.from(cardRef.current.querySelectorAll<HTMLElement>(
      "button:not([disabled]), textarea, input, [tabindex]:not([tabindex='-1'])"));
    if (!focusable.length) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const now = document.activeElement;
    if (event.shiftKey && (now === first || now === cardRef.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && now === last) {
      event.preventDefault();
      first.focus();
    }
  };

  // Swipe the sheet's handle down: Skip.
  const onHandleDown = (event: ReactPointerEvent<HTMLElement>) => {
    swipeRef.current = event.clientY;
    event.currentTarget.setPointerCapture?.(event.pointerId);
  };
  const onHandleUp = (event: ReactPointerEvent<HTMLElement>) => {
    const from = swipeRef.current;
    swipeRef.current = null;
    if (from !== null && event.clientY - from >= SWIPE_PX && !busy) skip();
  };

  // The guide speaks. A step that will ask says its words with the question
  // when the sheet opens (one utterance: the question never cuts the words).
  const sheetOpen = !done && !!step?.ask && stage.ready && !stage.line;
  const bubbleNow = !done && stage.ready && stage.line ? stage.line : done ? "" : spoken;
  useEffect(() => {
    if (!voiceRef.current || !begun || !step || !bubbleNow) return;
    if (step.ask && !step.press && !stage.line) return;
    if (saidRef.current === bubbleNow) return;
    saidRef.current = bubbleNow;
    speak(bubbleNow);
  }, [bubbleNow, begun, step, stage.line]);
  useEffect(() => {
    if (!voiceRef.current || !sheetOpen || !step?.ask) return;
    const before = spoken && saidRef.current !== spoken ? `${spoken} ` : "";
    saidRef.current = spoken;
    speak(`${before}${step.ask.question}`);
  }, [sheetOpen, step, spoken]);
  // The walk's end (or the walk going away) stops the voice.
  useEffect(() => { if (done || closed) stopVoice(); }, [done, closed]);
  useEffect(() => () => stopVoice(), []);
  // The robot bobs while the voice speaks.
  useEffect(() => onStateChange((state) => setTalking(state === "speaking")), []);

  const toggleVoice = () => {
    const next = !voice;
    setVoice(next);
    keepVoice(next);
    if (!next) stopVoice();
  };
  /** The first tap: the voice may play from now on (iOS). */
  const begin = () => {
    setBegun(true);
    if (page) speak(page.title);
  };

  if (closed) return null;

  if (refused) {
    return (
      <p className="walk-refused" role="status" data-walk="" data-testid="walk-refused">{refused}</p>
    );
  }
  if (!page) return null;

  const cards = steps.map((row, at) => (row.highlight || row.ask ? at : -1)).filter((at) => at >= 0);
  const count = stepCount(cards.indexOf(index) + 1, cards.length);
  const asking = !done && !!step && stage.ready && !stage.line && !!(step.highlight || step.ask);
  const marked = asking && stage.target && rect ? rect : null;
  const width = typeof window === "undefined" ? 1440 : window.innerWidth;
  const height = typeof window === "undefined" ? 900 : window.innerHeight;
  const docked = sheet || !marked;
  const placed = marked && !docked ? placeCard(marked, cardSize, width, height) : null;
  const cardStyle: CSSProperties | undefined = sheet
    // Over the dock, the dock keeps the home bar's inset; the sheet does not.
    ? { left: 0, right: 0, bottom: dock, maxHeight: sheetMax, ...(dock ? { paddingBottom: 12 } : {}) }
    : placed ? { left: placed.left, top: placed.top } : undefined;
  const ask = step?.ask;
  const said = words.trim();
  const line = !done && stage.ready ? stage.line : "";
  const bubble = bubbleNow;

  return (
    <div className="walk-layer" data-walk="" data-testid="walk" data-capturing={capturing ? "" : undefined}>
      <WalkFrame />
      <div ref={guideRef} className="walk-guide" data-testid="walk-guide"
        data-talking={talking ? "" : undefined} data-done={done ? "" : undefined}>
        <img className="walk-guide-bot" src={SYSTEM.dockAgents} alt="" width={32} height={32} draggable={false} />
        {!begun ? (
          <Button variant="secondary" className="walk-bubble walk-begin" onClick={begin} data-testid="walk-begin">
            Tap to begin
          </Button>
        ) : bubble ? (
          <p className="walk-bubble" role="status" aria-live="polite"
            data-testid={line ? "walk-line" : "walk-words"}>{bubble}</p>
        ) : null}
      </div>
      {cursor ? <PixelCursor cursor={cursor} /> : null}
      {pressed ? <Ring box={pressed} press /> : null}
      {marked ? (
        <>
          {Object.entries(dimRects(marked, width, height)).map(([side, box]) => (
            <div key={side} className="walk-backdrop" aria-hidden="true" data-testid={`walk-backdrop-${side}`}
              style={{ left: box.left, top: box.top, width: box.width, height: box.height }} />
          ))}
          <Ring box={marked} />
        </>
      ) : null}
      {done ? (
        <div className="walk-card walk-card-end" data-docked="" data-sheet={sheet ? "" : undefined}
          style={sheet ? { left: 0, right: 0, bottom: dock } : undefined} role="status" data-testid="walk-end">
          <p className="walk-title">{thanksWords(answered)}</p>
          <p className="walk-next-line" data-testid="walk-next-line">Next · Muad&apos;Dib · this morning</p>
          <div className="walk-verbs">
            <Button variant="primary" data-testid="walk-back"
              onClick={() => { stopVoice(); clearWalkFromLocation(); setClosed(true); }}>
              Back to the desk
            </Button>
          </div>
        </div>
      ) : null}
      {asking ? (
        <section ref={cardRef} className="walk-card" aria-label={page.title} tabIndex={-1} onKeyDown={keepFocus}
          data-docked={docked ? "" : undefined} data-sheet={sheet ? "" : undefined} data-side={placed?.side}
          style={cardStyle} data-testid="walk-card">
          <div className="walk-handle" data-testid="walk-handle"
            onPointerDown={onHandleDown} onPointerUp={onHandleUp}
            onPointerCancel={() => { swipeRef.current = null; }}>
            {sheet ? <span className="walk-grip" aria-hidden="true" /> : null}
            <span className="walk-name">{page.title}</span>
            {cards.length > 1 ? (
              <span className="walk-dots" aria-hidden="true" data-testid="walk-dots">
                {cards.map((at) => (
                  <span key={at} className="walk-dot"
                    data-state={at === index ? "now" : answeredAt[at] ? "done" : undefined} />
                ))}
              </span>
            ) : null}
            {count ? <span className="walk-count" data-testid="walk-count">{count}</span> : null}
            <Button variant="ghost" dense className="walk-voice" aria-pressed={voice}
              aria-label={voice ? "Voice on" : "Voice off"} title={voice ? "Voice on" : "Voice off"}
              onPointerDown={(event) => event.stopPropagation()} onClick={toggleVoice} data-testid="walk-voice">
              <VerbGlyph kind={voice ? "voice" : "voice-off"} />
            </Button>
          </div>
          {ask ? <p className="walk-question" data-testid="walk-question">{ask.question}</p> : null}
          <div className="walk-choices">
            {ask
              ? ask.choices.map((choice, at) => (
                // No choice is the default: words never imply one.
                <Button key={choice} variant="secondary" className="walk-choice" data-tone={choiceTone(choice)}
                  loading={busy === choice} disabled={!!busy} onClick={() => void answer(choice)}
                  data-testid={`walk-choice-${at}`}>
                  <ChoiceGlyph tone={choiceTone(choice)} />
                  {choice}
                </Button>
              ))
              : (
                <Button variant="primary" onClick={advance} data-testid="walk-next">Next</Button>
              )}
          </div>
          {ask ? (
            <div className="walk-more">
              <Button variant="ghost" aria-expanded={sayMore} disabled={!!busy}
                onClick={() => setSayMore((value) => !value)} data-testid="walk-say-more">
                Say more
              </Button>
              {sayMore ? (
                <PadGadget label="Say more" value={words} onChange={setWords} rows={3} autoFocus
                  micDraftScope={`walk-${ask.ref}`} />
              ) : null}
              {sayMore && said ? (
                <Button variant="primary" loading={busy === WORDS} disabled={!!busy}
                  onClick={() => void answer(WORDS)} data-testid="walk-send">
                  Send
                </Button>
              ) : null}
            </div>
          ) : null}
          {failure ? <p className="walk-line" role="alert" data-testid="walk-failure">{failure}</p> : null}
          <Button variant="ghost" dense className="walk-skip" disabled={!!busy} onClick={skip}
            data-testid="walk-skip">
            Skip
          </Button>
        </section>
      ) : null}
    </div>
  );
}

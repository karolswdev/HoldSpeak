/** The Walk (2026-11-07; direction C 2026-11-08, "the cursor is the hero"):
 * the desk runs a walk script step by step.
 *
 * For the whole walk a slow warm glow breathes at the viewport's edge inside
 * the safe area: the one constant signal "the guide holds this". There is no
 * character and no bubble (owner, 2026-11-08: the robot, the bubbles and the
 * pixel frame were "cringe", "terrible", "sterile"; "DIRECTION C, BUT PLEASE
 * MAKE THE CURSOR INTERESTING"). The step's words are one caption line at
 * the bottom edge, above the sheet and the dock; the voice says the same.
 *
 * A step opens a window (the desk's own openers), runs a verb, PRESSES a
 * part itself (the guide's cursor travels to it on an arc with a comet
 * trail, hovers one beat, taps with a ripple, the part settles pressed, the
 * real click lands), scrolls a part into the clear area, says words, marks
 * one part and asks one question. The mark is the part itself: it lifts one
 * step and wears a warm breathing halo; nothing is over it (it stays live)
 * and nothing dims. A part is searched ONLY in the window of the step's app;
 * when the window is not open, or holds no such part, the guide says so and
 * the step is skipped without a question. The question is a card beside the
 * part, or at phone width one sheet above the dock (Keep and Redo side by
 * side, Say more with the mic inline, Skip; swipe the handle down to skip).
 * A choice captures the WHOLE viewport as he sees it (the walk's chrome and
 * the halo hidden for that frame) with the viewport, the pixel ratio, the
 * browser and the part's box, posts the answer and goes on. Words never
 * choose: Send with words and no choice stores the choice "words". Esc skips.
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
import { VerbGlyph } from "../components/window/VerbGlyph";
import { speak, stop as stopVoice } from "../../lib/tts";
import { play } from "../../lib/sfx";
import { useCompactViewport } from "../useCompactViewport";
import {
  READY_BEAT_MS,
  READY_CEILING_MS,
  SKIP,
  STILL_LOADING,
  WORDS,
  clearWalkFromLocation,
  deskReady,
  noneWords,
  openWalkApp,
  postWalkAnswer,
  readWalk,
  resolveWalkScope,
  runWalkVerb,
  stepWindow,
  waitForDeskReady,
  waitForWalkTarget,
  waitForWalkWindow,
  walkAgent,
  walkAppName,
  walkTokenFromLocation,
  type WalkPage,
  type WalkPart,
  type WalkView,
} from "./walk";
import { dockHeight, markPart } from "./dom";

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

interface Point { x: number; y: number }

/** The guide's cursor. `travel`: on its way along an arc; `hover`: 2 px over
 * the tap point for one beat; `tap`: the squash; `rest`: idle on the part;
 * `out`: fading away (a step with no press). `trip` counts the journeys. */
interface Cursor { from: Point; to: Point; phase: "travel" | "hover" | "tap" | "rest" | "out"; ms: number; tilt: number; trip: number }

/** The comet trail: this many ghosts, this far apart in time. */
export const GHOSTS = 5;
const GHOST_MS = 60;

function stillMotion(): boolean {
  return typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/** The travel time: 450 ms for a short hop, up to 650 ms across the screen. */
export function travelMs(from: Point, to: Point): number {
  return Math.round(450 + 200 * Math.min(1, Math.hypot(to.x - from.x, to.y - from.y) / 900));
}

/** The lean into the travel: 8 to 12 degrees, the way it goes. */
export function tiltFor(from: Point, to: Point): number {
  const dx = to.x - from.x;
  return (dx < 0 ? -1 : 1) * Math.round(8 + 4 * Math.min(1, Math.abs(dx) / 400));
}

/** The arc: a quadratic curve bowed upward by a fifth of the distance (at
 * most 64 px), sampled in `steps`, with the lean rising and settling. */
export function arcFrames(from: Point, to: Point, tilt: number, steps = 12): string[] {
  const dx = to.x - from.x;
  const dy = to.y - from.y;
  const distance = Math.hypot(dx, dy) || 1;
  const lift = Math.min(64, distance / 5);
  // The normal of the travel that points up the screen.
  let nx = -dy / distance;
  let ny = dx / distance;
  if (ny > 0) { nx = -nx; ny = -ny; }
  const cx = (from.x + to.x) / 2 + nx * lift;
  const cy = (from.y + to.y) / 2 + ny * lift;
  return Array.from({ length: steps + 1 }, (_, at) => {
    const t = at / steps;
    const x = (1 - t) ** 2 * from.x + 2 * (1 - t) * t * cx + t ** 2 * to.x;
    const y = (1 - t) ** 2 * from.y + 2 * (1 - t) * t * cy + t ** 2 * to.y;
    return `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) rotate(${(tilt * Math.sin(Math.PI * t)).toFixed(2)}deg)`;
  });
}

/** The art: a 12 x 16 dart on whole pixels. The ember face is lit on its
 * left and shaded on its right of the fold (tip to notch), a 1 px ember-ink
 * edge, one specular pixel under the tip. Its tip is (0, 0). */
function DartArt() {
  return (
    <svg className="walk-dart" viewBox="0 0 12 16" width="12" height="16" shapeRendering="crispEdges" aria-hidden="true">
      <path className="walk-dart-edge" d="M0 0h1v1H0zM0 1h2v1H0zM0 2h1v1H0zM2 2h1v1H2zM0 3h1v1H0zM3 3h1v1H3zM0 4h1v1H0zM4 4h1v1H4zM0 5h1v1H0zM5 5h1v1H5zM0 6h1v1H0zM6 6h1v1H6zM0 7h1v1H0zM7 7h1v1H7zM0 8h1v1H0zM8 8h1v1H8zM0 9h1v1H0zM9 9h1v1H9zM0 10h1v1H0zM10 10h1v1H10zM0 11h1v1H0zM6 11h6v1H6zM0 12h1v1H0zM5 12h1v1H5zM0 13h1v1H0zM4 13h1v1H4zM0 14h1v1H0zM3 14h1v1H3zM0 15h3v1H0z" />
      <path className="walk-dart-lit" d="M1 3h1v1H1zM1 4h1v1H1zM1 5h2v1H1zM1 6h2v1H1zM1 7h3v1H1zM1 8h3v1H1zM1 9h4v1H1zM1 10h4v1H1zM1 11h4v1H1zM1 12h3v1H1zM1 13h2v1H1zM1 14h1v1H1z" />
      <path className="walk-dart-shade" d="M2 3h1v1H2zM2 4h2v1H2zM3 5h2v1H3zM3 6h3v1H3zM4 7h3v1H4zM4 8h4v1H4zM5 9h4v1H5zM5 10h5v1H5zM5 11h1v1H5zM4 12h1v1H4zM3 13h1v1H3zM2 14h1v1H2z" />
      <path className="walk-dart-shine" d="M1 2h1v1H1z" />
    </svg>
  );
}

/** The guide's cursor, the walk's one hero: it travels on an arc leaning
 * into its way with a comet trail of five shrinking ghosts, hovers, taps,
 * then breathes at rest. Transforms only; reduced motion: no trail, no
 * lean, it is simply there. */
function GuideCursor({ cursor }: { cursor: Cursor }) {
  const ref = useRef<HTMLDivElement | null>(null);
  const ghostRefs = useRef<Array<HTMLDivElement | null>>([]);
  const still = stillMotion();
  // The trail lives through the travel, the hover and the tap: its last
  // ghost lands 300 ms after the cursor.
  const trailing = !still && (cursor.phase === "travel" || cursor.phase === "hover" || cursor.phase === "tap");
  useLayoutEffect(() => {
    if (!trailing || cursor.phase !== "travel") return;
    const frames = arcFrames(cursor.from, cursor.to, cursor.tilt).map((transform) => ({ transform }));
    const running: Animation[] = [];
    const lead = ref.current;
    if (lead && typeof lead.animate === "function") {
      running.push(lead.animate(frames, { duration: cursor.ms, easing: "cubic-bezier(0.45, 0, 0.55, 1)" }));
    }
    ghostRefs.current.forEach((ghost, at) => {
      if (!ghost || typeof ghost.animate !== "function") return;
      const strength = 0.35 * (1 - at / GHOSTS);
      running.push(ghost.animate(
        frames.map((frame, step) => ({ ...frame, opacity: strength * (1 - step / (frames.length - 1)) })),
        { duration: cursor.ms, delay: (at + 1) * GHOST_MS, easing: "cubic-bezier(0.45, 0, 0.55, 1)", fill: "backwards" },
      ));
    });
    return () => running.forEach((animation) => animation.cancel());
    // One journey a trip; the phase change after it does not run it again.
  }, [cursor.trip, trailing]);
  const at = `translate(${Math.round(cursor.to.x)}px, ${Math.round(cursor.to.y)}px)`;
  return (
    <>
      {trailing ? Array.from({ length: GHOSTS }, (_, index) => (
        <div key={`${cursor.trip}-${index}`} ref={(element) => { ghostRefs.current[index] = element; }}
          className="walk-cursor walk-cursor-ghost" aria-hidden="true" data-testid="walk-cursor-ghost"
          style={{ transform: at, "--walk-ghost-scale": String(1 - (index + 1) * 0.1) } as CSSProperties}>
          <DartArt />
        </div>
      )) : null}
      <div ref={ref} className="walk-cursor" aria-hidden="true" data-testid="walk-cursor" data-phase={cursor.phase}
        style={{ transform: at }}>
        <div className="walk-cursor-body"><DartArt /></div>
      </div>
    </>
  );
}

/** The tap's soft warm ripple: one ring from 0.4 to 1.6 in 600 ms. */
function Ripple({ at }: { at: Point }) {
  return (
    <div className="walk-ripple" aria-hidden="true" data-testid="walk-ripple"
      style={{ transform: `translate(${Math.round(at.x)}px, ${Math.round(at.y)}px)` }} />
  );
}

/** The edge: a slow warm glow breathing inside the safe area for the whole
 * walk. No line, no pixels; it takes no pointer. */
function WalkEdge() {
  return <div className="walk-edge" aria-hidden="true" data-testid="walk-edge" />;
}

/** The caption: the step's words at the bottom edge, fading in with the
 * step; the words before fade out over them. */
function Caption({ text, testId }: { text: string; testId: string }) {
  const [leaving, setLeaving] = useState("");
  const last = useRef(text);
  useEffect(() => {
    if (last.current === text) return;
    const before = last.current;
    last.current = text;
    if (!before) return;
    setLeaving(before);
    const timer = setTimeout(() => setLeaving(""), CAPTION_OUT_MS);
    return () => clearTimeout(timer);
  }, [text]);
  return (
    <>
      {leaving && leaving !== text ? (
        <p className="walk-caption" data-leaving="" aria-hidden="true">{leaving}</p>
      ) : null}
      {text ? (
        <p key={text} className="walk-caption" role="status" aria-live="polite" data-testid={testId}>
          {text}
        </p>
      ) : null}
    </>
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

/** The phone sheet: at this width or less (or at the desk's compact
 * breakpoint) the card is one full-width sheet at the bottom. */
export const SHEET_MAX_WIDTH = 480;
/** The sheet is at most this part of the viewport height. */
const SHEET_HEIGHT = 0.4;
/** The space between the part and a card beside it. */
const RING = 6;
const GAP = 16;

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
/** The press: one beat of hover, the pressed look, the face's settle. */
const HOVER_MS = 240;
const PRESS_LOOK_MS = 120;
const SETTLE_MS = 600;
/** The caption's fade out. */
const CAPTION_OUT_MS = 200;
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
  // The guide's words, its cursor and the ripple of its tap.
  const [spoken, setSpoken] = useState("");
  const [cursor, setCursor] = useState<Cursor | null>(null);
  const [ripple, setRipple] = useState<Point | null>(null);
  // The steps he answered (the progress dots): index → choice.
  const [answeredAt, setAnsweredAt] = useState<Record<number, true>>({});
  // One frame without the walk's chrome: the shot is the screen he sees.
  const [capturing, setCapturing] = useState(false);
  // The voice, and (with the voice on) the one tap that lets it play.
  const [voice, setVoice] = useState(voiceDefault);
  const [begun, setBegun] = useState(() => !voiceDefault());
  // The desk's own readiness: "seen" when the predicate first held (the
  // `data-desk-ready` marker), "go" one beat later, "late" when it did not
  // hold within the ceiling (the guide says so and waits for a tap).
  const [deskState, setDeskState] = useState<"wait" | "seen" | "go" | "late">("wait");
  // He tapped through "still loading": no step waits for the desk again.
  const tappedRef = useRef(false);
  const trip = useRef(0);
  const voiceRef = useRef(voice);
  voiceRef.current = voice;
  const saidRef = useRef("");
  const cardRef = useRef<HTMLElement | null>(null);
  const captionRef = useRef<HTMLDivElement | null>(null);
  // Where the cursor rests: the next journey starts here.
  const restRef = useRef<Point | null>(null);
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

  // The walk starts only when the desk is ready, and moves one beat later.
  const loaded = !!page;
  useEffect(() => {
    if (!loaded) return;
    let alive = true;
    const started = Date.now();
    void (async () => {
      for (;;) {
        const ready = await waitForDeskReady(Math.max(0, started + READY_CEILING_MS - Date.now()));
        if (!alive) return;
        if (!ready) {
          // Late: the line stays and readiness is still watched; a tap starts.
          setDeskState((now) => (now === "go" ? now : "late"));
          while (alive && !deskReady()) await wait(100);
          if (!alive) return;
        }
        setDeskState((now) => (now === "go" ? now : "seen"));
        await wait(READY_BEAT_MS);
        if (!alive) return;
        if (deskReady()) break;
      }
      setDeskState("go");
    })();
    return () => { alive = false; };
  }, [loaded]);

  const steps = page?.steps ?? [];
  const done = !!page && index >= steps.length;
  const step = page && !done && begun && deskState === "go" ? steps[index] : undefined;

  const advance = useCallback(() => {
    setStage(EMPTY);
    setRect(null);
    setFailure("");
    setSayMore(false);
    setWords("");
    setRipple(null);
    setIndex((value) => value + 1);
  }, []);

  /** The top of the clear band: the viewport's top (no guide sits there). */
  const clearTop = () => 0;
  /** The bottom of the clear band: over the caption, and over the sheet's
   * top (an estimate before it is drawn), else the viewport's foot. */
  const clearBottom = () => {
    const height = window.innerHeight;
    const caption = captionRef.current?.getBoundingClientRect();
    const words = caption && caption.height ? caption.top - GAP / 2 : height;
    if (!sheetRef.current) return words;
    const card = cardRef.current?.getBoundingClientRect();
    if (card && card.height) return Math.min(words, card.top - GAP / 2);
    return Math.min(words, height - dockHeight() - Math.floor(height * SHEET_HEIGHT) - GAP / 2);
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
      // A later step's open, press and mark wait for the desk as the first does.
      if ((step.open || step.press || step.highlight) && !tappedRef.current && !deskReady()) await waitForDeskReady();
      if (!alive) return;
      // A step with no press: the cursor fades away where it rests.
      if (!step.press) setCursor((now) => (now && now.phase !== "out" ? { ...now, phase: "out" } : now));
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
        // The guide presses; he watches. The cursor comes from where it
        // rests (first: over the caption), hovers, taps, then the click lands.
        const part = await partOf(step.press.target, step.press.window ?? appRef.current, step.press.thing);
        if (!part?.target || !alive) return;
        const target = part.target;
        const box = rectOf(target);
        const to = { x: Math.round(box.left + box.width / 2), y: Math.round(box.top + box.height / 2) };
        const from = restRef.current ?? { x: Math.round(window.innerWidth / 2), y: Math.round(clearBottom()) };
        const still = stillMotion();
        const ms = still ? 0 : travelMs(from, to);
        trip.current += 1;
        setCursor({ from, to, phase: "travel", ms, tilt: still ? 0 : tiltFor(from, to), trip: trip.current });
        await wait(ms);
        if (!alive) return;
        setCursor((now) => (now ? { ...now, phase: "hover" } : now));
        await wait(HOVER_MS);
        if (!alive) return;
        setCursor((now) => (now ? { ...now, phase: "tap" } : now));
        if (!still) setRipple(to);
        markPart(target, "pressed", true);
        await wait(PRESS_LOOK_MS);
        markPart(target, "pressed", false);
        if (!alive) return;
        target.click();
        restRef.current = to;
        setCursor((now) => (now ? { ...now, phase: "rest" } : now));
        await wait(SETTLE_MS);
        if (!alive) return;
        setRipple(null);
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

  // The mark: the part itself lifts one step and wears the warm halo while
  // the guide asks about it (not in the shot: he sees the screen as is).
  const haloOn = !done && !!step && stage.ready && !stage.line && !!(step.highlight || step.ask) && !capturing;
  useEffect(() => {
    const target = haloOn ? stage.target : null;
    if (!target) return;
    markPart(target, "halo", true);
    return () => markPart(target, "halo", false);
  }, [haloOn, stage.target]);

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
  // The caption sits at the bottom edge: over the dock, over the sheet or a
  // docked card when one is up.
  const deskDock = dockHeight();
  const captionBottom = asking && sheet ? dock + Math.min(cardSize.height, sheetMax) + 10
    : asking && docked ? deskDock + 12 + cardSize.height + 10
      : deskDock + 12;

  return (
    <div className="walk-layer" data-walk="" data-testid="walk" data-capturing={capturing ? "" : undefined}
      data-desk-ready={deskState === "seen" || deskState === "go" ? "" : undefined}>
      <WalkEdge />
      {cursor && !done ? <GuideCursor cursor={cursor} /> : null}
      {ripple ? <Ripple at={ripple} /> : null}
      <div ref={captionRef} className="walk-caption-slot"
        style={{ "--walk-caption-bottom": `${captionBottom}px` } as CSSProperties}>
        {!begun ? (
          <Button variant="secondary" className="walk-begin" onClick={begin} data-testid="walk-begin">
            Tap to begin
          </Button>
        ) : deskState === "late" && !done ? (
          // The desk did not get ready: one plain line; a tap starts the walk.
          <Button variant="secondary" className="walk-begin"
            onClick={() => { tappedRef.current = true; setDeskState("go"); }} data-testid="walk-still-loading">
            {STILL_LOADING}
          </Button>
        ) : (
          <Caption text={bubbleNow} testId={line ? "walk-line" : "walk-words"} />
        )}
      </div>
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
            {count ? (
              <span className="walk-count" data-testid="walk-count" data-quiet={cards.length > 1 ? "" : undefined}>
                {count}
              </span>
            ) : null}
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

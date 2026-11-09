/** The Walk (2026-11-07; direction C 2026-11-08, "the cursor is the hero"):
 * the desk runs a walk script step by step.
 *
 * For the whole walk a slow warm glow breathes at the viewport's edge inside
 * the safe area: the one constant signal "the guide holds this". There is no
 * character and no bubble (owner, 2026-11-08: the robot, the bubbles and the
 * pixel frame were "cringe", "terrible", "sterile"; "DIRECTION C, BUT PLEASE
 * MAKE THE CURSOR INTERESTING"). The step's words are one caption line at
 * the bottom edge, above the bar and the dock; the voice says the same.
 *
 * A step opens a window (the desk's own openers), runs a verb, PRESSES a
 * part itself (the guide's cursor travels to it on an arc with a comet
 * trail, hovers one beat, taps with a ripple, the part settles pressed, the
 * real click lands), scrolls a part into the clear area, says words, marks
 * one part and asks one question. The mark is the part itself: it lifts one
 * step and wears a warm breathing halo; nothing is over it (it stays live)
 * and nothing dims. A part is searched ONLY in the window of the step's app;
 * when the window is not open, or holds no such part, the guide says so and
 * the step is skipped without a question. The question is one kit toolbar
 * band above the dock (direction S3 "the bar", 2026-11-08: the sheet was "so
 * ugly and unprofessional"): row 1 the voice, the question on one line and
 * the dots; row 2 Keep (primary), Redo (secondary), the mic (Say more opens
 * the words pad as a third row) and Skip. At desk width the same band is at
 * most 720 px wide, centred at the bottom edge.
 * A choice captures the WHOLE viewport as he sees it (the walk's chrome and
 * the halo hidden for that frame) with the viewport, the pixel ratio, the
 * browser and the part's box, posts the answer and goes on. Words never
 * choose: Send with words and no choice stores the choice "words". Esc skips.
 * The guide speaks its words and each question through the desk's one TTS
 * seam (lib/tts: the hub voice, else the browser voice). The voice is on by
 * default on a touch device and off on the desk (the bar's speaker
 * toggle, kept per device); with the voice on, the walk waits for one tap
 * (iOS plays audio only after a gesture).
 * A token the hub refuses gives one plain line, then the desk as usual. */
import "./walk.css";
import {
  useCallback, useEffect, useLayoutEffect, useRef, useState,
  type CSSProperties, type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { Button } from "../../components/signal/Signal";
import { PadGadget } from "../surface/gadgets";
import { ProgressDots } from "../surface/patterns/ProgressDots";
import { captureScale, captureViewportPng } from "../feedback/capture";
import { VerbGlyph } from "../components/window/VerbGlyph";
import { speak, stop as stopVoice } from "../../lib/tts";
import { play } from "../../lib/sfx";
import { useCompactViewport } from "../useCompactViewport";
import { SYSTEM } from "../systemSprites";
import {
  READY_BEAT_MS,
  READY_CEILING_MS,
  SKIP,
  STILL_LOADING,
  WORDS,
  clearWalkFromLocation,
  onLocalWalk,
  postWalkAnswer,
  readWalk,
  stepWindow,
  waitForDeskReady,
  walkAgent,
  walkTokenFromLocation,
  type LocalWalk,
  type WalkPage,
  type WalkView,
} from "./walk";
import { deskReady, dockHeight, markPart } from "../compositor/dom";
import {
  PRESS_LOOK_MS,
  deskAppName,
  executeDeskRequest,
  waitForDeskWindow,
  type DeskPart,
  type DeskResult,
  type DeskStage,
} from "../compositor/requests";
import { Caption } from "../compositor/DeskRequests";

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
    <svg className="walk-dart" viewBox="0 0 12 16" width="24" height="32" shapeRendering="crispEdges" aria-hidden="true">
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

/** The phone bar: at this width or less (or at the desk's compact
 * breakpoint) the band is full width above the dock; wider, it is at most
 * 720 px wide, centred at the bottom edge. */
export const SHEET_MAX_WIDTH = 480;
/** The band is at most this part of the viewport height (the words pad). */
const SHEET_HEIGHT = 0.4;
/** The band's two rows before it is drawn (its real height wins after). */
const BAND_PX = 112;
/** The space the part keeps from the band's edge. */
const RING = 6;
const GAP = 16;

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));
const frame = () => new Promise<void>((resolve) => requestAnimationFrame(() => resolve()));
/** The press: one beat of hover, the pressed look (PRESS_LOOK_MS, the
 * executor's), the face's settle. */
const HOVER_MS = 240;
const SETTLE_MS = 600;

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
 * and `limit` (the bar's top): centred in the band, or its top edge when
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

/** The desk's one walk runner: a linked walk (`?walk=<token>`), or an app's
 * own walk that its Show me started in place (the same session, the same
 * answer route; the steps start in the window of the mast he pressed). */
export function WalkRunner() {
  const [linked] = useState(walkTokenFromLocation);
  const [local, setLocal] = useState<LocalWalk | null>(null);
  useEffect(() => onLocalWalk(setLocal), []);
  if (local) return <WalkSession key={local.run} token={local.token} origin={local.origin} />;
  return linked ? <WalkSession token={linked} /> : null;
}

function WalkSession({ token, origin }: { token: string; origin?: string }) {
  const compact = useCompactViewport();
  const viewport = useViewport();
  const sheet = compact || viewport.width <= SHEET_MAX_WIDTH;
  const [page, setPage] = useState<WalkPage | null>(null);
  const [refused, setRefused] = useState("");
  const [index, setIndex] = useState(0);
  const [stage, setStage] = useState<Stage>(EMPTY);
  const [answered, setAnswered] = useState(0);
  const [closed, setClosed] = useState(false);
  const [busy, setBusy] = useState("");
  const [failure, setFailure] = useState("");
  const [sayMore, setSayMore] = useState(false);
  const [words, setWords] = useState("");
  const [cardSize, setCardSize] = useState({ width: 0, height: BAND_PX });
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
  // The window the steps look in: the last `open`, else where it started.
  const appRef = useRef<string | undefined>(origin);

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
    setFailure("");
    setSayMore(false);
    setWords("");
    setRipple(null);
    setIndex((value) => value + 1);
  }, []);

  /** The top of the clear band: the viewport's top (no guide sits there). */
  const clearTop = () => 0;
  /** The bottom of the clear band: over the caption, and over the bar's
   * top (its two rows before it is drawn), else the viewport's foot. */
  const clearBottom = () => {
    const height = window.innerHeight;
    const caption = captionRef.current?.getBoundingClientRect();
    const words = caption && caption.height ? caption.top - GAP / 2 : height;
    const card = cardRef.current?.getBoundingClientRect();
    if (card && card.height) return Math.min(words, card.top - GAP / 2);
    return Math.min(words, height - dockHeight() - BAND_PX - GAP / 2);
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
    /** The step's frame for the desk's one executor: the part goes into the
     * clear band; the Walk holds its own halo while it asks. */
    const stage: DeskStage = {
      alive: () => alive,
      reveal: (part) => {
        if (part.target) revealAbove(part.target, part.window, clearBottom(), clearTop());
      },
      mark: () => undefined,
    };
    /** A part the executor did not find: the guide says why and skips. */
    const skipFor = async (result: DeskResult) => {
      if (!alive) return;
      await skipWith(result.missing === "part" ? result.reason ?? "" : `${result.reason} · This step is skipped`);
    };
    /** The step's part, in the step's window only, scrolled into the clear
     * band; null after the guide said it is not there. */
    const partOf = async (op: "mark" | "scroll", target: string, app: string | undefined,
      thing?: string): Promise<DeskPart | null> => {
      const result = await executeDeskRequest({ op, args: { target, window: app, thing } }, stage);
      if (!result.done || !result.part) {
        await skipFor(result);
        return null;
      }
      return alive ? result.part : null;
    };
    void (async () => {
      // A later step's open, press and mark wait for the desk as the first does.
      if ((step.open || step.press || step.highlight) && !tappedRef.current && !deskReady()) await waitForDeskReady();
      if (!alive) return;
      // A step with no press: the cursor fades away where it rests.
      if (!step.press) setCursor((now) => (now && now.phase !== "out" ? { ...now, phase: "out" } : now));
      setSpoken(step.say?.words ?? step.press?.words ?? step.highlight?.words ?? "");
      if (step.open) {
        const opened = await executeDeskRequest({ op: "open", args: { ...step.open } }, stage);
        if (!alive) return;
        if (opened.missing === "scope") {
          await skipWith(`${opened.reason} · This step is skipped`);
          return;
        }
        appRef.current = step.open.app;
      }
      if (!alive) return;
      if (step.verb) {
        await executeDeskRequest({ op: "verb", args: { verb: step.verb.verb } }, stage);
        if (step.verb.window) appRef.current = step.verb.window;
      }
      const app = stepWindow(step, appRef.current);
      if (step.press) {
        // The guide presses; he watches. The cursor comes from where it
        // rests (first: over the caption), hovers, taps, then the click lands.
        let to = restRef.current;
        const pressed = await executeDeskRequest({ op: "press", args: {
          target: step.press.target, window: step.press.window ?? appRef.current, thing: step.press.thing,
        } }, { ...stage, press: async (target) => {
          const box = rectOf(target);
          to = { x: Math.round(box.left + box.width / 2), y: Math.round(box.top + box.height / 2) };
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
        } });
        if (!pressed.done) {
          await skipFor(pressed);
          return;
        }
        if (!alive) return;
        restRef.current = to;
        setCursor((now) => (now ? { ...now, phase: "rest" } : now));
        await wait(SETTLE_MS);
        if (!alive) return;
        setRipple(null);
      }
      if (step.scroll) {
        const part = await partOf("scroll", step.scroll.target, step.scroll.window ?? appRef.current, step.scroll.thing);
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
      let part: DeskPart = { window: null, target: null };
      if (step.highlight) {
        const found = await partOf("mark", step.highlight.target, app, step.highlight.thing);
        if (!found) return;
        part = found;
      } else if (app) {
        part = { window: await waitForDeskWindow(app), target: null };
        if (!alive) return;
        if (!part.window) {
          const name = await deskAppName(app);
          if (alive) await skipWith(`The ${name} window is not open · This step is skipped`);
          return;
        }
      }
      if (!alive) return;
      setStage({ ready: true, target: part.target, window: part.window, line: "" });
    })();
    return () => { alive = false; };
  }, [step, advance]);

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

  // The bar: on the dock, its real height, at most 40 % of the height.
  const dock = dockHeight();
  const sheetMax = Math.floor(viewport.height * SHEET_HEIGHT);
  const sheetTop = viewport.height - dock - Math.min(cardSize.height, sheetMax);

  // The part scrolls into the clear area above the bar.
  useLayoutEffect(() => {
    const target = stage.target;
    if (!target || !cardRef.current) return;
    revealAbove(target, stage.window, sheetTop - GAP / 2, clearTop());
  }, [stage.target, stage.window, sheetTop]);

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
    // and bar step out for one frame, then come back.
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

  // The guide speaks. A step that will ask says its words with the question
  // when the bar opens (one utterance: the question never cuts the words).
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
  const cardCount = cards.length;
  const count = stepCount(cards.indexOf(index) + 1, cards.length);
  const asking = !done && !!step && stage.ready && !stage.line && !!(step.highlight || step.ask);
  // The bar: full width on the phone, at most 720 px centred at desk width;
  // on the dock, the dock keeps the home bar's inset and the bar does not.
  const bandStyle: CSSProperties = {
    bottom: dock,
    maxHeight: sheetMax,
    ...(sheet ? { left: 0, right: 0 } : {}),
    ...(dock ? { paddingBottom: 12 } : {}),
  };
  const ask = step?.ask;
  const said = words.trim();
  const line = !done && stage.ready ? stage.line : "";
  // The caption sits at the bottom edge: over the dock, over the bar when
  // it is up.
  const captionBottom = asking ? dock + Math.min(cardSize.height, sheetMax) + 10 : dock + 12;

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
        <div className="walk-card walk-card-end" data-sheet={sheet ? "" : undefined}
          style={bandStyle} role="status" data-testid="walk-end">
          <div className="walk-ask">
            <p className="walk-question walk-title">{thanksWords(answered)}</p>
            <Button variant="primary" className="walk-back" data-testid="walk-back"
              onClick={() => { stopVoice(); clearWalkFromLocation(); setClosed(true); }}>
              Back to the desk
            </Button>
          </div>
        </div>
      ) : null}
      {asking ? (
        <section ref={cardRef} className="walk-card" aria-label={page.title} tabIndex={-1} onKeyDown={keepFocus}
          data-sheet={sheet ? "" : undefined} style={bandStyle} data-testid="walk-card">
          <div className="walk-ask">
            <Button variant="ghost" dense className="walk-voice" aria-pressed={voice}
              aria-label={voice ? "Voice on" : "Voice off"} title={voice ? "Voice on" : "Voice off"}
              onClick={toggleVoice} data-testid="walk-voice">
              <VerbGlyph kind={voice ? "voice" : "voice-off"} />
            </Button>
            {/* One line: the voice says the question in full. */}
            <p className="walk-question" title={ask?.question} data-testid={ask ? "walk-question" : undefined}>
              {ask?.question ?? ""}
            </p>
            {cards.length > 1 ? (
              <ProgressDots className="walk-progress" data-testid="walk-dots" at={cards.indexOf(index)}
                done={(dot) => Boolean(answeredAt[cards[dot]])}
                count={cardCount} />
            ) : null}
            {count ? <span className="walk-count" data-testid="walk-count">{count}</span> : null}
          </div>
          <div className="walk-choices">
            {ask
              ? ask.choices.map((choice, at) => (
                // Keep (the first choice) is the primary; words never imply one.
                <Button key={choice} variant={at === 0 ? "primary" : "secondary"} className="walk-choice"
                  loading={busy === choice} disabled={!!busy} onClick={() => void answer(choice)}
                  data-testid={`walk-choice-${at}`}>
                  {choice}
                </Button>
              ))
              : (
                <Button variant="primary" className="walk-choice" onClick={advance} data-testid="walk-next">
                  Next
                </Button>
              )}
            {ask ? (
              <Button variant="secondary" className="walk-mic" aria-label="Say more" title="Say more"
                aria-expanded={sayMore} disabled={!!busy}
                onClick={() => setSayMore((value) => !value)} data-testid="walk-say-more">
                <img src={SYSTEM.micGlyph} alt="" width={16} height={16} className="desk-chrome-sprite"
                  draggable={false} />
              </Button>
            ) : null}
            <Button variant="ghost" dense className="walk-skip" disabled={!!busy} onClick={skip}
              data-testid="walk-skip">
              Skip
            </Button>
          </div>
          {ask && sayMore ? (
            <div className="walk-more">
              <PadGadget label="Say more" value={words} onChange={setWords} rows={2} autoFocus
                micDraftScope={`walk-${ask.ref}`} />
              {said ? (
                <Button variant="primary" loading={busy === WORDS} disabled={!!busy}
                  onClick={() => void answer(WORDS)} data-testid="walk-send">
                  Send
                </Button>
              ) : null}
            </div>
          ) : null}
          {failure ? <p className="walk-line" role="alert" data-testid="walk-failure">{failure}</p> : null}
        </section>
      ) : null}
    </div>
  );
}

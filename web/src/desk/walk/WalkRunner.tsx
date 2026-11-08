/** The Walk (2026-11-07): the desk runs a walk script step by step.
 *
 * A step opens a window (the desk's own openers), runs a verb, marks one
 * part of a window and asks one question. The mark is a cut-out in a dim
 * backdrop (the backdrop is cut, nothing is drawn over the part, and the
 * part stays live to the pointer), with a 2 px accent ring that pulses once.
 * The card sits beside the part (the other side when there is no room). At
 * phone width the card is one sheet at the bottom, above the dock, and the
 * part scrolls into view above the sheet. The part is searched ONLY in the
 * window of the step's app; when that window is not open the step says so
 * and skips. A choice captures THAT window with the feedback capture, posts
 * the answer and goes on. Words never choose: Send with words and no choice
 * stores the choice "words". Esc skips.
 * A token the hub refuses gives one plain line, then the desk as usual. */
import "./walk.css";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type CSSProperties } from "react";
import { Button } from "../../components/signal/Signal";
import { PadGadget } from "../surface/gadgets";
import { captureWindowPng } from "../feedback/capture";
import { useCompactViewport } from "../useCompactViewport";
import {
  SKIP,
  WORDS,
  clearWalkFromLocation,
  openWalkApp,
  postWalkAnswer,
  readWalk,
  resolveWalkScope,
  runWalkVerb,
  waitForWalkTarget,
  waitForWalkWindow,
  walkAppName,
  walkTokenFromLocation,
  type WalkPage,
  type WalkPart,
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
/** The phone sheet: at this width or less (or at the desk's compact
 * breakpoint) the card is one full-width sheet at the bottom. */
export const SHEET_MAX_WIDTH = 480;
/** The sheet is at most this part of the viewport height. */
const SHEET_HEIGHT = 0.4;
const RING = 6;
const GAP = 16;

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

function rectOf(element: Element): Rect {
  const box = element.getBoundingClientRect();
  return { left: box.left, top: box.top, width: box.width, height: box.height };
}

function sameRect(a: Rect | null, b: Rect | null): boolean {
  return !!a && !!b && a.left === b.left && a.top === b.top && a.width === b.width && a.height === b.height;
}

/** The backdrop with the part cut out (even-odd: the hole is not painted and
 * takes no pointer). */
export function holePath(rect: Rect, width: number, height: number): string {
  const x = rect.left - RING;
  const y = rect.top - RING;
  const w = rect.width + RING * 2;
  const h = rect.height + RING * 2;
  const r = 8;
  return `path(evenodd, "M0 0H${width}V${height}H0Z M${x + r} ${y}H${x + w - r}A${r} ${r} 0 0 1 ${x + w} ${y + r}`
    + `V${y + h - r}A${r} ${r} 0 0 1 ${x + w - r} ${y + h}H${x + r}A${r} ${r} 0 0 1 ${x} ${y + h - r}`
    + `V${y + r}A${r} ${r} 0 0 1 ${x + r} ${y}Z")`;
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

/** Scroll the part into the band above the sheet (`limit` is the sheet's
 * top): centred in the band, or its top edge when it is taller. */
export function revealAbove(target: HTMLElement, root: HTMLElement | null, limit: number): void {
  const box = target.getBoundingClientRect();
  const scroller = scrollerOf(target, root);
  const top = Math.max(scroller ? scroller.getBoundingClientRect().top : 0, 0);
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
  const cardRef = useRef<HTMLElement | null>(null);
  const appRef = useRef<string | undefined>(undefined);

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
  const step = page && !done ? steps[index] : undefined;

  const advance = useCallback(() => {
    setStage(EMPTY);
    setRect(null);
    setFailure("");
    setSayMore(false);
    setWords("");
    setIndex((value) => value + 1);
  }, []);

  // Run one step: open, verb, then find the part to mark.
  useEffect(() => {
    if (!step) return;
    let alive = true;
    void (async () => {
      if (step.open) {
        const scope = await resolveWalkScope(step.open.scope);
        if (!alive) return;
        if (scope === null) {
          const none = step.open.scope === "@first-meeting" ? "No meeting yet" : "No project yet";
          setStage({ ready: true, target: null, window: null, line: `${none} · This step is skipped` });
          await wait(1600);
          if (alive) advance();
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
      if (!step.highlight && !step.ask) {
        await wait(400);
        if (alive) advance();
        return;
      }
      // The step's window: the mark's own, else the app the walk opened last.
      const app = step.highlight?.window ?? appRef.current;
      let part: WalkPart = { window: null, target: null };
      if (step.highlight) part = await waitForWalkTarget(step.highlight.target, app);
      else if (app) part = { window: await waitForWalkWindow(app), target: null };
      if (!alive) return;
      if (app && !part.window) {
        const name = await walkAppName(app);
        if (!alive) return;
        setStage({ ready: true, target: null, window: null, line: `The ${name} window is not open · This step is skipped` });
        await wait(1600);
        if (alive) advance();
        return;
      }
      const { target } = part;
      // The sheet scrolls the part above itself once it is measured.
      if (!sheetRef.current) target?.scrollIntoView?.({ block: "center", inline: "nearest" });
      setStage({ ready: true, target, window: part.window,
        line: step.highlight && !target ? "This part is not on the screen" : "" });
    })();
    return () => { alive = false; };
  }, [step, advance]);

  // Follow the part while windows move, scroll or resize.
  useEffect(() => {
    const target = stage.target;
    if (!target) return;
    let frame = 0;
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
      frame = requestAnimationFrame(tick);
    };
    tick();
    return () => cancelAnimationFrame(frame);
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
    revealAbove(target, stage.window, sheetTop - GAP / 2);
  }, [sheet, stage.target, stage.window, sheetTop]);

  const answer = useCallback(async (choice: string) => {
    const ask = step?.ask;
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
    setBusy(choice);
    setFailure("");
    let shot: string | undefined;
    const said = words.trim();
    if (choice === WORDS && !said) return;
    // The shot is of the step's window, never of another one.
    const root = stage.window ?? stage.target?.closest<HTMLElement>("[data-layer='window']") ?? null;
    if (root) shot = await captureWindowPng(root).catch(() => undefined);
    try {
      await postWalkAnswer(token, {
        ref: ask.ref,
        choice,
        ...(said ? { words: said } : {}),
        ...(shot ? { window_png: shot } : {}),
      });
      setAnswered((value) => value + 1);
      advance();
    } catch {
      setFailure("The answer did not reach the hub. Try again.");
    } finally {
      setBusy("");
    }
  }, [step, token, stage.target, stage.window, words, advance]);

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

  if (closed) return null;

  if (refused) {
    return (
      <p className="walk-refused" role="status" data-walk="" data-testid="walk-refused">{refused}</p>
    );
  }
  if (!page) return null;

  if (done) {
    return (
      <div className="walk-card walk-card-end" data-walk="" data-docked="" role="status" data-testid="walk-end">
        <p className="walk-title">{thanksWords(answered)}</p>
        <div className="walk-verbs">
          <Button variant="primary" data-testid="walk-back"
            onClick={() => { clearWalkFromLocation(); setClosed(true); }}>
            Back to the desk
          </Button>
        </div>
      </div>
    );
  }
  if (!step || !stage.ready) return null;

  const cards = steps.map((row, at) => (row.highlight || row.ask ? at : -1)).filter((at) => at >= 0);
  const count = stepCount(cards.indexOf(index) + 1, cards.length);
  const marked = stage.target && rect ? rect : null;
  const width = typeof window === "undefined" ? 1440 : window.innerWidth;
  const height = typeof window === "undefined" ? 900 : window.innerHeight;
  const docked = sheet || !marked;
  const placed = marked && !docked ? placeCard(marked, cardSize, width, height) : null;
  const cardStyle: CSSProperties | undefined = sheet
    ? { left: 0, right: 0, bottom: dock, maxHeight: sheetMax }
    : placed ? { left: placed.left, top: placed.top } : undefined;
  const ask = step.ask;
  const said = words.trim();

  return (
    <div className="walk-layer" data-walk="" data-testid="walk">
      {marked ? (
        <>
          <div className="walk-backdrop" aria-hidden="true" data-testid="walk-backdrop"
            style={{ clipPath: holePath(marked, width, height) }} />
          <div className="walk-ring" aria-hidden="true" data-testid="walk-ring"
            style={{ left: marked.left - RING, top: marked.top - RING,
              width: marked.width + RING * 2, height: marked.height + RING * 2 }} />
        </>
      ) : null}
      <section ref={cardRef} className="walk-card" aria-label={page.title}
        data-docked={docked ? "" : undefined} data-sheet={sheet ? "" : undefined} data-side={placed?.side}
        style={cardStyle} data-testid="walk-card">
        {step.highlight?.words ? <p className="walk-words" data-testid="walk-words">{step.highlight.words}</p> : null}
        {stage.line ? <p className="walk-line" data-testid="walk-line">{stage.line}</p> : null}
        {ask ? <p className="walk-question" data-testid="walk-question">{ask.question}</p> : null}
        <div className="walk-verbs">
          {ask
            ? ask.choices.map((choice, at) => (
              // No choice is the default: words never imply one.
              <Button key={choice} variant="secondary" loading={busy === choice}
                disabled={!!busy} onClick={() => void answer(choice)} data-testid={`walk-choice-${at}`}>
                {choice}
              </Button>
            ))
            : (
              <Button variant="primary" onClick={advance} data-testid="walk-next">Next</Button>
            )}
          {ask && sayMore && said ? (
            <Button variant="primary" loading={busy === WORDS} disabled={!!busy}
              onClick={() => void answer(WORDS)} data-testid="walk-send">
              Send
            </Button>
          ) : null}
          {ask ? (
            <Button variant="ghost" aria-expanded={sayMore} disabled={!!busy}
              onClick={() => setSayMore((value) => !value)} data-testid="walk-say-more">
              Say more
            </Button>
          ) : null}
          <Button variant="ghost" disabled={!!busy} onClick={skip} data-testid="walk-skip">Skip</Button>
        </div>
        {ask && sayMore ? (
          <PadGadget label="Say more" value={words} onChange={setWords} rows={3} autoFocus
            micDraftScope={`walk-${ask.ref}`} />
        ) : null}
        {failure ? <p className="walk-line" role="alert" data-testid="walk-failure">{failure}</p> : null}
        {count ? <p className="walk-count" data-testid="walk-count">{count}</p> : null}
      </section>
    </div>
  );
}

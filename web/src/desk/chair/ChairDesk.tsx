// PHILO-13-11 (C1, slice two) — THE CHAIR AS WINDOWS (design §5, §5b;
// boards C1-1, C1-4a–e, C1-6a; owner 2026-10-02 "Ratify, build it").
//
// The Chair is a Workbench screen of four DeskWindowFrame windows — Needs
// you, Brief, The week, Capture — each with its gadgets and its own scroll.
// The Chair screen itself never scrolls at 1440.
//   - Close closes (R1). At 1440 a closed window leaves one compact reopen
//     library Button in its place; Window ▸ Chair reopens it too.
//   - 393 (R2): one window at a time fills the work area; Needs you first;
//     Capture opens on demand from the Speak AppIcon (no permanent strip).
//
// PHILO-14 A1 (board A-1, RATIFIED 2026-10-07): the Chair is the SCREEN of
// objects (desk/screen/). The four windows open from it, the Dock and
// Window ▸ Chair, and float like every desk window; a closed one leaves the
// screen, not a reopen Button. The tiles above are PARKED behind
// `data-layout="tiles"` (no `screen` prop; ChairHome always passes one).
import { useEffect, useLayoutEffect, useRef, type ReactNode } from "react";
import { useAftercare } from "../intelligenceAttention";
import { frontWindowAftercareSlot } from "../../components/AmbientLayer";
import { Button } from "../../components/signal/Signal";
import { DeskWindowFrame } from "../components/DeskWindow";
import { GadgetGlyph } from "../components/window/GadgetGlyph";
import { useCompactViewport } from "../useCompactViewport";
import { useDesk } from "../store";
import { answerSurfaceFirst } from "../shell";
import { workBand } from "../components/window/windowGeometry";
import type { PanelRect } from "../store/types";
import {
  CHAIR_WINDOWS,
  CHAIR_WINDOW_IDS,
  closeChairWindow,
  keepCaptureForCard,
  openCaptureForCard,
  openCaptureOnPhone,
  openChairWindow,
  useChairWindows,
  type ChairWindowKey,
  type ChairWindowSpec,
} from "./chairWindows";

/** PHILO-14 A1c: Capture's height while the aftercare card stands in it
 * (chair.css: `--chair-capture-h: 300px` under the card's `:has` rule). */
const CAPTURE_CARD_H = 300;

export type ChairDeskProps = Record<ChairWindowKey, ReactNode> & {
  /** PHILO-14 A1: the screen of objects (board A-1). With it the Chair is
   * the screen and the four windows open from it, the Dock and Window ▸
   * Chair; they float like every desk window. Without it the PARKED
   * Phase-13 tiles return (`data-layout="tiles"`; ChairHome never sets it). */
  screen?: ReactNode;
};

function ChairWindow({
  spec,
  open,
  tiled,
  children,
}: {
  spec: ChairWindowSpec;
  open: boolean;
  tiled: boolean;
  children: ReactNode;
}) {
  return (
    <DeskWindowFrame
      id={spec.id}
      title={spec.title}
      label={spec.title}
      className={`chair-window chair-window--${spec.key}`}
      open={open}
      onClose={() => closeChairWindow(spec.id)}
      tiled={tiled}
      // PHILO-14 A1: a floating Chair window keeps its C1-1 seat's CSS height
      // until he arranges it (no max-height seed inflation over its neighbour).
      fitContent={!tiled}
      dockChip="iconified"
      escapeCloses={false}
      entrance={false}
      minW={280}
      minH={spec.key === "capture" ? 88 : 160}
    >
      <div
        className="chair-window-body"
        data-testid={`chair-window-body-${spec.key}`}
      >
        {children}
      </div>
    </DeskWindowFrame>
  );
}

/** The Needs-you window is the front Chair window when the Chair opens:
 * among the Chair's own planes only (a desk window above keeps its plane). */
function raiseNeedsAmongChair() {
  const s = useDesk.getState();
  const order = s.panelOrder;
  const chairAt = order
    .map((id, i) => (CHAIR_WINDOW_IDS.includes(id) ? i : -1))
    .filter((i) => i >= 0);
  if (!order.includes("chair:needs") || chairAt.length < 2) return;
  const chairIds = chairAt.map((i) => order[i]).filter((id) => id !== "chair:needs");
  chairIds.push("chair:needs");
  const next = [...order];
  chairAt.forEach((i, n) => {
    next[i] = chairIds[n];
  });
  if (next.join("|") !== order.join("|")) useDesk.setState({ panelOrder: next });
}

export function ChairDesk(props: ChairDeskProps) {
  const compact = useCompactViewport();
  const closed = useChairWindows((s) => s.closed);
  const phone = useChairWindows((s) => s.phone);

  // Muad'Dib's ruling: ONLY the Dock's Speak AppIcon opens Capture at 393.
  // Go ▸ Speak, the verb and ⌘1 keep opening the Speak window. PHILO-13-13
  // C3-W: the Dock says so itself — its launches carry `origin: "dock"`
  // (SurfaceOpenOptions, #744), so the Chair reads the origin and no press
  // window is needed.
  useEffect(
    () =>
      answerSurfaceFirst("dictate", (_scope, options) =>
        options?.origin === "dock" && openCaptureOnPhone(),
      ),
    [],
  );
  // PHILO-13-17 (C7, Q4; the owner's ruling): at 393 an arriving aftercare
  // card opens Capture, so the card lands in its slot (a desk window in
  // front iconifies, never closes). Muad'Dib's ruling 2026-10-03: when the
  // front desk window already hosts the card's slot (the meeting's own
  // record in Meetings), the card lands there and nothing moves. A card
  // already waiting when the Chair mounts keeps Capture in the ring (Q4b)
  // without taking the front.
  // PHILO-14 A1c (Muad'Dib's ruling 2026-10-07): the same at 1440 — the
  // Chair's windows start closed since A1, so a card with no Capture floated
  // over The week. Now a closed Capture opens for it; an open one holds it.
  const aftercare = useAftercare();
  const seenCard = useRef<string | null | undefined>(undefined);
  useEffect(() => {
    const key = aftercare ? `${aftercare.meetingId}:${aftercare.title}` : null;
    const first = seenCard.current === undefined;
    const arrived = key !== null && key !== seenCard.current;
    seenCard.current = key;
    if (!arrived) return;
    if (first) keepCaptureForCard();
    else if (!frontWindowAftercareSlot()) openCaptureForCard();
  }, [aftercare]);
  // PHILO-14 A1c: at 1440 Capture floats with a seat placed while it held
  // only the capture bar (100 px). While the card stands in it, Capture
  // grows UP to the card's height (chair.css: --chair-capture-h 300px), its
  // foot fixed; when the card leaves, the seat comes back. A Capture he
  // moved or sized keeps his geometry.
  const captureRect = useDesk((s) => s.panelRects["chair:capture"]);
  const captureArranged = useDesk((s) => s.panelSaved.includes("chair:capture"));
  const cardInCapture = !compact && Boolean(aftercare) && !closed["chair:capture"];
  const captureSeat = useRef<PanelRect | null>(null);
  useEffect(() => {
    if (compact || captureArranged) {
      captureSeat.current = null;
      return;
    }
    const desk = useDesk.getState();
    if (cardInCapture && captureRect && !captureSeat.current) {
      const foot = captureRect.y + captureRect.h;
      const top = Math.max(workBand().top, foot - CAPTURE_CARD_H);
      if (top >= captureRect.y) return;
      captureSeat.current = captureRect;
      desk.setPanelRect("chair:capture", { ...captureRect, y: top, h: foot - top });
    } else if (!cardInCapture && captureSeat.current) {
      const seat = captureSeat.current;
      captureSeat.current = null;
      if (captureRect) desk.setPanelRect("chair:capture", seat);
    }
  }, [compact, captureArranged, cardInCapture, captureRect]);
  // Parent layout effects run after the windows present themselves.
  useLayoutEffect(() => {
    raiseNeedsAmongChair();
  }, []);

  const phoneShown = compact && Boolean(phone) && !closed[phone];
  const tiles = props.screen === undefined;

  return (
    <div
      className="chair-desk"
      data-testid="chair-desk"
      data-layout={tiles ? "tiles" : "screen"}
      data-phone-shown={phoneShown ? "true" : undefined}
    >
      {tiles ? null : props.screen}
      {CHAIR_WINDOWS.map((spec) => {
        const isOpen = !closed[spec.id];
        if (!isOpen && !tiles) return null;
        if (!isOpen && !compact) {
          // R1: the closed window's place holds its reopen Button.
          return (
            <div
              key={spec.id}
              className={`chair-window-closed chair-window--${spec.key}`}
              data-testid={`chair-reopen-${spec.key}`}
            >
              <Button dense onClick={() => openChairWindow(spec.id)} aria-label={`Open ${spec.title}`}>
                <GadgetGlyph kind="zoom" />
                {spec.title}
              </Button>
            </div>
          );
        }
        const shown = compact ? isOpen && phone === spec.id : isOpen;
        return (
          <ChairWindow key={spec.id} spec={spec} open={shown} tiled={tiles}>
            {props[spec.key]}
          </ChairWindow>
        );
      })}
      {tiles && compact && !phoneShown ? (
        <div className="chair-reopen-list" data-testid="chair-reopen-list">
          {CHAIR_WINDOWS.filter((w) => w.phone).map((w) => (
            <Button key={w.id} onClick={() => openChairWindow(w.id)} aria-label={`Open ${w.title}`}>
              {w.title}
            </Button>
          ))}
        </div>
      ) : null}
    </div>
  );
}

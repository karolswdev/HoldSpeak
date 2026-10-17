/** Parked 2026-10-16: DESIGN-windows §4.5 gives completed meetings one
 * ready notice in the bell. The retired card must not open or grow Capture.
 * Retained here as history; no active component mounts this hook. */
import { useEffect, useRef } from "react";
import { useAftercare, useAftercareHost } from "../../intelligenceAttention";
import { frontWindowAftercareSlot } from "../../../components/AmbientLayer";
import { useDesk } from "../../store";
import { workBand } from "../../components/window/windowGeometry";
import type { PanelRect } from "../../store/types";
import { keepCaptureForCard, openCaptureForCard } from "../chairWindows";

const CAPTURE_CARD_H = 300;

export function useParkedAftercareCaptureEffects(compact: boolean, closed: Record<string, boolean>): void {
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
    else if (!frontWindowAftercareSlot(aftercare?.meetingId)) openCaptureForCard();
  }, [aftercare]);
  // PHILO-14 A1c: at 1440 Capture floats with a seat placed while it held
  // only the capture bar (100 px). While the card stands in it, Capture
  // grows UP to the card's height (chair.css: --chair-capture-h 300px), its
  // foot fixed; when the card leaves, the seat comes back. A Capture he
  // moved or sized keeps his geometry.
  const captureRect = useDesk((s) => s.panelRects["chair:capture"]);
  const captureArranged = useDesk((s) => s.panelSaved.includes("chair:capture"));
  // Astra r1 (#954): grow only while CAPTURE's own slot holds the card (a
  // card in the front Meetings window must not move Capture).
  const aftercareHost = useAftercareHost();
  const cardInCapture =
    !compact && Boolean(aftercare) && !closed["chair:capture"] && aftercareHost === "capture";
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
}

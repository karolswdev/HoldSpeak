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
import { useEffect, useLayoutEffect, useRef, type ReactNode } from "react";
import { useAftercare } from "../intelligenceAttention";
import { frontWindowAftercareSlot } from "../../components/AmbientLayer";
import { Button } from "../../components/signal/Signal";
import { DeskWindowFrame } from "../components/DeskWindow";
import { GadgetGlyph } from "../components/window/GadgetGlyph";
import { useCompactViewport } from "../useCompactViewport";
import { useDesk } from "../store";
import { answerSurfaceFirst } from "../shell";
import {
  CHAIR_WINDOWS,
  CHAIR_WINDOW_IDS,
  closeChairWindow,
  keepCaptureInRing,
  openCaptureOnPhone,
  openChairWindow,
  useChairWindows,
  type ChairWindowKey,
  type ChairWindowSpec,
} from "./chairWindows";

export type ChairDeskProps = Record<ChairWindowKey, ReactNode>;

function ChairWindow({
  spec,
  open,
  children,
}: {
  spec: ChairWindowSpec;
  open: boolean;
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
      tiled
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
  const aftercare = useAftercare();
  const seenCard = useRef<string | null | undefined>(undefined);
  useEffect(() => {
    const key = aftercare ? `${aftercare.meetingId}:${aftercare.title}` : null;
    const first = seenCard.current === undefined;
    const arrived = key !== null && key !== seenCard.current;
    seenCard.current = key;
    if (!arrived) return;
    if (first) keepCaptureInRing();
    else if (!frontWindowAftercareSlot()) openCaptureOnPhone();
  }, [aftercare]);
  // Parent layout effects run after the windows present themselves.
  useLayoutEffect(() => {
    raiseNeedsAmongChair();
  }, []);

  const phoneShown = compact && Boolean(phone) && !closed[phone];

  return (
    <div className="chair-desk" data-testid="chair-desk">
      {CHAIR_WINDOWS.map((spec) => {
        const isOpen = !closed[spec.id];
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
          <ChairWindow key={spec.id} spec={spec} open={shown}>
            {props[spec.key]}
          </ChairWindow>
        );
      })}
      {compact && !phoneShown ? (
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

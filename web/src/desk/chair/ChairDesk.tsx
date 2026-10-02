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
import { useEffect, useLayoutEffect, type ReactNode } from "react";
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
  openCaptureOnPhone,
  openChairWindow,
  useChairWindows,
  type ChairWindowKey,
  type ChairWindowSpec,
} from "./chairWindows";

export type ChairDeskProps = Record<ChairWindowKey, ReactNode>;

/** How long a press on the Dock's Speak AppIcon arms the Capture answer. */
const DOCK_PRESS_MS = 1500;

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
  // Go ▸ Speak, the verb and ⌘1 keep opening the Speak window. The Dock's
  // launch logic is not ours to change (Dock.tsx is Astra's), so the press
  // on the AppIcon arms the answer here: a capture-phase listener notes a
  // press on the Dock's Speak AppIcon, and the shell's "dictate" key is
  // answered only while that press is fresh (the Dock opens through an
  // async import, so the window is a short time, not the same tick).
  useEffect(() => {
    let armedAt = -Infinity;
    const arm = (e: Event) => {
      const t = e.target as Element | null;
      if (t?.closest?.(".desk-dock [aria-label^='Speak']")) armedAt = performance.now();
    };
    document.addEventListener("click", arm, true);
    const off = answerSurfaceFirst("dictate", () => {
      const fromDock = performance.now() - armedAt < DOCK_PRESS_MS;
      armedAt = -Infinity;
      return fromDock && openCaptureOnPhone();
    });
    return () => {
      document.removeEventListener("click", arm, true);
      off();
    };
  }, []);
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

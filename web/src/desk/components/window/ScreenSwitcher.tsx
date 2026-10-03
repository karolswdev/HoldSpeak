// PHILO-13-17 (C7, Q2; ratified 2026-10-03) — at 393 the screen title is
// the window switcher: a library menu Button, `<front window> ▾`. Its menu
// lists the phone's ring (phoneRing.ts), a check on the window in front:
// any open window in two taps. The title text truncates; the ▾ is its own
// fixed mark (painted by CSS) and never does. It also mounts the ring's touch swipe.
import { useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { WorkMenu, type WorkMenuEntry } from "../DeskMenu";
import { useDesk } from "../../store";
import { useChairState } from "../../chairState";
import { useChairWindows } from "../../chair/chairWindows";
import { useAllOpenWindows } from "./windowRegistry";
import { phoneCurrent, phoneRing, showRingWindow, usePhoneSwipe } from "./phoneRing";

export function ScreenSwitcher({ name }: { name: string }) {
  // Re-render on every fact the ring reads.
  useAllOpenWindows();
  useChairWindows((s) => s.phone);
  useChairWindows((s) => s.closed);
  useChairWindows((s) => s.captureInRing);
  useChairState((s) => s.surface);
  useDesk((s) => s.panelOrder);
  useDesk((s) => s.panelMin);
  usePhoneSwipe(true);
  const [at, setAt] = useState<{ x: number; y: number } | null>(null);
  // A press on the title while the menu is open CLOSES it. The menu's own
  // outside press (document, capture) closes it first and may re-render
  // before the title's handler runs, which then read "closed" and opened it
  // again. This listener is added before the menu's (on mount), so it notes
  // the press on the open title first; the title's handler then stays closed.
  const openRef = useRef(false);
  openRef.current = Boolean(at);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const pressClosesRef = useRef(false);
  useEffect(() => {
    const down = (e: PointerEvent) => {
      pressClosesRef.current =
        openRef.current && Boolean(buttonRef.current?.contains(e.target as Node));
    };
    document.addEventListener("pointerdown", down, true);
    return () => document.removeEventListener("pointerdown", down, true);
  }, []);
  const current = phoneCurrent();
  const entries: WorkMenuEntry[] = phoneRing().map((w) => ({
    type: "item" as const,
    id: `switch-${w.id}`,
    label: w.label,
    checked: w.id === current,
    onSelect: () => showRingWindow(w.id),
  }));
  return (
    <span className="desk-screen-title has-switcher" data-testid="desk-screen-title">
      <Button
        variant="chrome"
        className="desk-screen-switcher"
        aria-haspopup="menu"
        aria-expanded={Boolean(at)}
        aria-label={`Windows: ${name}`}
        data-testid="desk-screen-switcher"
        ref={buttonRef}
        onPointerDown={(e) => {
          if (e.button > 0) return; // a secondary button is not a tap
          if (pressClosesRef.current) {
            pressClosesRef.current = false;
            setAt(null);
            return;
          }
          const r = e.currentTarget.getBoundingClientRect();
          setAt(at ? null : { x: r.left, y: r.bottom });
        }}
        onClick={(e) => {
          // Keyboard activation arrives as a click with no pointer-down.
          if (e.detail !== 0 || at) return;
          const r = e.currentTarget.getBoundingClientRect();
          setAt({ x: r.left, y: r.bottom });
        }}
      >
        <span className="desk-screen-name" title={name}>{name}</span>
        {/* The ▾ is painted by CSS (chrome-menus.css): the title's text
            stays the window's name for every reader of the screen bar. */}
        <span className="desk-screen-switcher-mark" aria-hidden="true" data-testid="desk-screen-switcher-mark" />
      </Button>
      {at ? (
        <WorkMenu
          className="desk-head-menu desk-screen-switcher-menu"
          label="Open windows"
          x={at.x}
          y={at.y}
          entries={entries}
          onClose={() => setAt(null)}
        />
      ) : null}
    </span>
  );
}

// PHILO-13-17 (C7, Q2; ratified 2026-10-03) — at 393 the screen title is
// the window switcher: a library menu Button, `<front window> ▾`. Its menu
// lists the phone's ring (phoneRing.ts), a check on the window in front:
// any open window in two taps. The title text truncates; the ▾ is its own
// fixed mark (painted by CSS) and never does. It also mounts the ring's touch swipe.
import { useState } from "react";
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
        // Pointer-down, as the menu bar's titles: the menu's own outside
        // press closes first, and the render-time `at` still names the
        // state before it, so the same press toggles the menu closed.
        onPointerDown={(e) => {
          if (e.button > 0) return; // a secondary button is not a tap
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

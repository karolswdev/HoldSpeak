// PHILO-13-11 (C1, slice two) — the Chair's four windows: their ids, their
// names, and the ONE lifecycle (design/workbench-look.md §5, §5b; R1, R2).
//
//   Close CLOSES a Chair window. A closed one comes back from
//   Window ▸ Chair (393: Go ▸ Chair) or from the compact reopen Button the
//   Chair screen draws where it was (1440).
//   The phone is one window at a time: `phone` names the Chair window that
//   fills the work area; Capture opens there on demand (the Speak AppIcon).
//
// The stacking order and the rects stay in the desk compositor (panelOrder,
// panelRects, panelMax) under these ids, like every other window. B2
// (story 07) persists the four ids — open/closed, rect, zoom, order — with
// every other window family; this store does not persist (yet).
import { create } from "zustand";
import { useDesk } from "../store";
import { registrySnapshot } from "../components/window/windowRegistry";

export type ChairWindowKey = "needs" | "brief" | "week" | "capture";

export interface ChairWindowSpec {
  key: ChairWindowKey;
  id: `chair:${ChairWindowKey}`;
  title: string;
  /** Listed in Window ▸ Chair at 393 (Capture opens from Speak there). */
  phone: boolean;
}

export const CHAIR_WINDOWS: readonly ChairWindowSpec[] = [
  { key: "needs", id: "chair:needs", title: "Needs you", phone: true },
  { key: "brief", id: "chair:brief", title: "Brief", phone: true },
  { key: "week", id: "chair:week", title: "The week", phone: true },
  { key: "capture", id: "chair:capture", title: "Capture", phone: false },
];

export const CHAIR_WINDOW_IDS: readonly string[] = CHAIR_WINDOWS.map((w) => w.id);

export function chairWindowSpec(id: string): ChairWindowSpec | undefined {
  return CHAIR_WINDOWS.find((w) => w.id === id);
}

interface ChairWindowsState {
  /** The Chair windows the owner closed (absent = open). */
  closed: Record<string, boolean>;
  /** 393: the one Chair window that fills the work area ("" = none). */
  phone: string;
}

export const useChairWindows = create<ChairWindowsState>(() => ({
  closed: {},
  phone: "chair:needs",
}));

function compactNow(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof window.matchMedia === "function" &&
    window.matchMedia("(max-width: 720px)").matches
  );
}

export function isChairWindowOpen(id: string): boolean {
  return !useChairWindows.getState().closed[id];
}

/** Open a Chair window (or bring an open one to the front). At 393 it takes
 * the work area, and the desk window in front falls to its Dock chip: it is
 * iconified, never closed. */
export function openChairWindow(id: string): void {
  if (!chairWindowSpec(id)) return;
  const desk = useDesk.getState();
  if (compactNow()) {
    for (const w of registrySnapshot) {
      if (w.dock && !desk.panelMin.includes(w.id)) desk.minimizePanel(w.id);
    }
  }
  useChairWindows.setState((s) => ({
    closed: { ...s.closed, [id]: false },
    phone: id,
  }));
  if (desk.panelMin.includes(id)) desk.restorePanel(id);
  else useDesk.getState().focusPanel(id);
}

/** Close a Chair window. At 393 the next open Chair window takes the work
 * area (Capture never does: it opens on demand). */
export function closeChairWindow(id: string): void {
  useChairWindows.setState((s) => {
    const closed = { ...s.closed, [id]: true };
    let phone = s.phone;
    if (phone === id) {
      const order = useDesk.getState().panelOrder;
      const candidates = CHAIR_WINDOWS.filter(
        (w) => w.phone && w.id !== id && !closed[w.id],
      ).map((w): string => w.id);
      // the most recent open one first, then the canonical order
      const recent = [...order].reverse().find((o) => candidates.includes(o));
      phone = recent ?? candidates[0] ?? "";
    }
    return { closed, phone };
  });
}

/** PHILO-13-12 (C2) — depth on the phone: the Chair shows one window at a
 * time, so a Chair window sent to the back gives the work area to the next
 * open Chair window (the most recent first). At 1440 nothing changes here:
 * the stacking order alone draws depth. */
export function chairPhoneToBack(id: string): void {
  if (!compactNow() || !chairWindowSpec(id)) return;
  const s = useChairWindows.getState();
  if (s.phone !== id) return;
  // The next open Chair window after this one, in the Chair's own order
  // (the phone mounts one Chair window, so the stacking order holds only it).
  const ring = CHAIR_WINDOWS.filter((w) => w.phone).map((w): string => w.id);
  const at = ring.indexOf(id);
  for (let step = 1; step < ring.length; step++) {
    const next = ring[(at + step) % ring.length];
    if (!s.closed[next]) {
      useChairWindows.setState({ phone: next });
      return;
    }
  }
}

/** The Dock's Speak AppIcon at 393 on the Chair opens Capture on demand
 * (R2; the owner's "Yes" to Capture, 2026-10-02). The Chair screen calls this
 * only for a fresh press on that AppIcon (ChairDesk.tsx). True when it did. */
export function openCaptureOnPhone(): boolean {
  if (!compactNow()) return false;
  openChairWindow("chair:capture");
  return true;
}

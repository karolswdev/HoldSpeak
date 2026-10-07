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
// every other window family: the rects and order in the compositor's part of
// the workspace document, the closed ones and the phone's window here, in the
// document's `chair` section.
import { create } from "zustand";
import { useDesk } from "../store";
import {
  loadDeskWorkspace,
  saveDeskWorkspaceSection,
} from "../store/workspaceStorage";
import { registrySnapshot } from "../components/window/windowRegistry";
import type { ComponentType } from "react";
import { NeedsDrawer } from "../needs/NeedsDrawer";

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

/** PHILO-14 A5: a Chair window whose body is an object face of its own
 * (the Needs-you smart drawer), in place of the Chair's section. */
export const CHAIR_WINDOW_BODY: Partial<Record<ChairWindowKey, ComponentType>> = { needs: NeedsDrawer };

export const CHAIR_WINDOW_IDS: readonly string[] = CHAIR_WINDOWS.map((w) => w.id);

export function chairWindowSpec(id: string): ChairWindowSpec | undefined {
  return CHAIR_WINDOWS.find((w) => w.id === id);
}

interface ChairWindowsState {
  /** The Chair windows the owner closed (absent = open). */
  closed: Record<string, boolean>;
  /** 393: the one Chair window that fills the work area ("" = none). */
  phone: string;
  /** PHILO-13-17 (C7, Q4b): 393: Capture joins the phone's window ring when
   * it opens there and stays in it until it is closed. */
  captureInRing: boolean;
  /** PHILO-14 A1c: the Chair is mounted as the screen of objects (A1), not
   * the parked tiles. Set by ChairDesk; read by the aftercare card. */
  screenMounted: boolean;
}

// PHILO-13-07 (B2): the closed Chair windows and the phone's window come
// back from the one workspace document. Capture is in the ring when it was
// the phone's window (C7's ring is derived from that, not stored twice).
const storedChair = loadDeskWorkspace().chair;

// PHILO-14 A1: the Chair is the screen of objects (board A-1); a desk that
// remembers nothing opens with every Chair window closed and no phone window,
// so the owner arrives at his objects. A window he opened stays open (B2).
export const useChairWindows = create<ChairWindowsState>(() => ({
  closed: Object.fromEntries(
    (storedChair ? storedChair.closed : CHAIR_WINDOW_IDS)
      .filter((id) => CHAIR_WINDOW_IDS.includes(id))
      .map((id) => [id, true]),
  ),
  phone:
    storedChair && (storedChair.phone === "" || CHAIR_WINDOW_IDS.includes(storedChair.phone))
      ? storedChair.phone
      : "",
  captureInRing: storedChair?.phone === "chair:capture",
  screenMounted: false,
}));

// PHILO-13-07 (B2): a closed Chair window stays closed after a reload.
useChairWindows.subscribe((s, prev) => {
  if (s.closed === prev.closed && s.phone === prev.phone) return;
  saveDeskWorkspaceSection({
    chair: {
      closed: Object.keys(s.closed).filter((id) => s.closed[id]),
      phone: s.phone,
    },
  });
});

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
  const compact = compactNow();
  useChairWindows.setState((s) => ({
    closed: { ...s.closed, [id]: false },
    phone: id,
    captureInRing: s.captureInRing || (compact && id === "chair:capture"),
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
    return {
      closed,
      phone,
      captureInRing: id === "chair:capture" ? false : s.captureInRing,
    };
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

/** PHILO-13-17 (C7, Q4b) — at 393 Capture is in the ring without coming to
 * the front (a card waits for it when the Chair mounts with one pending). */
export function keepCaptureInRing(): void {
  if (!compactNow()) return;
  useChairWindows.setState((s) =>
    s.captureInRing && !s.closed["chair:capture"]
      ? s
      : { captureInRing: true, closed: { ...s.closed, "chair:capture": false } },
  );
}

/** PHILO-14 A1c (Muad'Dib's ruling 2026-10-07): an arriving aftercare card
 * lands in Capture's slot at both widths. At 393 Capture takes the work area
 * (PHILO-13-17 Q4). At 1440 a closed Capture opens and comes to the front; an
 * open one already holds the card, so nothing moves. True when it opened. */
export function openCaptureForCard(): boolean {
  if (compactNow()) return openCaptureOnPhone();
  if (!useChairWindows.getState().closed["chair:capture"]) return false;
  openChairWindow("chair:capture");
  return true;
}

/** PHILO-14 A1c: a card already waiting when the Chair mounts. At 393 Capture
 * joins the ring without the front (Q4b); at 1440 a closed Capture opens in
 * its seat without the front, so the card has its slot. */
export function keepCaptureForCard(): void {
  if (compactNow()) {
    keepCaptureInRing();
    return;
  }
  useChairWindows.setState((s) =>
    s.closed["chair:capture"]
      ? { closed: { ...s.closed, "chair:capture": false } }
      : s,
  );
}

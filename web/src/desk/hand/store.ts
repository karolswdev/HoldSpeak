/** PHILO-14 C3 — drop to hand: the drag in flight and the hand that waits.
 *
 *  Board A-3 (docs/internal/philo/phase-14/canvas/shots/A-3-1440.png): an
 *  item is dragged from the screen or a drawer onto the Conductor drawer or
 *  an agent icon. While it moves, a ghost follows the pointer and a dotted
 *  path runs back to where it began; the target under it lights. On the
 *  drop, in YOLO, the ConfirmLine waits in the drawer head (or at the
 *  screen's head) for the press; in Secure and Normal the launch sheet
 *  opens (`begin.ts`).
 *
 *  A `host` names where the line is drawn: `screen`, or `drawer:<projectId>`. */
import { create } from "zustand";
import type { HandOrigin } from "../agentHand";
import type { AgentId } from "../firstrun/agentsStep";

/** The dragged object's own face (the sprite the ghost and the line draw). */
export interface HandEnd {
  kind: string;
  id: string;
  sprite?: string;
}

export interface Point {
  x: number;
  y: number;
}

export interface HandDrag {
  origin: HandOrigin;
  source: HandEnd;
  host: string;
  /** The source icon's centre (viewport), where the dotted path begins. */
  from: Point;
  /** The pointer (viewport); null until the first move. */
  at: Point | null;
  /** The key of the target under the pointer (it lights). */
  over: string | null;
}

export interface HandPending {
  origin: HandOrigin;
  source: HandEnd;
  agent: AgentId;
  host: string;
  /** PHILO-15 B36: the default agent passed over (its sign-in is unknown). */
  skipped?: AgentId | null;
  /** The installed agents whose sign-in is unknown (the line warns for its own). */
  unknown?: AgentId[];
}

interface DropHandState {
  drag: HandDrag | null;
  pending: HandPending | null;
  startDrag(drag: Omit<HandDrag, "at" | "over">): void;
  moveDrag(at: Point): void;
  setOver(key: string | null): void;
  /** The pointer left `key`: unlight it (only if it is still the one lit). */
  leave(key: string): void;
  endDrag(): void;
  confirm(pending: HandPending): void;
  cancel(): void;
}

export const useDropHand = create<DropHandState>((set) => ({
  drag: null,
  pending: null,
  startDrag: (drag) => set({ drag: { ...drag, at: null, over: null } }),
  moveDrag: (at) => set((s) => (s.drag ? { drag: { ...s.drag, at } } : s)),
  setOver: (key) => set((s) => (s.drag && s.drag.over !== key ? { drag: { ...s.drag, over: key } } : s)),
  leave: (key) => set((s) => (s.drag && s.drag.over === key ? { drag: { ...s.drag, over: null } } : s)),
  endDrag: () => set({ drag: null }),
  confirm: (pending) => set({ pending, drag: null }),
  cancel: () => set({ pending: null }),
}));

export const SCREEN_HOST = "screen";
export const drawerHost = (projectId: string) => `drawer:${projectId}`;

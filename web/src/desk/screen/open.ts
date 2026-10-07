/** PHILO-14 A1 — what an object on the screen opens.
 *
 *  One function per drawer, so the lanes that build the new windows re-point
 *  ONE call each: `openDrawer` (lane A2: the Project drawer window), the
 *  Conductor (lane C4), the agent (lane C2 registers its lane window on the
 *  `coder:` ref in `openObject.ts`). The screen calls `openTarget` only. */
import { openChairWindow } from "../chair/chairWindows";
import { refOpener } from "../openObject";
import { openDrawer as openProjectDrawer, openParkedDrawer as openParkedWindow } from "../drawer/store";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";

export type ScreenTarget =
  | { type: "project"; id: string }
  | { type: "people" }
  | { type: "conductor" }
  | { type: "needs" }
  | { type: "parked" }
  | { type: "ref"; ref: string }
  | { type: "agent"; key: string };

/** A Project drawer (PHILO-14 A2b: the drawer is the Project's face; the
 *  Room is one press away, in the drawer's head). */
export function openDrawer(projectId: string): void {
  openProjectDrawer(projectId);
}

/** The Needs you smart drawer: the Phase-13 Needs you window. */
export function openNeedsYouDrawer(): void {
  openChairWindow("chair:needs");
}

/** The Conductor drawer (lane C4): where agents live; the Agents
 *  application folded into it. */
export function openConductorDrawer(): void {
  openSurfaceOr("open-conductor", "/conductor");
}

/** The People drawer: the People window. */
export function openPeopleDrawer(): void {
  openSurfaceOr("open-people", "/");
}

/** Parked (PHILO-15 04): the Parked drawer, every parked object across
 *  kinds; each row opens where it lives and restores in place. */
export function openParkedDrawer(): void {
  openParkedWindow();
}

/** A loose object (or a person, or an agent's `coder:` ref): the one open
 *  grammar of `openObject.ts`; a ref it does not name opens its pull-out,
 *  as the Floor does. */
export function openScreenRef(ref: string): void {
  const open = refOpener(ref);
  if (open) open();
  else useDesk.getState().openPullout(ref);
}

export function openTarget(target: ScreenTarget): void {
  switch (target.type) {
    case "project":
      return openDrawer(target.id);
    case "people":
      return openPeopleDrawer();
    case "conductor":
      return openConductorDrawer();
    case "needs":
      return openNeedsYouDrawer();
    case "parked":
      return openParkedDrawer();
    case "ref":
      return openScreenRef(target.ref);
    case "agent":
      return openScreenRef(`coder:${target.key}`);
  }
}

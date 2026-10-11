/* PHILO-11-05: the meeting's SEND well, loaded on demand. The species and
 * its CSS ride their own chunk, so the Desk entry bundle does not grow
 * (web/scripts/check-bundle.mjs ratchet; Astra counsel r1 finding 2). */
import { lazy, Suspense, type ComponentProps } from "react";
import type { MeetingSendWell as MeetingSendWellType } from "./MeetingSendWell";

let chunk: Promise<void> | null = null;
let Loaded: typeof MeetingSendWellType | null = null;

/** PHILO-17 (the desk sweep): load the well's chunk ahead. The meeting
 *  record draws its body once this has ended, so the well never arrives a
 *  frame late and moves the rows under it (UX-CANON D). A failed load ends
 *  the wait too; the well then loads on demand as before. */
export function preloadMeetingSendWell(): Promise<void> {
  chunk ??= import("./MeetingSendWell").then(
    (m) => { Loaded = m.MeetingSendWell; },
    () => { chunk = null; },
  );
  return chunk;
}

export const meetingSendWellLoaded = (): boolean => Loaded !== null;

const Well = lazy(() => import("./MeetingSendWell").then((m) => ({ default: m.MeetingSendWell })));

export function MeetingSendWellLazy(props: ComponentProps<typeof Well>) {
  // Loaded ahead: drawn at once, never through a Suspense frame.
  if (Loaded) return <Loaded {...props} />;
  return <Suspense fallback={null}><Well {...props} /></Suspense>;
}

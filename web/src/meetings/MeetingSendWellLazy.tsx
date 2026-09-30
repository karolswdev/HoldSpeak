/* PHILO-11-05: the meeting's SEND well, loaded on demand. The species and
 * its CSS ride their own chunk, so the Desk entry bundle does not grow
 * (web/scripts/check-bundle.mjs ratchet; Astra counsel r1 finding 2). */
import { lazy, Suspense, type ComponentProps } from "react";

const Well = lazy(() => import("./MeetingSendWell").then((m) => ({ default: m.MeetingSendWell })));

export function MeetingSendWellLazy(props: ComponentProps<typeof Well>) {
  return <Suspense fallback={null}><Well {...props} /></Suspense>;
}

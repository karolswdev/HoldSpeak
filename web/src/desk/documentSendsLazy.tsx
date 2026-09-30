/* PHILO-11-05a: the document SEND wells, loaded on demand. The species and
 * its CSS (send-well.css, channels.css) stay in their own chunk, out of the
 * Desk entry (web/scripts/check-bundle.mjs: the Desk CSS ratchet). Each seat
 * renders nothing until the chunk arrives, except the brief head, whose verbs
 * render as they were meanwhile. */
import { lazy, Suspense, type ComponentProps, type ReactNode } from "react";

const load = () => import("./documentSends");
const Brief = lazy(() => load().then((m) => ({ default: m.BriefSendWells })));
const Head = lazy(() => load().then((m) => ({ default: m.BriefHeadVerbs })));
const Desk = lazy(() => load().then((m) => ({ default: m.DeskDecisionSendWells })));
const Record = lazy(() => load().then((m) => ({ default: m.DecisionRecordSendWells })));
const Chip = lazy(() => load().then((m) => ({ default: m.DecisionRecordPreparedChip })));

type P<T> = T extends React.LazyExoticComponent<infer C> ? ComponentProps<C> : never;

export const BriefSendWells = (p: P<typeof Brief>) => <Suspense fallback={null}><Brief {...p} /></Suspense>;
export const BriefHeadVerbs = (p: P<typeof Head> & { children: ReactNode }) => (
  <Suspense fallback={<>{p.children}</>}><Head {...p} /></Suspense>
);
export const DeskDecisionSendWells = (p: P<typeof Desk>) => <Suspense fallback={null}><Desk {...p} /></Suspense>;
export const DecisionRecordSendWells = (p: P<typeof Record>) => <Suspense fallback={null}><Record {...p} /></Suspense>;
export const DecisionRecordPreparedChip = (p: P<typeof Chip>) => <Suspense fallback={null}><Chip {...p} /></Suspense>;

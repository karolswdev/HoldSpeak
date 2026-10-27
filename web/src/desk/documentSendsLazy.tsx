/* PHILO-11-05a: the document SEND wells, loaded on demand. The species and
 * its CSS (send-well.css, channels.css) stay in their own chunk, out of the
 * Desk entry (web/scripts/check-bundle.mjs: the Desk CSS ratchet). Wells show
 * the shared loading state until the chunk arrives; the brief head keeps its
 * own verbs meanwhile. */
import { lazy, Suspense, type ComponentProps, type ReactNode } from "react";
import { SurfaceState } from "./surface/Surface";

const load = () => import("./documentSends");
const Brief = lazy(() => load().then((m) => ({ default: m.BriefSendWells })));
const Head = lazy(() => load().then((m) => ({ default: m.BriefHeadVerbs })));
const Desk = lazy(() => load().then((m) => ({ default: m.DeskDecisionSendWells })));
const DeskSheet = lazy(() => load().then((m) => ({ default: m.DeskDecisionSendSheet })));
const Record = lazy(() => load().then((m) => ({ default: m.DecisionRecordSendWells })));
const RecordSheet = lazy(() => load().then((m) => ({ default: m.DecisionRecordSendSheet })));
const Artifact = lazy(() => load().then((m) => ({ default: m.ArtifactSendWells })));
const Note = lazy(() => load().then((m) => ({ default: m.NoteSendWells })));
const Chip = lazy(() => load().then((m) => ({ default: m.DecisionRecordPreparedChip })));

type P<T> = T extends React.LazyExoticComponent<infer C> ? ComponentProps<C> : never;

export const BriefSendWells = (p: P<typeof Brief>) => <Suspense fallback={<SurfaceState loading />}><Brief {...p} /></Suspense>;
export const BriefHeadVerbs = (p: P<typeof Head> & { children: ReactNode }) => (
  <Suspense fallback={<>{p.children}</>}><Head {...p} /></Suspense>
);
export const DeskDecisionSendWells = (p: P<typeof Desk>) => <Suspense fallback={<SurfaceState loading />}><Desk {...p} /></Suspense>;
export const DeskDecisionSendSheet = (p: P<typeof DeskSheet>) => <Suspense fallback={<SurfaceState loading />}><DeskSheet {...p} /></Suspense>;
export const DecisionRecordSendWells = (p: P<typeof Record>) => <Suspense fallback={<SurfaceState loading />}><Record {...p} /></Suspense>;
export const DecisionRecordSendSheet = (p: P<typeof RecordSheet>) => <Suspense fallback={<SurfaceState loading />}><RecordSheet {...p} /></Suspense>;
export const DecisionRecordPreparedChip = (p: P<typeof Chip>) => <Suspense fallback={null}><Chip {...p} /></Suspense>;
export const ArtifactSendWells = (p: P<typeof Artifact>) => <Suspense fallback={<SurfaceState loading />}><Artifact {...p} /></Suspense>;
export const NoteSendWells = (p: P<typeof Note>) => <Suspense fallback={<SurfaceState loading />}><Note {...p} /></Suspense>;

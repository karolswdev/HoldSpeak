/* PHILO-11-05a: the brief and the decisions as documents on the channels.
 * Each face composes the ONE species (desk/surface/send, contract.md
 * "SendWell") with a document reference and a label; no face draws a row of
 * its own. Built to the owner's ratified canvases (phase-11 story 03, boards
 * A1-A6, B1-B5, T2, T3).
 *
 * - The brief: `monday_brief:<id>`, labelled `BRIEF <day>`. The Chair's
 *   BRIEF section and Intelligence -> BRIEF show one pick and one press (the
 *   species' store is keyed by the document).
 * - A desk decision (the decision window): `desk_decision:<id>`.
 * - A decision record (Intelligence -> DECISIONS, the Room's DECISIONS &
 *   COMMITMENTS rows, also the rows marked `source="meeting"`):
 *   `decision_record:<id>`, never `meeting_decision:<id>` (design 6a).
 */
import type { ReactNode } from "react";
import { PreparedChip, SendWells, mergeKnown, useSends, type DocRef } from "./surface/send";
import { stamp } from "../features/channels/channels";
import "./documentSends.css";

/** `SEP 29` from an ISO time, in the viewer's zone. */
const day = (iso?: string | null) => (iso ? stamp(iso).slice(0, -6) : "");
/** The short id a prepared row shows: `record-85f927...` -> `85F927`. */
const short = (id: string) => id.replace(/^(record|decision|brief)[-_]/, "").slice(0, 6).toUpperCase();

type BriefLike = { id: string; generated_at?: string | null; period_end?: string | null };

export const briefDoc = (b: BriefLike): DocRef => {
  const d = day(b.generated_at ?? b.period_end);
  return { ref: `monday_brief:${b.id}`, title: d ? `Brief ${d}` : "Brief", label: d ? `BRIEF ${d}` : "BRIEF" };
};

export const deskDecisionDoc = (id: string, title?: string | null): DocRef => ({
  ref: `desk_decision:${id}`, title: String(title || "Decision"), label: `DECISION ${short(id)}`,
});

export const decisionRecordDoc = (id: string, text?: string | null): DocRef => ({
  ref: `decision_record:${id}`, title: String(text || "Decision record"), label: `D-${short(id)}`,
});

/** The brief's SEND well and its SENDS history (canvas A; the Chair and Intelligence -> BRIEF). */
export function BriefSendWells({ brief }: { brief: BriefLike }) {
  return <div data-seat="brief"><SendWells doc={briefDoc(brief)} /></div>;
}

/** The Chair's BRIEF head verbs with PREPARED ×K first (A4). With a
 *  prepared send the chip and the verbs are ONE group, so at narrow width
 *  the whole group wraps under the label (documentSends.css). With none,
 *  the verbs render as they were (no wrapper, the PHILO-4-01 head). */
export function BriefHeadVerbs({ brief, children }: { brief: BriefLike; children: ReactNode }) {
  const ref = briefDoc(brief).ref;
  const { data } = useSends(ref);
  const waiting = mergeKnown(ref, data ?? []).some((s) => s.state === "prepared");
  if (!waiting) return <>{children}</>;
  return <span className="brief-head-verbs"><PreparedChip docRef={ref} />{children}</span>;
}

/** The decision window's well (B1-B3, T2). */
export function DeskDecisionSendWells({ id, title }: { id: string; title?: string | null }) {
  return <div data-seat="desk-decision"><SendWells doc={deskDecisionDoc(id, title)} /></div>;
}

/** A decision record's well (B4b, B5). */
export function DecisionRecordSendWells({ id, text }: { id: string; text?: string | null }) {
  return <div data-seat="decision-record"><SendWells doc={decisionRecordDoc(id, text)} /></div>;
}

/** PREPARED ×K on a Room decision row (B4). Nothing at zero. */
export function DecisionRecordPreparedChip({ id }: { id: string }) {
  return <PreparedChip docRef={decisionRecordDoc(id).ref} />;
}

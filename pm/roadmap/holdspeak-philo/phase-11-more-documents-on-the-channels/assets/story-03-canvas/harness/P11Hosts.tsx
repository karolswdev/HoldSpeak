/* PHILO-11-03 CANVAS (PROPOSAL): the seats. Each face where a document lives
 * (R4) composes the ONE species (DocSendWell.tsx) through one of these small
 * hosts; harness/vite.config.mjs puts each host into the product file at a
 * named anchor (and fails the run if the anchor moved). No host draws a well
 * of its own: each passes a document reference and a label.
 */
import { useCallback, useEffect, useState, type ComponentProps } from "react";
import { CycleGadget, SurfaceLedgerRow } from "@w/desk/surface";
import { DeliveryHistory, ListChips as ProductListChips, mergeKnown as updateMergeKnown } from "@w/features/channels/SendWell";
import type { UpdateController } from "@w/features/project-room/update/useUpdateController";
import type { ProjectUpdate } from "@w/features/project-room/update/model";
import { stamp } from "@w/features/channels/channels";
import { DocSendWell, DocumentWells, PreparedChip, mergeKnown, useSends } from "./DocSendWell";

const day = (iso?: string | null) => (iso ? stamp(iso).slice(0, -6) : "");
const short = (id: string) => id.replace(/^(record|decision|brief)[-_]/, "").slice(0, 6).toUpperCase();

/* ── the brief (A: the Chair BRIEF section and the Intelligence BRIEF view) ── */

type BriefLike = { id: string; generated_at?: string | null; period_end?: string | null };
export const briefDoc = (b: BriefLike) => ({ ref: `monday_brief:${b.id}`, label: `BRIEF ${day(b.generated_at ?? b.period_end)}` });

export function P11BriefWell({ brief }: { brief: BriefLike }) {
  return <div className="p11-seat" data-p11="seat" data-seat="brief"><DocumentWells doc={briefDoc(brief)} /></div>;
}
export function P11BriefChip({ brief }: { brief: BriefLike }) {
  return <PreparedChip docRef={briefDoc(brief).ref} />;
}

/* ── a decision (B) ── */

export function P11DeskDecisionWell({ id }: { id: string }) {
  return <div className="p11-seat" data-p11="seat" data-seat="desk-decision">
    <DocumentWells doc={{ ref: `desk_decision:${id}`, label: `DECISION ${short(id)}` }} /></div>;
}
export function P11RecordWell({ id }: { id: string }) {
  return <div className="p11-seat" data-p11="seat" data-seat="decision-record">
    <DocumentWells doc={{ ref: `decision_record:${id}`, label: `D-${short(id)}` }} /></div>;
}

/** The Room's DECISIONS & COMMITMENTS row (a decision RECORD, design 6a):
 *  the row opens in place and holds the well; `Open` stays in its trailing
 *  slot; the row carries PREPARED ×K when a send waits (B4). */
export function P11RoomRow({ dec, cells, ...rest }: ComponentProps<typeof SurfaceLedgerRow> & { dec: { id: string } }) {
  const [open, setOpen] = useState(false);
  return (
    <SurfaceLedgerRow {...rest} open={open} onToggle={() => setOpen((o) => !o)}
      cells={<>{cells}<PreparedChip docRef={`decision_record:${dec.id}`} /></>}>
      {open ? <P11RecordWell id={dec.id} /> : null}
    </SurfaceLedgerRow>
  );
}

/* ── a meeting summary (C): three forms, one well (R3, R7) ── */

const FORMS = [
  { value: "meeting_summary", label: "Summary", word: "SUMMARY" },
  { value: "meeting_digest", label: "Digest", word: "DIGEST" },
  { value: "meeting_followup", label: "Follow-up", word: "FOLLOW-UP" },
];
const formPick = new Map<string, string>();   // meeting id -> the form he picked (survives a re-mount)

export function P11MeetingWell({ id, startedAt }: { id: string; startedAt?: string | null }) {
  const [kind, setKind] = useState(formPick.get(id) ?? "meeting_summary");
  const f = FORMS.find((x) => x.value === kind) ?? FORMS[0];
  const head = (
    <div className="p11-forms" data-p11="forms" data-testid="doc-forms">
      <CycleGadget label="Document" value={kind} options={FORMS.map(({ value, label }) => ({ value, label }))}
        onChange={(v) => { formPick.set(id, v); setKind(v); }} />
    </div>
  );
  return (
    <div className="p11-seat" data-p11="seat" data-seat="meeting">
      <DocumentWells key={kind} doc={{ ref: `${kind}:${id}`, label: `${f.word} ${day(startedAt)}` }} head={head} />
    </div>
  );
}

/* ── the update (E1): the same species; its Phase 10 history and manual row stay ── */

export function ListChips(props: ComponentProps<typeof ProductListChips>) { return <ProductListChips {...props} />; }

export function PublishedWells({ ctrl, update }: { ctrl: UpdateController; update: ProjectUpdate }) {
  const { reloadDeliveries } = ctrl;
  const settled = useCallback(() => { void reloadDeliveries(); }, [reloadDeliveries]);
  useEffect(() => { settled(); }, [update.id, settled]);
  const ref = `project_update:${update.id}`;
  const sendsRead = useSends(ref, settled);
  return (
    <div className="p11-seat" data-p11="seat" data-seat="update">
      <DocSendWell doc={{ ref, label: `REV ${update.draftRevision}` }} sendsRead={sendsRead} onSettled={settled} />
      <div data-section="delivery"><DeliveryHistory ctrl={ctrl} update={update} sends={updateMergeKnown(update.id, mergeKnown(ref, sendsRead.data ?? []))} /></div>
    </div>
  );
}

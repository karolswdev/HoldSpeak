/* PHILO-11-05: the SEND well of one meeting, built to the owner's ratified
 * canvas C (phase-11 story 03, "Yes...", 2026-09-29; boards C1-C6, T1).
 *
 * ONE well per meeting. A library CycleGadget, first inside SEND, picks the
 * form: Summary, Digest or Follow-up (R3, R7). Each form is its own document
 * (`meeting_summary:<id>`, `meeting_digest:<id>`, `meeting_followup:<id>`);
 * no form carries the transcript. The host mounts this only when the meeting
 * has a summary (C4: no summary, no well).
 *
 * Seats: the Meetings record under SUMMARY (MeetingDetail), the meeting
 * window (MeetingPullout) and the Chair's MEETINGS row when unfolded.
 */
import { useState } from "react";
import { CycleGadget } from "../desk/surface";
import { SendHistory, SendWell, mergeKnown, pickDestination, pickedDestination, useSends } from "../desk/surface/send";
import { useAnnounceWindowDocument } from "../desk/windowSend";
import { stamp } from "../features/channels/channels";

export const MEETING_FORMS = [
  { value: "meeting_summary", label: "Summary", word: "SUMMARY" },
  { value: "meeting_digest", label: "Digest", word: "DIGEST" },
  { value: "meeting_followup", label: "Follow-up", word: "FOLLOW-UP" },
] as const;
type Form = (typeof MEETING_FORMS)[number]["value"];
/** The Phase 12 binding's form word for each well form. */
const BINDING_FORM = { meeting_summary: "summary", meeting_digest: "digest", meeting_followup: "followup" } as const;

/** The form he picked, per meeting: two seats of one meeting show one pick. */
const formPick = new Map<string, Form>();

/** `SEP 29` from an ISO time (the stamp without its clock). */
const day = (iso?: string | null) => (iso ? stamp(iso).replace(/ \d\d:\d\d$/, "") : "");

export function MeetingSendWell({ meetingId, title, startedAt }: {
  meetingId: string; title: string; startedAt?: string | null;
}) {
  const [kind, setKind] = useState<Form>(formPick.get(meetingId) ?? "meeting_summary");
  const form = MEETING_FORMS.find((f) => f.value === kind) ?? MEETING_FORMS[0];
  // PHILO-13-15 (C5): the window's document for `Send to ▸` (this form).
  useAnnounceWindowDocument({ kind: "meeting", id: meetingId, form: BINDING_FORM[kind] });
  const head = (
    <div className="send-line" data-testid="doc-forms">
      <CycleGadget label="Document" value={kind}
        options={MEETING_FORMS.map(({ value, label }) => ({ value, label }))}
        onChange={(v) => {
          // PHILO-13-15 (C5, the push seam): Summary -> Digest -> Follow-up
          // keeps the picked destination.
          const was = pickedDestination(`${kind}:${meetingId}`);
          if (was) pickDestination(`${v}:${meetingId}`, was);
          formPick.set(meetingId, v as Form); setKind(v as Form);
        }} />
    </div>
  );
  // PHILO-13-15 (Astra C5 check, condition 2): ONE read per form, held here
  // across form changes, so a send of the summary still in flight when he
  // switches to Digest keeps its read and its result. The history is the
  // meeting's: every form's ended sends, each row named by its form.
  const reads = {
    meeting_summary: useSends(`meeting_summary:${meetingId}`),
    meeting_digest: useSends(`meeting_digest:${meetingId}`),
    meeting_followup: useSends(`meeting_followup:${meetingId}`),
  };
  const history = MEETING_FORMS.flatMap((f) => mergeKnown(`${f.value}:${meetingId}`, reads[f.value].data ?? []));
  const formTag = (s: { document_ref: string }) => {
    const f = MEETING_FORMS.find((x) => s.document_ref === `${x.value}:${meetingId}`);
    return f ? { form: f.value, word: f.word } : null;
  };
  return (
    <div data-seat="meeting" data-testid="meeting-send-well">
      <SendWell key={kind} head={head} sendsRead={reads[kind]}
        doc={{ ref: `${kind}:${meetingId}`, title: `${title} ${form.label.toLowerCase()}`, label: `${form.word} ${day(startedAt)}`.trim() }} />
      <SendHistory sends={history} tag={formTag} />
    </div>
  );
}

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
import { SendWells } from "../desk/surface/send";
import { stamp } from "../features/channels/channels";
import "./MeetingSendWell.css";

export const MEETING_FORMS = [
  { value: "meeting_summary", label: "Summary", word: "SUMMARY" },
  { value: "meeting_digest", label: "Digest", word: "DIGEST" },
  { value: "meeting_followup", label: "Follow-up", word: "FOLLOW-UP" },
] as const;
type Form = (typeof MEETING_FORMS)[number]["value"];

/** The form he picked, per meeting: two seats of one meeting show one pick. */
const formPick = new Map<string, Form>();

/** `SEP 29` from an ISO time (the stamp without its clock). */
const day = (iso?: string | null) => (iso ? stamp(iso).replace(/ \d\d:\d\d$/, "") : "");

export function MeetingSendWell({ meetingId, title, startedAt }: {
  meetingId: string; title: string; startedAt?: string | null;
}) {
  const [kind, setKind] = useState<Form>(formPick.get(meetingId) ?? "meeting_summary");
  const form = MEETING_FORMS.find((f) => f.value === kind) ?? MEETING_FORMS[0];
  const head = (
    <div className="send-forms" data-testid="doc-forms">
      <CycleGadget label="Document" value={kind}
        options={MEETING_FORMS.map(({ value, label }) => ({ value, label }))}
        onChange={(v) => { formPick.set(meetingId, v as Form); setKind(v as Form); }} />
    </div>
  );
  return (
    <div data-seat="meeting" data-testid="meeting-send-well">
      <SendWells key={kind} head={head}
        doc={{ ref: `${kind}:${meetingId}`, title: `${title} ${form.label.toLowerCase()}`, label: `${form.word} ${day(startedAt)}`.trim() }} />
    </div>
  );
}

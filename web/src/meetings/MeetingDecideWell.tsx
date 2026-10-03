/* PHILO-13-08 (B3): Decide, next to SEND in the meeting record.
 *
 * Two gestures from an open meeting: `Decide`, then type the title and
 * confirm (Enter or `Save`). The title is asked inline (a well, no modal,
 * UX-CANON A.4); nothing is written before he names it, so an abandoned try
 * leaves no `New decision` record. The decision carries the meeting and its
 * project (desk/decide.ts). The receipt stays here: the meeting lists the
 * decisions made from it, and each row opens its own window (B1's grammar).
 *
 * Seats: the Meetings record (MeetingDetail) and the meeting window
 * (MeetingPullout).
 */
import "./meeting-decide.css";
import { useState } from "react";
import { Button } from "../components/signal/Signal";
import { useDesk } from "../desk/store";
import { refOpener } from "../desk/openObject";
import { StringGadget } from "../desk/surface/gadgets";
import { SurfaceRow, SurfaceRows, SurfaceSection } from "../desk/surface/Surface";
import { decideFromMeeting, decisionsFromMeeting } from "../desk/decide";
import { writeFailureReason } from "../desk/hooks/useWriteReceipt";

const clock = (d: Date) =>
  `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;

export function MeetingDecideWell({ meetingId, title, startedAt, summary }: {
  meetingId: string;
  title: string;
  startedAt?: string | null;
  summary?: string | null;
}) {
  const decisions = useDesk((s) => s.items.decision);
  const made = decisionsFromMeeting(decisions, meetingId);
  const [naming, setNaming] = useState(false);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState("");
  const [receipt, setReceipt] = useState<{ id: string; at: string } | null>(null);

  const abandon = () => {
    setNaming(false);
    setDraft("");
    setRefusal("");
  };
  const save = async () => {
    const name = draft.trim();
    if (!name || busy) return;
    setBusy(true);
    setRefusal("");
    try {
      const { decision } = await decideFromMeeting({
        title: name, meetingId, meetingTitle: title, startedAt, summary,
      });
      setReceipt({ id: decision.id, at: clock(new Date()) });
      setNaming(false);
      setDraft("");
      await useDesk.getState().refresh();
    } catch (cause) {
      setRefusal(writeFailureReason(cause));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div data-seat="meeting" data-testid="meeting-decide-well" role="group" aria-label={`Decide ${title}`}>
      {made.length ? (
        <SurfaceSection label="DECISIONS">
          <SurfaceRows>
            {made.map((d) => (
              <SurfaceRow
                key={d.id}
                title={d.title}
                detail={d.status.toUpperCase()}
                meta={receipt?.id === d.id ? <span data-testid="decide-receipt">✓ DECIDED {receipt.at}</span> : undefined}
                onOpen={refOpener(`decision:${d.id}`) ?? undefined}
              />
            ))}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      {naming ? (
        <div className="meeting-decide-line" data-testid="decide-naming">
          <StringGadget
            label="Decision title"
            placeholder="Decision title"
            value={draft}
            autoFocus
            disabled={busy}
            onChange={setDraft}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault();
                void save();
              } else if (event.key === "Escape") {
                event.preventDefault();
                event.stopPropagation();
                abandon();
              }
            }}
          />
          <Button dense variant="primary" data-testid="decide-save" loading={busy}
            disabled={!draft.trim()} onClick={() => void save()}>
            Save
          </Button>
          <Button dense variant="ghost" data-testid="decide-cancel" disabled={busy} onClick={abandon}>
            Cancel
          </Button>
          {refusal ? (
            <span className="surface-token" data-chip data-testid="decide-refused">⚠ {refusal}</span>
          ) : null}
        </div>
      ) : (
        <div className="meeting-decide-line">
          <Button dense variant="primary" data-testid="meeting-decide" onClick={() => setNaming(true)}>
            Decide
          </Button>
        </div>
      )}
    </div>
  );
}

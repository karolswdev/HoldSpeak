/* Betterment Q9 "Find the tasks": the meeting's outcome rows, on a note.
 *
 * One press runs the meeting's extraction over the note (the hub's
 * note_outcomes_service.py) and draws the meeting's own rows
 * (MeetingDetail.tsx `OutcomeLedger`): Who owes what (task, owner, date) and
 * Decisions (proposed). Each row is one press to Confirm: the task lands
 * where tasks show (Needs you, the person's window), the decision is
 * proposed on the desk, each with the note as its source. The rows stay
 * with the note: the window reads them again when it opens. */
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { OutcomeLedger, type OutcomeRow } from "../../pages/cores/history/OutcomeLedger";
import { useDesk } from "../store";
import { confirmNoteOutcome, findNoteOutcomes, readNoteOutcomes, type NoteOutcome } from "../noteOutcomes";

/** The hub's own words for a refusal; never a raw code. */
function words(cause: unknown): string {
  const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
    ? cause.payload as { message?: unknown } : null;
  const said = typeof payload?.message === "string" ? payload.message.trim() : "";
  return said || "The tasks were not found. The note is unchanged. Try again.";
}

export interface NoteOutcomesState {
  rows: NoteOutcome[];
  finding: boolean;
  startedAt?: number;
  failure: string;
  confirming: string | null;
  find: () => Promise<void>;
  confirm: (row: NoteOutcome) => Promise<void>;
}

export function useNoteOutcomes(noteId: string): NoteOutcomesState {
  const [rows, setRows] = useState<NoteOutcome[]>([]);
  const [finding, setFinding] = useState(false);
  const [startedAt, setStartedAt] = useState<number | undefined>();
  const [failure, setFailure] = useState("");
  const [confirming, setConfirming] = useState<string | null>(null);
  const live = useRef(true);
  useEffect(() => {
    live.current = true;
    // The rows that stay with the note. A note with none, or a hub that
    // does not answer, shows no rows: Find the tasks is still there.
    void readNoteOutcomes(noteId)
      .then((answer) => { if (live.current) setRows(Array.isArray(answer?.rows) ? answer.rows : []); })
      .catch(() => undefined);
    return () => { live.current = false; };
  }, [noteId]);
  const find = useCallback(async () => {
    setFinding(true); setFailure(""); setStartedAt(Date.now());
    try {
      const answer = await findNoteOutcomes(noteId);
      if (live.current) setRows(Array.isArray(answer?.rows) ? answer.rows : []);
    } catch (cause) {
      if (live.current) setFailure(words(cause));
    } finally {
      if (live.current) setFinding(false);
    }
  }, [noteId]);
  const confirm = useCallback(async (row: NoteOutcome) => {
    setConfirming(row.id); setFailure("");
    try {
      const answer = await confirmNoteOutcome(noteId, row.id);
      if (live.current) setRows(Array.isArray(answer?.rows) ? answer.rows : []);
      void useDesk.getState().refresh();
    } catch (cause) {
      if (live.current) setFailure(words(cause));
    } finally {
      if (live.current) setConfirming(null);
    }
  }, [noteId]);
  return { rows, finding, startedAt, failure, confirming, find, confirm };
}

export function NoteOutcomesWell({ outcomes }: { outcomes: NoteOutcomesState }) {
  const { rows, confirming, confirm } = outcomes;
  if (!rows.length) return null;
  const when = (due: string) => (due.trim() ? `by ${due.trim()}` : "no date");
  const toRow = (row: NoteOutcome): OutcomeRow => {
    const made = row.state === "confirmed";
    return {
      key: row.id,
      plate: row.kind === "task" ? "ACT" : "DEC",
      text: row.text,
      meta: row.kind === "task"
        ? `${row.owner || "Me"} · ${made ? "Confirmed" : when(row.due)}`
        : made ? "Proposed on your desk" : "",
      tone: made ? "ok" : "ask",
      owner: row.owner,
      due: row.due,
      verbs: made ? null : (
        <Button dense variant="secondary" loading={confirming === row.id} disabled={Boolean(confirming)}
          aria-label={`Confirm: ${row.text}`} onClick={() => void confirm(row)}>
          Confirm
        </Button>
      ),
    };
  };
  return (
    <div className="note-outcomes" data-testid="note-outcomes">
      <OutcomeLedger label="Who owes what" rows={rows.filter((r) => r.kind === "task").map(toRow)} testId="note-commitments" />
      <OutcomeLedger label="Decisions" rows={rows.filter((r) => r.kind === "decision").map(toRow)} testId="note-decisions" />
    </div>
  );
}

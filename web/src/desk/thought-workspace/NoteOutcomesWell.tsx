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
import { StringGadget } from "../surface/gadgets";
import { WorkMenu, type WorkMenuEntry } from "../components/DeskMenu";
import { ApiError } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { OutcomeLedger, type OutcomeRow } from "../../pages/cores/history/OutcomeLedger";
import { useDesk } from "../store";
import {
  confirmNoteOutcome, dismissNoteOutcome, editNoteOutcome, findNoteOutcomes, readNoteOutcomes, type NoteOutcome,
} from "../noteOutcomes";

/** The hub's own words for a refusal; never a raw code. */
function words(cause: unknown): string {
  const payload = cause instanceof ApiError && cause.payload && typeof cause.payload === "object"
    ? cause.payload as { message?: unknown } : null;
  const said = typeof payload?.message === "string" ? payload.message.trim() : "";
  return said || "The tasks were not found. The note is unchanged. Try again.";
}

export interface NoteOutcomesState {
  /** The note the rows were found in (JRN2: Tonight adds a row's line from it). */
  noteId: string;
  rows: NoteOutcome[];
  finding: boolean;
  startedAt?: number;
  failure: string;
  confirming: string | null;
  find: () => Promise<void>;
  confirm: (row: NoteOutcome) => Promise<void>;
  dismiss: (row: NoteOutcome) => Promise<void>;
  edit: (row: NoteOutcome, fields: { text: string; owner_name?: string; due?: string }) => Promise<boolean>;
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
  /* Betterment Q9 follow-up: a proposed row is edited or dismissed before
     Confirm, as a meeting's rows are. */
  const change = useCallback(async (row: NoteOutcome, call: () => Promise<{ rows?: NoteOutcome[] }>): Promise<boolean> => {
    setConfirming(row.id); setFailure("");
    try {
      const answer = await call();
      if (live.current) setRows(Array.isArray(answer?.rows) ? answer.rows : []);
      return true;
    } catch (cause) {
      if (live.current) setFailure(words(cause));
      return false;
    } finally {
      if (live.current) setConfirming(null);
    }
  }, []);
  const dismiss = useCallback(async (row: NoteOutcome) => {
    await change(row, () => dismissNoteOutcome(noteId, row.id));
  }, [change, noteId]);
  const edit = useCallback((row: NoteOutcome, fields: { text: string; owner_name?: string; due?: string }) =>
    change(row, () => editNoteOutcome(noteId, row.id, fields)), [change, noteId]);
  return { noteId, rows, finding, startedAt, failure, confirming, find, confirm, dismiss, edit };
}

export function NoteOutcomesWell({ outcomes }: { outcomes: NoteOutcomesState }) {
  const { rows, confirming, confirm, dismiss, edit } = outcomes;
  const [more, setMore] = useState<{ id: string; x: number; y: number; autoFocus: boolean } | null>(null);
  const [editing, setEditing] = useState<{ id: string; text: string; owner: string; due: string } | null>(null);
  const moreRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  if (!rows.length) return null;
  const when = (due: string) => (due.trim() ? `by ${due.trim()}` : "no date");
  const save = async (row: NoteOutcome) => {
    if (!editing || editing.id !== row.id) return;
    const fields = row.kind === "task"
      ? { text: editing.text, owner_name: editing.owner, due: editing.due }
      : { text: editing.text };
    if (await edit(row, fields)) setEditing(null);
  };
  const toRow = (row: NoteOutcome): OutcomeRow => {
    const made = row.state === "confirmed";
    const open = editing?.id === row.id ? editing : null;
    const entries: WorkMenuEntry[] = [
      { type: "item", id: `edit-${row.id}`, label: open ? "Close edit" : "Edit",
        onSelect: () => setEditing(open ? null : { id: row.id, text: row.text, owner: row.owner, due: row.due }) },
      { type: "item", id: `dismiss-${row.id}`, label: "Dismiss", onSelect: () => void dismiss(row) },
    ];
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
        <>
          {open ? (
            <Button dense variant="secondary" loading={confirming === row.id} disabled={Boolean(confirming) || !open.text.trim()}
              onClick={() => void save(row)}>
              Save
            </Button>
          ) : (
            <Button dense variant="secondary" loading={confirming === row.id} disabled={Boolean(confirming)}
              aria-label={`Confirm: ${row.text}`} onClick={() => void confirm(row)}>
              Confirm
            </Button>
          )}
          <Button
            ref={(element) => { moreRefs.current[row.id] = element; }}
            dense
            variant="ghost"
            aria-label={`More for ${row.text}`}
            aria-haspopup="menu"
            aria-expanded={more?.id === row.id}
            disabled={Boolean(confirming)}
            onClick={(event) => {
              const rect = event.currentTarget.getBoundingClientRect();
              setMore(more?.id === row.id ? null : { id: row.id, x: rect.left, y: rect.bottom, autoFocus: event.detail === 0 });
            }}
          >
            More
          </Button>
          {more?.id === row.id ? (
            <WorkMenu
              label={`More actions for ${row.text}`}
              x={more.x}
              y={more.y}
              entries={entries}
              autoFocus={more.autoFocus}
              returnFocus={() => moreRefs.current[row.id]?.focus()}
              onClose={() => setMore(null)}
            />
          ) : null}
        </>
      ),
      children: open ? (
        <div className="note-outcome-edit" data-testid="note-outcome-edit">
          <StringGadget label={row.kind === "task" ? "Task" : "Decision"} value={open.text}
            onChange={(value) => setEditing({ ...open, text: value })} disabled={Boolean(confirming)} />
          {row.kind === "task" ? <>
            <StringGadget label="Who?" value={open.owner} onChange={(value) => setEditing({ ...open, owner: value })}
              disabled={Boolean(confirming)} />
            <StringGadget label="When?" value={open.due} onChange={(value) => setEditing({ ...open, due: value })}
              disabled={Boolean(confirming)} />
          </> : null}
        </div>
      ) : undefined,
    };
  };
  return (
    <div className="note-outcomes" data-testid="note-outcomes">
      <OutcomeLedger label="Who owes what" rows={rows.filter((r) => r.kind === "task").map(toRow)} testId="note-commitments" />
      <OutcomeLedger label="Decisions" rows={rows.filter((r) => r.kind === "decision").map(toRow)} testId="note-decisions" />
    </div>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { InspectorForm, ListView, PreferencePane, SurfaceState, PaneNotice, PaneInspector, StringGadget, type ListVerb, type StatusBarItem } from "../../../desk/surface";
import { apiFetch, readableError } from "../../../lib/api";
import { readOutcomeReview, type FollowThroughProposal } from "./useMeetingData";

/** The record's proposed tasks use the same proposal operations as its reader. */
export function useMeetingTasks({ meeting, onChanged, onStatus, kind, reader = false, feedbackKey }: { reader?: boolean; feedbackKey?: string; kind?: "action" | "decision"; meeting: Record<string, unknown>; onChanged(): void; onStatus?(parts: StatusBarItem[]): void }) {
  const meetingId = String(meeting.id);
  const [rows, setRows] = useState<FollowThroughProposal[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<{ id: string; text: string; owner: string; due: string } | null>(null);
  const [reading, setReading] = useState(true);
  const [error, setError] = useState("");
  const [readFailed, setReadFailed] = useState(false);
  const [receipt, setReceipt] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const readVersion = useRef(0);
  const live = useRef(true);
  useEffect(() => { live.current = true; return () => { live.current = false; }; }, []);
  useEffect(() => {
    let current = true;
    const version = ++readVersion.current;
    const currentRead = () => current && version === readVersion.current;
    setReading(true); setError(""); setReadFailed(false);
    void readOutcomeReview(meetingId).then((review) => {
      if (!Array.isArray(review?.proposals)) throw new Error("Tasks not read");
      if (currentRead()) setRows(review.proposals.filter((row) => row.state === "proposed" && (!kind || row.kind === kind)));
    }).catch(() => { if (currentRead()) { setError("Tasks not read"); setReadFailed(true); } })
      .finally(() => { if (currentRead()) setReading(false); });
    return () => { current = false; };
  }, [meetingId, meeting, attempt, kind]);
  useEffect(() => {
    if (feedbackKey && feedbackKey !== "tasks") { onStatus?.([]); return; }
    onStatus?.(readFailed ? [{ key: "tasks-read", lamp: "fail", notice:"Failed", text: "Tasks not read" }] : receipt ? [{ key: "tasks-receipt", text: receipt, priority: 99 }] : error ? [{ key: "tasks-write", lamp: "fail", notice:"Failed", text: error }] : []);
  }, [receipt, error, readFailed, onStatus, feedbackKey]);
  useEffect(() => { setReceipt(""); setDraft(null); setSelected(null); }, [meetingId]);
  const feedbackEpoch = useRef(0);
  const clearFeedback = useCallback(() => { feedbackEpoch.current++; setError(""); setReceipt(""); }, []);
  useEffect(clearFeedback, [feedbackKey, selected, clearFeedback]);
  const edit = (id: string) => {
    const row = rows.find((row) => row.id === id);
    if (row) { setSelected(id); setError(""); setDraft({ id, text: row.text, owner: row.owner ?? row.owner_hint ?? "", due: row.due ?? row.due_hint ?? "" }); }
  };
  const write = async (verb: "confirm" | "edit" | "dismiss", id: string) => {
    if (pending.current) return;
    const epoch = ++feedbackEpoch.current;
    pending.current = true; readVersion.current += 1; setReading(false); setBusy(true); setError(""); setReceipt("");
    try {
      const result = await apiFetch<{ proposal?: FollowThroughProposal; proposal_id?: string; state?: string; error?: string }>(`/api/proposals/${encodeURIComponent(id)}/${verb}`, {
        method: "POST", json: verb === "edit" && draft ? { text: draft.text.trim(), owner: draft.owner.trim(), due: draft.due.trim() } : { binding: rows.find((row) => row.id === id)?.binding },
      });
      if (!result || result.error) throw new Error(result?.error || "Write not confirmed");
      if (verb === "edit" ? result.proposal?.id !== id
        : result.proposal_id !== id || result.state !== (verb === "confirm" ? "confirmed" : "dismissed")) {
        throw new Error("Write not confirmed");
      }
      if (!live.current) return;
      readVersion.current += 1; setReading(false);
      setRows((current) => verb === "edit" ? current.map((row) => row.id === id ? result.proposal! : row) : current.filter((row) => row.id !== id));
      setDraft(null); if (epoch === feedbackEpoch.current) setReceipt(verb === "confirm" ? "Confirmed" : verb === "dismiss" ? "Dismissed" : "Saved");
      onChanged();
    } catch (cause) {
      if (live.current && epoch === feedbackEpoch.current) setError(`${verb === "edit" ? "Not saved" : verb === "confirm" ? "Not confirmed" : "Not dismissed"} · ${readableError(cause)}`);
    } finally { pending.current = false; if (live.current) setBusy(false); }
  };
  const verbs: ListVerb[] = [
    { id: "confirm", label: "Confirm", enabled: (row) => Boolean(row) && !busy && !draft, run: (row) => { if (row) void write("confirm", row.id); } },
    { id: "edit", label: "Edit", enabled: (row) => Boolean(row) && !busy && !draft, run: (row) => { if (row) edit(row.id); } },
    { id: "dismiss", label: "Dismiss", enabled: (row) => Boolean(row) && !busy && !draft, run: (row) => { if (row) void write("dismiss", row.id); } },
  ];
  const list = <PreferencePane label={kind === "decision" ? "Decision proposals" : "Tasks to confirm"} testId="meeting-task-well">
    {readFailed ? <SurfaceState error="Tasks not read" onRetry={() => setAttempt(value => value + 1)} /> : <>
<ListView externalToolbar={reader} label="Tasks to confirm" selectedId={selected} onSelect={setSelected} ordered defaultVerb="edit" verbs={verbs}
      columns={[{ key: "name", word: "Task", priority: 100, track: "minmax(0, 1fr)" }, { key: "owner", word: "Owner", priority: 30, track: "140px" }, { key: "due", word: "Due", priority: 20, track: "120px" }]}
      rows={rows.map((row) => ({ id: row.id, kind: row.kind, name: row.text, cells: { owner: row.owner ?? row.owner_hint ?? "", due: row.due ?? row.due_hint ?? "" } }))}
      rowProps={(row) => ({ "data-testid": `meeting-task-${row.id}` })} />
    {reading ? <SurfaceState loading /> : !rows.length ? <PaneNotice>No tasks to confirm</PaneNotice> : null}
    </>}
  </PreferencePane>;
  const inspector = draft ? <PaneInspector label="Edit task"><InspectorForm rows={[
        { label: "Task", control: <StringGadget label="Task" value={draft.text} disabled={busy} onChange={(text) => setDraft({ ...draft, text })} /> },
        { label: "Owner", control: <StringGadget label="Owner" value={draft.owner} disabled={busy} onChange={(owner) => setDraft({ ...draft, owner })} /> },
        { label: "Due", control: <StringGadget label="Due" value={draft.due} disabled={busy} onChange={(due) => setDraft({ ...draft, due })} /> },
      ]} notice={error ? <SurfaceState error={error} /> : null} completion={{ cancel: () => { setDraft(null); setError(""); }, cancelDisabled: busy,
        primary: { label: "Save", run: () => void write("edit", draft.id), disabled: !draft.text.trim(), busy } }} /></PaneInspector> : null;

  return { list, inspector, selected, clearFeedback };
}

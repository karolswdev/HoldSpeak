import { useEffect, useState } from "react";
import { InspectorFacts, InspectorForm, ListView, PaneInspector, PreferencePane, StringGadget, SurfaceState, type ListVerb } from "../../../desk/surface";
import { effectClassLabel, humanizeWireValue, authorityBasisLabel } from "../../../lib/productLanguage";
import { apiFetch } from "../../../lib/api";
import { openDecisionRecord, openPerson, openRef } from "../../../desk/openObject";
import { openProjectRoom } from "../../../desk/shell";
import { openSourceRef } from "../../../desk/surface/citations";
import { openPrepared, resultServing } from "./PreparedResults";
import type { FollowThroughProposal, MeetingData, MeetingDecision } from "./useMeetingData";
import type { OutcomeRow } from "./OutcomeLedger";

export const MEETING_TRANSCRIPT_OPEN = "holdspeak:meeting-transcript-open";
function deferredToken(value: unknown): string {
  const stamp = String(value ?? "").trim();
  if (!stamp) return "";
  const date = new Date(stamp);
  if (Number.isNaN(date.getTime())) return `Not now · Until ${stamp}`;
  return `Not now · Until ${date.toLocaleDateString(undefined, { weekday: "short" })}`;
}

export function meetingOutcomes(
  data: Pick<MeetingData, "ftProposals" | "openActions" | "settledActions"> &
    { completedActionIds?: ReadonlySet<string> }
    & { meetingDecisions?: readonly MeetingDecision[] },
  intelActions: readonly Record<string, unknown>[] = [],
): {
  decisions: OutcomeRow[];
  commitments: OutcomeRow[];
} {
  const owner = (value: unknown) => String(value ?? "").trim();
  const when = (value: unknown) => {
    const text = String(value ?? "").trim();
    return text ? `By ${text}` : "No date";
  };
  const live = data.ftProposals.filter((p) => p.state !== "dismissed");
  const said = (value: string) => value.trim().toLowerCase().replace(/\s+/g, " ");
  const same = (p: FollowThroughProposal, d: MeetingDecision) =>
    (Boolean(p.decision_record_id) && p.decision_record_id === d.record_id)
    || (Boolean(p.source_artifact_id) && p.source_artifact_id === d.source_artifact_id
      && said(p.text) === said(d.text));
  const recorded = data.meetingDecisions ?? [];
  const stateOf = (d: MeetingDecision | undefined) => {
    const lifecycle = String(d?.lifecycle ?? "").toLowerCase();
    return lifecycle === "superseded" ? "Replaced" : lifecycle === "disputed" ? "Disputed" : "";
  };
  const decisions: OutcomeRow[] = [];
  for (const p of live) {
    if (p.kind !== "decision") continue;
    if (p.state === "proposed") {
      decisions.push({
        key: `ft-${p.id}`, plate: "DEC", text: p.text, meta: "", tone: "ask",
        proposalId: p.id, projectId: p.project_id, segmentIndex: p.segment_index,
      });
      continue;
    }
    const paired = recorded.find((d) => same(p, d));
    if (String(paired?.lifecycle ?? "").toLowerCase() === "rejected") continue;
    decisions.push({
      key: `ft-${p.id}`, plate: "DEC", text: p.text,
      meta: stateOf(paired) || owner(p.owner) || owner(p.owner_hint) || owner(p.speaker_label) || "Decided",
      proposalId: p.id, projectId: p.project_id, segmentIndex: p.segment_index,
      recordId: p.decision_record_id || paired?.record_id || null,
      decisionId: paired?.id ?? null,
    });
  }
  const decisionProposals = live.filter((p) => p.kind === "decision");
  for (const d of recorded) {
    const lifecycle = String(d.lifecycle ?? "").toLowerCase();
    if (lifecycle === "rejected" || !String(d.text ?? "").trim() || decisionProposals.some((p) => same(p, d))) continue;
    decisions.push({
      key: `dec-${d.id}`, plate: "DEC", text: d.text, meta: stateOf(d) || "Decided",
      recordId: d.record_id || null, decisionId: d.id ?? null,
    });
  }

  const actionProposals = data.ftProposals.filter((p) => p.kind === "action");
  const toConfirm = (p: FollowThroughProposal): OutcomeRow => ({
    key: `ft-${p.id}`, plate: "ACT", text: p.text,
    meta: deferredToken(p.deferred_until) || `${owner(p.owner ?? p.owner_hint) || "No owner"} · ${when(p.due ?? p.due_hint)}`,
    tone: "ask", proposalId: p.id,
    owner: owner(p.owner ?? p.owner_hint), due: String(p.due ?? p.due_hint ?? "").trim(),
    gap: !owner(p.owner ?? p.owner_hint) || !String(p.due ?? p.due_hint ?? "").trim(),
    deferredUntil: p.deferred_until,
    projectId: p.project_id,
    segmentIndex: p.segment_index,
  });
  const commitments: OutcomeRow[] = [];
  const itemIds = new Set<string>();
  for (const proposal of actionProposals) {
    if (proposal.state === "dismissed") continue;
    const id = String(proposal.action_item_id ?? "");
    if (id) itemIds.add(id);
    if (proposal.state === "proposed") {
      commitments.push(toConfirm(proposal));
      continue;
    }
    const text = proposal.text || "Action item";
    const who = owner(proposal.owner) || owner(proposal.owner_hint);
    const due = proposal.due ?? proposal.due_hint;
    const linkedStatus = String(proposal.action_status ?? proposal.action_item_status ?? "open").toLowerCase();
    const done = linkedStatus === "done" || linkedStatus === "dismissed";
    commitments.push({
      key: `item-${id || proposal.id}`, plate: "ACT", text,
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "No owner"} · ${when(due)}`,
      tone: done ? "ok" : undefined,
      actionItemId: id || undefined,
      proposalId: proposal.id,
      actionStatus: linkedStatus || null,
      owner: who,
      due: String(due ?? "").trim(),
      projectId: proposal.project_id,
      segmentIndex: proposal.segment_index,
    });
  }
  const items = data.openActions.length || data.settledActions.length
    ? [...data.openActions, ...data.settledActions]
    : [...intelActions];
  for (const [index, row] of items.entries()) {
    const id = String(row.id ?? "");
    if (id && itemIds.has(id)) continue;
    const status = data.completedActionIds?.has(id)
      ? "done"
      : String(row.status ?? "").toLowerCase();
    if (status === "dismissed") continue;
    const text = String(row.task ?? row.text ?? row.title ?? "Action item");
    const who = owner(row.owner);
    const due = row.due;
    const done = status === "done";
    commitments.push({
      key: `item-${id || index}`, plate: "ACT", text,
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "No owner"} · ${when(due)}`,
      tone: done ? "ok" : undefined,
      actionItemId: id || undefined,
      actionStatus: status || null,
      owner: who,
      due: String(due ?? "").trim(),
      projectId: typeof row.project_id === "string" ? row.project_id : null,
    });
  }
  return { decisions, commitments };
}


export function validMeetingSegment(index: unknown, length: number): index is number {
  return typeof index === "number" && Number.isInteger(index) && index >= 0 && index < length;
}

export type OutcomeSelection = { picked: string | null; draft: { id: string; text: string; owner: string; due: string } | null };
const EMPTY_SELECTION: OutcomeSelection = { picked: null, draft: null };

/** Stored decisions and commitments share one selection grammar and operation set. */
export function MeetingOutcomes({ data, meeting, mode = "decisions", onDecide, selection, onSelection, reader = false, failure }: {
  failure?: string; reader?: boolean; selection?: OutcomeSelection; onSelection?(selection: OutcomeSelection): void;
  data: MeetingData; meeting: Record<string, unknown>; mode?: "decisions" | "commitments"; onDecide?(): void;
}) {
  const outcomes = meetingOutcomes(data);
  const rows = mode === "decisions" ? outcomes.decisions : outcomes.commitments;
  const [local, setLocal] = useState<OutcomeSelection>(EMPTY_SELECTION);
  const chosen = selection ?? (onSelection ? EMPTY_SELECTION : local), update = onSelection ?? setLocal;
  const { picked, draft } = chosen;
  const setPicked = (picked: string | null) => update({ picked, draft: null });
  const setDraft = (draft: OutcomeSelection["draft"]) => update({ ...chosen, draft });
  const selected = rows.find(row => row.key === picked);
  const proposal = data.ftProposals.find(row => row.id === selected?.proposalId && row.state === "proposed");
  const [person, setPerson] = useState<string | null>(null), [personFailed, setPersonFailed] = useState(false), [check, setCheck] = useState(0);
  const actionId = selected?.actionItemId;
  useEffect(() => {
    let live = true; setPerson(null); setPersonFailed(false);
    if (actionId) void apiFetch<{ board?: Record<string, { id?: string; source?: string; person_relationship_id?: string }[]> }>("/api/door")
      .then(body => {
        const ids = new Set(Object.values(body.board ?? {}).flat().filter(card => card.source === "action_item" && card.id === actionId && card.person_relationship_id).map(card => card.person_relationship_id!));
        if (live && ids.size === 1) setPerson([...ids][0]);
      }).catch(() => { if (live) setPersonFailed(true); });
    return () => { live = false; };
  }, [actionId, check]);
  useEffect(() => { if (draft && !data.ftProposals.some(row => row.id === draft.id && row.state === "proposed")) setDraft(null); }, [data.ftProposals, draft?.id]);
  const ready = Boolean(selected) && !data.busy;
  const open = () => {
    if (selected?.recordId) openDecisionRecord(selected.recordId);
    else if (selected?.decisionId) openRef(`decision:${selected.decisionId}`);
    else if (selected?.actionItemId) openRef(`action_item:${selected.actionItemId}`);
    else if (selected?.plate === "DEC") onDecide?.();
  };
  const serving = resultServing(data.prepared ?? [], actionId);
  const verbs: ListVerb[] = [
    { id: "open", label: "Open", key: "Enter", enabled: () => ready && Boolean(selected?.recordId || selected?.decisionId || selected?.actionItemId || (selected?.plate === "DEC" && !proposal)), run: open },
    { id: "confirm", label: "Confirm", enabled: () => ready && Boolean(proposal), run: () => { if (proposal) void data.confirmProposal(proposal.id); } },
    { id: "edit", label: "Edit", enabled: () => ready && Boolean(proposal), run: () => { if (proposal) setDraft({ id: proposal.id, text: proposal.text, owner: proposal.owner ?? proposal.owner_hint ?? "", due: proposal.due ?? proposal.due_hint ?? "" }); } },
    { id: "dismiss", label: "Dismiss", enabled: () => ready && Boolean(proposal), run: () => { if (proposal) void data.dismissProposal(proposal.id); } },
    { id: "later", label: "Not now", enabled: () => ready && Boolean(proposal), run: () => { if (proposal) void data.deferProposal(proposal.id); } },
    { id: "done", label: selected?.actionStatus === "done" ? "Reopen" : "Done", enabled: () => ready && Boolean(actionId), run: () => { if (actionId) void data.completeAction(actionId, selected?.actionStatus === "done" ? "reopen" : "done"); } },
    { id: "source", label: "Show in transcript", enabled: () => ready && validMeetingSegment(selected?.segmentIndex, data.segments.length), run: () => { if (selected) openSourceRef(`meeting:${String(meeting.id)}?segment=${selected.segmentIndex}`); } },
    { id: "project", label: "Project", enabled: () => ready && Boolean(selected?.projectId), run: () => { if (selected?.projectId) openProjectRoom(selected.projectId); } },
    { id: "person", label: "People", enabled: () => ready && Boolean(person), run: () => { if (person) openPerson(person, "prep"); } },
    { id: "check-person", label: "Check person", enabled: () => ready && Boolean(actionId) && !person, run: () => setCheck(value => value + 1) },
    { id: "draft", label: "Draft ready", enabled: () => ready && Boolean(serving), run: () => { if (serving) openPrepared(String(meeting.id), serving.kind); } },
    ...(data.outcomeRefreshFailed ? [{ enabled:()=>true, id: "refresh", label: "Read again", run: () => void data.retryOutcomeReview() }] : []),
  ];
  return <PreferencePane label={mode === "decisions" ? "Decisions" : "Commitments"} testId={`meeting-${mode}`} data-feedback-redact="true">
    {!draft ? <ListView externalToolbar={reader} label={mode === "decisions" ? "Decisions" : "Commitments"} rows={rows.map(row => ({ id: row.key, name: row.text, kind: row.plate === "DEC" ? "decision" : "action", cells: { facts: row.meta }, state: row.proposalId && data.ftProposals.some(p => p.id === row.proposalId && p.state === "proposed") ? { label: "To confirm", tone: "ask" as const } : row.actionStatus === "done" ? { label: "Done", tone: "ok" as const } : undefined }))}
      columns={[{ key: "name", word: mode === "decisions" ? "Decision" : "Commitment", track: "minmax(0,1fr)", priority: 100 }, { key: "facts", word: "Facts", track: "220px", priority: 20 }]}
      selectedId={picked} onSelect={setPicked} verbs={verbs} defaultVerb="open" ordered rowProps={row => ({ "data-testid": `meeting-outcome-${row.id}` })} /> : null}
    {draft ? <PaneInspector label={mode === "decisions" ? "Edit decision" : "Edit commitment"}><InspectorForm fit="rows" rows={[
      { label: mode === "decisions" ? "Decision" : "Commitment", control: <StringGadget label={mode === "decisions" ? "Decision" : "Commitment"} value={draft.text} onChange={text => setDraft({ ...draft, text })} /> },
      { label: "Owner", control: <StringGadget label="Owner" value={draft.owner} onChange={owner => setDraft({ ...draft, owner })} /> },
      { label: "Due", control: <StringGadget label="Due" value={draft.due} onChange={due => setDraft({ ...draft, due })} /> },
    ]} notice={failure ? <SurfaceState error={failure} /> : null} completion={{ cancel: () => setDraft(null), primary: { label: "Confirm", disabled: !draft.text.trim() || data.busy, run: () => void data.confirmProposal(draft.id, { text: draft.text.trim(), owner: draft.owner.trim(), due: draft.due.trim() }) } }} /></PaneInspector>
      : selected ? <InspectorFacts name={selected.text} rows={[{ label: "Owner", value: selected.owner }, { label: "Due", value: selected.due }, { label: "State", value: proposal ? "To confirm" : selected.plate === "DEC" ? selected.meta === "Replaced" ? "Replaced" : selected.meta === "Disputed" ? "Disputed" : "Decided" : selected.actionStatus === "done" ? "Done" : "Open" }]} /> : !rows.length ? <p>{data.firstRead ? mode === "decisions" ? "No decisions" : "No commitments" : "Reading outcomes…"}</p> : null}
    {personFailed ? <SurfaceState error="Person not read" onRetry={() => setCheck(value => value + 1)} /> : null}
  </PreferencePane>;
}

/** Gate-backed proposals keep their saved policy and explicit owner decision. */
export function MeetingProposals({ data, picked, onPick }: { data: MeetingData; picked: string | null; onPick(id: string): void }) {
  const selected = data.proposalRows.find(row => String(row.id) === picked);
  const policy = selected?.policy_snapshot as Record<string, unknown> | undefined;
  const operation = selected?.operation as Record<string, unknown> | undefined;
  const actionable = Boolean(selected?.status === "proposed" && policy?.outcome !== "refused" && !data.busy);
  const answer = (choice: "approved" | "rejected") => { if (selected && actionable) void data.decide(selected, choice); };
  return <PreferencePane label="Proposals" testId="meeting-proposals" data-feedback-redact="true">
    <ListView label="Proposals" ordered selectedId={picked} onSelect={onPick} rows={data.proposalRows.map(row => ({ id: String(row.id), kind: "proposal", name: String(row.title || row.preview || "Proposed action"),
      state: (row.policy_snapshot as Record<string, unknown> | null)?.outcome === "refused" ? { label: "Refused", tone: "fail" as const } : row.status !== "proposed" ? { label: String(row.status || "Unknown").replace(/^./, letter => letter.toUpperCase()), tone: "info" as const } : { label: "To decide", tone: "ask" as const } }))}
      columns={[{ key: "name", word: "Proposal", track: "minmax(0,1fr)", priority: 100 }, { key: "state", word: "State", track: "120px", priority: 20 }]}
      verbs={[{ id: "approve", label: "Decide", enabled: () => actionable, run: () => answer("approved") }, { id: "reject", label: "Dismiss", enabled: () => actionable, run: () => answer("rejected") }]} />
    {selected ? <InspectorFacts name={String(selected.title || selected.preview || "Proposed action")} rows={[
      { label: "Effect", value: effectClassLabel(String(operation?.effect_class || selected.action || "")) },
      { label: "Destination", value: humanizeWireValue(String(operation?.destination || selected.target || "")) },
      { label: "Basis", value: authorityBasisLabel(String(policy?.authority_basis || "per_action_required")) },
    ]} /> : null}
  </PreferencePane>;
}

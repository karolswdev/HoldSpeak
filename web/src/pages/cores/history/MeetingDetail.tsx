import { createPortal } from "react-dom";
import { useCompactViewport } from "../../../desk/useCompactViewport";
import { useHasWindowBack, useWindowBack } from "../../../desk/surface/back";
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { failureTitle, plainWords } from "../../../desk/surface/plainFailure";
import { ActionNotice } from "../../../desk/surface/patterns/ActionNotice";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, countLabel, StateChip } from "../../../desk/surface";
import { MeetingRunVerb } from "../../../meetings/runSlot";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import { MeetingSummary, readMeetingIntel } from "../../../meetings/MeetingSummarySlab";
import { Spine, type SpineTone } from "../../../desk/surface/patterns/Spine";
import {
  executedReceipt,
  readLastRefusal,
  readPlannedRoute,
  readRunReceipt,
  type PlannedRoute,
  type SummaryRefusal,
} from "../../../meetings/summaryRoute";
import { apiFetch } from "../../../lib/api";
import type { DetailView, Receipt } from "./helpers";
import {
  MEETING_READS_CAP_MS,
  useMeetingData,
  type FollowThroughProposal,
  type MeetingData,
  type MeetingDecision,
} from "./useMeetingData";
import { meetingReviewCount, type PlateLead } from "./plate";
import type { OutcomeRow } from "./OutcomeLedger";
import { CaptureSlab } from "./CaptureSlab";
import { DraftReady, PreparedResults, resultServing } from "./PreparedResults";
import { MeetingSendWellLazy as MeetingSendWell } from "../../../meetings/MeetingSendWellLazy";
import { SendWellReadContext } from "../../../desk/surface/send/SendWell";
import { MeetingDecideWell } from "../../../meetings/MeetingDecideWell";
import { SummaryRunVerbs, showsRunSummary } from "./SummaryRunVerbs";
import { TranscriptWell } from "./TranscriptWell";
import { LookedAtWell } from "./LookedAtWell";
import { SinceLastWell, readSinceLast } from "./SinceLastWell";
import { AudioOnlyVerb } from "./TranscribeVerb";
import { CycleGadget, StringGadget } from "../../../desk/surface/gadgets";
import { WorkMenu, type WorkMenuEntry } from "../../../desk/components/DeskMenu";
import { openDecisionRecord, openPerson, openRef } from "../../../desk/openObject";
import { openProjectRoom } from "../../../desk/shell";
import { openSourceRef } from "../../../desk/surface/citations";

export const MEETING_TRANSCRIPT_OPEN = "holdspeak:meeting-transcript-open";

function meetingAttendees(...reads: Array<Record<string, unknown> | null | undefined>): string[] {
  for (const read of reads) {
    const names = read?.attendees;
    if (Array.isArray(names)) return names.filter((n): n is string => typeof n === "string" && n.trim() !== "");
  }
  return [];
}

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
    return text ? `by ${text}` : "no date";
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
    return lifecycle === "superseded" ? "REPLACED" : lifecycle === "disputed" ? "DISPUTED" : "";
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
      meta: stateOf(paired) || owner(p.owner) || owner(p.owner_hint) || owner(p.speaker_label) || "DECIDED",
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
      key: `dec-${d.id}`, plate: "DEC", text: d.text, meta: stateOf(d) || "DECIDED",
      recordId: d.record_id || null, decisionId: d.id ?? null,
    });
  }

  const actionProposals = data.ftProposals.filter((p) => p.kind === "action");
  const toConfirm = (p: FollowThroughProposal): OutcomeRow => ({
    key: `ft-${p.id}`, plate: "ACT", text: p.text,
    meta: deferredToken(p.deferred_until) || `${owner(p.owner ?? p.owner_hint) || "no owner"} · ${when(p.due ?? p.due_hint)}`,
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
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "no owner"} · ${when(due)}`,
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
      meta: done ? (who ? `${who} · Done` : "Done") : `${who || "no owner"} · ${when(due)}`,
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

export function MeetingOutcomes({ data, meeting, onDecide, head, reviewSlot, doors, reading }: {
  reading?: ReactNode;
  reviewSlot?: HTMLElement | null;
  doors?: ReactNode;
  data: MeetingData;
  meeting: Record<string, unknown>;
  head?: ReactNode;
  onDecide?: () => void;
}) {
  const intel = ((data.detail ?? meeting)?.intel ?? null) as { action_items?: unknown } | null;
  const intelActions = Array.isArray(intel?.action_items)
    ? (intel!.action_items as unknown[]).filter((a): a is Record<string, unknown> => Boolean(a) && typeof a === "object")
    : [];
  const { decisions, commitments } = meetingOutcomes(data, intelActions);
  type Person = { id?: string; display_name?: string; owner_aliases?: string[] | null };
  type Draft = { text: string; owner: string; due: string };
  type MoreMenu = { x: number; y: number; autoFocus: boolean };
  const [people, setPeople] = useState<Person[]>([]);
  const [peopleLoading, setPeopleLoading] = useState(true);
  const [peopleError, setPeopleError] = useState("");
  const [peopleErrorTitle, setPeopleErrorTitle] = useState("");
  const [peopleAttempt, setPeopleAttempt] = useState(0);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [more, setMore] = useState<Record<string, MoreMenu>>({});
  const [editing, setEditing] = useState<Record<string, boolean>>({});
  type DoorRead = { key: string; status: "pending" | "ready" | "failed"; found: Record<string, string> };
  const [door, setDoor] = useState<DoorRead>({ key: "", status: "ready", found: {} });
  const [doorAttempt, setDoorAttempt] = useState(0);
  const doorRead = useRef<{ key: string; promise: Promise<Record<string, string>> } | null>(null);
  const moreRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  useEffect(() => {
    let live = true;
    setPeopleLoading(true);
    setPeopleError("");
    void apiFetch<{ relationships?: Person[] }>("/api/people/relationships")
      .then((body) => { if (live) setPeople(body.relationships ?? []); })
      .catch((cause) => { if (live) { setPeopleError(plainWords("Could not load people", "Your edits stay here")); setPeopleErrorTitle(failureTitle(cause)); } })
      .finally(() => { if (live) setPeopleLoading(false); });
    return () => { live = false; };
  }, [peopleAttempt]);
  const confirmedActionIds = data.ftProposals
    .filter((proposal) => proposal.kind === "action" && proposal.state === "confirmed" && proposal.action_item_id)
    .map((proposal) => String(proposal.action_item_id).trim())
    .filter(Boolean)
    .sort()
    .join("|");
  const doorReadKey = `${data.reviewRevision ?? ""}:${confirmedActionIds}:${doorAttempt}`;
  useEffect(() => {
    let live = true;
    if (!confirmedActionIds) {
      doorRead.current = null;
      setDoor({ key: doorReadKey, status: "ready", found: {} });
      return () => { live = false; };
    }
    setDoor({ key: doorReadKey, status: "pending", found: {} });
    const wanted = new Set(confirmedActionIds.split("|"));
    const existing = doorRead.current?.key === doorReadKey ? doorRead.current.promise : null;
    const promise = existing ?? apiFetch<{ board?: Record<string, Array<{
      id?: unknown;
      source?: unknown;
      person_relationship_id?: unknown;
    }>> }>("/api/door").then((body) => {
      const found: Record<string, string> = {};
      const ambiguous = new Set<string>();
      for (const cards of Object.values(body.board ?? {})) {
        for (const card of cards ?? []) {
          if (String(card.source ?? "") !== "action_item") continue;
          const actionId = String(card.id ?? "").trim();
          const relationshipId = String(card.person_relationship_id ?? "").trim();
          if (!wanted.has(actionId) || !relationshipId || ambiguous.has(actionId)) continue;
          if (found[actionId] && found[actionId] !== relationshipId) {
            delete found[actionId];
            ambiguous.add(actionId);
            continue;
          }
          found[actionId] = relationshipId;
        }
      }
      return found;
    });
    doorRead.current = { key: doorReadKey, promise };
    void promise
      .then((found) => {
        if (live) setDoor({ key: doorReadKey, status: "ready", found });
      })
      .catch(() => {
        if (doorRead.current?.key === doorReadKey) doorRead.current = null;
        if (live) setDoor({ key: doorReadKey, status: "failed", found: {} });
      });
    return () => { live = false; };
  }, [confirmedActionIds, doorReadKey]);
  const doorCurrent = door.key === doorReadKey ? door : { key: doorReadKey, status: "pending" as const, found: {} };
  const doorPeople = doorCurrent.status === "ready" ? doorCurrent.found : {};
  const checkPerson = () => setDoorAttempt((attempt) => attempt + 1);
  const ownerNames = Array.from(new Set(people
    .map((person) => String(person.display_name ?? "").trim())
    .filter(Boolean)));
  const ownerOptions = [
    { value: "", label: "Who?" },
    { value: "Me", label: "Me" },
    ...ownerNames.filter((name) => name !== "Me").map((name) => ({ value: name, label: name })),
  ];
  const draftFor = (row: OutcomeRow, id: string): Draft =>
    drafts[id] ?? { text: row.text, owner: row.owner ?? "", due: row.due ?? "" };
  const setDraft = (row: OutcomeRow, field: keyof Draft, value: string) => {
    const id = row.proposalId ?? row.key;
    setDrafts((current) => {
      const draft = current[id] ?? { text: row.text, owner: row.owner ?? "", due: row.due ?? "" };
      return { ...current, [id]: { ...draft, [field]: value } };
    });
  };
  const hasSource = (row: OutcomeRow) => validMeetingSegment(row.segmentIndex, data.segments.length);
  const sourceFor = (row: OutcomeRow) => {
    if (!hasSource(row)) return;
    const index = row.segmentIndex;
    openSourceRef(`meeting:${String(meeting.id)}?view=outcomes&segment=${index}`);
  };
  const destinationVerbs = (row: OutcomeRow, durable: boolean) => {
    if (!durable) return null;
    const actionId = row.actionItemId?.trim();
    return (
      <>
        {actionId ? (
          <Button dense variant="secondary" data-testid="proposal-follow-through-btn"
            aria-label={`Open follow-through: ${row.text}`} onClick={() => openRef(`action_item:${actionId}`)}>
            Follow-through
          </Button>
        ) : null}
      </>
    );
  };
  const closeMore = (id: string) => {
    setMore((current) => {
      if (!current[id]) return current;
      const next = { ...current };
      delete next[id];
      return next;
    });
  };
  const verbsFor = (row: OutcomeRow, original: OutcomeRow = row) => {
    const id = row.proposalId ?? (row.key.startsWith("ft-") ? row.key.slice(3) : "");
    const pending = id && data.ftProposals.some((p) => p.id === id && p.state === "proposed");
    const draft = draftFor(original, id);
    const editable = Boolean(pending && row.plate === "ACT");
    const menuEntries: WorkMenuEntry[] = [];
    const menuBusy = data.busy ? "Busy" : undefined;
    if (hasSource(row)) {
      menuEntries.push({
        type: "item", id: `show-transcript-${id}`, label: "Show in transcript", ghost: menuBusy,
        onSelect: () => sourceFor(row),
      });
    }
    if (editable) {
      menuEntries.push({
        type: "item", id: `edit-${id}`, label: editing[id] ? "Close edit" : "Edit", ghost: menuBusy,
        onSelect: () => setEditing((current) => ({ ...current, [id]: !current[id] })),
      });
    }
    if (pending) {
      menuEntries.push(
        {
          type: "item", id: `defer-${id}`, label: "Not now", ghost: menuBusy,
          onSelect: () => void data.deferProposal(id),
        },
        {
          type: "item", id: `dismiss-${id}`, label: "Dismiss", ghost: menuBusy,
          onSelect: () => void data.dismissProposal(id),
        },
      );
    }
    if (!pending && row.projectId) {
      menuEntries.push({
        type: "item", id: `project-${id}`, label: "Project", ghost: menuBusy,
        onSelect: () => openProjectRoom(row.projectId!),
      });
    }
    if (!pending && row.personRelationshipId) {
      menuEntries.push({
        type: "item", id: `people-${id}`, label: "People", ghost: menuBusy,
        onSelect: () => openPerson(row.personRelationshipId!, "prep"),
      });
    } else if (!pending && row.plate === "ACT" && row.proposalId && row.actionItemId) {
      menuEntries.push({
        type: "item", id: `check-person-${id}`, label: "Check person",
        ghost: menuBusy ?? (doorCurrent.status === "pending" ? "Reading" : undefined),
        onSelect: checkPerson,
      });
    }
    const hasMenu = menuEntries.length > 0;
    const menu = hasMenu ? (
      <>
        <Button
          ref={(element) => { moreRefs.current[id] = element; }}
          dense
          variant="ghost"
          loading={data.busy}
          data-testid="proposal-more-btn"
          aria-haspopup="menu"
          aria-expanded={Boolean(more[id])}
          onClick={(event) => {
            const rect = event.currentTarget.getBoundingClientRect();
            if (more[id]) closeMore(id);
            else setMore((current) => ({ ...current, [id]: { x: rect.left, y: rect.bottom, autoFocus: event.detail === 0 } }));
          }}
        >
          More
        </Button>
        {more[id] ? (
          <WorkMenu
            label={`More actions for ${row.text}`}
            x={more[id].x}
            y={more[id].y}
            entries={menuEntries}
            autoFocus={more[id].autoFocus}
            returnFocus={() => moreRefs.current[id]?.focus()}
            onClose={() => closeMore(id)}
          />
        ) : null}
      </>
    ) : null;
    const confirmBlocked = !draft.text.trim()
      || (Boolean(original.owner?.trim()) && !draft.owner.trim())
      || (Boolean(original.due?.trim()) && !draft.due.trim());
    const lifecycle = pending ? (
      <Button dense variant="secondary" loading={data.busy} data-testid="proposal-confirm-btn"
        disabled={confirmBlocked}
        aria-label={`Confirm: ${draft.text}`} onClick={() => {
          setEditing((current) => ({ ...current, [id]: false }));
          void data.confirmProposal(id, {
            text: draft.text.trim() && (editing[id] || draft.text.trim() !== original.text) ? draft.text.trim() : undefined,
            owner: draft.owner || undefined,
            due: draft.due || undefined,
          });
        }}>
        Confirm
      </Button>
    ) : null;
    const actionLifecycle = !pending && row.actionItemId ? (
      row.actionStatus === "done" ? (
        <Button dense variant="secondary" loading={data.busy} data-testid="action-reopen-btn"
          aria-label={`Reopen: ${row.text}`} onClick={() => void data.completeAction?.(row.actionItemId!, "reopen")}>
          Reopen
        </Button>
      ) : row.actionStatus !== "dismissed" ? (
        <Button dense variant="secondary" loading={data.busy} data-testid="action-done-btn"
          aria-label={`Done: ${row.text}`} onClick={() => void data.completeAction?.(row.actionItemId!)}>
          Done
        </Button>
      ) : null
    ) : null;
    const serving = resultServing(data.prepared ?? [], row.actionItemId?.trim());
    const draftReady = serving ? <DraftReady meetingId={String(meeting.id)} result={serving} /> : null;
    const recordId = String(row.recordId ?? "").trim();
    const decisionId = String(row.decisionId ?? "").trim();
    const decide = row.plate === "DEC" && !pending && (recordId || decisionId || onDecide) ? (
      <Button dense variant="secondary" data-testid="decision-decide-btn" aria-label={`Open the record: ${row.text}`}
        onClick={() => {
          if (recordId) openDecisionRecord(recordId);
          else if (decisionId) openRef(`decision:${decisionId}`);
          else onDecide?.();
        }}>
        Open the record
      </Button>
    ) : null;
    return <>{draftReady}{lifecycle}{decide}{actionLifecycle}{destinationVerbs(row, !pending)}{menu}</>;
  };
  const peopleReadRow = commitments.find((row) => row.proposalId
    && (row.gap || editing[row.proposalId])
    && (editing[row.proposalId] || !draftFor(row, row.proposalId).owner))?.proposalId;
  const gapFor = (row: OutcomeRow) => {
    if (!row.proposalId) return undefined;
    const id = row.proposalId;
    if (row.plate !== "ACT" && editing[id]) return undefined;
    if (!row.gap && !editing[id]) return undefined;
    const draft = draftFor(row, id);
    const editableAction = row.plate === "ACT";
    const showOwner = editableAction && (editing[id] || !draft.owner);
    const showDue = editableAction && (editing[id] || !draft.due);
    if (!editing[id] && !showOwner && !showDue) return undefined;
    return (
      <div className="meeting-outcome-gap" data-testid="outcome-gap">
        {editing[id] ? <StringGadget label="Task" value={draft.text} onChange={(value) => setDraft(row, "text", value)} disabled={data.busy} /> : null}
        {showOwner ? <CycleGadget label="Who?" value={draft.owner} options={ownerOptions} onChange={(value) => setDraft(row, "owner", value)} disabled={data.busy} /> : null}
        {showOwner && id === peopleReadRow && (peopleLoading || peopleError) ? <div data-testid="meeting-people-read" aria-busy={peopleLoading || undefined}>
          <ActionNotice tone={peopleError ? "warn" : "info"} role={peopleError ? "alert" : "status"}
            action={peopleError ? { label: "Try again", onClick: () => setPeopleAttempt((attempt) => attempt + 1) } : undefined}>
            {peopleLoading ? "Loading people" : <span title={peopleErrorTitle || undefined}>{peopleError}</span>}
          </ActionNotice>
        </div> : null}
        {showDue ? <StringGadget label="When?" type="date" value={draft.due} onChange={(value) => setDraft(row, "due", value)} disabled={data.busy} /> : null}
      </div>
    );
  };
  const withVerbs = (rows: OutcomeRow[]) => rows.map((row) => {
    const id = row.proposalId ?? row.key;
    const draft = draftFor(row, id);
    const pending = Boolean(data.ftProposals.find((proposal) => proposal.id === id)?.state === "proposed");
    const draftChanged = Boolean(pending && drafts[id]
      && (draft.text !== row.text || draft.owner !== (row.owner ?? "") || draft.due !== (row.due ?? "")));
    const actionId = row.actionItemId?.trim();
    const decorated = { ...row, personRelationshipId: actionId ? doorPeople[actionId] ?? null : null };
    const display = {
      ...decorated,
      text: draftChanged ? draft.text : row.text,
      owner: draftChanged ? draft.owner : row.owner,
      due: draftChanged ? draft.due : row.due,
      meta: draftChanged
        ? `${draft.owner || "no owner"} · ${draft.due ? `by ${draft.due}` : "no date"}`
        : pending && !hasSource(row) && data.ftProposals.find((proposal) => proposal.id === id)?.support === "unknown"
          ? [row.meta, "Not in the transcript"].filter(Boolean).join(" · ")
          : row.meta,
    };
    return {
      ...display,
      verbs: verbsFor(display, row),
      children: gapFor(display),
    };
  });
  const eligible = commitments.filter((row) => {
    const id = row.proposalId;
    if (!id || row.gap) return false;
    const proposal = data.ftProposals.find((item) => item.id === id);
    if (!proposal || proposal.state !== "proposed") return false;
    if (!(proposal.support === "supported" || proposal.support === "source_linked")) return false;
    if (Array.isArray(proposal.unknowns) && proposal.unknowns.length > 0) return false;
    if (data.reviewRevision && proposal.extraction_revision
      && proposal.extraction_revision !== data.reviewRevision) return false;
    return true;
  });
  const bulkBlocked = commitments.some((row) => {
    const id = row.proposalId;
    if (!id || data.ftProposals.find((proposal) => proposal.id === id)?.state !== "proposed") return false;
    if (editing[id]) return true;
    const draft = drafts[id];
    return Boolean(draft && (draft.text !== row.text || draft.owner !== (row.owner ?? "") || draft.due !== (row.due ?? "")));
  });
  const controls = eligible.length || data.outcomeRefreshFailed || (confirmedActionIds && doorCurrent.status === "failed") ? (
    <>
      {eligible.length ? (
        <Button dense variant={bulkBlocked ? "ghost" : "primary"} disabled={bulkBlocked} loading={data.busy} data-testid="proposal-confirm-all-btn" onClick={() => void data.confirmAll()}>
          {countLabel("Confirm all", eligible.length)}
        </Button>
      ) : null}
      {data.outcomeRefreshFailed ? (
        <Button dense variant="ghost" loading={data.busy} data-testid="outcome-refresh-retry-btn"
          aria-label="Retry outcome refresh" onClick={() => void data.retryOutcomeReview()}>
          Retry
        </Button>
      ) : null}
      {confirmedActionIds && doorCurrent.status === "failed" ? (
        <ActionNotice tone="warn" role="alert" action={{ label: "Check", onClick: checkPerson }}>
          <span data-testid="meeting-door-read-failed">Could not read who these are · Nothing changed · Check</span>
        </ActionNotice>
      ) : null}
    </>
  ) : undefined;
  const today = new Date().toISOString().slice(0, 10);
  const pendingIds = new Set(data.ftProposals.filter((p) => p.state === "proposed").map((p) => p.id));
  const weigh = (row: OutcomeRow): { weight: number; tone: SpineTone } => {
    if (row.deferredUntil) return { weight: 6, tone: "graphite" };
    if (row.proposalId && pendingIds.has(row.proposalId)) return { weight: row.plate === "ACT" ? 1 : 2, tone: "brass" };
    if (row.plate === "ACT") {
      if (row.actionStatus === "done") return { weight: 5, tone: "moss" };
      const overdue = /^\d{4}-\d{2}-\d{2}/.test(row.due ?? "") && String(row.due).slice(0, 10) < today;
      return { weight: 3, tone: overdue ? "coral" : "brass" };
    }
    return { weight: 4, tone: row.meta === "DISPUTED" ? "coral" : row.meta === "REPLACED" ? "graphite" : "moss" };
  };
  const rows = [...withVerbs(commitments), ...withVerbs(decisions)]
    .map((row, index) => ({ row, index, ...weigh(row) }))
    .sort((a, b) => a.weight - b.weight || a.index - b.index);
  const needs = data.needsRows ?? [];
  const pending = (row: OutcomeRow) => Boolean(row.proposalId && pendingIds.has(row.proposalId) && !row.deferredUntil);
  const drawRow = ({ row, tone }: typeof rows[number]) => (
    <SurfaceLedgerRow key={row.key}
      data-testid={row.plate === "DEC" ? "meeting-decisions-row" : "meeting-commitments-row"}
      lead={<Spine tone={tone} className="mt-ledger-mark" label={tone === "coral" ? "At risk" : undefined} />}
      primary={<span data-weight={pending(row) || row.plate === "DEC" || (row.due && row.actionStatus !== "done") ? "heavy" : "light"}>{row.text}</span>}
      meta={<>{row.meta.replace(/(?: · )?Done$|^DECIDED$|^DISPUTED$|^REPLACED$/g, "")} <StateChip state={pending(row) ? "warning" : row.actionStatus === "done" ? "success" : tone === "coral" ? "failure" : "idle"}
        label={pending(row) ? "Proposed" : row.deferredUntil ? "Not now" : row.plate === "DEC" ? (row.meta === "DISPUTED" ? "Disputed" : row.meta === "REPLACED" ? "Replaced" : "Decided") : row.actionStatus === "done" ? "Done" : tone === "coral" ? "Overdue" : "Open"} /></>}
      trailing={row.verbs} wrap open={Boolean(row.children)} expands={false}>{row.children}</SurfaceLedgerRow>
  );
  const review = <>
    {controls}
    <SurfaceLedger label="Review outcomes" cols="meeting-outcomes"><ul className="surface-ledger-rows">
      {needs.map((row, index) => <SurfaceLedgerRow key={`need-${index}`} data-testid="meeting-needs-row"
        lead={<Spine tone="brass" className="mt-ledger-mark" />} primary={row.cells[0]} trailing={row.verbs} wrap expands={false} />)}
      {rows.filter(({ row }) => pending(row)).map(drawRow)}
    </ul></SurfaceLedger>
  </>;
  const standing = reviewSlot ? rows.filter(({ row }) => !pending(row)) : rows;
  const groups = [
    { label: "Who owes what", rows: standing.filter(({ row }) => row.plate === "ACT" && row.actionStatus !== "done") },
    { label: "Decisions", rows: standing.filter(({ row }) => row.plate === "DEC") },
    { label: "Done", rows: standing.filter(({ row }) => row.plate === "ACT" && row.actionStatus === "done") },
  ];
  return <>
    {reviewSlot ? createPortal(review, reviewSlot) : null}
    {reading ?? <section className="mt-ledger" aria-label="Outcomes" data-testid="meeting-ledger">
      {head}
      <SurfaceLedger label="Outcomes" cols="meeting-outcomes" controls={reviewSlot ? undefined : controls}>
        <ul className="surface-ledger-rows">
          {reviewSlot ? null : needs.map((row, index) => <SurfaceLedgerRow key={`need-${index}`} data-testid="meeting-needs-row" primary={row.cells[0]} trailing={row.verbs} wrap expands={false} />)}
          {groups.filter((group) => group.rows.length).map((group) => <li key={group.label} className="mt-ledger-group">
            <h3>{group.label}</h3><ul className="surface-ledger-rows">{group.rows.map(drawRow)}</ul>
          </li>)}
          <PreparedResults meetingId={String(meeting.id)} results={data.prepared ?? []} canPrepare={data.canPrepare ?? []}
            selectionHash={readPlannedRoute(data.detail ?? meeting)?.selection_hash ?? null} onChanged={data.refreshPrepared} />
          {doors}
        </ul>
      </SurfaceLedger>
    </section>}
  </>;

}

export function validMeetingSegment(index: unknown, length: number): index is number {
  return typeof index === "number" && Number.isInteger(index) && index >= 0 && index < length;
}

export function MeetingDetail({
  meeting,
  view,
  momentSegmentIndex,
  onClose,
  onDeleted,
  onReceipt,
  onRunIntelligence,
  onSendBack,
  runRefusal,
  onTranscribe,
  revision = 0,
  sendRequested = false,
  decideRequested = false,
  onReviewCount,
  onLead,
  onConflicts,
  onDecide,
  reviewSlot,
  onReading,
}: {
  reviewSlot?: HTMLElement | null;
  onReading?: (reading: boolean) => void;
  onConflicts?: (count: number) => void;
  onLead?: (lead: PlateLead | null) => void;
  onDecide?: () => void;
  onReviewCount?: (count: number) => void;
  meeting: Record<string, unknown> | null;
  sendRequested?: boolean;
  decideRequested?: boolean;
  onTranscribe?: (id: string) => Promise<unknown>;
  view: DetailView;
  momentSegmentIndex?: number | null;
  onClose(): void;
  onDeleted(): void;
  onReceipt(receipt: Receipt): void;
  onRunIntelligence?: (route: PlannedRoute | null) => void;
  onSendBack?: () => void;
  runRefusal?: SummaryRefusal | null;
  revision?: number;
}) {
  const id = String(meeting?.id ?? "");
  const data = useMeetingData(meeting, onReceipt, revision);
  const reviewCount = meetingReviewCount(data);
  useEffect(() => { onReviewCount?.(reviewCount); }, [onReviewCount, reviewCount]);
  const openAction = reviewCount ? undefined : meetingOutcomes(data).commitments.find((row) => row.actionItemId && !row.proposalId && row.actionStatus !== "done");
  useEffect(() => {
    onLead?.(openAction?.actionItemId ? {
      id: openAction.actionItemId, text: openAction.text, facts: openAction.meta, verb: "Done", busy: data.busy,
      act: () => void data.completeAction?.(openAction.actionItemId!),
    } : null);
  }, [openAction?.actionItemId, openAction?.text, openAction?.meta, data.busy, onLead, reviewCount]);
  const [wellRead, setWellRead] = useState<{ id: string; read: boolean } | null>(null);
  const reportWell = useCallback((read: boolean) => {
    setWellRead({ id, read });
    if (read && sendRequested) window.requestAnimationFrame(() => {
      const well = document.getElementById(`meeting-${id}-send`);
      well?.scrollIntoView?.({ block: "start", behavior: "smooth" });
      well?.querySelector<HTMLElement>("button:not(:disabled), input, textarea")?.focus({ preventScroll: true });
    });
  }, [id, sendRequested]);
  const [cappedFor, setCappedFor] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(() => setCappedFor(id), MEETING_READS_CAP_MS);
    return () => window.clearTimeout(timer);
  }, [id]);
  const [drawnFor, setDrawnFor] = useState("");
  const wellAsked = sendRequested && view === "outcomes" && Boolean(readMeetingIntel(data.detail ?? meeting)?.summary?.trim());
  const wellDone = !wellAsked || (wellRead?.id === id && wellRead.read);
  const ready = cappedFor === id || (data.firstRead && wellDone);
  useLayoutEffect(() => {
    if (ready && drawnFor !== id) setDrawnFor(id);
  }, [ready, drawnFor, id]);
  const shown = drawnFor === id || ready;
  const [reader, setReader] = useState<"summary" | "transcript" | "context" | null>(momentSegmentIndex != null ? "transcript" : null);
  const compact = useCompactViewport();
  const hostedBack = useHasWindowBack();
  const bodyRef = useRef<HTMLDivElement>(null);
  const readerRef = useRef<HTMLElement>(null);
  const doorRef = useRef("meeting-read-summary");
  const back = () => {
    setReader(null);
    window.requestAnimationFrame(() => bodyRef.current?.querySelector<HTMLElement>(`[data-testid=${doorRef.current}]`)?.focus());
  };
  useWindowBack({ onBack: reader ? back : onClose, testId: reader ? "meeting-reader-back" : "meeting-record-back" }, [reader, onClose]);
  useEffect(() => { onReading?.(Boolean(reader)); }, [reader, onReading]);
  useEffect(() => {
    if (!reader || (reader === "transcript" && momentSegmentIndex != null)) return;
    const frame = window.requestAnimationFrame(() => readerRef.current?.scrollIntoView?.({ block: "start" }));
    return () => window.cancelAnimationFrame(frame);
  }, [reader, momentSegmentIndex]);
  useEffect(() => {
    const onOpen = (event: Event) => {
      if ((event as CustomEvent<string>).detail === id) setReader("transcript");
    };
    window.addEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
    return () => window.removeEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
  }, [id]);
  useEffect(() => { if (momentSegmentIndex != null) setReader("transcript"); }, [momentSegmentIndex]);
  const {
    detail,
    setDetail,
    segments,

    intelOff,
    intelState,
  } = data;

  if (!meeting) return null;
  const summaryIntel = readMeetingIntel(detail ?? meeting);
  const plannedRoute = readPlannedRoute(detail ?? meeting);
  const displayedRoute = runRefusal?.route ?? plannedRoute;
  const runReceipt = executedReceipt(id, readRunReceipt(detail ?? meeting));

  const meetingTitle = String(detail?.title ?? meeting.title ?? "Meeting");
  const hasTranscript = segments.length > 0 || (
    meeting.transcriptWords != null && Number(meeting.transcriptWords) > 0
  );

  return (
    <SurfaceSection>
      <SendWellReadContext.Provider value={reportWell}>
      <div ref={bodyRef} className="meetings-detail-body" data-settling={shown ? undefined : "true"} aria-busy={shown ? undefined : true}>
      {shown ? null : <div className="meetings-detail-settling-line"><SurfaceState loading /></div>}
      {onTranscribe ? (
        <MeetingRunVerb>
          <AudioOnlyVerb row={{ ...meeting, ...(detail ?? {}) }} onTranscribe={onTranscribe} setUpSpeech testId="meeting-transcribe" />
        </MeetingRunVerb>
      ) : null}
      <CaptureSlab detail={detail} meeting={meeting} />
      <div id={`meeting-${id}-conflict`} className="meetings-detail-anchor">
      <MeetingConflictRecovery
        meetingId={id}
        onCount={onConflicts}
        onResolved={(result) => {
          onDeleted();
          if (result.deleted) {
            onClose();
          } else if (result.meeting) {
            setDetail(result.meeting);
          }
        }}
      />
      </div>
      <MeetingIntelRecovery
        meetingId={id}
        revision={revision}
        onChanged={async () => {
          setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
          onDeleted();
        }}
      />
      <>
          <MeetingOutcomes data={data} meeting={meeting} onDecide={onDecide} reviewSlot={reviewSlot} reading={reader ? <section ref={readerRef} className="mt-reader" data-testid="meeting-reader" aria-label={reader === "summary" ? "Summary" : reader === "transcript" ? "Transcript" : "Meeting context"}>
        <header className="mt-reader-head">
          {compact && hostedBack ? null : <Button dense variant="secondary" data-testid="meeting-reader-back" onClick={back}>Back</Button>}
          <h3>{reader === "summary" ? "Summary" : reader === "transcript" ? "Transcript" : "Meeting context"}</h3>
        </header>
        {reader === "summary" ? <MeetingSummary intel={summaryIntel} receipt={runReceipt} />
          : reader === "transcript" ? <TranscriptWell id={id} segments={segments} momentSegmentIndex={momentSegmentIndex}
            emptyLabel={speechWasMissing(detail ?? meeting) ? NO_TRANSCRIPT_SPEECH : undefined} />
          : <><SinceLastWell since={readSinceLast(data.aftercare)} meetingId={id} /><LookedAtWell items={runReceipt?.looked_at} /></>}
      </section> : undefined} doors={<>
            <li className="mt-ledger-group"><h3>Read</h3></li>
            {summaryIntel?.summary?.trim() ? <SurfaceLedgerRow primary="Summary" meta={(summaryIntel.topics ?? []).join(" · ")} expands={false}
              trailing={<Button dense variant="secondary" data-testid="meeting-read-summary" onClick={() => { doorRef.current = "meeting-read-summary"; setReader("summary"); }}>Read summary</Button>} /> : null}
            <SurfaceLedgerRow primary="Transcript" meta={segments.length ? `${segments.length} ${segments.length === 1 ? "segment" : "segments"}` : "No transcript"} expands={false}
              trailing={<Button dense variant="secondary" data-testid="meeting-read-transcript" onClick={() => { doorRef.current = "meeting-read-transcript"; setReader("transcript"); }}>Read transcript</Button>} />
            {readSinceLast(data.aftercare) || runReceipt?.looked_at?.length ? <SurfaceLedgerRow primary="Meeting context" expands={false}
              trailing={<Button dense variant="secondary" data-testid="meeting-read-context" onClick={() => { doorRef.current = "meeting-read-context"; setReader("context"); }}>Read context</Button>} /> : null}
          </>} head={<>
            <SummaryRunVerbs
              intelOff={intelOff}
              intelState={intelState}
              hasTranscript={hasTranscript}
              plannedRoute={displayedRoute}
              refusal={runRefusal}
              durableRefusal={readLastRefusal(detail ?? meeting)}
              onRunIntelligence={onRunIntelligence ? () => onRunIntelligence(displayedRoute) : undefined}
              onRetryIntelligence={
                (intelState === "error" || intelState === "failed") && onRunIntelligence
                  ? () => onRunIntelligence(displayedRoute)
                  : undefined
              }
              onSkipIntelligence={
                (intelState === "queued" || intelState === "pending")
                  ? async () => {
                      try {
                        await apiFetch(`/api/meetings/${encodeURIComponent(id)}/intel-recovery/skip`, { method: "POST" });
                        setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
                        onDeleted();
                      } catch {  }
                    }
                  : undefined
              }
            />
          </>} />
              {sendRequested ? (
            <div id={`meeting-${id}-send`} className="meetings-detail-anchor">
              {summaryIntel?.summary?.trim() ? (
                <MeetingSendWell meetingId={id} title={meetingTitle} onBack={onSendBack}
                  startedAt={String((detail ?? meeting)?.started_at ?? "") || null} />
              ) : (
                <div role="status">Summary unavailable <Button dense variant="ghost" onClick={onDeleted}>Retry</Button></div>
              )}
            </div>
          ) : null}
              {decideRequested ? <div id={`meeting-${id}-decide`} className="meetings-detail-anchor"><MeetingDecideWell defaultOpen meetingId={id} title={meetingTitle}
            startedAt={String((detail ?? meeting)?.started_at ?? "") || null}
            deciders={meetingAttendees(meeting, detail)}
            summary={summaryIntel?.summary ?? null}
            runSummaryOnFace={showsRunSummary({
              intelOff, hasTranscript, plannedRoute: displayedRoute,
              onRunIntelligence: onRunIntelligence ? () => undefined : undefined,
            })} /></div> : null}
        </>
      </div>
      </SendWellReadContext.Provider>
    </SurfaceSection>
  );
}

// HS-170-04 — the meeting detail pane (the board's right side).
// Display title + tokens, NEEDS YOU section, TRANSCRIPT well, settled list.
import { NO_TRANSCRIPT_SPEECH, speechWasMissing } from "../../../desk/firstrun/speechTruth";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { plainFailure } from "../../../desk/surface/plainFailure";
import { ActionNotice } from "../../../desk/surface/patterns/ActionNotice";
import { AppHead, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState } from "../../../desk/surface";
import { MeetingConflictRecovery } from "../../../meetings/MeetingConflictRecovery";
import { MeetingIntelRecovery } from "../../../meetings/MeetingIntelRecovery";
import {
  MeetingSummarySlab,
  readMeetingIntel,
} from "../../../meetings/MeetingSummarySlab";
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
import { MeetingHeader, meetingOutcomeFact, meetingPipelineActive } from "./MeetingHeader";
import { CaptureSlab } from "./CaptureSlab";
import { ArtifactsLibrary } from "./ArtifactsLibrary";
import { MeetingSendWellLazy as MeetingSendWell } from "../../../meetings/MeetingSendWellLazy";
import { SendWellReadContext } from "../../../desk/surface/send/SendWell";
import { MeetingDecideWell } from "../../../meetings/MeetingDecideWell";
import { NeedsYouTable, showsRunSummary } from "./NeedsYouTable";
import { TranscriptWell } from "./TranscriptWell";
import { LookedAtWell } from "./LookedAtWell";
import { SinceLastWell, readSinceLast } from "./SinceLastWell";
import { AudioOnlyVerb } from "./TranscribeVerb";
import { CycleGadget, StringGadget } from "../../../desk/surface/gadgets";
import { WorkMenu, type WorkMenuEntry } from "../../../desk/components/DeskMenu";
import { openPerson, openRef } from "../../../desk/openObject";
import { openProjectRoom } from "../../../desk/shell";
import { openSourceRef } from "../../../desk/surface/citations";


/** PHILO-17: the meeting window's foot asks its record to open the
 *  transcript fold (`detail`: the meeting id). */
export const MEETING_TRANSCRIPT_OPEN = "holdspeak:meeting-transcript-open";

/** One row of the meeting's outcomes ledgers. */
type OutcomeRow = {
  key: string;
  plate: "DEC" | "ACT";
  text: string;
  meta: string;
  tone?: "ask" | "ok";
  actionItemId?: string;
  proposalId?: string;
  actionStatus?: string | null;
  owner?: string;
  due?: string;
  projectId?: string | null;
  personRelationshipId?: string | null;
  segmentIndex?: number | null;
  gap?: boolean;
  deferredUntil?: string | null;
  verbs?: ReactNode;
  children?: ReactNode;
};

function deferredToken(value: unknown): string {
  const stamp = String(value ?? "").trim();
  if (!stamp) return "";
  const date = new Date(stamp);
  if (Number.isNaN(date.getTime())) return `NOT NOW · UNTIL ${stamp}`;
  return `NOT NOW · UNTIL ${date.toLocaleDateString(undefined, { weekday: "short" }).toUpperCase()}`;
}

/** Phase 16 (the interior kit; the canvas window "Cutover sync"): the
 *  meeting's Decisions and Commitments, each a Section over a Ledger. A
 *  proposed decision carries Confirm and Dismiss; a
 *  confirmed one names its owner.
 *
 *  Commitments are OBLIGATIONS, one row each (Astra r1 M1): an action
 *  proposal names its action item (`action_item_id`, the producer's link in
 *  proposal_bridge_service.py), so the item and its proposal are ONE row
 *  while the proposal waits. A dismissed proposal or item is
 *  never drawn. The items are the aftercare's rows, else the meeting's own
 *  (`intel.action_items`). A Section with no rows is not drawn (A.8). */
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
  // PHILO-17 ("what did we decide yesterday?"): the decisions the meeting
  // recorded are on its record too (the ledger: never a confirmed action).
  // A proposal and a ledger row are the same decision only by identity: the
  // record the proposal wrote, or its artifact with the same words. The pair
  // is one row, and it says the RECORD's state (Astra r2: a record replaced
  // or disputed after Confirm is not DECIDED). A rejected one is not drawn.
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
    });
  }
  const decisionProposals = live.filter((p) => p.kind === "decision");
  for (const d of recorded) {
    const lifecycle = String(d.lifecycle ?? "").toLowerCase();
    if (lifecycle === "rejected" || !String(d.text ?? "").trim() || decisionProposals.some((p) => same(p, d))) continue;
    decisions.push({ key: `dec-${d.id}`, plate: "DEC", text: d.text, meta: stateOf(d) || "DECIDED" });
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
  // Outcomes is a single projection.  Every linked action carries both the
  // proposal decision and the action completion fact from the server.
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

function OutcomeLedger({ label, rows, testId, controls }: { label: string; rows: OutcomeRow[]; testId: string; controls?: ReactNode }) {
  if (!rows.length) return null;
  return (
    <SurfaceSection label={label} count={rows.length || null} data-testid={testId} className="meeting-outcome-section">
      <SurfaceLedger label={label} cols="meeting-outcomes" controls={controls}>
        <ul className="surface-ledger-rows">
          {rows.map((row) => (
            <SurfaceLedgerRow
              key={row.key}
              data-testid={`${testId}-row`}
              primary={row.text}
              meta={row.meta}
              metaTone={row.tone}
              trailing={row.verbs}
              wrap
              open={Boolean(row.children)}
              expands={false}
            >{row.children}</SurfaceLedgerRow>
          ))}
        </ul>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

export function MeetingOutcomes({ data, meeting }: { data: MeetingData; meeting: Record<string, unknown> }) {
  const intel = ((data.detail ?? meeting)?.intel ?? null) as { action_items?: unknown } | null;
  const intelActions = Array.isArray(intel?.action_items)
    ? (intel!.action_items as unknown[]).filter((a): a is Record<string, unknown> => Boolean(a) && typeof a === "object")
    : [];
  const { decisions, commitments } = meetingOutcomes(data, intelActions);
  // The proposals' verbs: Confirm and Dismiss. Never the filled
  // primary: the meeting's one primary is Send (the foot).
  type Person = { id?: string; display_name?: string; owner_aliases?: string[] | null };
  type Draft = { text: string; owner: string; due: string };
  type MoreMenu = { x: number; y: number; autoFocus: boolean };
  const [people, setPeople] = useState<Person[]>([]);
  const [peopleLoading, setPeopleLoading] = useState(true);
  const [peopleError, setPeopleError] = useState("");
  const [peopleAttempt, setPeopleAttempt] = useState(0);
  const [drafts, setDrafts] = useState<Record<string, Draft>>({});
  const [more, setMore] = useState<Record<string, MoreMenu>>({});
  const [editing, setEditing] = useState<Record<string, boolean>>({});
  const [doorPeople, setDoorPeople] = useState<Record<string, string>>({});
  const doorRead = useRef<{ key: string; promise: Promise<Record<string, string>> } | null>(null);
  const moreRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  useEffect(() => {
    let live = true;
    setPeopleLoading(true);
    setPeopleError("");
    void apiFetch<{ relationships?: Person[] }>("/api/people/relationships")
      .then((body) => { if (live) setPeople(body.relationships ?? []); })
      .catch((cause) => { if (live) setPeopleError(plainFailure("PEOPLE DID NOT LOAD", cause)); })
      .finally(() => { if (live) setPeopleLoading(false); });
    return () => { live = false; };
  }, [peopleAttempt]);
  // People is a read-time projection of the Door. Resolve a destination by
  // the durable action item id only; the owner label on a meeting row is not
  // enough to guess a relationship (aliases can be ambiguous or unavailable).
  const confirmedActionIds = data.ftProposals
    .filter((proposal) => proposal.kind === "action" && proposal.state === "confirmed" && proposal.action_item_id)
    .map((proposal) => String(proposal.action_item_id).trim())
    .filter(Boolean)
    .sort()
    .join("|");
  const doorReadKey = `${data.reviewRevision ?? ""}:${confirmedActionIds}`;
  useEffect(() => {
    let live = true;
    if (!confirmedActionIds) {
      doorRead.current = null;
      setDoorPeople({});
      return () => { live = false; };
    }
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
        if (live) setDoorPeople(found);
      })
      .catch(() => {
        if (doorRead.current?.key === doorReadKey) doorRead.current = null;
        if (live) setDoorPeople({});
      });
    return () => { live = false; };
  }, [confirmedActionIds, doorReadKey]);
  const ownerOptions = [
    { value: "", label: "Who?" },
    { value: "Me", label: "Me" },
    ...people
      .map((person) => String(person.display_name ?? "").trim())
      .filter(Boolean)
      .map((name) => ({ value: name, label: name })),
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
          <Button dense variant="primary" data-testid="proposal-follow-through-btn"
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
    return <>{lifecycle}{actionLifecycle}{destinationVerbs(row, !pending)}{menu}</>;
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
            action={peopleError ? { label: "Retry", onClick: () => setPeopleAttempt((attempt) => attempt + 1) } : undefined}>
            {peopleLoading ? "PEOPLE LOADING" : peopleError}
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
  const controls = (
    <>
      {eligible.length ? (
        <Button dense variant={bulkBlocked ? "ghost" : "primary"} disabled={bulkBlocked} loading={data.busy} data-testid="proposal-confirm-all-btn" onClick={() => void data.confirmAll()}>
          Confirm all {eligible.length}
        </Button>
      ) : null}
      {data.outcomeRefreshFailed ? (
        <Button dense variant="ghost" loading={data.busy} data-testid="outcome-refresh-retry-btn"
          aria-label="Retry outcome refresh" onClick={() => void data.retryOutcomeReview()}>
          Retry
        </Button>
      ) : null}
    </>
  );
  const decisionsControls = !commitments.length && data.outcomeRefreshFailed ? (
    <Button dense variant="ghost" loading={data.busy} data-testid="outcome-refresh-retry-btn"
      aria-label="Retry outcome refresh" onClick={() => void data.retryOutcomeReview()}>
      Retry
    </Button>
  ) : null;
  return (
    <>
      <OutcomeLedger label="Decisions" rows={withVerbs(decisions)} testId="meeting-decisions" controls={decisionsControls} />
      <OutcomeLedger label="Who owes what" rows={withVerbs(commitments)} testId="meeting-commitments" controls={controls} />
    </>
  );
}

/** A source destination requires a stored numeric segment, including valid zero. */
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
  runRefusal,
  onTranscribe,
  saidOnFace,
  revision = 0,
  sendRequested = false,
  decideRequested = false,
}: {
  meeting: Record<string, unknown> | null;
  sendRequested?: boolean;
  decideRequested?: boolean;
  /** PHILO-17 (U16): the engine host the window's foot already names. */
  saidOnFace?: string | null;
  /** PHILO-17 transcribe: start Transcribe on this audio-only meeting. */
  onTranscribe?: (id: string) => Promise<unknown>;
  /** "outcomes" (the face) or "artifacts". */
  view: DetailView;
  /** HS-109-02/05: a resolved decision moment seeks this transcript row. */
  momentSegmentIndex?: number | null;
  onClose(): void;
  onDeleted(): void;
  /** HS-111-03 — outcomes land on the footer receipt bar. */
  onReceipt(receipt: Receipt): void;
  /** HS-201-04 — called with the route this RECORD displays, so the
   *  disclosure and the request are the same object. */
  onRunIntelligence?: (route: PlannedRoute | null) => void;
  /** HS-201-04 — the hub's 409 on this record's last run gesture. */
  runRefusal?: SummaryRefusal | null;
  /** PHILO-17: bumped by the meeting window when its records may have moved. */
  revision?: number;
}) {
  const id = String(meeting?.id ?? "");
  const data = useMeetingData(meeting, onReceipt, revision);
  // PHILO-17 (the desk sweep): the body is drawn once (per meeting) when
  // the record's first reads and its Send well's have ended, or at the cap.
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
  // The Send well is drawn on the outcomes face of a meeting with a summary.
  const wellAsked = sendRequested && view === "outcomes" && Boolean(readMeetingIntel(data.detail ?? meeting)?.summary?.trim());
  const wellDone = !wellAsked || (wellRead?.id === id && wellRead.read);
  const ready = cappedFor === id || (data.firstRead && wellDone);
  useLayoutEffect(() => {
    if (ready && drawnFor !== id) setDrawnFor(id);
  }, [ready, drawnFor, id]);
  const shown = drawnFor === id || ready;
  // PHILO-17 (quiet by default): with a summary on the record the
  // transcript is folded; Open transcript (the foot) and a decision moment
  // open it. With no summary it is the record's content, open.
  const hasSummaryText = Boolean(readMeetingIntel(data.detail ?? meeting)?.summary?.trim());
  const [transcriptAsked, setTranscriptOpen] = useState<boolean | null>(null);
  const transcriptOpen = transcriptAsked ?? (!hasSummaryText || momentSegmentIndex != null);
  useEffect(() => {
    const onOpen = (event: Event) => {
      if ((event as CustomEvent<string>).detail === id) setTranscriptOpen(true);
    };
    window.addEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
    return () => window.removeEventListener(MEETING_TRANSCRIPT_OPEN, onOpen);
  }, [id]);
  useEffect(() => {
    if (momentSegmentIndex != null) setTranscriptOpen(true);
  }, [momentSegmentIndex]);
  const {
    detail,
    setDetail,
    segments,
    artifactRows,
    intelOff,
    intelState,
    needsRows,
    needsCount,
    timelineRows,
  } = data;

  if (!meeting) return null;

  // HS-201-04: the summary the hub persisted, and the route facts that
  // belong beside every verb that starts a run. The detail read model is
  // the source for all three (`intel`, `planned_route`, `run_receipt`).
  const summaryIntel = readMeetingIntel(detail ?? meeting);
  const plannedRoute = readPlannedRoute(detail ?? meeting);
  // The route the record DISPLAYS: a refusal's fresh route wins over it.
  const displayedRoute = runRefusal?.route ?? plannedRoute;
  const runReceipt = executedReceipt(id, readRunReceipt(detail ?? meeting));

  const meetingTitle = String(detail?.title ?? meeting.title ?? "Meeting");
  const hasTranscript = segments.length > 0 || (
    meeting.transcriptWords != null && Number(meeting.transcriptWords) > 0
  );
  const compactSavedOutcome = view === "outcomes" && !meetingPipelineActive(meeting, data);

  return (
    <SurfaceSection>
      {compactSavedOutcome ? (
        <AppHead
          className="meetings-detail-head"
          fact={meetingOutcomeFact(meeting, data)}
          as="div"
        >
          <MeetingHeader meeting={meeting} data={data} compact saidOnFace={saidOnFace} />
        </AppHead>
      ) : (
        <MeetingHeader meeting={meeting} data={data} compact={false} saidOnFace={saidOnFace} />
      )}
      {/* PHILO-17 (the desk sweep): the record's body is mounted at once
          (its wells start their reads) but drawn only when its first reads
          end, the Send well's included, or at the cap: a late read never
          moves a row under the owner's eye (UX-CANON D; the Room's pattern,
          roomReads.ts and project-room.css .room-body[data-settling]). */}
      <SendWellReadContext.Provider value={reportWell}>
      <div className="meetings-detail-body" data-settling={shown ? undefined : "true"} aria-busy={shown ? undefined : true}>
      {shown ? null : <div className="meetings-detail-settling-line"><SurfaceState loading /></div>}
      {/* PHILO-17 transcribe: an audio-only meeting's one verb, under the
          strip that says "NO TRANSCRIPT · SPEECH NOT SET UP". */}
      {onTranscribe ? (
        <AudioOnlyVerb row={{ ...meeting, ...(detail ?? {}) }} onTranscribe={onTranscribe} setUpSpeech testId="meeting-transcribe" />
      ) : null}
      <CaptureSlab detail={detail} meeting={meeting} />
      <MeetingConflictRecovery
        meetingId={id}
        onResolved={(result) => {
          onDeleted();
          if (result.deleted) {
            onClose();
          } else if (result.meeting) {
            setDetail(result.meeting);
          }
        }}
      />
      <MeetingIntelRecovery
        meetingId={id}
        revision={revision}
        onChanged={async () => {
          setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
          onDeleted();
        }}
      />
      {view === "artifacts" ? (
        <ArtifactsLibrary
          artifactRows={artifactRows}
          meetingTitle={meetingTitle}
        />
      ) : (
        <>
          {/* PHILO-17 (the Today language): what was said first (the
              summary), then what was decided and who owes what, then the
              follow-up (Send), the transcript last. */}
          <MeetingSummarySlab intel={summaryIntel} receipt={runReceipt} saidOnFace={saidOnFace} />
          {/* betterment/capture C6: what changed since the last meeting of this kind. */}
          <SinceLastWell since={readSinceLast(data.aftercare)} meetingId={id} />
          <MeetingOutcomes data={data} meeting={meeting} />
          <NeedsYouTable
            needsRows={needsRows}
            needsCount={needsCount}
            intelOff={intelOff}
            intelState={intelState}
            hasTranscript={hasTranscript}
            plannedRoute={displayedRoute}
            refusal={runRefusal}
            durableRefusal={readLastRefusal(detail ?? meeting)}
            onRunIntelligence={
              onRunIntelligence ? () => onRunIntelligence(displayedRoute) : undefined
            }
            onRetryIntelligence={
              (intelState === "error" || intelState === "failed") && onRunIntelligence
                ? () => onRunIntelligence(displayedRoute)
                : undefined
            }
            onSkipIntelligence={
              // HS-201-04: error/failed belong to the summary slab, which
              // already carries Retry and Skip. Only the QUEUED state (the
              // slab suppresses itself there) keeps its Skip here.
              (intelState === "queued" || intelState === "pending")
                ? async () => {
                    try {
                      await apiFetch(
                        `/api/meetings/${encodeURIComponent(id)}/intel-recovery/skip`,
                        { method: "POST" },
                      );
                      setDetail(await apiFetch(`/api/meetings/${encodeURIComponent(id)}`));
                      onDeleted();
                    } catch { /* stays */ }
                  }
                : undefined
            }
          />
          {/* PHILO-11-05 (canvas C1, C4): SUMMARY, then SEND; no summary, no well.
              The old aftercare Slack rows are gone (R7): the digest and the
              follow-up are forms of this one well. */}
          {sendRequested ? (
            <div id={`meeting-${id}-send`} className="meetings-detail-anchor">
              {summaryIntel?.summary?.trim() ? (
                <MeetingSendWell meetingId={id} title={meetingTitle}
                  startedAt={String((detail ?? meeting)?.started_at ?? "") || null} />
              ) : (
                <div role="status">Summary unavailable <Button dense variant="ghost" onClick={onDeleted}>Retry</Button></div>
              )}
            </div>
          ) : null}
          {/* PHILO-13-08 (B3): Decide, next to SEND; with or without a summary. */}
          {decideRequested ? <div id={`meeting-${id}-decide`} className="meetings-detail-anchor"><MeetingDecideWell defaultOpen meetingId={id} title={meetingTitle}
            startedAt={String((detail ?? meeting)?.started_at ?? "") || null}
            summary={summaryIntel?.summary ?? null}
            runSummaryOnFace={showsRunSummary({
              intelOff, hasTranscript, plannedRoute: displayedRoute,
              onRunIntelligence: onRunIntelligence ? () => undefined : undefined,
            })} /></div> : null}
          <div id={`meeting-${id}-transcript`} className="meetings-detail-anchor">
            <TranscriptWell
              id={id}
              segments={segments}
              momentSegmentIndex={momentSegmentIndex}
              open={transcriptOpen}
              onOpenChange={setTranscriptOpen}
              emptyLabel={speechWasMissing(detail ?? meeting) ? NO_TRANSCRIPT_SPEECH : undefined}
            />
          </div>
          {/* betterment/capture C2: what the summary read, each with its date. */}
          <LookedAtWell items={runReceipt?.looked_at} />
          {/* RAW · ROUTING — the intent timeline section (only when data present) */}
          {timelineRows.length > 0 ? (
            <div className="meetings-detail-routing">
              <span className="surface-caption">RAW · ROUTING</span>
              <ul>
                {timelineRows.map((row, i) => (
                  <li key={i}>{String(row.kind ?? row.intent ?? row.text ?? "")}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}
      </div>
      </SendWellReadContext.Provider>
    </SurfaceSection>
  );
}

// HS-172 — extracted from MeetingDetail: the parallel API fetches and
// derived row arrays. Now also fetches follow-through proposals.
import { preloadMeetingSendWell } from "../../../meetings/MeetingSendWellLazy";
import { useCallback, useEffect, useRef, useState } from "react";
import type {
  MeetingDetailResponse,
  MeetingArtifactsResponse,
  MeetingAftercareResponse,
  MeetingTimelineResponse,
  MeetingProposalsResponse,
  AuthorityPolicyResponse,
} from "../core-types";
import { apiFetch, readableError } from "../../../lib/api";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import { asRows } from "../../pageSupport";
import type { Receipt, NeedsRow } from "./helpers";
import type { ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { presentValue } from "../../../desk/surface/format";
import {
  effectClassLabel,
  humanizeWireValue,
  authorityBasisLabel,
  proposalStatusLabel,
} from "../../../lib/productLanguage";

/** HS-172: a follow-through proposal from the wire. */
export interface FollowThroughProposal {
  id: string;
  meeting_id: string;
  project_id?: string | null;
  kind: "decision" | "action";
  text: string;
  owner_hint?: string | null;
  due_hint?: string | null;
  speaker_label?: string | null;
  model_host?: string | null;
  state: "proposed" | "confirmed" | "dismissed";
  created_at: string;
  /** What the owner confirmed (the wire's `owner`, `due`). */
  owner?: string | null;
  due?: string | null;
  /** Phase 16 (Astra r1 M1): the action item an action proposal names (the
   *  producer's link, proposal_bridge_service.py): one obligation, one row. */
  action_item_id?: string | null;
  /** The record a confirmed proposal wrote, and the artifact it came from
   *  (PHILO-17: a recorded decision is the same one only by identity). */
  decision_record_id?: string | null;
  source_artifact_id?: string | null;
}

export interface MeetingData {
  detail: Record<string, unknown> | null;
  setDetail: (detail: Record<string, unknown> | null) => void;
  error: string;
  segments: Record<string, unknown>[];
  artifactRows: Record<string, unknown>[];
  actionRows: Record<string, unknown>[];
  timelineRows: Record<string, unknown>[];
  proposalRows: Record<string, unknown>[];
  openActions: Record<string, unknown>[];
  settledActions: Record<string, unknown>[];
  authority: Record<string, unknown>;
  aftercare: Record<string, unknown>;
  busy: boolean;
  decide: (
    proposal: Record<string, unknown>,
    decision: "approved" | "rejected",
  ) => Promise<void>;
  hasOutcomes: boolean;
  intelOff: boolean;
  /** The raw intel state string for QUEUED/FAILED verb display. */
  intelState: string;
  captureBad: boolean;
  needsRows: NeedsRow[];
  needsCount: number;
  startedAt: unknown;
  durationS: number;
  /** HS-172: follow-through proposals for this meeting. */
  ftProposals: FollowThroughProposal[];
  confirmProposal: (id: string) => Promise<void>;
  dismissProposal: (id: string) => Promise<void>;
  /** PHILO-17: the decisions the meeting recorded (the `decisions` table,
   *  `GET /api/decisions?meeting_id=`), not only its proposals. */
  meetingDecisions: MeetingDecision[];
  /** PHILO-17 (the desk sweep): the record's first reads ended (each read
   *  or failed; the newest read of its records). The record holds its body
   *  until then, or until MEETING_READS_CAP_MS, so no late read moves a row
   *  under the owner's eye (UX-CANON D). */
  firstRead: boolean;
}

/** The record body is drawn after this long even when a read is still out
 *  (the Room's cap, roomReads.ts ROOM_READS_CAP_MS). */
export const MEETING_READS_CAP_MS = 8000;

/** The record's first reads, by name (useMeetingData). */
const FIRST_READS = [
  "detail", "sendWell", "artifacts", "aftercare", "timeline", "proposals", "authority", "ftProposals", "decisions",
] as const;
type FirstRead = (typeof FIRST_READS)[number];

/** PHILO-17: one decision the meeting recorded (a ledger row of
 *  `GET /api/decisions?scope=all&meeting_id=`: never a confirmed action; its
 *  lifecycle is its record's when it has one). */
export interface MeetingDecision {
  id: string;
  text: string;
  lifecycle?: string | null;
  decided_at?: string | null;
  record_id?: string | null;
  source_artifact_id?: string | null;
}

export function useMeetingData(
  meeting: Record<string, unknown> | null,
  onReceipt: (receipt: Receipt) => void,
  /** PHILO-17 (Astra r1): a count the host bumps when the meeting's own
   *  records may have moved (a Review confirm, a desk change) though the
   *  meeting row did not: the decisions and proposals read again. */
  revision = 0,
): MeetingData {
  const id = String(meeting?.id ?? "");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(meeting);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>>({});
  const [aftercare, setAftercare] = useState<Record<string, unknown>>({});
  const [timeline, setTimeline] = useState<Record<string, unknown>>({});
  const [proposals, setProposals] = useState<Record<string, unknown>>({});
  const [authority, setAuthority] = useState<Record<string, unknown>>({});
  const [ftProposals, setFtProposals] = useState<FollowThroughProposal[]>([]);
  const [meetingDecisions, setMeetingDecisions] = useState<MeetingDecision[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  // PHILO-17 (the desk sweep; Astra r1 on #1108): each first read, by name,
  // for this meeting. A read counts once it ended (read or failed); a records
  // read superseded by a newer one (a desk change) counts when the newer one
  // of the SAME name ends. A new object for the same meeting (a list refresh)
  // keeps what has ended; another meeting starts again.
  const [ended, setEnded] = useState<{ id: string; names: readonly string[] }>({ id: "", names: [] });
  const markEnded = useCallback((forId: string, name: FirstRead) => {
    setEnded((cur) => {
      if (cur.id !== forId) return { id: forId, names: [name] };
      return cur.names.includes(name) ? cur : { id: forId, names: [...cur.names, name] };
    });
  }, []);
  const firstRead = ended.id === id && FIRST_READS.every((name) => ended.names.includes(name));
  // PHILO-17 (Astra r2): ONE freshness rule for the meeting's own records
  // (aftercare, proposals, follow-through proposals, decisions), read by the
  // first read and again on every revision: only the newest request writes.
  const recordsSeq = useRef(0);
  useEffect(() => {
    if (!id) return;
    const records = ++recordsSeq.current;
    const newest = <T,>(apply: (value: T) => void) => (value: T) => {
      if (records === recordsSeq.current) apply(value);
    };
    /* HS-202-02 (Astra's counsel finding 3 on PR #595, one layer deeper
       than it pointed) — every read here is for THIS record. A response
       that lands after the owner opened another meeting must be dropped,
       or the record on the glass wears another meeting's facts. The
       rendered fence in `__tests__/meetingRefresh202.test.tsx` catches
       exactly that: without this guard a stalled `/api/meetings/m-1`
       overwrote the open m-2. */
    let live = true;
    const mine = <T,>(apply: (value: T) => void) => (value: T) => {
      if (live) apply(value);
    };
    // Each read ends on its own (allSettled): a failure never ends the others.
    const end = (name: FirstRead) => () => { if (live) markEnded(id, name); };
    const endNewest = (name: FirstRead) => () => {
      if (live && records === recordsSeq.current) markEnded(id, name);
    };
    setDetail(meeting);
    setError("");
    void apiFetch<MeetingDetailResponse>(`/api/meetings/${encodeURIComponent(id)}`)
      .then(mine(setDetail))
      .catch((reason) => { if (live) setError(readableError(reason)); })
      .finally(end("detail"));
    // The Send well's own chunk: the body waits for it too (it drew a
    // frame late and moved the rows under it).
    void preloadMeetingSendWell().finally(end("sendWell"));
    void apiFetch<MeetingArtifactsResponse>(`/api/meetings/${encodeURIComponent(id)}/artifacts`)
      .then(mine(setArtifacts))
      .catch(() => { if (live) setArtifacts({}); })
      .finally(end("artifacts"));
    void apiFetch<MeetingAftercareResponse>(`/api/meetings/${encodeURIComponent(id)}/aftercare`)
      .then(mine(newest(setAftercare)))
      .catch(() => { if (live && records === recordsSeq.current) setAftercare({}); })
      .finally(endNewest("aftercare"));
    void apiFetch<MeetingTimelineResponse>(
      `/api/meetings/${encodeURIComponent(id)}/intent-timeline`,
    )
      .then(mine(setTimeline))
      .catch(() => { if (live) setTimeline({}); })
      .finally(end("timeline"));
    void apiFetch<MeetingProposalsResponse>(`/api/meetings/${encodeURIComponent(id)}/proposals`)
      .then(mine(newest(setProposals)))
      .catch(() => { if (live && records === recordsSeq.current) setProposals({}); })
      .finally(endNewest("proposals"));
    void apiFetch<AuthorityPolicyResponse>("/api/authority/policy")
      .then(mine(setAuthority))
      .catch(() => { if (live) setAuthority({}); })
      .finally(end("authority"));
    void apiFetch<{ proposals: FollowThroughProposal[] }>(
      `/api/meetings/${encodeURIComponent(id)}/follow-through-proposals`,
    )
      .then(mine(newest((res: { proposals?: FollowThroughProposal[] }) =>
        setFtProposals(res.proposals ?? []))))
      .catch(() => { if (live && records === recordsSeq.current) setFtProposals([]); })
      .finally(endNewest("ftProposals"));
    void apiFetch<{ decisions?: MeetingDecision[] }>(
      `/api/decisions?scope=all&limit=500&meeting_id=${encodeURIComponent(id)}`,
    )
      .then(mine(newest((res: { decisions?: MeetingDecision[] }) =>
        setMeetingDecisions(Array.isArray(res?.decisions) ? res.decisions : []))))
      .catch(() => { if (live && records === recordsSeq.current) setMeetingDecisions([]); })
      .finally(endNewest("decisions"));
    return () => {
      live = false;
    };
  }, [id, meeting, markEnded]);
  // PHILO-17 (Astra r1): Confirm in Review writes proposal and decision
  // records, not the meeting row, so the reads above (keyed on the meeting
  // object) never re-ran and Outcomes still said TO DECIDE. These reads
  // follow the host's revision on their own; the meeting object (and the
  // Send well's form) stays as it is.
  useEffect(() => {
    if (!id || revision === 0) return;
    let live = true;
    const records = ++recordsSeq.current;
    const mine = <T,>(apply: (value: T) => void) => (value: T) => {
      if (live && records === recordsSeq.current) apply(value);
    };
    // A newer read ends the first read of its OWN name only (Astra r1 on
    // #1108): the detail, artifacts and the rest still hold the body.
    const endNewest = (name: FirstRead) => () => {
      if (live && records === recordsSeq.current) markEnded(id, name);
    };
    void apiFetch<MeetingAftercareResponse>(`/api/meetings/${encodeURIComponent(id)}/aftercare`)
      .then(mine(setAftercare)).catch(() => undefined).finally(endNewest("aftercare"));
    void apiFetch<MeetingProposalsResponse>(`/api/meetings/${encodeURIComponent(id)}/proposals`)
      .then(mine(setProposals)).catch(() => undefined).finally(endNewest("proposals"));
    void apiFetch<{ proposals: FollowThroughProposal[] }>(
      `/api/meetings/${encodeURIComponent(id)}/follow-through-proposals`,
    ).then(mine((res: { proposals?: FollowThroughProposal[] }) => setFtProposals(res.proposals ?? [])))
      .catch(() => undefined).finally(endNewest("ftProposals"));
    void apiFetch<{ decisions?: MeetingDecision[] }>(
      `/api/decisions?scope=all&limit=500&meeting_id=${encodeURIComponent(id)}`,
    ).then(mine((res: { decisions?: MeetingDecision[] }) =>
      setMeetingDecisions(Array.isArray(res?.decisions) ? res.decisions : [])))
      .catch(() => undefined).finally(endNewest("decisions"));
    return () => {
      live = false;
    };
  }, [id, revision, markEnded]);
  const { subscribe } = useRuntimeBus();
  useEffect(
    () =>
      subscribe("actuator_result", (frame) => {
        const event = frame.data as Record<string, unknown> | undefined;
        if (!event?.id || String(event.meeting_id ?? "") !== id) return;
        setProposals((current) => {
          const rows = Array.isArray(current.proposals)
            ? (current.proposals as Record<string, unknown>[])
            : [];
          if (!rows.some((row) => String(row.id) === String(event.id)))
            return current;
          return {
            ...current,
            proposals: rows.map((row) =>
              String(row.id) === String(event.id) ? { ...row, ...event } : row,
            ),
          };
        });
      }),
    [subscribe, id],
  );
  const decide = async (
    proposal: Record<string, unknown>,
    decision: "approved" | "rejected",
  ) => {
    setBusy(true);
    try {
      await apiFetch(
        `/api/meetings/${encodeURIComponent(id)}/proposals/${encodeURIComponent(String(proposal.id))}/decision`,
        { method: "POST", json: { decision } },
      );
      setProposals(
        await apiFetch(`/api/meetings/${encodeURIComponent(id)}/proposals`),
      );
      onReceipt({
        text: decision === "approved" ? "APPROVED" : "REJECTED",
      });
    } catch (reason) {
      onReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusy(false);
    }
  };

  // HS-172: confirm/dismiss follow-through proposals.
  const confirmProposal = async (proposalId: string) => {
    setBusy(true);
    try {
      await apiFetch(`/api/proposals/${encodeURIComponent(proposalId)}/confirm`, {
        method: "POST",
      });
      // Phase 16 (Astra r1 M2): the confirmed proposal stays on the record
      // (Decisions · n keeps it, now decided), never vanishing until a reload.
      setFtProposals((prev) => prev.map((p) => (p.id === proposalId ? { ...p, state: "confirmed" } : p)));
      onReceipt({ text: "CONFIRMED" });
    } catch (reason) {
      onReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusy(false);
    }
  };

  const dismissProposal = async (proposalId: string) => {
    setBusy(true);
    try {
      await apiFetch(`/api/proposals/${encodeURIComponent(proposalId)}/dismiss`, {
        method: "POST",
      });
      setFtProposals((prev) => prev.map((p) => (p.id === proposalId ? { ...p, state: "dismissed" } : p)));
      onReceipt({ text: "DISMISSED" });
    } catch (reason) {
      onReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusy(false);
    }
  };

  const segments = asRows(detail, ["segments", "transcript"]);
  const artifactRows = asRows(artifacts, ["artifacts", "items"]);
  const actionRows = asRows(aftercare, ["action_items", "actions", "items"]);
  const timelineRows = asRows(timeline, ["timeline", "items"]);
  const proposalRows = asRows(proposals, ["proposals"]);
  const openActions = actionRows.filter((row) => row.status !== "done");
  const settledActions = actionRows.filter((row) => row.status === "done");

  const startedAt = detail?.started_at ?? meeting?.started_at;
  const durationS = Number(detail?.duration_seconds ?? meeting?.duration_seconds ?? 0);
  const intelStatus = detail?.intel_status;
  const intelState =
    typeof intelStatus === "object" && intelStatus !== null
      ? String((intelStatus as Record<string, unknown>).state ?? "")
      : String(intelStatus ?? "");
  const intelOff = intelState === "disabled";
  const hasOutcomes =
    proposalRows.length > 0 || openActions.length > 0 || settledActions.length > 0 || ftProposals.length > 0
    || meetingDecisions.length > 0;
  const captureBad =
    Boolean(detail?.capture_status) && detail?.capture_status !== "finalized";

  // Legacy actuator proposals.
  const undecided = proposalRows.filter(
    (row) =>
      row.status === "proposed" &&
      (row.policy_snapshot as Record<string, unknown> | undefined)?.outcome !== "refused",
  ).length;
  const needsCount = undecided;

  // Phase 16 (the interior kit; the canvas window "Cutover sync"): the
  // follow-through proposals and the open actions are the Decisions and
  // Commitments ledgers (MeetingDetail `MeetingOutcomes`); NEEDS YOU keeps
  // the legacy actuator proposals and the summary run's verbs.
  const needsRows: NeedsRow[] = [
    // Legacy actuator proposals (from the old aftercare/proposals pipeline).
    ...proposalRows.map((row) => {
      const policy = (row.policy_snapshot ?? {}) as Record<string, unknown>;
      const operation = (row.operation ?? {}) as Record<string, unknown>;
      const refused = policy.outcome === "refused";
      const effect = String(operation.effect_class ?? row.action ?? "");
      const destination = String(operation.destination ?? row.target ?? "");
      const facts = [
        effect ? `EFFECT: ${effectClassLabel(effect)}` : null,
        destination ? `DEST: ${humanizeWireValue(destination)}` : null,
        `BASIS: ${authorityBasisLabel(
          String(policy.authority_basis ?? "per_action_required"),
        )}`,
      ]
        .filter((fact): fact is string => Boolean(fact))
        .join(" · ")
        .toUpperCase();
      const commitment = row.commitment as Record<string, unknown> | undefined;
      return {
        cells: [
          <span key="what" title={presentValue(row.preview ?? row.body ?? "")}>
            {String(row.title ?? row.preview ?? row.kind ?? "Proposed action")}
          </span>,
          <span key="facts" title={facts}>
            {facts}
          </span>,
        ] as ReactNode[],
        verbs:
          row.status === "proposed" && !refused ? (
            <>
              <Button
                dense
                loading={busy}
                title={String(commitment?.approve ?? "")}
                onClick={() => void decide(row, "approved")}
              >
                Decide
              </Button>
              <Button
                dense
                variant="ghost"
                title={String(commitment?.reject ?? "")}
                onClick={() => void decide(row, "rejected")}
              >
                Dismiss
              </Button>
            </>
          ) : (
            <span
              className="surface-token"
              data-tone={refused ? "danger" : undefined}
            >
              {refused
                ? "REFUSED"
                : proposalStatusLabel(String(row.status ?? "")).toUpperCase()}
            </span>
          ),
      };
    }),
  ];

  return {
    detail,
    setDetail,
    error,
    segments,
    artifactRows,
    actionRows,
    timelineRows,
    proposalRows,
    openActions,
    settledActions,
    authority,
    aftercare,
    busy,
    decide,
    hasOutcomes,
    intelOff,
    intelState,
    captureBad,
    needsRows,
    needsCount,
    startedAt,
    durationS,
    ftProposals,
    confirmProposal,
    dismissProposal,
    meetingDecisions,
    firstRead,
  };
}

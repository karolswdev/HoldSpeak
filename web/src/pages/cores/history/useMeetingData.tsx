// HS-117-09 — extracted from MeetingDetail: the 6 parallel API
// fetches and derived row arrays.
import { useEffect, useState } from "react";
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
  proposeSlack: (what: "digest" | "followup") => Promise<void>;
  /** Derived: has any outcomes at all. */
  hasOutcomes: boolean;
  /** Derived: intelligence is disabled. */
  intelOff: boolean;
  /** Derived: capture is in a bad state. */
  captureBad: boolean;
  /** The needs-you table rows. */
  needsRows: NeedsRow[];
  needsCount: number;
  startedAt: unknown;
  durationS: number;
}

export function useMeetingData(
  meeting: Record<string, unknown> | null,
  onReceipt: (receipt: Receipt) => void,
): MeetingData {
  const id = String(meeting?.id ?? "");
  const [detail, setDetail] = useState<Record<string, unknown> | null>(meeting);
  const [artifacts, setArtifacts] = useState<Record<string, unknown>>({});
  const [aftercare, setAftercare] = useState<Record<string, unknown>>({});
  const [timeline, setTimeline] = useState<Record<string, unknown>>({});
  const [proposals, setProposals] = useState<Record<string, unknown>>({});
  const [authority, setAuthority] = useState<Record<string, unknown>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!id) return;
    setDetail(meeting);
    setError("");
    void Promise.all([
      apiFetch<MeetingDetailResponse>(`/api/meetings/${encodeURIComponent(id)}`).then(
        setDetail,
      ),
      apiFetch<MeetingArtifactsResponse>(`/api/meetings/${encodeURIComponent(id)}/artifacts`)
        .then(setArtifacts)
        .catch(() => setArtifacts({})),
      apiFetch<MeetingAftercareResponse>(`/api/meetings/${encodeURIComponent(id)}/aftercare`)
        .then(setAftercare)
        .catch(() => setAftercare({})),
      apiFetch<MeetingTimelineResponse>(
        `/api/meetings/${encodeURIComponent(id)}/intent-timeline`,
      )
        .then(setTimeline)
        .catch(() => setTimeline({})),
      apiFetch<MeetingProposalsResponse>(`/api/meetings/${encodeURIComponent(id)}/proposals`)
        .then(setProposals)
        .catch(() => setProposals({})),
      apiFetch<AuthorityPolicyResponse>("/api/authority/policy")
        .then(setAuthority)
        .catch(() => setAuthority({})),
    ]).catch((reason) => setError(readableError(reason)));
  }, [id, meeting]);
  // HS-132-03 — `actuator_result` was broadcast to nobody. A proposal
  // decided or executed anywhere else (the ambient card, a device, mission
  // control) now lands on THIS open meeting without a refetch.
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
      onReceipt({ text: `⚠ REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusy(false);
    }
  };
  const proposeSlack = async (what: "digest" | "followup") => {
    setBusy(true);
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(id)}/export/slack`, {
        method: "POST",
        json: { what },
      });
      setProposals(
        await apiFetch(`/api/meetings/${encodeURIComponent(id)}/proposals`),
      );
      onReceipt({
        text: what === "digest" ? "PROPOSED DIGEST" : "PROPOSED FOLLOW-UP",
      });
    } catch (reason) {
      onReceipt({ text: `⚠ REFUSED · ${readableError(reason)}`, tone: "danger" });
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
  const intelOff =
    (typeof intelStatus === "object" && intelStatus !== null
      ? String((intelStatus as Record<string, unknown>).state ?? "")
      : String(intelStatus ?? "")) === "disabled";
  const hasOutcomes =
    proposalRows.length > 0 || openActions.length > 0 || settledActions.length > 0;
  const captureBad =
    Boolean(detail?.capture_status) && detail?.capture_status !== "finalized";

  /* The needs-you table: undecided proposals lead, open action items
     follow — pending receipts, one dense table (audit §3.2.3). */
  const undecided = proposalRows.filter(
    (row) =>
      row.status === "proposed" &&
      (row.policy_snapshot as Record<string, unknown> | undefined)?.outcome !== "refused",
  ).length;
  const needsCount = undecided + openActions.length;
  const needsRows: NeedsRow[] =
    [
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
              {String(row.title ?? row.kind ?? "Proposed action")}
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
                  Approve
                </Button>
                <Button
                  dense
                  variant="ghost"
                  title={String(commitment?.reject ?? "")}
                  onClick={() => void decide(row, "rejected")}
                >
                  Reject
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
      ...openActions.map((row) => ({
        cells: [
          <span key="what">{String(row.text ?? row.title ?? "Action item")}</span>,
          <span key="facts">
            {presentValue(row.owner) ? `OWNER: ${presentValue(row.owner)}`.toUpperCase() : ""}
          </span>,
        ] as ReactNode[],
        verbs: <span className="surface-token" data-tone="warn">OPEN</span> as ReactNode,
      })),
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
    proposeSlack,
    hasOutcomes,
    intelOff,
    captureBad,
    needsRows,
    needsCount,
    startedAt,
    durationS,
  };
}

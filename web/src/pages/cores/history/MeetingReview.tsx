// HS-200-12 — the meeting REVIEW wing (posture 4 of the daily workflow).
// Boards: P4Review (1440), P4ReviewPhone (393), P4Processing (loading +
// resumed).  One projection (`/api/meetings/{id}/outcome-review`), read
// through `reviewModel.ts`; every verb calls the canonical proposal routes
// and renders the durable result they return.
//
// Laws this face obeys (settled design D1 / D2(d)):
//  - coverage rides above the answer, in every state, and is N OF N only
//    when the read is complete;
//  - one verb per row (`Confirm`); `Edit`, `Dismiss` and `Open evidence`
//    live in the row's MORE disclosure; `Open evidence` is withheld when
//    the proposal has no span (a verb that does nothing is a lie);
//  - the three claim axes are three chips: PROPOSAL · <support> ·
//    <acceptance>; an unknown owner/due is a typed unknown chip until
//    supplied; an edited sentence reads LINKED · EDITED;
//  - one filled primary (`Accept reviewed`), drawn refused when nothing is
//    left to accept; egress where egress happened (the job's host);
//  - `ATTEMPT n · SAME JOB` and `ALREADY KEPT n` (a verb that opens the kept
//    rows) on the processing face — the owner's Q5 verdict;
//  - Enter on a row fires Confirm, Escape closes MORE, Backspace never
//    dismisses; Confirm leaves the row in place, Dismiss moves focus on.
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { openSurfaceOr } from "../../../desk/shell";
import { useRuntimeBus } from "../../../runtime/RuntimeBus";
import {
  ConfirmVerb,
  EditInPlace,
  SurfaceState,
} from "../../../desk/surface/Surface";
import { SurfaceFooter } from "../../../desk/surface/SurfaceFooter";
import { EgressChip } from "../../../desk/surface/gadgets";
import { egressFor } from "../../../desk/surface/egress";
import { StateChip } from "../../../desk/surface/patterns/StateChip";
import { Disclosure } from "../../../desk/surface/patterns/Disclosure";
import { ProgressPlan, type PlanStep } from "../../../desk/surface/patterns/ProgressPlan";
import { useRovingRows } from "../../../desk/surface/roving";
import { useWindowTitle } from "../../../desk/surface/title";
import { countLabel } from "../../../desk/surface/count";
import {
  acceptanceToken,
  decodeMeetingReview,
  decodeReviewProposal,
  heldReason,
  isPriorRevision,
  jobHandle,
  reviewHeadline,
  spanLabel,
  stamp,
  supportToken,
  unknownToken,
  type MeetingReviewModel,
  type ReviewProposal,
} from "./reviewModel";

type Receipt = { text: string; tone?: "warn" | "danger" | "success" };

const PROCESSING = new Set(["queued", "reserved", "claimed", "running"]);

function nowStamp(): string {
  return stamp(new Date().toISOString());
}

export function MeetingReview({
  meetingId,
  onOpenEvidence,
  onOpenTranscript,
  onRunIntelligence,
  onChanged,
}: {
  meetingId: string;
  /** Lands on the transcript well scrolled to the span's segment. */
  onOpenEvidence(segmentIndex: number): void;
  onOpenTranscript(): void;
  /** `Re-read` on a failed read; absent when the meeting cannot be re-run. */
  onRunIntelligence?: () => void;
  /** A durable write happened; the host may refresh what it lists. */
  onChanged?: () => void;
}) {
  const [model, setModel] = useState<MeetingReviewModel | null>(null);
  const [error, setError] = useState("");
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [accepting, setAccepting] = useState(false);
  const rowsRef = useRef<HTMLDivElement>(null);
  useRovingRows(rowsRef, { selector: ".meetings-review-line" });
  // Counsel P2-ii: the window title bar carries the meeting's name while
  // the review is open (the subject, said once); the body never repeats it.
  useWindowTitle(model?.title || null, [model?.title]);

  const load = useCallback(async () => {
    if (!meetingId) return;
    try {
      const raw = await apiFetch<Record<string, unknown>>(
        `/api/meetings/${encodeURIComponent(meetingId)}/outcome-review`,
      );
      setModel(decodeMeetingReview(raw));
      setError("");
    } catch (reason) {
      setError(readableError(reason));
    }
  }, [meetingId]);

  useEffect(() => {
    setModel(null);
    setOpenId(null);
    setReceipt(null);
    void load();
  }, [load]);

  // A read in flight: poll the projection until the job settles, and jump
  // on the frames the drainer broadcasts when it finishes.
  const processing = Boolean(model?.job && PROCESSING.has(model.job.status));
  useEffect(() => {
    if (!processing) return;
    const timer = setInterval(() => void load(), 3000);
    return () => clearInterval(timer);
  }, [processing, load]);
  const { subscribe } = useRuntimeBus();
  useEffect(
    () =>
      subscribe("aftercare_ready", (frame) => {
        const data = frame.data as Record<string, unknown> | undefined;
        if (String(data?.meeting_id ?? "") === meetingId) void load();
      }),
    [subscribe, meetingId, load],
  );

  const replace = useCallback((next: ReviewProposal) => {
    setModel((current) =>
      current
        ? {
            ...current,
            proposals: current.proposals.map((p) => (p.id === next.id ? next : p)),
          }
        : current,
    );
  }, []);

  const focusRow = (id: string | null) => {
    if (!id) return;
    window.requestAnimationFrame(() => {
      rowsRef.current
        ?.querySelector<HTMLElement>(`[data-proposal-id="${CSS.escape(id)}"]`)
        ?.focus();
    });
  };

  const confirm = async (p: ReviewProposal) => {
    if (busyId) return;
    setBusyId(p.id);
    try {
      const result = await apiFetch<Record<string, unknown>>(
        `/api/proposals/${encodeURIComponent(p.id)}/confirm`,
        { method: "POST", json: {} },
      );
      const durable = result.proposal as Record<string, unknown> | undefined;
      if (durable) replace(decodeReviewProposal(durable));
      setReceipt({
        text: `${result.replayed ? "ALREADY KEPT" : "CONFIRMED"} ${nowStamp()}`,
        tone: "success",
      });
      onChanged?.();
      focusRow(p.id);
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusyId(null);
    }
  };

  const dismiss = async (p: ReviewProposal) => {
    if (busyId || !model) return;
    setBusyId(p.id);
    const visible = model.proposals.filter((row) => row.state !== "dismissed");
    const at = visible.findIndex((row) => row.id === p.id);
    const successor = visible[at + 1]?.id ?? visible[at - 1]?.id ?? null;
    try {
      const result = await apiFetch<Record<string, unknown>>(
        `/api/proposals/${encodeURIComponent(p.id)}/dismiss`,
        { method: "POST" },
      );
      const durable = result.proposal as Record<string, unknown> | undefined;
      if (durable) replace(decodeReviewProposal(durable));
      setOpenId((current) => (current === p.id ? null : current));
      setReceipt({ text: `DISMISSED ${nowStamp()}` });
      onChanged?.();
      focusRow(successor);
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusyId(null);
    }
  };

  const edit = async (p: ReviewProposal, body: { text?: string; owner?: string; due?: string }) => {
    if (busyId) return;
    setBusyId(p.id);
    try {
      const result = await apiFetch<Record<string, unknown>>(
        `/api/proposals/${encodeURIComponent(p.id)}/edit`,
        { method: "POST", json: body },
      );
      const durable = result.proposal as Record<string, unknown> | undefined;
      if (durable) {
        const next = decodeReviewProposal(durable);
        replace(next);
        setReceipt({
          text: body.text !== undefined
            ? `EDITED ${nowStamp()}`
            : `SUPPLIED ${nowStamp()} · ${body.owner !== undefined ? "OWNER" : "DUE"}`,
        });
      }
      focusRow(p.id);
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setBusyId(null);
    }
  };

  // Counsel P1-1: ONE call to the canonical bulk verb.  The service keeps
  // only SUPPORTED/LINKED rows with no typed unknown (and none from an
  // earlier revision); the receipt names what was left and why, and those
  // rows stay on the face with their chips.
  const acceptReviewed = async () => {
    if (!model || accepting) return;
    setAccepting(true);
    try {
      const result = await apiFetch<Record<string, unknown>>(
        `/api/meetings/${encodeURIComponent(meetingId)}/proposals/accept-reviewed`,
        { method: "POST", json: {} },
      );
      for (const entry of (result.accepted as Record<string, unknown>[] | undefined) ?? []) {
        const durable = entry.proposal as Record<string, unknown> | undefined;
        if (durable) replace(decodeReviewProposal(durable));
      }
      const accepted = Number(result.accepted_count ?? 0);
      const left = Number(result.left_count ?? 0);
      const parts = [`ACCEPTED ${accepted}`];
      if (left > 0) parts.push(`LEFT ${left}`);
      for (const [key, label] of [["unsupported", "UNSUPPORTED"], ["unknown", "UNKNOWN"], ["prior", "PRIOR REVISION"]] as const) {
        const n = Number(result[key] ?? 0);
        if (n > 0) parts.push(`${label} ${n}`);
      }
      setReceipt({ text: parts.join(" · "), tone: left > 0 ? "warn" : "success" });
      onChanged?.();
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    } finally {
      setAccepting(false);
    }
  };

  const skipRead = async () => {
    try {
      await apiFetch(`/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery/skip`, {
        method: "POST",
      });
      setReceipt({ text: `SKIPPED ${nowStamp()}` });
      onChanged?.();
      void load();
    } catch (reason) {
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    }
  };

  const openProject = () => {
    if (!model?.project) return;
    openSurfaceOr("project-room", "/projects", model.project.id);
  };

  // ── derived ──
  // The head counts the CURRENT revision's decisions; an earlier revision's
  // sit in their own disclosure (counsel P1-2).
  const decided = useMemo(
    () => (model?.proposals ?? []).filter((p) => p.state !== "proposed" && !(model && isPriorRevision(p, model))),
    [model],
  );
  const accepted = decided.filter((p) => p.state === "confirmed").length;
  const dismissed = decided.filter((p) => p.state === "dismissed").length;
  // Counsel P1-2: rows keyed under an EARLIER transcript revision live in
  // the head's PRIOR REVISION disclosure, never in the ledgers, so a
  // re-read after a transcript change doubles nothing silently.
  const prior = (model?.proposals ?? []).filter((p) => model && isPriorRevision(p, model));
  const currentRows = (model?.proposals ?? []).filter((p) => !(model && isPriorRevision(p, model)));
  const open = currentRows.filter((p) => p.state === "proposed");
  const eligible = model ? open.filter((p) => heldReason(p, model) === null) : [];
  const eligibleCount = eligible.length;
  // While a read is in flight the decided rows are the ALREADY KEPT ledger
  // (a retry cannot look like new work); otherwise a confirmed row stays
  // in place with its ACCEPTED chip, and a dismissed one is gone.
  const ledgerRows = processing
    ? open
    : currentRows.filter((p) => p.state !== "dismissed");
  const decisions = ledgerRows.filter((p) => p.kind === "decision");
  const commitments = ledgerRows.filter((p) => p.kind === "action");

  if (error && !model) {
    return <SurfaceState error={error} onRetry={() => void load()} />;
  }
  if (!model) return null;

  const headline = reviewHeadline(model);
  const host = model.job?.modelHost ?? model.proposals[0]?.modelHost ?? null;
  const eg = egressFor(host);
  const modelLabel = model.job?.extractionModel ?? model.proposals[0]?.extractionModel ?? null;

  const headTokens: ReactNode[] = [];
  if (model.project) {
    headTokens.push(
      <span key="project" role="group" aria-label="Project" className="meetings-review-project">
        <Button
          variant="ghost"
          dense
          aria-label={`Open the Project: ${model.project.name || "Project"}`}
          onClick={openProject}
          data-testid="review-project"
        >
          {(model.project.name || "PROJECT").toUpperCase()}
        </Button>
      </span>,
    );
  }
  if (processing && model.job) {
    const reading = model.job.status === "claimed" || model.job.status === "running";
    headTokens.push(
      <StateChip
        key="admitted"
        state={reading ? "working" : "active"}
        label={reading ? "READING" : "ADMITTED"}
      />,
    );
    headTokens.push(
      <span key="job" className="surface-token" data-testid="review-job">
        {`JOB ${jobHandle(model.job.jobId)}`}
      </span>,
    );
    if (model.job.sameJob) {
      headTokens.push(
        <span key="attempt" className="surface-token" data-testid="review-attempt">
          {`ATTEMPT ${model.job.attempt} · SAME JOB`}
        </span>,
      );
    }
  } else {
    headTokens.push(
      <span key="accepted" className="surface-token" data-testid="review-accepted">
        {accepted > 0 ? `ACCEPTED ${accepted}` : "NOTHING ACCEPTED YET"}
      </span>,
    );
    if (dismissed > 0) {
      headTokens.push(
        <span key="dismissed" className="surface-token">{`DISMISSED ${dismissed}`}</span>,
      );
    }
    const extracted = stamp(model.extractedAt);
    if (extracted) {
      headTokens.push(
        <span key="extracted" className="surface-token">{`EXTRACTED ${extracted}`}</span>,
      );
    }
  }

  const coverage = model.coverage;
  const coverageChip: { state: "success" | "working" | "idle" | "failure" | "warning"; label: string } =
    coverage.state === "available"
      ? { state: "success", label: "AVAILABLE" }
      : coverage.state === "reading"
        ? { state: "working", label: "READING" }
        : coverage.state === "queued"
          ? { state: "idle", label: "QUEUED" }
          : coverage.state === "failed"
            ? { state: "failure", label: "FAILED" }
            : { state: "warning", label: "NOT READ" };
  const coverageFact =
    coverage.state === "available"
      ? "READ IN FULL"
      : coverage.turns > 0
        ? `${coverage.turns} ${coverage.turns === 1 ? "TURN" : "TURNS"} NOT YET READ`
        : "NO TRANSCRIPT";
  const observed = stamp(coverage.observedAt);

  const proposalCount = model.proposals.length;
  const steps: PlanStep[] = [
    {
      id: "transcript",
      label: coverage.turns > 0 ? `TRANSCRIPT · ${coverage.turns} TURNS` : "TRANSCRIPT",
      status: coverage.turns > 0 ? "done" : "failed",
    },
    {
      id: "read",
      // A queued successor after a failed attempt is a RETRY, said as a
      // token; the kernel's sentence stays off the face (no prose).
      label: coverage.state === "queued" && model.job?.lastError ? "READ · RETRY" : "READ",
      status:
        coverage.state === "available"
          ? "done"
          : coverage.state === "reading"
            ? "running"
            : coverage.state === "failed"
              ? "failed"
              : "queued",
    },
    {
      id: "proposals",
      label: countLabel("PROPOSALS", proposalCount),
      status: proposalCount > 0 ? "done" : coverage.state === "failed" ? "failed" : "queued",
    },
  ];

  const renderAxes = (p: ReviewProposal) => {
    const support = supportToken(p);
    const acceptance = acceptanceToken(p);
    const span = spanLabel(p, model.startedAt);
    return (
      <span className="meetings-review-axes" data-testid="review-axes">
        {span ? (
          <span className="surface-token" data-chip data-testid="review-span">{span}</span>
        ) : (
          <span className="surface-token" data-chip data-tone="warn" data-testid="review-no-source">
            NO SOURCE
          </span>
        )}
        <span className="surface-token" data-chip data-testid="review-kind">PROPOSAL</span>
        <span data-testid="review-support" data-support={p.support}>
          <StateChip state={support.state} label={support.label} />
        </span>
        <span data-testid="review-acceptance" data-acceptance={p.acceptance}>
          <StateChip state={acceptance.state} label={acceptance.label} />
        </span>
        {p.unknowns.map((u) => (
          <span key={u.type} data-testid="review-unknown" data-unknown={u.type}>
            <StateChip state="warning" label={unknownToken(u)} />
          </span>
        ))}
        {p.kind === "action" && p.owner ? (
          <span className="surface-token" data-chip data-testid="review-owner" data-supplied={p.ownerSupplied ? "" : undefined}>
            {`OWNER · ${p.owner.toUpperCase()}${p.ownerSupplied ? " · SUPPLIED" : ""}`}
          </span>
        ) : null}
        {p.kind === "action" && p.due ? (
          <span className="surface-token" data-chip data-testid="review-due" data-supplied={p.dueSupplied ? "" : undefined}>
            {`DUE · ${p.due.toUpperCase()}${p.dueSupplied ? " · SUPPLIED" : ""}`}
          </span>
        ) : null}
      </span>
    );
  };

  const renderRow = (p: ReviewProposal) => {
    const isOpen = openId === p.id;
    const busy = busyId === p.id;
    const decidedRow = p.state !== "proposed";
    return (
      <li
        key={p.id}
        className="meetings-review-row meetings-review-line"
        data-proposal-id={p.id}
        data-state={p.state}
        data-testid={`review-row-${p.kind}`}
        tabIndex={0}
        aria-label={p.text}
        onKeyDown={(event) => {
          if (event.target !== event.currentTarget) return;
          if (event.key === "Enter" && !decidedRow) {
            event.preventDefault();
            void confirm(p);
          } else if (event.key === "Escape" && isOpen) {
            event.preventDefault();
            setOpenId(null);
          }
        }}
      >
        <div className="meetings-review-sentence" data-testid="review-sentence">
          {decidedRow ? (
            <span className="meetings-review-text">{p.text}</span>
          ) : (
            <EditInPlace
              value={p.text}
              label={p.text}
              multiline
              onCommit={(next) => edit(p, { text: next })}
            />
          )}
        </div>
        {renderAxes(p)}
        <div className="meetings-review-verbs">
          {decidedRow ? (
            <span className="surface-token" data-testid="review-kept">
              {p.state === "confirmed"
                ? `${p.kind === "decision" ? "DECISION RECORD" : "COMMITMENT"} · KEPT ${stamp(p.decidedAt)}`
                : `DISMISSED ${stamp(p.decidedAt)}`}
            </span>
          ) : (
            <>
              <Button
                variant="ghost"
                dense
                aria-expanded={isOpen}
                aria-label={`More: ${p.text}`}
                onClick={() => setOpenId(isOpen ? null : p.id)}
                data-testid="review-more"
              >
                {`${isOpen ? "▾" : "▸"} MORE`}
              </Button>
              <Button
                variant="ghost"
                dense
                loading={busy}
                disabled={Boolean(busyId) && !busy}
                aria-label={`Confirm: ${p.text}`}
                onClick={() => void confirm(p)}
                data-testid="review-confirm"
              >
                Confirm
              </Button>
            </>
          )}
        </div>
        {isOpen && !decidedRow ? (
          <div className="meetings-review-more" role="region" aria-label={`More: ${p.text}`}>
            <Button
              variant="ghost"
              dense
              aria-label={`Edit: ${p.text}`}
              onClick={(event) => {
                const line = (event.currentTarget as HTMLElement).closest(".meetings-review-row");
                line?.querySelector<HTMLElement>(".surface-edit-in-place")?.click();
              }}
              data-testid="review-edit"
            >
              Edit
            </Button>
            <ConfirmVerb
              label="Dismiss"
              confirmLabel="Dismiss?"
              ariaLabel={`Dismiss: ${p.text}`}
              busy={busy}
              onConfirm={() => void dismiss(p)}
            />
            {p.segmentIndex != null ? (
              <Button
                variant="ghost"
                dense
                aria-label={`Open evidence: ${p.text}`}
                onClick={() => onOpenEvidence(p.segmentIndex as number)}
                data-testid="review-evidence"
              >
                Open evidence
              </Button>
            ) : null}
            {p.unknowns.some((u) => u.type === "owner") ? (
              <span className="meetings-review-supply" data-testid="review-supply-owner">
                <span className="surface-caption">OWNER</span>
                <EditInPlace
                  value="Unknown"
                  label={`owner: ${p.text}`}
                  onCommit={(next) => edit(p, { owner: next })}
                />
              </span>
            ) : null}
            {p.unknowns.some((u) => u.type === "due") ? (
              <span className="meetings-review-supply" data-testid="review-supply-due">
                <span className="surface-caption">DUE</span>
                <EditInPlace
                  value="Unknown"
                  label={`due: ${p.text}`}
                  onCommit={(next) => edit(p, { due: next })}
                />
              </span>
            ) : null}
            {p.textEdited && p.originalText ? (
              <span className="surface-token" data-testid="review-was">
                {`WAS · ${p.originalText}`}
              </span>
            ) : null}
          </div>
        ) : null}
      </li>
    );
  };

  const renderKept = (p: ReviewProposal) => (
    <li
      key={p.id}
      className="meetings-review-kept-row meetings-review-line"
      data-proposal-id={p.id}
      tabIndex={0}
      data-testid="review-kept-row"
    >
      <span className="meetings-review-emblem">{p.kind === "decision" ? "DEC" : "CMT"}</span>
      <span className="meetings-review-text">{p.text}</span>
      <StateChip
        state={p.state === "confirmed" ? (p.kind === "decision" ? "success" : "idle") : "idle"}
        label={
          p.state === "confirmed"
            ? p.kind === "decision"
              ? "ACCEPTED"
              : "NOT COMPLETE"
            : "DISMISSED"
        }
      />
      {p.jobAttempt != null ? (
        <span className="surface-token">{`ATTEMPT ${p.jobAttempt}`}</span>
      ) : null}
      <Button
        variant="ghost"
        dense
        aria-label={`Open: ${p.text}`}
        onClick={() => (p.segmentIndex != null ? onOpenEvidence(p.segmentIndex) : onOpenTranscript())}
        data-testid="review-kept-open"
      >
        Open
      </Button>
    </li>
  );

  // Counsel P1-2: the earlier revision's rows, listed in the head.
  const priorDecided = prior.filter((p) => p.state !== "proposed").length;
  const priorOpen = prior.length - priorDecided;
  const priorToken = [
    priorDecided > 0 ? `${priorDecided} DECIDED` : "",
    priorOpen > 0 ? `${priorOpen} OPEN` : "",
  ].filter(Boolean).join(" · ");
  const renderPrior = (p: ReviewProposal) => (
    <li key={p.id} className="meetings-review-kept-row meetings-review-line" data-proposal-id={p.id} tabIndex={0} data-testid="review-prior-row">
      <span className="meetings-review-emblem">{p.kind === "decision" ? "DEC" : "CMT"}</span>
      <span className="meetings-review-text">{p.text}</span>
      <StateChip
        state={p.state === "confirmed" ? "success" : p.state === "dismissed" ? "idle" : "warning"}
        label={p.state === "confirmed" ? "ACCEPTED" : p.state === "dismissed" ? "DISMISSED" : "UNREVIEWED"}
      />
      {p.state === "proposed" ? (
        <Button variant="ghost" dense aria-label={`Confirm: ${p.text}`} loading={busyId === p.id} onClick={() => void confirm(p)} data-testid="review-prior-confirm">
          Confirm
        </Button>
      ) : null}
    </li>
  );

  return (
    <>
      <div className="meetings-review" data-testid="meeting-review" data-processing={processing || undefined}>
        <div className="meetings-review-head">
          <div
            className="surface-display"
            data-accent={headline.accent || undefined}
            data-testid="review-headline"
          >
            {headline.text}
          </div>
          <div className="meetings-review-tokens">
            {headTokens.flatMap((token, i) =>
              i > 0
                ? [<span key={`dot-${i}`} className="meetings-review-dot" aria-hidden="true">{"·"}</span>, token]
                : [token],
            )}
          </div>
          {prior.length > 0 ? (
            <div className="meetings-review-prior" data-testid="review-prior-revision">
              <Disclosure label="PRIOR REVISION" token={priorToken || undefined}>
                <ul className="meetings-review-rows">{prior.map(renderPrior)}</ul>
              </Disclosure>
            </div>
          ) : null}
        </div>

        <section className="meetings-review-coverage" data-testid="review-coverage">
          <span className="surface-caption">
            COVERAGE
            {coverage.read != null ? (
              <span className="meetings-review-caption-value">
                {` ${coverage.read} OF ${coverage.turns} ${coverage.turns === 1 ? "TURN" : "TURNS"}`}
              </span>
            ) : null}
          </span>
          <div className="meetings-review-coverage-row">
            <span className="meetings-review-emblem">MTG</span>
            <span className="meetings-review-text meetings-review-coverage-name">Transcript</span>
            <span className="meetings-review-coverage-facts">
              <span className="surface-token" data-tone={coverage.state === "available" ? undefined : "warn"}>
                {coverageFact}
              </span>
              <StateChip state={coverageChip.state} label={coverageChip.label} />
              {observed ? <span className="surface-token">{`OBSERVED ${observed}`}</span> : null}
              {coverage.state === "failed" && onRunIntelligence ? (
                <Button variant="ghost" dense aria-label="Re-read: Transcript" onClick={onRunIntelligence}>
                  Re-read
                </Button>
              ) : coverage.turns > 0 ? (
                <Button
                  variant="ghost"
                  dense
                  aria-label="Open transcript: Transcript"
                  onClick={onOpenTranscript}
                  data-testid="review-open-transcript"
                >
                  Open transcript
                </Button>
              ) : null}
            </span>
          </div>
        </section>

        {processing ? (
          <ProgressPlan
            steps={steps}
            ariaLabel="Reading the meeting"
            egress={eg.label ? <EgressChip label={eg.label} scope={eg.scope} /> : undefined}
            action={{ label: "Skip", onClick: () => void skipRead() }}
          />
        ) : null}

        {processing && decided.length > 0 ? (
          <div className="meetings-review-kept" data-testid="review-already-kept">
            <Disclosure label="ALREADY KEPT" token={decided.length || undefined} defaultOpen>
              <ul className="meetings-review-rows">{decided.map(renderKept)}</ul>
            </Disclosure>
          </div>
        ) : null}

        {/* The empty state is the display line itself (`Nothing to review`),
            said once; the coverage row and its transcript verb stay. */}
        <div ref={rowsRef} className="meetings-review-ledgers">
          {decisions.length > 0 ? (
            <section className="meetings-review-section" data-testid="review-decisions">
              <span className="surface-caption">{countLabel("DECISIONS", decisions.length)}</span>
              <ul className="meetings-review-rows">{decisions.map(renderRow)}</ul>
            </section>
          ) : null}
          {commitments.length > 0 ? (
            <section className="meetings-review-section" data-testid="review-commitments">
              <span className="surface-caption">{countLabel("COMMITMENTS", commitments.length)}</span>
              <ul className="meetings-review-rows">{commitments.map(renderRow)}</ul>
            </section>
          ) : null}
        </div>
      </div>
      <SurfaceFooter
        egress={
          eg.label ? (
            <>
              <EgressChip label={eg.label} scope={eg.scope} />
              {modelLabel ? <span className="surface-token">{modelLabel.toUpperCase()}</span> : null}
            </>
          ) : (
            <EgressChip />
          )
        }
        receipt={
          <span
            className="surface-footer-receipt-line"
            data-tone={receipt?.tone}
            role="status"
            data-testid="review-receipt"
          >
            {receipt
              ? receipt.text
              : processing && model.job
                ? `ATTEMPT ${model.job.attempt}`
                : ""}
          </span>
        }
        verbs={
          <span className="surface-footer-verbs-group">
            <Button variant="ghost" dense aria-label="Open transcript" onClick={onOpenTranscript}>
              Open transcript
            </Button>
            <ConfirmVerb
              label="Accept reviewed"
              confirmLabel={`${countLabel("Accept", eligibleCount)}?`}
              ariaLabel="Accept reviewed"
              variant="primary"
              armedVariant="primary"
              busy={accepting}
              disabled={eligibleCount === 0 || processing}
              onConfirm={() => void acceptReviewed()}
              data-testid="review-accept-all"
            />
          </span>
        }
      />
    </>
  );
}

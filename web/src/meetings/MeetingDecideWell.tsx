/* PHILO-13-08 (B3): Decide, next to SEND in the meeting record.
 *
 * Two gestures from an open meeting: `Decide`, then type the title and
 * confirm (Enter or `Save`). The title is asked inline (a well, no modal,
 * UX-CANON A.4); nothing is written before he names it, so an abandoned try
 * leaves no `New decision` record. The decision carries the meeting and its
 * project (desk/decide.ts). The receipt stays here: the meeting lists the
 * decisions made from it, and each row opens its own window (B1's grammar).
 *
 * HS-S42: the project is shown and chosen before Save. One linked project is
 * preselected; several wait for his pick; a failed lookup is not "no
 * project". The receipt keeps the record and its filing apart: a filing that
 * failed offers `File to <project>` on the same record, never Save again; an
 * unconfirmed Save keeps Save off for that same title until he edits it.
 *
 * Seats: the Meetings record (MeetingDetail) and the meeting window
 * (MeetingPullout).
 */
import "./meeting-decide.css";
import { useEffect, useRef, useState } from "react";
import { Button } from "../components/signal/Signal";
import { useDesk } from "../desk/store";
import { refOpener } from "../desk/openObject";
import { StringGadget } from "../desk/surface/gadgets";
import { DotWord } from "../desk/surface/kit";
import { SurfaceRow, SurfaceRows, SurfaceSection } from "../desk/surface/Surface";
import {
  DecisionUnconfirmed, decideFromMeeting, decisionsFromMeeting, fileAgain, meetingScope,
  type FilingState, type MeetingScope,
} from "../desk/decide";
import { writeFailureReason } from "../desk/hooks/useWriteReceipt";
import { forgetDraft, keepDraft, keptDraft } from "../desk/deskMemory";

/** W6-G words: a decision's state in sentence case (`to_review` → `To review`). */
const stateWords = (status: string) => {
  const words = String(status ?? "").replace(/_/g, " ").trim().toLowerCase();
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : "";
};

const clock = (d: Date) =>
  `${String(d.getHours()).padStart(2, "0")}:${String(d.getMinutes()).padStart(2, "0")}`;

/** An unfinished title, per meeting: a draft never moves to another meeting
 * (Astra's single pass: a title typed under A posted under B when the
 * Meetings record reused the well). Back on A, A's own draft returns. */
const drafts = new Map<string, string>();

interface DecideWellProps {
  meetingId: string;
  title: string;
  startedAt?: string | null;
  summary?: string | null;
  /** True while the record draws its filled `Run summary`. The face has one
   *  filled primary (surface/contract.md), so `Decide` and `Save` are ghost
   *  then. Without it they are filled, as ratified next to SEND (Phase 13 B3). */
  runSummaryOnFace?: boolean;
  defaultOpen?: boolean;
}

/** One well per meeting: keyed by the meeting, so no state crosses meetings. */
export function MeetingDecideWell(props: DecideWellProps) {
  return <DecideWellFor key={props.meetingId} {...props} />;
}

function DecideWellFor({ meetingId, title, startedAt, summary, runSummaryOnFace, defaultOpen = false }: DecideWellProps) {
  // PHILO-17 (one filled primary per window): with a summary, the meeting's
  // primary is Send (the foot); Decide is a quieter steel verb then.
  const weight = runSummaryOnFace ? "ghost" : String(summary ?? "").trim() ? "secondary" : "primary";
  const decisions = useDesk((s) => s.items.decision);
  const made = decisionsFromMeeting(decisions, meetingId);
  // PHILO-13-07 (B2): the unfinished title is also kept in the workspace
  // document, per meeting, so it returns after a reload and a close.
  const draftKey = `meeting/decide/${meetingId}`;
  const [naming, setNaming] = useState(() => defaultOpen || drafts.has(meetingId) || keptDraft(draftKey) !== null);
  const [draft, setDraftState] = useState(() => drafts.get(meetingId) ?? keptDraft(draftKey) ?? "");
  const setDraft = (next: string) => {
    drafts.set(meetingId, next);
    keepDraft(draftKey, next);
    setDraftState(next);
  };
  const forget = () => {
    drafts.delete(meetingId);
    forgetDraft(draftKey);
    setDraftState("");
  };
  const [busy, setBusy] = useState(false);
  const pending = useRef(false);
  const [refusal, setRefusal] = useState("");
  // HS-S42: the scope is read when the well opens; `choice` undefined is no
  // pick yet, null is "No project", a string is the project he picked.
  const [scope, setScope] = useState<MeetingScope | "loading">("loading");
  const [choice, setChoice] = useState<string | null | undefined>(undefined);
  const [scopeRead, setScopeRead] = useState(0);
  useEffect(() => {
    if (!naming) return;
    let live = true;
    setScope("loading");
    void meetingScope(meetingId).then((next) => {
      if (!live) return;
      setScope(next);
      setChoice((current) => {
        if (current !== undefined) return current;
        if (next.state === "known" && next.projects.length === 1) return next.projects[0].id;
        if (next.state === "none") return null;
        return undefined;
      });
    });
    return () => { live = false; };
  }, [naming, meetingId, scopeRead]);
  // An unconfirmed Save: Save stays off for that same draft until he edits it
  // (a version, so A→B→A is a new draft and the old one is not).
  const editVersion = useRef(0);
  const [unconfirmedAt, setUnconfirmedAt] = useState<number | null>(null);
  const [receipt, setReceipt] = useState<{
    recordId: string; sourceId: string; at: string;
    project: { id: string; name: string } | null; filing: FilingState;
  } | null>(null);
  const [filingBusy, setFilingBusy] = useState(false);

  const abandon = () => {
    setNaming(false);
    forget();
    setRefusal("");
    setUnconfirmedAt(null);
    setChoice(undefined);
  };
  const projects = scope !== "loading" && scope.state === "known" ? scope.projects : [];
  const chosen = choice ? projects.find((p) => p.id === choice) ?? null : null;
  const unconfirmed = unconfirmedAt !== null && unconfirmedAt === editVersion.current;
  const ready = Boolean(draft.trim()) && choice !== undefined && (choice === null || chosen !== null) && !unconfirmed;
  const save = async () => {
    const name = draft.trim();
    if (!name || !ready || pending.current) return;
    pending.current = true;
    const attempt = editVersion.current;
    const project = chosen;
    setBusy(true);
    setRefusal("");
    try {
      const made = await decideFromMeeting({
        title: name, meetingId, meetingTitle: title, startedAt, summary, project,
      });
      setReceipt({ recordId: made.recordId, sourceId: made.sourceId, at: clock(new Date()), project: made.project, filing: made.filing });
      // A late answer never clears a newer draft.
      if ((drafts.get(meetingId) ?? keptDraft(draftKey) ?? "").trim() === name) {
        setNaming(false);
        forget();
        setChoice(undefined);
      }
    } catch (cause) {
      if (cause instanceof DecisionUnconfirmed) setUnconfirmedAt(attempt);
      else setRefusal(writeFailureReason(cause));
      return;
    } finally {
      pending.current = false;
      setBusy(false);
    }
    // The record is known; a failed refresh does not unmake it.
    await useDesk.getState().refresh().catch(() => undefined);
  };
  const fileRecord = async () => {
    if (!receipt?.project || filingBusy) return;
    const { recordId, project } = receipt;
    setFilingBusy(true);
    const filing = await fileAgain(recordId, project.id);
    setReceipt((current) => (current && current.recordId === recordId ? { ...current, filing } : current));
    setFilingBusy(false);
  };
  const projectWords = (p: { id: string; name: string } | null) => (p ? p.name : "No project");

  return (
    <div data-seat="meeting" data-testid="meeting-decide-well" role="group" aria-label={`Decide ${title}`}>
      {made.length ? (
        <SurfaceSection label="Decisions">
          <SurfaceRows>
            {made.map((d) => (
              <SurfaceRow
                key={d.id}
                title={d.title}
                detail={stateWords(d.status)}
                meta={receipt?.sourceId === d.id ? (
                  <span data-testid="decide-receipt">
                    Decided {receipt.at}{receipt.filing === "filed" || receipt.filing === "unfiled" ? ` · ${projectWords(receipt.project)}` : ""}
                  </span>
                ) : undefined}
                onOpen={refOpener(`decision:${d.id}`) ?? undefined}
              />
            ))}
          </SurfaceRows>
        </SurfaceSection>
      ) : null}
      {receipt && receipt.project && !["filed", "unfiled"].includes(receipt.filing) ? (
        <div className="meeting-decide-line" data-testid="decide-filing">
          <DotWord tone={receipt.filing === "other" ? "info" : "warn"} data-testid="decide-filing-state">
            {receipt.filing === "other"
              ? `Decided · ${receipt.project.name} links it as a source, not a member`
              : `Decided · Not filed to ${receipt.project.name}`}
          </DotWord>
          {receipt.filing === "other" ? null : (
            <Button dense variant="ghost" data-testid="decide-file-again" loading={filingBusy} onClick={() => void fileRecord()}>
              File to {receipt.project.name}
            </Button>
          )}
        </div>
      ) : null}
      {naming ? (
        <div className="meeting-decide-line" data-testid="decide-naming">
          <StringGadget
            label="Decision title"
            placeholder="Decision title"
            value={draft}
            autoFocus
            disabled={busy}
            onChange={(next) => { editVersion.current += 1; setDraft(next); }}
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
          <Button dense variant={weight} data-testid="decide-save" loading={busy}
            disabled={!ready} onClick={() => void save()}>
            Save
          </Button>
          <Button dense variant="ghost" data-testid="decide-cancel" disabled={busy} onClick={abandon}>
            Cancel
          </Button>
          {refusal ? (
            <DotWord tone="fail" data-testid="decide-refused" title={refusal}>Could not save the decision · Your title stays here · Try again</DotWord>
          ) : null}
          {unconfirmed ? (
            <>
              <DotWord tone="warn" data-testid="decide-unconfirmed">Save not confirmed · Check the decisions before you save again</DotWord>
              <Button dense variant="ghost" data-testid="decide-check" onClick={() => void useDesk.getState().refresh().catch(() => undefined)}>
                Check
              </Button>
            </>
          ) : null}
        </div>
      ) : null}
      {naming ? (
        <div className="meeting-decide-line" role="group" aria-label="Project" data-testid="decide-scope">
          {scope === "loading" ? (
            <DotWord tone="info" live data-testid="decide-scope-state">Reading projects</DotWord>
          ) : scope.state === "unavailable" ? (
            <>
              <DotWord tone="fail" data-testid="decide-scope-state" title={scope.reason}>Projects not read</DotWord>
              <Button dense variant="ghost" data-testid="decide-scope-retry" onClick={() => setScopeRead((n) => n + 1)}>
                Read again
              </Button>
            </>
          ) : scope.state === "none" ? (
            <DotWord data-testid="decide-scope-state">No linked project</DotWord>
          ) : (
            projects.map((project) => (
              <Button key={project.id} dense variant="chrome" className={`desk-chip quiet${choice === project.id ? " in-zone" : ""}`}
                aria-pressed={choice === project.id} disabled={busy} onClick={() => setChoice(project.id)}>
                {project.name}
              </Button>
            ))
          )}
          {scope !== "loading" && scope.state !== "none" ? (
            <Button dense variant="chrome" className={`desk-chip quiet${choice === null ? " in-zone" : ""}`}
              aria-pressed={choice === null} disabled={busy} onClick={() => setChoice(null)}>
              No project
            </Button>
          ) : null}
        </div>
      ) : (
        <div className="meeting-decide-line">
          <Button dense variant={weight} data-testid="meeting-decide" onClick={() => { setNaming(true); setDraft(""); }}>
            Decide
          </Button>
        </div>
      )}
    </div>
  );
}

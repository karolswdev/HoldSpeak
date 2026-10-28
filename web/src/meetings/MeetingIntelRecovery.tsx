// HS-111-03 — intel recovery is a one-row attention slab (audit §3.5):
// a GadgetGroup, one row of tokens (state · kept · not done) with the
// RETRY/SKIP verbs on the row. The warn reads as the token's color
// only; the transcript well stays the spine.
// HS-201-06 — every word on the row is a plain one (tenet 4).
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../components/signal/Signal";
import { SurfaceState } from "../desk/surface/Surface";
import { GadgetGroup, GadgetRow } from "../desk/surface/gadgets";
import { apiFetch, readableError } from "../lib/api";
import { countToken } from "../desk/surface/count";
import { RefusalToken, RouteDisclosure, RunAttempts, routeTitle } from "./RouteDisclosure";
import { MeetingRunVerb } from "./runSlot";
import { DotWord, ToolGlyph } from "../desk/surface/kit";
import {
  executedReceipt,
  postSummaryRun,
  readLastRefusal,
  readPlannedRoute,
  readRunReceipt,
  routeReady,
  type SummaryRefusal,
} from "./summaryRoute";

type RecoveryFact = {
  label: string;
  detail: string;
};

export type MeetingIntelRecoveryState = {
  meeting_id: string;
  visible: boolean;
  state: string;
  headline: string;
  completed: RecoveryFact[];
  remaining: RecoveryFact;
  job: {
    status: string;
    attempts: number;
    requested_at: string;
    updated_at: string;
  } | null;
  actions: {
    retry: boolean;
    skip: boolean;
  };
  /** HS-201-03's settled contract, served by the recovery read model. */
  planned_route?: unknown;
  run_receipt?: unknown;
  /** Saved analysis needs only local outcome publication; no route leaves. */
  local_publication?: boolean;
};

type RecoveryResponse = {
  success: boolean;
  recovery: MeetingIntelRecoveryState;
};

/** The wire speaks sentences ("3 saved segments"); the slab speaks
 * tokens. Facts that carry no count stay off the line.
 *
 * HS-201-06 (Constitution tenet 4, ASD-STE100): the words are whole and
 * common — `KEPT 3 SEGMENTS · 2 ARTIFACTS`, never the clipped `RETAINED
 * 3 SEG / 2 ART` (audit row 2). A count of zero says nothing at all
 * (UX-CANON A8: no counters of zero), so `RETAINED 0 SEG` is gone. */
function keptToken(completed: RecoveryFact[]): string {
  const tokens: string[] = [];
  for (const fact of completed) {
    const match = /(\d+)\s+saved\s+(segment|artifact)/i.exec(fact.detail);
    if (!match) continue;
    const token = countToken(
      Number(match[1]),
      match[2].toLowerCase() === "segment" ? "segment" : "artifact",
      match[2].toLowerCase() === "segment" ? "segments" : "artifacts",
    );
    if (token) tokens.push(token);
  }
  return tokens.join(" and ");
}

/** Window Program W4 (the words): the state is a dot and one word, never
 *  the wire's caps token (`ERROR` reads `Failed`). */
export function recoveryStateWord(state: string): { word: string; tone: "fail" | "warn" | "idle" } {
  const st = state.trim().toLowerCase();
  if (st === "error" || st === "failed") return { word: "Failed", tone: "fail" };
  if (st === "partial") return { word: "Partial", tone: "warn" };
  if (st === "skipped") return { word: "Skipped", tone: "idle" };
  const word = st.replace(/[_-]+/g, " ");
  return { word: word ? word.charAt(0).toUpperCase() + word.slice(1) : "Not done", tone: "warn" };
}

/** Window Program W4: a list in plain words (`summary, topics and action
 *  items`). */
function listWords(label: string): string {
  const parts = remainingWords(label).toLowerCase().split(/\s*,\s*(?:and\s+)?|\s+and\s+/).filter(Boolean);
  if (parts.length < 2) return parts.join("");
  return `${parts.slice(0, -1).join(", ")} and ${parts[parts.length - 1]}`;
}

/** Window Program W4: one quiet sentence pair: `Kept 2 segments. The
 *  summary, topics and action items did not finish.` */
export function recoverySentence(kept: string, remaining: string): string {
  const keptLine = kept ? `Kept ${kept}.` : "";
  const list = listWords(remaining);
  const rest = list ? `The ${list} did not finish.` : "";
  return [keptLine, rest].filter(Boolean).join(" ");
}

/** HS-201-06: the hub names the remaining work in its own vocabulary
 * ("routed meeting intelligence"). The face says it in plain words: a
 * summary is a summary, and "routed artifacts" is dropped — the user
 * never asked for a route (audit rows 3 and 4). */
function remainingWords(label: string): string {
  return label
    .replace(/,?\s*and\s+routed\s+artifacts/i, "")
    .replace(/routed\s+meeting\s+intelligence/i, "artifacts")
    .replace(/remaining\s+meeting\s+intelligence/i, "the rest of the summary")
    .replace(/intelligence/gi, "summary")
    .trim()
    .toUpperCase();
}

/** HS-201-06 (audit row 5): the hub's refusal is one sentence and the
 * face adds a second. Without a full stop between them they read as one
 * run-on line. End the first sentence before the second begins. */
function twoSentences(first: string, second: string): string {
  const head = first.trim();
  const closed = /[.!?]$/.test(head) ? head : `${head}.`;
  return `${closed} ${second}`;
}

export function MeetingIntelRecovery({
  meetingId,
  onChanged,
  revision = 0,
}: {
  meetingId: string;
  revision?: number;
  onChanged?(recovery: MeetingIntelRecoveryState): void | Promise<void>;
}) {
  const [recovery, setRecovery] = useState<MeetingIntelRecoveryState | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<"retry" | "skip" | "">("");
  const [error, setError] = useState("");
  // HS-201-04: a refused run is a REFUSAL with its plain reason, not an
  // error surface. It never replaces the receipt of an earlier real run.
  const [refusal, setRefusal] = useState<SummaryRefusal | null>(null);
  const readSequence = useRef(0);
  const currentMeeting = useRef(meetingId);
  currentMeeting.current = meetingId;
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => { mounted.current = false; };
  }, []);
  useEffect(() => { setBusy(""); }, [meetingId]);

  const load = useCallback(async () => {
    if (!meetingId) return;
    const sequence = ++readSequence.current;
    setLoading(true);
    setError("");
    try {
      const fresh = await apiFetch<MeetingIntelRecoveryState>(
          `/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery`,
        );
      if (sequence === readSequence.current) setRecovery(fresh);
    } catch (reason) {
      if (sequence !== readSequence.current) return;
      setError(
        twoSentences(
          readableError(reason),
          "The Meeting and completed work remain saved.",
        ),
      );
    } finally {
      if (sequence === readSequence.current) setLoading(false);
    }
  }, [meetingId]);

  useEffect(() => {
    void load();
    return () => { readSequence.current += 1; };
  }, [load, revision]);

  // HS-201-04 (Article III, the point of decision): the route the next run
  // WILL use, and the destinations the last run DID contact. Both come from
  // the recovery read model; neither is composed from configuration. The
  // refusal's fresh route wins while a refusal stands.
  const route = refusal?.route ?? readPlannedRoute(recovery);
  // The last run that actually contacted something wins over a bare
  // refusal receipt (pickRunReceipt): a refusal never erases the hosts.
  const receipt = executedReceipt(
    meetingId,
    refusal?.receipt,
    readRunReceipt(recovery),
    readRunReceipt(recovery?.job),
  );
  const localPublication = Boolean(recovery?.local_publication);
  const canRun = localPublication || routeReady(route);

  const choose = async (action: "retry" | "skip") => {
    const forMeeting = meetingId;
    const mine = () => mounted.current && currentMeeting.current === forMeeting;
    const accept = async (fresh: MeetingIntelRecoveryState) => {
      if (!mine()) return;
      readSequence.current += 1;
      setRecovery(fresh);
      await onChanged?.(fresh);
    };
    setBusy(action);
    setError("");
    setRefusal(null);
    readSequence.current += 1;
    const path = `/api/meetings/${encodeURIComponent(meetingId)}/intel-recovery/${action}`;
    try {
      // HS-201-04: Retry starts a summary run, so it carries the disclosed
      // selection hash (lane A's interlock). Skip starts no run.
      if (action === "retry") {
        if (localPublication) {
          const result = await apiFetch<RecoveryResponse>(path, { method: "POST" });
          await accept(result.recovery);
          return;
        }
        const outcome = await postSummaryRun<RecoveryResponse>(path, route);
        if (!mine()) return;
        if (!outcome.ok) {
          readSequence.current += 1;
          setRefusal(outcome.refusal);
          await load();
          return;
        }
        await accept(outcome.result.recovery);
        return;
      }
      const result = await apiFetch<RecoveryResponse>(path, { method: "POST" });
      await accept(result.recovery);
    } catch (reason) {
      if (!mine()) return;
      setError(
        twoSentences(
          readableError(reason),
          "The Meeting and completed work remain saved.",
        ),
      );
    } finally {
      if (mine()) setBusy("");
    }
  };

  if (loading && recovery === null) return null;
  if (!error && !recovery?.visible) return null;
  // HS-172: QUEUED and RUNNING states are shown in the header chip now;
  // the legacy panel (prose REMAINING + clipped text) is suppressed.
  const st = recovery?.state?.toLowerCase() ?? "";
  if (st === "queued" || st === "running" || st === "pending") return null;

  const kept = recovery ? keptToken(recovery.completed) : "";
  const running = recovery?.state === "running";
  const stateWord = recoveryStateWord(recovery?.state ?? "");
  return (
    <section
      className="meeting-intel-recovery"
      aria-label="Meeting intelligence recovery"
    >
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {/* HS-201-06: the group is the meeting SUMMARY. "Intelligence" is
          the wire's word for it, and a summary is what the user asked
          for (Constitution tenet 4, audit row 4). */}
      {recovery?.visible ? (
        <GadgetGroup label={localPublication ? "Outcomes" : "Summary"}>
          {/* HS-201-04 (audit defects 6 and 7): the facts span the row and
              the verbs sit at its trailing edge, so nothing is pushed under
              the window footer and no fact is clipped into a column of
              seven characters. */}
          <GadgetRow
            label={
              <span className="meeting-intel-recovery-facts">
                <DotWord tone={running ? "idle" : stateWord.tone} data-testid="recovery-state">
                  {stateWord.word}
                </DotWord>
                <span className="gadget-fact" title={recovery.remaining.detail} data-testid="recovery-sentence">
                  {recoverySentence(kept, recovery.remaining.label)}
                </span>
                {/* Article III: the destinations of the LAST run, then the
                    route the NEXT run will use. */}
                <RunAttempts receipt={receipt} testId="recovery-attempts" />
                {recovery.actions.retry && !localPublication ? (
                  <RouteDisclosure route={route} testId="recovery-route" />
                ) : null}
                <RefusalToken
                  refusal={refusal}
                  durable={readLastRefusal(recovery)}
                  testId="recovery-refusal"
                />
              </span>
            }
          >
            {/* UX-CANON A.11: a verb that cannot run is withheld, and the
                reason stands in its place (RouteDisclosure says it). */}
            {/* Window grammar: Retry and Skip sit in the meeting window's toolbar. */}
            <MeetingRunVerb>
            {recovery.actions.retry && canRun ? (
              <Button
                dense
                variant="primary"
                loading={busy === "retry"}
                disabled={Boolean(busy)}
                title={localPublication ? undefined : routeTitle(route)}
                onClick={() => void choose("retry")}
              >
                <ToolGlyph kind="retry" />
                Retry
              </Button>
            ) : null}
            {recovery.actions.skip ? (
              <Button
                dense
                variant="ghost"
                loading={busy === "skip"}
                disabled={Boolean(busy)}
                onClick={() => void choose("skip")}
              >
                Skip
              </Button>
            ) : null}
            </MeetingRunVerb>
          </GadgetRow>
        </GadgetGroup>
      ) : null}
    </section>
  );
}

// PHILO-17 (owner 2026-10-10, "A meeting opens in one window") — the
// summary run, shared by the Meetings list (a row's Run summary) and the
// meeting's own window (the record's Run summary). Moved whole from
// HistoryCore: the receipt (QUEUED → RAN, bound to its run), the running
// row, the hub's refusal, and the poll.
import { useCallback, useRef, useState, type Dispatch, type SetStateAction } from "react";
import { apiFetch, readableError } from "../../../lib/api";
import { postSummaryRun, type PlannedRoute, type SummaryRefusal } from "../../../meetings/summaryRoute";
import type { MeetingDetailResponse } from "../core-types";
import { clockTime, finishedRunReceipt, type Receipt, type RunIdentity } from "./helpers";

export interface SummaryRun {
  receipt: Receipt | null;
  setReceipt: Dispatch<SetStateAction<Receipt | null>>;
  runningId: string | null;
  runRefusal: { meetingId: string; refusal: SummaryRefusal } | null;
  /** PHILO-15-07 (B15): this run's receipt (and only this run's) follows
   *  it to the final state. */
  settleRun(run: RunIdentity, state: string, at?: string): void;
  run(meetingId: string, displayed?: PlannedRoute | null): Promise<void>;
}

/** `routeFor` names the route a meeting's row disclosed when the face
 *  passes none; `refresh` re-reads the face after the run moves. */
export function useSummaryRun(
  routeFor: (meetingId: string) => PlannedRoute | null,
  refresh: () => void | Promise<void>,
): SummaryRun {
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [runningId, setRunningId] = useState<string | null>(null);
  // HS-201-04: the hub's 409 refusal, kept as a refusal (code + plain
  // reason + the fresh route), never as an error surface.
  const [runRefusal, setRunRefusal] = useState<
    { meetingId: string; refusal: SummaryRefusal } | null
  >(null);
  const routeRef = useRef(routeFor);
  routeRef.current = routeFor;
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;
  const refreshFace = () => void refreshRef.current();

  // PHILO-15-07 (B15): a `QUEUED hh:mm` receipt is bound to its run
  // (meeting id + job id, Astra r1 on #982). It turns into `RAN · hh:mm` only
  // for that run. Astra iteration 2: the settled receipt KEEPS its run
  // identity, so the Review wing (which shows only a receipt bound to its
  // meeting) sees the completion too.
  const settleRun = useCallback((run: RunIdentity, state: string, at?: string) => {
    setReceipt((current) =>
      current?.run &&
      current.run.meetingId === run.meetingId &&
      current.run.jobId === run.jobId
        ? { ...finishedRunReceipt(state, at || new Date().toISOString()), run: current.run }
        : current,
    );
  }, []);

  const run = useCallback(async (meetingId: string, displayed?: PlannedRoute | null) => {
    setRunningId(meetingId);
    setRunRefusal(null);
    // HS-201-04 (lane A's interlock): the route the face DISCLOSED is the
    // route the request binds — the same object, never a second lookup.
    const route = displayed ?? routeRef.current(meetingId);
    try {
      const outcome = await postSummaryRun<{
        jobId: string;
        state: string;
        host: string;
        drainer?: string;
      }>(
        `/api/meetings/${encodeURIComponent(meetingId)}/intelligence/run`,
        route,
      );
      if (!outcome.ok) {
        // A refusal is a refusal, with its plain reason — never an error
        // surface, and it never erases the receipt of an earlier real run.
        setRunningId(null);
        setRunRefusal({ meetingId, refusal: outcome.refusal });
        setReceipt({
          text: `REFUSED · ${outcome.refusal.plainReason}`,
          tone: "danger",
        });
        refreshFace();
        return;
      }
      const result = outcome.result;
      const identity: RunIdentity = { meetingId, jobId: String(result.jobId ?? meetingId) };
      setReceipt({ text: `QUEUED ${clockTime(new Date().toISOString())}`, run: identity });
      // HS-200-42: when the route says no drainer exists, polling every 3s for
      // 120s is a lie told forty times — nothing in the hub will move this job.
      // Stop the poll and refresh the row once. `runningId` is deliberately
      // LEFT SET: where the run egresses is a fact the click established.
      if (result.drainer !== "running") {
        refreshFace();
        return;
      }
      // Poll for completion
      const poll = setInterval(async () => {
        try {
          const statusResp = await apiFetch<MeetingDetailResponse>(
            `/api/meetings/${encodeURIComponent(meetingId)}`,
          );
          const intelStatus = statusResp?.intel_status;
          const state = typeof intelStatus === "object" && intelStatus !== null
            ? String((intelStatus as Record<string, unknown>).state ?? "")
            : String(intelStatus ?? "");
          if (state !== "queued" && state !== "running" && state !== "pending") {
            clearInterval(poll);
            setRunningId(null);
            settleRun(identity, state);
            refreshFace();
          }
        } catch {
          clearInterval(poll);
          setRunningId(null);
        }
      }, 3000);
      // Safety timeout
      setTimeout(() => {
        clearInterval(poll);
        setRunningId((current) => {
          if (current === meetingId) {
            refreshFace();
            return null;
          }
          return current;
        });
      }, 120_000);
    } catch (reason) {
      setRunningId(null);
      setReceipt({ text: `REFUSED · ${readableError(reason)}`, tone: "danger" });
    }
  }, [settleRun]);

  return { receipt, setReceipt, runningId, runRefusal, settleRun, run };
}

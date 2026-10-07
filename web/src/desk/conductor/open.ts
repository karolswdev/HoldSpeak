/** PHILO-14 C4 — what a Conductor member opens, and its verbs.
 *
 *  Open on a live or stale agent = its lane window (`launch:<id>` in the one
 *  open grammar, `openObject.ts`); a session no launch holds opens its
 *  session window (`coder:<key>`). Open on a ready agent = its Get Info.
 *  Answer opens the ask well; Stop goes through the lane (its ARM and its
 *  kill route), so the receipt lands in the lane window. */
import { apiFetch } from "../../lib/api";
import { refOpener } from "../openObject";
import type { LaneReceipt } from "../lane/laneStore";
import type { LaneControl, LaneWire, NotRead } from "../lane/laneWire";
import { openAgentLane, openCoderSession } from "../shell";
import type { ConductorMember } from "./members";
import { useConductor } from "./store";

export function openMember(member: ConductorMember): void {
  if (member.role === "ready") {
    useConductor.getState().openInfo(member);
    return;
  }
  refOpener(member.ref)?.();
}

/** The agent asks (or holds a call): Answer opens its ask well. */
export function answers(member: ConductorMember): boolean {
  return member.role === "live" && (member.live === "ask" || member.live === "held") && Boolean(member.sessionKey);
}

export function answerMember(member: ConductorMember): void {
  if (!member.sessionKey) return;
  if (member.launchId) openAgentLane(member.launchId, { sessionKey: member.sessionKey, answer: true });
  else openCoderSession(member.sessionKey, { answer: true });
}

/** Stop is for a launched agent with a session (the lane's own kill). */
export function stops(member: ConductorMember): boolean {
  return member.role === "live" && Boolean(member.launchId && member.sessionKey);
}

/** Stop the pressed member's launch. Its launch id and session key are taken
 *  at the press and passed to the lane store's bound path
 *  (`stopLaunch`): no await re-reads the lane that is open now, so opening
 *  another agent meanwhile never redirects the kill (Astra r1 on #947, P1).
 *  The receipt lands on the member (and on its lane, when that is open). */
export async function stopMember(member: ConductorMember): Promise<LaneReceipt | null> {
  const launchId = member.launchId;
  const pressed = member.sessionKey;
  if (!launchId || !pressed) return null;
  let control: LaneControl | NotRead | null = null;
  let sessionKey = pressed;
  try {
    // This launch's own lane (its control and its registered session).
    const lane = await apiFetch<Partial<LaneWire> | null>(
      `/api/agent/launches/${encodeURIComponent(launchId)}/lane?after=0&limit=1`,
    );
    control = (lane?.control as LaneControl | NotRead | undefined) ?? null;
    if (lane?.launch?.session_key) sessionKey = String(lane.launch.session_key);
  } catch {
    // Unread control: the hub's kill route answers for the ARM itself.
  }
  const { useLane } = await import("../lane/laneStore");
  const receipt = await useLane.getState().stopLaunch({ launchId, sessionKey, control });
  useConductor.getState().setStop(member.ref, receipt);
  return receipt;
}

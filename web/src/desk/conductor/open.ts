/** PHILO-14 C4 — what a Conductor member opens, and its verbs.
 *
 *  Open on a live or stale agent = its lane window (`launch:<id>` in the one
 *  open grammar, `openObject.ts`); a session no launch holds opens its
 *  session window (`coder:<key>`). Open on a ready agent = its Get Info.
 *  Answer opens the ask well; Stop goes through the lane (its ARM and its
 *  kill route), so the receipt lands in the lane window. */
import { refOpener } from "../openObject";
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

export async function stopMember(member: ConductorMember): Promise<boolean> {
  if (!member.launchId) return false;
  const { useLane } = await import("../lane/laneStore");
  const lane = useLane.getState();
  lane.open(member.launchId, { sessionKey: member.sessionKey ?? null });
  await useLane.getState().load();
  return useLane.getState().stop();
}

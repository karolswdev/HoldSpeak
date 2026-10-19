/** Parked (Betterment AG8, 2026-10-18): one desk icon per live agent on
 *  the floor (screen/compose.ts). The Agents list is the fleet now: the
 *  Agents drawer, its Dock tile (worst-state lamp and the count that needs
 *  him) and Needs you carry the agents. Nothing imports this file. */
import type { CoderSessionRow } from "../../agentFlights";
import { agentName, agentState, type ScreenObject } from "../../screen/compose";
import type { ObjectTone } from "../../surface";

const AGENT_LAMP: Record<"ask" | "idle" | "done" | "work" | "pr", ObjectTone> = { ask: "ask", idle: "info", done: "ok", work: "info", pr: "ok" };

function agentWordFor(row: CoderSessionRow): string {
  const state = agentState(row);
  if (state === "ask") return "ASKS";
  if (state === "idle") return "IDLE";
  if (state === "done") return row.flight?.isNew ? "NEW" : "DONE";
  if (state === "pr") return row.flight?.pr?.number ? `PR #${row.flight.pr.number}` : "PR OPEN";
  return "WORKS";
}

export function floorAgents(live: readonly CoderSessionRow[], sprites: (kind: string, id: string, agent?: string) => object): ScreenObject[] {
  return live.map((row) => {
    const state = agentState(row);
    return {
      key: `coder:${row.key}`,
      role: "agent",
      kind: "coder",
      kindWord: "AGENT",
      name: agentName(row),
      ...sprites("coder", row.key, row.agent),
      lamp: { tone: AGENT_LAMP[state], label: agentWordFor(row) },
      target: { type: "agent", key: row.key },
    } as ScreenObject;
  });
}

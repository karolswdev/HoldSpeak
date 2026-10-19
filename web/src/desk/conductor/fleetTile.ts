/** Betterment AG8: the Agents tile on the Dock carries the fleet's worst
 *  state (a lamp), a mark for New and the count of agents that need him
 *  (agents/DESIGN.md §4, "Where agents show outside Agents"). It reads the
 *  one flights store every agent face reads (`agentFlights.ts`). */
import { useMemo } from "react";
import { useAgentFlights, useAgentFlightsLive } from "../agentFlights";
import { conductorMembers, fleetCounts, fleetTile } from "./members";

export interface AgentsTile {
  lamp: "ask" | "new" | "work" | null;
  needYou: number;
  fresh: boolean;
  /** `2 need you, 1 new, 3 working` for the tile's name; "" with none. */
  words: string;
}

export function agentsTileOf(sessions: Parameters<typeof conductorMembers>[0]["sessions"],
  flights: Parameters<typeof conductorMembers>[0]["flights"]): AgentsTile {
  const members = conductorMembers({ detect: null, sessions, flights, launchedAt: {} });
  const counts = fleetCounts(members);
  const words = [
    counts.needYou ? `${counts.needYou} ${counts.needYou === 1 ? "needs" : "need"} you` : "",
    counts.fresh ? `${counts.fresh} new` : "",
    counts.working ? `${counts.working} working` : "",
  ].filter(Boolean).join(", ");
  return { ...fleetTile(members), words };
}

export function useAgentsTile(): AgentsTile {
  useAgentFlightsLive();
  const sessions = useAgentFlights((s) => s.sessions);
  const flights = useAgentFlights((s) => s.flights);
  return useMemo(() => agentsTileOf(sessions, flights), [sessions, flights]);
}

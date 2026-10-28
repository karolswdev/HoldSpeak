/** Betterment AG8 gaps: a desk object's "Agent" line (agents/DESIGN.md §4,
 *  "Where agents show outside Agents"). While an agent works on the object
 *  (a note, an action, a decision), its window says so in one press:
 *  "Claude Code · Working", "Claude Code · Done · New". The press opens the
 *  agent's window. Nothing shows when no agent holds the object. */
import { Button } from "../../components/signal/Signal";
import { flightForItem, useAgentFlights, type AgentFlight } from "../agentFlights";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { openAgentLane } from "../shell";
import { launchLive, liveWord } from "../conductor/members";

/** The flight's state in his words: the Agents row's own word (W4 AGENT 2:
 *  one source, `members.launchLive` + `liveWord`, on every face). */
export function agentLineWord(flight: AgentFlight): string {
  if (flight.state === "merged") return "Merged";
  return liveWord(launchLive(flight), {
    isNew: flight.isNew,
    pr: flight.pr?.number ?? null,
    phase: flight.state === "starting" ? "starting" : flight.state === "resuming" ? "resuming" : null,
  }).word;
}

export function AgentLine({ objectRef }: { objectRef: string | null | undefined }) {
  // The desk keeps the flights store live (ChairHome); a window only reads it.
  const flights = useAgentFlights((s) => s.flights);
  const flight = objectRef ? flightForItem(flights, { ref: objectRef }) : null;
  if (!flight || !flight.launchId) return null;
  const launchId = flight.launchId;
  const words = `${AGENT_NAME[flight.agent as AgentId] ?? flight.agent} · ${agentLineWord(flight)}`;
  return (
    <Button
      dense
      variant="ghost"
      className="desk-agent-line"
      aria-label={`Agent: ${words}`}
      data-testid="desk-agent-line"
      onClick={() => openAgentLane(launchId)}
    >
      {words}
    </Button>
  );
}

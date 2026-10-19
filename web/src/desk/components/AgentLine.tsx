/** Betterment AG8 gaps: a desk object's "Agent" line (agents/DESIGN.md §4,
 *  "Where agents show outside Agents"). While an agent works on the object
 *  (a note, an action, a decision), its window says so in one press:
 *  "Claude Code · Working", "Claude Code · Done · New". The press opens the
 *  agent's window. Nothing shows when no agent holds the object. */
import { Button } from "../../components/signal/Signal";
import { flightForItem, useAgentFlights, type AgentFlight } from "../agentFlights";
import { AGENT_NAME, type AgentId } from "../firstrun/agentsStep";
import { openAgentLane } from "../shell";

/** The flight's state in his words (the Agents row's own words). */
export function agentLineWord(flight: AgentFlight): string {
  switch (flight.state) {
    case "waiting":
      return flight.turnEnd === "idle" ? "Quiet" : flight.screen?.wait === "approve" ? "Wants to run" : "Asks you";
    case "done":
      return flight.isNew ? "Done · New" : "Quiet";
    case "pr_open":
      return flight.pr?.number ? `PR #${flight.pr.number} open` : "PR open";
    case "queued":
      return "Waits for a free agent";
    case "starting":
      return "Starting";
    case "resuming":
      return "Resuming";
    case "no_signal":
      return "No signal";
    case "merged":
      return "Merged";
    default:
      return "Working";
  }
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

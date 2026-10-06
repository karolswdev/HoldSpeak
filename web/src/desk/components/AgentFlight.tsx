/* Conductor F2 (ratified boards K4a, K4b): the item wears its agent where it
 * lives. One chip (`CLAUDE CODE · WAITING`, `CODEX · WORKING`, `PR #412 ·
 * OPEN`) and the flight's verb: `Session` while the agent runs, the
 * `GITHUB.COM` egress chip and `Open PR` once a PR exists. The Door row and
 * the Room's OPEN HERE row draw the same two parts. */
import "./agent-flight.css";
import { Button } from "../../components/signal/Signal";
import { EgressChip, StateChip } from "../surface";
import { openCoderSession } from "../shell";
import { flightLabel, flightTone, type AgentFlight } from "../agentFlights";

export function FlightChip({ flight }: { flight: AgentFlight | null }) {
  if (!flight) return null;
  const label = flightLabel(flight);
  if (!label) return null;
  return <StateChip state={flightTone(flight.state)} label={label} data-testid="flight-chip" />;
}

export function FlightVerbs({ flight, title }: { flight: AgentFlight | null; title: string }) {
  if (!flight || !flightLabel(flight)) return null;
  if ((flight.state === "pr_open" || flight.state === "merged") && flight.pr?.url) {
    const url = flight.pr.url;
    return (
      <span className="desk-flight-verbs">
        <EgressChip label="GITHUB.COM" scope="cloud" />
        <Button
          dense
          variant="ghost"
          aria-label={`Open PR #${flight.pr.number ?? ""}: ${title}`}
          data-testid="flight-open-pr"
          onClick={() => window.open(url, "_blank", "noopener")}
        >
          Open PR
        </Button>
      </span>
    );
  }
  const key = flight.sessionKey;
  if (!key) return null;
  return (
    <Button
      dense
      variant="ghost"
      aria-label={`Open session: ${title}`}
      data-testid="flight-session"
      onClick={() => openCoderSession(key)}
    >
      Session
    </Button>
  );
}

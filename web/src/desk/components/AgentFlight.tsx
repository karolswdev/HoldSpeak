/* Conductor F2 (ratified boards K4a, K4b): the item wears its agent where it
 * lives. One dot and word (`Claude Code · Waiting`, `Codex · Working`, `PR #412 ·
 * Open`) and the flight's verb: `Session` while the agent runs, and
 * `Open PR` once a PR exists (no host chip: owner ruling 2026-10-25; the
 * verb's hover title names the address). The Door row and
 * the Room's OPEN HERE row draw the same two parts. */
import "./agent-flight.css";
import { Button } from "../../components/signal/Signal";
import { DotWord } from "../surface";
import { stateWords } from "../surface/objects/NeedsRow";
import { openCoderSession } from "../shell";
import { flightLabel, flightTone, type AgentFlight } from "../agentFlights";

/** The agents' own names (the flight vocabulary says them in caps). */
const AGENT_FACE: Record<string, string> = { "CLAUDE CODE": "Claude Code", CODEX: "Codex", PI: "pi" };
const FLIGHT_DOT = { working: "info", warning: "warn", active: "ask", success: "ok", idle: "idle" } as const;

/** W6-J words: the flight's state in sentence case (`Claude Code · Waiting`,
 *  `PR #412 · Open`); the caps vocabulary of `flightLabel` stays as it is. */
export function flightWords(flight: AgentFlight): string | null {
  const label = flightLabel(flight);
  if (!label) return null;
  const [head, ...rest] = label.split(" · ");
  const name = AGENT_FACE[head];
  return name ? [name, stateWords(rest.join(" · "))].filter(Boolean).join(" · ") : stateWords(label);
}

export function FlightChip({ flight }: { flight: AgentFlight | null }) {
  if (!flight) return null;
  const words = flightWords(flight);
  if (!words) return null;
  return <DotWord tone={FLIGHT_DOT[flightTone(flight.state)]} data-testid="flight-chip">{words}</DotWord>;
}

export function FlightVerbs({ flight, title }: { flight: AgentFlight | null; title: string }) {
  if (!flight || !flightLabel(flight)) return null;
  if ((flight.state === "pr_open" || flight.state === "merged") && flight.pr?.url) {
    const url = flight.pr.url;
    return (
      <span className="desk-flight-verbs">
        <Button
          dense
          variant="ghost"
          aria-label={`Open PR #${flight.pr.number ?? ""}: ${title}`}
          data-testid="flight-open-pr"
          title={url}
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

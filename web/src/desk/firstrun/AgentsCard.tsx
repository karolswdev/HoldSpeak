/* First run — the Agents card (the Conductor canvas K1a/K1b/K1c, ratified
 * 2026-10-06). One row per coding agent (Claude Code, Codex) with the lamps
 * INSTALLED / SIGNED IN / HOOKS, a tmux row (a TOOL, not counted as an agent), and one verb: Install hooks
 * (THIS DEVICE: the press writes the agents' settings files on this Mac).
 * Done folds the card to its receipt. Not installed: tokens + Copy install
 * per agent, and Check again. */
import { Button } from "../../components/signal/Signal";
import { EgressChip, StateChip, SurfaceLedgerRow } from "../surface";
import { countToken } from "../surface/count";
import { useCopyReceipt } from "../hooks/useCopyReceipt";
import { Card } from "./Card";
import {
  AGENT_GLYPH,
  AGENT_INSTALL,
  AGENT_NAME,
  type AgentRow,
  type AgentsStep,
} from "./agentsStep";

/** A wire code as words for a token (never raw snake_case on a face). */
export function codeWords(code: string): string {
  return code.replace(/_/g, " ").toUpperCase();
}

function Lamp({ on, label }: { on: boolean; label: string }) {
  return <StateChip state={on ? "success" : "idle"} label={label} icon={on ? "●" : "○"} />;
}

/** SIGNED IN is `yes` only from a credential file; else the hub cannot say
 * (a Keychain token, a keyring): its own token, never a false NO. */
function SignedIn({ row }: { row: AgentRow }) {
  return row.signed_in === "yes" ? (
    <Lamp on label="SIGNED IN" />
  ) : (
    <StateChip state="idle" label="SIGN-IN UNKNOWN" icon="?" />
  );
}

function Hooks({ row }: { row: AgentRow }) {
  switch (row.hooks) {
    case "installed":
      return <Lamp on label="HOOKS" />;
    case "partial":
      return <StateChip state="warning" label="HOOKS PARTIAL" />;
    case "broken":
      return <StateChip state="failure" label="HOOKS BROKEN" />;
    case "unreadable":
      return <StateChip state="failure" label="HOOKS UNREADABLE" />;
    case "not_read":
      // A rig hub did not read them: unknown, never a false "no hooks".
      return <StateChip state="idle" label="HOOKS UNKNOWN" icon="?" />;
    default:
      return <Lamp on={false} label="HOOKS" />;
  }
}

function versionToken(tool: string, version?: string | null): string {
  return version ? `${tool} ${version}`.toUpperCase() : tool.toUpperCase();
}

function AgentLedgerRow({ row, onCopy }: { row: AgentRow; onCopy: (text: string) => void }) {
  return (
    <SurfaceLedgerRow
      lead={<span className="concierge-group-glyph">{AGENT_GLYPH[row.id]}</span>}
      primary={<span className="concierge-group-name">{AGENT_NAME[row.id]}</span>}
      cells={
        <span className="firstrun-agent-cells" data-testid="firstrun-agent-row" data-agent={row.id}>
          {row.installed ? (
            <>
              <span className="surface-token" data-chip>{versionToken(row.id, row.version)}</span>
              <Lamp on label="INSTALLED" />
              <SignedIn row={row} />
              <Hooks row={row} />
            </>
          ) : (
            <>
              <span className="surface-token" data-chip>{row.id.toUpperCase()} NOT INSTALLED</span>
              <Button
                dense
                variant="secondary"
                aria-label={`Copy install: ${AGENT_NAME[row.id]}`}
                onClick={() => onCopy(AGENT_INSTALL[row.id])}
              >
                Copy install
              </Button>
            </>
          )}
        </span>
      }
      expands={false}
      wrap
    />
  );
}

export function AgentsCard({ step, lit }: { step: AgentsStep; lit: boolean }) {
  const { copy, receipt } = useCopyReceipt();
  const tmux = step.tmux;
  const installed = step.installed.length;
  const missingAny = step.rows.some((row) => !row.installed) || (tmux !== null && !tmux.installed);
  if (step.done) {
    return (
      <Card
        title="Agents"
        testId="firstrun-agents"
        selected
        state={<StateChip state="success" label={`${countToken(installed, "AGENT")} READY`} icon="●" />}
      >
        <span className="firstrun-tokens" data-testid="firstrun-agents-receipt">
          {step.installed.map((row) => (
            <span key={row.id} className="surface-token" data-chip>
              {AGENT_NAME[row.id].toUpperCase()} · HOOKS IN
            </span>
          ))}
          {tmux?.installed ? (
            <span className="surface-token" data-chip>{versionToken("tmux", tmux.version)}</span>
          ) : null}
        </span>
      </Card>
    );
  }
  return (
    <Card
      title="Agents"
      testId="firstrun-agents"
      lit={lit}
      state={
        installed > 0 ? (
          // PHILO-15 11 (B17): count the agents only; tmux is a tool, labelled so.
          <StateChip state="success" label={`${countToken(installed, "AGENT")} FOUND`} icon="●" />
        ) : step.loaded && !step.unread ? (
          <StateChip state="idle" label="NO AGENT FOUND" />
        ) : null
      }
    >
      {step.unread ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="unreachable" label="CAN'T CHECK" />
          <span className="surface-token" data-testid="firstrun-agents-unread">{step.unread}</span>
          <Button dense variant="secondary" onClick={() => void step.read()}>
            Try again
          </Button>
        </div>
      ) : null}
      {step.rows.length ? (
        <ul className="concierge-found-list firstrun-ledger" aria-label="Found agents">
          {step.rows.map((row) => (
            <AgentLedgerRow key={row.id} row={row} onCopy={(text) => void copy(text)} />
          ))}
          {tmux ? (
            <SurfaceLedgerRow
              lead={<span className="concierge-group-glyph">TM</span>}
              primary={<span className="concierge-group-name">tmux</span>}
              cells={
                <span className="firstrun-agent-cells" data-testid="firstrun-agent-row" data-agent="tmux">
                  <span className="surface-token" data-chip data-testid="firstrun-tool-token">TOOL</span>
                  {tmux.installed ? (
                    <>
                      <span className="surface-token" data-chip>{versionToken("tmux", tmux.version)}</span>
                      <Lamp on label="INSTALLED" />
                    </>
                  ) : (
                    <span className="surface-token" data-chip>TMUX NOT INSTALLED</span>
                  )}
                </span>
              }
              expands={false}
              wrap
            />
          ) : null}
        </ul>
      ) : null}
      {step.refused.length ? (
        <div className="firstrun-fail" role="alert" data-testid="firstrun-agents-refused">
          <StateChip state="failure" label="HOOKS NOT IN" />
          {step.refused.map((r) => (
            <span key={r.agent} className="surface-token" data-tone="danger">
              {AGENT_NAME[r.agent].toUpperCase()} · {codeWords(r.code ?? "failed")}
            </span>
          ))}
        </div>
      ) : null}
      {step.loaded && !step.unread ? (
        <span className="firstrun-agents-foot">
          {receipt}
          {missingAny ? (
            <Button
              dense
              variant="secondary"
              loading={step.checking}
              disabled={step.checking}
              data-testid="firstrun-agents-check"
              onClick={() => void step.read()}
            >
              Check again
            </Button>
          ) : null}
          {step.pending.length ? (
            <>
              <EgressChip label="THIS DEVICE" scope="local" />
              <Button
                dense
                variant="secondary"
                loading={step.busy}
                disabled={step.busy}
                aria-label={`Install hooks: ${step.pending.map((row) => AGENT_NAME[row.id]).join(" and ")}`}
                onClick={() => void step.install()}
              >
                Install hooks
              </Button>
            </>
          ) : null}
        </span>
      ) : null}
    </Card>
  );
}

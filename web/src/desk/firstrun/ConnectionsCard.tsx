/* First run, option A "One screen" — the Connections card (owner ratified
 * 2026-10-05, canvas YDTpkaJqFs3hyrZ4g581Mx §1). The gh and acli sign-ins
 * this Mac already has, one "Use it" each; each row names the host its
 * press reaches (GITHUB.COM, the Atlassian site). */
import { Button } from "../../components/signal/Signal";
import { EgressChip, StateChip, SurfaceLedgerRow } from "../surface";
import { stateWords } from "../../pages/cores/connections/ConnectionsPane";
import { Card } from "./Card";
import { stateCount } from "./calendarStep";
import {
  PROVIDER_GLYPH,
  PROVIDER_NAME,
  PROVIDER_TOOL,
  type ConnectionCandidate,
  type ConnectionsStep,
} from "./connectionsStep";

/** Why a row has no verb, as one token. */
function noVerbToken(row: ConnectionCandidate, step: ConnectionsStep): string {
  const tool = PROVIDER_TOOL[row.provider];
  if (!step.tools[tool]?.installed) return `${tool.toUpperCase()} NOT INSTALLED`;
  if (row.provider === "github" && !row.active) return "NOT ACTIVE IN GH";
  return "";
}

function isSignedIn(row: ConnectionCandidate): boolean {
  if (row.provider !== "github") return true;
  return row.connected || row.state === "signed_in" || row.state === "connected";
}

export function ConnectionsCard({ step, lit }: { step: ConnectionsStep; lit: boolean }) {
  const { rows } = step;
  const connected = step.connected.length;
  const allDone = step.done && connected > 0;
  const connectedLabel = stateCount("CONNECTED", connected);
  // PHILO-15 B31: a GitHub row counts as signed in only when the one
  // Connections entry says so (a stored probe, else gh's sign-in file).
  const signedIn = stateCount("SIGNED IN", rows.filter(isSignedIn).length);
  return (
    <Card
      title="Connections"
      testId="firstrun-connections"
      lit={lit}
      selected={allDone}
      state={
        allDone && connectedLabel ? (
          <StateChip state="success" label={connectedLabel} icon="●" />
        ) : signedIn ? (
          <StateChip state="success" label={signedIn} icon="●" />
        ) : step.loaded && !step.unread ? (
          <StateChip state="idle" label="NO SIGN-IN FOUND" />
        ) : null
      }
    >
      {step.unread ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="unreachable" label="CAN'T CHECK" />
          <span className="firstrun-reason">{step.unread}</span>
          <Button dense variant="secondary" onClick={() => void step.read()}>
            Try again
          </Button>
        </div>
      ) : null}
      {rows.length ? (
        <ul className="concierge-found-list firstrun-ledger" aria-label="Found sign-ins">
          {rows.map((row) => {
            const state = step.states[row.id];
            const name = PROVIDER_NAME[row.provider];
            const token = row.verb ? "" : noVerbToken(row, step);
            return (
              <SurfaceLedgerRow
                key={row.id}
                lead={<span className="concierge-group-glyph">{PROVIDER_GLYPH[row.provider]}</span>}
                primary={<span className="concierge-group-name">{name}</span>}
                cells={
                  <span className="concierge-found-cells" data-testid="firstrun-connection-row" data-provider={row.provider}>
                    <span className="concierge-token">
                      {PROVIDER_TOOL[row.provider]} · {row.account}
                    </span>
                    <span className="concierge-cloud-actions">
                      {row.connected ? (
                        <StateChip state="success" label="CONNECTED" icon="●" />
                      ) : row.verb ? (
                        <Button
                          dense
                          variant="secondary"
                          loading={state?.kind === "busy"}
                          disabled={state?.kind === "busy"}
                          aria-label={`Use ${name} ${row.account}`}
                          onClick={() => void step.use(row)}
                        >
                          Use it
                        </Button>
                      ) : token ? (
                        <span className="surface-token">{token}</span>
                      ) : null}
                    </span>
                    {row.egress_host ? (
                      <span className="concierge-found-line2">
                        <EgressChip label={row.egress_host.toUpperCase()} scope={row.lamp === "cloud" ? "cloud" : "local"} />
                      </span>
                    ) : null}
                    {state?.kind === "refused" ? (
                      <span className="concierge-found-line2 firstrun-fail" role="alert">
                        <StateChip state="failure" label="NOT CONNECTED" />
                        <span className="firstrun-reason">{state.reason}</span>
                      </span>
                    ) : null}
                  </span>
                }
                expands={false}
                wrap
              />
            );
          })}
        </ul>
      ) : step.loaded && !step.unread ? (
        <span className="firstrun-tokens">
          <span className="surface-token">{step.tools.gh?.installed ? "GH · NO SIGN-IN" : "GH NOT INSTALLED"}</span>
          <span className="surface-token">{step.tools.acli?.installed ? "ACLI · NO SIGN-IN" : "ACLI NOT INSTALLED"}</span>
        </span>
      ) : null}
    </Card>
  );
}

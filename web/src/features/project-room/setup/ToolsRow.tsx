// HS-168-04 -- the TOOLS row: connector-pack providers from GET /api/connections.
// One compact tool card per provider (GitHub, Jira -- native needs none).
// Connected = no verb; disconnected = "Connect GitHub" / "Connect Jira"
// primary verb + quiet "Recheck". The face never derives "connected" --
// it reads the wire.

import {
  SurfaceSection,
  ChoiceCardShell,
  StateChip,
  ProvenanceChip,
  EgressChip,
} from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import type { ConnectionTool } from "../../../pages/cores/connections/api";
import { connectionChipLabel } from "../../../pages/cores/connections";
import type { ConnectionState } from "../../../pages/cores/connections/api";

/** Provider emblem glyph (HS-167-05 vocabulary). */
const PROVIDER_EMBLEM: Record<string, string> = {
  github: "GH",
  jira: "J",
};

/** Provenance source for each provider. */
const PROVIDER_PROVENANCE: Record<string, { source: string; boundary: string }> = {
  github: { source: "gh", boundary: "github.com" },
  jira: { source: "acli", boundary: "" },
};

function toolStateChip(tool: ConnectionTool): { state: "success" | "warning" | "failure" | "idle" | "unreachable"; label: string } {
  // ONE label vocabulary with Settings → Connections (the 03 face).
  const label = connectionChipLabel(tool.state as ConnectionState, tool.provider_id);
  switch (tool.state) {
    case "connected": return { state: "success", label };
    case "owner_action_required": return { state: "warning", label };
    case "unavailable": return { state: "failure", label };
    case "degraded": return { state: "unreachable", label };
    case "not_configured": return { state: "idle", label };
    default: return { state: "idle", label: "Unknown" };
  }
}

/** Account summary from the tool entry. */
function accountSummary(tool: ConnectionTool): string {
  if (tool.account?.login) return tool.account.login;
  if (tool.account?.site) {
    return tool.account.email
      ? `${tool.account.site} · ${tool.account.email}`
      : tool.account.site;
  }
  return "";
}

/** Only connector-pack providers (github, jira) -- native needs no tool card. */
const CONNECTOR_PROVIDERS = new Set(["github", "jira"]);

export function ToolsRow({
  tools,
  onConnect,
  onRecheck,
}: {
  tools: ConnectionTool[];
  onConnect: () => void;
  onRecheck: () => void;
}) {
  const connectorTools = tools.filter((t) => CONNECTOR_PROVIDERS.has(t.provider_id));
  if (connectorTools.length === 0) return null;

  return (
    <div data-testid="setup-tools-row">
      <SurfaceSection label={`TOOLS ${connectorTools.length}`}>
        <div className="setup-tools-cards">
          {connectorTools.map((tool) => (
            <ToolCard
              key={tool.provider_id}
              tool={tool}
              onConnect={onConnect}
              onRecheck={onRecheck}
            />
          ))}
        </div>
      </SurfaceSection>
    </div>
  );
}

function ToolCard({
  tool,
  onConnect,
  onRecheck,
}: {
  tool: ConnectionTool;
  onConnect: () => void;
  onRecheck: () => void;
}) {
  const isConnected = tool.state === "connected";
  const chip = toolStateChip(tool);
  const emblem = PROVIDER_EMBLEM[tool.provider_id] ?? tool.provider_id[0]?.toUpperCase() ?? "?";
  const label = tool.provider_id === "github" ? "GitHub" : tool.provider_id === "jira" ? "Jira" : tool.provider_id;
  const summary = accountSummary(tool);
  const prov = PROVIDER_PROVENANCE[tool.provider_id];
  const jiraBoundary = tool.account?.site ?? tool.egress_host ?? "";

  return (
    <ChoiceCardShell
      label={label}
      summary={summary || undefined}
      emblem={emblem}
      data-testid={`setup-tool-${tool.provider_id}`}
      data-state={tool.state}
    >
      <div className="setup-tool-chips">
        <StateChip state={chip.state} label={chip.label} />
        {prov ? (
          <ProvenanceChip
            source={prov.source}
            boundary={tool.provider_id === "jira" ? jiraBoundary : prov.boundary}
          />
        ) : null}
      </div>
      {!isConnected ? (
        <div className="setup-tool-actions">
          <Button
            dense
            variant="primary"
            onClick={onConnect}
            data-testid={`setup-connect-${tool.provider_id}`}
          >
            Connect {label}
          </Button>
          <Button
            dense
            variant="ghost"
            onClick={onRecheck}
          >
            Recheck
          </Button>
        </div>
      ) : null}
    </ChoiceCardShell>
  );
}

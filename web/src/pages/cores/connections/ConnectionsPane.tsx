// HS-168-03 — the Connections face: Settings -> Connections.
// Composed from the barrel only. The face reads `state` from the wire;
// it never derives "connected" itself. Zero sentences.

import { useCallback, useEffect, useState } from "react";
import {
  GadgetGroup,
  StateChip,
  ProvenanceChip,
  EgressChip,
  Receipt,
  SurfaceWell,
  SurfaceState,
  TransportKey,
  StringGadget,
  type ChipState,
} from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import type {
  ConnectionTool,
  ConnectionsResponse,
  ConnectionState,
  JiraSubConnection,
} from "./api";
import { fetchConnections, recheckProvider } from "./api";
import "./connections.css";

/* ── State mapping (D1 + D6) ── */

function chipState(state: ConnectionState): ChipState {
  switch (state) {
    case "connected": return "success";
    case "owner_action_required": return "warning";
    case "unavailable": return "failure";
    case "degraded": return "unreachable";
    case "not_configured": return "idle";
  }
}

export function chipLabel(state: ConnectionState, providerId: string): string {
  switch (state) {
    case "connected": return "Connected";
    case "owner_action_required": return "Sign in";
    case "unavailable":
      if (providerId === "jira" || providerId === "confluence") return "acli missing";
      return "gh missing";
    case "degraded": return "Unreachable";
    case "not_configured":
      if (providerId === "jira" || providerId === "confluence") return "Not set up";
      return "Off";
  }
}

function toolTier(state: ConnectionState): string | undefined {
  if (state === "connected") return "ok";
  if (state === "owner_action_required") return "warn";
  return undefined;
}

/** Whether the fold should be open by default for this state. */
function foldOpen(state: ConnectionState): boolean {
  return state === "owner_action_required" || state === "unavailable";
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleTimeString([], { hour12: false });
  } catch {
    return "";
  }
}

function siteInitial(site: string): string {
  return (site[0] ?? "?").toUpperCase();
}

/* ── Calendar emblem: inline SVG outline, never emoji (HS-148-05 law) ── */

function CalendarEmblem() {
  return (
    <svg
      className="connections-tool-emblem-svg"
      width="16"
      height="16"
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.4"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="1.5" y="2.5" width="13" height="12" rx="1.5" />
      <line x1="1.5" y1="6" x2="14.5" y2="6" />
      <line x1="5" y1="1" x2="5" y2="4" />
      <line x1="11" y1="1" x2="11" y2="4" />
    </svg>
  );
}

/* ── Command well: code left, COPY right ── */

function CommandWell({
  hint,
}: {
  hint: string;
}) {
  return (
    <SurfaceWell>
      <div className="connections-command-row">
        <code className="connections-command-code">{hint}</code>
        <TransportKey
          label="Copy"
          glyph="C"
          compact
          onClick={() => {
            try { void navigator.clipboard.writeText(hint); } catch { /* noop */ }
          }}
        />
      </div>
    </SurfaceWell>
  );
}

/* ── Tool cards ── */

function GitHubCard({
  tool,
  onRecheck,
  busy,
}: {
  tool: ConnectionTool;
  onRecheck: () => void;
  busy: boolean;
}) {
  const state = tool.state;
  const showFold = foldOpen(state);
  const hint = tool.recovery_hint ?? "gh auth login";

  return (
    <div className="connections-tool-row" data-testid="connections-github" data-tier={toolTier(state)}>
      <span className="connections-tool-identity">
        <span className="connections-tool-emblem">GH</span>
        <span className="connections-tool-label">GitHub</span>
      </span>
      {state === "connected" && tool.account?.login ? (
        <span className="connections-tool-summary">{tool.account.login}</span>
      ) : null}
      <div className="connections-tool-chips">
        <span title={state === "degraded" ? (tool.error_detail ?? undefined) : undefined}>
          <StateChip
            state={chipState(state)}
            label={chipLabel(state, "github")}
          />
        </span>
        <ProvenanceChip source="gh" boundary="github.com" />
      </div>
      <div className="connections-tool-actions">
        {!showFold ? (
          <>
            <Button dense variant="ghost" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label="GITHUB.COM" scope="cloud" />
          </>
        ) : null}
      </div>
      {showFold ? (
        <div className="connections-fold">
          <CommandWell hint={hint} />
          <div className="connections-fold-actions">
            <Button dense variant="primary" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label="GITHUB.COM" scope="cloud" />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function JiraConnectionRow({
  conn,
  onRecheck,
  busy,
}: {
  conn: JiraSubConnection;
  onRecheck: () => void;
  busy: boolean;
}) {
  const state = conn.state;
  const showFold = state === "owner_action_required";
  const hint = conn.recovery_hint ?? `acli jira auth login --site ${conn.account.site} --email ${conn.account.email} --token`;
  const site = conn.account.site;

  return (
    <div className="connections-tool-row" data-testid={`connections-jira-conn-${conn.connection_ref}`} data-tier={toolTier(state)}>
      <span className="connections-tool-identity">
        <span className="connections-tool-emblem">{siteInitial(site)}</span>
        <span className="connections-tool-label">{site}</span>
      </span>
      <span className="connections-tool-summary">{conn.account.email}</span>
      <div className="connections-tool-chips">
        <StateChip state={chipState(state)} label={chipLabel(state, "jira")} />
        <ProvenanceChip source="acli" boundary={site} />
      </div>
      <div className="connections-tool-actions">
        {!showFold ? (
          <>
            <Button dense variant="ghost" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label={site.toUpperCase()} scope="cloud" />
          </>
        ) : null}
      </div>
      {showFold ? (
        <div className="connections-fold">
          <CommandWell hint={hint} />
          <div className="connections-fold-actions">
            <Button dense variant="primary" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label={site.toUpperCase()} scope="cloud" />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function JiraCards({
  tool,
  onRecheck,
  onAddAccount,
  busyRef,
}: {
  tool: ConnectionTool;
  onRecheck: (ref?: string) => void;
  onAddAccount: (site: string, email: string) => void;
  busyRef: string | null;
}) {
  const [addSite, setAddSite] = useState("");
  const [addEmail, setAddEmail] = useState("");

  const handleAdd = useCallback(() => {
    const s = addSite.trim();
    const e = addEmail.trim();
    if (s && e) {
      onAddAccount(s, e);
      setAddSite("");
      setAddEmail("");
    }
  }, [addSite, addEmail, onAddAccount]);

  const connections = tool.connections ?? [];
  const hasConnections = connections.length > 0;

  // With zero connections: the ghost "Add account" card IS the Jira card
  if (!hasConnections) {
    return (
      <div className="connections-tool-row connections-jira-ghost" data-testid="connections-jira" data-tier={undefined}>
        <span className="connections-tool-identity">
          <span className="connections-tool-emblem">J</span>
          <span className="connections-tool-label">Jira</span>
        </span>
        <div className="connections-tool-chips">
          <StateChip state="idle" label="Not set up" />
          <ProvenanceChip source="acli" />
        </div>
        <div className="connections-jira-ghost-fields">
          <label className="connections-field-label">
            <span className="connections-field-label-text">Site</span>
            <StringGadget label="Site" value={addSite} onChange={setAddSite} placeholder="site.atlassian.net" />
          </label>
          <label className="connections-field-label">
            <span className="connections-field-label-text">Email</span>
            <StringGadget label="Email" value={addEmail} onChange={setAddEmail} placeholder="email" />
          </label>
          <div className="connections-jira-add-row">
            <Button dense variant="ghost" disabled={!addSite.trim() || !addEmail.trim()} onClick={handleAdd}>
              Add
            </Button>
          </div>
        </div>
      </div>
    );
  }

  // With connections: one row per connection
  return (
    <>
      {connections.map((conn) => (
        <JiraConnectionRow
          key={conn.connection_ref}
          conn={conn}
          onRecheck={() => onRecheck(conn.connection_ref)}
          busy={busyRef === conn.connection_ref}
        />
      ))}
    </>
  );
}

/* ── HS-174-07: Confluence connection rows (same grammar as Jira) ── */

function ConfluenceConnectionRow({
  conn,
  onRecheck,
  busy,
}: {
  conn: JiraSubConnection;
  onRecheck: () => void;
  busy: boolean;
}) {
  const state = conn.state;
  const showFold = state === "owner_action_required";
  const hint = conn.recovery_hint ?? `acli confluence auth login --site ${conn.account.site} --email ${conn.account.email} --token`;
  const site = conn.account.site;

  return (
    <div className="connections-tool-row" data-testid={`connections-confluence-conn-${conn.connection_ref}`} data-tier={toolTier(state)}>
      <span className="connections-tool-identity">
        <span className="connections-tool-emblem">{siteInitial(site)}</span>
        <span className="connections-tool-label">{site}</span>
      </span>
      <span className="connections-tool-summary">{conn.account.email}</span>
      <div className="connections-tool-chips">
        <StateChip state={chipState(state)} label={chipLabel(state, "confluence")} />
        <ProvenanceChip source="acli" boundary={site} />
      </div>
      <div className="connections-tool-actions">
        {!showFold ? (
          <>
            <Button dense variant="ghost" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label={site.toUpperCase()} scope="cloud" />
          </>
        ) : null}
      </div>
      {showFold ? (
        <div className="connections-fold">
          <CommandWell hint={hint} />
          <div className="connections-fold-actions">
            <Button dense variant="primary" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <EgressChip label={site.toUpperCase()} scope="cloud" />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ConfluenceCards({
  tool,
  onRecheck,
  busyRef,
}: {
  tool: ConnectionTool;
  onRecheck: (ref?: string) => void;
  busyRef: string | null;
}) {
  const connections = tool.connections ?? [];

  if (connections.length === 0) {
    return (
      <div className="connections-tool-row" data-testid="connections-confluence" data-tier={undefined}>
        <span className="connections-tool-identity">
          <span className="connections-tool-emblem">C</span>
          <span className="connections-tool-label">Confluence</span>
        </span>
        <div className="connections-tool-chips">
          <StateChip state={chipState(tool.state)} label={chipLabel(tool.state, "confluence")} />
          <ProvenanceChip source="acli" />
        </div>
      </div>
    );
  }

  return (
    <>
      {connections.map((conn) => (
        <ConfluenceConnectionRow
          key={conn.connection_ref}
          conn={conn}
          onRecheck={() => onRecheck(conn.connection_ref)}
          busy={busyRef === conn.connection_ref}
        />
      ))}
    </>
  );
}

function CalendarCard({
  tool,
  onOpen,
}: {
  tool: ConnectionTool | undefined;
  onOpen: () => void;
}) {
  const sources = tool?.account?.sources;
  const isConnected = tool?.state === "connected";
  const state: ChipState = isConnected ? "success" : "idle";
  const label = isConnected ? "Connected" : "Not set up";
  const summary = isConnected && sources != null ? `${sources} sources` : undefined;
  const verb = isConnected ? "Sources" : "Set up";

  return (
    <div className="connections-tool-row" data-testid="connections-calendar">
      <span className="connections-tool-identity">
        <CalendarEmblem />
        <span className="connections-tool-label">Calendar</span>
      </span>
      {summary ? <span className="connections-tool-summary">{summary}</span> : null}
      <div className="connections-tool-chips">
        <StateChip state={state} label={label} />
        <ProvenanceChip source="local" />
      </div>
      <div className="connections-tool-actions">
        <Button dense variant="ghost" onClick={onOpen}>
          {verb}
        </Button>
      </div>
    </div>
  );
}

function ModelsCard({
  tool,
  onOpen,
}: {
  tool: ConnectionTool | undefined;
  onOpen: () => void;
}) {
  const assigned = tool?.account?.assigned ?? 0;
  const total = tool?.account?.total ?? 7;
  const hasAssigned = assigned > 0;
  const state: ChipState = hasAssigned ? "active" : "idle";
  const label = hasAssigned ? "Assigned" : "Unassigned";
  const summary = hasAssigned ? `${assigned} of ${total} assigned` : "Unassigned";

  return (
    <div className="connections-tool-row" data-testid="connections-models">
      <span className="connections-tool-identity">
        <span className="connections-tool-emblem">M</span>
        <span className="connections-tool-label">Models</span>
      </span>
      <span className="connections-tool-summary">{summary}</span>
      <div className="connections-tool-chips">
        <StateChip state={state} label={label} />
        <ProvenanceChip source="local" />
      </div>
      <div className="connections-tool-actions">
        <Button dense variant="ghost" onClick={onOpen}>
          Open Models
        </Button>
      </div>
    </div>
  );
}

/* ── ConnectionsPane ── */

export interface ConnectionsFoot {
  egressHost: string | undefined;
  checkedAt: string | undefined;
}

export function ConnectionsPane({
  onFooterUpdate,
  onOpenModule,
}: {
  /** Lifts the connections receipt to the parent footer. */
  onFooterUpdate: (foot: ConnectionsFoot) => void;
  /** Navigate to another settings module (calendar -> "meetings", models -> "models"). */
  onOpenModule: (moduleId: string) => void;
}) {
  const [data, setData] = useState<ConnectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>(undefined);
  const [recheckBusy, setRecheckBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(undefined);
    try {
      const resp = await fetchConnections();
      setData(resp);
      // Compute the foot from the response
      const lastChecked = resp.tools
        .map((t) => t.last_checked_at)
        .filter(Boolean)
        .sort()
        .pop();
      const lastEgress = resp.tools
        .filter((t) => t.last_checked_at)
        .sort((a, b) => (a.last_checked_at ?? "").localeCompare(b.last_checked_at ?? ""))
        .pop()?.egress_host;
      onFooterUpdate({
        egressHost: lastEgress,
        checkedAt: lastChecked ? formatTime(lastChecked) : undefined,
      });
    } catch (err) {
      setError(
        err instanceof Error && err.message
          ? `Connections did not load from this hub (${err.message}). Nothing changed. Retry.`
          : "Connections did not load from this hub. Nothing changed. Retry.",
      );
    } finally {
      setLoading(false);
    }
  }, [onFooterUpdate]);

  useEffect(() => { void load(); }, [load]);

  const handleRecheck = useCallback(async (providerId: string, subRef?: string) => {
    setRecheckBusy(subRef ?? providerId);
    try {
      const updated = await recheckProvider(providerId);
      if (updated && data) {
        setData({
          tools: data.tools.map((t) =>
            t.provider_id === providerId ? updated : t
          ),
        });
        const checkedAt = updated.last_checked_at ? formatTime(updated.last_checked_at) : undefined;
        onFooterUpdate({
          egressHost: updated.egress_host,
          checkedAt,
        });
      }
    } finally {
      setRecheckBusy(null);
    }
  }, [data, onFooterUpdate]);

  const handleAddJiraAccount = useCallback(async (site: string, email: string) => {
    try {
      await import("../../../lib/api").then(({ apiFetch: f }) =>
        f("/api/providers/jira/connections", { method: "POST", json: { site, email } })
      );
      void load();
    } catch {
      // The add failed silently; the user will see the state is unchanged.
    }
  }, [load]);

  if (loading && !data) {
    return <SurfaceState loading={true} onRetry={load} />;
  }

  if (error && !data) {
    return <SurfaceState loading={false} error={error} onRetry={load} />;
  }

  const tools = data?.tools ?? [];
  const github = tools.find((t) => t.provider_id === "github");
  const jira = tools.find((t) => t.provider_id === "jira");
  const confluence = tools.find((t) => t.provider_id === "confluence");
  const calendar = tools.find((t) => t.provider_id === "calendar");
  const models = tools.find((t) => t.provider_id === "models");

  const toolCount = tools.length || 5; // D1: always 5 if the wire returns them (GH, Jira, Confluence, Calendar, Models)

  return (
    <GadgetGroup label={`Tools ${toolCount}`}>
      {github ? (
        <GitHubCard
          tool={github}
          onRecheck={() => void handleRecheck("github")}
          busy={recheckBusy === "github"}
        />
      ) : null}
      {jira ? (
        <JiraCards
          tool={jira}
          onRecheck={(ref) => void handleRecheck("jira", ref)}
          onAddAccount={handleAddJiraAccount}
          busyRef={recheckBusy}
        />
      ) : null}
      {confluence ? (
        <ConfluenceCards
          tool={confluence}
          onRecheck={(ref) => void handleRecheck("confluence", ref)}
          busyRef={recheckBusy}
        />
      ) : null}
      <CalendarCard
        tool={calendar}
        onOpen={() => onOpenModule("meetings")}
      />
      <ModelsCard
        tool={models}
        onOpen={() => onOpenModule("models")}
      />
    </GadgetGroup>
  );
}

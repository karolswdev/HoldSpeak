// HS-168-03 — the Connections face: Settings -> Connections.
// Composed from the barrel only. The face reads `state` from the wire;
// it never derives "connected" itself. Zero sentences.

import { wireDate } from "../../../desk/surface/format";
import { useCallback, useEffect, useRef, useState } from "react";
import {
  GadgetGroup,
  StateChip,
  EgressChip,
  Receipt,
  SurfaceWell,
  SurfaceState,
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
import { ACCOUNTS_CHANGED, addAtlassianAccount, fetchConnections, recheckProvider } from "./api";
import "./connections.css";
import { CalendarCard as CalendarSetupCard } from "../../../desk/firstrun/CalendarCard";
import { useCalendarStep } from "../../../desk/firstrun/calendarStep";
import "../../../desk/firstrun/firstrun.css";

/* ── State mapping (D1 + D6) ── */

function chipState(state: ConnectionState): ChipState {
  switch (state) {
    case "connected": return "success";
    case "owner_action_required": return "warning";
    case "unavailable": return "failure";
    case "degraded": return "unreachable";
    case "not_configured": return "idle";
    case "never_checked": return "idle";
    case "signed_in": return "success";
  }
}

/** PHILO-17 U29: the producer names a missing sign-in (`owner_action_required`:
 *  github_provider / jira_provider classify the CLI's own answer); the face
 *  reads that state, never the error text. */
export function notSignedIn(state: ConnectionState): boolean {
  return state === "owner_action_required";
}

export function chipLabel(state: ConnectionState, providerId: string): string {
  switch (state) {
    case "connected": return "Connected";
    case "owner_action_required": return "Not signed in";
    case "unavailable":
      if (providerId === "jira" || providerId === "confluence") return "acli missing";
      return "gh missing";
    case "degraded": return "Unreachable";
    case "not_configured":
      if (providerId === "jira" || providerId === "confluence") return "Not set up";
      return "Off";
    case "never_checked": return "Never checked";
    case "signed_in": return "Signed in";
  }
}

/** PHILO-9-02 B1: the age of this row's own stored check, as words. */
export function checkedAgo(
  lastCheckedAt: string | undefined | null,
  ageSeconds?: number,
  now: number = Date.now(),
): string | undefined {
  let seconds: number | undefined;
  if (lastCheckedAt) {
    const then = wireDate(lastCheckedAt)?.getTime() ?? Number.NaN;
    if (!Number.isNaN(then)) seconds = Math.max(0, Math.floor((now - then) / 1000));
  }
  if (seconds === undefined && typeof ageSeconds === "number") seconds = Math.max(0, ageSeconds);
  if (seconds === undefined) return undefined;
  if (seconds < 60) return "Checked now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `Checked ${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Checked ${hours} h ago`;
  return `Checked ${Math.floor(hours / 24)} d ago`;
}

/** The state chip words: the state, then this row's own check age. */
export function stateWords(
  state: ConnectionState,
  providerId: string,
  row: { last_checked_at?: string; checked_age_seconds?: number; account?: { login?: string } | object },
): string {
  const label = chipLabel(state, providerId);
  if (state === "never_checked") return label;
  // PHILO-15 B31 (Astra r1): a sign-in read from gh's config is no check:
  // it names its source and carries no time.
  const login = row.account && "login" in row.account ? row.account.login : undefined;
  if (state === "signed_in") return [label, login, "From gh config"].filter(Boolean).join(" · ");
  const age = checkedAgo(row.last_checked_at, row.checked_age_seconds);
  return age ? `${label} · ${age}` : label;
}

function toolTier(state: ConnectionState): string | undefined {
  if (state === "connected") return "ok";
  if (state === "owner_action_required") return "warn";
  return undefined;
}

/** PHILO-17 U29: every row that is not ready shows its exact command and Copy. */
function foldOpen(state: ConnectionState): boolean {
  return state !== "connected" && state !== "signed_in";
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return "";
  try {
    return wireDate(iso)?.toLocaleTimeString([], { hour12: false }) ?? "";
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

/* ── Command well: code left, COPY right ── (first run's Connections card
   uses it too, PHILO-17) */

export function CommandWell({
  hint,
}: {
  hint: string;
}) {
  const [copy, setCopy] = useState<"Copy" | "Copied" | "Copy failed">("Copy");
  return (
    <SurfaceWell>
      <div className="connections-command-row">
        <code className="connections-command-code">{hint}</code>
        <Button
          dense
          variant="secondary"
          onClick={() => {
            void (async () => {
              try { await navigator.clipboard.writeText(hint); setCopy("Copied"); }
              catch { setCopy("Copy failed"); }
            })();
          }}
        >{copy}</Button>
      </div>
    </SurfaceWell>
  );
}

/** PHILO-17 U29: sign in where the source row is (New Project, the Room):
 *  the exact command with Copy, Add for an Atlassian account, and Recheck.
 *  No Settings window over the work. */
export function SignInWell({
  tool,
  busy,
  onRecheck,
  onAddAccount,
}: {
  tool: ConnectionTool;
  busy: boolean;
  onRecheck: () => void;
  onAddAccount: (site: string, email: string) => void | Promise<void>;
}) {
  const provider = tool.provider_id;
  const atlassian = provider === "jira" || provider === "confluence";
  const waiting = (tool.connections ?? []).filter((c) => c.state !== "connected");
  const hints: string[] = atlassian
    ? waiting.map((c) => c.recovery_hint ?? `acli ${provider} auth login --site ${c.account.site} --email ${c.account.email} --token`)
    : [tool.recovery_hint && tool.state !== "unavailable" ? tool.recovery_hint : "gh auth login"];
  if (tool.state === "unavailable" && tool.recovery_hint) hints.splice(0, hints.length, tool.recovery_hint);
  const noAccount = atlassian && !(tool.connections ?? []).length;
  return (
    <div className="connections-signin-well" data-testid={`signin-well-${provider}`}>
      {noAccount ? (
        <AddAccountFields provider={provider as "jira" | "confluence"} onAdd={onAddAccount} busy={busy} />
      ) : (
        <>
          {hints.map((hint) => <CommandWell key={hint} hint={hint} />)}
          <div className="connections-fold-actions">
            <Button dense variant="secondary" onClick={onRecheck} loading={busy} data-testid={`signin-recheck-${provider}`}>
              Recheck
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Tool cards ── */

function GitHubCard({
  tool,
  onRecheck,
  busy,
  lead = false,
}: {
  tool: ConnectionTool;
  onRecheck: () => void;
  busy: boolean;
  /** PHILO-17 REFIT: this row holds the window's one primary. */
  lead?: boolean;
}) {
  const state = tool.state;
  const showFold = foldOpen(state);
  const hint = tool.recovery_hint ?? "gh auth login";
  const [shown, setShown] = useState(false);
  const [copy, setCopy] = useState("Copy command");
  const copyHint = async () => {
    try { await navigator.clipboard.writeText(hint); setCopy("Copied"); }
    catch { setCopy("Copy failed"); }
  };

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
            label={stateWords(state, "github", tool)}
          />
        </span>
      </div>
      {showFold ? (
        <span className="connections-signin-word" data-testid="connections-github-signin">
          {state === "unavailable" ? "Install gh" : "Sign in to GitHub"}
        </span>
      ) : null}
      <div className="connections-tool-actions">
        {showFold ? (
          <>
            {/* PHILO-17 REFIT: the sign-in is one compact row; the command
                is copied by a verb and drawn only on demand. */}
            <Button dense variant="ghost" onClick={() => void copyHint()} data-testid="connections-github-copy">
              {copy}
            </Button>
            <Button dense variant="ghost" aria-expanded={shown} onClick={() => setShown((value) => !value)} data-testid="connections-github-show">
              {shown ? "Hide" : "Show"}
            </Button>
          </>
        ) : null}
        <Button dense variant={showFold && lead ? "primary" : showFold ? "secondary" : "ghost"} onClick={onRecheck} loading={busy}>
          Recheck
        </Button>
        <EgressChip label="GITHUB.COM" scope="cloud" />
      </div>
      {showFold && shown ? (
        <code className="connections-signin-code" data-testid="connections-github-command">{hint}</code>
      ) : null}
    </div>
  );
}

/* PHILO-4-01 r4: an acli host chip. The row label shows the full host, so
   this chip (and only this kind) may truncate; title carries the full host
   so the chip never inherits EgressChip's "route not set" default. */
function HostChip({ site }: { site: string }) {
  return (
    <EgressChip
      label={site.toUpperCase()}
      scope="cloud"
      className="gadget-chip-truncate"
      title={site}
    />
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
  const showFold = foldOpen(state);
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
        <StateChip state={chipState(state)} label={stateWords(state, "jira", conn)} />
      </div>
      <div className="connections-tool-actions">
        {!showFold ? (
          <>
            <Button dense variant="ghost" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <HostChip site={site} />
          </>
        ) : null}
      </div>
      {showFold ? (
        <div className="connections-fold">
          <CommandWell hint={hint} />
          <div className="connections-fold-actions">
            <Button dense variant="secondary" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <HostChip site={site} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

/** PHILO-17 U29: the Add for a Jira or Confluence account: Site, Email, the
 *  exact sign-in command (with Copy) and Add. The caller checks the new
 *  account at once. */
export function AddAccountFields({
  provider,
  onAdd,
  busy = false,
}: {
  provider: "jira" | "confluence";
  onAdd: (site: string, email: string) => void | Promise<void>;
  busy?: boolean;
}) {
  const [site, setSite] = useState("");
  const [email, setEmail] = useState("");
  const [failed, setFailed] = useState(false);
  const [saving, setSaving] = useState(false);
  const s = site.trim();
  const e = email.trim();
  const add = async () => {
    if (!s || !e || saving) return;
    setSaving(true); setFailed(false);
    try {
      await onAdd(s, e);
      setSite(""); setEmail("");
    } catch { setFailed(true); }
    finally { setSaving(false); }
  };
  return (
    <div className="connections-jira-ghost-fields" data-testid={`connections-add-${provider}`}>
      <label className="connections-field-label">
        <span className="connections-field-label-text">Site</span>
        <StringGadget label="Site" value={site} onChange={setSite} placeholder="site.atlassian.net" />
      </label>
      <label className="connections-field-label">
        <span className="connections-field-label-text">Email</span>
        <StringGadget label="Email" value={email} onChange={setEmail} placeholder="email" />
      </label>
      <CommandWell hint={`acli ${provider} auth login --site ${s || "<site>"} --email ${e || "<email>"} --token`} />
      <div className="connections-jira-add-row">
        <Button dense variant="secondary" disabled={!s || !e || busy} loading={saving} onClick={() => void add()}>
          {failed ? "Retry" : "Add"}
        </Button>
        {failed ? <StateChip state="failure" label="Account not added" /> : null}
      </div>
    </div>
  );
}

/** PHILO-17 REFIT: an account with no row yet shows one verb, Add account;
 *  the Site and Email fields and the sign-in command unfold under it. */
function AddAccountFold({
  provider,
  onAdd,
  busy,
}: {
  provider: "jira" | "confluence";
  onAdd: (site: string, email: string) => void | Promise<void>;
  busy: boolean;
}) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <div className="connections-tool-actions">
        <Button dense variant="ghost" aria-expanded={open} onClick={() => setOpen((value) => !value)} data-testid={`connections-add-open-${provider}`}>
          {open ? "Cancel" : "Add account"}
        </Button>
      </div>
      {open ? <AddAccountFields provider={provider} onAdd={onAdd} busy={busy} /> : null}
    </>
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
  onAddAccount: (site: string, email: string) => void | Promise<void>;
  busyRef: string | null;
}) {
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
          {/* PHILO-9-02 B1 (Codex Astra r1 finding 7): the empty card says the tool's own state. */}
          <StateChip state={chipState(tool.state)} label={stateWords(tool.state, "jira", tool)} />
        </div>
        <AddAccountFold provider="jira" busy={busyRef === "jira"} onAdd={onAddAccount} />
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
      <AddAccountFold provider="jira" busy={busyRef === "jira"} onAdd={onAddAccount} />
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
  const showFold = foldOpen(state);
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
        <StateChip state={chipState(state)} label={stateWords(state, "confluence", conn)} />
      </div>
      <div className="connections-tool-actions">
        {!showFold ? (
          <>
            <Button dense variant="ghost" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <HostChip site={site} />
          </>
        ) : null}
      </div>
      {showFold ? (
        <div className="connections-fold">
          <CommandWell hint={hint} />
          <div className="connections-fold-actions">
            <Button dense variant="secondary" onClick={onRecheck} loading={busy}>
              Recheck
            </Button>
            <HostChip site={site} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ConfluenceCards({
  tool,
  onRecheck,
  onAddAccount,
  busyRef,
}: {
  tool: ConnectionTool;
  onRecheck: (ref?: string) => void;
  onAddAccount: (site: string, email: string) => void | Promise<void>;
  busyRef: string | null;
}) {
  const connections = tool.connections ?? [];

  if (connections.length === 0) {
    return (
      <div className="connections-tool-row connections-jira-ghost" data-testid="connections-confluence" data-tier={undefined}>
        <span className="connections-tool-identity">
          <span className="connections-tool-emblem">C</span>
          <span className="connections-tool-label">Confluence</span>
        </span>
        <div className="connections-tool-chips">
          <StateChip state={chipState(tool.state)} label={stateWords(tool.state, "confluence", tool)} />
        </div>
        <AddAccountFold provider="confluence" busy={busyRef === "confluence"} onAdd={onAddAccount} />
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
      <AddAccountFold provider="confluence" busy={busyRef === "confluence"} onAdd={onAddAccount} />
    </>
  );
}

function CalendarCard({
  tool,
  onOpen,
  onChoose,
}: {
  tool: ConnectionTool | undefined;
  onOpen: () => void;
  onChoose: () => void;
}) {
  const sources = tool?.account?.sources;
  const isConnected = tool?.state === "connected";
  const state: ChipState = isConnected ? "success" : "idle";
  const label = isConnected ? "Connected" : "Not set up";
  const summary = isConnected && sources ? `${sources} sources` : undefined;
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
      </div>
      <div className="connections-tool-actions">
        {isConnected ? <Button dense variant="ghost" onClick={onOpen}>{verb}</Button> : null}
        <Button dense variant="secondary" onClick={onChoose}>Choose calendar</Button>
      </div>
    </div>
  );
}

function CalendarChooser({ onCalendarChanged, onBeforeCalendarChange }: {
  onCalendarChanged?: () => Promise<void>;
  onBeforeCalendarChange?: () => Promise<boolean>;
}) {
  const step = useCalendarStep();
  return <div className="connections-calendar-setup"><CalendarSetupCard step={step} lit={false} reselectNative onUsed={onCalendarChanged} beforeUse={onBeforeCalendarChange} /></div>;
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
  // PHILO-15 B33: summaries that run on the route (the default or a pick)
  // are in use even when no group row is assigned.
  const summaryHost = tool?.account?.summary_host ?? null;
  const hasAssigned = assigned > 0;
  const inUse = hasAssigned || Boolean(summaryHost);
  const state: ChipState = inUse ? "active" : "idle";
  const label = hasAssigned ? "Assigned" : summaryHost ? "In use" : "Unassigned";
  const summary = hasAssigned
    ? `${assigned} of ${total} assigned`
    : summaryHost
      ? `Summaries · ${summaryHost}`
      : "Unassigned";

  return (
    <div className="connections-tool-row" data-testid="connections-models">
      <span className="connections-tool-identity">
        <span className="connections-tool-emblem">M</span>
        {/* PHILO-17 REFIT: one name for the engines window, Runs on. */}
        <span className="connections-tool-label">Runs on</span>
      </span>
      {summary !== label ? <span className="connections-tool-summary">{summary}</span> : null}
      <div className="connections-tool-chips">
        <StateChip state={state} label={label} />
      </div>
      <div className="connections-tool-actions">
        <Button dense variant="ghost" onClick={onOpen}>
          Choose engines
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
  focusProvider,
  onCalendarChanged,
  onBeforeCalendarChange,
}: {
  /** Lifts the connections receipt to the parent footer. */
  onFooterUpdate: (foot: ConnectionsFoot) => void;
  /** Navigate to another settings module (calendar -> "meetings", models -> "models"). */
  onOpenModule: (moduleId: string) => void;
  /** PHILO-17 (needsyou): the provider to bring into view and focus
   *  (`github`, `jira`, `confluence`): Needs you's Reconnect lands here. */
  focusProvider?: string | null;
  onCalendarChanged?: () => Promise<void>;
  onBeforeCalendarChange?: () => Promise<boolean>;
}) {
  const [data, setData] = useState<ConnectionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | undefined>(undefined);
  const [recheckBusy, setRecheckBusy] = useState<string | null>(null);
  const [checkFailed, setCheckFailed] = useState<string | null>(null);
  const [calendarOpen, setCalendarOpen] = useState(focusProvider === "calendar");
  useEffect(() => { if (focusProvider === "calendar") setCalendarOpen(true); }, [focusProvider]);

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
    } catch {
      setError("Accounts could not be read");
    } finally {
      setLoading(false);
    }
  }, [onFooterUpdate]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => {
    const read = () => void load();
    window.addEventListener(ACCOUNTS_CHANGED, read);
    return () => window.removeEventListener(ACCOUNTS_CHANGED, read);
  }, [load]);

  // PHILO-17 (needsyou): Reconnect opens on the provider's row, focused.
  const anchorRef = useRef<HTMLSpanElement>(null);
  const loaded = Boolean(data);
  useEffect(() => {
    if (!focusProvider || !loaded) return;
    const group = anchorRef.current?.parentElement;
    const row = group?.querySelector<HTMLElement>(`[data-testid^="connections-${focusProvider}"]`);
    if (!row) return;
    row.scrollIntoView?.({ block: "center" });
    const target = row.querySelector<HTMLElement>("button:not([disabled])") ?? row;
    if (target === row) row.tabIndex = -1;
    target.focus({ preventScroll: true });
  }, [focusProvider, loaded]);

  const handleRecheck = useCallback(async (providerId: string, subRef?: string) => {
    setRecheckBusy(subRef ?? providerId);
    setCheckFailed(null);
    try {
      const updated = await recheckProvider(providerId);
      if (!updated) throw new Error("No check result");
      if (data) {
        setData((current) => current ? ({
          tools: current.tools.map((t) =>
            t.provider_id === providerId ? updated : t
          ),
        }) : current);
        const checkedAt = updated.last_checked_at ? formatTime(updated.last_checked_at) : undefined;
        onFooterUpdate({
          egressHost: updated.egress_host,
          checkedAt,
        });
      }
      window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
    } catch { setCheckFailed(providerId); }
    finally {
      setRecheckBusy(null);
    }
  }, [data, onFooterUpdate]);

  // PHILO-17 U29: an added account is checked at once (never left NEVER CHECKED).
  const handleAddAccount = useCallback(async (provider: "jira" | "confluence", site: string, email: string) => {
    setRecheckBusy(provider);
    setCheckFailed(null);
    try {
      await addAtlassianAccount(provider, site, email);
      window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
      try { await recheckProvider(provider); }
      catch { setCheckFailed(provider); }
    } finally {
      setRecheckBusy(null);
      void load();
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

  void toolCount;
  return (
    <GadgetGroup label="Accounts">
      <span ref={anchorRef} hidden />
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {checkFailed ? <div className="connections-check-failed" role="alert"><span>{checkFailed === "github" ? "GitHub" : checkFailed === "jira" ? "Jira" : "Confluence"}</span><StateChip state="failure" label="Check failed" /><Button dense variant="secondary" onClick={() => void handleRecheck(checkFailed)}>Retry</Button></div> : null}
      {github ? (
        <GitHubCard
          tool={github}
          onRecheck={() => void handleRecheck("github")}
          busy={recheckBusy === "github"}
          lead={foldOpen(github.state)}
        />
      ) : null}
      {jira ? (
        <JiraCards
          tool={jira}
          onRecheck={(ref) => void handleRecheck("jira", ref)}
          onAddAccount={(site, email) => handleAddAccount("jira", site, email)}
          busyRef={recheckBusy}
        />
      ) : null}
      {confluence ? (
        <ConfluenceCards
          tool={confluence}
          onRecheck={(ref) => void handleRecheck("confluence", ref)}
          onAddAccount={(site, email) => handleAddAccount("confluence", site, email)}
          busyRef={recheckBusy}
        />
      ) : null}
      <CalendarCard
        tool={calendar}
        onOpen={() => onOpenModule("meetings")}
        onChoose={() => setCalendarOpen((value) => !value)}
      />
      {calendarOpen ? <CalendarChooser onCalendarChanged={async () => { await onCalendarChanged?.(); await load(); }} onBeforeCalendarChange={onBeforeCalendarChange} /> : null}
      <ModelsCard
        tool={models}
        onOpen={() => onOpenModule("models")}
      />
    </GadgetGroup>
  );
}

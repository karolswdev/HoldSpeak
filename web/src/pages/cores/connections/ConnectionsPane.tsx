// HS-168-03 — the Connections face: Settings -> Connections.
// Composed from the barrel only. The face reads `state` from the wire;
// it never derives "connected" itself. Zero sentences.

import { wireDate } from "../../../desk/surface/format";
import { useCallback, useEffect, useRef, useState, type Dispatch, type ReactNode, type SetStateAction } from "react";
import {
  GadgetGroup,
  GadgetRow,
  FoldGadget,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  StateChip,
  EgressChip,
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

/** A producer-named sign-in or missing tool opens its details on request. */
function needsDetails(state: ConnectionState): boolean {
  return state === "owner_action_required" || state === "unavailable";
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return "";
  try {
    return wireDate(iso)?.toLocaleTimeString([], { hour12: false }) ?? "";
  } catch {
    return "";
  }
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

function GitHubCard({ tool, onRecheck, busy, blocked, lead = false }: {
  tool: ConnectionTool; onRecheck: () => void; busy: boolean; blocked: boolean; lead?: boolean;
}) {
  const state = tool.state;
  const details = needsDetails(state);
  const hint = tool.recovery_hint ?? "gh auth login";
  const [shown, setShown] = useState(false);
  const [copy, setCopy] = useState("Copy command");
  const copyHint = async () => {
    try { await navigator.clipboard.writeText(hint); setCopy("Copied"); }
    catch { setCopy("Copy failed"); }
  };
  const check = <span className="connections-check-action"><EgressChip label="GITHUB.COM" scope="cloud"/><Button dense variant={lead ? "primary" : "secondary"} onClick={onRecheck} loading={busy} disabled={blocked && !busy}>{state === "degraded" ? "Retry" : "Recheck"}</Button></span>;
  return <SurfaceLedgerRow data-testid="connections-github" wrap expands={false} open={details && shown}
    lead={<span className="connections-tool-emblem">GH</span>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">GitHub</strong>{tool.account?.login ? <span className="connections-tool-summary">{tool.account.login}</span> : null}</span>}
    cells={<span className="surface-ledger-cells connections-tool-chips" title={state === "degraded" ? tool.error_detail : undefined}><StateChip wrap state={chipState(state)} label={stateWords(state, "github", tool)}/></span>}
    trailing={details ? <Button dense variant={lead ? "primary" : "secondary"} aria-expanded={shown} onClick={() => setShown(value => !value)} data-testid="connections-github-show">{shown ? "Close" : state === "owner_action_required" ? "Sign in" : "Details"}</Button> : check}>
    <SurfaceWell><div className="connections-well-head"><strong>{state === "unavailable" ? "Install gh" : "Sign in to GitHub"}</strong></div><div className="connections-command-row"><code className="connections-command-code" data-testid="connections-github-command">{hint}</code><Button dense variant="secondary" onClick={() => void copyHint()} data-testid="connections-github-copy">{copy}</Button></div><div className="connections-fold-actions">{check}</div></SurfaceWell>
  </SurfaceLedgerRow>;
}

function HostChip({ site }: { site: string }) {
  return <EgressChip label={site.toUpperCase()} scope="cloud" title={site}/>;
}

function AccountEmail({ email }: { email: string }) {
  const at = email.indexOf("@");
  return <span className="connections-tool-summary">{at < 0 ? email : <>{email.slice(0, at + 1)}<wbr/>{email.slice(at + 1)}</>}</span>;
}

function AtlassianConnectionRow({ provider, conn, onRecheck, busy, blocked, open, onToggle, addAction, addWell, addOpen = false }: {
  provider: "jira" | "confluence"; conn: JiraSubConnection; onRecheck: () => void; busy: boolean; blocked: boolean; open: boolean; onToggle: () => void;
  addAction?: ReactNode; addWell?: ReactNode; addOpen?: boolean;
}) {
  const state = conn.state;
  const details = needsDetails(state);
  const name = provider === "jira" ? "Jira" : "Confluence";
  const hint = conn.recovery_hint ?? `acli ${provider} auth login --site ${conn.account.site} --email ${conn.account.email} --token`;
  const check = <span className="connections-check-action"><HostChip site={conn.account.site}/><Button dense variant="secondary" onClick={onRecheck} loading={busy} disabled={blocked && !busy}>{state === "degraded" ? "Retry" : "Recheck"}</Button></span>;
  const shown = (details && open) || addOpen;
  // The Add form keeps its pending/refusal state through sign-in detours.
  return <SurfaceLedgerRow data-testid={`connections-${provider}-conn-${conn.connection_ref}`} wrap expands={false} open={shown || Boolean(addWell)}
    lead={<span className="connections-tool-emblem">{name[0]}</span>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">{name}</strong><AccountEmail email={conn.account.email}/>{details && !open ? <span className="connections-tool-summary">{conn.account.site}</span> : null}</span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={chipState(state)} label={stateWords(state, provider, conn)}/></span>}
    trailing={<span className="connections-tool-actions">{details ? <Button dense variant="secondary" aria-expanded={open} onClick={onToggle}>{open ? "Close" : state === "owner_action_required" ? "Sign in" : "Details"}</Button> : check}{addAction}</span>}>
    <div className="connections-account-wells" hidden={!shown}>
      {addWell ? <div hidden={!addOpen}>{addWell}</div> : null}
      {details && open ? <SurfaceWell><div className="connections-well-head"><strong>{state === "unavailable" ? "Install acli" : `Sign in to ${name}`}</strong></div><CommandWell hint={hint}/><div className="connections-fold-actions">{check}</div></SurfaceWell> : null}
    </div>
  </SurfaceLedgerRow>;
}

type AccountDraft = { site: string; email: string };

/** PHILO-17 U29: the Add for a Jira or Confluence account: Site, Email, the
 *  exact sign-in command (with Copy) and Add. The caller checks the new
 *  account at once. */
export function AddAccountFields({
  provider,
  onAdd,
  busy = false,
  compact = false,
  onCancel,
  draft,
  onDraftChange,
}: {
  provider: "jira" | "confluence";
  onAdd: (site: string, email: string) => void | Promise<void>;
  busy?: boolean;
  compact?: boolean;
  onCancel?: () => void;
  draft?: AccountDraft;
  onDraftChange?: Dispatch<SetStateAction<AccountDraft>>;
}) {
  const [localDraft, setLocalDraft] = useState<AccountDraft>({ site: "", email: "" });
  const { site, email } = draft ?? localDraft;
  const setDraft = onDraftChange ?? setLocalDraft;
  const setSite = (value: string) => setDraft(current => ({ ...current, site: value }));
  const setEmail = (value: string) => setDraft(current => ({ ...current, email: value }));
  const [failed, setFailed] = useState(false);
  const [saving, setSaving] = useState(false);
  const s = site.trim();
  const e = email.trim();
  const add = async () => {
    if (!s || !e || saving) return;
    setSaving(true); setFailed(false);
    try {
      await onAdd(s, e);
      setDraft(current => ({
        site: current.site === site ? "" : current.site,
        email: current.email === email ? "" : current.email,
      }));
    } catch { setFailed(true); }
    finally { setSaving(false); }
  };
  return (
    <div className="connections-jira-ghost-fields" data-testid={`connections-add-${provider}`}>
      {compact ? <GadgetGroup><GadgetRow wide label="Site"><StringGadget label="Site" value={site} onChange={setSite} placeholder="site.atlassian.net"/></GadgetRow><GadgetRow wide label="Email"><StringGadget label="Email" value={email} onChange={setEmail} placeholder="you@example.com"/></GadgetRow></GadgetGroup> : <>
      <label className="connections-field-label">
        <span className="connections-field-label-text">Site</span>
        <StringGadget label="Site" value={site} onChange={setSite} placeholder="site.atlassian.net" />
      </label>
      <label className="connections-field-label">
        <span className="connections-field-label-text">Email</span>
        <StringGadget label="Email" value={email} onChange={setEmail} placeholder="email" />
      </label>
      <CommandWell hint={`acli ${provider} auth login --site ${s || "<site>"} --email ${e || "<email>"} --token`} />
      </>}
      <div className="connections-jira-add-row">
        <Button dense variant="secondary" disabled={!s || !e || busy} loading={saving} onClick={() => void add()}>
          {failed ? "Retry" : "Add"}
        </Button>
        {onCancel ? <Button dense variant="ghost" onClick={onCancel}>Cancel</Button> : null}
        {failed ? <StateChip wrap state="failure" label="Account not added" /> : null}
      </div>
      {compact ? <FoldGadget title="Sign-in command"><CommandWell hint={`acli ${provider} auth login --site ${s || "<site>"} --email ${e || "<email>"} --token`}/></FoldGadget> : null}
    </div>
  );
}

function AtlassianCards({ tool, onRecheck, onAddAccount, busyRef }: {
  tool: ConnectionTool; onRecheck: (ref?: string) => void;
  onAddAccount: (site: string, email: string) => void | Promise<void>; busyRef: string | null;
}) {
  const provider = tool.provider_id as "jira" | "confluence";
  const name = provider === "jira" ? "Jira" : "Confluence";
  const connections = tool.connections ?? [];
  const [well, setWell] = useState<string | null>(null);
  const [draft, setDraft] = useState<AccountDraft>({ site: "", email: "" });
  const addButton = <Button dense variant="ghost" aria-expanded={well === "add"} onClick={() => setWell(value => value === "add" ? null : "add")} data-testid={`connections-add-open-${provider}`}>{well === "add" ? "Cancel" : connections.length ? `Add ${name} account` : "Add account"}</Button>;
  const form = <SurfaceWell><div className="connections-well-head"><strong>Add {name} account</strong></div><AddAccountFields compact provider={provider} onAdd={onAddAccount} busy={busyRef !== null} onCancel={() => setWell(null)} draft={draft} onDraftChange={setDraft}/></SurfaceWell>;
  if (!connections.length) return <SurfaceLedgerRow data-testid={`connections-${provider}`} wrap expands={false} open
    lead={<span className="connections-tool-emblem">{name[0]}</span>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">{name}</strong></span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={chipState(tool.state)} label={stateWords(tool.state, provider, tool)}/></span>}
    trailing={addButton}><div className="connections-account-wells" hidden={well !== "add"}>{form}</div></SurfaceLedgerRow>;
  return <>
    {connections.map((conn, index) => {
      const last = index === connections.length - 1;
      return <AtlassianConnectionRow
        key={conn.connection_ref} provider={provider} conn={conn}
        onRecheck={() => onRecheck(conn.connection_ref)} busy={busyRef === conn.connection_ref} blocked={busyRef !== null}
        open={well === conn.connection_ref}
        onToggle={() => setWell(value => value === conn.connection_ref ? null : conn.connection_ref)}
        addAction={last ? addButton : undefined} addWell={last ? form : undefined}
        addOpen={last && well === "add"}
      />;
    })}
  </>;
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

  return <SurfaceLedgerRow data-testid="connections-calendar" wrap expands={false}
    lead={<CalendarEmblem/>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">Calendar</strong>{summary ? <span className="connections-tool-summary">{summary}</span> : null}</span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={state} label={label}/></span>}
    trailing={<span className="connections-tool-actions">{isConnected ? <Button dense variant="ghost" onClick={onOpen}>{verb}</Button> : null}<Button dense variant="secondary" onClick={onChoose}>Choose calendar</Button></span>}/>;
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

  return <div className="connections-engines" data-testid="connections-models"><span className="connections-tool-label">Runs on</span>{summary !== label ? <span className="connections-tool-summary">{summary}</span> : <StateChip wrap state={state} label={label}/>}<Button dense variant="ghost" onClick={onOpen}>Choose engines</Button></div>;
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
  const [checkFailed, setCheckFailed] = useState<{ providerId: string; subRef?: string } | null>(null);
  const loadGeneration = useRef(0);
  const actionPending = useRef(false);
  const [calendarOpen, setCalendarOpen] = useState(focusProvider === "calendar");
  useEffect(() => { if (focusProvider === "calendar") setCalendarOpen(true); }, [focusProvider]);

  const load = useCallback(async () => {
    const generation = ++loadGeneration.current;
    setLoading(true);
    setError(undefined);
    try {
      const resp = await fetchConnections();
      if (generation !== loadGeneration.current) return;
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
      if (generation === loadGeneration.current) setError("Accounts could not be read");
    } finally {
      if (generation === loadGeneration.current) setLoading(false);
    }
  }, [onFooterUpdate]);

  useEffect(() => { void load(); }, [load]);
  useEffect(() => () => { ++loadGeneration.current; }, []);
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
    if (actionPending.current) return;
    actionPending.current = true;
    setRecheckBusy(subRef ?? providerId);
    setCheckFailed(null);
    try {
      const updated = subRef ? await recheckProvider(providerId, subRef) : await recheckProvider(providerId);
      if (!updated) throw new Error("No check result");
      ++loadGeneration.current;
      setLoading(false);
      setError(undefined);
      setData((current) => current ? ({
        tools: current.tools.map((t) => t.provider_id === providerId ? updated : t),
      }) : current);
      const checkedAt = updated.last_checked_at ? formatTime(updated.last_checked_at) : undefined;
      onFooterUpdate({ egressHost: updated.egress_host, checkedAt });
      window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
    } catch { setCheckFailed({ providerId, subRef }); }
    finally {
      actionPending.current = false;
      setRecheckBusy(null);
    }
  }, [onFooterUpdate]);

  // PHILO-17 U29: an added account is checked at once (never left NEVER CHECKED).
  const handleAddAccount = useCallback(async (provider: "jira" | "confluence", site: string, email: string) => {
    if (actionPending.current) throw new Error("Another account action is pending");
    actionPending.current = true;
    setRecheckBusy(provider);
    setCheckFailed(null);
    try {
      await addAtlassianAccount(provider, site, email);
      window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
      try { await recheckProvider(provider); }
      catch { setCheckFailed({ providerId: provider }); }
    } finally {
      actionPending.current = false;
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

  return (
    <div className="connections-pane prefs-column">
      <span ref={anchorRef} hidden />
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {checkFailed ? <div className="connections-check-failed" role="alert"><span>{checkFailed.providerId === "github" ? "GitHub" : checkFailed.providerId === "jira" ? "Jira" : "Confluence"}</span><StateChip wrap state="failure" label="Check failed" /><Button dense variant="secondary" disabled={recheckBusy !== null} onClick={() => void handleRecheck(checkFailed.providerId, checkFailed.subRef)}>Retry</Button></div> : null}
      <SurfaceSection label="Services"><SurfaceLedger cols="accounts"><ul className="surface-ledger-rows connections-services">
      {github ? (
        <GitHubCard
          tool={github}
          onRecheck={() => void handleRecheck("github")}
          busy={recheckBusy === "github"}
          blocked={recheckBusy !== null}
          lead={github.state !== "connected" && github.state !== "signed_in"}
        />
      ) : null}
      {jira ? (
        <AtlassianCards
          tool={jira}
          onRecheck={(ref) => void handleRecheck("jira", ref)}
          onAddAccount={(site, email) => handleAddAccount("jira", site, email)}
          busyRef={recheckBusy}
        />
      ) : null}
      {confluence ? (
        <AtlassianCards
          tool={confluence}
          onRecheck={(ref) => void handleRecheck("confluence", ref)}
          onAddAccount={(site, email) => handleAddAccount("confluence", site, email)}
          busyRef={recheckBusy}
        />
      ) : null}
      </ul></SurfaceLedger></SurfaceSection>
      <SurfaceSection label="Calendar"><SurfaceLedger cols="accounts"><ul className="surface-ledger-rows">
      <CalendarCard
        tool={calendar}
        onOpen={() => onOpenModule("meetings")}
        onChoose={() => setCalendarOpen((value) => !value)}
      />
      </ul></SurfaceLedger>
      {calendarOpen ? <CalendarChooser onCalendarChanged={async () => { await onCalendarChanged?.(); await load(); }} onBeforeCalendarChange={onBeforeCalendarChange} /> : null}
      </SurfaceSection>
      <ModelsCard
        tool={models}
        onOpen={() => onOpenModule("models")}
      />
    </div>
  );
}

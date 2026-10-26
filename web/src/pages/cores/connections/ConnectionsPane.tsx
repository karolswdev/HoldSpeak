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
  PaneWell,
  type ChipState,
} from "../../../desk/surface";
import { Button } from "../../../components/signal/Signal";
import type {
  AccountUse,
  ConnectionTool,
  ConnectionsResponse,
  ConnectionState,
  JiraSubConnection,
} from "./api";
import { ACCOUNTS_CHANGED, addAtlassianAccount, fetchConnections, recheckProvider, removeAtlassianAccount } from "./api";
import { readableError } from "../../../lib/api";
import { startSignin as startSigninApi, signinStatus, type SigninStatusResponse, type SigninTarget } from "./api";
import { sameTarget, useDeliveryTerminal, type OpenTarget } from "../../../desk/deliveryTerminal";
import { PROVIDER_NAME, useConnectionsStep, type ConnectionCandidate } from "../../../desk/firstrun/connectionsStep";
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

/** Betterment ST2: a row's state in words: Works, Not signed in, Signed in
 *  as another account, Could not check: <reason>.  The reason is the hub's
 *  own words (`reason`); the face never reads the error text. */
export function chipLabel(
  state: ConnectionState,
  providerId: string,
  words: { reason?: string; other_account?: boolean } = {},
): string {
  const cli = providerId === "jira" || providerId === "confluence" ? "acli" : "gh";
  switch (state) {
    case "connected": return "Works";
    case "owner_action_required": return "Not signed in";
    case "unavailable": return `Could not check: ${words.reason ?? `${cli} is not installed`}`;
    case "degraded":
      if (words.other_account) return "Signed in as another account";
      return `Could not check: ${words.reason ?? `${cli} gave no answer`}`;
    case "not_configured":
      if (providerId === "jira" || providerId === "confluence") return "Not set up";
      return "Off";
    case "never_checked": return "Not checked";
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
  row: {
    last_checked_at?: string; checked_age_seconds?: number; account?: { login?: string } | object;
    reason?: string; other_account?: boolean;
  },
): string {
  const label = chipLabel(state, providerId, row);
  if (state === "never_checked") return label;
  // PHILO-15 B31 (Astra r1): a sign-in read from gh's config is no check:
  // it names its source and carries no time.
  const login = row.account && "login" in row.account ? row.account.login : undefined;
  if (state === "signed_in") return [label, login, "From gh config"].filter(Boolean).join(" · ");
  const age = checkedAgo(row.last_checked_at, row.checked_age_seconds);
  return age ? `${label} · ${age}` : label;
}

function formatTime(iso: string | undefined | null): string {
  if (!iso) return "";
  try {
    return wireDate(iso)?.toLocaleTimeString([], { hour12: false }) ?? "";
  } catch {
    return "";
  }
}

type SigninRun = {
  providerId: string;
  connectionRef?: string;
  runId: string;
  target: OpenTarget;
};

function openTargetFromSignin(target: SigninTarget): OpenTarget {
  return {
    targetId: target.target_id,
    targetGeneration: target.target_generation,
    nodeId: target.node_id,
    label: target.label,
    sessionLabel: target.session_label,
    worktreeId: target.worktree_id ?? null,
    agent: target.agent,
    presentation: "embedded",
  };
}

function SigninPane({
  run,
  onFinished,
}: {
  run: SigninRun;
  onFinished: (status: SigninStatusResponse) => void;
}) {
  const status = useDeliveryTerminal((s) => s.status);
  const lines = useDeliveryTerminal((s) => s.lines);
  const raw = useDeliveryTerminal((s) => s.raw);
  const changedAt = useDeliveryTerminal((s) => s.changedAt);
  const completed = useRef(false);
  const inputQueue = useRef(Promise.resolve());
  useEffect(() => {
    useDeliveryTerminal.getState().open(run.target);
    return () => {
      const current = useDeliveryTerminal.getState().openTarget;
      if (sameTarget(current, run.target)) useDeliveryTerminal.getState().close();
    };
  }, [run.target]);
  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await signinStatus(run.runId);
        if (!cancelled && !completed.current && (result.status === "finished" || result.status === "failed")) {
          completed.current = true;
          onFinished(result);
        }
      } catch {
        // The terminal stream remains the truth while a status read retries.
      }
    };
    void poll();
    const timer = window.setInterval(() => void poll(), 500);
    return () => { cancelled = true; window.clearInterval(timer); };
  }, [onFinished, run.runId]);
  const onData = useCallback((data: string) => {
    inputQueue.current = inputQueue.current.then(async () => {
      const terminal = useDeliveryTerminal.getState();
      const text = data.replace(/[\r\n\u0003]/g, "");
      if (text) await terminal.sendText(text, false);
      for (const key of data) {
        if (key === "\r" || key === "\n") await terminal.sendKeys(["Enter"], "ENTER");
        else if (key === "\u0003") await terminal.sendKeys(["C-c"], "INT");
      }
    }).catch(() => {
      // A pane close cancels the queue at the same command boundary.
    });
  }, []);
  const live = status === "live" || status === "resyncing";
  return (
    <SurfaceWell>
      <div className="connections-signin-terminal" data-testid={`connections-signin-terminal-${run.runId}`}>
        <PaneWell
          live={live}
          lines={lines}
          raw={raw}
          changedAt={changedAt}
          absence={<StateChip state="idle" label="Starting" wrap />}
          onData={onData}
        />
      </div>
    </SurfaceWell>
  );
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
              Check
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

/* ── Tool cards ── */

/** Betterment ST2: what a pressed row unfolds: what uses the account, Sign in
 *  again (today's command, until ST8) and, for Jira and Confluence, Remove. */
function AccountUnfold({ usedBy, hint, signInLabel, onRemove, testid, commandOpen = false, onSignIn, signin, onSigninFinished }: {
  usedBy: AccountUse[] | undefined; hint: string; signInLabel: string; onRemove?: () => void; testid: string;
  /** A row that is not signed in opens with its command shown. */
  commandOpen?: boolean;
  /** Starts the provider-owned browser flow in the existing terminal seam. */
  onSignIn?: () => Promise<boolean>;
  signin?: SigninRun | null;
  onSigninFinished?: (status: SigninStatusResponse) => void;
}) {
  const [signIn, setSignIn] = useState(commandOpen);
  const [starting, setStarting] = useState(false);
  const uses = usedBy ?? [];
  const pressSignIn = async () => {
    if (!onSignIn) {
      setSignIn((value) => !value);
      return;
    }
    if (starting) return;
    setStarting(true);
    setSignIn(false);
    let started = false;
    try { started = await onSignIn(); }
    finally {
      setStarting(false);
      if (!started) setSignIn(true);
    }
  };
  return <SurfaceWell>
    <div className="connections-unfold" data-testid={testid}>
      <div className="connections-unfold-uses">
        <span className="connections-field-label-text">Used by</span>
        {uses.length ? uses.map((u) => <span key={`${u.kind}:${u.name}`} className="connections-tool-summary">{u.kind === "destination" ? "Send to" : "Project"} · {u.name}</span>)
          : <span className="connections-tool-summary">Nothing yet</span>}
      </div>
      <div className="connections-fold-actions">
        <Button dense variant="secondary" aria-expanded={Boolean(signin) || signIn} onClick={() => void pressSignIn()} loading={starting}>{signInLabel}</Button>
        {onRemove ? <Button dense variant="ghost" onClick={onRemove}>Remove</Button> : null}
      </div>
      {signin ? <SigninPane run={signin} onFinished={(status) => {
        setSignIn(false);
        onSigninFinished?.(status);
      }}/> : signIn ? <CommandWell hint={hint}/> : null}
    </div>
  </SurfaceWell>;
}

/** The words of a row's fix verb: Sign in, Install <cli>, or Sign in again. */
function fixLabel(state: ConnectionState, cli: "gh" | "acli"): string {
  if (state === "unavailable") return `Install ${cli}`;
  return notSignedIn(state) ? "Sign in" : "Sign in again";
}

/** A row that cannot work until he acts shows its fix verb next to Check. */
function needsFix(state: ConnectionState): boolean {
  return state === "owner_action_required" || state === "unavailable";
}

function GitHubCard({ tool, onRecheck, busy, blocked, lead = false, open, onToggle, onSignIn, signin, onSigninFinished }: {
  tool: ConnectionTool; onRecheck: () => void; busy: boolean; blocked: boolean; lead?: boolean;
  open: boolean; onToggle: () => void; onSignIn?: () => Promise<boolean>; signin?: SigninRun | null;
  onSigninFinished?: (status: SigninStatusResponse) => void;
}) {
  const state = tool.state;
  const hint = tool.state === "unavailable" ? (tool.recovery_hint ?? "brew install gh") : "gh auth login";
  const host = tool.egress_host ?? "github.com";
  // The host is named next to the account; the verb's hover title says
  // where the check goes (UX-CANON A.9 as amended 2026-10-25).
  const check = <span className="connections-check-action"><Button dense variant={lead && !needsFix(state) ? "primary" : "secondary"} title={`Checks ${host}`} onClick={onRecheck} loading={busy} disabled={blocked && !busy}>Check</Button></span>;
  const startFromRow = () => {
    onToggle();
    if (onSignIn) void onSignIn();
  };
  return <SurfaceLedgerRow data-testid="connections-github" wrap open={open} onToggle={onToggle} lineLabel="GitHub"
    lead={<ServiceGlyph provider="github"/>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">GitHub</strong>{tool.account?.login ? <span className="connections-tool-summary">{tool.account.login}</span> : null}<span className="connections-tool-summary connections-site">{host}</span></span>}
    cells={<span className="surface-ledger-cells connections-tool-chips" title={state === "degraded" ? tool.error_detail : undefined}><StateChip wrap state={chipState(state)} label={stateWords(state, "github", tool)}/></span>}
    trailing={<span className="connections-tool-actions">{needsFix(state) ? <Button dense variant={lead ? "primary" : "secondary"} aria-expanded={open} onClick={state === "owner_action_required" && !open ? startFromRow : onToggle} data-testid="connections-github-show">{open ? "Close" : fixLabel(state, "gh")}</Button> : null}{check}</span>}>
    {open ? <AccountUnfold testid="connections-github-unfold" usedBy={tool.used_by} hint={hint}
      signInLabel={fixLabel(state, "gh")} commandOpen={needsFix(state)}
      onSignIn={state !== "unavailable" ? onSignIn : undefined} signin={signin} onSigninFinished={onSigninFinished}/> : null}
  </SurfaceLedgerRow>;
}

/** A service's glyph: a small coloured tile with its initial (sans), in
 *  place of a mono monogram. Decorative: the row names the service. */
function ServiceGlyph({ provider }: { provider: string }) {
  const name = PROVIDER_NAME[provider as keyof typeof PROVIDER_NAME] ?? provider;
  return <span className="connections-tool-emblem" data-provider={provider} aria-hidden="true">{String(name)[0]?.toUpperCase()}</span>;
}

function HostChip({ site }: { site: string }) {
  return <EgressChip label={site.toUpperCase()} scope="cloud" title={site}/>;
}

function AccountEmail({ email }: { email: string }) {
  const at = email.indexOf("@");
  return <span className="connections-tool-summary">{at < 0 ? email : <>{email.slice(0, at + 1)}<wbr/>{email.slice(at + 1)}</>}</span>;
}

function AtlassianConnectionRow({ provider, conn, onRecheck, onRemove, busy, blocked, open, onToggle, addAction, addWell, addOpen = false, onSignIn, signin, onSigninFinished }: {
  provider: "jira" | "confluence"; conn: JiraSubConnection; onRecheck: () => void; onRemove: () => void; busy: boolean; blocked: boolean; open: boolean; onToggle: () => void;
  addAction?: ReactNode; addWell?: ReactNode; addOpen?: boolean;
  onSignIn?: () => Promise<boolean>; signin?: SigninRun | null;
  onSigninFinished?: (status: SigninStatusResponse) => void;
}) {
  const state = conn.state;
  const name = provider === "jira" ? "Jira" : "Confluence";
  const hint = state === "unavailable" ? "brew tap atlassian/homebrew-acli && brew install acli"
    : conn.recovery_hint ?? `acli ${provider} auth login --site ${conn.account.site} --email ${conn.account.email} --token`;
  const check = <span className="connections-check-action"><Button dense variant="secondary" title={`Checks ${conn.account.site}`} onClick={onRecheck} loading={busy} disabled={blocked && !busy}>Check</Button></span>;
  const startFromRow = () => {
    onToggle();
    if (onSignIn) void onSignIn();
  };
  // The Add form keeps its pending/refusal state through sign-in detours.
  return <SurfaceLedgerRow data-testid={`connections-${provider}-conn-${conn.connection_ref}`} wrap onToggle={onToggle} lineLabel={`${name} ${conn.account.site}`}
    // The last row keeps the Add form mounted (its draft and refusal survive a
    // sign-in detour), so it claims no aria-expanded of its own.
    open={open || addOpen || Boolean(addWell)} expands={!addWell}
    lead={<ServiceGlyph provider={provider}/>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">{name}</strong><AccountEmail email={conn.account.email}/><span className="connections-tool-summary connections-site">{conn.account.site}</span></span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={chipState(state)} label={stateWords(state, provider, conn)}/></span>}
    trailing={<span className="connections-tool-actions">{needsFix(state) ? <Button dense variant="secondary" aria-expanded={open} onClick={state === "owner_action_required" && !open ? startFromRow : onToggle}>{open ? "Close" : fixLabel(state, "acli")}</Button> : null}{check}{addAction}</span>}>
    <div className="connections-account-wells" hidden={!(open || addOpen)}>
      {addWell ? <div hidden={!addOpen}>{addWell}</div> : null}
      {open ? <AccountUnfold testid={`connections-${provider}-unfold-${conn.connection_ref}`} usedBy={conn.used_by} hint={hint} onRemove={onRemove}
        signInLabel={fixLabel(state, "acli")} commandOpen={needsFix(state)}
        onSignIn={state !== "unavailable" ? onSignIn : undefined} signin={signin} onSigninFinished={onSigninFinished}/> : null}
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

function AtlassianCards({ tool, onRecheck, onAddAccount, onRemove, busyRef, onSignIn, signin, onSigninFinished }: {
  tool: ConnectionTool; onRecheck: (ref?: string) => void;
  onAddAccount: (site: string, email: string) => void | Promise<void>;
  onRemove: (conn: JiraSubConnection) => void; busyRef: string | null;
  onSignIn?: (site: string, email: string, ref: string) => Promise<boolean>;
  signin?: SigninRun | null;
  onSigninFinished?: (status: SigninStatusResponse) => void;
}) {
  const provider = tool.provider_id as "jira" | "confluence";
  const name = provider === "jira" ? "Jira" : "Confluence";
  const connections = tool.connections ?? [];
  const [well, setWell] = useState<string | null>(null);
  const [draft, setDraft] = useState<AccountDraft>({ site: "", email: "" });
  const addButton = <Button dense variant="ghost" aria-expanded={well === "add"} onClick={() => setWell(value => value === "add" ? null : "add")} data-testid={`connections-add-open-${provider}`}>{well === "add" ? "Cancel" : connections.length ? `Add ${name} account` : "Add account"}</Button>;
  const form = <SurfaceWell><div className="connections-well-head"><strong>Add {name} account</strong></div><AddAccountFields compact provider={provider} onAdd={onAddAccount} busy={busyRef !== null} onCancel={() => setWell(null)} draft={draft} onDraftChange={setDraft}/></SurfaceWell>;
  if (!connections.length) return <SurfaceLedgerRow data-testid={`connections-${provider}`} wrap expands={false} open
    lead={<ServiceGlyph provider={provider}/>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">{name}</strong></span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={chipState(tool.state)} label={stateWords(tool.state, provider, tool)}/></span>}
    trailing={addButton}><div className="connections-account-wells" hidden={well !== "add"}>{form}</div></SurfaceLedgerRow>;
  return <>
    {connections.map((conn, index) => {
      const last = index === connections.length - 1;
      return <AtlassianConnectionRow
        key={conn.connection_ref} provider={provider} conn={conn}
        onRecheck={() => onRecheck(conn.connection_ref)} onRemove={() => onRemove(conn)}
        busy={busyRef === conn.connection_ref} blocked={busyRef !== null}
        open={well === conn.connection_ref}
        onToggle={() => setWell(value => value === conn.connection_ref ? null : conn.connection_ref)}
        addAction={last ? addButton : undefined} addWell={last ? form : undefined}
        addOpen={last && well === "add"}
        onSignIn={onSignIn ? () => onSignIn(conn.account.site, conn.account.email, conn.connection_ref) : undefined}
        signin={signin?.connectionRef === conn.connection_ref ? signin : null}
        onSigninFinished={onSigninFinished}
      />;
    })}
  </>;
}

function CalendarCard({
  tool,
  onChoose,
}: {
  tool: ConnectionTool | undefined;
  onChoose: () => void;
}) {
  const sources = tool?.account?.sources;
  const isConnected = tool?.state === "connected";
  const state: ChipState = isConnected ? "success" : "idle";
  const label = isConnected ? "Connected" : "Not set up";
  const summary = isConnected && sources ? `${sources} sources` : undefined;

  return <SurfaceLedgerRow data-testid="connections-calendar" wrap expands={false}
    lead={<span className="connections-tool-emblem" data-provider="calendar" aria-hidden="true"><CalendarEmblem/></span>}
    primary={<span className="connections-tool-identity"><strong className="connections-tool-label">Calendar</strong>{summary ? <span className="connections-tool-summary">{summary}</span> : null}</span>}
    cells={<span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state={state} label={label}/></span>}
    // Betterment setup ST1: the sources are under this row now (no
    // `Sources` verb that went to Meetings).
    trailing={<span className="connections-tool-actions"><Button dense variant="secondary" onClick={onChoose}>Choose calendar</Button></span>}/>;
}

function CalendarChooser({ onCalendarChanged, onBeforeCalendarChange }: {
  onCalendarChanged?: () => Promise<void>;
  onBeforeCalendarChange?: () => Promise<boolean>;
}) {
  const step = useCalendarStep();
  return <div className="connections-calendar-setup"><CalendarSetupCard step={step} lit={false} reselectNative onUsed={onCalendarChanged} beforeUse={onBeforeCalendarChange} /></div>;
}

/* ── ConnectionsPane ── */

export interface ConnectionsFoot {
  egressHost: string | undefined;
  checkedAt: string | undefined;
}

export function ConnectionsPane({
  onFooterUpdate,
  focusProvider,
  onCalendarChanged,
  onBeforeCalendarChange,
}: {
  /** Lifts the connections receipt to the parent footer. */
  onFooterUpdate: (foot: ConnectionsFoot) => void;
  /** Navigate to another settings module. Betterment setup ST1: nothing in
   *  Accounts navigates away now (Calendar's sources and the engine row
   *  moved); kept for callers. */
  onOpenModule?: (moduleId: string) => void;
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
  // Betterment ST2: the pressed row (one open at a time), and the Undo of a Remove.
  const [openRow, setOpenRow] = useState<string | null>(null);
  const [signin, setSignin] = useState<SigninRun | null>(null);
  const signinRef = useRef<SigninRun | null>(null);
  const [signinFailure, setSigninFailure] = useState<string | null>(null);
  const [removed, setRemoved] = useState<{ provider: "jira" | "confluence"; site: string; email: string } | null>(null);
  const [removeFailed, setRemoveFailed] = useState(false);
  const found = useConnectionsStep();
  const readFound = found.read;
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
      if (generation === loadGeneration.current) setError("Account read failed · Accounts unchanged · Retry");
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

  const beginSignin = useCallback(async (providerId: string, site: string, email?: string, connectionRef?: string): Promise<boolean> => {
    setSigninFailure(null);
    try {
      const result = await startSigninApi(providerId, site, email);
      if (!result || typeof result.run_id !== "string" || !result.target?.target_id) return false;
      const run: SigninRun = {
        providerId,
        connectionRef,
        runId: result.run_id,
        target: openTargetFromSignin(result.target),
      };
      signinRef.current = run;
      setSignin(run);
      return true;
    } catch (exc) {
      setSigninFailure(readableError(exc));
      return false;
    }
  }, []);

  const finishSignin = useCallback((result: SigninStatusResponse) => {
    const run = signinRef.current;
    if (!run) return;
    signinRef.current = null;
    setSignin(null);
    if (result.status === "failed") setSigninFailure(result.error || "CLI failed");
    void handleRecheck(run.providerId, run.connectionRef);
  }, [handleRecheck]);

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

  // Betterment ST2: Remove takes the row out of HoldSpeak (never out of acli);
  // Undo adds it again for 8 s and checks it.
  const handleRemove = useCallback(async (provider: "jira" | "confluence", conn: JiraSubConnection) => {
    setRemoveFailed(false);
    try {
      await removeAtlassianAccount(provider, conn.connection_ref);
      setRemoved({ provider, site: conn.account.site, email: conn.account.email });
      setOpenRow(null);
    } catch { setRemoveFailed(true); }
    window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
    void readFound();
  }, [readFound]);
  useEffect(() => {
    if (!removed) return;
    const timer = window.setTimeout(() => setRemoved(null), 8000);
    return () => window.clearTimeout(timer);
  }, [removed]);
  const undoRemove = useCallback(async () => {
    if (!removed) return;
    const { provider, site, email } = removed;
    setRemoved(null);
    try { await handleAddAccount(provider, site, email); } catch { setRemoveFailed(true); }
    void readFound();
  }, [removed, handleAddAccount, readFound]);
  const useFound = useCallback(async (candidate: ConnectionCandidate) => {
    await found.use(candidate);
    window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
  }, [found]);

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
  // Found on this Mac: accounts in gh's and acli's own files that HoldSpeak
  // does not use yet, each with Use.  Absent when there is none.
  const usedRefs = new Set<string>([
    ...(jira?.connections ?? []).map((c) => `jira:${c.connection_ref}`),
    ...(confluence?.connections ?? []).map((c) => `confluence:${c.connection_ref}`),
  ]);
  const githubLogin = github?.account?.login ?? "";
  const foundRows = found.rows.filter((row) => row.verb && !row.connected && !usedRefs.has(row.id)
    && !(row.provider === "github" && githubLogin && (githubLogin === row.account || githubLogin === `${row.site}:${row.account}`)));
  const toggle = (key: string) => setOpenRow((value) => value === key ? null : key);

  return (
    <div className="connections-pane prefs-column">
      <span ref={anchorRef} hidden />
      {error ? <SurfaceState error={error} onRetry={() => void load()} /> : null}
      {signinFailure ? <div className="connections-check-failed" role="alert"><StateChip wrap state="failure" label={signinFailure} /></div> : null}
      {checkFailed ? <div className="connections-check-failed" role="alert"><span>{checkFailed.providerId === "github" ? "GitHub" : checkFailed.providerId === "jira" ? "Jira" : "Confluence"}</span><StateChip wrap state="failure" label="Check failed" /><Button dense variant="secondary" disabled={recheckBusy !== null} onClick={() => void handleRecheck(checkFailed.providerId, checkFailed.subRef)}>Check</Button></div> : null}
      <SurfaceSection label="Services"><SurfaceLedger cols="accounts"><ul className="surface-ledger-rows connections-services">
      {github ? (
        <GitHubCard
          tool={github}
          onRecheck={() => void handleRecheck("github")}
          busy={recheckBusy === "github"}
          blocked={recheckBusy !== null}
          lead={github.state !== "connected" && github.state !== "signed_in"}
          open={openRow === "github"}
          onToggle={() => toggle("github")}
          onSignIn={github.state !== "unavailable" ? () => beginSignin("github", github.egress_host ?? "github.com") : undefined}
          signin={signin?.providerId === "github" ? signin : null}
          onSigninFinished={finishSignin}
        />
      ) : null}
      {jira ? (
        <AtlassianCards
          tool={jira}
          onRecheck={(ref) => void handleRecheck("jira", ref)}
          onAddAccount={(site, email) => handleAddAccount("jira", site, email)}
          onRemove={(conn) => void handleRemove("jira", conn)}
          busyRef={recheckBusy}
          onSignIn={(site, email, ref) => beginSignin("jira", site, email, ref)}
          signin={signin?.providerId === "jira" ? signin : null}
          onSigninFinished={finishSignin}
        />
      ) : null}
      {confluence ? (
        <AtlassianCards
          tool={confluence}
          onRecheck={(ref) => void handleRecheck("confluence", ref)}
          onAddAccount={(site, email) => handleAddAccount("confluence", site, email)}
          onRemove={(conn) => void handleRemove("confluence", conn)}
          busyRef={recheckBusy}
          onSignIn={(site, email, ref) => beginSignin("confluence", site, email, ref)}
          signin={signin?.providerId === "confluence" ? signin : null}
          onSigninFinished={finishSignin}
        />
      ) : null}
      </ul></SurfaceLedger></SurfaceSection>
      {removed ? <div className="connections-check-failed" data-testid="connections-removed"><span>{removed.provider === "jira" ? "Jira" : "Confluence"} · {removed.site}</span><StateChip wrap state="idle" label="Removed"/><Button dense variant="secondary" onClick={() => void undoRemove()}>Undo</Button></div> : null}
      {removeFailed ? <div className="connections-check-failed" role="alert"><StateChip wrap state="failure" label="Not removed"/></div> : null}
      {foundRows.length ? <SurfaceSection label="Found on this Mac"><SurfaceLedger cols="accounts"><ul className="surface-ledger-rows" data-testid="connections-found">
        {foundRows.map((row) => {
          const st = found.states[row.id];
          return <SurfaceLedgerRow key={row.id} data-testid={`connections-found-${row.id}`} wrap expands={false}
            lead={<ServiceGlyph provider={row.provider}/>}
            primary={<span className="connections-tool-identity"><strong className="connections-tool-label">{PROVIDER_NAME[row.provider]}</strong><AccountEmail email={row.account}/><span className="connections-tool-summary connections-site">{row.site}</span></span>}
            cells={st?.kind === "refused" ? <span className="surface-ledger-cells connections-tool-chips"><StateChip wrap state="failure" label={`Does not work: ${st.reason}`}/></span> : undefined}
            trailing={<span className="connections-check-action"><HostChip site={row.egress_host}/><Button dense variant="secondary" loading={st?.kind === "busy"} onClick={() => void useFound(row)}>Use</Button></span>}/>;
        })}
      </ul></SurfaceLedger></SurfaceSection> : null}
      <SurfaceSection label="Calendar"><SurfaceLedger cols="accounts"><ul className="surface-ledger-rows">
      <CalendarCard
        tool={calendar}
        onChoose={() => setCalendarOpen((value) => !value)}
      />
      </ul></SurfaceLedger>
      {calendarOpen ? <CalendarChooser onCalendarChanged={async () => { await onCalendarChanged?.(); await load(); }} onBeforeCalendarChange={onBeforeCalendarChange} /> : null}
      </SurfaceSection>
      {/* Betterment setup ST1: the `Runs on N of 7 assigned` row is parked
          (pages/cores/_parked/ConnectionsModelsCard.tsx); Engines owns it. */}
    </div>
  );
}

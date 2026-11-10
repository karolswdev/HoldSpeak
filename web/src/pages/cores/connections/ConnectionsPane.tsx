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
  DotWord, ListView, PaneInspector, PaneActions, type ListVerb,
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

// HS-S53: the account state words have one owner, next to the destination
// form that also shows them; re-exported here for older callers.
import { chipLabel } from "../../../features/channels/accountChip";
export { chipLabel };
import { CalendarCard as CalendarSetupCard } from "../../../desk/firstrun/CalendarCard";
import { useCalendarStep } from "../../../desk/firstrun/calendarStep";

/* ── State mapping (D1 + D6) ── */

/** PHILO-17 U29: the producer names a missing sign-in (`owner_action_required`:
 *  github_provider / jira_provider classify the CLI's own answer); the face
 *  reads that state, never the error text. */
export function notSignedIn(state: ConnectionState): boolean {
  return state === "owner_action_required";
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

/** Window grammar: the age of a row's own check as a quiet sentence-case
 *  fact after its state word (`checked 11 days ago`). */
export function checkedWords(
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
  const ago = (n: number, unit: string) => `checked ${n} ${unit}${n === 1 ? "" : "s"} ago`;
  if (seconds < 60) return "checked just now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return ago(minutes, "minute");
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return ago(hours, "hour");
  return ago(Math.floor(hours / 24), "day");
}

type SigninRun = {
  host?: string;
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
      {run.host ? <EgressChip label={run.host} scope="cloud" /> : null}
      <div className="surface-terminal-well" data-testid={`connections-signin-terminal-${run.runId}`}>
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


export function CommandWell({
  hint,
}: {
  hint: string;
}) {
  const [copy, setCopy] = useState<"Copy" | "Copied" | "Copy failed">("Copy");
  return (
    <SurfaceWell>
      <div className="surface-pane-actions">
        <code className="surface-command-code">{hint}</code>
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

type AccountDraft = { site: string; email: string };

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
    <div className="surface-preference-pane" data-testid={`connections-add-${provider}`}>
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
      <div className="surface-pane-actions">
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


export interface ConnectionsFoot { egressHost: string | undefined; checkedAt: string | undefined }

/** Services use the same selection list as every preference list. */
export function ConnectionsPane({ onFooterUpdate, focusProvider, extraVerbs = [], onAttention }: {
  onFooterUpdate: (foot: ConnectionsFoot) => void;
  extraVerbs?: ListVerb[];
  onAttention?: (reason: string | null) => void;
  onOpenModule?: (id: string) => void;
  focusProvider?: string | null;
  onCalendarChanged?: () => Promise<void>;
  onBeforeCalendarChange?: () => Promise<boolean>;
}) {
  const [data, setData] = useState<ConnectionsResponse | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [picked, pick] = useState<string | null>(focusProvider ?? null);
  const [adding, add] = useState<"jira" | "confluence" | null>(null);
  const [drafts, setDrafts] = useState({ jira: { site: "", email: "" }, confluence: { site: "", email: "" } });
  const [signin, setSignin] = useState<SigninRun | null>(null);
  const pending = useRef(false);
  const generation = useRef(0);
  const load = useCallback(async () => {
    const at = ++generation.current;
    try {
      let answer = await fetchConnections();
      if (at !== generation.current) return;
      setData(answer); setError("");
      // The declared recheck operation owns probes. An age supplied by the
      // hub wins over the browser clock; missing and stale checks run here.
      const expired = (row: { checked_age_seconds?: number; last_checked_at?: string }) =>
        (row.checked_age_seconds ?? (row.last_checked_at ? (Date.now() - Date.parse(row.last_checked_at)) / 1000 : Infinity)) > 300;
      const stale = answer.tools.filter((tool) => ["github", "jira", "confluence"].includes(tool.provider_id)
        && (expired(tool) || tool.connections?.some(expired)));
      for (const tool of stale) {
        try {
          const checked = await recheckProvider(tool.provider_id);
          if (at !== generation.current) return;
          if (checked) answer = { tools: answer.tools.map((row) => row.provider_id === checked.provider_id ? checked : row) };
          setData(answer);
        } catch { if (at === generation.current) setError("Account check failed"); }
      }
      onFooterUpdate({ egressHost: undefined, checkedAt: undefined });
    } catch { if (at === generation.current) setError("Accounts not read"); }
  }, [onFooterUpdate]);
  useEffect(() => {
    void load();
    const read = () => { if (!pending.current) void load(); };
    const timer = window.setInterval(read, 300_000);
    window.addEventListener(ACCOUNTS_CHANGED, read);
    return () => { ++generation.current; window.clearInterval(timer); window.removeEventListener(ACCOUNTS_CHANGED, read); };
  }, [load]);
  const act = async (work: () => Promise<void>) => {
    if (pending.current) return false;
    pending.current = true; setBusy(true); setError(""); ++generation.current;
    try { await work(); await load(); window.dispatchEvent(new Event(ACCOUNTS_CHANGED)); return true; }
    catch (error) { setError(readableError(error)); return false; }
    finally { pending.current = false; setBusy(false); }
  };
  const rows = (data?.tools ?? []).filter((tool) => ["github", "jira", "confluence"].includes(tool.provider_id)).flatMap((tool) => {
    const name = PROVIDER_NAME[tool.provider_id as keyof typeof PROVIDER_NAME] ?? tool.provider_id;
    const sub = tool.connections?.length ? tool.connections.map((conn) => ({ ...conn, provider: tool.provider_id, id: `${tool.provider_id}:${conn.connection_ref}`, ref: conn.connection_ref }))
      : [{ ...tool, provider: tool.provider_id, id: tool.provider_id, ref: undefined }];
    return sub.map((row) => ({ ...row, name }));
  });
  const attention = rows.find((row) => row.state === "owner_action_required" || row.state === "degraded");
  useEffect(() => { onAttention?.(error || (attention ? `${attention.name}: ${attention.state === "owner_action_required" ? "Sign in again" : "Not reachable"}` : null)); }, [error, attention?.id, attention?.state, onAttention]);
  const selected = (id?: string) => rows.find((row) => row.id === id);
  const signIn = async (id?: string) => {
    const row = selected(id); if (!row) return;
    await act(async () => {
      const run = await startSigninApi(row.provider, row.account?.site || row.egress_host || "github.com", row.account?.email);
      setSignin({ host: row.account?.site || row.egress_host || "github.com", providerId: row.provider, connectionRef: row.ref, runId: run.run_id, target: openTargetFromSignin(run.target) });
    });
  };
  const verbs: ListVerb[] = [
    { id: "add", label: "Add account", symbol: "+", enabled: () => !busy, run: () => {}, items: [
      { id: "github", label: "GitHub", run: () => void signIn("github") },
      { id: "jira", label: "Jira", run: () => add("jira") },
      { id: "confluence", label: "Confluence", run: () => add("confluence") },
    ] },
    { id: "remove", label: "Remove account", symbol: "−", key: "Delete", enabled: (row) => !busy && Boolean(selected(row?.id)?.ref), run: (row) => {
      const source = selected(row?.id); if (!source?.ref) return;
      void act(async () => { await removeAtlassianAccount(source.provider as "jira" | "confluence", source.ref!); pick(null); });
    } },
    { id: "signin", label: "Sign in…", key: "Enter", enabled: (row) => !busy && Boolean(row) && selected(row?.id)?.state !== "unavailable", run: (row) => void signIn(row?.id) },
    ...extraVerbs,
  ];
  return <>
    {error ? <PaneActions><span role="alert">{error}</span>{adding ? null : <Button dense onClick={() => void load()}>Retry</Button>}</PaneActions> : null}
    {!data ? <span role="status">Reading accounts…</span> : null}
    {adding ? <PaneInspector label={`Add ${PROVIDER_NAME[adding]} account`} onClose={() => add(null)}>
      <AddAccountFields compact provider={adding} busy={busy} draft={drafts[adding]} onDraftChange={(next) => setDrafts((current) => ({ ...current, [adding]: typeof next === "function" ? next(current[adding]) : next }))} onAdd={async (site, email) => {
        const ok = await act(async () => { await addAtlassianAccount(adding, site, email); });
        if (!ok) throw new Error("Account not added");
        add(null);
      }} />
    </PaneInspector> : signin ? <PaneInspector label="Sign in" onClose={() => setSignin(null)}>
      <SigninPane run={signin} onFinished={(answer) => { const run = signin; setSignin(null); if (answer.status === "failed") setError(answer.error || "Sign-in failed"); else void act(async () => { await recheckProvider(run.providerId, run.connectionRef); }); }} />
    </PaneInspector> : <ListView label="Services" ordered rows={rows.map((row) => ({ id: row.id, kind: "account", name: row.name,
      cells: { account: row.account?.site || (row.account as ConnectionTool["account"])?.login || row.account?.email || "—" },
      state: row.state === "connected" || row.state === "signed_in" ? undefined : {
        label: row.state === "owner_action_required" ? "Sign in again" : row.state === "unavailable" ? "Not available" : row.state === "degraded" ? "Not reachable" : "Not set up",
        tone: row.state === "owner_action_required" ? "fail" as const : "warn" as const,
      },
    }))} columns={[{ key: "name", word: "Service", track: "minmax(100px, 1fr)" }, { key: "account", word: "Account", track: "minmax(0, 2fr)" }, { key: "state", word: "State", track: "160px" }]}
      selectedId={picked} onSelect={pick} defaultVerb="signin" verbs={verbs} />}
  </>;
}

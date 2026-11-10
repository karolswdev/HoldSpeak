/* HS-S53: the ONE destination form (`DestForm`) and its draft rules.
 * Settings -> Connections -> Destinations and the Send sheet's inline Add
 * destination both consume it. It depends on lower contracts only: the
 * channels wire, the account wire types, the account chip words and the
 * public surface barrel. It never imports the Settings screen
 * (ConnectionsPane, Destinations) or the stateful Send module (SendWell);
 * `web/scripts/guard-architecture.mjs` checks that closure.
 * Moved from pages/cores/connections/Destinations.tsx; that module
 * re-exports these names.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  DotWord,
  EgressChip,
  GadgetGroup,
  GadgetRow,
  PadGadget,
  PaneActions,
  SecretRow,
  StateChip,
  StringGadget,
} from "../../desk/surface";
import type { ConnectionsResponse } from "../../pages/cores/connections/api";
import { accountChip } from "./accountChip";
import {
  DEFAULT_EMAIL_PROVIDER, EMAIL_PROVIDERS, SEND_WORDS, egressOf, keyNotSavedNext, refusedWord,
  wire, Refusal, type Channel, type Destination, type EmailProvider, type SaveBody,
} from "./channels";
import "./channels.css";
import { Token } from "../../desk/surface/Token";

const CHANNELS: { value: Channel; label: string }[] = [
  { value: "file", label: "Folder" },
  { value: "github", label: "GitHub comment" },
  { value: "jira", label: "Jira comment" },
  { value: "confluence", label: "Confluence blog post" },
  { value: "email", label: "Email" },
  { value: "slack", label: "Slack" },
];
/** Story 07: the email providers, from the one table (PHILO-15 04: Resend first, the default). */
const PROVIDERS = (Object.keys(EMAIL_PROVIDERS) as EmailProvider[]).map((p) => ({ value: p, label: EMAIL_PROVIDERS[p].label }));

export type Draft = {
  channel: Channel; name: string; nameTouched: boolean;
  folder: string; synced: boolean;
  repo: string; kind: "issue" | "pr"; number: string;
  jiraAccount: string; key: string;
  confAccount: string; space: string;
  provider: EmailProvider; fromEmail: string; fromName: string; emailRef: string; to: string; cc: string;
  /** Slack: his channel label, and the key_ref the webhook save returned (empty until he types it). */
  slackLabel: string; slackRef: string;
};
export const EMPTY: Draft = {
  channel: "file", name: "", nameTouched: false, folder: "", synced: false, repo: "", kind: "issue", number: "",
  jiraAccount: "", key: "", confAccount: "", space: "", provider: DEFAULT_EMAIL_PROVIDER, fromEmail: "", fromName: "", emailRef: "", to: "", cc: "",
  slackLabel: "", slackRef: "",
};

/** B3: the name he would type, from the target (editable). */
export function autoName(d: Pick<Draft, "channel" | "folder" | "repo" | "kind" | "number" | "key" | "space" | "to"> & Partial<Pick<Draft, "slackLabel">>): string {
  switch (d.channel) {
    case "file": return d.folder ? `Folder ${d.folder.split("/").filter(Boolean).pop() ?? ""}` : "";
    case "github": return d.repo && d.number ? `${d.repo} ${d.kind === "pr" ? "PR " : ""}#${d.number}` : "";
    case "jira": return d.key ? `Jira ${d.key}` : "";
    case "confluence": return d.space ? `Confluence space ${d.space}` : "";
    case "email": {
      const first = addresses(d.to)[0];
      return first ? `Email ${first}` : "";
    }
    case "slack": return d.slackLabel?.trim() ? `Slack ${d.slackLabel.trim()}` : "";
    default: return "";
  }
}
/** The keychain item's name for a sender, per provider (story 03's key_ref: letters, digits, `_ . @ -`). */
export const keyRef = (fromEmail: string, provider: EmailProvider = DEFAULT_EMAIL_PROVIDER) =>
  `${provider}-${fromEmail.trim().toLowerCase().replace(/[^a-z0-9_.@-]/g, "-")}`.slice(0, 100);
/** Presence follows the hub's provider/ref key slot, including legacy refs. */
export const emailKeyIdentity = (provider: string, ref: string) => `email:${provider}:${ref}`;
const addresses = (text: string) => text.split(/[,\r\n]/).map((a) => a.trim()).filter(Boolean);

/**
 * The admitted destination form. Settings (Destinations.tsx) and the Send
 * sheet's inline Add destination both seat this one form, so both have the
 * same validation and keychain semantics. Each host owns its account read,
 * its key cache and its Set up account action.
 */
export type DestFormProps = {
  conns: ConnectionsResponse | null; replaces?: string;
  /** The draft the form opens on (a new destination: EMPTY). */
  initial?: Draft; keys: Record<string, boolean>;
  accountsLoading: boolean; accountsReadError: boolean; onAccountsRetry: () => void;
  onKey: (ref: string, v: string, provider: EmailProvider) => Promise<string | null>;
  /** The webhook save: the minted key_ref, or the refusal code. */
  onSlackKey: (url: string) => Promise<{ keyRef: string } | { code: string }>;
  /** What a Check found about a key's cache identity: present or absent. */
  onKeyKnown: (ref: string, present: boolean) => void;
  /** `saved`: the destination the hub saved (its account as the hub found it). */
  onDone: (saved?: Destination) => void; onCancel?: () => void;
  /** Set up account: the host opens its own account control for `channel`.
   *  The form stays mounted, so the draft is kept. */
  onSetUpAccount: (channel: Channel) => void;
};

export function DestForm({ conns, accountsLoading, accountsReadError, onAccountsRetry, initial = EMPTY, replaces, keys, onKey, onSlackKey, onKeyKnown, onDone, onCancel, onSetUpAccount }: DestFormProps) {
  const [keyRefused, setKeyRefused] = useState<string | null>(null);
  const [keyChecking, setKeyChecking] = useState(false);
  const [d, setD] = useState<Draft>(initial);
  const [busy, setBusy] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const [emailCheck, setEmailCheck] = useState<{ identity: string; busy: boolean; code?: string } | null>(null);
  const emailRequest = useRef(0);
  const set = (patch: Partial<Draft>) => { setRefused(null); setD((x) => ({ ...x, ...patch })); };
  const name = d.nameTouched ? d.name : autoName(d);
  // The webhook is SET only when a save or a Check in this session confirmed it (Astra counsel r1 F1):
  // unknown is never SET. Edit on a saved row starts unknown and offers Check.
  const slackKnown: boolean | undefined = d.slackRef ? keys[d.slackRef] : false;
  const slackSet = slackKnown === true;
  // A saved key name is an identity, including names from older versions.
  // A changed sender/provider uses the current naming rule for its new key.
  const savedEmailIdentity = d.channel === "email" && initial.emailRef !== ""
    && d.provider === initial.provider
    && d.fromEmail.trim().toLowerCase() === initial.fromEmail.trim().toLowerCase();
  const ref = savedEmailIdentity ? initial.emailRef : keyRef(d.fromEmail, d.provider);
  const emailKey = emailKeyIdentity(d.provider, ref);
  const emailIdentity = `${d.channel}:${d.provider}:${d.fromEmail.trim().toLowerCase()}:${ref}`;
  const currentEmailIdentity = useRef(emailIdentity);
  currentEmailIdentity.current = emailIdentity;
  const checkEmailKey = useCallback(async () => {
    // Check names the saved destination, so it can establish only that
    // destination's original sender/provider/key identity.
    if (!replaces || !savedEmailIdentity) return;
    const request = ++emailRequest.current;
    setEmailCheck({ identity: emailIdentity, busy: true });
    try {
      const result = await wire.check(replaces);
      if (request !== emailRequest.current || currentEmailIdentity.current !== emailIdentity) return;
      const state = result.check.state;
      if (["ready", "sender_accepted", "sender_not_verified", "key_changed"].includes(state)) {
        onKeyKnown(emailKey, true);
        setEmailCheck(null);
      } else {
        // Locked/unavailable reads do not say that a key is absent.
        if (state === "email_key_missing") onKeyKnown(emailKey, false);
        setEmailCheck({ identity: emailIdentity, busy: false, code: state });
      }
    } catch (error) {
      if (request !== emailRequest.current || currentEmailIdentity.current !== emailIdentity) return;
      setEmailCheck({ identity: emailIdentity, busy: false, code: error instanceof Refusal ? error.code : "no_answer" });
    }
  }, [replaces, savedEmailIdentity, emailIdentity, emailKey, onKeyKnown]);
  const emailKnown = keys[emailKey];
  useEffect(() => {
    if (replaces && savedEmailIdentity && emailKnown === undefined) void checkEmailKey();
    return () => { emailRequest.current += 1; };
  }, [replaces, savedEmailIdentity, emailKnown, checkEmailKey]);
  const gh = conns?.tools.find((t) => t.provider_id === "github");
  const jiraConns = conns?.tools.find((t) => t.provider_id === "jira")?.connections ?? [];
  const confConns = conns?.tools.find((t) => t.provider_id === "confluence")?.connections ?? [];
  const pick = (v: string) => { const [site, email] = v.split("|"); return { site: site ?? "", email: email ?? "" }; };
  const jiraAcc = d.jiraAccount || (jiraConns[0] ? `${jiraConns[0].account.site}|${jiraConns[0].account.email}` : "");
  const confAcc = d.confAccount || (confConns[0] ? `${confConns[0].account.site}|${confConns[0].account.email}` : "");
  const account: Record<string, string | boolean> =
    d.channel === "github" ? { host: "github.com", login: String(gh?.account?.login ?? "") }
    : d.channel === "jira" ? pick(jiraAcc)
    : d.channel === "confluence" ? pick(confAcc)
    : d.channel === "email" ? { provider: d.provider, from_email: d.fromEmail, from_name: d.fromName, key_ref: ref, key_present: emailKnown === true }
    : d.channel === "slack" ? { key_ref: d.slackRef, ...(slackKnown === undefined ? {} : { key_present: slackKnown }) }
    : {};
  const eg = egressOf({ channel: d.channel, account, synced: d.synced });
  const acc = accountChip({ channel: d.channel, account }, conns);
  const accountsUnavailable = accountsLoading || accountsReadError;
  // Betterment send S1: a GitHub save asks gh itself (`gh api user`, the check
  // every send uses), so it never waits on the Accounts row's `gh auth status`.
  const dependsOnAccount = ["jira", "confluence"].includes(d.channel);
  const accountReadState = accountsLoading ? <span aria-busy="true">Reading accounts</span>
    : <><StateChip state="failure" label="Account read failed · Draft kept · Retry" wrap /><Button dense variant="secondary" onClick={onAccountsRetry}>Retry</Button></>;
  const missingAccount = d.channel === "jira" ? !jiraAcc : d.channel === "confluence" ? !confAcc : false;
  const valid = Boolean(name.trim()) && !missingAccount && (!dependsOnAccount || !accountsUnavailable) && (
    d.channel === "file" ? Boolean(d.folder.trim())
    : d.channel === "github" ? Boolean(d.repo.trim()) && Number.isInteger(Number(d.number)) && Number(d.number) > 0
    : d.channel === "jira" ? Boolean(d.key.trim())
    : d.channel === "confluence" ? Boolean(d.space.trim())
    : d.channel === "email" ? Boolean(d.fromEmail.trim()) && addresses(d.to).length > 0 && emailKnown === true
    : Boolean(d.slackLabel.trim()) && Boolean(d.slackRef) && slackKnown !== false
  );
  const save = async () => {
    if (!valid || busy) return;
    // Slack: no webhook typed, nothing to save (the hub would store a row that cannot post).
    if (d.channel === "slack" && slackKnown === false) { setRefused("slack_webhook_missing"); return; }
    setBusy(true); setRefused(null);
    const base = { name, channel: d.channel, ...(replaces ? { replaces } : {}) };
    const body: SaveBody =
      d.channel === "file" ? { ...base, folder: d.folder, synced: d.synced }
      : d.channel === "github" ? { ...base, host: "github.com", repo: d.repo.trim(), kind: d.kind, number: Number(d.number) || 0 }
      : d.channel === "jira" ? { ...base, ...pick(jiraAcc), key: d.key.trim() }
      : d.channel === "confluence" ? { ...base, ...pick(confAcc), space_id: d.space.trim() }
      : d.channel === "slack" ? { ...base, key_ref: d.slackRef, channel_label: d.slackLabel.trim() }
      : { ...base, provider: d.provider, from_email: d.fromEmail.trim(), from_name: d.fromName.trim(),
          key_ref: ref, to: addresses(d.to), cc: addresses(d.cc) };
    try {
      onDone(await wire.save(body));
    } catch (e) {
      setRefused(e instanceof Refusal ? e.code : "no_answer");
    } finally { setBusy(false); }
  };
  return (
    <div className="dest-form" data-testid="dest-form" data-channel={d.channel}>
      <GadgetGroup label={replaces ? "Edit destination" : "New destination"} material="inset" actions={
        <div data-testid="dest-form-verbs"><PaneActions>
          {onCancel ? <Button dense variant="ghost" onClick={onCancel} data-testid="dest-cancel">Cancel</Button> : null}
          <Button dense variant="primary" disabled={!valid} loading={busy} onClick={() => void save()} data-testid="dest-save">Save</Button>
          <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
          {refused ? (
            <span className="send-line" data-testid="dest-refused" data-code={refused}>
              <StateChip state="failure" label="REFUSED" />
              <Token className="surface-token" data-chip>{refusedWord(refused)}</Token>
            </span>
          ) : null}
        </PaneActions></div>
      }>
      {replaces ? null : (
        <GadgetRow label="Channel" controlWidth="standard">
          <CycleGadget label="Channel" value={d.channel} options={CHANNELS} onChange={(v) => set({ ...EMPTY, channel: v as Channel })} />
        </GadgetRow>
      )}
      {d.channel === "file" ? (<>
        <GadgetRow controlWidth="standard" label="Folder"><StringGadget label="Folder" value={d.folder} onChange={(v) => set({ folder: v })} placeholder="/Users/you/Reports" inputProps={{ "data-testid": "dest-folder" } as never} /></GadgetRow>
        <GadgetRow controlWidth="standard" label="Synced"><CheckGadget variant="token" label="Synced" checked={d.synced} onChange={(v) => set({ synced: v })} /></GadgetRow>
      </>) : null}
      {d.channel === "github" ? (<>
        <GadgetRow controlWidth="standard" label="Account">
          <span className="send-line" data-testid="dest-github-account">
            <Token className="surface-token send-literal" data-chip>{gh?.account?.login ? `@${gh.account.login}` : "READ FROM gh AT SAVE"}</Token>
          </span>
        </GadgetRow>
        <GadgetRow controlWidth="standard" label="Repository"><StringGadget label="Repository" value={d.repo} onChange={(v) => set({ repo: v })} placeholder="owner/repo" inputProps={{ "data-testid": "dest-repo" } as never} /></GadgetRow>
        <GadgetRow controlWidth="standard" label="Kind"><CycleGadget label="Kind" value={d.kind} options={[{ value: "issue", label: "Issue" }, { value: "pr", label: "Pull request" }]} onChange={(v) => set({ kind: v as "issue" | "pr" })} /></GadgetRow>
        <GadgetRow controlWidth="short" label="Number"><StringGadget label="Number" value={d.number} onChange={(v) => set({ number: v })} placeholder="42" inputProps={{ "data-testid": "dest-number", inputMode: "numeric" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "jira" ? (<>
        <GadgetRow controlWidth="standard" label="Account">
          <span className="send-line">
            {accountsUnavailable ? accountReadState : jiraConns.length ? (
              <CycleGadget label="Jira account" value={jiraAcc} onChange={(v) => set({ jiraAccount: v })}
                options={jiraConns.map((c) => ({ value: `${c.account.site}|${c.account.email}`, label: `${c.account.site} · ${c.account.email}` }))} />
            ) : <><Token className="surface-token" data-chip>No Jira account</Token><Button dense variant="secondary" onClick={() => onSetUpAccount(d.channel)}>Set up account</Button></>}
            {!accountsUnavailable && acc && jiraConns.length ? <StateChip state={acc.state} label={acc.label} /> : null}
          </span>
        </GadgetRow>
        <GadgetRow controlWidth="standard" label="Work item"><StringGadget label="Work item" value={d.key} onChange={(v) => set({ key: v })} placeholder="PAY-118" inputProps={{ "data-testid": "dest-key" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "confluence" ? (<>
        <GadgetRow controlWidth="standard" label="Account">
          <span className="send-line">
            {accountsUnavailable ? accountReadState : confConns.length ? (
              <CycleGadget label="Confluence account" value={confAcc} onChange={(v) => set({ confAccount: v })}
                options={confConns.map((c) => ({ value: `${c.account.site}|${c.account.email}`, label: `${c.account.site} · ${c.account.email}` }))} />
            ) : <><Token className="surface-token" data-chip>No Confluence account</Token><Button dense variant="secondary" onClick={() => onSetUpAccount(d.channel)}>Set up account</Button></>}
            {!accountsUnavailable && acc && confConns.length ? <StateChip state={acc.state} label={acc.label} /> : null}
          </span>
        </GadgetRow>
        <GadgetRow controlWidth="standard" label="Space id"><StringGadget label="Space id" value={d.space} onChange={(v) => set({ space: v })} placeholder="98304" inputProps={{ "data-testid": "dest-space", inputMode: "numeric" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "email" ? (<>
        <GadgetRow controlWidth="standard" label="Provider"><CycleGadget label="Provider" value={d.provider} options={PROVIDERS} onChange={(v) => { setKeyRefused(null); set({ provider: v as EmailProvider }); }} /></GadgetRow>
        <GadgetRow controlWidth="standard" label="From"><StringGadget label="From" value={d.fromEmail} onChange={(v) => set({ fromEmail: v })} placeholder="you@company.com" inputProps={{ "data-testid": "dest-from" } as never} /></GadgetRow>
        <GadgetRow controlWidth="standard" label="From name"><StringGadget label="From name" value={d.fromName} onChange={(v) => set({ fromName: v })} placeholder="Your name" /></GadgetRow>
        <div className="dest-secret" data-testid="dest-key-row">
          <SecretRow label={`${EMAIL_PROVIDERS[d.provider].label} key`} configured={emailKnown === true}
            onReplace={(v) => {
              emailRequest.current += 1;
              setEmailCheck(null); setKeyRefused(null);
              void onKey(ref, v, d.provider).then(setKeyRefused);
            }} />
          {replaces && savedEmailIdentity && emailKnown !== true ? (
            <span className="send-line" data-testid="dest-email-key-check" aria-busy={emailCheck?.identity === emailIdentity && emailCheck.busy}>
              {emailCheck?.identity === emailIdentity && emailCheck.busy ? <span role="status">Reading key</span>
                : emailCheck?.identity === emailIdentity && emailCheck.code ? <>
                  <StateChip state={emailCheck.code === "email_key_missing" ? "warning" : "failure"}
                    label={emailCheck.code === "email_key_missing" ? "NO KEY" : "CANNOT READ KEY"} />
                  {emailCheck.code === "email_key_missing" ? null : <Token className="surface-token" data-chip>{refusedWord(emailCheck.code)}</Token>}
                </> : null}
              <Button dense variant="ghost" loading={emailCheck?.identity === emailIdentity && emailCheck.busy}
                onClick={() => void checkEmailKey()}>{emailCheck?.identity === emailIdentity && emailCheck.code ? "Retry" : "Check"}</Button>
            </span>
          ) : null}
          {keyRefused ? (
            <span className="send-line" data-testid="dest-key-refused" data-code={keyRefused} title={refusedWord(keyRefused)}>
              <DotWord tone="fail">{`${SEND_WORDS.keyNotSaved} · ${keyNotSavedNext(keyRefused)}`}</DotWord>
            </span>
          ) : null}
        </div>
        <GadgetRow controlWidth="standard" label="To"><PadGadget label="To" value={d.to} onChange={(v) => set({ to: v })} placeholder={"a@company.com\nb@company.com"} autoGrow /></GadgetRow>
        <GadgetRow controlWidth="standard" label="Cc"><PadGadget label="Cc" value={d.cc} onChange={(v) => set({ cc: v })} placeholder="c@company.com" autoGrow /></GadgetRow>
      </>) : null}
      {d.channel === "slack" ? (<>
        <div className="dest-secret" data-testid="dest-key-row">
          <SecretRow label="Webhook" configured={slackSet}
            onReplace={(v) => {
              setKeyRefused(null);
              void onSlackKey(v).then((r) => ("keyRef" in r ? set({ slackRef: r.keyRef }) : setKeyRefused(r.code)));
            }} />
          {slackKnown === false ? (
            <span className="send-line" data-testid="dest-key-missing">
              <StateChip state="warning" label="NO WEBHOOK" />
            </span>
          ) : null}
          {replaces && d.slackRef && slackKnown === undefined ? (
            <Button dense variant="ghost" loading={keyChecking} data-testid="dest-key-check"
              onClick={() => {
                setKeyChecking(true);
                void wire.check(replaces)
                  .then((r) => { if (r.check.state === "ready" || r.check.state === "slack_webhook_missing") onKeyKnown(d.slackRef, r.check.state === "ready"); else setKeyRefused(r.check.state); })
                  .catch((e) => setKeyRefused(e instanceof Refusal ? e.code : "no_answer"))
                  .finally(() => setKeyChecking(false));
              }}>Check</Button>
          ) : null}
          {keyRefused ? (
            <span className="send-line" data-testid="dest-key-refused" data-code={keyRefused} title={refusedWord(keyRefused)}>
              <DotWord tone="fail">{`${SEND_WORDS.keyNotSaved} · ${keyNotSavedNext(keyRefused)}`}</DotWord>
            </span>
          ) : null}
        </div>
        <GadgetRow controlWidth="standard" label="Channel name"><StringGadget label="Channel name" value={d.slackLabel} onChange={(v) => set({ slackLabel: v })} placeholder="#leads" inputProps={{ "data-testid": "dest-slack-label" } as never} /></GadgetRow>
      </>) : null}
      <GadgetRow controlWidth="standard" label="Name"><StringGadget label="Name" value={name} onChange={(v) => set({ name: v, nameTouched: true })} placeholder="Name" inputProps={{ "data-testid": "dest-name" } as never} /></GadgetRow>
      </GadgetGroup>
    </div>
  );
}

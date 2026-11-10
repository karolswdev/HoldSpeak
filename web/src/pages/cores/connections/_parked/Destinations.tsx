// Parked: destination row verbs replaced by shared selection actions.
/* PHILO-10-04: the Destinations group in Settings -> Connections, under
 * Tools (the accounts each destination uses live in Tools, right above).
 * Built to the owner's ratified canvas (assets/story-04-destinations-canvas/,
 * "Ratify as drawn", 2026-09-29: B1 here; B2 the Room's Add destination
 * arrives AT the group with the form open; B3 the name fills from the target
 * and stays editable). Library species only: GadgetGroup, GadgetRow,
 * CycleGadget, StringGadget, CheckGadget, SecretRow, FoldGadget,
 * SurfaceLedger, SurfaceLedgerRow, StateChip, EgressChip, Button,
 * ConfirmVerb.
 *
 * - A row never changes its target. Edit = Save makes a NEW row and PARKS
 *   the old one (`replaces`); Remove = park. Parked rows keep their history
 *   (the PARKED fold).
 * - The key is typed once into the OS keychain and never shown again (SET /
 *   NOT SET); the face knows only present or absent.
 * - A read that gets no answer says CANNOT READ DESTINATIONS + Retry, never
 *   the empty add form. A refused key save says KEY NOT SAVED + why.
 * - Email Check reports the sender's verification, never the key alone.
 * - PHILO-11-05 (canvas D1-D4, design section 5): Slack is the sixth channel.
 *   The webhook URL is the credential: a SecretRow saved through the HTTP-only
 *   `channel.save_slack_webhook` (the hub mints the key_ref), never shown
 *   again. The channel name is his label; the name fills from it. Check says
 *   what is known without a post (WEBHOOK SET · HOST OK); it never posts.
 * - No counter of zero: the group head counts only when there is a row.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import {
  ConfirmVerb,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  StateChip,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "../../../desk/surface";
import type { ConnectionsResponse } from "./api";
import { ACCOUNTS_CHANGED, fetchConnections } from "./api";
import "./connections.css";
import { accountChip } from "../../../features/channels/accountChip";
import { DestForm, EMPTY, emailKeyIdentity, type Draft } from "../../../features/channels/DestinationForm";
import {
  CHANNEL_WORD, DEFAULT_EMAIL_PROVIDER, DEST_FOCUS, SEND_WORDS, egressOf, emailProvider, refusedWord, stamp,
  takeDestinationsFocus, targetToken, wire, Refusal, type Channel, type Destination, type EmailProvider,
} from "../../../features/channels/channels";
import "../../../features/channels/channels.css";
import { Token } from "../../../desk/surface/Token";

// HS-S53: the form has one owner, features/channels/DestinationForm.tsx.
// These names stay importable from here; they forward to that owner.
export { DestForm, EMPTY, autoName, keyRef, type DestFormProps, type Draft } from "../../../features/channels/DestinationForm";

/** A destination's channel in sentence case on its row (the Send faces keep
 *  their own CHANNEL_WORD). */
const CHANNEL_NAME: Record<string, string> = {
  file: "File", github: "GitHub", jira: "Jira", confluence: "Confluence", email: "Email", slack: "Slack",
};

function fromDestination(d: Destination): Draft {
  const t = d.target, a = d.account;
  return {
    ...EMPTY, channel: d.channel, name: d.name, nameTouched: true,
    folder: String(t.folder ?? ""), synced: d.synced,
    repo: String(t.repo ?? ""), kind: t.kind === "pr" ? "pr" : "issue", number: t.number != null ? String(t.number) : "",
    jiraAccount: d.channel === "jira" ? `${a.site}|${a.email}` : "", key: String(t.key ?? ""),
    confAccount: d.channel === "confluence" ? `${a.site}|${a.email}` : "", space: String(t.space_id ?? ""),
    provider: a.provider === "resend" ? "resend" : "sendgrid",
    fromEmail: String(a.from_email ?? ""), fromName: String(a.from_name ?? ""), emailRef: String(a.key_ref ?? ""),
    to: [t.to as unknown].flat().filter(Boolean).join("\n"), cc: [t.cc as unknown].flat().filter(Boolean).join("\n"),
    // A new webhook is a new destination: Edit keeps this key_ref until he types a new URL (design section 5).
    slackLabel: String(t.channel_label ?? ""), slackRef: d.channel === "slack" ? String(a.key_ref ?? "") : "",
  };
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="send-field">
      <dt className="surface-token">{label}</dt>
      <dd>{value || "—"}</dd>
    </div>
  );
}

function detailFields(d: Destination, keyKnown?: boolean): [string, string][] {
  const t = d.target, a = d.account;
  const base: [string, string][] = [["Channel", CHANNEL_WORD[d.channel] ?? d.channel]];
  switch (d.channel) {
    case "file": return [...base, ["Folder", String(t.folder)], ["Synced", d.synced ? "YES" : "NO"]];
    case "github": return [...base, ["Account", `@${a.login} · ${a.host}`], ["Repository", String(t.repo)], [t.kind === "pr" ? "Pull request" : "Issue", `#${t.number}`]];
    case "jira": return [...base, ["Account", `${a.email} · ${a.site}`], ["Work item", String(t.key)]];
    case "confluence": return [...base, ["Account", `${a.email} · ${a.site}`], ["Space id", String(t.space_id)]];
    case "email": return [...base, ["Provider", emailProvider(a).label], ["From", a.from_name ? `${a.from_name} <${a.from_email}>` : String(a.from_email)],
      ["To", [t.to as unknown].flat().join(", ")], ["Cc", [t.cc as unknown].flat().join(", ") || "—"]];
    // The face knows the webhook only as present or absent, and only when known: never the URL.
    case "slack": return [...base, ["Channel name", String(t.channel_label ?? "")],
      ["Webhook", keyKnown === true ? "SET · hooks.slack.com" : keyKnown === false ? "NOT SET" : "hooks.slack.com"]];
    default: return base;
  }
}

/** The Check result, by the hub's check state. */
function CheckChip({ state, channel, answeredAt }: { state: string; channel: Channel; answeredAt?: string | null }) {
  // Email (B11): Check reports what the provider last answered for this sender, and when -- never a fresh
  // verification (Codex Astra r2 on #697), never the key alone.
  if (channel === "email") {
    const when = answeredAt ? <Token className="surface-token" data-chip>{`LAST SEND ${stamp(answeredAt)}`}</Token> : null;
    if (state === "ready") return <StateChip state="idle" label="SENDER NOT CHECKED" />;
    if (state === "sender_accepted") return <><StateChip state="success" label="SENDER ACCEPTED" />{when}</>;
    if (state === "sender_not_verified") return <><StateChip state="failure" label="SENDER NOT VERIFIED" />{when}</>;
    if (state === "key_changed") return <StateChip state="warning" label="NOT CHECKED SINCE KEY CHANGE" />;
  }
  // Slack (design section 5): what is known without a post -- the webhook is in the keychain and its
  // host passes the rule. Check never posts a test message.
  if (channel === "slack" && state === "ready") return <StateChip state="success" label="WEBHOOK SET · HOST OK" />;
  if (state === "ready" || state === "connected") return <StateChip state="success" label="CHECKED" />;
  const words: Record<string, string> = {
    changed: "DESTINATION CHANGED", missing: "NO FOLDER", not_writable: "NOT WRITABLE", parked: "DESTINATION PARKED",
    owner_action_required: "NOT SIGNED IN", never_checked: "NEVER CHECKED", unavailable: "UNAVAILABLE",
    degraded: "DEGRADED", not_configured: "NOT SET UP", no_answer: "NO ANSWER",
  };
  return <StateChip state="warning" label={words[state] ?? refusedWord(state)} />;
}

export function Destinations() {
  const [rows, setRows] = useState<Destination[] | null>(null);
  const [readFailed, setReadFailed] = useState(false);
  const [arrive, setArrive] = useState(false);
  const groupRef = useRef<HTMLDivElement>(null);
  const [conns, setConns] = useState<ConnectionsResponse | null>(null);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsReadError, setAccountsReadError] = useState(false);
  const onAccountsRetry = () => window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
  // Settings: Accounts and Destinations share this module. Open the existing
  // account control above the form, so the destination draft stays mounted.
  const setUpAccount = (channel: Channel) => {
    const module = groupRef.current?.closest(".prefs-module") ?? document;
    const row = module.querySelector<HTMLElement>(`[data-testid="connections-${channel}"]`)
      ?? module.querySelector<HTMLElement>(`[data-testid^="connections-${channel}-conn-"]`);
    const add = module.querySelector<HTMLButtonElement>(`[data-testid="connections-add-open-${channel}"]`);
    const show = module.querySelector<HTMLButtonElement>(`[data-testid="connections-${channel}-show"]`);
    if (add && add.getAttribute("aria-expanded") !== "true") add.click();
    if (show && show.getAttribute("aria-expanded") !== "true") show.click();
    (row ?? add)?.scrollIntoView?.({ block: "center" });
    const target = module.querySelector<HTMLInputElement>(`[data-testid="connections-add-${channel}"] input`)
      ?? show ?? row?.querySelector<HTMLButtonElement>("button:not([disabled])") ?? add;
    target?.focus({ preventScroll: true });
  };
  useEffect(() => {
    let live = true;
    const read = () => {
      setAccountsLoading(true);
      void fetchConnections().then((answer) => { if (live) { setConns(answer); setAccountsReadError(false); } })
        .catch(() => { if (live) { setConns(null); setAccountsReadError(true); } })
        .finally(() => { if (live) setAccountsLoading(false); });
    };
    read();
    window.addEventListener("focus", read);
    window.addEventListener(ACCOUNTS_CHANGED, read);
    return () => { live = false; window.removeEventListener("focus", read); window.removeEventListener(ACCOUNTS_CHANGED, read); };
  }, []);
  const [open, setOpen] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [keys, setKeys] = useState<Record<string, boolean>>({});
  const [checks, setChecks] = useState<Record<string, { busy: boolean; state?: string; at?: string; answeredAt?: string | null }>>({});
  const [removeBusy, setRemoveBusy] = useState<string | null>(null);
  // A Remove the hub did not confirm: the row stays open, named, with Retry
  // (Codex Astra r1 F2 on #697). Never closed as if it were parked.
  const [removeFailed, setRemoveFailed] = useState<Record<string, string>>({});
  const remove = (id: string) => {
    setRemoveBusy(id);
    setRemoveFailed((m) => { const n = { ...m }; delete n[id]; return n; });
    void wire.park(id)
      .then(() => { setOpen(null); reload(); })
      .catch((e) => setRemoveFailed((m) => ({ ...m, [id]: e instanceof Refusal ? e.code : "no_answer" })))
      .finally(() => setRemoveBusy(null));
  };
  const reload = useCallback(() => void wire.destinations(true).then((r) => {
    setRows(r); setReadFailed(false);
    setKeys((k) => ({
      ...k,
      ...Object.fromEntries(r.filter((d) => d.channel === "email" && typeof d.account.key_present === "boolean")
        .map((d) => [emailKeyIdentity(String(d.account.provider ?? DEFAULT_EMAIL_PROVIDER), String(d.account.key_ref)), !!d.account.key_present])),
    }));
  }).catch(() => setReadFailed(true)), []);
  useEffect(() => {
    reload();
    const want = () => { if (takeDestinationsFocus()) setArrive(true); };
    want();
    window.addEventListener(DEST_FOCUS, want);
    return () => window.removeEventListener(DEST_FOCUS, want);
  }, [reload]);
  // B2, the arrival: once the group has drawn, bring it into view with the add form open.
  useEffect(() => {
    if (!arrive || (rows === null && !readFailed)) return;
    setArrive(false);
    setOpen(null); setEditing(null); setAdding(true);
    requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
  }, [arrive, rows, readFailed]);
  const onKey = (ref: string, v: string, provider: EmailProvider): Promise<string | null> => wire.saveKey(ref, v, provider)
    .then(() => { setKeys((k) => ({ ...k, [emailKeyIdentity(provider, ref)]: true })); return null; })
    .catch((e) => (e instanceof Refusal ? e.code : "no_answer"));
  const onSlackKey = (url: string): Promise<{ keyRef: string } | { code: string }> => wire.saveSlackWebhook(url)
    .then((r) => { setKeys((k) => ({ ...k, [r.key_ref]: true })); return { keyRef: r.key_ref }; })
    .catch((e) => ({ code: e instanceof Refusal ? e.code : "no_answer" }));
  const onKeyKnown = useCallback((ref: string, present: boolean) => setKeys((k) => ({ ...k, [ref]: present })), []);
  /** A Slack row's webhook, as far as this face knows it (a save or a Check): true, false or unknown. */
  const slackKey = (d: Destination): boolean | undefined =>
    d.channel === "slack" ? keys[String(d.account.key_ref ?? "")] : undefined;
  if (readFailed) {
    return (
      <div className="connections-destinations" data-send="destinations" data-testid="destinations" ref={groupRef}>
        <GadgetGroup label="Destinations">
          <div className="send-verbs" data-testid="dest-unreadable">
            <StateChip state="failure" label={`${SEND_WORDS.cannotRead} DESTINATIONS`} />
            <Button dense variant="ghost" data-testid="dest-unreadable-retry" onClick={reload}>{SEND_WORDS.retry}</Button>
          </div>
        </GadgetGroup>
      </div>
    );
  }
  // The first read is out: nothing drawn yet, but still reading (aria-busy), so
  // the group's late arrival is not read as a settled window moving.
  if (rows === null) return <span hidden aria-busy="true" data-testid="dest-reading" />;
  const active = rows.filter((d) => d.state === "active");
  const parked = rows.filter((d) => d.state === "parked");
  const form = (
    <DestForm conns={conns} accountsLoading={accountsLoading} accountsReadError={accountsReadError} onAccountsRetry={onAccountsRetry} initial={EMPTY} keys={keys} onKey={onKey} onSlackKey={onSlackKey} onKeyKnown={onKeyKnown} onSetUpAccount={setUpAccount}
      onDone={(saved) => {
        // PHILO-10-07: after Save the form closes; the saved row stays in view (at 393 the closed form
        // otherwise leaves the list above the window).
        setAdding(false); reload();
        // Betterment send S1: a saved GitHub row opens, so its Account line shows the login gh named.
        if (saved?.channel === "github") setOpen(saved.id);
        requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
      }}
      onCancel={active.length ? () => setAdding(false) : undefined} />
  );
  return (
    <div className="connections-destinations" data-send="destinations" data-testid="destinations" ref={groupRef}>
      <GadgetGroup label={active.length ? `Destinations ${active.length}` : "Destinations"} actions={active.length === 0 || adding ? undefined : (
        // Window grammar: the group's verb sits on its caption line.
        <div className="send-verbs" data-testid="dest-add-line">
          <Button dense variant="secondary" data-testid="dest-add" onClick={() => { setOpen(null); setAdding(true); }}>Add destination</Button>
        </div>
      )}>
        {active.length ? (
          <SurfaceLedger count="" cols="account-destinations">
            <ul className="surface-ledger-rows" data-testid="dest-list">
              {active.map((d) => {
                const eg = egressOf(d);
                const known = slackKey(d);
                const acc = (accountsLoading || accountsReadError) && ["github", "jira", "confluence"].includes(d.channel) ? null
                  : accountChip(known === undefined ? d : { ...d, account: { ...d.account, key_present: known } }, conns);
                const c = checks[d.id];
                return (
                  <SurfaceLedgerRow key={d.id} data-testid="dest-row" wrap open={open === d.id}
                    lineLabel={`${d.name}, ${CHANNEL_WORD[d.channel] ?? d.channel}`}
                    onToggle={() => { setEditing(null); setOpen(open === d.id ? null : d.id); }}
                    lead={<span className="send-pick" aria-hidden="true">{open === d.id ? "▾" : "▸"}</span>}
                    primary={<span className="connections-tool-identity"><strong className="connections-tool-label" data-destination={d.name}>{d.name}</strong><span className="connections-tool-summary send-target">{targetToken(d.channel, d.target)}</span></span>}
                    cells={<span className="surface-ledger-cells connections-tool-chips"><span className="connections-tool-summary">{CHANNEL_NAME[d.channel] ?? d.channel}</span>{acc ? <StateChip state={acc.state} label={acc.label}/> : null}</span>}
                    trailing={<Button dense variant="secondary" onClick={() => { setEditing(null); setOpen(open === d.id ? null : d.id); }}>{open === d.id ? "Close" : "Details"}</Button>}>
                    {open === d.id ? (
                      editing === d.id ? (
                        <DestForm conns={conns} accountsLoading={accountsLoading} accountsReadError={accountsReadError} onAccountsRetry={onAccountsRetry} initial={fromDestination(d)} replaces={d.id} keys={keys} onKey={onKey} onSlackKey={onSlackKey} onKeyKnown={onKeyKnown} onSetUpAccount={setUpAccount}
                          onDone={() => { setEditing(null); setOpen(null); reload(); }} onCancel={() => setEditing(null)} />
                      ) : (
                        <div className="send-open" data-testid="dest-open">
                          <dl className="send-fields">
                            {detailFields(d, slackKey(d)).map(([l, v]) => <Field key={l} label={l} value={v} />)}
                            <Field label="Saved" value={stamp(d.created_at)} />
                            {c?.at ? <Field label="Checked" value={stamp(c.at)} /> : null}
                            {d.channel === "email" && c?.state ? (
                              <Field label="Key" value={c.state === "email_key_missing" ? "NOT SET" : c.state.startsWith("email_key") ? refusedWord(c.state) : "SET"} />
                            ) : null}
                          </dl>
                          <div className="send-verbs" data-testid="dest-verbs">
                            <Button dense variant="ghost" loading={c?.busy} data-testid="dest-check"
                              onClick={() => {
                                setChecks((m) => ({ ...m, [d.id]: { busy: true } }));
                                void wire.check(d.id)
                                  .then((r) => {
                                    setChecks((m) => ({ ...m, [d.id]: { busy: false, state: r.check.state, at: new Date().toISOString(), answeredAt: r.check.answered_at ?? null } }));
                                    // Slack: the Check reads the keychain, so it tells the face present or absent.
                                    const ref = String(d.account.key_ref ?? "");
                                    if (d.channel === "slack" && ref && (r.check.state === "ready" || r.check.state === "slack_webhook_missing")) {
                                      setKeys((k) => ({ ...k, [ref]: r.check.state === "ready" }));
                                    }
                                  })
                                  .catch((e) => setChecks((m) => ({ ...m, [d.id]: { busy: false, state: e instanceof Refusal ? e.code : "no_answer" } })));
                              }}>Check</Button>
                            <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                            {/* The built-in HoldSpeak folder is always there: no Edit, no Remove. */}
                            {d.builtin ? null : <>
                              <Button dense variant="ghost" data-testid="dest-edit" onClick={() => setEditing(d.id)}>Edit</Button>
                              <ConfirmVerb label="Remove" confirmLabel="Remove?" busy={removeBusy === d.id} data-testid="dest-remove"
                                onConfirm={() => remove(d.id)} />
                            </>}
                            {removeFailed[d.id] ? (
                              <span className="send-line" data-testid="dest-remove-failed" data-code={removeFailed[d.id]}>
                                <StateChip state="failure" label="NOT REMOVED" />
                                <Token className="surface-token" data-chip>{refusedWord(removeFailed[d.id])}</Token>
                                <Button dense variant="ghost" data-testid="dest-remove-retry" onClick={() => remove(d.id)}>{SEND_WORDS.retry}</Button>
                              </span>
                            ) : null}
                            {c?.state ? (
                              <span className="send-line" data-testid="dest-check-result" data-code={c.state}>
                                <CheckChip state={c.state} channel={d.channel} answeredAt={c.answeredAt} />
                              </span>
                            ) : null}
                          </div>
                        </div>
                      )
                    ) : null}
                  </SurfaceLedgerRow>
                );
              })}
            </ul>
          </SurfaceLedger>
        ) : null}
        {active.length === 0 || adding ? form : null}
        {parked.length ? (
          <div data-testid="dest-parked">
            <FoldGadget title="PARKED" token={String(parked.length)}>
              <SurfaceLedger count="" cols="account-destinations">
                <ul className="surface-ledger-rows">
                  {parked.map((d) => (
                    <SurfaceLedgerRow key={d.id} data-testid="dest-parked-row" wrap expands={false}
                      primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                      cells={<span className="surface-ledger-cells connections-tool-chips">
                        <Token className="surface-token" data-chip>{CHANNEL_WORD[d.channel] ?? d.channel}</Token>
                        <Token className="surface-token send-literal send-wrap send-target" data-chip title={targetToken(d.channel, d.target)}>{targetToken(d.channel, d.target)}</Token>
                        <Token className="surface-token" data-chip>{`PARKED ${stamp(d.parked_at)}`}</Token>
                      </span>} />
                  ))}
                </ul>
              </SurfaceLedger>
            </FoldGadget>
          </div>
        ) : null}
      </GadgetGroup>
    </div>
  );
}

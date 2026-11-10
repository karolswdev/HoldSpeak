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
  EgressChip,
  GadgetGroup,
  StateChip,
} from "../../../desk/surface";
import type { ConnectionsResponse } from "./api";
import { ACCOUNTS_CHANGED, fetchConnections } from "./api";
import { DestForm, EMPTY, emailKeyIdentity, type Draft } from "../../../features/channels/DestinationForm";
import {
  CHANNEL_WORD, DEFAULT_EMAIL_PROVIDER, DEST_FOCUS, SEND_WORDS, egressOf, emailProvider, refusedWord, stamp,
  takeDestinationsFocus, targetToken, wire, Refusal, type Channel, type Destination, type EmailProvider,
} from "../../../features/channels/channels";
import { ListView, PaneInspector, InspectorForm, InspectorQuestion, PaneActions, GadgetRow, ListPane, CycleGadget, type ListVerb } from "../../../desk/surface";
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

export function Destinations({ onSetUpAccount, onCount }: { onSetUpAccount?: (channel: Channel) => void; onCount?: (count: number) => void } = {}) {
  const [rows, setRows] = useState<Destination[] | null>(null);
  const [readFailed, setReadFailed] = useState(false);
  const [arrive, setArrive] = useState(false);
  const groupRef = useRef<HTMLDivElement>(null);
  const [conns, setConns] = useState<ConnectionsResponse | null>(null);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [accountsReadError, setAccountsReadError] = useState(false);
  const onAccountsRetry = () => window.dispatchEvent(new Event(ACCOUNTS_CHANGED));
  const setUpAccount = (channel: Channel) => onSetUpAccount?.(channel);
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
  const [details, setDetails] = useState<string | null>(null);
  const [confirmRemove, setConfirmRemove] = useState<string | null>(null);
  const [tab, setTab] = useState("active");
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
      .then(() => { setOpen(null); setConfirmRemove(null); setDetails(null); reload(); })
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
  const activeCount = rows?.filter((row) => row.state === "active").length;
  useEffect(() => { if (activeCount !== undefined) onCount?.(activeCount); }, [activeCount, onCount]);
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
        if (saved?.channel === "github") { setOpen(saved.id); setDetails(saved.id); }
        requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
      }}
      onCancel={() => setAdding(false)} />
  );
  const check = (id: string) => {
    const destination = rows.find((row) => row.id === id);
    if (!destination || checks[id]?.busy) return;
    setChecks((m) => ({ ...m, [id]: { busy: true } }));
    setDetails(id);
    void wire.check(id).then((answer) => {
      setChecks((m) => ({ ...m, [id]: { busy: false, state: answer.check.state, at: new Date().toISOString(), answeredAt: answer.check.answered_at ?? null } }));
      const ref = String(destination.account.key_ref ?? "");
      if (destination.channel === "slack" && ref && ["ready", "slack_webhook_missing"].includes(answer.check.state)) {
        setKeys((keys) => ({ ...keys, [ref]: answer.check.state === "ready" }));
      }
    }).catch((error) => setChecks((m) => ({ ...m, [id]: { busy: false, state: error instanceof Refusal ? error.code : "no_answer" } })));
  };
  const shown = tab === "parked" ? parked : active;
  const editable = (id: string | undefined) => Boolean(active.find((row) => row.id === id && !row.builtin));
  const verbs: ListVerb[] = [
    { id: "add", label: "Add destination", symbol: "+", run: () => { setEditing(null); setDetails(null); setAdding(true); } },
    { id: "remove", label: "Remove destination", symbol: "−", key: "Delete", enabled: (row) => editable(row?.id) && !removeBusy, run: (row) => setConfirmRemove(row!.id) },
    { id: "check", label: "Check", enabled: (row) => Boolean(row) && tab === "active" && !checks[row!.id]?.busy, run: (row) => check(row!.id) },
    { id: "edit", label: "Edit", enabled: (row) => editable(row?.id), run: (row) => { setDetails(null); setEditing(row!.id); } },
    { id: "open", label: "Open", key: "Enter", enabled: (row) => Boolean(row), run: (row) => { setAdding(false); setDetails(row!.id); } },
  ];
  const selected = rows.find((row) => row.id === editing);
  const inspected = rows.find((row) => row.id === details);
  const result = inspected ? checks[inspected.id] : undefined;
  const fields = inspected ? [...detailFields(inspected, slackKey(inspected)), ["Saved", stamp(inspected.created_at)],
    ...(inspected.parked_at ? [["Parked", stamp(inspected.parked_at)]] : []),
    ...(result?.at ? [["Checked", stamp(result.at)]] : []),
    ...(inspected.channel === "email" && result?.state ? [["Key", result.state === "email_key_missing" ? "NOT SET" : result.state.startsWith("email_key") ? refusedWord(result.state) : "SET"]] : []),
  ] : [];
  const list = <>
      <ListView label="Send to" ordered rows={shown.map((destination) => ({ id: destination.id, kind: "destination", name: destination.name,
        cells: { channel: CHANNEL_NAME[destination.channel], target: targetToken(destination.channel, destination.target) } }))}
        rowProps={() => ({ "data-testid": tab === "parked" ? "dest-parked-row" : "dest-row" })}
        columns={[{ key: "name", word: "Destination", priority: 100, track: "minmax(0, 1.2fr)" }, { key: "channel", word: "Channel", priority: 30, track: "80px" }, { key: "target", word: "To", priority: 20, track: "minmax(0, 1fr)" }]}
        toolbar={{scopes: parked.length ? [{id:"state",kind:"cycle",label:"Destinations",value:tab,onChange:(next) => {setTab(next);setOpen(null);setDetails(null);setEditing(null);setAdding(false);},options:[{value:"active",label:"Active"},{value:"parked",label:"Parked"}]}] : []}}
        selectedId={open} onSelect={(id) => { setOpen(id); setDetails(null); setConfirmRemove(null); }} verbs={verbs} defaultVerb="open" />
      {confirmRemove ? <InspectorQuestion targetId={confirmRemove} question={`Remove ${rows.find((row) => row.id === confirmRemove)?.name}?`}
        cancel={() => setConfirmRemove(null)} verb={{label:"Remove",busy:removeBusy === confirmRemove,disabled:Boolean(removeBusy),testId:"dest-remove",run:() => remove(confirmRemove)}}
        notice={removeFailed[confirmRemove] ? <div role="alert" data-testid="dest-remove-failed" data-code={removeFailed[confirmRemove]}><PaneActions><span>Not removed · {refusedWord(removeFailed[confirmRemove])}</span><Button dense variant="ghost" data-testid="dest-remove-retry" onClick={() => remove(confirmRemove)}>Retry</Button></PaneActions></div> : null} /> : null}
  </>;
  return <div className="surface-tab-panel" data-testid="destinations" ref={groupRef}>

    <ListPane list={list} label="Destination inspector">
    {adding ? <PaneInspector label="Add destination">{form}</PaneInspector>
    : selected ? <PaneInspector label={selected.name}>
      <DestForm conns={conns} accountsLoading={accountsLoading} accountsReadError={accountsReadError} onAccountsRetry={onAccountsRetry}
        initial={fromDestination(selected)} replaces={selected.id} keys={keys} onKey={onKey} onSlackKey={onSlackKey} onKeyKnown={onKeyKnown} onSetUpAccount={setUpAccount}
        onDone={() => { setEditing(null); reload(); }} onCancel={() => setEditing(null)} />
    </PaneInspector> : inspected ? <PaneInspector label={inspected.name} onClose={() => setDetails(null)}>
        <InspectorForm testId="dest-open">
          {fields.map(([label, value]) => <GadgetRow key={label} label={label}>{value}</GadgetRow>)}
          <GadgetRow label="Destination"><span data-testid="dest-verbs"><EgressChip {...egressOf(inspected)} /></span></GadgetRow>
          {result?.busy ? <GadgetRow label="Check"><span role="status">Checking…</span></GadgetRow> : null}
          {result?.state ? <GadgetRow label="Check"><span data-testid="dest-check-result" data-code={result.state}><CheckChip state={result.state} channel={inspected.channel} answeredAt={result.answeredAt} /></span></GadgetRow> : null}
        </InspectorForm>
      </PaneInspector> : null}
    </ListPane>
  </div>;
}

/* PHILO-10-04 canvas 2 (PROPOSAL): the Destinations group, in Settings ->
 * Connections, under Tools (the accounts each destination depends on live in
 * Tools, right above). Library species only: GadgetGroup, GadgetRow,
 * CycleGadget, StringGadget, CheckGadget, SecretRow, FoldGadget,
 * SurfaceLedger, SurfaceLedgerRow, StateChip, EgressChip, Button, ConfirmVerb.
 *
 * Rules drawn (design/send-lifecycle.md sections 1, 5, 8):
 * - A row never changes its target. Edit = Save makes a NEW row and PARKS the
 *   old one; Remove = park. Parked rows keep their history (PARKED fold).
 * - The account is concrete: GitHub {host, login} read from gh at save;
 *   Jira/Confluence one saved account {site, email}; email {provider, from,
 *   name, key_ref}. The key is typed once into the OS keychain and never
 *   shown again (SET / —).
 * - No counter of zero: the group head counts only when there is a row.
 * Round two (Codex Astra r1 on #693):
 * - The Room's "Add destination" ARRIVES here: the group scrolls itself into
 *   view and opens the add form (the intent in p10.ts). No harness scroll.
 * - A read that gets no answer says CANNOT READ DESTINATIONS + Retry; it is
 *   never the empty add form. A refused key save says KEY NOT SAVED + why.
 * - Email Check reports the sender's verification, never the key alone.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "@w/components/signal/Signal";
import {
  CheckGadget,
  ConfirmVerb,
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  SecretRow,
  StateChip,
  StringGadget,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "@w/desk/surface";
import { fetchConnections, type ConnectionsResponse } from "@w/pages/cores/connections/api";
import { accountChip } from "./SendWell";
import {
  CHANNEL_WORD, DEST_FOCUS, SEND_WORDS, egressOf, failedWord, refusedWord, stamp, takeDestinationsFocus, targetToken, wire,
  Refusal, type Channel, type Destination,
} from "./p10";

const CHANNELS: { value: Channel; label: string }[] = [
  { value: "file", label: "Folder" },
  { value: "github", label: "GitHub comment" },
  { value: "jira", label: "Jira comment" },
  { value: "confluence", label: "Confluence blog post" },
  { value: "email", label: "Email (SendGrid)" },
];

type Draft = {
  channel: Channel; name: string; nameTouched: boolean;
  folder: string; synced: boolean;
  repo: string; kind: "issue" | "pr"; number: string;
  jiraAccount: string; key: string;
  confAccount: string; space: string;
  fromEmail: string; fromName: string; to: string; cc: string;
};
const EMPTY: Draft = {
  channel: "file", name: "", nameTouched: false, folder: "", synced: false, repo: "", kind: "issue", number: "",
  jiraAccount: "", key: "", confAccount: "", space: "", fromEmail: "", fromName: "", to: "", cc: "",
};

function fromDestination(d: Destination): Draft {
  const t = d.target, a = d.account;
  return {
    ...EMPTY, channel: d.channel, name: d.name, nameTouched: true,
    folder: String(t.folder ?? ""), synced: d.synced,
    repo: String(t.repo ?? ""), kind: t.kind === "pr" ? "pr" : "issue", number: t.number != null ? String(t.number) : "",
    jiraAccount: d.channel === "jira" ? `${a.site}|${a.email}` : "", key: String(t.key ?? ""),
    confAccount: d.channel === "confluence" ? `${a.site}|${a.email}` : "", space: String(t.space ?? ""),
    fromEmail: String(a.from_email ?? ""), fromName: String(a.from_name ?? ""), to: String(t.to ?? ""), cc: String(t.cc ?? ""),
  };
}

/** The name he would type, from the target (editable). */
function autoName(d: Draft): string {
  switch (d.channel) {
    case "file": return d.folder ? `Folder ${d.folder.split("/").filter(Boolean).pop() ?? ""}` : "";
    case "github": return d.repo && d.number ? `${d.repo} ${d.kind === "pr" ? "PR " : ""}#${d.number}` : "";
    case "jira": return d.key ? `Jira ${d.key}` : "";
    case "confluence": return d.space ? `Confluence space ${d.space}` : "";
    case "email": return d.to ? `Email ${d.to.split(",")[0].trim()}` : "";
  }
}
const keyRef = (fromEmail: string) => `holdspeak.email.sendgrid:${fromEmail.trim().toLowerCase()}`;

function DestForm({ conns, initial, replaces, keys, onKey, onDone, onCancel }: {
  conns: ConnectionsResponse | null; initial: Draft; replaces?: string; keys: Record<string, boolean>;
  onKey: (ref: string, v: string) => Promise<string | null>; onDone: () => void; onCancel?: () => void;
}) {
  const [keyRefused, setKeyRefused] = useState<string | null>(null);
  const [d, setD] = useState<Draft>(initial);
  const [busy, setBusy] = useState(false);
  const [refused, setRefused] = useState<string | null>(null);
  const set = (patch: Partial<Draft>) => { setRefused(null); setD((x) => ({ ...x, ...patch })); };
  const name = d.nameTouched ? d.name : autoName(d);
  const gh = conns?.tools.find((t) => t.provider_id === "github");
  const jiraConns = conns?.tools.find((t) => t.provider_id === "jira")?.connections ?? [];
  const confConns = conns?.tools.find((t) => t.provider_id === "confluence")?.connections ?? [];
  const pick = (v: string) => { const [site, email] = v.split("|"); return { site, email }; };
  const jiraAcc = d.jiraAccount || (jiraConns[0] ? `${jiraConns[0].account.site}|${jiraConns[0].account.email}` : "");
  const confAcc = d.confAccount || (confConns[0] ? `${confConns[0].account.site}|${confConns[0].account.email}` : "");
  const account: Record<string, string | boolean> =
    d.channel === "github" ? { host: "github.com", login: String(gh?.account?.login ?? "") }
    : d.channel === "jira" ? pick(jiraAcc)
    : d.channel === "confluence" ? pick(confAcc)
    : d.channel === "email" ? { provider: "sendgrid", from_email: d.fromEmail, from_name: d.fromName, key_ref: keyRef(d.fromEmail), key_present: !!keys[keyRef(d.fromEmail)] }
    : {};
  const eg = egressOf({ channel: d.channel, account, synced: d.synced });
  const acc = accountChip({ channel: d.channel, account }, conns);
  const save = async () => {
    setBusy(true); setRefused(null);
    const target =
      d.channel === "file" ? { folder: d.folder }
      : d.channel === "github" ? { repo: d.repo, kind: d.kind, number: d.number }
      : d.channel === "jira" ? { key: d.key }
      : d.channel === "confluence" ? { space: d.space }
      : { to: d.to, cc: d.cc };
    try {
      await wire.addDestination({ channel: d.channel, name, account, target: target as never, synced: d.synced, replaces } as never);
      onDone();
    } catch (e) {
      setRefused(e instanceof Refusal ? e.code : "no_answer");
    } finally { setBusy(false); }
  };
  return (
    <div className="p10-dest-form" data-testid="dest-form" data-channel={d.channel}>
      {replaces ? null : (
        <GadgetRow label="Channel">
          <CycleGadget label="Channel" value={d.channel} options={CHANNELS} onChange={(v) => set({ ...EMPTY, channel: v as Channel })} />
        </GadgetRow>
      )}
      {d.channel === "file" ? (<>
        <GadgetRow label="Folder"><StringGadget label="Folder" value={d.folder} onChange={(v) => set({ folder: v })} placeholder="/Users/you/Reports" inputProps={{ "data-testid": "dest-folder" } as never} /></GadgetRow>
        <GadgetRow label="Synced"><CheckGadget variant="token" label="SYNCED" checked={d.synced} onChange={(v) => set({ synced: v })} /></GadgetRow>
      </>) : null}
      {d.channel === "github" ? (<>
        <GadgetRow label="Account">
          <span className="p10-inline">
            <span className="surface-token" data-chip>{gh?.account?.login ? `@${gh.account.login}` : "—"}</span>
            {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
          </span>
        </GadgetRow>
        <GadgetRow label="Repository"><StringGadget label="Repository" value={d.repo} onChange={(v) => set({ repo: v })} placeholder="owner/repo" inputProps={{ "data-testid": "dest-repo" } as never} /></GadgetRow>
        <GadgetRow label="Kind"><CycleGadget label="Kind" value={d.kind} options={[{ value: "issue", label: "Issue" }, { value: "pr", label: "Pull request" }]} onChange={(v) => set({ kind: v as "issue" | "pr" })} /></GadgetRow>
        <GadgetRow label="Number"><StringGadget label="Number" value={d.number} onChange={(v) => set({ number: v })} placeholder="42" inputProps={{ "data-testid": "dest-number", inputMode: "numeric" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "jira" ? (<>
        <GadgetRow label="Account">
          <span className="p10-inline">
            {jiraConns.length ? (
              <CycleGadget label="Jira account" value={jiraAcc} onChange={(v) => set({ jiraAccount: v })}
                options={jiraConns.map((c) => ({ value: `${c.account.site}|${c.account.email}`, label: `${c.account.site} · ${c.account.email}` }))} />
            ) : <span className="surface-token" data-chip>NO JIRA ACCOUNT</span>}
            {acc && jiraConns.length ? <StateChip state={acc.state} label={acc.label} /> : null}
          </span>
        </GadgetRow>
        <GadgetRow label="Work item"><StringGadget label="Work item" value={d.key} onChange={(v) => set({ key: v })} placeholder="PAY-118" inputProps={{ "data-testid": "dest-key" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "confluence" ? (<>
        <GadgetRow label="Account">
          <span className="p10-inline">
            {confConns.length ? (
              <CycleGadget label="Confluence account" value={confAcc} onChange={(v) => set({ confAccount: v })}
                options={confConns.map((c) => ({ value: `${c.account.site}|${c.account.email}`, label: `${c.account.site} · ${c.account.email}` }))} />
            ) : <span className="surface-token" data-chip>NO CONFLUENCE ACCOUNT</span>}
            {acc && confConns.length ? <StateChip state={acc.state} label={acc.label} /> : null}
          </span>
        </GadgetRow>
        <GadgetRow label="Space id"><StringGadget label="Space id" value={d.space} onChange={(v) => set({ space: v })} placeholder="98304" inputProps={{ "data-testid": "dest-space", inputMode: "numeric" } as never} /></GadgetRow>
      </>) : null}
      {d.channel === "email" ? (<>
        <GadgetRow label="Provider"><CycleGadget label="Provider" value="sendgrid" options={[{ value: "sendgrid", label: "SendGrid" }]} onChange={() => {}} /></GadgetRow>
        <GadgetRow label="From"><StringGadget label="From" value={d.fromEmail} onChange={(v) => set({ fromEmail: v })} placeholder="you@company.com" inputProps={{ "data-testid": "dest-from" } as never} /></GadgetRow>
        <GadgetRow label="From name"><StringGadget label="From name" value={d.fromName} onChange={(v) => set({ fromName: v })} placeholder="Your name" /></GadgetRow>
        <div className="p10-secret" data-testid="dest-key-row">
          <SecretRow label="SendGrid key" configured={!!keys[keyRef(d.fromEmail)]}
            onReplace={(v) => { setKeyRefused(null); void onKey(keyRef(d.fromEmail), v).then(setKeyRefused); }} />
          {keyRefused ? (
            <span className="p10-outcome" data-testid="dest-key-refused" data-code={keyRefused}>
              <StateChip state="failure" label={SEND_WORDS.keyNotSaved} />
              <span className="surface-token" data-chip>{refusedWord(keyRefused)}</span>
            </span>
          ) : null}
        </div>
        <GadgetRow label="To"><StringGadget label="To" value={d.to} onChange={(v) => set({ to: v })} placeholder="a@company.com, b@company.com" inputProps={{ "data-testid": "dest-to" } as never} /></GadgetRow>
        <GadgetRow label="Cc"><StringGadget label="Cc" value={d.cc} onChange={(v) => set({ cc: v })} placeholder="c@company.com" /></GadgetRow>
      </>) : null}
      <GadgetRow label="Name"><StringGadget label="Name" value={name} onChange={(v) => set({ name: v, nameTouched: true })} placeholder="Name" inputProps={{ "data-testid": "dest-name" } as never} /></GadgetRow>
      <div className="p10-verbs" data-testid="dest-form-verbs">
        <Button dense variant="primary" loading={busy} onClick={() => void save()} data-testid="dest-save">Save</Button>
        {onCancel ? <Button dense variant="ghost" onClick={onCancel} data-testid="dest-cancel">Cancel</Button> : null}
        <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
        {refused ? (
          <span className="p10-outcome" data-testid="dest-refused" data-code={refused}>
            <StateChip state="failure" label="REFUSED" />
            <span className="surface-token" data-chip>{refusedWord(refused)}</span>
          </span>
        ) : null}
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="p10-preview-field">
      <dt className="surface-token">{label}</dt>
      <dd>{value || "—"}</dd>
    </div>
  );
}

function detailFields(d: Destination): [string, string][] {
  const t = d.target, a = d.account;
  const base: [string, string][] = [["Channel", CHANNEL_WORD[d.channel]]];
  switch (d.channel) {
    case "file": return [...base, ["Folder", String(t.folder)], ["Synced", d.synced ? "YES" : "NO"]];
    case "github": return [...base, ["Account", `@${a.login} · ${a.host}`], ["Repository", String(t.repo)], [t.kind === "pr" ? "Pull request" : "Issue", `#${t.number}`]];
    case "jira": return [...base, ["Account", `${a.email} · ${a.site}`], ["Work item", String(t.key)]];
    case "confluence": return [...base, ["Account", `${a.email} · ${a.site}`], ["Space id", String(t.space)]];
    case "email": return [...base, ["Provider", "SendGrid"], ["From", `${a.from_name} <${a.from_email}>`], ["Key", a.key_present ? "SET" : "—"], ["To", String(t.to)], ["Cc", String(t.cc || "—")]];
  }
}

export function Destinations() {
  const [rows, setRows] = useState<Destination[] | null>(null);
  const [readFailed, setReadFailed] = useState(false);
  const [arrive, setArrive] = useState(false);
  const groupRef = useRef<HTMLDivElement>(null);
  const [conns, setConns] = useState<ConnectionsResponse | null>(null);
  const [open, setOpen] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [keys, setKeys] = useState<Record<string, boolean>>({});
  const [checks, setChecks] = useState<Record<string, { busy: boolean; state?: string }>>({});
  const [removeBusy, setRemoveBusy] = useState<string | null>(null);
  const reload = useCallback(() => void wire.destinations(true).then((r) => {
    setRows(r); setReadFailed(false);
    setKeys((k) => ({ ...k, ...Object.fromEntries(r.filter((d) => d.channel === "email").map((d) => [String(d.account.key_ref), !!d.account.key_present])) }));
  }).catch(() => setReadFailed(true)), []);
  useEffect(() => {
    reload(); void fetchConnections().then(setConns).catch(() => setConns(null));
    const want = () => { if (takeDestinationsFocus()) setArrive(true); };
    want();
    window.addEventListener(DEST_FOCUS, want);
    return () => window.removeEventListener(DEST_FOCUS, want);
  }, [reload]);
  // The arrival: once the group has drawn, bring it into view with the add form open.
  useEffect(() => {
    if (!arrive || (rows === null && !readFailed)) return;
    setArrive(false);
    setOpen(null); setEditing(null); setAdding(true);
    requestAnimationFrame(() => groupRef.current?.scrollIntoView({ block: "start" }));
  }, [arrive, rows, readFailed]);
  const onKey = (ref: string, v: string): Promise<string | null> => wire.saveKey(ref, v)
    .then((r) => { setKeys((k) => ({ ...k, [ref]: r.key_present })); return null; })
    .catch((e) => (e instanceof Refusal ? e.code : "no_answer"));
  if (readFailed) {
    return (
      <div data-p10="destinations" data-testid="destinations" ref={groupRef}>
        <GadgetGroup label="Destinations">
          <div className="p10-verbs" data-testid="dest-unreadable">
            <StateChip state="failure" label={`${SEND_WORDS.cannotRead} DESTINATIONS`} />
            <Button dense variant="ghost" data-testid="dest-unreadable-retry" onClick={reload}>{SEND_WORDS.retry}</Button>
          </div>
        </GadgetGroup>
      </div>
    );
  }
  if (rows === null) return null;
  const active = rows.filter((d) => d.state === "active");
  const parked = rows.filter((d) => d.state === "parked");
  const form = (
    <DestForm conns={conns} initial={EMPTY} keys={keys} onKey={onKey}
      onDone={() => { setAdding(false); reload(); }}
      onCancel={active.length ? () => setAdding(false) : undefined} />
  );
  return (
    <div data-p10="destinations" data-testid="destinations" ref={groupRef}>
      <GadgetGroup label={active.length ? `Destinations ${active.length}` : "Destinations"}>
        {active.length ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="dest-list">
              {active.map((d) => {
                const eg = egressOf(d);
                const acc = accountChip(d, conns);
                const c = checks[d.id];
                return (
                  <SurfaceLedgerRow key={d.id} data-testid="dest-row" wrap open={open === d.id}
                    lineLabel={`${d.name}, ${CHANNEL_WORD[d.channel]}`}
                    onToggle={() => { setEditing(null); setOpen(open === d.id ? null : d.id); }}
                    lead={<span className="p10-pick" aria-hidden="true">{open === d.id ? "▾" : "▸"}</span>}
                    primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                    cells={<>
                      <span className="surface-token" data-chip>{CHANNEL_WORD[d.channel]}</span>
                      <span className="surface-token p10-literal p10-target" data-chip>{targetToken(d.channel, d.target)}</span>
                      {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                      <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    </>}>
                    {open === d.id ? (
                      editing === d.id ? (
                        <DestForm conns={conns} initial={fromDestination(d)} replaces={d.id} keys={keys} onKey={onKey}
                          onDone={() => { setEditing(null); setOpen(null); reload(); }} onCancel={() => setEditing(null)} />
                      ) : (
                        <div className="p10-open" data-testid="dest-open">
                          <dl className="p10-preview-fields">
                            {detailFields(d).map(([l, v]) => <Field key={l} label={l} value={v} />)}
                            <Field label="Saved" value={stamp(d.created_at)} />
                            {d.checked_at ? <Field label="Checked" value={stamp(d.checked_at)} /> : null}
                          </dl>
                          <div className="p10-verbs" data-testid="dest-verbs">
                            <Button dense variant="ghost" loading={c?.busy} data-testid="dest-check"
                              onClick={() => {
                                setChecks((m) => ({ ...m, [d.id]: { busy: true } }));
                                void wire.check(d.id).then((r) => { setChecks((m) => ({ ...m, [d.id]: { busy: false, state: r.state } })); reload(); })
                                  .catch(() => setChecks((m) => ({ ...m, [d.id]: { busy: false, state: "no_answer" } })));
                              }}>Check</Button>
                            <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                            <Button dense variant="ghost" data-testid="dest-edit" onClick={() => setEditing(d.id)}>Edit</Button>
                            <ConfirmVerb label="Remove" confirmLabel="Remove?" busy={removeBusy === d.id} data-testid="dest-remove"
                              onConfirm={() => { setRemoveBusy(d.id); void wire.park(d.id).finally(() => { setRemoveBusy(null); setOpen(null); reload(); }); }} />
                            {c?.state ? (
                              <span className="p10-outcome" data-testid="dest-check-result" data-code={c.state}>
                                {c.state === "checked" || c.state === "sender_verified" || c.state === "connected"
                                  ? <StateChip state="success" label={c.state === "sender_verified" ? "SENDER VERIFIED" : "CHECKED"} />
                                  : c.state === "sender_not_verified"
                                    ? <StateChip state="failure" label={failedWord(c.state)} />
                                    : <StateChip state="warning" label={refusedWord(c.state === "owner_action_required" ? "atlassian_not_signed_in" : c.state === "never_checked" ? "NEVER CHECKED" : c.state)} />}
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
        {active.length === 0 || adding ? form : (
          <div className="p10-verbs" data-testid="dest-add-line">
            <Button dense variant="ghost" data-testid="dest-add" onClick={() => { setOpen(null); setAdding(true); }}>Add destination</Button>
          </div>
        )}
        {parked.length ? (
          <div data-testid="dest-parked">
            <FoldGadget title="PARKED" token={String(parked.length)}>
              <SurfaceLedger count="" cols="room">
                <ul className="surface-ledger-rows">
                  {parked.map((d) => (
                    <SurfaceLedgerRow key={d.id} data-testid="dest-parked-row" wrap expands={false}
                      primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                      cells={<>
                        <span className="surface-token" data-chip>{CHANNEL_WORD[d.channel]}</span>
                        <span className="surface-token p10-literal p10-target" data-chip>{targetToken(d.channel, d.target)}</span>
                        <span className="surface-token" data-chip>{`PARKED ${stamp(d.parked_at)}`}</span>
                      </>} />
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

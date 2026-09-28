/* PHILO-10-04 canvas 1 (PROPOSAL): the SEND well on a published update, the
 * PREPARED rows, and the one DELIVERY history (every channel + the manual
 * Mark delivered, kept as the manual channel). Library species only:
 * SurfaceSection, SurfaceLedger, SurfaceLedgerRow, SurfaceWell, StateChip,
 * EgressChip, Material, Button, ConfirmVerb, StringGadget.
 *
 * THE PRESS RULE (settled; Phase 9 canvases r1 F4 / r2 F1 carried over):
 * one press = one {update, destination or prepared row, command_id, preview
 * digest}, held PER UPDATE AND TARGET in a module store that survives Back
 * and opening another update. A lost answer keeps all four; Retry sends the
 * same key, and the hub's replay answers the settled row, never a second
 * dispatch. A new key only after the result is known. A channel UNKNOWN is a
 * settled record: "Send again" is a NEW send with a NEW key, never a retry.
 */
import { useCallback, useEffect, useState, useSyncExternalStore } from "react";
import { Button } from "@w/components/signal/Signal";
import {
  ConfirmVerb,
  EgressChip,
  Material,
  StateChip,
  StringGadget,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceSection,
  SurfaceWell,
} from "@w/desk/surface";
import { refusalWord } from "@w/desk/surface/egress";
import { useDesk } from "@w/desk/store";
import { fetchConnections } from "@w/pages/cores/connections/api";
import { chipLabel } from "@w/pages/cores/connections/ConnectionsPane";
import type { ConnectionsResponse, ConnectionState } from "@w/pages/cores/connections/api";
import type { UpdateController } from "@w/features/project-room/update/useUpdateController";
import type { ProjectUpdate } from "@w/features/project-room/update/model";
import {
  CHANNEL_WORD, SENT_WORD, SEND_WORDS, egressOf, failedWord, farSide, refusedWord, stamp, targetToken, unknownWord, wire,
  Refusal, type Destination, type Preview, type Send,
} from "./p10";

/* ── the per-update store ──────────────────────────────────────────── */

type Outcome =
  | { kind: "none" }
  | { kind: "refused"; code: string }
  | { kind: "failed"; code: string }
  | { kind: "lost" }
  | { kind: "settled"; send: Send };
type Held = { key: string; body: Parameters<typeof wire.send>[0] };
const store = {
  picked: new Map<string, string | null>(),          // updateId -> destination id
  holds: new Map<string, Held>(),                     // `${updateId}|${target}` -> the held press
  outcomes: new Map<string, Outcome>(),
  busy: new Set<string>(),
  tick: 0,
  subs: new Set<() => void>(),
};
const bump = () => { store.tick++; store.subs.forEach((f) => f()); };
const useStore = () => useSyncExternalStore((f) => { store.subs.add(f); return () => store.subs.delete(f); }, () => store.tick);

/* ── the reads ─────────────────────────────────────────────────────── */

export function useSends(updateId: string) {
  const [sends, setSends] = useState<Send[]>([]);
  const reload = useCallback(() => { void wire.sends(updateId).then(setSends).catch(() => setSends([])); }, [updateId]);
  const tick = useStore();
  useEffect(() => { reload(); }, [reload, tick]);
  return { sends, reload };
}

function useDestinations() {
  const [rows, setRows] = useState<Destination[] | null>(null);
  useEffect(() => { void wire.destinations().then(setRows).catch(() => setRows([])); }, []);
  return rows;
}

function useConnections() {
  const [c, setC] = useState<ConnectionsResponse | null>(null);
  useEffect(() => { void fetchConnections().then(setC).catch(() => setC(null)); }, []);
  return c;
}

/** The account state a destination depends on (Phase 9 B1 words, the real
 *  Connections chip words). Null for a folder. */
export function accountChip(d: Pick<Destination, "channel" | "account">, c: ConnectionsResponse | null):
  { state: "success" | "warning" | "idle" | "failure"; label: string; code: string } | null {
  if (d.channel === "file") return null;
  if (d.channel === "email") {
    return d.account.key_present
      ? { state: "success", label: "KEY SET", code: "key_present" }
      : { state: "warning", label: "NO KEY", code: "email_key_missing" };
  }
  const tool = c?.tools.find((t) => t.provider_id === d.channel);
  let state: ConnectionState = "not_configured";
  if (d.channel === "github") {
    state = (tool?.state ?? "not_configured") as ConnectionState;
    if (state === "connected" && tool?.account?.login !== d.account.login) {
      return { state: "failure", label: "ACCOUNT CHANGED", code: "github_identity_changed" };
    }
  } else {
    const conn = tool?.connections?.find((x) => x.account.site === d.account.site && x.account.email === d.account.email);
    state = (conn?.state ?? "not_configured") as ConnectionState;
  }
  const map: Record<string, "success" | "warning" | "idle" | "failure"> = {
    connected: "success", owner_action_required: "warning", never_checked: "idle", not_configured: "idle", unavailable: "failure", degraded: "warning",
  };
  return { state: map[state] ?? "idle", label: chipLabel(state, d.channel).toUpperCase(), code: state };
}

/* ── pieces ────────────────────────────────────────────────────────── */

function PreviewWell({ preview, testid }: { preview: Preview; testid: string }) {
  return (
    <div className="p10-preview" data-testid={testid}>
      <SurfaceWell>
        <dl className="p10-preview-fields">
          {preview.fields.map((f) => (
            <div key={f.label} className="p10-preview-field" data-testid="send-preview-field">
              <dt className="surface-token">{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
        <div className="p10-preview-body" data-testid="send-preview-body">
          {preview.body_kind === "markdown" ? <Material>{preview.body}</Material> : <div className="p10-preview-text">{preview.body}</div>}
        </div>
      </SurfaceWell>
    </div>
  );
}

function OutcomeLine({ o }: { o: Outcome }) {
  if (o.kind === "refused" || o.kind === "failed") {
    return (
      <span className="p10-outcome" data-testid={`send-${o.kind}`} data-code={o.code}>
        <StateChip state="failure" label={o.kind === "refused" ? "REFUSED" : "FAILED"} />
        <span className="surface-token" data-chip>{o.kind === "refused" ? refusedWord(o.code) : failedWord(o.code)}</span>
        <span className="surface-token" data-chip>NOTHING SENT</span>
      </span>
    );
  }
  if (o.kind === "lost") {
    return (
      <span className="p10-outcome" data-testid="send-lost">
        <StateChip state="warning" label={SEND_WORDS.lost} />
      </span>
    );
  }
  return null;
}

function LastChip({ s }: { s: Send | undefined }) {
  if (!s) return null;
  if (s.state === "sent") return <StateChip state="success" icon="✓" label={`${SENT_WORD[s.channel]} ${stamp(s.settled_at).slice(-5)}`} />;
  if (s.state === "unknown") return <span data-testid="send-last-unknown"><StateChip state="warning" label={SEND_WORDS.lastUnknown} /></span>;
  return null;
}

function openFar(url: string | null) { if (url) window.open(url, "_blank", "noopener"); }

/* ── the press ─────────────────────────────────────────────────────── */

async function press(updateId: string, target: string, fresh: () => Held["body"], reload: () => void) {
  const k = `${updateId}|${target}`;
  if (store.busy.has(k)) return;                 // a double-click is one press
  let held = store.holds.get(k);
  if (!held) { held = { key: crypto.randomUUID(), body: fresh() }; store.holds.set(k, held); }
  store.busy.add(k); store.outcomes.set(k, { kind: "none" }); bump();
  try {
    const send = await wire.send({ ...held.body, command_id: held.key });
    store.holds.delete(k);
    store.outcomes.set(k, { kind: "settled", send });
  } catch (e) {
    if (e instanceof Refusal) { store.holds.delete(k); store.outcomes.set(k, { kind: e.kind, code: e.code }); }
    else store.outcomes.set(k, { kind: "lost" });  // keep the update, the key and the body for Retry
  } finally {
    store.busy.delete(k); bump(); reload();
  }
}

/* ── the SEND well ─────────────────────────────────────────────────── */

export function SendWell({ update, sends, reload }: { update: ProjectUpdate; sends: Send[]; reload: () => void }) {
  useStore();
  const destinations = useDestinations();
  const conns = useConnections();
  const uid = update.id;
  const picked = store.picked.get(uid) ?? null;
  const [preview, setPreview] = useState<{ id: string; digest: string; preview: Preview } | null>(null);
  useEffect(() => {
    if (!picked) { setPreview(null); return; }
    let live = true;
    void wire.preview(uid, picked).then((p) => { if (live) setPreview({ id: picked, digest: p.payload_digest, preview: p.preview }); }).catch(() => {});
    return () => { live = false; };
  }, [uid, picked]);

  const pending = sends.filter((s) => s.state === "prepared");
  const lastFor = (destId: string) => [...sends].reverse().find((s) => s.destination_id === destId && (s.state === "sent" || s.state === "unknown"));

  if (destinations === null) return null;
  return (
    <div data-p10="send" data-testid="send-well">
      <SurfaceSection label={SEND_WORDS.section}>
        {pending.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepared-list">
              {pending.map((s) => <PreparedRow key={s.id} uid={uid} s={s} reload={reload} conns={conns} dest={destinations.find((d) => d.id === s.destination_id)} />)}
            </ul>
          </SurfaceLedger>
        ) : null}
        {destinations.length === 0 ? (
          <div className="p10-none" data-testid="send-none">
            <span className="surface-token" data-chip>{SEND_WORDS.noDestination}</span>
            <Button dense variant="primary" data-testid="send-add-destination"
              onClick={() => useDesk.getState().openSurfaceWindow("configure-settings", "integrations")}>
              {SEND_WORDS.addDestination}
            </Button>
          </div>
        ) : (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="destination-list">
              {destinations.map((d) => {
                const k = `${uid}|${d.id}`;
                const open = picked === d.id;
                const o = store.outcomes.get(k) ?? { kind: "none" };
                const held = store.holds.get(k);
                const last = lastFor(d.id);
                const eg = egressOf(d);
                const acc = accountChip(d, conns);
                const busy = store.busy.has(k);
                const lost = o.kind === "lost";
                return (
                  <SurfaceLedgerRow
                    key={d.id}
                    data-testid="destination-row"
                    wrap
                    open={open}
                    lineLabel={`${d.name}, ${CHANNEL_WORD[d.channel]}`}
                    onToggle={() => {
                      if (busy || held) return;           // a held press keeps its pick
                      store.picked.set(uid, open ? null : d.id); bump();
                    }}
                    lead={<span className="p10-pick" aria-hidden="true">{open ? "●" : "○"}</span>}
                    primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                    cells={<>
                      <span className="surface-token" data-chip>{CHANNEL_WORD[d.channel]}</span>
                      <span className="surface-token p10-target" data-chip>{targetToken(d.channel, d.target)}</span>
                      {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                      <LastChip s={last} />
                      <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    </>}
                  >
                    {open ? (
                      <div className="p10-open" data-testid="send-open" data-destination={d.name}>
                        {preview && preview.id === d.id ? <PreviewWell preview={preview.preview} testid="send-preview" /> : null}
                        <div className="p10-verbs" data-testid="send-verbs">
                          <Button dense variant="primary" loading={busy}
                            disabled={!preview || preview.id !== d.id}
                            data-testid={lost ? "send-retry" : "send-verb"}
                            onClick={() => void press(uid, d.id, () => ({
                              document_ref: `project_update:${uid}`, destination_id: d.id, preview_digest: preview!.digest,
                            } as Held["body"]), reload)}>
                            {lost ? SEND_WORDS.retry : last ? SEND_WORDS.sendAgain : SEND_WORDS.send}
                          </Button>
                          <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                          {last?.state === "unknown" && farSide(d.channel, d.target, d.account) ? (
                            <Button dense variant="ghost" data-testid="send-check"
                              onClick={() => openFar(farSide(d.channel, d.target, d.account))}>{SEND_WORDS.check}</Button>
                          ) : null}
                          <OutcomeLine o={o} />
                        </div>
                      </div>
                    ) : null}
                  </SurfaceLedgerRow>
                );
              })}
            </ul>
          </SurfaceLedger>
        )}
      </SurfaceSection>
    </div>
  );
}

const BY: Record<string, string> = { owner: "BY YOU", steward: "BY STEWARD" };

function PreparedRow({ uid, s, reload, conns, dest }: {
  uid: string; s: Send; reload: () => void; conns: ConnectionsResponse | null; dest: Destination | undefined;
}) {
  const k = `${uid}|${s.id}`;
  const o = store.outcomes.get(k) ?? { kind: "none" };
  const busy = store.busy.has(k);
  const eg = egressOf({ channel: s.channel, account: s.account, synced: dest?.synced });
  const acc = accountChip({ channel: s.channel, account: { ...s.account, key_present: dest?.account.key_present ?? s.account.key_present ?? false } }, conns);
  // A named destination refusal is final for this row: Send would only
  // refuse again (UX-CANON §A.11), so only Discard stays.
  const dead = o.kind === "refused" && (o.code === "destination_changed" || o.code === "destination_parked");
  const [discardBusy, setDiscardBusy] = useState(false);
  const [discardOutcome, setDiscardOutcome] = useState<string | null>(null);
  return (
    <SurfaceLedgerRow
      data-testid="prepared-row"
      wrap
      open
      expands={false}
      lead={<StateChip state="active" icon="◆" label="" />}
      primary={<span className="surface-primary" data-destination={s.destination_name}>{s.destination_name}</span>}
      cells={<>
        <StateChip state="active" icon="◆" label={SEND_WORDS.prepared} />
        <span className="surface-token" data-chip data-testid="prepared-by">{BY[s.prepared_by_kind] ?? `BY ${s.prepared_by_identity.toUpperCase()}`}</span>
        <span className="surface-token" data-chip>REV {s.draft_revision}</span>
        <span className="surface-token" data-chip>{stamp(s.created_at)}</span>
        {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
        <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
      </>}
    >
      <div className="p10-open" data-testid="prepared-open">
        <PreviewWell preview={s.preview} testid="prepared-preview" />
        <div className="p10-verbs" data-testid="prepared-verbs">
          {!dead ? (
            <Button dense variant="primary" loading={busy} data-testid={o.kind === "lost" ? "prepared-retry" : "prepared-send"}
              onClick={() => void press(uid, s.id, () => ({ send_id: s.id } as Held["body"]), reload)}>
              {o.kind === "lost" ? SEND_WORDS.retry : SEND_WORDS.send}
            </Button>
          ) : null}
          {!dead ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
          <ConfirmVerb label={SEND_WORDS.discard} confirmLabel={SEND_WORDS.discardArmed} busy={discardBusy}
            data-testid="prepared-discard"
            onConfirm={() => {
              setDiscardBusy(true);
              void wire.discard(s.id, crypto.randomUUID())
                .then(() => { store.outcomes.delete(k); bump(); })
                .catch((e) => setDiscardOutcome(e instanceof Refusal ? e.code : "no_answer"))
                .finally(() => { setDiscardBusy(false); reload(); });
            }} />
          <OutcomeLine o={o} />
          {discardOutcome ? <span className="surface-token" data-chip>{refusalWord(discardOutcome)}</span> : null}
        </div>
      </div>
    </SurfaceLedgerRow>
  );
}

/* ── the one DELIVERY history ──────────────────────────────────────── */

type HistoryRow =
  | { kind: "manual"; id: string; at: string; to: string | null }
  | { kind: "send"; id: string; at: string; s: Send };

export function historyOf(update: ProjectUpdate, sends: Send[]): HistoryRow[] {
  const rows: HistoryRow[] = [
    ...update.deliveries.map((d) => ({ kind: "manual" as const, id: d.id, at: d.deliveredAt, to: d.deliveredTo })),
    ...sends.filter((s) => s.state === "sent" || s.state === "unknown").map((s) => ({ kind: "send" as const, id: s.id, at: s.settled_at ?? s.created_at, s })),
  ];
  return rows.sort((a, b) => a.at.localeCompare(b.at));
}

function ProofCell({ s }: { s: Send }) {
  const p = s.proof ?? {};
  if (s.channel === "file") return <span className="surface-token p10-proof-path" data-chip data-testid="proof">{String(p.path ?? "")}</span>;
  if (s.channel === "email") return <span className="surface-token" data-chip data-testid="proof">ID {String(p.message_id ?? "")}</span>;
  const url = String(p.url ?? "");
  return (
    <Button dense variant="ghost" className="desk-chip quiet" data-testid="proof" title={url} onClick={() => openFar(url)}>
      {targetToken(s.channel, s.target)}
    </Button>
  );
}

export function DeliveryHistory({ ctrl, update, sends }: { ctrl: UpdateController; update: ProjectUpdate; sends: Send[] }) {
  const rows = historyOf(update, sends);
  const ok = rows.filter((r) => r.kind === "manual" || r.s.state === "sent").length;
  const unknown = rows.length - ok;
  const head = ok > 0 ? `${SEND_WORDS.history} ${ok}${unknown ? ` · UNKNOWN ${unknown}` : ""}` : unknown ? `${SEND_WORDS.history} · UNKNOWN ${unknown}` : SEND_WORDS.history;
  return (
    <div data-p10="history" data-testid="delivery-section">
      <SurfaceSection label={head}>
        <div className="update-deliver-line p10-manual" data-testid="deliver-line">
          <span className="update-deliver-to">
            <StringGadget label="To" value={ctrl.deliverTo} onChange={ctrl.setDeliverTo} placeholder="To"
              disabled={ctrl.deliverBusy || ctrl.deliverLocked}
              inputProps={{ "data-testid": "deliver-to" } as never} />
          </span>
          <Button dense variant="ghost" loading={ctrl.deliverBusy} onClick={() => void ctrl.markDelivered()}
            data-testid={ctrl.deliverOutcome.kind === "uncertain" ? "deliver-retry" : "deliver-verb"}>
            {ctrl.deliverOutcome.kind === "uncertain" ? "Retry" : "Mark delivered"}
          </Button>
        </div>
        {rows.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="delivery-history">
              {rows.map((r) => {
                if (r.kind === "manual") {
                  return (
                    <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                      lead={<StateChip state="success" label="" icon="✓" />}
                      primary={<span className="surface-primary">{r.to ?? "—"}</span>}
                      cells={<>
                        <span className="surface-token" data-chip data-testid="history-word">{SENT_WORD.manual}</span>
                        <span className="surface-token" data-chip>MANUAL</span>
                        <span className="surface-token" data-chip>{stamp(r.at)}</span>
                      </>} />
                  );
                }
                const s = r.s;
                const unknownRow = s.state === "unknown";
                return (
                  <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                    lead={unknownRow ? <StateChip state="warning" label="" icon="⚠" /> : <StateChip state="success" label="" icon="✓" />}
                    primary={<span className="surface-primary">{s.destination_name}</span>}
                    cells={<>
                      {unknownRow ? (
                        <>
                          <span className="surface-token" data-chip data-tone="warn" data-testid="history-word">RESULT UNKNOWN</span>
                          <span className="surface-token" data-chip data-code={s.reason ?? ""}>{unknownWord(s.reason ?? "no_answer")}</span>
                          {farSide(s.channel, s.target, s.account) ? (
                            <Button dense variant="ghost" data-testid="history-check"
                              onClick={() => openFar(farSide(s.channel, s.target, s.account))}>
                              {`${SEND_WORDS.check} ${targetToken(s.channel, s.target)}`}
                            </Button>
                          ) : <span className="surface-token p10-proof-path" data-chip>{`CHECK ${String(s.target.folder ?? "")}`}</span>}
                        </>
                      ) : (
                        <>
                          <span className="surface-token" data-chip data-tone="ok" data-testid="history-word">
                            {s.channel === "file" ? "SAVED TO" : SENT_WORD[s.channel]}
                          </span>
                          <ProofCell s={s} />
                        </>
                      )}
                      <span className="surface-token" data-chip>{stamp(r.at)}</span>
                    </>} />
                );
              })}
            </ul>
          </SurfaceLedger>
        ) : null}
        {ctrl.deliverOutcome.kind === "refused" ? (
          <span className="p10-outcome" data-testid="deliver-refused" data-code={ctrl.deliverOutcome.code}>
            <StateChip state="failure" label="REFUSED" />
            <span className="surface-token" data-chip>{refusalWord(ctrl.deliverOutcome.code)}</span>
          </span>
        ) : ctrl.deliverOutcome.kind === "uncertain" ? (
          <span className="p10-outcome" data-testid="deliver-uncertain"><StateChip state="warning" label="NO ANSWER · RESULT UNKNOWN" /></span>
        ) : null}
      </SurfaceSection>
    </div>
  );
}

/** The update list's chips: DELIVERY ×N (✓ rows), UNKNOWN ×M, PREPARED ×K.
 *  No chip at zero. */
export function ListChips({ update }: { update: ProjectUpdate }) {
  const { sends } = useSends(update.id);
  const rows = historyOf(update, sends);
  const ok = rows.filter((r) => r.kind === "manual" || r.s.state === "sent").length;
  const unknown = rows.length - ok;
  const prep = sends.filter((s) => s.state === "prepared").length;
  return (
    <>
      {prep > 0 ? <span data-p10="list-chip" data-testid="update-prepared-chip"><StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${prep}`} /></span> : null}
      {unknown > 0 ? <span data-p10="list-chip" data-testid="update-unknown-chip"><StateChip state="warning" label={`UNKNOWN ×${unknown}`} /></span> : null}
      {ok > 0 ? <span data-p10="list-chip" data-testid="update-delivered-chip"><StateChip state="success" label={`${SEND_WORDS.history} ×${ok}`} /></span> : null}
    </>
  );
}

/* PHILO-10-04 canvas A (PROPOSAL): the SEND well on a published update, the
 * PREPARED rows, and the one DELIVERY history. Library species only:
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
 *
 * ROUND TWO (Codex Astra r1 on #693):
 * - A result never lives only inside a branch that goes away (F1). A prepared
 *   send that ended (sent, failed, unknown, discarded) stays in the PREPARED
 *   group as a closed result row, from its stored record; a destination row
 *   carries its last send's result (sent, unknown, failed).
 * - The history is story 01's ONE table (F4): `update.deliveries`, read again
 *   after every settle, each row by its own `outcome` and `channel`
 *   (`isDelivered`, web/src/features/project-room/update/model.ts). No second
 *   list, no double count.
 * - Unreadable is never empty (F5): a read or a preview that gets no answer
 *   names it and offers Retry.
 * - The well reads its destinations again on the Settings change signal and
 *   on window focus (F2): no reload after setup.
 */
import { useCallback, useEffect, useState, useSyncExternalStore, type ReactNode } from "react";
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
import { apiFetch } from "@w/lib/api";
import { fetchConnections } from "@w/pages/cores/connections/api";
import { chipLabel } from "@w/pages/cores/connections/ConnectionsPane";
import type { ConnectionsResponse, ConnectionState } from "@w/pages/cores/connections/api";
import type { UpdateController } from "@w/features/project-room/update/useUpdateController";
import { decodeDelivery, isDelivered, type Delivery, type ProjectUpdate } from "@w/features/project-room/update/model";
import {
  CHANNEL_WORD, DEST_CHANGED, SENT_WORD, SEND_WORDS, egressOf, failedWord, farSide, refusedWord, requestDestinationsFocus,
  stamp, targetToken, unknownWord, wire, Refusal, type Channel, type Destination, type Preview, type Send,
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
  preparedOpen: new Map<string, string | null>(),    // updateId -> the one open prepared row (absent = the first)
  holds: new Map<string, Held>(),                     // `${updateId}|${target}` -> the held press
  outcomes: new Map<string, Outcome>(),
  busy: new Set<string>(),
  tick: 0,
  subs: new Set<() => void>(),
};
const bump = () => { store.tick++; store.subs.forEach((f) => f()); };
const useStore = () => useSyncExternalStore((f) => { store.subs.add(f); return () => store.subs.delete(f); }, () => store.tick);

/* ── the reads (each names its failure) ──────────────────────────────── */

type Read<T> = { data: T | null; failed: boolean; reload: () => void };

export function useSends(updateId: string): Read<Send[]> {
  const [data, setData] = useState<Send[] | null>(null);
  const [failed, setFailed] = useState(false);
  const reload = useCallback(() => {
    void wire.sends(updateId).then((r) => { setData(r); setFailed(false); }).catch(() => setFailed(true));
  }, [updateId]);
  const tick = useStore();
  useEffect(() => { reload(); }, [reload, tick]);
  return { data, failed, reload };
}

function useDestinations(): Read<Destination[]> {
  const [data, setData] = useState<Destination[] | null>(null);
  const [failed, setFailed] = useState(false);
  const reload = useCallback(() => {
    void wire.destinations().then((r) => { setData(r); setFailed(false); }).catch(() => setFailed(true));
  }, []);
  useEffect(() => {
    reload();
    window.addEventListener(DEST_CHANGED, reload);   // a save or a remove in Settings
    window.addEventListener("focus", reload);        // he comes back to the window
    return () => { window.removeEventListener(DEST_CHANGED, reload); window.removeEventListener("focus", reload); };
  }, [reload]);
  return { data, failed, reload };
}

/** Story 01's one table, read again after each settle. The build adds this
 *  re-read to the controller (today `current` is a snapshot of the list
 *  read); `proof` and `sendId` are the model fields story 04 adds to
 *  `Delivery` (`proof_json`, `send_id` are on the wire since story 01). */
type HistoryRow = Delivery & { proof: Record<string, unknown> | null; sendId: string | null };
function useHistory(update: ProjectUpdate): Read<HistoryRow[]> {
  const [data, setData] = useState<HistoryRow[] | null>(null);
  const [failed, setFailed] = useState(false);
  const tick = useStore();
  const reload = useCallback(() => {
    void apiFetch<{ updates: Record<string, unknown>[] }>(`/api/projects/${encodeURIComponent(update.projectId)}/updates`)
      .then((r) => {
        const raw = r.updates.find((u) => u.id === update.id);
        const rows = ((raw?.deliveries as Record<string, unknown>[] | undefined) ?? []).map((d) => {
          let proof: Record<string, unknown> | null = null;
          try { proof = d.proof_json ? JSON.parse(String(d.proof_json)) : null; } catch { proof = null; }
          return { ...decodeDelivery(d), proof, sendId: d.send_id ? String(d.send_id) : null };
        });
        setData(rows); setFailed(false);
      })
      .catch(() => setFailed(true));
  }, [update.id, update.projectId]);
  useEffect(() => { reload(); }, [reload, tick, update.deliveries.length]);
  return { data, failed, reload };
}

function useConnections() {
  const [c, setC] = useState<ConnectionsResponse | null>(null);
  useEffect(() => {
    const read = () => void fetchConnections().then(setC).catch(() => setC(null));
    read();
    window.addEventListener("focus", read);
    return () => window.removeEventListener("focus", read);
  }, []);
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

/** The preview: its fields, then the verbs, then the body. The verbs sit
 *  above the body so Send and its result are in view at 393 without a
 *  scroll through the whole text. */
function PreviewWell({ preview, testid, verbs }: { preview: Preview; testid: string; verbs: ReactNode }) {
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
        {verbs}
        <div className="p10-preview-body" data-testid="send-preview-body">
          {preview.body_kind === "markdown" ? <Material>{preview.body}</Material> : <div className="p10-preview-text">{preview.body}</div>}
        </div>
      </SurfaceWell>
    </div>
  );
}

/** A read that got no answer: named, with Retry. Never shown as empty. */
function Unreadable({ what, testid, onRetry }: { what: string; testid: string; onRetry: () => void }) {
  return (
    <div className="p10-none" data-testid={testid}>
      <StateChip state="failure" label={`${SEND_WORDS.cannotRead} ${what}`} />
      <Button dense variant="ghost" data-testid={`${testid}-retry`} onClick={onRetry}>{SEND_WORDS.retry}</Button>
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

/** A destination row's last send, from the stored record (it outlives the
 *  open row and a reload). */
function LastChip({ s }: { s: Send | undefined }) {
  if (!s) return null;
  if (s.state === "sent") return <span data-testid="send-last-sent"><StateChip state="success" icon="✓" label={`${SENT_WORD[s.channel]} ${stamp(s.settled_at).slice(-5)}`} /></span>;
  if (s.state === "unknown") return <span data-testid="send-last-unknown"><StateChip state="warning" label={SEND_WORDS.lastUnknown} /></span>;
  if (s.state === "failed") return <span data-testid="send-last-failed" data-code={s.reason ?? ""}><StateChip state="failure" label={SEND_WORDS.lastFailed} /></span>;
  return null;
}

function openFar(url: string | null) { if (url) window.open(url, "_blank", "noopener"); }

/** The proof of a SENT row, exact as the channel gave it (no uppercasing). */
function ProofCell({ channel, proof, target }: { channel: string; proof: Record<string, unknown> | null; target?: Record<string, string | number> }) {
  const p = proof ?? {};
  if (channel === "file") return <span className="surface-token p10-literal p10-proof-path" data-chip data-testid="proof">{String(p.path ?? "")}</span>;
  if (channel === "email") return <span className="surface-token p10-literal" data-chip data-testid="proof">{`ID ${String(p.message_id ?? "")}`}</span>;
  const url = String(p.url ?? "");
  return (
    <Button dense variant="ghost" className="desk-chip quiet" data-testid="proof" title={url} onClick={() => openFar(url)}>
      {target ? targetToken(channel as Channel, target) : url.replace(/^https:\/\//, "")}
    </Button>
  );
}

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

export function SendWell({ update, sendsRead }: { update: ProjectUpdate; sendsRead: Read<Send[]> }) {
  useStore();
  const dests = useDestinations();
  const conns = useConnections();
  const uid = update.id;
  const picked = store.picked.get(uid) ?? null;
  const [preview, setPreview] = useState<{ id: string; digest: string; preview: Preview } | { id: string; failed: true } | null>(null);
  const [previewTry, setPreviewTry] = useState(0);
  useEffect(() => {
    if (!picked) { setPreview(null); return; }
    let live = true;
    setPreview(null);
    void wire.preview(uid, picked)
      .then((p) => { if (live) setPreview({ id: picked, digest: p.payload_digest, preview: p.preview }); })
      .catch(() => { if (live) setPreview({ id: picked, failed: true }); });
    return () => { live = false; };
  }, [uid, picked, previewTry]);

  const sends = sendsRead.data ?? [];
  const reload = sendsRead.reload;
  // Every send someone else prepared, in the order prepared: the open ones
  // and the ones that ended (their result stays here, F1).
  const prepared = sends.filter((s) => s.prepared_by_kind !== "owner" && s.state !== "dispatching");
  const waiting = prepared.filter((s) => s.state === "prepared");
  const openPrepared = store.preparedOpen.has(uid) ? store.preparedOpen.get(uid) : waiting[0]?.id ?? null;
  const lastFor = (destId: string) =>
    [...sends].reverse().find((s) => s.destination_id === destId && (s.state === "sent" || s.state === "unknown" || s.state === "failed"));
  const destinations = dests.data;

  return (
    <div data-p10="send" data-testid="send-well">
      <SurfaceSection label={SEND_WORDS.section}>
        {sendsRead.failed ? (
          <Unreadable what="SENDS" testid="sends-unreadable" onRetry={reload} />
        ) : prepared.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepared-list">
              {prepared.map((s) => (
                <PreparedRow key={s.id} uid={uid} s={s} reload={reload} conns={conns}
                  open={s.state === "prepared" && openPrepared === s.id}
                  onToggle={() => { store.preparedOpen.set(uid, openPrepared === s.id ? null : s.id); bump(); }}
                  dest={destinations?.find((d) => d.id === s.destination_id)} />
              ))}
            </ul>
          </SurfaceLedger>
        ) : null}
        {dests.failed ? (
          <Unreadable what="DESTINATIONS" testid="destinations-unreadable" onRetry={dests.reload} />
        ) : destinations === null ? null : destinations.length === 0 ? (
          <div className="p10-none" data-testid="send-none">
            <span className="surface-token" data-chip>{SEND_WORDS.noDestination}</span>
            <Button dense variant="primary" data-testid="send-add-destination"
              onClick={() => { requestDestinationsFocus(); useDesk.getState().openSurfaceWindow("configure-settings", "integrations"); }}>
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
                const pv = preview && preview.id === d.id ? preview : null;
                const verbs = (
                  <div className="p10-verbs" data-testid="send-verbs">
                    <Button dense variant="primary" loading={busy}
                      disabled={!pv || "failed" in pv}
                      data-testid={lost ? "send-retry" : "send-verb"}
                      onClick={() => void press(uid, d.id, () => ({
                        update_id: uid, destination_id: d.id,
                        preview_digest: (pv as { digest: string }).digest,
                      } as Held["body"]), reload)}>
                      {lost ? SEND_WORDS.retry : last ? SEND_WORDS.sendAgain : SEND_WORDS.send}
                    </Button>
                    <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    {last?.state === "unknown" && farSide(d.channel, d.target, d.account) ? (
                      <Button dense variant="ghost" data-testid="send-check"
                        onClick={() => openFar(farSide(d.channel, d.target, d.account))}>{`${SEND_WORDS.check} ${targetToken(d.channel, d.target)}`}</Button>
                    ) : null}
                    <OutcomeLine o={o} />
                    {o.kind === "settled" && o.send.state === "sent" ? (
                      <span className="p10-outcome" data-testid="send-sent">
                        <StateChip state="success" icon="✓" label={SENT_WORD[o.send.channel]} />
                        <ProofCell channel={o.send.channel} proof={o.send.proof} target={o.send.target} />
                      </span>
                    ) : o.kind === "settled" && o.send.state === "unknown" ? (
                      <span className="p10-outcome" data-testid="send-unknown">
                        <StateChip state="warning" label={SEND_WORDS.unknownChip} />
                        <span className="surface-token" data-chip>{unknownWord(o.send.reason ?? "no_answer")}</span>
                      </span>
                    ) : null}
                  </div>
                );
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
                      <span className="surface-token p10-literal p10-target" data-chip>{targetToken(d.channel, d.target)}</span>
                      {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                      <LastChip s={last} />
                      <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    </>}
                  >
                    {open ? (
                      <div className="p10-open" data-testid="send-open" data-destination={d.name}>
                        {pv && !("failed" in pv) ? <PreviewWell preview={pv.preview} testid="send-preview" verbs={verbs} /> : null}
                        {pv && "failed" in pv ? (
                          <div className="p10-verbs" data-testid="preview-failed">
                            <StateChip state="failure" label={SEND_WORDS.noPreview} />
                            <span className="surface-token" data-chip>NO ANSWER</span>
                            <Button dense variant="ghost" data-testid="preview-retry" onClick={() => setPreviewTry((n) => n + 1)}>{SEND_WORDS.retry}</Button>
                          </div>
                        ) : null}
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

/** One send someone else prepared. While it waits: Send and Discard (one
 *  row open at a time; the first one opens). When it ended: a closed result
 *  row that stays (F1). */
function PreparedRow({ uid, s, reload, conns, dest, open, onToggle }: {
  uid: string; s: Send; reload: () => void; conns: ConnectionsResponse | null; dest: Destination | undefined;
  open: boolean; onToggle: () => void;
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
  const by = BY[s.prepared_by_kind] ?? `BY ${s.prepared_by_identity.toUpperCase()}`;
  const waiting = s.state === "prepared";

  const result = waiting ? null
    : s.state === "sent" ? <><StateChip state="success" icon="✓" label={SENT_WORD[s.channel]} /><ProofCell channel={s.channel} proof={s.proof} target={s.target} /></>
    : s.state === "failed" ? <><StateChip state="failure" label="FAILED" /><span className="surface-token" data-chip>{failedWord(s.reason ?? "")}</span><span className="surface-token" data-chip>NOTHING SENT</span></>
    : s.state === "unknown" ? <><StateChip state="warning" label={SEND_WORDS.unknownChip} /><span className="surface-token" data-chip>{unknownWord(s.reason ?? "no_answer")}</span></>
    : <StateChip state="idle" label={SEND_WORDS.discarded} />;

  return (
    <SurfaceLedgerRow
      data-testid={waiting ? "prepared-row" : "prepared-result"}
      wrap
      open={open}
      expands={waiting}
      lineLabel={`${s.destination_name}, ${waiting ? SEND_WORDS.prepared : s.state}`}
      onToggle={waiting ? onToggle : undefined}
      lead={waiting ? <StateChip state="active" icon="◆" label="" /> : <span className="p10-pick" aria-hidden="true">·</span>}
      primary={<span className="surface-primary" data-destination={s.destination_name} data-state={s.state}>{s.destination_name}</span>}
      cells={<>
        {waiting ? <StateChip state="active" icon="◆" label={SEND_WORDS.prepared} /> : <span className="p10-inline" data-testid="prepared-result-word" data-state={s.state} data-code={s.reason ?? ""}>{result}</span>}
        <span className="surface-token" data-chip data-testid="prepared-by">{by}</span>
        <span className="surface-token" data-chip>REV {s.draft_revision}</span>
        {waiting && o.kind === "refused" ? (
          <span data-testid="prepared-refused-chip" data-code={o.code}><StateChip state="failure" label={refusedWord(o.code)} /></span>
        ) : null}
        <span className="surface-token" data-chip>{stamp(s.settled_at ?? s.created_at)}</span>
        {waiting && acc ? <StateChip state={acc.state} label={acc.label} /> : null}
        {waiting ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
      </>}
    >
      {waiting && open ? (
        <div className="p10-open" data-testid="prepared-open">
          <PreviewWell preview={s.preview} testid="prepared-preview" verbs={
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
                    .then(() => { store.outcomes.delete(k); store.preparedOpen.delete(uid); bump(); })
                    .catch((e) => setDiscardOutcome(e instanceof Refusal ? e.code : "no_answer"))
                    .finally(() => { setDiscardBusy(false); reload(); });
                }} />
              <OutcomeLine o={o} />
              {discardOutcome ? <span className="surface-token" data-chip>{refusalWord(discardOutcome)}</span> : null}
            </div>
          } />
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

/* ── the one DELIVERY history (story 01's table) ─────────────────────── */

export function DeliveryHistory({ ctrl, update, sends }: { ctrl: UpdateController; update: ProjectUpdate; sends: Send[] }) {
  const history = useHistory(update);
  const rows = history.data ?? [];
  const ok = rows.filter(isDelivered).length;
  const reasonOf = (sendId: string | null) => sends.find((s) => s.id === sendId)?.reason ?? null;
  const channelOf = (sendId: string | null) => sends.find((s) => s.id === sendId);
  return (
    <div data-p10="history" data-testid="delivery-section">
      <SurfaceSection label={ok > 0 ? `${SEND_WORDS.history} ${ok}` : SEND_WORDS.history}>
        <div className="update-deliver-line p10-manual" data-testid="deliver-line">
          <span className="update-deliver-to">
            <StringGadget label="To" value={ctrl.deliverTo} onChange={ctrl.setDeliverTo} placeholder="To"
              disabled={ctrl.deliverBusy || ctrl.deliverLocked}
              inputProps={{ "data-testid": "deliver-to" } as never} />
          </span>
          <Button dense variant="ghost" loading={ctrl.deliverBusy} onClick={() => void ctrl.markDelivered().then(history.reload)}
            data-testid={ctrl.deliverOutcome.kind === "uncertain" ? "deliver-retry" : "deliver-verb"}>
            {ctrl.deliverOutcome.kind === "uncertain" ? "Retry" : "Mark delivered"}
          </Button>
        </div>
        {history.failed ? <Unreadable what="HISTORY" testid="history-unreadable" onRetry={history.reload} /> : null}
        {rows.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="delivery-history">
              {rows.map((r) => {
                const send = channelOf(r.sendId);
                if (!isDelivered(r)) {
                  // Story 01's UNKNOWN row, as it renders today; Check opens the far side.
                  const far = send ? farSide(send.channel, send.target, send.account) : null;
                  const reason = reasonOf(r.sendId);
                  return (
                    <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                      lead={<span data-outcome={r.outcome}><StateChip state="warning" label="" icon="⚠" /></span>}
                      primary={<span className="surface-primary" data-to={r.deliveredTo ?? ""}>{`${SEND_WORDS.unknownChip} · CHECK ${r.deliveredTo ?? "—"}`}</span>}
                      cells={<>
                        {reason ? <span className="surface-token" data-chip data-code={reason}>{unknownWord(reason)}</span> : null}
                        {far ? <Button dense variant="ghost" data-testid="history-check" onClick={() => openFar(far)}>{SEND_WORDS.check}</Button> : null}
                        <span className="surface-token" data-chip>{stamp(r.deliveredAt)}</span>
                      </>} />
                  );
                }
                const manual = r.channel === "manual";
                return (
                  <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                    lead={<span data-outcome={r.outcome}><StateChip state="success" label="" icon="✓" /></span>}
                    primary={<span className="surface-primary" data-to={r.deliveredTo ?? ""}>{r.deliveredTo ?? "—"}</span>}
                    cells={<>
                      <span className="surface-token" data-chip data-tone="ok" data-testid="history-word">
                        {manual ? SENT_WORD.manual : SENT_WORD[r.channel as Channel] ?? r.channel.toUpperCase()}
                      </span>
                      {manual ? <span className="surface-token" data-chip>MANUAL</span> : <ProofCell channel={r.channel} proof={r.proof} target={send?.target} />}
                      <span className="surface-token" data-chip>{stamp(r.deliveredAt)}</span>
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

/** The update list's chips, over story 01's table: DELIVERY ×N (isDelivered
 *  rows), RESULT UNKNOWN ×M (story 01's chip, unchanged), PREPARED ×K (still
 *  waiting). No chip at zero. */
export function ListChips({ update }: { update: ProjectUpdate }) {
  const { data } = useSends(update.id);
  const ok = update.deliveries.filter(isDelivered).length;
  const unknown = update.deliveries.length - ok;
  const prep = (data ?? []).filter((s) => s.state === "prepared").length;
  return (
    <>
      {prep > 0 ? <span data-p10="list-chip" data-testid="update-prepared-chip"><StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${prep}`} /></span> : null}
      {unknown > 0 ? <span data-p10="list-chip" data-testid="update-unknown-chip"><StateChip state="warning" label={`${SEND_WORDS.unknownChip} ×${unknown}`} /></span> : null}
      {ok > 0 ? <span data-p10="list-chip" data-testid="update-delivered-chip"><StateChip state="success" label={`${SEND_WORDS.history} ×${ok}`} /></span> : null}
    </>
  );
}

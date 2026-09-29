/* PHILO-10-04: the SEND well on a published update, the PREPARED rows, and
 * the one DELIVERY history (story 01's table). Built to the owner's ratified
 * canvas (assets/story-04-send-canvas/, "Ratify as drawn", 2026-09-29).
 * Library species only: SurfaceSection, SurfaceLedger, SurfaceLedgerRow,
 * SurfaceWell, StateChip, EgressChip, Material, Button, ConfirmVerb,
 * StringGadget.
 *
 * THE PRESS RULE: one press = one {update, destination or prepared row,
 * command_id, preview digest}, held PER UPDATE AND TARGET in a module store
 * that survives Back and opening another update. A lost answer keeps all
 * four; Retry sends the same key, and the hub's replay answers the settled
 * row, never a second dispatch. A new key only after the result is known. A
 * channel UNKNOWN is a settled record: "Send again" is a NEW send with a NEW
 * key; the product never sends again by itself.
 *
 * A1: the pick opens the preview and Send in place, under the row.
 * A3: prepared sends first, ONE preview open (the first), each other a click
 * away; a prepared send that ended stays in place as its result.
 * A destination's header and its open receipt come from ONE source: its
 * latest send by `dispatch_started_at` (Codex Astra r2 F1, r3 F1).
 * A read that gets no answer names it and offers Retry; unreadable is never
 * shown as empty.
 */
import { useCallback, useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
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
} from "../../desk/surface";
import { useDesk } from "../../desk/store";
import { fetchConnections, type ConnectionsResponse, type ConnectionState } from "../../pages/cores/connections/api";
import { chipLabel } from "../../pages/cores/connections/ConnectionsPane";
import type { UpdateController } from "../project-room/update/useUpdateController";
import { isDelivered, type Delivery, type ProjectUpdate } from "../project-room/update/model";
import {
  CHANNEL_WORD, DEST_CHANGED, SENT_WORD, SEND_WORDS, commandId, egressOf, failedWord, farSide, previewOf,
  refusedWord, requestDestinationsFocus, sentWord, stamp, targetToken, unknownWord, wire, Refusal,
  type Channel, type Destination, type Preview, type Send, type WirePreview,
} from "./channels";
import "./channels.css";

/* ── the per-update store (survives Back and another update) ───────────── */

type Outcome =
  | { kind: "none" }
  | { kind: "refused"; code: string; at: number }
  | { kind: "lost" }
  | { kind: "settled"; send: Send };
type Held = { key: string; body: { send_id?: string; update_id?: string; destination_id?: string; preview_digest?: string } };
const store = {
  picked: new Map<string, string | null>(),          // updateId -> destination id
  preparedOpen: new Map<string, string | null>(),    // updateId -> the one open prepared row (absent = the first)
  holds: new Map<string, Held>(),                     // `${updateId}|${target}` -> the held press
  outcomes: new Map<string, Outcome>(),
  busy: new Set<string>(),
  /** Records the hub RETURNED to a press (send, discard): a later read that
   *  fails or is stale can never hide them (Codex Astra r1 F1 on #697). */
  known: new Map<string, Send>(),
  tick: 0,
  subs: new Set<() => void>(),
};
const bump = () => { store.tick++; store.subs.forEach((f) => f()); };
const useStore = () =>
  useSyncExternalStore((f) => { store.subs.add(f); return () => { store.subs.delete(f); }; }, () => store.tick);

/** Test seam: forget every held press (a fresh page has none). */
export function resetSendStore() {
  store.picked.clear(); store.preparedOpen.clear(); store.holds.clear(); store.outcomes.clear(); store.busy.clear();
  store.known.clear(); bump();
}

/* ── the reads (each names its failure) ──────────────────────────────── */

export type Read<T> = { data: T | null; failed: boolean; reload: () => void };

/** One update's sends. While any row is `dispatching` the well reads again;
 *  when the last one settles, `onSettled` runs once (the history read). */
export function useSends(updateId: string, onSettled?: () => void): Read<Send[]> {
  const [data, setData] = useState<Send[] | null>(null);
  const [failed, setFailed] = useState(false);
  const reload = useCallback(() => {
    void wire.sends(updateId).then((r) => { setData(r); setFailed(false); }).catch(() => setFailed(true));
  }, [updateId]);
  const tick = useStore();
  useEffect(() => { reload(); }, [reload, tick]);
  const running = (data ?? []).some((s) => s.state === "dispatching");
  const wasRunning = useRef(false);
  const settled = useRef(onSettled);
  settled.current = onSettled;
  useEffect(() => {
    if (running) {
      wasRunning.current = true;
      const t = setTimeout(reload, 700);
      return () => clearTimeout(t);
    }
    if (wasRunning.current) { wasRunning.current = false; settled.current?.(); }
    return undefined;
  }, [running, data, reload]);
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

export function useConnections(): ConnectionsResponse | null {
  const [c, setC] = useState<ConnectionsResponse | null>(null);
  useEffect(() => {
    let live = true;
    const read = () => void fetchConnections().then((r) => { if (live) setC(r); }).catch(() => { if (live) setC(null); });
    read();
    window.addEventListener("focus", read);
    return () => { live = false; window.removeEventListener("focus", read); };
  }, []);
  return c;
}

/** The account state a destination depends on (the Phase 9 B1 words, the
 *  Connections chip words). Null for a folder. Email: the key only present
 *  or absent (never the key). */
export function accountChip(
  d: Pick<Destination, "channel" | "account"> & { connection?: Destination["connection"] },
  c: ConnectionsResponse | null,
): { state: "success" | "warning" | "idle" | "failure"; label: string; code: string } | null {
  if (d.channel === "file") return null;
  if (d.channel === "email") {
    // Present or absent only, and only when known (the list read does not open the keychain).
    if (typeof d.account.key_present !== "boolean") return null;
    return d.account.key_present
      ? { state: "success", label: "KEY SET", code: "key_present" }
      : { state: "warning", label: "NO KEY", code: "email_key_missing" };
  }
  const tool = c?.tools.find((t) => t.provider_id === d.channel);
  let state: ConnectionState = "not_configured";
  if (d.channel === "github") {
    state = (d.connection?.state ?? tool?.state ?? "not_configured") as ConnectionState;
    const login = tool?.account?.login;
    if (state === "connected" && login && d.account.login && login !== d.account.login) {
      return { state: "failure", label: "ACCOUNT CHANGED", code: "github_identity_changed" };
    }
  } else {
    const conn = tool?.connections?.find((x) => x.account.site === d.account.site && x.account.email === d.account.email);
    state = (d.connection?.state ?? conn?.state ?? "not_configured") as ConnectionState;
  }
  const map: Record<string, "success" | "warning" | "idle" | "failure"> = {
    connected: "success", owner_action_required: "warning", never_checked: "idle", not_configured: "idle",
    unavailable: "failure", degraded: "warning",
  };
  return { state: map[state] ?? "idle", label: chipLabel(state, d.channel).toUpperCase(), code: state };
}

/* ── pieces ────────────────────────────────────────────────────────── */

/** The preview: its fields, then the verbs, then the body. The verbs sit
 *  above the body so Send and its result are in view at 393. */
function PreviewWell({ preview, testid, verbs }: { preview: Preview; testid: string; verbs: ReactNode }) {
  return (
    <div className="send-preview" data-testid={testid}>
      <SurfaceWell>
        <dl className="send-fields">
          {preview.fields.map((f) => (
            <div key={f.label} className="send-field" data-testid="send-preview-field">
              <dt className="surface-token">{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
        {verbs}
        <div className="send-preview-body" data-testid="send-preview-body">
          {preview.body_kind === "markdown" ? <Material>{preview.body}</Material> : <div className="send-preview-text">{preview.body}</div>}
        </div>
      </SurfaceWell>
    </div>
  );
}

/** A read that got no answer: named, with Retry. Never shown as empty. */
export function Unreadable({ what, testid, onRetry }: { what: string; testid: string; onRetry: () => void }) {
  return (
    <div className="send-line" data-testid={testid}>
      <StateChip state="failure" label={`${SEND_WORDS.cannotRead} ${what}`} />
      <Button dense variant="ghost" data-testid={`${testid}-retry`} onClick={onRetry}>{SEND_WORDS.retry}</Button>
    </div>
  );
}

function OutcomeLine({ o }: { o: Outcome }) {
  if (o.kind === "refused") {
    return (
      <span className="send-line" data-testid="send-refused" data-code={o.code}>
        <StateChip state="failure" label="REFUSED" />
        <span className="surface-token" data-chip>{refusedWord(o.code)}</span>
        <span className="surface-token" data-chip>{SEND_WORDS.nothingSent}</span>
      </span>
    );
  }
  if (o.kind === "lost") {
    return (
      <span className="send-line" data-testid="send-lost">
        <StateChip state="warning" label={SEND_WORDS.lost} />
      </span>
    );
  }
  return null;
}

/** A destination row's last send, from the stored record. */
function LastChip({ s }: { s: Send | undefined }) {
  if (!s) return null;
  if (s.state === "sent") return <span data-testid="send-last-sent"><StateChip state="success" label={`${SENT_WORD[s.channel] ?? sentWord(s.channel)} ${stamp(s.settled_at).slice(-5)}`} /></span>;
  if (s.state === "unknown") return <span data-testid="send-last-unknown"><StateChip state="warning" label={SEND_WORDS.lastUnknown} /></span>;
  if (s.state === "failed") return <span data-testid="send-last-failed" data-code={s.reason ?? ""}><StateChip state="failure" label={SEND_WORDS.lastFailed} /></span>;
  if (s.state === "dispatching") return <span data-testid="send-last-running"><StateChip state="active" icon="◆" label={SEND_WORDS.sending} /></span>;
  return null;
}

/** The destination's latest send: the one receipt the open row shows. */
function LatestReceipt({ s }: { s: Send | undefined }) {
  if (!s) return null;
  if (s.state === "sent") return (
    <span className="send-line" data-testid="send-sent" data-receipt="latest" data-state="sent">
      <StateChip state="success" label={sentWord(s.channel)} />
      <ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} />
    </span>
  );
  if (s.state === "failed") return (
    <span className="send-line" data-testid="send-failed" data-receipt="latest" data-state="failed" data-code={s.reason ?? ""}>
      <StateChip state="failure" label="FAILED" />
      <span className="surface-token" data-chip>{failedWord(s.reason ?? "")}</span>
      <span className="surface-token" data-chip>{SEND_WORDS.nothingSent}</span>
    </span>
  );
  if (s.state === "unknown") return (
    <span className="send-line" data-testid="send-unknown" data-receipt="latest" data-state="unknown">
      <StateChip state="warning" label={SEND_WORDS.unknownChip} />
      <span className="surface-token" data-chip>{(s.reason ? unknownWord(s.reason) : "NO ANSWER")}</span>
    </span>
  );
  if (s.state === "dispatching") return (
    <span className="send-line" data-testid="send-running" data-receipt="latest" data-state="dispatching">
      <StateChip state="active" icon="◆" label={SEND_WORDS.sending} />
    </span>
  );
  return null;
}

function openFar(url: string | null) { if (url) window.open(url, "_blank", "noopener"); }

/** Where a SENT row's proof opens: the comment, the work item, the post. */
export function proofLink(channel: string, proof: Record<string, unknown>, target?: Record<string, string | number>,
  account?: Record<string, string | boolean>): string {
  const url = String(proof.url ?? "");
  const site = String(account?.site ?? "");
  if (channel === "jira" && site) return `https://${site}/browse/${String(proof.key ?? target?.key ?? "")}`;
  if (channel === "confluence" && url.startsWith("/") && site) return `https://${site}/wiki${url}`;
  return url;
}

/** The proof of a SENT row, exact as the channel gave it (no uppercasing). */
function ProofCell({ channel, proof, target, account }: {
  channel: string; proof: Record<string, unknown> | null; target?: Record<string, string | number>;
  account?: Record<string, string | boolean>;
}) {
  const p = proof ?? {};
  if (channel === "file") return <span className="surface-token send-literal send-wrap" data-chip data-testid="proof">{String(p.path ?? "")}</span>;
  if (channel === "email") return <span className="surface-token send-literal" data-chip data-testid="proof">{`ID ${String(p.message_id ?? "")}`}</span>;
  const url = proofLink(channel, p, target, account);
  const label = target ? targetToken(channel as Channel, target) : url.replace(/^https:\/\//, "");
  return url ? (
    <Button dense variant="ghost" className="desk-chip quiet send-literal" data-testid="proof" data-href={url} title={url}
      onClick={() => openFar(url)}>
      {label}
    </Button>
  ) : <span className="surface-token send-literal" data-chip data-testid="proof">{label}</span>;
}

/* ── the press ─────────────────────────────────────────────────────── */

async function press(updateId: string, target: string, fresh: () => Held["body"], reload: () => void, onSettled?: () => void) {
  const k = `${updateId}|${target}`;
  if (store.busy.has(k)) return;                 // a double-click is one press
  let held = store.holds.get(k);
  if (!held) { held = { key: commandId(), body: fresh() }; store.holds.set(k, held); }
  store.busy.add(k); store.outcomes.set(k, { kind: "none" }); bump();
  try {
    const pending = wire.send({ ...held.body, command_id: held.key });
    // Read again once the send has crossed its boundary, so a running send
    // shows as SENDING while it runs.
    const peek = setTimeout(reload, 250);
    const send = await pending.finally(() => clearTimeout(peek));
    store.holds.delete(k);
    store.known.set(send.id, send);
    store.outcomes.set(k, { kind: "settled", send });
  } catch (e) {
    if (e instanceof Refusal) { store.holds.delete(k); store.outcomes.set(k, { kind: "refused", code: e.code, at: Date.now() }); }
    else store.outcomes.set(k, { kind: "lost" });  // keep the update, the key and the body for Retry
  } finally {
    store.busy.delete(k); bump(); reload(); onSettled?.();
  }
}

/** The destination's latest send: the latest to LEAVE, by story 01's
 *  `dispatch_started_at`, never the latest prepared. A running send is the
 *  latest while it runs. */
export function latestFor(sends: Send[], destId: string): Send | undefined {
  return sends
    .filter((s) => s.destination_id === destId && !!s.dispatch_started_at
      && (s.state === "sent" || s.state === "unknown" || s.state === "failed" || s.state === "dispatching"))
    .sort((a, b) => (a.dispatch_seq ?? 0) - (b.dispatch_seq ?? 0)
      || String(a.dispatch_started_at).localeCompare(String(b.dispatch_started_at)))
    .pop();
}

const ENDED = new Set(["sent", "failed", "unknown", "discarded"]);

/** The ONE result source: the last read, with every record the hub returned
 *  to a press merged in. A read row replaces a returned one only when it is
 *  as far along (an ended row, or the returned one still running); a read
 *  that failed or predates the press never hides a known result. */
export function mergeKnown(updateId: string, read: Send[], known: Iterable<Send> = store.known.values()): Send[] {
  const ref = `project_update:${updateId}`;
  const out = new Map(read.map((s) => [s.id, s]));
  for (const k of known) {
    if (k.document_ref !== ref) continue;
    const r = out.get(k.id);
    if (!r || (ENDED.has(k.state) && !ENDED.has(r.state))) out.set(k.id, k);
  }
  return [...out.values()];
}

/* ── the SEND well ─────────────────────────────────────────────────── */

export function SendWell({ update, sendsRead, onSettled }: {
  update: ProjectUpdate; sendsRead: Read<Send[]>; onSettled?: () => void;
}) {
  useStore();
  const dests = useDestinations();
  const conns = useConnections();
  const uid = update.id;
  const picked = store.picked.get(uid) ?? null;
  const [preview, setPreview] = useState<{ id: string; digest: string; preview: WirePreview } | { id: string; failed: true } | null>(null);
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

  const sends = mergeKnown(uid, sendsRead.data ?? []);
  const reload = sendsRead.reload;
  // Every send that went through a prepare, in the order prepared: the open
  // ones and the ones that ended (their result stays here).
  const prepared = sends.filter((s) => !!s.prepare_operation_id);
  const waiting = prepared.filter((s) => s.state === "prepared");
  const openPrepared = store.preparedOpen.has(uid) ? store.preparedOpen.get(uid) : waiting[0]?.id ?? null;
  const destinations = dests.data;

  return (
    <div data-send="well" data-testid="send-well">
      <SurfaceSection label={SEND_WORDS.section}>
        {sendsRead.failed ? (
          <Unreadable what="SENDS" testid="sends-unreadable" onRetry={reload} />
        ) : prepared.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepared-list">
              {prepared.map((s) => (
                <PreparedRow key={s.id} uid={uid} revision={update.draftRevision} s={s} reload={reload} conns={conns}
                  onSettled={onSettled}
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
          <div className="send-line" data-testid="send-none">
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
                const o = store.outcomes.get(k) ?? { kind: "none" as const };
                const held = store.holds.get(k);
                const last = latestFor(sends, d.id);
                const eg = egressOf(d);
                const acc = accountChip(d, conns);
                const busy = store.busy.has(k);
                const lost = o.kind === "lost";
                const pv = preview && preview.id === d.id ? preview : null;
                const running = last?.state === "dispatching";
                const far = farSide(d.channel, d.target, d.account);
                const verbs = (
                  <div className="send-verbs" data-testid="send-verbs">
                    <Button dense variant="primary" loading={busy || running}
                      disabled={!pv || "failed" in pv || running}
                      data-testid={lost ? "send-retry" : "send-verb"}
                      onClick={() => void press(uid, d.id, () => ({
                        update_id: uid, destination_id: d.id,
                        preview_digest: (pv as { digest: string }).digest,
                      }), reload, onSettled)}>
                      {lost ? SEND_WORDS.retry : last ? SEND_WORDS.sendAgain : SEND_WORDS.send}
                    </Button>
                    <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    {last?.state === "unknown" && far ? (
                      <Button dense variant="ghost" data-testid="send-check" onClick={() => openFar(far)}>
                        {`${SEND_WORDS.check} ${targetToken(d.channel, d.target)}`}
                      </Button>
                    ) : null}
                    {/* ONE source: the latest send by dispatch_started_at. The press
                        cache keeps only what no record holds: a lost answer (with its
                        Retry), and a refusal newer than the latest send. */}
                    {lost ? <OutcomeLine o={o} />
                      : o.kind === "refused" && (!last?.dispatch_started_at || o.at > Date.parse(last.dispatch_started_at))
                        ? <OutcomeLine o={o} />
                        : <LatestReceipt s={last} />}
                  </div>
                );
                return (
                  <SurfaceLedgerRow
                    key={d.id}
                    data-testid="destination-row"
                    wrap
                    open={open}
                    lineLabel={`${d.name}, ${CHANNEL_WORD[d.channel] ?? d.channel}`}
                    onToggle={() => {
                      if (busy || held) return;           // a held press keeps its pick
                      store.picked.set(uid, open ? null : d.id); bump();
                    }}
                    lead={<span className="send-pick" aria-hidden="true">{open ? "●" : "○"}</span>}
                    primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                    cells={<>
                      <span className="surface-token" data-chip>{CHANNEL_WORD[d.channel] ?? d.channel}</span>
                      <span className="surface-token send-literal send-wrap send-target" data-chip title={targetToken(d.channel, d.target)}>{targetToken(d.channel, d.target)}</span>
                      {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                      <LastChip s={last} />
                      <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    </>}
                  >
                    {open ? (
                      <div className="send-open" data-testid="send-open" data-destination={d.name}>
                        {pv && !("failed" in pv)
                          ? <PreviewWell preview={previewOf(d.channel, d.target, d.account, pv.preview)} testid="send-preview" verbs={verbs} />
                          : null}
                        {pv && "failed" in pv ? (
                          <div className="send-verbs" data-testid="preview-failed">
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

function byWord(s: Send): string {
  const kind = s.prepared_by?.kind ?? "";
  if (kind === "owner") return "BY YOU";
  if (kind === "steward" || kind === "scheduler") return "BY STEWARD";
  return `BY ${String(s.prepared_by?.identity || kind).toUpperCase()}`;
}

/** A prepared send. While it waits: Send and Discard (one row open at a
 *  time; the first one opens). When it ended: a closed result row that stays. */
function PreparedRow({ uid, revision, s, reload, conns, dest, open, onToggle, onSettled }: {
  uid: string; revision: number; s: Send; reload: () => void; conns: ConnectionsResponse | null;
  dest: Destination | undefined; open: boolean; onToggle: () => void; onSettled?: () => void;
}) {
  const k = `${uid}|${s.id}`;
  const o = store.outcomes.get(k) ?? { kind: "none" as const };
  const busy = store.busy.has(k);
  const eg = egressOf({ channel: s.channel, account: s.account, synced: dest?.synced });
  const acc = accountChip({ channel: s.channel, connection: dest?.connection,
    account: { ...s.account, ...(typeof dest?.account.key_present === "boolean" ? { key_present: dest.account.key_present } : {}) } }, conns);
  // A named destination refusal is final for this row: Send would only
  // refuse again, so only Discard stays.
  const dead = o.kind === "refused" && (o.code === "destination_changed" || o.code === "destination_parked");
  const [discardBusy, setDiscardBusy] = useState(false);
  const [discardOutcome, setDiscardOutcome] = useState<string | null>(null);
  const waiting = s.state === "prepared";
  const running = s.state === "dispatching";
  const name = s.destination_name ?? dest?.name ?? "—";
  const frozen = previewOf(s.channel, s.target, s.account, s.preview, s.file_path);

  const result = waiting ? null
    : running ? <span data-testid="prepared-running"><StateChip state="active" icon="◆" label={SEND_WORDS.sending} /></span>
    : s.state === "sent" ? <><StateChip state="success" label={sentWord(s.channel)} /><ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} /></>
    : s.state === "failed" ? <><StateChip state="failure" label="FAILED" /><span className="surface-token" data-chip>{failedWord(s.reason ?? "")}</span><span className="surface-token" data-chip>{SEND_WORDS.nothingSent}</span></>
    : s.state === "unknown" ? <><StateChip state="warning" label={SEND_WORDS.unknownChip} /><span className="surface-token" data-chip>{(s.reason ? unknownWord(s.reason) : "NO ANSWER")}</span></>
    : <StateChip state="idle" label={SEND_WORDS.discarded} />;

  return (
    <SurfaceLedgerRow
      data-testid={waiting ? "prepared-row" : running ? "prepared-sending" : "prepared-result"}
      wrap
      open={open}
      expands={waiting}
      lineLabel={`${name}, ${waiting ? SEND_WORDS.prepared : s.state}`}
      onToggle={waiting ? onToggle : undefined}
      lead={waiting ? <StateChip state="active" icon="◆" label="" /> : <span className="send-pick" aria-hidden="true">·</span>}
      primary={<span className="surface-primary" data-destination={name} data-state={s.state}>{name}</span>}
      cells={<>
        {waiting
          ? <StateChip state="active" icon="◆" label={SEND_WORDS.prepared} />
          : <span className="send-line" data-testid="prepared-result-word" data-state={s.state} data-code={s.reason ?? ""}>{result}</span>}
        <span className="surface-token" data-chip data-testid="prepared-by">{byWord(s)}</span>
        <span className="surface-token" data-chip>{`REV ${revision}`}</span>
        {waiting && o.kind === "refused" ? (
          <span data-testid="prepared-refused-chip" data-code={o.code}><StateChip state="failure" label={refusedWord(o.code)} /></span>
        ) : null}
        <span className="surface-token" data-chip>{stamp(s.settled_at ?? s.created_at)}</span>
        {waiting && acc ? <StateChip state={acc.state} label={acc.label} /> : null}
        {waiting ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
      </>}
    >
      {waiting && open ? (
        <div className="send-open" data-testid="prepared-open">
          <PreviewWell preview={frozen} testid="prepared-preview" verbs={
            <div className="send-verbs" data-testid="prepared-verbs">
              {!dead ? (
                <Button dense variant="primary" loading={busy} data-testid={o.kind === "lost" ? "prepared-retry" : "prepared-send"}
                  onClick={() => void press(uid, s.id, () => ({ send_id: s.id }), reload, onSettled)}>
                  {o.kind === "lost" ? SEND_WORDS.retry : SEND_WORDS.send}
                </Button>
              ) : null}
              {!dead ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
              <ConfirmVerb label={SEND_WORDS.discard} confirmLabel={SEND_WORDS.discardArmed} busy={discardBusy}
                data-testid="prepared-discard"
                onConfirm={() => {
                  setDiscardBusy(true);
                  void wire.discard(s.id)
                    .then((ended) => { store.known.set(ended.id, ended); store.outcomes.delete(k); store.preparedOpen.delete(uid); bump(); })
                    .catch((e) => setDiscardOutcome(e instanceof Refusal ? e.code : "no_answer"))
                    .finally(() => { setDiscardBusy(false); reload(); });
                }} />
              <OutcomeLine o={o} />
              {discardOutcome ? (
                <span className="send-line" data-testid="discard-refused" data-code={discardOutcome}>
                  <StateChip state="failure" label="REFUSED" />
                  <span className="surface-token" data-chip>{refusedWord(discardOutcome)}</span>
                </span>
              ) : null}
            </div>
          } />
        </div>
      ) : null}
    </SurfaceLedgerRow>
  );
}

/* ── the one DELIVERY history (story 01's table) ─────────────────────── */

export function DeliveryHistory({ ctrl, update, sends }: { ctrl: UpdateController; update: ProjectUpdate; sends: Send[] }) {
  const rows: Delivery[] = update.deliveries;
  const ok = rows.filter(isDelivered).length;
  const sendOf = (sendId: string | null | undefined) => (sendId ? sends.find((s) => s.id === sendId) : undefined);
  return (
    <div data-send="history" data-testid="delivery-section">
      <SurfaceSection label={ok > 0 ? `${SEND_WORDS.history} ${ok}` : SEND_WORDS.history}>
        <div className="update-deliver-line send-manual" data-testid="deliver-line">
          <span className="update-deliver-to">
            <StringGadget label="To" value={ctrl.deliverTo} onChange={ctrl.setDeliverTo} placeholder="To"
              disabled={ctrl.deliverBusy || ctrl.deliverLocked}
              onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); void ctrl.markDelivered(); } }}
              inputProps={{ "data-testid": "deliver-to" } as never} />
          </span>
          <Button dense variant="ghost" loading={ctrl.deliverBusy} onClick={() => void ctrl.markDelivered()}
            data-testid={ctrl.deliverOutcome.kind === "uncertain" ? "deliver-retry" : "deliver-verb"}>
            {ctrl.deliverOutcome.kind === "uncertain" ? SEND_WORDS.retry : "Mark delivered"}
          </Button>
        </div>
        {ctrl.deliverOutcome.kind === "refused" ? (
          <span className="send-line" data-testid="deliver-refused" data-code={ctrl.deliverOutcome.code}>
            <StateChip state="failure" label="REFUSED" />
            <span className="surface-token" data-chip>{refusedWord(ctrl.deliverOutcome.code)}</span>
          </span>
        ) : ctrl.deliverOutcome.kind === "uncertain" ? (
          <span className="send-line" data-testid="deliver-uncertain"><StateChip state="warning" label={SEND_WORDS.lost} /></span>
        ) : null}
        {ctrl.deliveriesReadFailed ? (
          <Unreadable what="HISTORY" testid="history-unreadable" onRetry={() => void ctrl.reloadDeliveries()} />
        ) : null}
        {rows.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="delivery-history">
              {rows.map((r) => {
                const send = sendOf(r.sendId);
                if (!isDelivered(r)) {
                  // Story 01's UNKNOWN row; Check opens the far side.
                  const far = send ? farSide(send.channel, send.target, send.account) : null;
                  const reason = send?.reason ?? null;
                  return (
                    <SurfaceLedgerRow key={r.id} data-testid="delivery-row" wrap expands={false}
                      lead={<span data-outcome={r.outcome}><StateChip state="warning" label="" /></span>}
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
                    lead={<span data-outcome={r.outcome}><StateChip state="success" label="" /></span>}
                    primary={<span className="surface-primary" data-to={r.deliveredTo ?? ""}>{r.deliveredTo ?? "—"}</span>}
                    cells={<>
                      <span className="surface-token" data-chip data-tone="ok" data-testid="history-word">
                        {manual ? SENT_WORD.manual : sentWord(r.channel)}
                      </span>
                      {manual
                        ? <span className="surface-token" data-chip>MANUAL</span>
                        : <ProofCell channel={r.channel} proof={r.proof ?? null} target={send?.target} account={send?.account} />}
                      <span className="surface-token" data-chip>{stamp(r.deliveredAt)}</span>
                    </>} />
                );
              })}
            </ul>
          </SurfaceLedger>
        ) : null}
      </SurfaceSection>
    </div>
  );
}

/** The update list's chips, over story 01's table: PREPARED ×K (still
 *  waiting), RESULT UNKNOWN ×M, DELIVERY ×N (isDelivered rows). No chip at
 *  zero. */
export function ListChips({ update }: { update: ProjectUpdate }) {
  const { data } = useSends(update.id);
  const ok = update.deliveries.filter(isDelivered).length;
  const unknown = update.deliveries.length - ok;
  const prep = mergeKnown(update.id, data ?? []).filter((s) => s.state === "prepared").length;
  return (
    <>
      {prep > 0 ? <span data-testid="update-prepared-chip"><StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${prep}`} /></span> : null}
      {unknown > 0 ? <span data-testid="update-unknown-chip"><StateChip state="warning" label={`${SEND_WORDS.unknownChip} ×${unknown}`} /></span> : null}
      {ok > 0 ? <span data-testid="update-delivered-chip"><StateChip state="success" label={`${SEND_WORDS.history} ×${ok}`} /></span> : null}
    </>
  );
}

/** The two wells of a published update, over ONE read of its sends. */
export function PublishedWells({ ctrl, update }: { ctrl: UpdateController; update: ProjectUpdate }) {
  const { reloadDeliveries } = ctrl;
  const settled = useCallback(() => { void reloadDeliveries(); }, [reloadDeliveries]);
  // Opening a published update reads its history again (story 01's table):
  // a send that settled while he was away shows; no answer is named.
  useEffect(() => { settled(); }, [update.id, settled]);
  const sendsRead = useSends(update.id, settled);
  return (
    <>
      <SendWell update={update} sendsRead={sendsRead} onSettled={settled} />
      <div data-section="delivery"><DeliveryHistory ctrl={ctrl} update={update} sends={mergeKnown(update.id, sendsRead.data ?? [])} /></div>
    </>
  );
}

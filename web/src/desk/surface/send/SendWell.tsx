/* PHILO-11-04: the SEND well as ONE library species. Built to the owner's
 * ratified canvas E (phase-11 story 03, "Yes...", 2026-09-29): the Phase 10
 * well (ratified "Ratify as drawn", 2026-09-29) with its eight update
 * bindings (faces.md section 2, B1-B8) replaced by ONE document reference
 * {ref: "<kind>:<id>", title, label}. Documented in desk/surface/contract.md
 * ("SendWell"). Library species only: SurfaceSection, SurfaceLedger,
 * SurfaceLedgerRow, SurfaceWell, StateChip, EgressChip, Material, Button,
 * ConfirmVerb.
 *
 * THE PRESS RULE: one press = one {document, destination or prepared row,
 * command_id, preview digest}, held PER DOCUMENT AND TARGET in a module store
 * that survives Back and opening another document. Two seats of one document
 * (the Chair's brief and Intelligence -> BRIEF) share that store, so they
 * show one pick and one press. A lost answer keeps all four; Retry sends the
 * same key, and the hub's replay answers the settled row, never a second
 * dispatch. A channel UNKNOWN is a settled record: "Send again" is a NEW send
 * with a NEW key; the product never sends again by itself.
 *
 * A1: the pick opens the preview and Send in place, under the row.
 * A3: prepared sends first, ONE preview open (the first), each other a click
 * away; a prepared send that ended stays in place as its result.
 * A destination's header and its open receipt come from ONE source: its
 * latest send by `dispatch_started_at`.
 * G2 (canvas T1): a preview refused by name shows REFUSED + its word (+ the
 * size and the limit when the answer carries them), never NO ANSWER.
 * T2: a PREVIEW CHANGED refusal reads a fresh preview of the same document.
 * A read that gets no answer names it and offers Retry.
 *
 * The history: a new kind's is its ENDED SENDS, headed SENDS N (no manual
 * row, R8). The update fills the `history` slot with its own DELIVERY N and
 * Mark delivered (features/channels/SendWell.tsx).
 */
import { useCallback, useEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { ConfirmVerb, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceWell } from "../Surface";
import { EgressChip } from "../gadgets";
import { Material } from "../Material";
import { StateChip } from "../patterns";
import { useDesk } from "../../store";
import { fetchConnections, type ConnectionsResponse, type ConnectionState } from "../../../pages/cores/connections/api";
import { chipLabel } from "../../../pages/cores/connections/ConnectionsPane";
import {
  CHANNEL_WORD, DEST_CHANGED, SEND_WORDS, commandId, egressOf, failedWord, farSide, previewOf,
  refusalSize, refusedWord, requestDestinationsFocus, sentWord, stamp, targetToken, unknownWord, wire, Refusal,
  type Channel, type Destination, type Preview, type Send, type WirePreview,
} from "../../../features/channels/channels";
import "../../../features/channels/channels.css";
import "./send-well.css";

/** The one document a well sends: `ref` is `<kind>:<id>` (the wire's
 *  `document_ref`), `title` its name, `label` the short token a prepared row
 *  shows (REV 4, BRIEF SEP 29, D-1a2b3c). */
export type DocRef = { ref: string; title: string; label: string };

/* ── the per-document store (survives Back and another document) ──────── */

type Outcome =
  | { kind: "none" }
  | { kind: "refused"; code: string; at: number }
  | { kind: "lost" }
  | { kind: "settled"; send: Send };
type Held = { key: string; body: { send_id?: string; document_ref?: string; destination_id?: string; preview_digest?: string } };
const store = {
  picked: new Map<string, string | null>(),          // ref -> destination id
  preparedOpen: new Map<string, string | null>(),    // ref -> the one open prepared row (absent = the first)
  holds: new Map<string, Held>(),                     // `${ref}|${target}` -> the held press
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

/** One document's sends. The read is KEYED by the document: a response for
 *  another document (a late read after the well changed document) is
 *  dropped, and the rows it returns belong to the document it was asked for
 *  or to nothing (Astra r1 F1 on #708). While any row is `dispatching` the
 *  well reads again; when the last one settles, `onSettled` runs once. */
export function useSends(ref: string, onSettled?: () => void): Read<Send[]> {
  const [state, setState] = useState<{ ref: string; data: Send[] | null; failed: boolean }>({ ref, data: null, failed: false });
  const current = useRef(ref);
  current.current = ref;
  const reload = useCallback(() => {
    const asked = ref;
    void wire.sends(asked)
      .then((r) => {
        if (current.current !== asked) return;       // an obsolete answer
        setState({ ref: asked, data: r.filter((s) => s.document_ref === asked), failed: false });
      })
      .catch(() => {
        if (current.current !== asked) return;
        setState((st) => ({ ref: asked, data: st.ref === asked ? st.data : null, failed: true }));
      });
  }, [ref]);
  const tick = useStore();
  useEffect(() => { reload(); }, [reload, tick]);
  const data = state.ref === ref ? state.data : null;
  const failed = state.ref === ref && state.failed;
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

export function useDestinations(): Read<Destination[]> {
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
 *  Connections chip words). Null for a folder. Email and Slack: the key only
 *  present or absent (never the key). */
export function accountChip(
  d: Pick<Destination, "channel" | "account"> & { connection?: Destination["connection"] },
  c: ConnectionsResponse | null,
): { state: "success" | "warning" | "idle" | "failure"; label: string; code: string } | null {
  if (d.channel === "file") return null;
  if (d.channel === "email" || d.channel === "slack") {
    // Present or absent only, and only when known (the list read does not open the keychain).
    if (typeof d.account.key_present !== "boolean") return null;
    if (d.channel === "slack") {
      return d.account.key_present
        ? { state: "success", label: "WEBHOOK SET", code: "webhook_present" }
        : { state: "warning", label: "NO WEBHOOK", code: "slack_webhook_missing" };
    }
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
export function PreviewWell({ preview, testid, verbs }: { preview: Preview; testid: string; verbs: ReactNode }) {
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
  if (s.state === "sent") return <span data-testid="send-last-sent"><StateChip state="success" label={`${sentWord(s.channel, s.proof, s.account)} ${stamp(s.settled_at).slice(-5)}`} /></span>;
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
      <StateChip state="success" label={sentWord(s.channel, s.proof, s.account)} />
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

export function openFar(url: string | null) { if (url) window.open(url, "_blank", "noopener"); }

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
export function ProofCell({ channel, proof, target, account }: {
  channel: string; proof: Record<string, unknown> | null; target?: Record<string, string | number>;
  account?: Record<string, string | boolean>;
}) {
  const p = proof ?? {};
  if (channel === "file") return <span className="surface-token send-literal send-wrap" data-chip data-testid="proof">{String(p.path ?? "")}</span>;
  if (channel === "email") return <span className="surface-token send-literal" data-chip data-testid="proof">{`ID ${String(p.message_id ?? "")}`}</span>;
  // Slack by webhook answers only `ok`: the proof is the channel, never a link (design section 5).
  if (channel === "slack") return <span className="surface-token send-literal" data-chip data-testid="proof">{String(target?.channel_label ?? "")}</span>;
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

async function press(ref: string, target: string, fresh: () => Held["body"], reload: () => void, onSettled?: () => void) {
  const k = `${ref}|${target}`;
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
    else store.outcomes.set(k, { kind: "lost" });  // keep the document, the key and the body for Retry
  } finally {
    store.busy.delete(k); bump(); reload(); onSettled?.();
  }
}

/** The destination's latest send: the latest to LEAVE, by
 *  `dispatch_started_at` (then the hub's dispatch sequence), never the latest
 *  prepared. A running send is the latest while it runs. */
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
 *  that failed or predates the press never hides a known result. Every row
 *  in the answer belongs to `ref`. */
export function mergeKnown(ref: string, read: Send[], known: Iterable<Send> = store.known.values()): Send[] {
  // Only this document's rows: a read row of another document never enters.
  const out = new Map(read.filter((s) => s.document_ref === ref).map((s) => [s.id, s]));
  for (const k of known) {
    if (k.document_ref !== ref) continue;
    const r = out.get(k.id);
    if (!r || (ENDED.has(k.state) && !ENDED.has(r.state))) out.set(k.id, k);
  }
  return [...out.values()];
}

/* ── the SEND well ─────────────────────────────────────────────────── */

type PreviewState =
  | { ref: string; id: string; digest: string; preview: WirePreview }
  | { ref: string; id: string; failed: true; code?: string; size?: { size: number; limit: number } | null };

/** A preview that did not come: a named refusal (REFUSED + its word, the
 *  size and the limit when the answer carries them, NOTHING SENT, the
 *  egress) or no answer at all (NO PREVIEW · NO ANSWER + Retry). */
function PreviewFailed({ pv, eg, onRetry }: {
  pv: Extract<PreviewState, { failed: true }>; eg: ReturnType<typeof egressOf>; onRetry: () => void;
}) {
  if (pv.code) {
    return (
      <div className="send-verbs" data-testid="preview-refused" data-code={pv.code}>
        <StateChip state="failure" label="REFUSED" />
        <span className="surface-token" data-chip>{refusedWord(pv.code)}</span>
        {pv.size ? (
          <span className="surface-token" data-chip data-testid="preview-size">
            {`${pv.size.size.toLocaleString("en-US")} / ${pv.size.limit.toLocaleString("en-US")} CHARACTERS`}
          </span>
        ) : null}
        <span className="surface-token" data-chip>{SEND_WORDS.nothingSent}</span>
        <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
      </div>
    );
  }
  return (
    <div className="send-verbs" data-testid="preview-failed">
      <StateChip state="failure" label={SEND_WORDS.noPreview} />
      <span className="surface-token" data-chip>NO ANSWER</span>
      <Button dense variant="ghost" data-testid="preview-retry" onClick={onRetry}>{SEND_WORDS.retry}</Button>
    </div>
  );
}

/** The SEND well of one document: its prepared sends, then its destinations.
 *  `head` sits first inside SEND (the meeting's form picker). */
export function SendWell({ doc, sendsRead, onSettled, head }: {
  doc: DocRef; sendsRead: Read<Send[]>; onSettled?: () => void; head?: ReactNode;
}) {
  useStore();
  const dests = useDestinations();
  const conns = useConnections();
  const ref = doc.ref;
  const picked = store.picked.get(ref) ?? null;
  const [preview, setPreview] = useState<PreviewState | null>(null);
  const [previewTry, setPreviewTry] = useState(0);
  useEffect(() => {
    if (!picked) { setPreview(null); return; }
    let live = true;
    setPreview(null);
    void wire.preview(ref, picked)
      .then((p) => { if (live) setPreview({ ref, id: picked, digest: p.payload_digest, preview: p.preview }); })
      .catch((e) => {
        if (!live) return;
        setPreview(e instanceof Refusal
          ? { ref, id: picked, failed: true, code: e.code, size: refusalSize(e) }
          : { ref, id: picked, failed: true });
      });
    return () => { live = false; };
  }, [ref, picked, previewTry]);
  // T2: a PREVIEW CHANGED refusal reads the preview again (same document, same destination).
  const pickedOutcome = picked ? store.outcomes.get(`${ref}|${picked}`) : undefined;
  const changedAt = pickedOutcome?.kind === "refused"
    && (pickedOutcome.code === "preview_changed" || pickedOutcome.code === "payload_changed") ? pickedOutcome.at : 0;
  useEffect(() => { if (changedAt) setPreviewTry((n) => n + 1); }, [changedAt]);

  const sends = mergeKnown(ref, sendsRead.data ?? []);
  const reload = sendsRead.reload;
  // Every send that went through a prepare, in the order prepared: the open
  // ones and the ones that ended (their result stays here).
  const prepared = sends.filter((s) => !!s.prepare_operation_id);
  const waiting = prepared.filter((s) => s.state === "prepared");
  const openPrepared = store.preparedOpen.has(ref) ? store.preparedOpen.get(ref) : waiting[0]?.id ?? null;
  const destinations = dests.data;

  return (
    <div data-send="well" data-testid="send-well" data-doc={ref} aria-label={`${SEND_WORDS.send} ${doc.title}`} role="group">
      <SurfaceSection label={SEND_WORDS.section}>
        {head}
        {sendsRead.failed ? (
          <Unreadable what="SENDS" testid="sends-unreadable" onRetry={reload} />
        ) : prepared.length > 0 ? (
          <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows" data-testid="prepared-list">
              {prepared.map((s) => (
                <PreparedRow key={s.id} docRef={ref} label={doc.label} s={s} reload={reload} conns={conns}
                  onSettled={onSettled}
                  open={s.state === "prepared" && openPrepared === s.id}
                  onToggle={() => { store.preparedOpen.set(ref, openPrepared === s.id ? null : s.id); bump(); }}
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
                const k = `${ref}|${d.id}`;
                const open = picked === d.id;
                const o = store.outcomes.get(k) ?? { kind: "none" as const };
                const held = store.holds.get(k);
                const last = latestFor(sends, d.id);
                const eg = egressOf(d);
                const acc = accountChip(d, conns);
                const busy = store.busy.has(k);
                const lost = o.kind === "lost";
                const pv = preview && preview.ref === ref && preview.id === d.id ? preview : null;
                const running = last?.state === "dispatching";
                const far = farSide(d.channel, d.target, d.account);
                const verbs = (
                  <div className="send-verbs" data-testid="send-verbs">
                    <Button dense variant="primary" loading={busy || running}
                      disabled={!pv || "failed" in pv || running}
                      data-testid={lost ? "send-retry" : "send-verb"}
                      onClick={() => void press(ref, d.id, () => ({
                        document_ref: ref, destination_id: d.id,
                        preview_digest: (pv as { digest: string }).digest,
                      }), reload, onSettled)}>
                      {lost ? SEND_WORDS.retry : last ? SEND_WORDS.sendAgain : SEND_WORDS.send}
                    </Button>
                    <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    {last?.state === "unknown" && far ? (
                      <Button dense variant="ghost" data-testid="send-check" data-href={far} onClick={() => openFar(far)}>
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
                      store.picked.set(ref, open ? null : d.id); bump();
                    }}
                    lead={<span className="send-pick" aria-hidden="true">{open ? "●" : "○"}</span>}
                    primary={<span className="surface-primary" data-destination={d.name}>{d.name}</span>}
                    cells={<span className="send-cells">
                      <span className="surface-token" data-chip>{CHANNEL_WORD[d.channel] ?? d.channel}</span>
                      <span className="surface-token send-literal send-wrap send-target" data-chip title={targetToken(d.channel, d.target)}>{targetToken(d.channel, d.target)}</span>
                      {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                      <LastChip s={last} />
                      <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                    </span>}
                  >
                    {open ? (
                      <div className="send-open" data-testid="send-open" data-destination={d.name}>
                        {pv && !("failed" in pv)
                          ? <PreviewWell preview={previewOf(d.channel, d.target, d.account, pv.preview)} testid="send-preview" verbs={verbs} />
                          : null}
                        {pv && "failed" in pv ? <PreviewFailed pv={pv} eg={eg} onRetry={() => setPreviewTry((n) => n + 1)} /> : null}
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
function PreparedRow({ docRef, label, s, reload, conns, dest, open, onToggle, onSettled }: {
  docRef: string; label: string; s: Send; reload: () => void; conns: ConnectionsResponse | null;
  dest: Destination | undefined; open: boolean; onToggle: () => void; onSettled?: () => void;
}) {
  const k = `${docRef}|${s.id}`;
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
    : s.state === "sent" ? <><StateChip state="success" label={sentWord(s.channel, s.proof, s.account)} /><ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} /></>
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
      cells={<span className="send-cells">
        {waiting
          ? <StateChip state="active" icon="◆" label={SEND_WORDS.prepared} />
          : <span className="send-line" data-testid="prepared-result-word" data-state={s.state} data-code={s.reason ?? ""}>{result}</span>}
        <span className="surface-token" data-chip data-testid="prepared-by">{byWord(s)}</span>
        <span className="surface-token" data-chip data-testid="prepared-label">{label}</span>
        {waiting && o.kind === "refused" ? (
          <span data-testid="prepared-refused-chip" data-code={o.code}><StateChip state="failure" label={refusedWord(o.code)} /></span>
        ) : null}
        <span className="surface-token" data-chip>{stamp(s.settled_at ?? s.created_at)}</span>
        {waiting && acc ? <StateChip state={acc.state} label={acc.label} /> : null}
        {waiting ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
      </span>}
    >
      {waiting && open ? (
        <div className="send-open" data-testid="prepared-open">
          <PreviewWell preview={frozen} testid="prepared-preview" verbs={
            <div className="send-verbs" data-testid="prepared-verbs">
              {!dead ? (
                <Button dense variant="primary" loading={busy} data-testid={o.kind === "lost" ? "prepared-retry" : "prepared-send"}
                  onClick={() => void press(docRef, s.id, () => ({ send_id: s.id }), reload, onSettled)}>
                  {o.kind === "lost" ? SEND_WORDS.retry : SEND_WORDS.send}
                </Button>
              ) : null}
              {!dead ? <EgressChip label={eg.label} scope={eg.scope} title={eg.title} /> : null}
              <ConfirmVerb label={SEND_WORDS.discard} confirmLabel={SEND_WORDS.discardArmed} busy={discardBusy}
                data-testid="prepared-discard"
                onConfirm={() => {
                  setDiscardBusy(true);
                  void wire.discard(s.id)
                    .then((ended) => { store.known.set(ended.id, ended); store.outcomes.delete(k); store.preparedOpen.delete(docRef); bump(); })
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

/* ── the history of a new kind: its ENDED SENDS (R8: no manual row) ────── */

/** The head word (faces.md F8, settled by the brains' check): SENDS N, N the
 *  sent rows; no counter at zero. The update keeps its DELIVERY N. */
export const HISTORY_HEAD = "SENDS";

export function SendHistory({ sends }: { sends: Send[] }) {
  const rows = sends
    .filter((s) => s.state === "sent" || s.state === "unknown")
    .sort((a, b) => String(b.settled_at ?? "").localeCompare(String(a.settled_at ?? "")));
  if (!rows.length) return null;
  const ok = rows.filter((r) => r.state === "sent").length;
  return (
    <div data-send="history" data-species="send" data-testid="send-history">
      <SurfaceSection label={ok > 0 ? `${HISTORY_HEAD} ${ok}` : HISTORY_HEAD}>
        <SurfaceLedger count="" cols="room">
          <ul className="surface-ledger-rows" data-testid="history-list">
            {rows.map((r) => {
              const name = r.destination_name ?? "—";
              if (r.state === "unknown") {
                const far = farSide(r.channel, r.target, r.account);
                return (
                  <SurfaceLedgerRow key={r.id} data-testid="history-row" wrap expands={false}
                    lead={<span data-outcome="unknown"><StateChip state="warning" label="" /></span>}
                    primary={<span className="surface-primary" data-to={name}>{`${SEND_WORDS.unknownChip} · CHECK ${name}`}</span>}
                    cells={<span className="send-cells">
                      {r.reason ? <span className="surface-token" data-chip>{unknownWord(r.reason)}</span> : null}
                      {far ? <Button dense variant="ghost" data-testid="history-check" data-href={far} onClick={() => openFar(far)}>{SEND_WORDS.check}</Button> : null}
                      <span className="surface-token" data-chip>{stamp(r.settled_at)}</span>
                    </span>} />
                );
              }
              return (
                <SurfaceLedgerRow key={r.id} data-testid="history-row" wrap expands={false}
                  lead={<span data-outcome="sent"><StateChip state="success" label="" /></span>}
                  primary={<span className="surface-primary" data-to={name}>{name}</span>}
                  cells={<span className="send-cells">
                    <span className="surface-token" data-chip data-tone="ok" data-testid="history-word">{sentWord(r.channel, r.proof, r.account)}</span>
                    <ProofCell channel={r.channel} proof={r.proof} target={r.target} account={r.account} />
                    <span className="surface-token" data-chip>{stamp(r.settled_at)}</span>
                  </span>} />
              );
            })}
          </ul>
        </SurfaceLedger>
      </SurfaceSection>
    </div>
  );
}

/** The PREPARED ×K chip for a document's host head (the Chair BRIEF head,
 *  a Room decision row). No chip at zero. `data-head-chip` lets a section
 *  head wrap its chips under its label at narrow width (surface.css). */
export function PreparedChip({ docRef }: { docRef: string }) {
  const { data } = useSends(docRef);
  const k = mergeKnown(docRef, data ?? []).filter((s) => s.state === "prepared").length;
  return k > 0 ? <span data-head-chip data-testid="doc-prepared-chip"><StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${k}`} /></span> : null;
}

/** The species as a host composes it: the well, then its history, over ONE
 *  read of the document's sends. `head` sits first inside SEND. `history`
 *  is the slot only the update fills (its DELIVERY N and Mark delivered,
 *  R8); every other document gets SENDS N. */
export function SendWells({ doc, head, onSettled, history }: {
  doc: DocRef; head?: ReactNode; onSettled?: () => void;
  history?: (sends: Send[]) => ReactNode;
}) {
  const sendsRead = useSends(doc.ref, onSettled);
  const sends = mergeKnown(doc.ref, sendsRead.data ?? []);
  return (
    <>
      <SendWell doc={doc} sendsRead={sendsRead} onSettled={onSettled} head={head} />
      {history ? history(sends) : <SendHistory sends={sends} />}
    </>
  );
}

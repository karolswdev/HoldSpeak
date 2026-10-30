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
 * command_id, preview digest}, held PER DOCUMENT AND TARGET with tab custody
 * that survives Back, opening another document and a reload. Two seats of one document
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
import { createPortal } from "react-dom";
import { createContext, lazy, Suspense, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { ConfirmVerb, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, SurfaceWell } from "../Surface";
import { SurfaceFooter } from "../SurfaceFooter";
import { EgressChip } from "../gadgets";
import { Material } from "../Material";
import { StateChip } from "../patterns";
import { DotWord, ToolGlyph, Toolbar } from "../kit";
import { fetchConnections, type ConnectionsResponse, type ConnectionState } from "../../../pages/cores/connections/api";
import { chipLabel } from "../../../pages/cores/connections/ConnectionsPane";
import {
  CHANNEL_WORD, DEST_CHANGED, SEND_WORDS, syncEgress, commandId, egressOf, failedWord, farSide, noAnswerWords, previewOf,
  refusalSize, refusedWord, sentWord, stamp, targetName, targetToken, unknownWord, wire, Refusal,
  type Channel, type Destination, type Preview, type Send, type WirePreview,
  type EmailProvider,
} from "../../../features/channels/channels";
import "../../../features/channels/channels.css";
import "./send-well.css"; import { keepPlace, keptPlace } from "../../deskMemory"; // PHILO-13-07 (B2)
import { clearPendingCommand, keepPendingCommand, pendingCommands, resetPendingCommands, type HeldCommand } from "./pendingCommand";
import { apiFetch } from "../../../lib/api";
import { openRef } from "../../openObject";
import { SEND_OPEN } from "../../windowSend";
import { Token } from "../Token";

// Settings owns the admitted destination form. It is loaded only when the
// sheet asks for Add destination, which keeps the shared Send species free of
// a second form implementation and avoids a static Settings import cycle.
/** W4-PHONE: the channel as a plain word on a destination row (`Folder`,
 *  `GitHub`); the menus keep CHANNEL_WORD. */
const CHANNEL_NAME: Record<string, string> = {
  file: "Folder", github: "GitHub", jira: "Jira", confluence: "Confluence", email: "Email", slack: "Slack",
};
const AdmittedDestinationForm = lazy(() => import("../../../pages/cores/connections/Destinations").then((m) => ({ default: m.DestForm })));

/** The one document a well sends: `ref` is `<kind>:<id>` (the wire's
 *  `document_ref`), `title` its name, `label` the short token a prepared row
 *  shows (REV 4, BRIEF SEP 29, D-1a2b3c). */
/** `version`: what changes when the document's text does under the same ref
 *  (PHILO-15-09: a regenerated Brief keeps its id); the preview reads again. */
export type DocRef = { ref: string; title: string; label: string; version?: string };

/* ── the per-document store (survives Back and another document) ──────── */

type Outcome =
  | { kind: "none" }
  | { kind: "refused"; code: string; at: number }
  | { kind: "lost"; storageFailed?: boolean }
  | { kind: "settled"; send: Send };
type Held = HeldCommand;
export type RetryCommand = NonNullable<Send["retry_command"]>;
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
function restorePendingCommands() {
  try {
    for (const { ref, target, command } of pendingCommands()) {
      const k = `${ref}|${target}`;
      store.holds.set(k, command);
      store.outcomes.set(k, { kind: "lost" });
      if (command.body.send_id) store.preparedOpen.set(ref, target);
      else store.picked.set(ref, target);
    }
  } catch { /* A later press must establish custody and will name this failure. */ }
}
restorePendingCommands();
const bump = () => { store.tick++; store.subs.forEach((f) => f()); };
const useStore = () =>
  useSyncExternalStore((f) => { store.subs.add(f); return () => { store.subs.delete(f); }; }, () => store.tick);

/** PHILO-13-15 (C5): the push seam (Phase 12 design section 6). ONE setter
 *  per well: `Send to ▸` sets the destination of the document `ref`; an open
 *  well reacts in place (no remount), a well that mounts later opens on it.
 *  A held press keeps its pick (the row's own toggle rule). */
export function pickDestination(ref: string, destinationId: string | null) {
  const was = store.picked.get(ref) ?? null;
  if (was && [...store.busy, ...store.holds.keys()].includes(`${ref}|${was}`)) return;
  store.picked.set(ref, destinationId); bump();
}
/** The destination picked for `ref`, or null. */
export const pickedDestination = (ref: string): string | null => store.picked.get(ref) ?? null;

/** Test seam: ordinary isolation clears custody; reload simulation restores it. */
export function resetSendStore(restorePending = false) {
  store.picked.clear(); store.preparedOpen.clear(); store.holds.clear(); store.outcomes.clear(); store.busy.clear();
  store.known.clear();
  if (restorePending) restorePendingCommands();
  else resetPendingCommands();
  bump();
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

/** The account states that say "this account did not sign in". */
const SIGN_IN_FAILED = new Set<string>(["owner_action_required", "unavailable", "degraded"]);

/** The account warning a destination row shows (the Phase 9 B1 words, the
 *  Connections chip words), or null. Betterment send S1: a chip shows ONLY
 *  when the newest word on that account (a check or a send: the hub's
 *  `connection`, where a good send counts as a good check) says it failed to
 *  sign in. Never CONNECTED, NEVER CHECKED or KEY SET beside a good send.
 *  Null for a folder. Email and Slack: only a key known to be absent. */
export function accountChip(
  d: Pick<Destination, "channel" | "account"> & { connection?: Destination["connection"] },
  c: ConnectionsResponse | null,
): { state: "success" | "warning" | "idle" | "failure"; label: string; code: string } | null {
  if (d.channel === "file") return null;
  if (d.channel === "email" || d.channel === "slack") {
    // Present or absent only, and only when known (the list read does not open the keychain).
    if (d.account.key_present !== false) return null;
    return d.channel === "slack"
      ? { state: "warning", label: "NO WEBHOOK", code: "slack_webhook_missing" }
      : { state: "warning", label: "NO KEY", code: "email_key_missing" };
  }
  const tool = c?.tools.find((t) => t.provider_id === d.channel);
  let state: ConnectionState = "not_configured";
  // Betterment ST2: the Accounts row's own words (its reason) name the chip.
  let words: { reason?: string; other_account?: boolean } | undefined = tool;
  if (d.channel === "github") {
    state = (d.connection?.state ?? tool?.state ?? "not_configured") as ConnectionState;
    const login = tool?.account?.login;
    if (state === "connected" && login && d.account.login && login !== d.account.login) {
      return { state: "failure", label: "Account changed", code: "github_identity_changed" };
    }
  } else {
    const conn = tool?.connections?.find((x) => x.account.site === d.account.site && x.account.email === d.account.email);
    state = (d.connection?.state ?? conn?.state ?? "not_configured") as ConnectionState;
    words = conn;
  }
  if (!SIGN_IN_FAILED.has(state)) return null;
  const map: Record<string, "warning" | "failure"> = {
    owner_action_required: "warning", unavailable: "failure", degraded: "warning",
  };
  return { state: map[state] ?? "warning", label: chipLabel(state, d.channel, words ?? {}), code: state };
}

/* ── pieces ────────────────────────────────────────────────────────── */

/** The frozen fields and payload. The host owns scrolling; the payload well
 *  never traps the Send action. `Edit` is the one shared transition into the
 *  ordinary Note editor. */
export function PreviewWell({ preview, testid, verbs, onEdit, editBusy }: {
  preview: Preview; testid: string; verbs?: ReactNode; onEdit?: () => void; editBusy?: boolean;
}) {
  // W4-PHONE (2026-10-27): the preview is the document — one quiet line of
  // frozen fields (sans 12, sentence case) with Edit at its end, then the
  // words on the paper. No PREVIEW caption, no card in a card.
  return (
    <div className="send-preview" data-send="well" data-testid={testid}>
      <div className="send-preview-head">
        <dl className="send-fields">
          {preview.fields.map((f) => (
            <div key={f.label} className="send-field" data-testid="send-preview-field">
              <dt>{f.label}</dt>
              <dd>{f.value}</dd>
            </div>
          ))}
        </dl>
        {onEdit ? (
          <Button dense variant="ghost" data-testid="send-edit" loading={editBusy} disabled={editBusy} onClick={onEdit}>Edit</Button>
        ) : null}
      </div>
      <SurfaceWell>
        <div className="send-preview-body" data-testid="send-preview-body">
          {preview.body_kind === "markdown" ? <Material>{preview.body}</Material> : <div className="send-preview-text">{preview.body}</div>}
        </div>
      </SurfaceWell>
      {verbs ?? null}
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
        <Token className="surface-token" data-chip>{refusedWord(o.code)}</Token>
        <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
      </span>
    );
  }
  if (o.kind === "lost") {
    return (
      <span className="send-line" data-testid="send-lost">
        <StateChip state="warning" label={SEND_WORDS.lost} />
        {o.storageFailed ? <Token className="surface-token" data-chip>{SEND_WORDS.storageUnavailable}</Token> : null}
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

/** A CLOSED destination row's receipt, at the seat the canvas draws the
 *  last send (line 2, beside the egress chip): when the click that left the
 *  row leaves a failure, a refusal or no answer, the words stay on screen
 *  (Astra built-check r2 F1). SENT and SENDING keep their one chip. */
function ClosedReceipt({ o, last }: { o: Outcome; last: Send | undefined }) {
  if (o.kind === "lost") {
    return <span className="send-line" data-testid="send-last-lost"><StateChip state="warning" label={SEND_WORDS.lost} /></span>;
  }
  if (o.kind === "refused" && (!last?.dispatch_started_at || o.at > Date.parse(last.dispatch_started_at))) {
    return (
      <span className="send-line" data-testid="send-last-refused" data-code={o.code}>
        <StateChip state="failure" label="REFUSED" />
        <Token className="surface-token" data-chip>{refusedWord(o.code)}</Token>
        <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
      </span>
    );
  }
  if (last?.state === "failed") {
    return (
      <span className="send-line" data-testid="send-last-failed" data-code={last.reason ?? ""}>
        <StateChip state="failure" label={SEND_WORDS.lastFailed} />
        <Token className="surface-token" data-chip>{failedWord(last.reason ?? "")}</Token>
        <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
      </span>
    );
  }
  if (last?.state === "unknown") {
    return (
      <span className="send-line" data-testid="send-last-unknown">
        <StateChip state="warning" label={SEND_WORDS.lastUnknown} />
        <Token className="surface-token" data-chip>{last.reason ? unknownWord(last.reason) : "No answer"}</Token>
      </span>
    );
  }
  return <LastChip s={last} />;
}

/** The destination's latest send: the one receipt the open row shows. */
/** The egress a send's receipt names (judged at its boundary, kept on its row
 *  and in its proof): the sync service that took the file off this device. Every
 *  receipt branch (latest, prepared result, history) shows it. */
export function ReceiptEgress({ s }: { s: Pick<Send, "proof"> & { egress?: string | null } }) {
  const sync = syncEgress(s.egress ?? s.proof?.egress);
  return sync ? <EgressChip label={sync.label} scope={sync.scope} title={sync.title} /> : null;
}

function LatestReceipt({ s }: { s: Send | undefined }) {
  if (!s) return null;
  if (s.state === "sent") return (
    <span className="send-line" data-testid="send-sent" data-receipt="latest" data-state="sent">
      <StateChip state="success" label={sentWord(s.channel, s.proof, s.account)} />
      <ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} />
      <ReceiptEgress s={s} />
    </span>
  );
  if (s.state === "failed") return (
    <span className="send-line" data-testid="send-failed" data-receipt="latest" data-state="failed" data-code={s.reason ?? ""}>
      <StateChip state="failure" label="FAILED" />
      <Token className="surface-token" data-chip>{failedWord(s.reason ?? "")}</Token>
      <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
    </span>
  );
  if (s.state === "unknown") return (
    <span className="send-line" data-testid="send-unknown" data-receipt="latest" data-state="unknown">
      <StateChip state="warning" label={SEND_WORDS.unknownChip} />
      <Token className="surface-token" data-chip>{(s.reason ? unknownWord(s.reason) : "No answer")}</Token>
      <ReceiptEgress s={s} />
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

/** A SAVED file's path as the receipt shows it: under the destination's
 * folder, the folder's short token leads (the hub's `display`, made by
 * holdspeak/home_paths.py from the known HOME), so no receipt prints the
 * full home path. Any other path stays whole. The proof itself stays exact. */
export function shownPath(path: string, target?: Record<string, string | number>): string {
  const folder = String(target?.folder ?? "");
  const display = String(target?.display ?? "");
  if (folder && display && (path === folder || path.startsWith(`${folder}/`)))
    return display + path.slice(folder.length);
  // No guess from a pattern: /Users/alice is not this HOME (Astra, #869).
  // Only the hub knows HOME; with no short token the path stays whole.
  return path;
}

/** The proof of a SENT row, exact as the channel gave it (no uppercasing). */
export function ProofCell({ channel, proof, target, account }: {
  channel: string; proof: Record<string, unknown> | null; target?: Record<string, string | number>;
  account?: Record<string, string | boolean>;
}) {
  const p = proof ?? {};
  if (channel === "file") return <Token code className="surface-token send-literal send-wrap" data-chip data-testid="proof">{shownPath(String(p.path ?? ""), target)}</Token>;
  if (channel === "email") return <Token code className="surface-token send-literal" data-chip data-testid="proof">{`ID ${String(p.message_id ?? "")}`}</Token>;
  // Slack by webhook answers only `ok`: the proof is the channel, never a link (design section 5).
  if (channel === "slack") return <Token code className="surface-token send-literal" data-chip data-testid="proof">{String(target?.channel_label ?? "")}</Token>;
  const url = proofLink(channel, p, target, account);
  const label = target ? targetToken(channel as Channel, target) : url.replace(/^https:\/\//, "");
  return url ? (
    <Button dense variant="ghost" className="desk-chip quiet send-literal" data-testid="proof" data-href={url} title={url}
      onClick={() => openFar(url)}>
      {label}
    </Button>
  ) : <Token code className="surface-token send-literal" data-chip data-testid="proof">{label}</Token>;
}

/* ── the press ─────────────────────────────────────────────────────── */

async function press(ref: string, target: string, fresh: () => Held["body"], reload: () => void, onSettled?: () => void,
  preview?: Preview, commandKey?: string) {
  const k = `${ref}|${target}`;
  if (store.busy.has(k)) return;                 // a double-click is one press
  let held = store.holds.get(k);
  const uncertain = Boolean(held);
  if (!held) held = { key: commandKey ?? commandId(), body: fresh(), preview };
  try { keepPendingCommand(ref, target, held); }
  catch {
    store.outcomes.set(k, uncertain ? { kind: "lost", storageFailed: true }
      : { kind: "refused", code: "send_storage_unavailable", at: Date.now() });
    bump();
    return;
  }
  store.holds.set(k, held);
  const heldKey = held.key;
  const forget = () => {
    // If storage closes after dispatch, its retained record is safe to replay.
    try { clearPendingCommand(ref, target, heldKey); } catch { /* keep the safe replay */ }
    store.holds.delete(k);
  };
  store.busy.add(k); store.outcomes.set(k, { kind: "none" }); bump();
  try {
    const pending = wire.send({ ...held.body, command_id: held.key });
    // Read again once the send has crossed its boundary, so a running send
    // shows as SENDING while it runs.
    const peek = setTimeout(reload, 250);
    const send = await pending.finally(() => clearTimeout(peek));
    forget();
    store.known.set(send.id, send);
    store.outcomes.set(k, { kind: "settled", send });
  } catch (e) {
    if (e instanceof Refusal && e.code !== "operation_in_progress") { forget(); store.outcomes.set(k, { kind: "refused", code: e.code, at: Date.now() }); }
    else store.outcomes.set(k, { kind: "lost" });  // keep the document, the key and the body for Retry
  } finally {
    store.busy.delete(k); bump(); reload(); onSettled?.();
  }
}

/** The narrow shared adapter for a prepared row outside the full Send well.
 * Needs you uses the same held command custody, including a replay after an
 * unknown answer, and therefore never invents a second press implementation. */
export function sendPrepared(ref: string, sendId: string, reload: () => void = () => {}, onSettled?: () => void,
  retry?: RetryCommand): Promise<void> {
  const body = retry && !retry.send_id && retry.document_ref && retry.destination_id && retry.preview_digest
    ? () => ({ document_ref: retry.document_ref!, destination_id: retry.destination_id!, preview_digest: retry.preview_digest! })
    : () => ({ send_id: retry?.send_id ?? sendId });
  return press(ref, sendId, body, reload, onSettled, undefined, retry?.command_id);
}

/** A failed send is a new owner press against the same frozen document and
 * destination. Its command is new by design; only an unknown retry replays. */
export function retryInline(
  ref: string, destinationId: string, previewDigest: string,
  reload: () => void = () => {}, onSettled?: () => void,
): Promise<void> {
  return press(ref, destinationId, () => ({
    document_ref: ref, destination_id: destinationId, preview_digest: previewDigest,
  }), reload, onSettled);
}

/** Discard is shared so Needs you keeps the Send well's receipt custody. */
export async function discardPrepared(sendId: string): Promise<Send> {
  const ended = await wire.discard(sendId);
  store.known.set(ended.id, ended);
  bump();
  return ended;
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
        <Token className="surface-token" data-chip>{refusedWord(pv.code)}</Token>
        {pv.size ? (
          <Token className="surface-token" data-chip data-testid="preview-size">
            {`${pv.size.size.toLocaleString("en-US")} / ${pv.size.limit.toLocaleString("en-US")} CHARACTERS`}
          </Token>
        ) : null}
        <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
        <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
      </div>
    );
  }
  return (
    <div className="send-verbs" data-testid="preview-failed">
      <StateChip state="failure" label={SEND_WORDS.noPreview} />
      <Token className="surface-token" data-chip>No answer</Token>
      <Button dense variant="ghost" data-testid="preview-retry" onClick={onRetry}>{SEND_WORDS.retry}</Button>
    </div>
  );
}

/** The SEND well of one document: its prepared sends, then its destinations.
 *  `head` sits first inside SEND (the meeting's form picker). */
/** PHILO-17 (the desk sweep): a host that holds its body until its first
 *  reads end (the meeting record) hears when this well's own first reads
 *  (its destinations and its sends) have ended, read or failed. No host,
 *  no report. */
export const SendWellReadContext = createContext<((resolved: boolean) => void) | null>(null);

const EMPTY_DESTINATION_DRAFT = {
  channel: "file" as Channel, name: "", nameTouched: false,
  folder: "", synced: false, repo: "", kind: "issue" as const, number: "",
  jiraAccount: "", key: "", confAccount: "", space: "",
  provider: "resend" as EmailProvider, fromEmail: "", fromName: "", emailRef: "", to: "", cc: "",
  slackLabel: "", slackRef: "",
};

/** Settings' admitted form, seated inside the Send sheet. The destination
 * controller stays in Destinations.tsx; this component only supplies the
 * same account/key callbacks and returns the saved row to the sheet. */
function InlineDestinationForm({ onDone, onCancel }: { onDone: (saved?: Destination) => void; onCancel: () => void }) {
  const [conns, setConns] = useState<ConnectionsResponse | null>(null);
  const [accountsReadError, setAccountsReadError] = useState(false);
  const [accountsLoading, setAccountsLoading] = useState(true);
  const [keys, setKeys] = useState<Record<string, boolean>>({});
  const reloadAccounts = useCallback(() => {
    setAccountsLoading(true);
    void fetchConnections()
      .then((answer) => { setConns(answer); setAccountsReadError(false); })
      .catch(() => setAccountsReadError(true))
      .finally(() => setAccountsLoading(false));
  }, []);
  useEffect(() => {
    reloadAccounts();
    window.addEventListener("focus", reloadAccounts);
    return () => window.removeEventListener("focus", reloadAccounts);
  }, [reloadAccounts]);
  const onKey = useCallback((ref: string, value: string, provider: EmailProvider) =>
    wire.saveKey(ref, value, provider).then(() => { setKeys((current) => ({ ...current, [`email:${provider}:${ref}`]: true })); return null; })
      .catch((error) => error instanceof Refusal ? error.code : "no_answer"), []);
  const onSlackKey = useCallback((url: string) =>
    wire.saveSlackWebhook(url).then((answer) => { setKeys((current) => ({ ...current, [answer.key_ref]: true })); return { keyRef: answer.key_ref }; })
      .catch((error) => ({ code: error instanceof Refusal ? error.code : "no_answer" })), []);
  const onKeyKnown = useCallback((ref: string, present: boolean) => setKeys((current) => ({ ...current, [ref]: present })), []);
  return (
    <Suspense fallback={<div data-testid="dest-form-loading"><SurfaceState loading /></div>}>
      <AdmittedDestinationForm
        conns={conns}
        accountsLoading={accountsLoading}
        accountsReadError={accountsReadError}
        onAccountsRetry={reloadAccounts}
        initial={EMPTY_DESTINATION_DRAFT}
        keys={keys}
        onKey={onKey}
        onSlackKey={onSlackKey}
        onKeyKnown={onKeyKnown}
        onDone={onDone}
        onCancel={onCancel}
      />
    </Suspense>
  );
}

/** Open the new Note and deliver the existing window Send signal after its
 * pullout has mounted. The bounded retry is only for the asynchronous
 * arrival path; the note editor remains the owner of the Send state. */
function openNoteSend(noteRef: string) {
  openRef(noteRef);
  if (typeof window === "undefined") return;
  const winId = `pullout:${noteRef}`;
  let tries = 0;
  const request = () => {
    const root = document.getElementById(winId);
    if (root?.querySelector("[data-testid=thought-send]")) return;
    window.dispatchEvent(new CustomEvent(SEND_OPEN, { detail: { winId } }));
    tries += 1;
    if (tries < 30) window.setTimeout(request, 50);
  };
  request();
}

export function SendWell({ doc, sendsRead, onSettled, head, destinationIds, onBack }: {
  doc: DocRef; sendsRead: Read<Send[]>; onSettled?: () => void; head?: ReactNode; onBack?: () => void;
  /** Optional source-owned allow-list (for example a Room action's exact saved target). */
  destinationIds?: string[];
}) {
  useStore();
  const dests = useDestinations();
  const reportRead = useContext(SendWellReadContext);
  const conns = useConnections();
  const ref = doc.ref;
  const sends = mergeKnown(ref, sendsRead.data ?? []);
  const rememberedPick = keptPlace(`send/pick/${ref}`);
  // B2: the kept pick returns, onto a listed destination only. With no kept pick
  // and no destination but the built-in HoldSpeak folder (a fresh desk), the folder is picked.
  const destinations = dests.data === null
    ? null
    : dests.data.filter((d) => !destinationIds || destinationIds.includes(d.id));
  const orderedDestinations: Destination[] | null = destinations === null ? null : destinations.slice().sort((a, b) => {
    if (rememberedPick && a.id === rememberedPick) return -1;
    if (rememberedPick && b.id === rememberedPick) return 1;
    const at = latestFor(sends, a.id)?.dispatch_started_at ?? "";
    const bt = latestFor(sends, b.id)?.dispatch_started_at ?? "";
    return bt.localeCompare(at);
  });
  const onlyBuiltin = orderedDestinations?.length === 1 && orderedDestinations[0].builtin ? orderedDestinations[0].id : null;
  const savedPick = store.picked.get(ref);
  const picked = savedPick !== undefined && (savedPick === null || !destinationIds || destinationIds.includes(savedPick))
    ? savedPick
    : ((k) => (k && orderedDestinations?.some((d) => d.id === k) ? k : onlyBuiltin))(rememberedPick);
  const [preview, setPreview] = useState<PreviewState | null>(null);
  const [previewTry, setPreviewTry] = useState(0);
  const [addingDestination, setAddingDestination] = useState(false);
  const [editingPreview, setEditingPreview] = useState<string | null>(null);
  const [editFailure, setEditFailure] = useState<string | null>(null);
  const [verbSlot, setVerbSlot] = useState<HTMLSpanElement | null>(null);
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
  }, [ref, picked, previewTry, doc.version]);
  // T2: a PREVIEW CHANGED refusal reads the preview again (same document, same destination).
  const pickedOutcome = picked ? store.outcomes.get(`${ref}|${picked}`) : undefined;
  const changedAt = pickedOutcome?.kind === "refused"
    && (pickedOutcome.code === "preview_changed" || pickedOutcome.code === "payload_changed") ? pickedOutcome.at : 0;
  useEffect(() => { if (changedAt) setPreviewTry((n) => n + 1); }, [changedAt]);
  // The well's first reads: its destinations, its sends, and the preview of
  // the destination it picked on its own (Astra r1 on #1108: the preview drew
  // above the meeting's Decide and Transcript after the body was shown).
  const heldPreview = picked ? store.holds.get(`${ref}|${picked}`)?.preview : undefined;
  const previewRead = !picked || Boolean(heldPreview) || (preview !== null && preview.ref === ref && preview.id === picked);
  const wellRead = (dests.data !== null || dests.failed) && (sendsRead.data !== null || sendsRead.failed) && previewRead;
  useLayoutEffect(() => { reportRead?.(wellRead); }, [reportRead, wellRead]);

  useEffect(() => {
    // Prepared rows already name their exact command target. A terminal read
    // resolves that row even if its browser answer was lost; it must not leave
    // a hidden pending Retry holding the fold open forever.
    let changed = false;
    for (const [k, command] of store.holds) {
      const ended = sendsRead.data?.find((s) => s.document_ref === ref
        && s.id === command.body.send_id && ENDED.has(s.state));
      if (!ended) continue;
      try { clearPendingCommand(ref, ended.id, command.key); } catch { /* a later reload replays safely */ }
      store.holds.delete(k);
      store.outcomes.set(k, { kind: "settled", send: ended });
      changed = true;
    }
    if (changed) bump();
  }, [ref, sendsRead.data]);
  const reload = sendsRead.reload;
  // Every send that went through a prepare, in the order prepared: the open
  // ones and the ones that ended (their result stays here).
  const prepared = sends.filter((s) => !!s.prepare_operation_id);
  const waiting = prepared.filter((s) => s.state === "prepared");
  const openPrepared = store.preparedOpen.has(ref) ? store.preparedOpen.get(ref) : waiting[0]?.id ?? null;
  const pendingReads = (destinations === null && !dests.failed) || (sendsRead.data === null && !sendsRead.failed);
  const edit = useCallback(async (destination: Destination, rendered: Preview) => {
    if (editingPreview) return;
    setEditingPreview(destination.id);
    setEditFailure(null);
    try {
      const made = await apiFetch<{ note?: { id?: string; note_id?: string } }>("/api/notes", {
        method: "POST",
        json: {
          title: `${doc.title || "Note"} (to send)`,
          body_markdown: rendered.source_markdown ?? rendered.body,
          tags: ["send"],
        },
      });
      const noteId = String(made.note?.id ?? made.note?.note_id ?? "");
      if (!noteId) throw new Error("note_not_created");
      const noteRef = `note:${noteId}`;
      pickDestination(noteRef, destination.id);
      keepPlace(`send/pick/${noteRef}`, destination.id);
      openNoteSend(noteRef);
    } catch (error) {
      setEditFailure(error instanceof Refusal ? error.code : "note_not_created");
    } finally {
      setEditingPreview(null);
    }
  }, [doc.title, editingPreview]);

  return (
    <div data-send="well" data-testid="send-well" data-doc={ref}
      aria-busy={wellRead ? undefined : "true"}
      aria-label={`${SEND_WORDS.send} ${doc.title}`} role="group">
      {/* W4-PHONE (2026-10-27): the sheet's toolbar — Send (the picked
          destination's verb, portaled into the slot below) and Cancel
          (the host's Back); Add destination at the end. */}
      <Toolbar label={SEND_WORDS.send} className="send-sheet-header" data-testid="send-sheet-header"
        trailingStays
        trailing={
          <Button dense variant="ghost" className="send-add-destination" data-testid="send-add-destination"
            aria-expanded={addingDestination}
            onClick={() => setAddingDestination((open) => !open)}>
            <ToolGlyph kind="new" />{SEND_WORDS.addDestination}
          </Button>
        }>
        <span className="send-toolbar-slot" ref={setVerbSlot} />
        {onBack ? <Button dense variant="secondary" data-testid="send-back" onClick={onBack}>Cancel</Button> : null}
      </Toolbar>
      <SurfaceSection className="send-destination-section">
        {head}
        {pendingReads ? <div data-testid="send-read-loading"><SurfaceState loading /></div> : null}
        <div className="send-sheet-sections">
        {sendsRead.failed ? (
          <Unreadable what="SENDS" testid="sends-unreadable" onRetry={reload} />
        ) : prepared.length > 0 ? (
          <SurfaceSection className="send-ready-section" label="Ready to send" data-testid="send-ready-section">
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
          </SurfaceSection>
        ) : null}
        {dests.failed ? (
          <Unreadable what="DESTINATIONS" testid="destinations-unreadable" onRetry={dests.reload} />
        ) : (
          <SurfaceSection className="send-to-section" data-testid="send-to-section">
            {addingDestination ? (
              <div className="send-inline-destination" data-testid="send-inline-destination">
                <InlineDestinationForm
                  onDone={(saved) => {
                    setAddingDestination(false);
                    if (saved) {
                      pickDestination(ref, saved.id);
                      keepPlace(`send/pick/${ref}`, saved.id);
                    }
                    dests.reload();
                  }}
                  onCancel={() => setAddingDestination(false)}
                />
              </div>
            ) : null}
            {orderedDestinations === null ? null : orderedDestinations.length === 0 ? (
              <div className="send-line" data-testid="send-none">
                <Token className="surface-token" data-chip>{SEND_WORDS.noDestination}</Token>
              </div>
            ) : (
            <SurfaceLedger count="" cols="room">
            <ul className="surface-ledger-rows send-destination-list" data-testid="destination-list">
              {orderedDestinations.map((d) => {
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
                // Retry replays the held command's bytes, even after Back
                // and a newer save. Show that command's original preview.
                const activePreview = held?.preview ?? (pv && !("failed" in pv)
                  ? previewOf(d.channel, d.target, d.account, pv.preview) : null);
                const running = last?.state === "dispatching";
                // A new command needs an authoritative history read. An exact
                // held replay remains safe even when that read gets no answer.
                const waitingForHistory = !held && (sendsRead.data === null || sendsRead.failed);
                const waitingForSend = running && !held;
                const far = farSide(d.channel, d.target, d.account);
                // Betterment send S1: the hub reads a send still running past its
                // channel's limit as no answer. The face says what to do (Check,
                // Try again) and never stays SENDING; a press still waiting in
                // this tab lets go, and Try again replays its held command.
                const noAnswer = last?.state === "unknown" && last.reason === "no_answer_in_time";
                // W4-PHONE: Send (and Check) are the sheet's toolbar verbs; the
                // receipt is the sheet's status line; the egress is the row's.
                const verbs = (
                  <div className="send-verbs" data-testid="send-verbs">
                    <Button dense variant="primary" loading={(busy && !noAnswer) || waitingForSend}
                      disabled={!activePreview || waitingForSend || waitingForHistory}
                      data-testid={lost && !noAnswer ? "send-retry" : "send-verb"}
                      onClick={() => {
                        if (noAnswer) store.busy.delete(k);
                        void press(ref, d.id, () => ({
                          document_ref: ref, destination_id: d.id,
                          preview_digest: (pv as { digest: string }).digest,
                        }), reload, onSettled, activePreview ?? undefined);
                      }}>
                      <ToolGlyph kind="send" />
                      {lost && !noAnswer ? SEND_WORDS.retry
                        : last?.state === "failed" || last?.state === "unknown" ? SEND_WORDS.tryAgain
                          : last ? SEND_WORDS.sendAgain : SEND_WORDS.send}
                    </Button>
                    {last?.state === "unknown" && far ? (
                      <Button dense variant="ghost" data-testid="send-check" data-href={far} onClick={() => openFar(far)}>
                        {`${SEND_WORDS.check} ${targetToken(d.channel, d.target)}`}
                      </Button>
                    ) : null}
                  </div>
                );
                const receipt = (
                  <div className="send-receipt-line" data-testid="send-receipt-line">
                    {noAnswer ? (
                      <span className="send-line send-no-answer" data-testid="send-no-answer" data-receipt="latest" data-state="unknown">
                        {noAnswerWords(d.channel, d.account, d.target)}
                      </span>
                    ) : null}
                    {/* ONE source: the latest send by dispatch_started_at. The press
                        cache keeps only what no record holds: a lost answer (with its
                        Retry), and a refusal newer than the latest send. */}
                    {noAnswer ? null
                      : lost ? <OutcomeLine o={o} />
                      : o.kind === "refused" && (!last?.dispatch_started_at || o.at > Date.parse(last.dispatch_started_at))
                        ? <OutcomeLine o={o} />
                        : <LatestReceipt s={last} />}
                  </div>
                );
                return (
                  <li key={d.id} className="send-destination-item" data-testid="destination-row" data-open={open || undefined}>
                    <Button dense variant="ghost" disabled={busy || Boolean(held)}
                      aria-pressed={open}
                      className="send-destination-chip"
                      onClick={() => {
                        if (busy || held) return;           // a held press keeps its pick
                        store.picked.set(ref, open ? null : d.id); keepPlace(`send/pick/${ref}`, open ? "" : d.id); bump();
                      }}>
                      <span className="send-pick" aria-hidden="true">{open ? "●" : "○"}</span>
                      <span className="surface-primary" data-destination={d.name} title={targetToken(d.channel, d.target)}>{d.name}</span>
                      <span className="send-cells">
                        <Token className="surface-token send-channel" data-chip>{CHANNEL_NAME[d.channel] ?? CHANNEL_WORD[d.channel] ?? d.channel}</Token>
                        {!open ? <Token code className="surface-token send-literal send-wrap send-target" data-chip title={targetToken(d.channel, d.target)}>{targetName(d.channel, d.target)}</Token> : null}
                        {acc ? <StateChip state={acc.state} label={acc.label} /> : null}
                        {open ? <LastChip s={last} /> : <ClosedReceipt o={o} last={last} />}
                        <EgressChip label={eg.label} scope={eg.scope} title={eg.title} />
                      </span>
                    </Button>
                    {open ? (
                      <div className="send-open" data-testid="send-open" data-destination={d.name}>
                        {!activePreview && !pv && !pendingReads ? <div data-testid="send-preview-loading"><SurfaceState loading /></div> : null}
                        {activePreview
                          ? <>
                              <PreviewWell preview={activePreview} testid="send-preview"
                                onEdit={() => void edit(d, activePreview)} editBusy={editingPreview === d.id} />
                              {verbSlot ? createPortal(verbs, verbSlot) : null}
                              <SurfaceFooter dataSend="actions" className="send-sheet-footer" fold={false}
                                verbs={
                                  <>
                                    {editFailure ? <span className="send-line" data-testid="send-edit-failed" title={editFailure}><DotWord tone="fail">Could not make a note to edit · The preview stays here · Press Edit again</DotWord></span> : null}
                                    {receipt}
                                  </>
                                } />
                            </>
                          : null}
                        {!activePreview && pv && "failed" in pv ? <PreviewFailed pv={pv} eg={eg} onRetry={() => setPreviewTry((n) => n + 1)} /> : null}
                      </div>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </SurfaceLedger>
            )}
          </SurfaceSection>
        )}
        </div>
      </SurfaceSection>
    </div>
  );
}

function byWord(s: Send): string {
  const kind = s.prepared_by?.kind ?? "";
  // WORDS-VOCAB: said in sentence case here; the name stays as typed.
  if (kind === "owner") return "By you";
  if (kind === "steward" || kind === "scheduler") return "By steward";
  return `By ${String(s.prepared_by?.identity || kind)}`;
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
  const eg = egressOf({ channel: s.channel, account: s.account, synced: dest?.synced, target: s.target });
  const acc = accountChip({ channel: s.channel, connection: dest?.connection,
    account: { ...s.account, ...(typeof dest?.account.key_present === "boolean" ? { key_present: dest.account.key_present } : {}) } }, conns);
  // A named destination refusal is final for this row: Send would only
  // refuse again, so only Discard stays.
  // PREVIEW CHANGED on a prepared row is final too (its frozen words are not
  // the document's words now): only Discard stays; a new pick reads a new preview.
  const dead = o.kind === "refused" && (o.code === "destination_changed" || o.code === "destination_parked"
    || o.code === "preview_changed");
  const [discardBusy, setDiscardBusy] = useState(false);
  const [discardOutcome, setDiscardOutcome] = useState<string | null>(null);
  const waiting = s.state === "prepared";
  const running = s.state === "dispatching";
  const name = s.destination_name ?? dest?.name ?? "—";
  const frozen = previewOf(s.channel, s.target, s.account, s.preview, s.file_path);

  const result = waiting ? null
    : running ? <span data-testid="prepared-running"><StateChip state="active" icon="◆" label={SEND_WORDS.sending} /></span>
    : s.state === "sent" ? <><StateChip state="success" label={sentWord(s.channel, s.proof, s.account)} /><ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} /><ReceiptEgress s={s} /></>
    : s.state === "failed" ? <><StateChip state="failure" label="FAILED" /><Token className="surface-token" data-chip>{failedWord(s.reason ?? "")}</Token><Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token></>
    : s.state === "unknown" ? <><StateChip state="warning" label={SEND_WORDS.unknownChip} /><Token className="surface-token" data-chip>{(s.reason ? unknownWord(s.reason) : "No answer")}</Token><ReceiptEgress s={s} /></>
    : <StateChip state="idle" label={SEND_WORDS.discarded} />;

  return (
    <SurfaceLedgerRow
      data-testid={waiting ? "prepared-row" : running ? "prepared-sending" : "prepared-result"}
      wrap
      open={open}
      expands={waiting}
      lineLabel={`${name}, ${waiting ? SEND_WORDS.prepared : s.state}`}
      onToggle={waiting ? onToggle : undefined}
      lead={waiting ? <StateChip state="active" icon="◆" label="" wordless /> : <span className="send-pick" aria-hidden="true">·</span>}
      primary={<span className="surface-primary" data-destination={name} data-state={s.state}>{name}</span>}
      cells={<span className="send-cells">
        {waiting
          ? <StateChip state="active" icon="◆" label={SEND_WORDS.prepared} />
          : <span className="send-line" data-testid="prepared-result-word" data-state={s.state} data-code={s.reason ?? ""}>{result}</span>}
        <Token className="surface-token" data-chip data-testid="prepared-by">{byWord(s)}</Token>
        <Token className="surface-token" data-chip data-testid="prepared-label">{label}</Token>
        {waiting && o.kind === "refused" ? (
          <span data-testid="prepared-refused-chip" data-code={o.code}><StateChip state="failure" label={refusedWord(o.code)} /></span>
        ) : null}
        <Token className="surface-token" data-chip>{stamp(s.settled_at ?? s.created_at)}</Token>
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
                  <Token className="surface-token" data-chip>{refusedWord(discardOutcome)}</Token>
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

/** The shared sheet's one receipt list: SENT, with no counter at zero. */
export const HISTORY_HEAD = "SENT";

/** `tag` (PHILO-13-15, Astra C5 check condition 2): a host whose document has
 *  forms (the meeting) names each row's form, so a result of another form
 *  stays readable after he switches form. */
export function SendHistory({ sends, tag }: { sends: Send[]; tag?: (s: Send) => { form: string; word: string } | null }) {
  const rows = sends
    .filter((s) => s.state === "sent" || s.state === "unknown")
    .sort((a, b) => String(b.settled_at ?? "").localeCompare(String(a.settled_at ?? "")));
  if (!rows.length) return null;
  const ok = rows.filter((r) => r.state === "sent").length;
  return (
    <div data-send="history" data-species="send" data-testid="send-history">
      <SurfaceSection data-testid="sent-section" label={ok > 0 ? `${HISTORY_HEAD} ${ok}` : HISTORY_HEAD}>
        <SurfaceLedger count="" cols="room">
          <ul className="surface-ledger-rows" data-testid="history-list">
            {rows.map((r) => {
              const name = r.destination_name ?? "—";
              const t = tag?.(r) ?? null;
              const formChip = t ? <Token className="surface-token" data-chip data-form={t.form} data-testid="history-form">{t.word}</Token> : null;
              if (r.state === "unknown") {
                const far = farSide(r.channel, r.target, r.account);
                return (
                  <SurfaceLedgerRow key={r.id} data-testid="history-row" wrap expands={false}
                    lead={<span data-outcome="unknown"><StateChip state="warning" label="" wordless /></span>}
                    primary={<span className="surface-primary" data-to={name}>{`${SEND_WORDS.unknownChip} · Check ${name}`}</span>}
                    cells={<span className="send-cells">
                      {formChip}
                      {r.reason ? <Token className="surface-token" data-chip>{unknownWord(r.reason)}</Token> : null}
                      <ReceiptEgress s={r} />
                      {far ? <Button dense variant="ghost" data-testid="history-check" data-href={far} onClick={() => openFar(far)}>{SEND_WORDS.check}</Button> : null}
                      <Token className="surface-token" data-chip>{stamp(r.settled_at)}</Token>
                    </span>} />
                );
              }
              return (
                <SurfaceLedgerRow key={r.id} data-testid="history-row" wrap expands={false}
                  lead={<span data-outcome="sent"><StateChip state="success" label="" wordless /></span>}
                  primary={<span className="surface-primary" data-to={name}>{name}</span>}
                  cells={<span className="send-cells">
                    {formChip}
                    <Token className="surface-token" data-chip data-tone="ok" data-testid="history-word">{sentWord(r.channel, r.proof, r.account)}</Token>
                    <ProofCell channel={r.channel} proof={r.proof} target={r.target} account={r.account} />
                    <ReceiptEgress s={r} />
                    <Token className="surface-token" data-chip>{stamp(r.settled_at)}</Token>
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
type SendWellsProps = {
  doc: DocRef; head?: ReactNode; onSettled?: () => void;
  history?: (sends: Send[]) => ReactNode;
  destinationIds?: string[];
  /** The host's narrow Back state. The shared sheet owns the control and
   * returns focus to the host's opening Send… control through this callback. */
  onBack?: () => void;
};

export function SendSheet({ doc, head, onSettled, history, destinationIds, onBack, sendsRead }: SendWellsProps & { sendsRead: Read<Send[]> }) {
  const sends = mergeKnown(doc.ref, sendsRead.data ?? []);
  return (
    <div data-send="sheet" data-testid="send-sheet" data-doc={doc.ref} className="send-sheet">
      <SendWell doc={doc} sendsRead={sendsRead} onSettled={onSettled} head={head} destinationIds={destinationIds} onBack={onBack} />
      {history ? history(sends) : <SendHistory sends={sends} />}
    </div>
  );
}

export function SendWells(props: SendWellsProps) {
  const sendsRead = useSends(props.doc.ref, props.onSettled);
  return <SendSheet {...props} sendsRead={sendsRead} />;
}

/** A compact document host. Sends stay readable while destinations and the
 * ordinary preview mount only after Send. A held press keeps its exact Retry
 * in view, including when another seat of this document made the press. */
export function SendWellsFold(props: SendWellsProps) {
  useStore();
  const { doc } = props;
  const sendsRead = useSends(doc.ref, props.onSettled);
  const sends = mergeKnown(doc.ref, sendsRead.data ?? []);
  const [openedRef, setOpenedRef] = useState<string | null>(null);
  const prefix = `${doc.ref}|`;
  const held = [...store.holds.keys(), ...store.busy].some((key) => key.startsWith(prefix));
  const open = openedRef === doc.ref || held;
  const prepared = sends.filter((s) => s.state === "prepared").length;
  const running = sends.some((s) => s.state === "dispatching");
  const ended = sends.some((s) => s.state !== "prepared" && s.state !== "dispatching");
  const refusals = [...store.outcomes.entries()].filter(([key, outcome]) => key.startsWith(prefix) && outcome.kind === "refused");
  return (
    <div className="send-fold" data-send="fold" data-doc={doc.ref} data-testid="send-fold">
      <div className="send-fold-head">
        {prepared > 0 ? <StateChip state="active" label={`${SEND_WORDS.prepared} ×${prepared}`} /> : null}
        {running ? <StateChip state="active" label={SEND_WORDS.sending} /> : null}
        {ended && !open ? <StateChip state="idle" label={HISTORY_HEAD} /> : null}
        <Button dense variant="ghost" aria-expanded={open} disabled={held}
          onClick={() => setOpenedRef(open ? null : doc.ref)}>{open ? "Hide" : "Send…"}</Button>
      </div>
      {open ? <SendSheet {...props} onBack={() => setOpenedRef(null)} sendsRead={sendsRead} /> : <>
        {sendsRead.failed ? <Unreadable what="SENDS" testid="sends-unreadable" onRetry={sendsRead.reload} /> : null}
        {refusals.map(([key, outcome]) => <OutcomeLine key={key} o={outcome} />)}
      </>}
    </div>
  );
}

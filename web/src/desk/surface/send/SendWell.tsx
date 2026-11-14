import { parseReading, readingChildren, readingContent } from "../ReadingDocument";
import { proseDateWords, wireDayClock, wireClock } from "../format";
/* One Send species for every stored document. The kit owns channel tabs,
 * saved-destination choices, form rows, the completion row and the question.
 * Hosts keep the same public props and the shared per-document press store.
 *
 * One owner press holds the exact command id, document/destination or
 * prepared-send id, preview digest and bytes. A lost answer replays that
 * command; it never creates another dispatch. A settled unknown result can
 * start a new send only on another owner press. Preview reads also belong to
 * the saved document version and destination revision.
 */
import { createContext, lazy, Suspense, useCallback, useContext, useEffect, useLayoutEffect, useRef, useState,
  useSyncExternalStore, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { SurfaceState, SurfaceWell } from "../Surface";
import { InspectorFacts, InspectorActions, PaneGroup, type InspectorCompletion, ListPane, InspectorForm, InspectorQuestion,
  PaneActions, SegmentedTabs, CycleGadget, GadgetRow, ListView, StatusBar, objectSprite, type ListVerb } from "../index";
import { safeSendText, safeSendPreview, destinationRevision, sendPreviewBlocked, CREDENTIAL_WORD, EDIT_FAILED_WORD } from "./sendPresentation";
import { Material } from "../Material";
import { StateChip } from "../patterns";
import { DotWord } from "../kit";
import { fetchConnections, type ConnectionsResponse } from "../../../pages/cores/connections/api";
// HS-S53: the destination warning has one owner (features/channels); this
// module keeps its public name for the Send barrel.
import { accountChip } from "../../../features/channels/accountChip";
export { accountChip };
import { useDesk } from "../../store";
import { emailProvider, CHANNEL_WORD, DEST_CHANGED, SEND_WORDS, syncEgress, commandId, egressOf, failedWord, farSide,
  noAnswerWords, previewOf, refusalSize, refusedWord, sentWord, stamp, targetToken, unknownWord,
  wire, Refusal, type Channel, type Destination, type Preview, type Send, type WirePreview, type EmailProvider } from "../../../features/channels/channels";
import "./send-well.css";
import { keepPlace, keptPlace } from "../../deskMemory"; // PHILO-13-07 (B2)
import { clearPendingCommand, keepPendingCommand, pendingCommands, resetPendingCommands, type HeldCommand } from "./pendingCommand";
import { apiFetch } from "../../../lib/api";
import { openRef } from "../../openObject";
import { SEND_OPEN } from "../../windowSend";
import { Token } from "../Token";
import { stateWords } from "../words";
import { MiddleText } from "../MiddleText";
import { useCopyReceipt } from "../../hooks/useCopyReceipt";

// Channel names stay the same in every Send seat.
const CHANNEL_NAME: Record<string, string> = {
  file: "Folder",
  github: "GitHub",
  jira: "Jira",
  confluence: "Confluence",
  email: "Email",
  slack: "Slack",
};
const AdmittedDestinationForm = lazy(() =>
  import("../../../features/channels/DestinationForm").then((m) => ({
    default: m.DestForm,
  })),
);

/** A stored document and its saved revision. */
export type DocRef = { ref: string; title: string; label: string; version?: string };

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

export function useDestinations(includeParked = false): Read<Destination[]> {
  const [data, setData] = useState<Destination[] | null>(null);
  const [failed, setFailed] = useState(false);
  const reload = useCallback(() => {
    void wire.destinations(includeParked).then((r) => { setData(r); setFailed(false); }).catch(() => setFailed(true));
  }, [includeParked]);
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

/** The frozen fields and payload. The host owns scrolling; the payload well
 *  never traps the Send action. `Edit` is the one shared transition into the
 *  ordinary Note editor. */
export function PreviewWell({ preview, testid }: {
  preview: Preview; testid: string;
}) {
  const safe = safeSendPreview(preview);
  return <div data-send="preview" data-testid={testid} data-feedback-redact="true" role="region" aria-label="Preview">
    <PaneGroup label=""><InspectorForm>
      {safe.fields.map(f => <GadgetRow key={f.label} label={f.label}><span data-testid="send-preview-field">{f.value}</span></GadgetRow>)}
    </InspectorForm><GadgetRow label="" wide><SurfaceWell wholeLines><div className="send-preview-body" data-testid="send-preview-body">
      {safe.body_kind !== "text" ? <Material formatDates dialect={safe.body_kind}>{safe.body}</Material> : proseDateWords(safe.body)}
    </div></SurfaceWell></GadgetRow></PaneGroup>
  </div>;
}

export function SendDestinationWord({name,channel,empty = false}: {name?: string; channel?: string; empty?: boolean}) {
  return <span data-testid="send-destination-word" data-feedback-redact="true">{name ? safeSendText(name) : <span data-testid={empty ? "send-none" : undefined}>No destination</span>}</span>;
}

/** One edit transition for ordinary, prepared and Needs you previews. */
async function editSendPreview(title: string, destinationId: string, rendered: Preview) {
  const made = await apiFetch<{note?: {id?:string; note_id?:string}}>("/api/notes", {method:"POST",json:{
    title:`${safeSendText(title)} (to send)`, body_markdown:rendered.source_markdown ?? rendered.body, tags:["send"],
  }});
  const id = String(made.note?.id ?? made.note?.note_id ?? "");
  if (!id) throw new Error("note_not_created");
  const ref = `note:${id}`;
  pickDestination(ref, destinationId); keepPlace(`send/pick/${ref}`,destinationId);
  // A blocked draft must open its editor, so Edit can remove the credential.
  if (sendPreviewBlocked(rendered)) openRef(ref);
  else openNoteSend(ref);
}

type FaceDestination = Pick<Destination, "id" | "name" | "channel" | "target" | "account"> & { synced?: boolean };
/** Ordinary, frozen and Needs you sends use this one form and completion. */
export function SendFace({ destination, destinations, onDestination, onAdded, preview, previewTestId = "send-preview", completion, secondary, notice, children, editDestinationId, editAction, confirming = false, onAddDestination }: {
  destination?: FaceDestination; destinations?: FaceDestination[]; onDestination?(id: string): void; onAdded?(d: Destination): void;
  preview?: Preview | null; previewTestId?: string; completion: InspectorCompletion; secondary?: ReactNode; notice?: ReactNode; children?: ReactNode;
  editDestinationId?: string; editAction?: ReactNode; confirming?: boolean; onAddDestination?(): void;
}) {
  const [adding, setAdding] = useState(false);
  const [editing, setEditing] = useState(false);
  const [editFailed, setEditFailed] = useState(false);
  const blocked = Boolean(preview && sendPreviewBlocked(preview));
  if (adding) return <div className="surface-preference-pane" data-send="destination" data-testid="send-inline-destination" data-feedback-redact="true"><InlineDestinationForm
    onDone={d => { setAdding(false); if(d) onAdded?.(d); }} onCancel={() => setAdding(false)}
    onSetUpAccount={() => useDesk.getState().openSurfaceWindow("configure-settings", "integrations")} /></div>;
  const name = destination ? safeSendText(destination.name) : "No destination";
  const eg = destination ? egressOf(destination) : null;
  const leading = <>{secondary}{editAction ?? (blocked && destination && preview ? <Button dense variant="secondary" data-testid="send-edit" loading={editing} onClick={() => {
    setEditing(true); setEditFailed(false);
    void editSendPreview("Draft", editDestinationId ?? destination.id, preview).catch(() => setEditFailed(true)).finally(() => setEditing(false));
  }}>Edit</Button> : null)}<Button dense variant="secondary" data-verb-secondary data-testid="send-add-destination" disabled={"primary" in completion && completion.primary.busy} onClick={()=>onAddDestination ? onAddDestination() : setAdding(true)}>Add destination</Button></>;
  const confirmation = <>{destination?.channel === "file" ? "Save in " : destination ? "Send to " : ""}<SendDestinationWord name={destination?.name} channel={destination?.channel} empty={destinations?.length === 0} />{destination?.channel === "email" ? ` via ${emailProvider(destination.account).word}` : destination?.channel === "file" ? eg?.scope === "cloud" ? ` · ${safeSendText(eg.title)}` : " on this device" : destination ? ` on ${CHANNEL_WORD[destination.channel]}` : ""}</>;
  const guarded = "primary" in completion ? {...completion, primary:{...completion.primary, dispatching:true,
    disabled:blocked || completion.primary.disabled, run:() => {if (!blocked) completion.primary.run();}}} : completion;
  return <div data-send="face" className="surface-preference-pane"><InspectorForm completion={confirming ? undefined : { ...guarded, leading,
    state:<>{confirmation}{editFailed || blocked ? <><br /><DotWord tone="fail">{editFailed ? EDIT_FAILED_WORD : CREDENTIAL_WORD}</DotWord></> : null}</> }} notice={notice}>
    <GadgetRow label="Destination"><CycleGadget label="Destination" roster value={destination?.id ?? ""} disabled={!onDestination}
      options={[{value:"",label:"Choose a destination"}, ...(destinations ?? (destination ? [destination] : [])).map(d => ({value:d.id,label:safeSendText(d.name)}))]}
      onChange={id => onDestination?.(id)} />
    </GadgetRow>
    <GadgetRow label="" wide><div data-send="inspection" data-testid={destination ? previewTestId === "prepared-preview" ? "prepared-open" : "send-open" : undefined} data-destination={destination ? name : undefined} data-feedback-redact="true">
      {preview ? <PreviewWell preview={preview} testid={previewTestId} /> : children}
    </div></GadgetRow>
  </InspectorForm></div>;
}

/** A read that got no answer: named, with Retry. Never shown as empty. */
export function Unreadable({ what, testid, onRetry }: { what: string; testid: string; onRetry: () => void }) {
  return (
    <div className="surface-pane-actions" data-testid={testid}>
      <StateChip state="failure" label={`${SEND_WORDS.cannotRead} ${what}`} />
      <Button dense variant="secondary" data-testid={`${testid}-retry`} onClick={onRetry}>
        {SEND_WORDS.retry}
      </Button>
    </div>
  );
}

function OutcomeLine({ o }: { o: Outcome }) {
  if (o.kind === "refused") {
    return (
      <span className="surface-pane-actions" data-testid="send-refused" data-code={safeSendText(o.code)}>
        <StateChip state="failure" label="REFUSED" />
        <Token className="surface-token" data-chip>{refusedWord(o.code)}</Token>
        <Token className="surface-token" data-chip>{SEND_WORDS.nothingSent}</Token>
      </span>
    );
  }
  if (o.kind === "lost") {
    return (
      <span className="surface-pane-actions" data-testid="send-lost">
        <StateChip state="warning" label={SEND_WORDS.lost} />
        {o.storageFailed ? <Token className="surface-token" data-chip>{SEND_WORDS.storageUnavailable}</Token> : null}
      </span>
    );
  }
  return null;
}

/** The destination's latest send: the one receipt the open row shows. */
/** The egress a send's receipt names (judged at its boundary, kept on its row
 *  and in its proof): the sync service that took the file off this device. Every
 *  receipt branch (latest, prepared result, history) shows it. */
export function ReceiptEgress({ s }: { s: Pick<Send, "proof"> & { egress?: string | null } }) {
  const sync = syncEgress(s.egress ?? s.proof?.egress);
  return sync ? <span>{sync.label}</span> : null;
}

function LatestReceipt({ s, statusInBar = false }: { s: Send | undefined; statusInBar?: boolean }) {
  if (!s) return null;
  if (s.state === "sent")
    return (
      <span className="surface-pane-actions" data-testid="send-sent" data-receipt="latest" data-state="sent">
        <StateChip state="success" label={sentWord(s.channel, s.proof, s.account)} />
        <ProofCell channel={s.channel} proof={s.proof} target={s.target} account={s.account} />
        <ReceiptEgress s={s} />
      </span>
    );
  if (s.state === "failed")
    return (
      <span className="surface-pane-actions" data-testid="send-failed" data-receipt="latest" data-state="failed" data-code={safeSendText(s.reason ?? "")}>
        <StateChip state="failure" label="FAILED" />
        <Token className="surface-token" data-chip>
          {failedWord(s.reason ?? "")}
        </Token>
        <Token className="surface-token" data-chip>
          {SEND_WORDS.nothingSent}
        </Token>
      </span>
    );
  if (s.state === "unknown")
    return (
      <span className="surface-pane-actions" data-testid="send-unknown" data-receipt="latest" data-state="unknown">
        {!statusInBar ? <StateChip state="warning" label={SEND_WORDS.unknownChip} /> : null}
        <Token className="surface-token" data-chip>
          {s.reason ? unknownWord(s.reason) : "No answer"}
        </Token>
        <ReceiptEgress s={s} />
      </span>
    );
  if (s.state === "dispatching")
    return (
      <span className="surface-pane-actions" data-testid="send-running" data-receipt="latest" data-state="dispatching">
        <StateChip state="active" icon="◆" label={SEND_WORDS.sending} />
      </span>
    );
  return null;
}

export function openFar(url: string | null) {
  if (url) window.open(url, "_blank", "noopener");
}

/** Where a SENT row's proof opens: the comment, the work item, the post. */
export function proofLink(
  channel: string,
  proof: Record<string, unknown>,
  target?: Record<string, string | number>,
  account?: Record<string, string | boolean>,
): string {
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
  if (folder && display && (path === folder || path.startsWith(`${folder}/`))) return display + path.slice(folder.length);
  // No guess from a pattern: /Users/alice is not this HOME (Astra, #869).
  // Only the hub knows HOME; with no short token the path stays whole.
  return path;
}

/** The proof of a SENT row, exact as the channel gave it (no uppercasing). */
type ProofProps = { channel: string; proof: Record<string, unknown> | null; target?: Record<string, string | number>; account?: Record<string, string | boolean> };
export function ProofCell(props: ProofProps) { return <ProofValue key={`${props.channel}:${props.proof?.path ?? ""}`} {...props} />; }
function ProofValue({ channel, proof, target, account }: ProofProps) {
  const p = proof ?? {};
  const {copy, state} = useCopyReceipt();
  if (channel === "file")
    return (
      <span className="surface-pane-actions send-proof"><MiddleText cut="path" className="send-proof-path" testId="proof" title={safeSendText(String(p.path ?? ""))} value={safeSendText(shownPath(String(p.path ?? ""), target))} /><Button dense variant="secondary" onClick={() => void copy(String(p.path ?? ""))}>Copy path</Button>{state === "copied" ? "Copied" : state === "failed" ? <DotWord tone="fail">Copy failed</DotWord> : null}</span>
    );
  if (channel === "email")
    return (
      <Token code className="surface-token" data-chip data-wrap data-testid="proof">
        {safeSendText(`ID ${String(p.message_id ?? "")}`)}
      </Token>
    );
  // Slack by webhook answers only `ok`: the proof is the channel, never a link (design section 5).
  if (channel === "slack")
    return (
      <Token code className="surface-token" data-chip data-wrap data-testid="proof">
        {safeSendText(String(target?.channel_label ?? ""))}
      </Token>
    );
  const rawUrl = proofLink(channel, p, target, account);
  const url = safeSendText(rawUrl) === rawUrl ? rawUrl : "";
  const label = safeSendText(target ? targetToken(channel as Channel, target) : url.replace(/^https:\/\//, ""));
  return url ? (
    <Button
      dense
      variant="secondary"
      className="desk-chip quiet send-literal"
      data-testid="proof"
      data-href={url}
      title={url}
      onClick={() => openFar(url)}
    >
      {label}
    </Button>
  ) : (
    <Token code className="surface-token" data-chip data-wrap data-testid="proof">
      {label}
    </Token>
  );
}

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
  if (retry?.destination_id) store.picked.set(ref, retry.destination_id);
  else store.preparedOpen.set(ref, retry?.send_id ?? sendId);
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
  store.picked.set(ref, destinationId);
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

type PreviewState =
  | {
      ref: string;
      id: string;
      revision: string;
      digest: string;
      preview: WirePreview;
    }
  | {
      ref: string;
      id: string;
      revision: string;
      failed: true;
      code?: string;
      size?: { size: number; limit: number } | null;
    };

/** A preview that did not come: a named refusal (REFUSED + its word, the
 *  size and the limit when the answer carries them, NOTHING SENT, the
 *  Retry) or no answer at all (NO PREVIEW · NO ANSWER + Retry). */
function PreviewFailed({
  pv,
  onRetry,
}: {
  pv: Extract<PreviewState, { failed: true }>;
  onRetry: () => void;
}) {
  if (pv.code) {
    return (
      <div className="surface-pane-actions" data-testid="preview-refused" data-code={safeSendText(pv.code ?? "")}>
        <StateChip state="failure" label="REFUSED" />
        <Token className="surface-token" data-chip>
          {refusedWord(pv.code)}
        </Token>
        {pv.size ? (
          <Token className="surface-token" data-chip data-testid="preview-size">
            {`${pv.size.size.toLocaleString("en-US")} / ${pv.size.limit.toLocaleString("en-US")} CHARACTERS`}
          </Token>
        ) : null}
        <Token className="surface-token" data-chip>
          {SEND_WORDS.nothingSent}
        </Token>
        <Button dense variant="secondary" data-testid="preview-retry" onClick={onRetry}>{SEND_WORDS.retry}</Button>
      </div>
    );
  }
  return (
    <div className="surface-pane-actions" data-testid="preview-failed">
      <StateChip state="failure" label={SEND_WORDS.noPreview} />
      <Token className="surface-token" data-chip>
        No answer
      </Token>
      <Button dense variant="secondary" data-testid="preview-retry" onClick={onRetry}>
        {SEND_WORDS.retry}
      </Button>
    </div>
  );
}

/** A reader can wait until the destinations, sends and preview resolve. */
const ReceiptSelection = createContext<((s: Send) => void) | null>(null);
export const SendWellReadContext = createContext<((resolved: boolean) => void) | null>(null);

/** The one destination form, seated inside the Send sheet. This host
 * supplies its own account read and key callbacks, and returns the saved
 * row to the sheet. Set up account is the host's: it opens Settings ->
 * Connections in its own window; the sheet and the draft stay mounted. */
function InlineDestinationForm({ onDone, onCancel, onSetUpAccount }: {
  onDone: (saved?: Destination) => void; onCancel: () => void; onSetUpAccount: (channel: Channel) => void;
}) {
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
        keys={keys}
        onKey={onKey}
        onSlackKey={onSlackKey}
        onKeyKnown={onKeyKnown}
        onDone={onDone}
        onCancel={onCancel}
        onSetUpAccount={onSetUpAccount}
      />
    </Suspense>
  );
}

/** Open the new Note and deliver the existing window Send signal after its
 * pullout has mounted. The bounded retry is only for the asynchronous
 * arrival path; the note editor remains the owner of the Send state. The
 * retry stops at the first request the window takes (it cancels the event):
 * a later tick must not open Send again after the owner pressed Cancel. */
function openNoteSend(noteRef: string) {
  openRef(noteRef);
  if (typeof window === "undefined") return;
  const winId = `pullout:${noteRef}`;
  let tries = 0;
  const request = () => {
    const root = document.getElementById(winId);
    if (root?.querySelector("[data-testid=thought-send]")) return;
    const taken = !window.dispatchEvent(new CustomEvent(SEND_OPEN, { detail: { winId }, cancelable: true }));
    if (taken) return;
    tries += 1;
    if (tries < 30) window.setTimeout(request, 50);
  };
  request();
}

export function SendWell({
  doc,
  sendsRead,
  onSettled,
  head,
  destinationIds,
  onBack,
  history,
  initialTab,
}: {
  doc: DocRef;
  sendsRead: Read<Send[]>;
  onSettled?: () => void;
  head?: ReactNode;
  onBack?: () => void;
  /** Optional source-owned allow-list (for example a Room action's exact saved target). */
  destinationIds?: string[];
  history?: (sends: Send[]) => ReactNode;
  initialTab?: string;
}) {
  useStore();
  const hasHeld = [...store.holds.keys()].some(key => key.startsWith(`${doc.ref}|`));
  const dests = useDestinations(hasHeld);
  const reportRead = useContext(SendWellReadContext);
  const conns = useConnections();
  const ref = doc.ref;
  const [receiptPick, setReceiptPick] = useState<Send | null>(null);
  useEffect(() => setReceiptPick(null), [ref]);
  const sends = mergeKnown(ref, sendsRead.data ?? []);
  const rememberedPick = keptPlace(`send/pick/${ref}`);
  // B2: the kept pick returns, onto a listed destination only. With no kept pick
  // and no destination but the built-in HoldSpeak folder (a fresh desk), the folder is picked.
  const destinations = dests.data === null ? null : dests.data.filter((d) => (d.state === "active" || store.holds.has(`${ref}|${d.id}`)) && (!destinationIds || destinationIds.includes(d.id)));
  const orderedDestinations: Destination[] | null =
    destinations === null
      ? null
      : destinations.slice().sort((a, b) => {
          if (rememberedPick && a.id === rememberedPick) return -1;
          if (rememberedPick && b.id === rememberedPick) return 1;
          const at = latestFor(sends, a.id)?.dispatch_started_at ?? "";
          const bt = latestFor(sends, b.id)?.dispatch_started_at ?? "";
          return bt.localeCompare(at);
        });
  const onlyBuiltin = orderedDestinations?.length === 1 && orderedDestinations[0].builtin ? orderedDestinations[0].id : null;
  const savedPick = store.picked.get(ref);
  const picked =
    savedPick !== undefined && (savedPick === null || !destinationIds || destinationIds.includes(savedPick))
      ? savedPick
      : ((k) => (k && orderedDestinations?.some((d) => d.id === k) ? k : onlyBuiltin))(rememberedPick);
  const [preview, setPreview] = useState<PreviewState | null>(null);
  const [previewTry, setPreviewTry] = useState(0);
  const [editingPreview, setEditingPreview] = useState<string | null>(null);
  const [editFailure, setEditFailure] = useState<string | null>(null);
  const selectedDestination = destinations?.find((d) => d.id === picked);
  const revision = JSON.stringify([doc.version ?? "", selectedDestination ? destinationRevision(selectedDestination) : ""]);
  const [tab, setTab] = useState<string | null>(initialTab ?? null);
  const previousPick = useRef(`${ref}|${picked}`);
  useEffect(() => {
    const next = `${ref}|${picked}`;
    if (previousPick.current !== next) {
      previousPick.current = next;
      if (store.picked.has(ref)) setTab(selectedDestination?.channel ?? null);
    }
  }, [ref, picked, selectedDestination?.channel]);
  useEffect(() => {
    if (!picked) {
      setPreview(null);
      return;
    }
    let live = true;
    setPreview(null);
    void wire
      .preview(ref, picked)
      .then((p) => {
        if (live)
          setPreview({
            ref,
            id: picked,
            revision,
            digest: p.payload_digest,
            preview: p.preview,
          });
      })
      .catch((e) => {
        if (!live) return;
        setPreview(
          e instanceof Refusal
            ? {
                ref,
                id: picked,
                revision,
                failed: true,
                code: e.code,
                size: refusalSize(e),
              }
            : { ref, id: picked, revision, failed: true },
        );
      });
    return () => {
      live = false;
    };
  }, [ref, picked, previewTry, revision]);
  // T2: a PREVIEW CHANGED refusal reads the preview again (same document, same destination).
  const pickedOutcome = picked ? store.outcomes.get(`${ref}|${picked}`) : undefined;
  const changedAt =
    pickedOutcome?.kind === "refused" && (pickedOutcome.code === "preview_changed" || pickedOutcome.code === "payload_changed")
      ? pickedOutcome.at
      : 0;
  useEffect(() => {
    if (changedAt) setPreviewTry((n) => n + 1);
  }, [changedAt]);
  // The well's first reads: its destinations, its sends, and the preview of
  // the destination it picked on its own (Astra r1 on #1108: the preview drew
  // above the meeting's Decide and Transcript after the body was shown).
  const heldPreview = picked ? store.holds.get(`${ref}|${picked}`)?.preview : undefined;
  const previewRead =
    !picked || Boolean(heldPreview) || (preview !== null && preview.ref === ref && preview.id === picked && preview.revision === revision);
  const wellRead = (dests.data !== null || dests.failed) && (sendsRead.data !== null || sendsRead.failed) && previewRead;
  useLayoutEffect(() => {
    reportRead?.(wellRead);
  }, [reportRead, wellRead]);

  useEffect(() => {
    // Prepared rows already name their exact command target. A terminal read
    // resolves that row even if its browser answer was lost; it must not leave
    // a hidden pending Retry holding the fold open forever.
    let changed = false;
    for (const [k, command] of store.holds) {
      const ended = sendsRead.data?.find((s) => s.document_ref === ref && s.id === command.body.send_id && ENDED.has(s.state));
      if (!ended) continue;
      try {
        clearPendingCommand(ref, ended.id, command.key);
      } catch {
        /* a later reload replays safely */
      }
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
  const waiting = prepared.filter((s) => s.state === "prepared" || s.state === "dispatching");
  const openPrepared = store.preparedOpen.has(ref) ? store.preparedOpen.get(ref) : (waiting[0]?.id ?? null);
  const pendingReads = (destinations === null && !dests.failed) || (sendsRead.data === null && !sendsRead.failed);
  const edit = useCallback(
    async (destination: Destination, rendered: Preview) => {
      if (editingPreview) return;
      setEditingPreview(destination.id);
      setEditFailure(null);
      try {
        await editSendPreview(doc.title || "Note", destination.id, rendered);
      } catch (error) {
        setEditFailure(error instanceof Refusal ? error.code : "note_not_created");
      } finally {
        setEditingPreview(null);
      }
    },
    [doc.title, editingPreview],
  );

  const preparedPick = waiting.find((s) => s.id === openPrepared) ?? waiting[0];
  const channels = [...new Set(orderedDestinations?.map((d) => d.channel) ?? [])];
  const tabs = [
    ...(waiting.length ? [{ id: "prepared", label: "Prepared" }] : []),
    ...(channels.length ? channels : ["file" as Channel]).map((channel) => ({
      id: channel,
      label: CHANNEL_NAME[channel] ?? CHANNEL_WORD[channel] ?? channel,
    })),
    ...(history || sends.some(s => s.state === "sent" || s.state === "unknown") ? [{id:"history",label:"Sent"}] : []),
  ];
  const activeTab =
    tab && tabs.some((t) => t.id === tab) ? tab : preparedPick ? "prepared" : (selectedDestination?.channel ?? channels[0] ?? "file");
  const locked = [...store.busy].some((k) => k.startsWith(`${ref}|`));
  const select = (id: string) => {
    if (locked) return;
    store.picked.set(ref, id || null); bump();
    keepPlace(`send/pick/${ref}`, id);
  };
  const d = selectedDestination?.channel === activeTab ? selectedDestination : undefined;
  const k = picked ? `${ref}|${picked}` : "";
  const o = store.outcomes.get(k) ?? { kind: "none" as const };
  const held = store.holds.get(k);
  const last = picked ? latestFor(sends, picked) : undefined;
  const pv = d && preview?.ref === ref && preview.id === d.id && preview.revision === revision ? preview : null;
  // Needs you can start the same inline retry without mounting a preview.
  // Recover its frozen words from the stored row; a new draft is not that press.
  const heldSend = held && sends.find(s => s.destination_id === picked && s.payload_digest === held.body.preview_digest);
  const activePreview = held?.preview
    ?? (heldSend ? previewOf(heldSend.channel, heldSend.target, heldSend.account, heldSend.preview) : null)
    ?? (d && pv && !("failed" in pv) && (!held || pv.digest === held.body.preview_digest) ? previewOf(d.channel, d.target, d.account, pv.preview) : null);
  const noAnswer = last?.state === "unknown" && last.reason === "no_answer_in_time";
  const busy = store.busy.has(k) && !noAnswer;
  const far = d ? farSide(d.channel, d.target, d.account) : null;
  const acc = d ? accountChip(d, conns) : null;
  const chosenPrepared = activeTab === "prepared" ? preparedPick : undefined;
  const canSend =
    Boolean(d && activePreview && (held || (pv && !("failed" in pv)))) &&
    !busy &&
    !(last?.state === "dispatching" && !held) &&
    Boolean(held || (sendsRead.data !== null && !sendsRead.failed));
  const ordinaryCompletion = {
    cancel: () => {
      if (onBack) onBack();
      else select("");
    },
    cancelDisabled: busy,
    cancelTestId: "send-back",
    primary: {
      label:
        o.kind === "lost" && !noAnswer
          ? SEND_WORDS.retry
          : busy || last?.state === "dispatching"
            ? "Sending…"
          : last?.state === "failed" || last?.state === "unknown"
            ? SEND_WORDS.tryAgain
            : last
              ? SEND_WORDS.sendAgain
              : SEND_WORDS.send,
      testId: o.kind === "lost" && !noAnswer ? "send-retry" : "send-verb",
      busy,
      disabled: !canSend,
      run: () => {
        if (!canSend || !d) return;
        if (noAnswer) store.busy.delete(k);
        void press(
          ref,
          d.id,
          () => ({
            document_ref: ref,
            destination_id: d.id,
            preview_digest: pv && !("failed" in pv) ? pv.digest : "",
          }),
          reload,
          onSettled,
          activePreview ?? undefined,
        );
      },
    },
  };
  const discarded = prepared.filter(s => s.state === "discarded")
    .sort((a,b) => String(a.settled_at ?? "").localeCompare(String(b.settled_at ?? ""))).at(-1);
  const showDiscarded = d && discarded?.destination_id === d.id && !busy && (!last?.dispatch_started_at || String(discarded.settled_at ?? "") > last.dispatch_started_at);
  const statusSend = chosenPrepared ?? (activeTab === "history" ? receiptPick ?? last : last);
  const statusLost = chosenPrepared ? store.outcomes.get(`${ref}|${chosenPrepared.id}`) : o;
  const statusFailed = sendsRead.failed || dests.failed || (pv && "failed" in pv);
  const deliveryState = statusLost?.kind === "refused" ? "Refused" : statusFailed ? "Failed" : statusLost?.kind === "lost" ? "Result unknown"
    : showDiscarded && !chosenPrepared && activeTab !== "history" ? "Discarded" : statusSend?.state === "sent" ? `Sent at ${wireClock(statusSend.settled_at)}`
    : statusSend?.state === "unknown" ? "Result unknown" : statusSend?.state === "failed" ? "Failed"
    : statusSend?.state === "dispatching" || busy ? "Sending…" : chosenPrepared ? "Prepared" : showDiscarded ? "Discarded" : "New";
  const receipt = (
    <PaneActions>
      <span data-testid="send-receipt-line">
        {noAnswer && d ? (
          <span data-testid="send-no-answer" data-receipt="latest" data-state="unknown">
            {safeSendText(noAnswerWords(d.channel, d.account, d.target))}
          </span>
        ) : o.kind === "lost" || (o.kind === "refused" && (!last?.dispatch_started_at || o.at > Date.parse(last.dispatch_started_at))) ? (
          <OutcomeLine o={o} />
        ) : showDiscarded ? (
          <span data-testid="prepared-result">Document kept</span>
        ) : (
          <LatestReceipt s={last} statusInBar />
        )}
      </span>
      {last?.state === "unknown" && far && safeSendText(far) === far ? (
        <Button
          dense
          variant="secondary"
          data-testid="send-check"
          onClick={() => openFar(far)}
        >{`${SEND_WORDS.check} ${safeSendText(targetToken(d!.channel, d!.target))}`}</Button>
      ) : null}
    </PaneActions>
  );

  return (
    <div
      data-send="well"
      data-testid="send-well"
      data-doc={ref}
      className="surface-preference-pane"
      aria-busy={wellRead ? undefined : "true"}
      aria-label={`${SEND_WORDS.send} ${safeSendText(doc.title)}`}
      role="group"
    >
      {head}
      {pendingReads ? (
        <div data-testid="send-read-loading">
          <SurfaceState loading />
        </div>
      ) : null}
      {sendsRead.failed ? <Unreadable what="sends" testid="sends-unreadable" onRetry={reload} /> : null}
      {dests.failed ? <Unreadable what="destinations" testid="destinations-unreadable" onRetry={dests.reload} /> : null}
        <SegmentedTabs
          label="Send to"
          value={activeTab}
          tabs={tabs}
          onChange={(next) => {
            if (locked) return;
            setTab(next);
            if (next !== "prepared" && next !== "history") {
              const first = orderedDestinations?.find((d) => d.channel === next);
              if (first) select(first.id);
            }
          }}
        >
          {activeTab === "history" ? (
            <>
              <ReceiptSelection.Provider value={setReceiptPick}>{history ? history(sends) : <SendHistory sends={sends} />}</ReceiptSelection.Provider>
              {onBack ? <InspectorActions completion={{done:onBack,leading:receiptPick ? <SendDestinationWord name={receiptPick.destination_name ?? undefined} channel={receiptPick.channel} /> : undefined}} /> : null}
            </>
          ) : activeTab === "prepared" ? (
            <>
              {chosenPrepared && (
                <PreparedRow
                  key={chosenPrepared.id}
                  docRef={ref}
                  label={doc.label}
                  s={chosenPrepared}
                  reload={reload}
                  conns={conns}
                  choices={waiting} onPick={id => { if(!locked) { store.preparedOpen.set(ref,id); bump(); } }}
                  dest={destinations?.find((d) => d.id === chosenPrepared.destination_id)}
                  onSettled={() => {
                    const next = destinations?.find((d) => d.id === chosenPrepared.destination_id);
                    const result = store.known.get(chosenPrepared.id);
                    if (next && result && ENDED.has(result.state) && result.state !== "discarded") {
                      select(next.id);
                      setTab(next.channel);
                    }
                    onSettled?.();
                  }}
                  onBack={onBack ?? (() => setTab(channels[0] ?? "file"))}
                />
              )}
            </>
          ) : (
            <SendFace destination={d} destinations={orderedDestinations?.filter(d => d.channel === activeTab)}
              onDestination={locked ? undefined : select} onAdded={saved => { select(saved.id); setTab(saved.channel); dests.reload(); }} preview={activePreview}
              completion={ordinaryCompletion} editAction={d && activePreview ? <Button dense variant="secondary" data-testid="send-edit"
                loading={editingPreview === d.id} disabled={editingPreview === d.id || busy} onClick={() => void edit(d, activePreview)}>Edit</Button> : null}
              notice={<>{acc ? <StateChip state={acc.state} label={safeSendText(acc.label)} /> : null}{receipt}
                  {(orderedDestinations ?? [])
                    .filter((other) => other.id !== d?.id)
                    .map((other) => {
                      const outcome = store.outcomes.get(`${ref}|${other.id}`);
                      const latest = latestFor(sends, other.id);
                      if (outcome?.kind !== "lost" && outcome?.kind !== "refused" && latest?.state !== "failed" && latest?.state !== "unknown") return null;
                      return (
                        <PaneActions key={other.id}>
                          <span>{safeSendText(other.name)}</span>
                          {outcome?.kind === "lost" || outcome?.kind === "refused" ? (
                            <OutcomeLine o={outcome} />
                          ) : (
                            <LatestReceipt s={latest} />
                          )}
                        </PaneActions>
                      );
                    })}
{editFailure ? <span data-testid="send-edit-failed"><DotWord tone="fail">{EDIT_FAILED_WORD}</DotWord></span> : null}</>}>
              {orderedDestinations?.length === 0 ? null : !pv ? <div data-testid="send-preview-loading"><PaneActions role="status" aria-busy="true"><DotWord tone="info">Preparing preview…</DotWord></PaneActions></div>
                : "failed" in pv ? <PreviewFailed pv={pv} onRetry={() => setPreviewTry(n => n + 1)} /> : null}
            </SendFace>
          )}
        </SegmentedTabs>
      <StatusBar data-testid="send-status" parts={[{ key: "delivery", text: deliveryState, lamp: deliveryState === "Failed" || deliveryState === "Refused" ? "fail" : deliveryState === "Result unknown" ? "ask" : undefined, priority: 100 }]} />
    </div>
  );
}

function byWord(s: Send): string {
  const kind = s.prepared_by?.kind ?? "";
  // WORDS-VOCAB: said in sentence case here; the name stays as typed.
  if (kind === "owner") return "By you";
  if (kind === "steward" || kind === "scheduler") return "By steward";
  return `By ${safeSendText(String(s.prepared_by?.identity || kind))}`;
}

/** Frozen sends keep their exact command and revision-bound discard question. */
function PreparedRow({docRef,label,s,reload,conns,dest,onSettled,onBack,choices,onPick}: {
  docRef: string; label: string; s: Send; reload(): void; conns: ConnectionsResponse | null;
  dest: Destination | undefined; onSettled?(): void; onBack?(): void; choices: Send[]; onPick(id: string): void;
}) {
  const k = `${docRef}|${s.id}`;
  const o = store.outcomes.get(k) ?? { kind: "none" as const };
  const busy = store.busy.has(k) || s.state === "dispatching";
  const revision = JSON.stringify([s.id, s.payload_digest, (s as Send & {target_digest?: string}).target_digest, s.target, s.account, s.created_at, s.destination_name]);
  const [question, setQuestion] = useState<string | null>(null);
  const [discardBusy, setDiscardBusy] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);
  useLayoutEffect(() => {
    if (question && question !== revision) setQuestion(null);
  }, [question, revision]);
  const dead = o.kind === "refused" && ["destination_changed", "destination_parked", "preview_changed"].includes(o.code);
  const name = safeSendText(s.destination_name ?? dest?.name ?? "Destination");
  const acc = accountChip({channel:s.channel,connection:dest?.connection,account:{...s.account,...(dest?.account.key_present === false ? {key_present:false} : {})}},conns);
  return (
    <div data-testid="prepared-row" className="surface-preference-pane" data-send="prepared">

        <SendFace destination={{id:s.id,name,channel:s.channel,target:s.target,account:s.account,synced:dest?.synced}}
          destinations={choices.map(row => ({id:row.id,name:(row.destination_name ?? "Destination") + (choices.length > 1 ? ` · ${byWord(row)} · ${stateWords(stamp(row.created_at))}` : ""),channel:row.channel,target:row.target,account:row.account}))}
          onDestination={choices.length > 1 && !busy ? onPick : undefined}
          confirming={question === revision} editDestinationId={s.destination_id} preview={previewOf(s.channel,s.target,s.account,s.preview,s.file_path)} previewTestId="prepared-preview"
          completion={{
            cancel: () => onBack?.(),
            cancelDisabled: busy,
            cancelTestId: "send-back",
            primary: {
              label: o.kind === "lost" ? SEND_WORDS.retry : SEND_WORDS.send,
              testId: o.kind === "lost" ? "prepared-retry" : "prepared-send",
              busy,
              disabled: dead,
              run: () => void press(docRef, s.id, () => ({ send_id: s.id }), reload, onSettled),
            },
          }}
          secondary={<Button dense variant="secondary" disabled={busy} data-testid="prepared-discard" onClick={() => setQuestion(revision)}>Discard</Button>}
          notice={<>{acc ? <StateChip state={acc.state} label={safeSendText(acc.label)} /> : null}<OutcomeLine o={o} />{s.state === "dispatching" ? <LatestReceipt s={s} /> : null}
            <InspectorFacts header={false} name="Prepared send" rows={[
              {label:"Prepared",value:<span data-testid="prepared-by">{byWord(s)}</span>},
              {label:"Document",value:<span data-testid="prepared-label">{stateWords(safeSendText(label))}</span>},
            ]} /></>}
        />
      {question === revision ? (
        <InspectorQuestion
          actionId="discard-send"
          targetId={revision}
          testId="inspector-question"
          leading={<SendDestinationWord name={name} channel={s.channel} />}
          question={`Discard send to ${name}?`}
          keeps={["The document"]}
          cancel={() => setQuestion(null)}
          notice={failure ? <span data-testid="discard-refused">{refusedWord(failure)}</span> : null}
          verb={{
            label: "Discard",
            testId: "prepared-discard-confirm",
            busy: discardBusy,
            run: () => {
              setDiscardBusy(true);
              setFailure(null);
              void discardPrepared(s.id)
                .then(() => {
                  store.outcomes.delete(k);
                  store.preparedOpen.delete(docRef);
                  setQuestion(null);
                  reload();
                  onSettled?.();
                })
                .catch((e) => setFailure(e instanceof Refusal ? e.code : "no_answer"))
                .finally(() => setDiscardBusy(false));
            },
          }}
        />
      ) : null}
    </div>
  );
}

/** Name the frozen document, not the destination shared by many receipts. */
function sentDocumentName(send: Send): string {
  const title = send.document_json?.title || send.preview.title || send.preview.subject;
  if (typeof title === "string" && title.trim()) return safeSendText(title);
  const text = String(send.preview.markdown ?? send.preview.text ?? "");
  const heading = readingChildren(parseReading(text)).find(node => /^(ATX|Setext)Heading/.test(node.name));
  return safeSendText(heading ? readingContent(heading, text) : "Document name not reported");
}

/** The shared sheet's one receipt list: SENT, with no counter at zero. */
export const HISTORY_HEAD = "SENT";

/** `tag` (PHILO-13-15, Astra C5 check condition 2): a host whose document has
 *  forms (the meeting) names each row's form, so a result of another form
 *  stays readable after he switches form. */
export function SendHistory({ sends, tag }: { sends: Send[]; tag?: (s: Send) => { form: string; word: string } | null }) {
  const publishPick = useContext(ReceiptSelection);
  const [selected, setSelected] = useState<string | null>(null);
  const rows = sends
    .filter((s) => s.state === "sent" || s.state === "unknown")
    .sort((a, b) => String(b.settled_at ?? "").localeCompare(String(a.settled_at ?? "")));
  if (!rows.length) return null;
  const link = (id: string) => {
    const s = rows.find((s) => s.id === id);
    if (!s) return null;
    const url = s.state === "unknown" ? farSide(s.channel, s.target, s.account) : proofLink(s.channel, s.proof ?? {}, s.target, s.account);
    return url && safeSendText(url) === url ? url : null;
  };
  const current = rows.find((s) => s.id === selected);
  const verbs: ListVerb[] = rows.some(s => link(s.id)) ? [
    {
      id: "check-send",
      label: "Check destination",
      enabled: (row) => Boolean(row && link(row.id)),
      run: (row) => {
        if (row) openFar(link(row.id));
      },
    },
  ] : [];
  return (
    <div data-send="history" data-species="send" data-testid="send-history" data-feedback-redact="true" className="surface-preference-pane">
      <ListPane
        label="Send receipt"
        list={
          <ListView
            ordered
            label="Sent"
            rows={rows.map((s) => ({
              id: s.id,
              kind: "note",
              name: sentDocumentName(s),
              detail: safeSendText(s.destination_name ?? "Destination"),
              when: wireDayClock(s.settled_at || s.dispatch_started_at),
              cells: {
                result: (
                  <span data-testid="history-word">
                    {s.state === "sent" ? sentWord(s.channel, s.proof, s.account) : SEND_WORDS.unknownChip}
                    {s.egress || s.proof?.egress ? ` · ${syncEgress(s.egress ?? s.proof?.egress)?.label ?? ""}` : ""}
                  </span>
                ),
                form: tag?.(s) ? (
                  <span data-testid="history-form" data-form={tag(s)!.form}>
                    {stateWords(safeSendText(tag(s)!.word))}
                  </span>
                ) : (
                  ""
                ),
              },
            }))}
            columns={[
              { key: "when", word: "When", priority: 1, track: "138px" },
              { key: "name", word: "Document" },
              { key: "result", word: "Result", priority: 3 },
              ...(tag ? [{ key: "form", word: "Form", priority: 2 as const }] : []),
            ]}
            selectedId={selected}
            onSelect={id => { setSelected(id); const send = rows.find(s => s.id === id); if(send) publishPick?.(send); }}
            onOpen={(id) => openFar(link(id))}
            verbs={verbs}
            defaultVerb="check-send"
            rowProps={(row) => ({
              "data-testid": "history-row",
              "data-to": sends.find(send => send.id === row.id)?.destination_name,
            })}
          />
        }
      >
        {current ? (
          <InspectorFacts
            object={current.channel === "file" ? <img src={objectSprite("directory", String(current.target.folder ?? current.destination_id), "rest", 32)} width={32} height={32} alt="" draggable={false} /> : undefined}
            name={safeSendText(current.destination_name ?? "Destination")}
            rows={[
              { label: "Result", value: <LatestReceipt s={current} /> },
              { label: "When", value: stateWords(stamp(current.settled_at)) },
              { label: "Document", value: sentDocumentName(current) },
              { label: "Prepared", value: byWord(current) },
            ]}
          />
        ) : null}
      </ListPane>
    </div>
  );
}

/** The PREPARED ×K chip for a document's host head (the Chair BRIEF head,
 *  a Room decision row). No chip at zero. `data-head-chip` lets a section
 *  head wrap its chips under its label at narrow width (surface.css). */
export function PreparedChip({ docRef }: { docRef: string }) {
  const { data } = useSends(docRef);
  const k = mergeKnown(docRef, data ?? []).filter((s) => s.state === "prepared").length;
  return k > 0 ? (
    <span data-head-chip data-testid="doc-prepared-chip">
      <StateChip state="active" icon="◆" label={`${SEND_WORDS.prepared} ×${k}`} />
    </span>
  ) : null;
}

/** The species as a host composes it: the well, then its history, over ONE
 *  read of the document's sends. `head` sits first inside SEND. `history`
 *  is the slot only the update fills (its DELIVERY N and Mark delivered,
 *  R8); every other document gets SENDS N. */
type SendWellsProps = {
  doc: DocRef;
  head?: ReactNode;
  onSettled?: () => void;
  history?: (sends: Send[]) => ReactNode;
  /** Initial tab only; later choices and retained receipts stay in their view. */
  initialTab?: string;
  destinationIds?: string[];
  /** The host's narrow Back state. The shared sheet owns the control and
   * returns focus to the host's opening Send… control through this callback. */
  onBack?: () => void;
};

export function SendSheet({
  doc,
  head,
  onSettled,
  history,
  initialTab,
  destinationIds,
  onBack,
  sendsRead,
}: SendWellsProps & { sendsRead: Read<Send[]> }) {
  const opener = useRef(document.activeElement instanceof HTMLElement ? document.activeElement : null);
  const back = onBack ? () => {
    const target = opener.current;
    onBack();
    requestAnimationFrame(() => { if (target?.isConnected) target.focus(); });
  } : undefined;
  return (
    <div data-send="sheet" data-testid="send-sheet" data-doc={doc.ref} className="send-sheet surface-preference-pane">
      <SendWell
        doc={doc}
        sendsRead={sendsRead}
        onSettled={onSettled}
        head={head}
        destinationIds={destinationIds}
        onBack={back}
        history={history}
        initialTab={initialTab}
      />
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
      <div className="surface-pane-actions">
        {prepared > 0 ? <StateChip state="active" label={`${SEND_WORDS.prepared} ×${prepared}`} /> : null}
        {running ? <StateChip state="active" label={SEND_WORDS.sending} /> : null}
        {ended && !open ? <StateChip state="idle" label={HISTORY_HEAD} /> : null}
        <Button dense variant="secondary" aria-expanded={open} disabled={held}
          onClick={() => setOpenedRef(open ? null : doc.ref)}>{open ? "Hide" : "Send…"}</Button>
      </div>
      {open ? <SendSheet {...props} onBack={() => setOpenedRef(null)} sendsRead={sendsRead} /> : <>
        {sendsRead.failed ? <Unreadable what="SENDS" testid="sends-unreadable" onRetry={sendsRead.reload} /> : null}
        {refusals.map(([key, outcome]) => <OutcomeLine key={key} o={outcome} />)}
      </>}
    </div>
  );
}

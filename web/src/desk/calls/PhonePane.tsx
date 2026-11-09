/* Phone (PHONE-DESIGN-2026-10-28 §9): the phone's pane in the Calls window
 * (the language, 2026-11-08). The rail's phone row picks it.
 *
 * The MAST is the paired phone (its name; paired and seen in mono); the
 * PLATE is the one thing now: a line from his phone or a desk ask that waits
 * on him, with the composer to answer it (Reply), else the composer to write
 * to the phone (Send); the LEDGER is the thread by time (time · who · words;
 * a reply under the line it answers; a desk call as one line with its state
 * and its one verb on the line). No host, number or engine chip (UX-CANON
 * A.9): egress is said in the Phone fold. */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { openRef } from "../openObject";
import { spriteUrl } from "../sprites";
import { ComposerWell } from "../surface/ComposerWell";
import { PadGadget } from "../surface/gadgets";
import { DotWord, countWords, type StatusBarItem } from "../surface/kit";
import { Mast } from "../surface/patterns/Mast";
import { Spine } from "../surface/patterns/Spine";
import type { ObjectTone } from "../surface/objects/kinds";
import { SurfaceState } from "../surface/Surface";
import { stateWords } from "../surface/words";
import { plainFail } from "../surface/plainFailure";
import { canReach, markPhoneMessageRead, pairedPhone, phoneCallVerb, sendPhoneMessage, waitsForReply, type usePhone } from "./phoneApi";
import type { PhoneCall, PhoneDevice, PhoneMessage } from "./phoneTypes";
import { usePhoneFocus } from "./phoneFocus";
import "./phone.css";

function at(value: string | null | undefined): number {
  const ms = value ? Date.parse(value) : NaN;
  return Number.isFinite(ms) ? ms : NaN;
}

export function clock(value: string | null | undefined): string {
  const ms = at(value);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
}

/** The day caption of a thread band: Today, Yesterday, `Mon 26 Oct`. */
export function dayWords(value: string, now = new Date()): string {
  const date = new Date(at(value));
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === now.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
}

function minutes(fromMs: number, toMs: number): string {
  const seconds = Math.max(0, Math.round((toMs - fromMs) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** A desk line's receipt (§4: sent → delivered → read). */
export function receiptWords(message: PhoneMessage): { word: string; tone: ObjectTone | "idle" } {
  if (message.read_at) return { word: stateWords("READ"), tone: "ok" };
  if (message.delivered_at) return { word: stateWords("DELIVERED"), tone: "idle" };
  return { word: stateWords("SENT"), tone: "idle" };
}

/** A call's state in a dot and a word (§4). */
export function callStateWords(call: PhoneCall): { word: string; tone: ObjectTone | "idle"; live?: boolean } {
  const urgent = call.urgent ? " · urgent" : "";
  switch (call.state) {
    case "held": return { word: "Waits for your yes", tone: "ask" };
    case "ringing": return { word: "Ringing", tone: "info", live: true };
    case "answered": return { word: "On the call", tone: "fail", live: true };
    case "missed": return { word: `Missed${urgent}`, tone: "fail" };
    case "declined": return { word: `Declined${urgent}`, tone: "warn" };
    default: {
      const start = at(call.answered_at);
      const end = at(call.ended_at);
      return Number.isFinite(start) && Number.isFinite(end)
        ? { word: `Answered · ${minutes(start, end)}`, tone: "ok" }
        : { word: stateWords("ENDED"), tone: "idle" };
    }
  }
}

function callLead(call: PhoneCall): string {
  if (call.direction === "from_phone") return "You called";
  if (call.state === "held") return "Call you about";
  if (call.state === "missed") return "Missed call";
  if (call.state === "declined") return "Declined call";
  return "Called you";
}

type Entry =
  | { kind: "message"; at: number; message: PhoneMessage; reply: boolean; waits: boolean }
  | { kind: "call"; at: number; call: PhoneCall };

/** The thread in reading order: roots by time, each reply under the line
 *  it answers (and the replies to that reply after it). */
export function threadEntries(messages: readonly PhoneMessage[], calls: readonly PhoneCall[]): Entry[] {
  const ids = new Set(messages.map((message) => message.id));
  const children = new Map<string, PhoneMessage[]>();
  const roots: Entry[] = [];
  for (const message of messages) {
    if (message.reply_to && ids.has(message.reply_to)) {
      const list = children.get(message.reply_to) ?? [];
      list.push(message);
      children.set(message.reply_to, list);
    } else {
      roots.push({ kind: "message", at: at(message.created_at) || 0, message, reply: false, waits: waitsForReply(message, messages) });
    }
  }
  for (const call of calls) roots.push({ kind: "call", at: at(call.created_at) || 0, call });
  roots.sort((a, b) => a.at - b.at);
  const out: Entry[] = [];
  const walk = (id: string) => {
    for (const child of (children.get(id) ?? []).sort((a, b) => a.seq - b.seq)) {
      out.push({ kind: "message", at: at(child.created_at) || 0, message: child, reply: true, waits: waitsForReply(child, messages) });
      walk(child.id);
    }
  };
  for (const root of roots) {
    out.push(root);
    if (root.kind === "message") walk(root.message.id);
  }
  return out;
}

/** Where a desk line came from, in words, and what it opens. */
export function originOf(ref: string | null | undefined): { words: string; open?: string } | null {
  const text = String(ref ?? "");
  if (!text) return null;
  const [kind, id] = text.split(":");
  if (kind === "program" && id) return { words: "a program", open: `program:${id}` };
  if (kind === "program_step") return { words: "a program step" };
  if (kind === "agent") return { words: "an agent" };
  if (kind === "phone_call") return { words: "a missed call" };
  if (kind === "heartbeat") return { words: "the heartbeat" };
  return null;
}

function MessageLine({ message, reply, waits, replying, onReply }: {
  message: PhoneMessage; reply: boolean; waits: boolean; replying: boolean; onReply(): void;
}) {
  const desk = message.direction === "to_phone";
  const receipt = desk ? receiptWords(message) : null;
  const origin = desk ? originOf(message.origin_ref) : null;
  return (
    <li className="phone-msg" data-reply={reply || undefined} data-waits={waits || undefined}
      data-replying={replying || undefined} data-direction={message.direction}
      data-testid="phone-message" data-message={message.id}>
      <span className="phone-at">{clock(message.created_at)}</span>
      <span className="phone-msg-body">
        <span className="phone-who" data-who={desk ? "holdspeak" : "you"}>
          {desk ? "HoldSpeak" : "You"}
          {origin ? (
            <span className="phone-from">
              {" · from "}
              {origin.open ? (
                <Button variant="ghost" dense className="phone-from-link" onClick={() => openRef(origin.open!)}
                  data-testid="phone-message-origin">{origin.words}</Button>
              ) : <span data-testid="phone-message-origin">{origin.words}</span>}
            </span>
          ) : !desk ? <span className="phone-from"> · from your phone</span> : null}
        </span>
        <span className="phone-text">{message.text}</span>
      </span>
      <span className="phone-msg-end">
        {receipt ? <DotWord tone={receipt.tone} data-testid="phone-receipt">{receipt.word}</DotWord> : null}
        {!desk ? (
          <Button variant="ghost" dense className="phone-reply" onClick={onReply} data-testid="phone-reply">Reply</Button>
        ) : null}
      </span>
    </li>
  );
}

function CallLine({ call, busy, onOpen, onVerb }: {
  call: PhoneCall; busy: boolean; onOpen?: () => void; onVerb(verb: "again" | "ring"): void;
}) {
  const state = callStateWords(call);
  return (
    <li className="phone-call" data-state={call.state} data-testid="phone-call" data-call={call.id}>
      <span className="phone-at">{clock(call.created_at)}</span>
      <img src={spriteUrl("call", "calls", "rest", null, 20)} alt="" width={20} height={20} draggable={false} />
      <span className="phone-call-what">
        <span className="phone-call-words"><b>{callLead(call)}:</b> {call.reason}</span>
        <DotWord tone={state.tone} data-testid="phone-call-state">{state.word}</DotWord>
      </span>
      <span className="phone-call-verb">
        {call.state === "missed" || call.state === "declined" ? (
          <Button variant="primary" dense loading={busy} onClick={() => onVerb("again")} data-testid="phone-call-again">Call again</Button>
        ) : call.state === "held" ? (
          <Button variant="primary" dense loading={busy} onClick={() => onVerb("ring")} data-testid="phone-call-ring">Call now</Button>
        ) : onOpen ? (
          <Button variant="secondary" dense onClick={onOpen} data-testid="phone-open-transcript">Open transcript</Button>
        ) : null}
      </span>
    </li>
  );
}

/** A call's transcript: a Calls call (`call:<id>`) opens in the Calls
 *  wing; another ref opens as its object. */
export function transcriptOf(call: PhoneCall): { callsId?: string; ref?: string } | null {
  const ref = String(call.transcript_ref ?? "");
  if (!ref) return null;
  return ref.startsWith("call:") ? { callsId: ref.slice("call:".length) } : { ref };
}

/** The push word of a paired phone (`push_state`, RECIPE PH13): null when
 *  a push will go (or the hub did not say), else "Push not ready" and why. */
const PUSH_REASONS: Record<string, string> = {
  no_key: "no Apple push key on the hub",
  http2_unavailable: "the hub has no HTTP/2",
  unregistered: "the phone sent no push token",
};

export function pushNotReady(device: PhoneDevice): string | null {
  const reason = device.push_state ? PUSH_REASONS[device.push_state] : undefined;
  return reason ? `Push not ready: ${reason}` : null;
}

/** `Paired 21 Oct · seen 2 min ago`. */
export function deviceFact(device: PhoneDevice, now = Date.now()): string {
  const paired = at(device.paired_at);
  const seen = at(device.last_seen_at);
  const parts: string[] = [];
  if (Number.isFinite(paired)) parts.push(`Paired ${new Date(paired).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`);
  if (Number.isFinite(seen)) {
    const mins = Math.max(0, Math.round((now - seen) / 60_000));
    parts.push(mins < 1 ? "seen now" : mins < 60 ? `seen ${mins} min ago` : `seen ${clock(device.last_seen_at)}`);
  }
  return parts.join(" · ");
}


/** The status bar of the phone's pane: what waits on him, the calls from the desk. */
export function phoneStatusItems(phone: ReturnType<typeof usePhone>): Array<StatusBarItem | null> {
  const device = pairedPhone(phone.status);
  const waiting = phone.messages.filter((message) => waitsForReply(message, phone.messages));
  const none = <span className="calls-idle-word"><span className="kit-dot" data-tone="idle" aria-hidden="true" />No phone paired</span>;
  if (phone.status == null) return [{ key: "none", text: none }];
  return [
    waiting.length
      ? { key: "waits", lamp: "ask", text: waiting.length === 1 ? "A reply is waiting on you" : `${waiting.length} replies are waiting on you`, testId: "phone-status-waits" }
      : device ? { key: "paired", lamp: "ok", text: "Your phone is paired", testId: "phone-status-paired" }
        : phone.status.line?.ready ? { key: "number", lamp: "ok", text: "Reaches you by number", testId: "phone-status-number" }
          : { key: "none", text: none, testId: "phone-status-none" },
    { key: "calls", text: countWords(phone.calls.filter((call) => call.direction === "to_phone").length, "call from the desk", "calls from the desk") },
  ];
}

export function PhonePane({ phone, onOpenCall, onPair, onBack }: {
  phone: ReturnType<typeof usePhone>;
  /** Open a Calls call (a desk call on the number transport) as a document. */
  onOpenCall(callsId: string): void;
  /** Pair a phone: the Phone fold at the window's foot (Settings when the hub has no phone). */
  onPair(): void;
  /** A narrow window: back to the rail. */
  onBack(): void;
}) {
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{ words: string; title: string } | null>(null);
  const replyTo = usePhoneFocus((st) => st.replyTo);
  const clearReply = usePhoneFocus((st) => st.clear);
  const [replying, setReplying] = useState<string | null>(replyTo);
  useEffect(() => { if (replyTo) setReplying(replyTo); }, [replyTo]);
  const composer = useRef<HTMLTextAreaElement | null>(null);

  const device = pairedPhone(phone.status);
  const reachable = canReach(phone.status);
  const entries = useMemo(() => threadEntries(phone.messages, phone.calls), [phone.messages, phone.calls]);
  const waiting = phone.messages.filter((message) => waitsForReply(message, phone.messages));
  const replyLine = replying ? phone.messages.find((message) => message.id === replying) ?? null : null;
  // The one thing now: the line he replies to, else the newest line that waits on him.
  const ask = replyLine ?? waiting[waiting.length - 1] ?? null;

  // Reading a line from his phone marks it read (his phone sees the receipt).
  const unread = phone.messages.filter((message) => message.direction === "from_phone" && !message.read_at).map((m) => m.id).join(",");
  useEffect(() => {
    if (!unread) return;
    for (const id of unread.split(",")) void markPhoneMessageRead(id).catch(() => undefined);
  }, [unread]);

  const run = async (kind: string, act: () => Promise<void>, failed: (cause: unknown) => { words: string; title: string }) => {
    setBusy(kind);
    setRefusal(null);
    try { await act(); } catch (error) {
      setRefusal(failed(error));
    } finally { setBusy(""); }
  };
  const send = () => {
    const text = draft.trim();
    if (!text) return;
    void run("send", async () => {
      await sendPhoneMessage(text, replying);
      setDraft("");
      setReplying(null);
      clearReply();
      await phone.catchUp();
    }, (cause) => plainFail("The message did not reach your phone", cause, "Your words are kept", "Try again"));
  };
  const callVerb = (call: PhoneCall, verb: "again" | "ring") => void run(`call-${call.id}`, async () => {
    await phoneCallVerb(call.id, verb);
    await phone.reload();
  }, (cause) => plainFail("The call did not start", cause, "Nothing rang", "Try again"));
  const openTranscript = (call: PhoneCall) => {
    const where = transcriptOf(call);
    if (where?.callsId) onOpenCall(where.callsId);
    else if (where?.ref) openRef(where.ref);
  };

  if (phone.loading || phone.error) {
    return <SurfaceState loading={phone.loading} error={phone.error} onRetry={() => void phone.reload()} />;
  }
  if (!reachable && !entries.length) {
    return (
      <SurfaceState
        empty
        emptyKind="call"
        emptyImage={spriteUrl("call", "calls")}
        emptyLabel="No phone yet"
        emptyHint="Pair a phone, or add a number in Calls, and the desk can reach you."
        actionLabel="Pair a phone"
        onAction={onPair}
      />
    );
  }

  let lastDay = "";
  const rows: ReactNode[] = [];
  for (const entry of entries) {
    const when = entry.kind === "message" ? entry.message.created_at : entry.call.created_at;
    const day = dayWords(when);
    if (day !== lastDay && !(entry.kind === "message" && entry.reply)) {
      rows.push(<li key={`day-${when}`} className="phone-day" aria-hidden="true">{day}</li>);
      lastDay = day;
    }
    rows.push(entry.kind === "message" ? (
      <MessageLine key={entry.message.id} message={entry.message} reply={entry.reply} waits={entry.waits} replying={replying === entry.message.id}
        onReply={() => { setReplying(entry.message.id); composer.current?.focus(); }} />
    ) : (
      <CallLine key={entry.call.id} call={entry.call} busy={busy === `call-${entry.call.id}`}
        onOpen={transcriptOf(entry.call) ? () => openTranscript(entry.call) : undefined}
        onVerb={(verb) => callVerb(entry.call, verb)} />
    ));
  }
  const push = device ? pushNotReady(device) : null;
  const facts = device ? deviceFact(device) : phone.status?.line?.ready ? "Reaches you by number" : "No phone paired";
  const tone = waiting.length ? "brass" : refusal ? "coral" : device || phone.status?.line?.ready ? "moss" : "idle";
  return (
    <article className="cl-object phone-pane" data-testid="phone-wing">
      <Mast className="cl-mast" kind="call" id="phone" title={device?.name ?? "Your phone"} facts={facts} data-testid="phone-device">
        {push ? <DotWord tone="warn" data-testid="phone-device-push" title={push}>Push not ready</DotWord> : null}
        <Button variant="ghost" dense className="cl-back" onClick={onBack}>All calls</Button>
      </Mast>
      <Spine className="cl-spine" tone={tone} />
      <section className="cl-plate" data-tone={waiting.length ? "brass" : "steel"} data-testid="phone-plate">
        <header className="cl-plate-head">
          <h3 className="cl-plate-title">{ask ? (ask.direction === "from_phone" ? "Reply" : "Waits on you") : "Message your phone"}</h3>
          {device ? <span className="cl-plate-facts">Goes to {device.name}</span> : null}
        </header>
        {ask ? <p className="cl-plate-words">{ask.text}</p> : null}
        <ComposerWell
          className="phone-compose"
          data-testid="phone-composer"
          details={replyLine ? (
            <span className="phone-replying" data-testid="phone-replying">
              Reply to: <b>{replyLine.text}</b>
              <Button variant="ghost" dense onClick={() => { setReplying(null); clearReply(); }}>Cancel</Button>
            </span>
          ) : undefined}
          actions={
            <Button variant="primary" dense loading={busy === "send"} disabled={!draft.trim() || !reachable} onClick={send}
              data-testid="phone-send">{replyLine ? "Reply" : "Send"}</Button>
          }
        >
          <PadGadget
            label="Message your phone"
            placeholder="Message your phone"
            value={draft}
            onChange={setDraft}
            rows={2}
            micLabel="Speak a message to your phone"
            autoGrow
            inputRef={composer}
            onKeyDown={(event) => { if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) send(); }}
          />
        </ComposerWell>
        {refusal ? <p className="cl-plate-refusal" title={refusal.title} data-testid="phone-refusal">{refusal.words}</p> : null}
      </section>
      <div className="cl-ledger" role="group" aria-label="Messages and calls">
        {rows.length ? (
          <ol className="phone-lines" aria-label="Messages and calls" data-testid="phone-thread">{rows}</ol>
        ) : (
          <SurfaceState empty emptyKind="call" emptyImage={spriteUrl("call", "calls")}
            emptyLabel="No messages yet" emptyHint="When the desk needs you away from it, it messages your phone here." />
        )}
      </div>
    </article>
  );
}

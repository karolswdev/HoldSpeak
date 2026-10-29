/* Phone (PHONE-DESIGN-2026-10-28 §9; canvas
 * docs/internal/betterment/phone/canvases/phone-2026-10-28.html, direction
 * A): the Phone wing of the Calls window.
 *
 * Window grammar: Toolbar (Message, the verb that makes the object; Call
 * me) → the thread edge to edge (the Live transcript's grammar: time · who
 * · words; a reply under the line it answers with the elbow rule; a line
 * the desk waits on in the ember rule; a desk call as one line with its
 * state and one verb) with the mic composer at its foot, and a rail (From
 * the desk, Your phone) → a 24 px StatusBar with a dot and a word. No host,
 * number or engine chip (UX-CANON A.9): egress is said in Settings ▸ Calls
 * ▸ Phone. In a narrow window the rail folds away. */
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { spriteUrl } from "../sprites";
import { ComposerWell } from "../surface/ComposerWell";
import { PadGadget } from "../surface/gadgets";
import { DotWord, StatusBar, Toolbar, countWords, type StatusBarItem } from "../surface/kit";
import type { ObjectTone } from "../surface/objects/kinds";
import { SurfaceState } from "../surface/Surface";
import { stateWords } from "../surface/words";
import { plainFail } from "../surface/plainFailure";
import { canReach, markPhoneMessageRead, pairedPhone, phoneCallVerb, sendPhoneMessage, waitsForReply, type usePhone } from "./phoneApi";
import type { PhoneCall, PhoneDevice, PhoneMessage } from "./phoneTypes";
import { openPhoneWing, usePhoneFocus } from "./phoneFocus";
import "./phone.css";

export { openPhoneWing, usePhoneFocus };

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

function DeviceRow({ device }: { device: PhoneDevice | null }) {
  if (!device) {
    return (
      <div className="phone-device" data-testid="phone-device-none">
        <span className="phone-handset" aria-hidden="true"><i /></span>
        <span className="phone-device-words"><span className="phone-device-name">No phone paired</span></span>
        <Button variant="secondary" dense onClick={openPhoneSettings} data-testid="phone-pair-open">Pair a phone</Button>
      </div>
    );
  }
  return (
    <div className="phone-device" data-testid="phone-device">
      <span className="phone-handset" aria-hidden="true"><i /></span>
      <span className="phone-device-words">
        <span className="phone-device-name">{device.name}</span>
        <span className="phone-device-fact">{deviceFact(device)}</span>
      </span>
      <DotWord tone="ok">{stateWords("PAIRED")}</DotWord>
    </div>
  );
}

/** A call's transcript: a Calls call (`call:<id>`) opens in the Calls
 *  wing; another ref opens as its object. */
export function transcriptOf(call: PhoneCall): { callsId?: string; ref?: string } | null {
  const ref = String(call.transcript_ref ?? "");
  if (!ref) return null;
  return ref.startsWith("call:") ? { callsId: ref.slice("call:".length) } : { ref };
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

export function openPhoneSettings(): void {
  openSurfaceOr("configure-settings", "/settings", "calls");
}

export function PhoneWing({ phone, canCall, calling, onCallMe, onOpenCall, wings }: {
  phone: ReturnType<typeof usePhone>;
  /** Call me is ready (the Calls checklist is done). */
  canCall: boolean;
  calling: boolean;
  onCallMe(): void;
  /** Open a Calls call (a desk call on the number transport) as a document. */
  onOpenCall(callsId: string): void;
  wings?: ReactNode;
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

  let body: ReactNode;
  if (phone.loading || phone.error) {
    body = <SurfaceState loading={phone.loading} error={phone.error} onRetry={() => void phone.reload()} />;
  } else if (!reachable && !entries.length) {
    body = (
      <SurfaceState
        empty
        emptyKind="call"
        emptyImage={spriteUrl("call", "calls")}
        emptyLabel="No phone yet"
        emptyHint="Pair a phone, or add a number in Calls, and the desk can reach you."
        actionLabel="Pair a phone"
        onAction={openPhoneSettings}
      />
    );
  } else {
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
    const deskCalls = phone.calls.filter((call) => call.direction === "to_phone");
    body = (
      <div className="phone-wing" data-testid="phone-wing">
        <div className="phone-thread">
          {rows.length ? (
            <ol className="phone-lines" aria-label="Messages and calls" data-testid="phone-thread">{rows}</ol>
          ) : (
            <SurfaceState empty emptyKind="call" emptyImage={spriteUrl("call", "calls")}
              emptyLabel="No messages yet" emptyHint="When the desk needs you away from it, it messages your phone here." />
          )}
          <ComposerWell
            className="phone-compose"
            data-testid="phone-composer"
            details={replyLine ? (
              <span className="phone-replying" data-testid="phone-replying">
                Reply to: <b>{replyLine.text}</b>
                <Button variant="ghost" dense onClick={() => { setReplying(null); clearReply(); }}>Cancel</Button>
              </span>
            ) : undefined}
            context={device ? <span className="phone-compose-to">Goes to {device.name}</span> : null}
            actions={
              <Button variant="primary" dense loading={busy === "send"} disabled={!draft.trim() || !reachable} onClick={send}
                data-testid="phone-send">Send</Button>
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
        </div>
        <aside className="phone-rail" aria-label="From the desk">
          {deskCalls.length ? (
            <>
              <h3 className="phone-rail-cap">From the desk</h3>
              <ul className="phone-rail-list">
                {[...deskCalls].reverse().map((call) => {
                  const state = callStateWords(call);
                  return (
                    <li key={call.id}>
                      <Button variant="chrome" className="phone-rail-row" data-testid="phone-rail-call"
                        disabled={!transcriptOf(call)} onClick={() => openTranscript(call)}>
                        <span className="phone-rail-name">{call.reason}</span>
                        <DotWord tone={state.tone}>{state.word.split(" · ")[0]}</DotWord>
                        <span className="phone-rail-fact">{`Call · ${dayWords(call.created_at)} ${clock(call.created_at)}${call.urgent ? " · urgent" : ""}`}</span>
                      </Button>
                    </li>
                  );
                })}
              </ul>
            </>
          ) : null}
          <h3 className="phone-rail-cap">Your phone</h3>
          <DeviceRow device={device} />
        </aside>
      </div>
    );
  }

  const status: Array<StatusBarItem | null> = refusal ? [
    { key: "refusal", lamp: "warn", text: <span title={refusal.title}>{refusal.words}</span>, testId: "phone-refusal" },
  ] : phone.status == null ? [
    { key: "none", text: <span className="calls-idle-word"><span className="kit-dot" data-tone="idle" aria-hidden="true" />No phone paired</span> },
  ] : [
    waiting.length
      ? { key: "waits", lamp: "ask", text: waiting.length === 1 ? "A reply is waiting on you" : `${waiting.length} replies are waiting on you`, testId: "phone-status-waits" }
      : device ? { key: "paired", lamp: "ok", text: "Your phone is paired", testId: "phone-status-paired" }
        : phone.status.line?.ready ? { key: "number", lamp: "ok", text: "Reaches you by number", testId: "phone-status-number" }
          : { key: "none", text: <span className="calls-idle-word"><span className="kit-dot" data-tone="idle" aria-hidden="true" />No phone paired</span>, testId: "phone-status-none" },
    { key: "calls", text: countWords(phone.calls.filter((call) => call.direction === "to_phone").length, "call from the desk", "calls from the desk") },
  ];

  return (
    <div className="calls-window phone-window" data-testid="calls-window" data-state="phone">
      {wings}
      <Toolbar label="Phone" data-testid="phone-toolbar">
        <Button variant="primary" dense disabled={!reachable} onClick={() => composer.current?.focus()}
          title={reachable ? "Write to your phone" : "Pair a phone in Settings ▸ Calls ▸ Phone"} data-testid="phone-message-verb">
          Message
        </Button>
        <Button variant="secondary" dense loading={calling} disabled={!canCall} onClick={onCallMe}
          title={canCall ? "HoldSpeak rings your number" : "Set up calls in Settings ▸ Calls"} data-testid="phone-call-me">
          Call me
        </Button>
      </Toolbar>
      <div className="calls-body" data-phase="phone">{body}</div>
      <StatusBar data-testid="calls-status" items={status} />
    </div>
  );
}

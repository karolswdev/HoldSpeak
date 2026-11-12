import { stateWords } from "../surface/words";
import { plainFail } from "../surface/plainFailure";
import {
  useEffect,
  useMemo,
  useState,
  type Dispatch,
  type SetStateAction,
} from "react";
import { openRef } from "../openObject";
import {
  ActionNotice,
  InspectorBody,
  InspectorFacts,
  InspectorForm,
  ListPane,
  ListView,
  PaneInspector,
  PadGadget,
  SurfaceState,
  countWords,
  type ListVerb,
  type StatusBarItem,
} from "../surface";
import type { ObjectTone } from "../surface/objects/kinds";
import {
  canReach,
  markPhoneMessageRead,
  pairedPhone,
  phoneCallVerb,
  sendPhoneMessage,
  waitsForReply,
  type usePhone,
} from "./phoneApi";
import type { PhoneCall, PhoneDevice, PhoneMessage } from "./phoneTypes";
import { usePhoneFocus } from "./phoneFocus";

function at(value: string | null | undefined): number {
  const ms = value ? Date.parse(value) : NaN;
  return Number.isFinite(ms) ? ms : NaN;
}

export function clock(value: string | null | undefined): string {
  const ms = at(value);
  if (!Number.isFinite(ms)) return "";
  return new Date(ms).toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

/** The day caption of a thread band: Today, Yesterday, `Mon 26 Oct`. */
export function dayWords(value: string, now = new Date()): string {
  const date = new Date(at(value));
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (date.toDateString() === now.toDateString()) return "Today";
  if (date.toDateString() === yesterday.toDateString()) return "Yesterday";
  return date.toLocaleDateString("en-GB", {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
}

function minutes(fromMs: number, toMs: number): string {
  const seconds = Math.max(0, Math.round((toMs - fromMs) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

/** A desk line's receipt (§4: sent → delivered → read). */
export function receiptWords(message: PhoneMessage): {
  word: string;
  tone: ObjectTone | "idle";
} {
  if (message.read_at) return { word: stateWords("READ"), tone: "ok" };
  if (message.delivered_at)
    return { word: stateWords("DELIVERED"), tone: "idle" };
  return { word: stateWords("SENT"), tone: "idle" };
}

/** A call's state in a dot and a word (§4). */
export function callStateWords(call: PhoneCall): {
  word: string;
  tone: ObjectTone | "idle";
  live?: boolean;
} {
  const urgent = call.urgent ? " · urgent" : "";
  switch (call.state) {
    case "held":
      return { word: "Waits for your yes", tone: "ask" };
    case "ringing":
      return { word: "Ringing", tone: "info", live: true };
    case "answered":
      return { word: "On the call", tone: "fail", live: true };
    case "missed":
      return { word: `Missed${urgent}`, tone: "fail" };
    case "declined":
      return { word: `Declined${urgent}`, tone: "warn" };
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
  | {
      kind: "message";
      at: number;
      message: PhoneMessage;
      reply: boolean;
      waits: boolean;
    }
  | { kind: "call"; at: number; call: PhoneCall };

/** The thread in reading order: roots by time, each reply under the line
 *  it answers (and the replies to that reply after it). */
export function threadEntries(
  messages: readonly PhoneMessage[],
  calls: readonly PhoneCall[],
): Entry[] {
  const ids = new Set(messages.map((message) => message.id));
  const children = new Map<string, PhoneMessage[]>();
  const roots: Entry[] = [];
  for (const message of messages) {
    if (message.reply_to && ids.has(message.reply_to)) {
      const list = children.get(message.reply_to) ?? [];
      list.push(message);
      children.set(message.reply_to, list);
    } else {
      roots.push({
        kind: "message",
        at: at(message.created_at) || 0,
        message,
        reply: false,
        waits: waitsForReply(message, messages),
      });
    }
  }
  for (const call of calls)
    roots.push({ kind: "call", at: at(call.created_at) || 0, call });
  roots.sort((a, b) => a.at - b.at);
  const out: Entry[] = [];
  const walk = (id: string) => {
    for (const child of (children.get(id) ?? []).sort(
      (a, b) => a.seq - b.seq,
    )) {
      out.push({
        kind: "message",
        at: at(child.created_at) || 0,
        message: child,
        reply: true,
        waits: waitsForReply(child, messages),
      });
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
export function originOf(
  ref: string | null | undefined,
): { words: string; open?: string } | null {
  const text = String(ref ?? "");
  if (!text) return null;
  const [kind, id] = text.split(":");
  if (kind === "program" && id)
    return { words: "a program", open: `program:${id}` };
  if (kind === "program_step") return { words: "a program step" };
  if (kind === "agent") return { words: "an agent" };
  if (kind === "phone_call") return { words: "a missed call" };
  if (kind === "heartbeat") return { words: "the heartbeat" };
  return null;
}

/** A call's transcript: a Calls call (`call:<id>`) opens in the Calls
 *  wing; another ref opens as its object. */
export function transcriptOf(
  call: PhoneCall,
): { callsId?: string; ref?: string } | null {
  const ref = String(call.transcript_ref ?? "");
  if (!ref) return null;
  return ref.startsWith("call:")
    ? { callsId: ref.slice("call:".length) }
    : { ref };
}

/** The push word of a paired phone (`push_state`, RECIPE PH13): null when
 *  a push will go (or the hub did not say), else "Push not ready" and why. */
const PUSH_REASONS: Record<string, string> = {
  no_key: "no Apple push key on the hub",
  http2_unavailable: "the hub has no HTTP/2",
  unregistered: "the phone sent no push token",
};

export function pushNotReady(device: PhoneDevice): string | null {
  const reason = device.push_state
    ? PUSH_REASONS[device.push_state]
    : undefined;
  return reason ? `Push not ready: ${reason}` : null;
}

/** `Paired 21 Oct · seen 2 min ago`. */
export function deviceFact(device: PhoneDevice, now = Date.now()): string {
  const paired = at(device.paired_at);
  const seen = at(device.last_seen_at);
  const parts: string[] = [];
  if (Number.isFinite(paired))
    parts.push(
      `Paired ${new Date(paired).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}`,
    );
  if (Number.isFinite(seen)) {
    const mins = Math.max(0, Math.round((now - seen) / 60_000));
    parts.push(
      mins < 1
        ? "seen now"
        : mins < 60
          ? `seen ${mins} min ago`
          : `seen ${clock(device.last_seen_at)}`,
    );
  }
  return parts.join(" · ");
}

/** The status bar of the phone's pane: what waits on him, the calls from the desk. */
export function phoneStatusItems(
  phone: ReturnType<typeof usePhone>,
): Array<StatusBarItem | null> {
  const device = pairedPhone(phone.status);
  const waiting = phone.messages.filter((message) =>
    waitsForReply(message, phone.messages),
  );
  const none = "No phone paired";
  if (phone.status == null) return [{ key: "none", text: none }];
  return [
    waiting.length
      ? {
          key: "waits",
          lamp: "ask",
          text:
            waiting.length === 1
              ? "A reply is waiting on you"
              : `${waiting.length} replies are waiting on you`,
          testId: "phone-status-waits",
        }
      : device
        ? {
            key: "paired",
            lamp: "ok",
            text: "Your phone is paired",
            testId: "phone-status-paired",
          }
        : phone.status.line?.ready
          ? {
              key: "number",
              lamp: "ok",
              text: "Reaches you by number",
              testId: "phone-status-number",
            }
          : { key: "none", text: none, testId: "phone-status-none" },
    {
      key: "calls",
      text: countWords(
        phone.calls.filter((call) => call.direction === "to_phone").length,
        "call from the desk",
        "calls from the desk",
      ),
    },
  ];
}

export type PhoneFailure = { words: string; title: string } | null;

export function PhonePane({
  phone,
  onOpenCall,
  onPair,
  draft,
  setDraft,
  replying,
  setReplying,
  busy,
  setBusy,
  refusal,
  setRefusal,
}: {
  phone: ReturnType<typeof usePhone>;
  onOpenCall(id: string): void;
  onPair(): void;
  draft: string;
  setDraft: Dispatch<SetStateAction<string>>;
  replying: string | null;
  setReplying: Dispatch<SetStateAction<string | null>>;
  busy: string;
  setBusy: Dispatch<SetStateAction<string>>;
  refusal: PhoneFailure;
  setRefusal: Dispatch<SetStateAction<PhoneFailure>>;
}) {
  const replyTo = usePhoneFocus((st) => st.replyTo);
  const clearReply = usePhoneFocus((st) => st.clear);
  const [picked, setPicked] = useState<string | null>(null);
  const [composing, setComposing] = useState(Boolean(replying || draft));
  useEffect(() => {
    if (replyTo) {
      setComposing(true);
      setReplying(replyTo);
      setPicked(replyTo);
    }
  }, [replyTo]);
  const device = pairedPhone(phone.status),
    reachable = canReach(phone.status);
  const entries = useMemo(
    () => threadEntries(phone.messages, phone.calls),
    [phone.messages, phone.calls],
  );
  const selected = entries.find(
    (entry) =>
      (entry.kind === "message" ? entry.message.id : entry.call.id) === picked,
  );
  const replyLine = phone.messages.find((message) => message.id === replying);
  const unread = phone.messages
    .filter((message) => message.direction === "from_phone" && !message.read_at)
    .map((message) => message.id)
    .join(",");
  useEffect(() => {
    for (const id of unread.split(",").filter(Boolean))
      void markPhoneMessageRead(id).catch(() => undefined);
  }, [unread]);
  const run = async (kind: string, action: () => Promise<void>) => {
    if (busy) return;
    setBusy(kind);
    setRefusal(null);
    try {
      await action();
    } catch (cause) {
      setRefusal(
        plainFail(
          kind === "send"
            ? "The message did not reach your phone"
            : "The call did not start",
          cause,
          kind === "send" ? "Your words are kept" : "Nothing rang",
          "Try again",
        ),
      );
    } finally {
      setBusy("");
    }
  };
  const send = () => {
    const sentDraft = draft,
      text = sentDraft.trim(),
      reply = replying;
    if (!text || !reachable || busy) return;
    void run("send", async () => {
      await sendPhoneMessage(text, reply);
      setDraft((current) => (current === sentDraft ? "" : current));
      setReplying((current) => (current === reply ? null : current));
      clearReply();
      await phone.catchUp();
    });
  };
  const call = selected?.kind === "call" ? selected.call : null;
  const message = selected?.kind === "message" ? selected.message : null;
  const origin = message ? originOf(message.origin_ref) : null;
  const callVerb = (verb: "again" | "ring") => {
    if (call)
      void run(`call-${call.id}`, async () => {
        await phoneCallVerb(call.id, verb);
        await phone.reload();
      });
  };
  const verbs: ListVerb[] = [
    {
      id: "new-message",
      label: "New message",
      testId: "phone-new-message",
      enabled: () => reachable,
      run: () => setComposing(true),
    },
    {
      id: "reply",
      label: "Reply",
      testId: "phone-reply",
      enabled: () => message?.direction === "from_phone",
      run: () => {
        setReplying(message!.id);
        setComposing(true);
      },
    },
    {
      id: "again",
      label: "Call again",
      testId: "phone-call-again",
      dispatching: Boolean(call && busy === `call-${call.id}`),
      enabled: () =>
        Boolean(call && ["missed", "declined"].includes(call.state) && !busy),
      run: () => callVerb("again"),
    },
    {
      id: "ring",
      label: "Call now",
      testId: "phone-call-ring",
      dispatching: Boolean(call && busy === `call-${call.id}`),
      enabled: () => call?.state === "held" && !busy,
      run: () => callVerb("ring"),
    },
    {
      id: "transcript",
      label: "Open transcript",
      testId: "phone-open-transcript",
      enabled: () => Boolean(call && transcriptOf(call)),
      run: () => {
        const where = call && transcriptOf(call);
        if (where?.callsId) onOpenCall(where.callsId);
        else if (where?.ref) openRef(where.ref);
      },
    },
    {
      id: "source",
      label: "Open source",
      enabled: () => Boolean(origin?.open),
      run: () => {
        if (origin?.open) openRef(origin.open);
      },
    },
  ];
  if (phone.loading || phone.error)
    return (
      <SurfaceState
        loading={phone.loading}
        error={phone.error}
        onRetry={() => void phone.reload()}
      />
    );
  if (!reachable && !entries.length)
    return (
      <SurfaceState
        empty
        emptyLabel="No phone yet"
        actionLabel="Pair a phone"
        onAction={onPair}
      />
    );
  const push = device ? pushNotReady(device) : null;
  return (
    <PaneInspector
      label={device?.name ?? "Your phone"}
      subtitle={device ? deviceFact(device) : "Reaches you by number"}
      testId="phone-wing"
    >
      <InspectorBody>
        {push ? <ActionNotice tone="warn">{push}</ActionNotice> : null}
        {composing ? (
          <InspectorForm
            fit="rows"
            testId="phone-composer"
            rows={[
              { label: "To", control: device?.name ?? "Your phone number" },
              ...(replyLine
                ? [
                    {
                      label: "Reply to",
                      control: (
                        <span
                          data-feedback-redact="true"
                          data-testid="phone-replying"
                        >
                          {replyLine.text}
                        </span>
                      ),
                    },
                  ]
                : []),
              {
                label: "Message",
                control: (
                  <PadGadget
                    autoFocus
                    label="Message your phone"
                    value={draft}
                    onChange={setDraft}
                    rows={2}
                    micLabel="Speak a message to your phone"
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter" &&
                        (event.metaKey || event.ctrlKey)
                      )
                        send();
                    }}
                  />
                ),
              },
            ]}
            notice={
              refusal ? (
                <ActionNotice tone="danger" role="alert">
                  <span data-testid="phone-refusal">{refusal.words}</span>
                </ActionNotice>
              ) : null
            }
            completion={{
              cancel: () => {
                setComposing(false);
                setReplying(null);
                clearReply();
              },
              primary: {
                label: replyLine ? "Reply" : "Send",
                run: send,
                busy: busy === "send",
                disabled: !draft.trim() || !reachable,
                testId: "phone-send",
              },
            }}
          />
        ) : (
          <ListPane
            label="Messages and calls"
            list={
              <ListView
                label="Messages and calls"
                ordered
                headerless
                rows={entries.map((entry) => {
                  if (entry.kind === "call") {
                    const call = entry.call,
                      state = callStateWords(call);
                    return {
                      id: call.id,
                      kind: "call",
                      name: call.reason,
                      detail: `${callLead(call)} · ${dayWords(call.created_at)} ${clock(call.created_at)} · ${state.word}`,
                      state: { label: state.word, tone: state.tone },
                    };
                  }
                  const message = entry.message,
                    receipt = receiptWords(message);
                  return {
                    id: message.id,
                    kind: "note",
                    name: message.text,
                    detail: `${entry.reply ? "Reply · " : ""}${message.direction === "from_phone" ? "You" : "HoldSpeak"} · ${dayWords(message.created_at)} ${clock(message.created_at)} · ${entry.waits ? "Waits on you" : receipt.word}`,
                    state: {
                      label: entry.waits
                        ? "Waits on you"
                        : message.direction === "to_phone"
                          ? receipt.word
                          : "Read",
                      tone: entry.waits ? ("ask" as const) : receipt.tone,
                    },
                  };
                })}
                selectedId={picked}
                onSelect={setPicked}
                verbs={verbs}
                defaultVerb="reply"
                columns={[{ key: "name", word: "Message or call" }]}
                rowProps={(row) => ({
                  "data-testid": phone.messages.some(
                    (message) => message.id === row.id,
                  )
                    ? "phone-message"
                    : "phone-call",
                  "data-message": row.id,
                  "data-call": row.id,
                  "data-feedback-redact": "true",
                })}
              />
            }
          >
            {selected ? (
              <InspectorFacts
                header={false}
                name="Selected line"
                data-feedback-redact="true"
                rows={[
                  { label: "Words", value: message?.text ?? call?.reason },
                  {
                    label: "At",
                    value: message
                      ? `${dayWords(message.created_at)} ${clock(message.created_at)}`
                      : call
                        ? `${dayWords(call.created_at)} ${clock(call.created_at)}`
                        : null,
                  },
                  {
                    label: "Receipt",
                    value:
                      message?.direction === "to_phone"
                        ? receiptWords(message).word
                        : null,
                  },
                  {
                    label: "From",
                    value:
                      origin?.words ??
                      (message?.direction === "from_phone"
                        ? "Your phone"
                        : null),
                  },
                ]}
              />
            ) : null}
          </ListPane>
        )}
      </InspectorBody>
    </PaneInspector>
  );
}

/* Calls, the native app (the language, 2026-11-08; Agents and Meetings are
 * the pattern). Go ▸ Work ▸ Calls.
 *
 * The rail at the left: the call on the line first (its spine steel; brass
 * when it holds a question for him), then the recent calls by time, then the
 * paired phone as one row with its state. The picked thing at the right:
 * the MAST (the person sprite when the caller is him, else the call sprite;
 * who; when, how long, the line and the engine on a live call), its spine,
 * the raised PLATE (the one thing now: a held question with Yes and No and
 * Hang up; a live call with Hang up; an ended call with Call me; nothing
 * picked: Place a call), then the LEDGER (the call's turns, then what it
 * did). The phone's pane is PhonePane. The Line and the Phone settings are
 * two folds at the window's foot. One status bar: a dot and a word. No host
 * or number chip (UX-CANON A.9). A narrow window shows the rail or the
 * picked thing, never both. A `call_state` frame replaces the call it names. */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { LiveTranscript } from "../../pages/cores/LiveTranscript";
import "../../pages/cores/liveTranscript.css";
import type { CoreProps } from "../../pages/cores/core-types";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { listSprite, spriteUrl } from "../sprites";
import {
  FoldGadget, Mast, Rail, Spine, StatusBar, SurfaceState, ToolGlyph, countWords, useWindowInterior,
  type RailItem, type SpineTone, type StatusBarItem, type ToolGlyphKind,
} from "../surface";
import { decide, hangUp, lineInUse, placeCall, readCall, refusalWords, useCalls, withTranscript, writeCallsSetting } from "./api";
import { LineSettingsPane } from "./LineSettings";
import { pairedPhone, usePhone, waitsForReply } from "./phoneApi";
import { PhonePane, phoneStatusItems, pushNotReady } from "./PhonePane";
import { PhoneSettingsPane } from "./PhoneSettings";
import { usePhoneFocus } from "./phoneFocus";
import type { Call, CallResult, CallSummary, CallsSettings, CallsStatus } from "./types";
import "./calls.css";
import { ShowMe } from "../walk/ShowMe";

/** Seconds → `m:ss` (`h:mm:ss` past the hour). */
export function clockWords(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  const h = Math.floor(whole / 3600);
  const m = Math.floor((whole % 3600) / 60);
  const s = String(whole % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}

function at(value: string | null | undefined): number {
  const ms = value ? Date.parse(value) : NaN;
  return Number.isFinite(ms) ? ms : NaN;
}

/** When a call was, in words: `Today 18:40`, `Yesterday 18:40`, `Mon 08:05`,
 *  `Oct 3 08:05`. */
export function callWhen(value: string | null | undefined, now = new Date()): string {
  const ms = at(value);
  if (!Number.isFinite(ms)) return "";
  const date = new Date(ms);
  const clock = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
  const day = (d: Date) => d.toDateString();
  const yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  if (day(date) === day(now)) return `Today ${clock}`;
  if (day(date) === day(yesterday)) return `Yesterday ${clock}`;
  if (now.getTime() - ms < 6 * 86_400_000 && now.getTime() > ms) {
    return `${date.toLocaleDateString("en-US", { weekday: "short" })} ${clock}`;
  }
  return `${date.toLocaleDateString("en-US", { month: "short", day: "numeric" })} ${clock}`;
}

type Tone = "ok" | "idle" | "warn" | "fail" | "info" | "ask";

const OUTCOMES: Record<string, { word: string; tone: Tone }> = {
  done: { word: "Done", tone: "ok" },
  no_answer: { word: "No answer", tone: "idle" },
  rejected: { word: "Refused", tone: "warn" },
  busy: { word: "Busy", tone: "warn" },
  failed: { word: "Failed", tone: "fail" },
  denied: { word: "Not let in", tone: "warn" },
};

export function outcomeOf(call: CallSummary): { word: string; tone: Tone } {
  if (call.state !== "ended") return call.hold ? { word: "Waits for you", tone: "ask" } : { word: "On the line", tone: "info" };
  const known = OUTCOMES[String(call.outcome ?? "")];
  if (known) return known;
  const raw = String(call.outcome ?? "").replace(/_/g, " ").trim();
  return { word: raw ? raw[0].toUpperCase() + raw.slice(1) : "Ended", tone: "idle" };
}

/** One colour per meaning (steel on the line, brass waits on him, moss done,
 *  coral at risk, idle nothing came of it). */
const SPINE: Record<Tone, SpineTone> = { info: "steel", ask: "brass", ok: "moss", warn: "coral", fail: "coral", idle: "idle" };

function digits(value: string): string {
  return value.replace(/^sip:/i, "").split("@", 1)[0].replace(/[^\d+]/g, "");
}

function masked(number: string): string {
  return number.length > 4 ? `${number.startsWith("+") ? number.slice(0, 2) : ""} ··· ${number.slice(-4)}`.trim() : number;
}

/** Who was on the other end: `You` for his own number, else the number with
 *  its middle hidden (`+1 ··· 0142`). */
export function remoteWords(remote: string, mine: readonly string[]): string {
  const number = digits(remote);
  if (number && mine.some((own) => digits(own) === number)) return "You";
  return masked(number) || "Unknown";
}

const EFFECT_WORDS: Record<CallResult["effect"], string> = {
  wrote: "Wrote",
  prepared: "Prepared",
  sent: "Sent on your yes",
  started: "Started on your yes",
  changed: "Changed on your yes",
};

/** A result's kind mark: the toolbar glyph of its kind (kit ToolGlyph). */
const KIND_MARK: Record<string, ToolGlyphKind> = { note: "note", action: "done", task: "done", send: "send", decision: "summary", project: "project", program: "run" };

function ResultRow({ kind, label, word, onOpen, testId }: {
  kind: string; label: string; word: string; onOpen?: () => void; testId?: string;
}) {
  return (
    <Button variant="chrome" className="calls-result" data-kind={kind} onClick={onOpen} disabled={!onOpen} data-testid={testId}>
      <span className="calls-result-mark" aria-hidden="true"><ToolGlyph kind={KIND_MARK[kind] ?? "open"} /></span>
      <span className="calls-result-label">{label}</span>
      <span className="calls-result-word">{word}</span>
    </Button>
  );
}

function noteWhen(call: CallSummary): string {
  const ms = at(call.started_at);
  if (!Number.isFinite(ms)) return "Call";
  const date = new Date(ms);
  const day = date.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  const clock = date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `Call · ${day} ${clock}`;
}

/** DELIGHT slice 4 (2026-10-28): the held question's answer settles out,
 *  the Needs-you Done settle (180 ms, a wash that fades, opacity and colour
 *  only): green for Yes, the quiet rule for No. None under reduced motion
 *  (or with no media query). */
export const SETTLE_MS = 180;
function motionAllowed(): boolean {
  return Boolean(window.matchMedia?.("(prefers-reduced-motion: no-preference)")?.matches);
}

/** The live clock of a call: seconds since it was answered. */
function useCallClock(call: Call | null): number | null {
  const [now, setNow] = useState(() => Date.now());
  const start = call ? (at(call.answered_at) || at(call.started_at)) : NaN;
  useEffect(() => {
    if (!call || !Number.isFinite(start)) return;
    setNow(Date.now());
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [call?.id, start]);
  return call && Number.isFinite(start) ? Math.max(0, (now - start) / 1000) : null;
}

/** Ready for calls: Calls on and the phone running (the Line ready, or
 *  the ai-phone daemon running). */
export function callsReady(settings: CallsSettings | null, status: CallsStatus): boolean {
  const phone = lineInUse(status) ? status.line?.state === "ready" : status.aiphone.state === "running";
  return Boolean(settings?.enabled && status.enabled && phone);
}

/** The status bar's word for the Line (LINE canvas, the Calls bar): no
 *  machine is named here (A.9). */
export function lineBarItem(status: CallsStatus): StatusBarItem {
  const state = status.line?.state;
  if (state === "ready") return { key: "ready", lamp: "ok", text: "Ready for calls", testId: "calls-status-ready" };
  if (state === "starting") return { key: "line", lamp: "info", live: true, text: "Line starting", testId: "calls-status-line" };
  if (state === "not_running" || state === "offline") return { key: "line", lamp: "warn", text: "Line not running", testId: "calls-status-line" };
  return {
    key: "line",
    testId: "calls-status-line",
    text: (
      <span className="calls-idle-word">
        <span className="kit-dot" data-tone="idle" aria-hidden="true" />
        No line: set one in Settings ▸ Calls ▸ Line
      </span>
    ),
  };
}

function openCallsSettings() {
  openSurfaceOr("configure-settings", "/settings", "calls");
}

/* ── the rail ─────────────────────────────────────────────────────────── */

function callTitle(call: CallSummary): string {
  if (call.first_words) return `“${call.first_words}”`;
  if (call.state !== "ended") return "On the line";
  return call.direction === "out" ? "HoldSpeak called you" : "No words";
}

function callItem(call: CallSummary, mine: readonly string[]): RailItem {
  const outcome = outcomeOf(call);
  return {
    id: call.id, label: callTitle(call),
    glyph: <img src={listSprite(spriteUrl("call", "calls"))} alt="" draggable={false} />,
    state: <span data-tone={SPINE[outcome.tone]} data-testid="calls-outcome">{outcome.word}</span>,
    facts: [remoteWords(call.remote, mine), callWhen(call.started_at), call.duration_sec && call.duration_sec > 0 ? clockWords(call.duration_sec) : ""].filter(Boolean).join(" · "),
    spine: { tone: SPINE[outcome.tone] },
    data: { "data-testid": "calls-row", "data-call": call.id, "data-kind": "call", "data-state": call.state },
  };
}

function phoneItem(phone: ReturnType<typeof usePhone>, on: boolean): RailItem {
  const device = pairedPhone(phone.status);
  const waits = phone.messages.filter((message) => waitsForReply(message, phone.messages)).length
    + phone.calls.filter((call) => call.state === "held").length;
  const push = device ? pushNotReady(device) : null;
  const state: { word: string; tone: Tone } = !on ? { word: "Off", tone: "idle" }
    : waits ? { word: waits === 1 ? "Waits on you" : `${waits} wait on you`, tone: "ask" }
      : device ? (push ? { word: "Push not ready", tone: "warn" } : { word: "Paired", tone: "ok" })
        : phone.status?.line?.ready ? { word: "By number", tone: "ok" } : { word: "Not paired", tone: "idle" };
  return { id: "phone", label: device?.name ?? "Your phone", glyph: <img src={spriteUrl("call", "phone")} alt="" draggable={false} />,
    state: state.word, spine: { tone: SPINE[state.tone] }, data: { "data-testid": "calls-rail-phone" } };
}

/* ── the plate ────────────────────────────────────────────────────────── */

export function Plate({ tone, head, facts, children, testId, settle }: {
  tone: SpineTone; head: ReactNode; facts?: ReactNode; children?: ReactNode; testId?: string; settle?: string;
}) {
  return (
    <section className="cl-plate" data-tone={tone} data-testid={testId} data-settle={settle || undefined}>
      <header className="cl-plate-head">
        <h3 className="cl-plate-title">{head}</h3>
        {facts ? <span className="cl-plate-facts">{facts}</span> : null}
      </header>
      {children}
    </section>
  );
}

/** The handset glyph of Call me and Hang up (16 px, the toolbar pen). */
function CallGlyph({ down = false }: { down?: boolean }) {
  return (
    <svg className="kit-toolglyph calls-glyph" data-down={down || undefined} width={16} height={16} viewBox="0 0 16 16"
      fill="none" stroke="currentColor" strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" focusable="false">
      <path d="M5.2 2.75 3.4 3.6c-.6.3-.9 1-.7 1.6 1.3 3.8 4.2 6.8 8.1 8.1.6.2 1.3-.1 1.6-.7l.85-1.8-2.6-1.5-1.2 1.1c-1.5-.7-2.7-1.9-3.4-3.4l1.1-1.2Z" />
    </svg>
  );
}

function CallMe({ canCall, busy, onCall }: { canCall: boolean; busy: boolean; onCall(): void }) {
  return (
    <Button variant="primary" dense loading={busy} disabled={!canCall} onClick={onCall}
      title={canCall ? "HoldSpeak rings your number" : "Set up calls in Settings ▸ Calls"} data-testid="calls-call-me">
      <CallGlyph />
      Call me
    </Button>
  );
}

/* ── the call ─────────────────────────────────────────────────────────── */

function CallPane({ call, live, clock, mine, status, busy, settle, canCall, onCall, onHangUp, onDecide, onBack }: {
  call: Call; live: boolean; clock: number | null; mine: readonly string[]; status: CallsStatus;
  busy: string; settle: "" | "yes" | "no"; canCall: boolean;
  onCall(): void; onHangUp(): void; onDecide(decision: "approve" | "deny"): void; onBack(): void;
}) {
  const who = remoteWords(call.remote, mine);
  const outcome = outcomeOf(call);
  const tone = SPINE[outcome.tone];
  const length = live ? (clock != null ? clockWords(clock) : "") : call.duration_sec ? clockWords(call.duration_sec) : "";
  // The line and the engine are known for the call on the line only.
  const facts = [callWhen(call.started_at), length,
    live ? (lineInUse(status) ? "the Line" : "ai-phone") : "", live ? status.engine.model ?? "" : ""].filter(Boolean).join(" · ");
  const start = at(call.answered_at) || at(call.started_at);
  const segments = useMemo(() => call.transcript.map((line, index) => {
    const when = at(line.at);
    return {
      id: `${call.id}-${index}`,
      start_time: Number.isFinite(when) && Number.isFinite(start) ? Math.max(0, (when - start) / 1000) : undefined,
      speaker: line.who === "holdspeak" ? "HoldSpeak" : "You",
      who: line.who,
      text: line.text,
    };
  }), [call.id, call.transcript, start]);
  const results = call.results ?? [];
  const hangUp = (
    <Button variant="danger" dense loading={busy === "hangup"} onClick={onHangUp} data-testid="calls-hangup">
      <CallGlyph down />
      Hang up
    </Button>
  );
  return (
    <article className="cl-object" data-testid="calls-document" data-call={call.id}>
      <Mast className="cl-mast" kind={who === "You" ? "person" : "call"} id={who === "You" ? "you" : "calls"} title={who} facts={facts} data-testid="calls-mast">
        {!live && call.note_ref ? (
          <Button variant="secondary" dense onClick={() => openRef(call.note_ref!)} data-testid="calls-open-note">
            <ToolGlyph kind="note" />
            Open note
          </Button>
        ) : null}
        <Button variant="ghost" dense className="cl-back" onClick={onBack} data-testid="calls-back">All calls</Button>
        <ShowMe app="surface-calls" />
      </Mast>
      <Spine className="cl-spine" tone={tone} label={outcome.word} />
      {live && call.hold ? (
        <Plate tone="brass" head="HoldSpeak asks" facts={clock != null ? clockWords(clock) : undefined} testId="calls-hold" settle={settle}>
          <p className="cl-plate-words">{call.hold.words}</p>
          <div className="cl-plate-verbs">
            <Button variant="primary" dense loading={busy === "decide" && !settle} onClick={() => onDecide("approve")} data-testid="calls-yes">Yes</Button>
            <Button variant="secondary" dense disabled={busy === "decide"} onClick={() => onDecide("deny")} data-testid="calls-no">No</Button>
            {hangUp}
          </div>
        </Plate>
      ) : live ? (
        <Plate tone="steel" head="On the line" facts={clock != null ? clockWords(clock) : undefined} testId="calls-plate">
          <div className="cl-plate-verbs">{hangUp}</div>
        </Plate>
      ) : (
        <Plate tone={tone} head={outcome.word} facts={length || undefined} testId="calls-plate">
          <div className="cl-plate-verbs"><CallMe canCall={canCall} busy={busy === "place"} onCall={onCall} /></div>
        </Plate>
      )}
      <div className="cl-ledger" role="group" aria-label="The call">
        {/* The turns scroll in their own well: a live call follows its newest line there, and the plate keeps its place. */}
        {segments.length ? <div className="cl-turns"><LiveTranscript segments={segments} listening={live && !call.hold} /></div> : null}
        {results.length || call.note_ref ? (
          <section className="calls-done" aria-label="Done on this call" data-testid="calls-done">
            <h3 className="cl-cap">Done on this call</h3>
            {results.map((result, index) => (
              <ResultRow key={`${result.ref}-${index}`} kind={result.kind} label={result.label}
                word={EFFECT_WORDS[result.effect] ?? result.effect} onOpen={result.ref ? () => openRef(result.ref) : undefined}
                testId="calls-result" />
            ))}
            {call.note_ref ? (
              <ResultRow kind="note" label={noteWhen(call)} word="Transcript" onOpen={() => openRef(call.note_ref!)} testId="calls-transcript-note" />
            ) : null}
          </section>
        ) : null}
      </div>
    </article>
  );
}

/* ── the window ───────────────────────────────────────────────────────── */

type Picked = { kind: "call"; id: string } | { kind: "phone" } | null;

export function CallsCore({ scope }: CoreProps) {
  const calls = useCalls();
  const phoneOn = Boolean(calls.settings?.phone_on);
  const phone = usePhone(phoneOn);
  const asks = usePhoneFocus.getState();
  const [picked, setPicked] = useState<Picked>(scope === "phone" || (asks.pending && !asks.callId) ? { kind: "phone" } : null);
  const asked = usePhoneFocus((st) => st.pending);
  const askedCall = usePhoneFocus((st) => st.callId);
  const [viewing, setViewing] = useState<Call | null>(null);
  const [busy, setBusy] = useState<"" | "place" | "hangup" | "decide" | "open">("");
  const [refusal, setRefusal] = useState("");
  const [settle, setSettle] = useState<"" | "yes" | "no">("");
  const [fold, setFold] = useState<"" | "line" | "phone">("");
  const active = calls.active;
  const onPhone = picked?.kind === "phone";
  const shown = onPhone ? null : active ?? calls.ended ?? viewing;
  const clock = useCallClock(active);
  useWindowInterior("list");

  const ready = callsReady(calls.settings, calls.status);
  const mine = calls.settings?.allowed_numbers ?? [];
  const canCall = ready && mine.length > 0 && !active;
  const onLine = lineInUse(calls.status);

  const run = async (kind: typeof busy, act: () => Promise<void>) => {
    setBusy(kind);
    setRefusal("");
    try { await act(); } catch (error) { setRefusal(refusalWords(error, onLine)); } finally { setBusy(""); }
  };
  const callMe = () => void run("place", async () => {
    setViewing(null);
    setPicked(null);
    calls.clearEnded();
    calls.apply(withTranscript(await placeCall(), null));
  });
  const hangup = () => { if (active) void run("hangup", async () => { calls.apply(withTranscript(await hangUp(active.id), active)); }); };
  const answer = (decision: "approve" | "deny") => {
    if (active) void run("decide", async () => {
      const next = withTranscript(await decide(active.id, decision), active);
      if (motionAllowed()) {
        setSettle(decision === "approve" ? "yes" : "no");
        await new Promise((resolve) => window.setTimeout(resolve, SETTLE_MS));
      }
      setSettle("");
      calls.apply(next);
    });
  };
  const open = (id: string) => {
    setPicked({ kind: "call", id });
    if (active?.id === id) return;
    calls.clearEnded();
    void run("open", async () => { setViewing(await readCall(id)); });
  };
  useEffect(() => {
    if (!asked) return;
    if (askedCall) open(askedCall);
    else setPicked({ kind: "phone" });
    usePhoneFocus.getState().take();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [asked, askedCall]);
  const back = () => { setViewing(null); setPicked(null); calls.clearEnded(); };
  /** The Line's one writer (the `calls` subtree), then the window reads again. */
  const writeLine = async (_key: "line", value: unknown) => {
    await writeCallsSetting("line", value);
    await calls.reload();
  };

  const ended = calls.calls.filter((row) => row.state === "ended")
    .sort((a, b) => (at(b.started_at) || 0) - (at(a.started_at) || 0));
  const live = calls.calls.filter((row) => row.state !== "ended");
  const pickedId = onPhone ? null : shown?.id ?? null;

  let statusItems: Array<StatusBarItem | null>;
  let statusVerbs: ReactNode = null;
  if (onPhone) {
    statusItems = phoneStatusItems(phone);
  } else {
    statusItems = refusal ? [
      { key: "refusal", lamp: "warn", text: refusal, testId: "calls-refusal" },
    ] : active ? [
      { key: "live", lamp: "fail", live: true, text: "On a call", testId: "calls-status-live" },
      // The clock counts in place: no fade each second (a moment runs once).
      clock != null ? { key: "clock", text: <span className="calls-clock">{clockWords(clock)}</span>, testId: "calls-clock" } : null,
      active.hold ? { key: "hold", text: "Waiting for your answer" } : null,
    ] : shown ? [
      { key: "ended", text: <span className="calls-idle-word"><span className="kit-dot" data-tone="idle" aria-hidden="true" />Call ended</span> },
      shown.duration_sec ? { key: "length", text: <b>{clockWords(shown.duration_sec)}</b> } : null,
    ] : !calls.settings || !calls.settings.enabled ? [
      {
        key: "off",
        testId: "calls-status-off",
        text: (
          <span className="calls-idle-word">
            <span className="kit-dot" data-tone="idle" aria-hidden="true" />
            Calls are off
          </span>
        ),
      },
    ] : onLine ? [
      lineBarItem(calls.status),
    ] : calls.status.aiphone.state !== "running" ? [
      { key: "daemon", lamp: "warn", text: "ai-phone not running", testId: "calls-status-daemon" },
    ] : [
      { key: "ready", lamp: "ok", text: "Ready for calls", testId: "calls-status-ready" },
    ];
    if (!active) statusItems.push({ key: "count", text: countWords(ended.length, "call") });
    if (!active && !shown && (!calls.settings || !calls.settings.enabled)) {
      statusVerbs = (
        <Button variant="ghost" dense className="calls-status-link" onClick={openCallsSettings} data-testid="calls-open-settings">
          Settings ▸ Calls
        </Button>
      );
    }
  }

  /* The pane's phase keys it, so what arrives after the first read (the
     home, a call, the phone) fades up once, as the first paint does
     (pullout.css). A call that changes in place does not. */
  const phase = onPhone ? "phone" : calls.loading || calls.error ? "read" : shown ? `call-${shown.id}` : !ended.length ? "empty" : "list";
  const lineFold = calls.settings?.line ? "line" : null;
  const setUpLine = () => (lineFold ? setFold("line") : openSurfaceOr("configure-settings", "/settings", "calls::line"));

  let pane: ReactNode;
  if (onPhone) {
    pane = (
      // With the phone off the hub has nothing to read: no phone yet, at once.
      <PhonePane phone={phoneOn ? phone : { ...phone, loading: false }} onOpenCall={open} onBack={back}
        onPair={phoneOn ? () => setFold("phone") : openCallsSettings} />
    );
  } else if (calls.loading || calls.error) {
    pane = <SurfaceState loading={calls.loading} error={calls.error} onRetry={() => void calls.reload()} />;
  } else if (shown) {
    pane = (
      <CallPane call={shown} live={Boolean(active && active.id === shown.id)} clock={clock} mine={mine} status={calls.status}
        busy={busy} settle={settle} canCall={canCall} onCall={callMe} onHangUp={hangup} onDecide={answer} onBack={back} />
    );
  } else {
    const number = mine[0] ? masked(digits(mine[0])) : "";
    pane = (
      <div className="cl-object cl-home">
        <Plate tone={ready ? "steel" : "idle"} head="Place a call" facts={number ? `Rings ${number}` : undefined} testId="calls-plate">
          <div className="cl-plate-verbs">
            <CallMe canCall={canCall} busy={busy === "place"} onCall={callMe} />
          </div>
        </Plate>
        {ended.length ? null : (
          <SurfaceState
            empty
            emptyKind="call"
            emptyImage={spriteUrl("call", "calls")}
            emptyLabel={onLine && !ready ? "No line yet" : "No calls yet"}
            emptyHint={onLine && !ready ? "Set up the Line, then Call me rings your number." : "Call me rings your number and HoldSpeak answers."}
            actionLabel={canCall ? undefined : onLine ? "Set up the Line ›" : "Set up calls"}
            onAction={canCall ? undefined : onLine ? setUpLine : openCallsSettings}
          />
        )}
      </div>
    );
  }

  const hasRail = live.length > 0 || ended.length > 0 || phoneOn;
  return (
    <div className="calls-window cl" data-testid="calls-window" data-state={onPhone ? "phone" : active ? "live" : shown ? "call" : "list"}>
      <div className="cl-frame surface-rail-layout" data-picked={onPhone || shown ? "" : undefined}>
        {hasRail ? (
          <Rail label="Calls" data-testid="calls-rail" picked={onPhone ? "phone" : pickedId}
            onPick={(id) => { if (id === "phone") setPicked({ kind: "phone" }); else open(id); }}
            paneOpen={picked ? true : undefined} onBack={back} groups={[
              { id: "live", label: "On the line", items: live.map((call) => callItem(call, mine)) },
              { id: "recent", label: "Recent", testId: "calls-list", items: ended.map((call) => callItem(call, mine)) },
              { id: "phone", label: "Your phone", items: [phoneItem(phone, phoneOn)] },
            ]} />
        ) : null}
        <div className="calls-body cl-pane" key={phase} data-phase={phase}>{pane}</div>
      </div>
      {lineFold || phoneOn ? (
        <div className="cl-folds">
          {lineFold ? (
            <div className="cl-fold" data-testid="calls-fold-line" data-open={fold === "line" || undefined}>
              <FoldGadget title="Line" open={fold === "line"} onToggle={(open) => setFold((now) => (open ? "line" : now === "line" ? "" : now))}>
                {fold === "line" && calls.settings ? (
                  <LineSettingsPane settings={calls.settings} onWrite={writeLine} onReload={calls.reload} />
                ) : null}
              </FoldGadget>
            </div>
          ) : null}
          {phoneOn ? (
            <div className="cl-fold" data-testid="calls-fold-phone" data-open={fold === "phone" || undefined}>
              <FoldGadget title="Phone" open={fold === "phone"} onToggle={(open) => setFold((now) => (open ? "phone" : now === "phone" ? "" : now))}>
                {fold === "phone" ? <PhoneSettingsPane /> : null}
              </FoldGadget>
            </div>
          ) : null}
        </div>
      ) : null}
      <StatusBar data-testid="calls-status" items={statusItems} verbs={statusVerbs} />
    </div>
  );
}

export default CallsCore;

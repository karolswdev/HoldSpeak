/* Calls (CALLS-DESIGN-2026-10-28 §6; canvas
 * docs/internal/betterment/canvases/calls-2026-10-28.html): the Calls
 * window, Go ▸ Work ▸ Calls.
 *
 * Window grammar: title bar → Toolbar (Call me, the primary that makes the
 * object; Hang up on a call) → the body → a 24 px StatusBar with a dot and a
 * word (`● Ready for calls`, `● On a call · 2:14`, `● ai-phone not running`,
 * `● Calls are off · Settings ▸ Calls`). No host, number or engine chip
 * (UX-CANON A.9): egress is said in Settings ▸ Calls.
 *
 * On a call the body is the call as a document (the Live transcript), a
 * held question as one warm row with Yes and No (the tap form of his spoken
 * yes), and "Done on this call". Idle, the past calls are a dense list; a
 * press opens a call as a document. A `call_state` frame replaces the call
 * it names. */
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { LiveTranscript } from "../../pages/cores/LiveTranscript";
import "../../pages/cores/liveTranscript.css";
import type { CoreProps } from "../../pages/cores/core-types";
import { openRef } from "../openObject";
import { openSurfaceOr } from "../shell";
import { spriteUrl } from "../sprites";
import { useWindowInterior } from "../surface/interior";
import { StatusBar, TickNumber, ToolGlyph, Toolbar, countWords, type StatusBarItem } from "../surface/kit";
import { ObjectList, type ObjectListRow, type ObjectListSort, type ObjectListTone } from "../surface/objects/ObjectList";
import { SurfaceState } from "../surface/Surface";
import { decide, hangUp, placeCall, readCall, refusalWords, useCalls, withTranscript } from "./api";
import type { Call, CallResult, CallSummary, CallsSettings, CallsStatus } from "./types";
import "./calls.css";

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

const OUTCOMES: Record<string, { word: string; tone: ObjectListTone }> = {
  done: { word: "Done", tone: "ok" },
  no_answer: { word: "No answer", tone: "idle" },
  rejected: { word: "Refused", tone: "warn" },
  busy: { word: "Busy", tone: "warn" },
  failed: { word: "Failed", tone: "fail" },
  denied: { word: "Not let in", tone: "warn" },
};

export function outcomeOf(call: CallSummary): { word: string; tone: ObjectListTone } {
  if (call.state !== "ended") return { word: "On the line", tone: "fail" };
  const known = OUTCOMES[String(call.outcome ?? "")];
  if (known) return known;
  const raw = String(call.outcome ?? "").replace(/_/g, " ").trim();
  return { word: raw ? raw[0].toUpperCase() + raw.slice(1) : "Ended", tone: "idle" };
}

function digits(value: string): string {
  return value.replace(/^sip:/i, "").split("@", 1)[0].replace(/[^\d+]/g, "");
}

/** Who was on the other end: `You` for his own number, else the number with
 *  its middle hidden (`+1 ··· 0142`). */
export function remoteWords(remote: string, mine: readonly string[]): string {
  const number = digits(remote);
  if (number && mine.some((own) => digits(own) === number)) return "You";
  if (number.length > 4) return `${number.startsWith("+") ? number.slice(0, 2) : ""} ··· ${number.slice(-4)}`.trim();
  return number || "Unknown";
}

const EFFECT_WORDS: Record<CallResult["effect"], string> = {
  wrote: "Wrote",
  prepared: "Prepared",
  sent: "Sent on your yes",
};

const KIND_MARK: Record<string, string> = { note: "N", action: "✓", task: "✓", send: "➤", decision: "D", project: "P" };

function ResultRow({ kind, label, word, onOpen, testId }: {
  kind: string; label: string; word: string; onOpen?: () => void; testId?: string;
}) {
  return (
    <Button variant="chrome" className="calls-result" data-kind={kind} onClick={onOpen} disabled={!onOpen} data-testid={testId}>
      <span className="calls-result-mark" aria-hidden="true">{KIND_MARK[kind] ?? "•"}</span>
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

/** The call as a document: the transcript, the held question, what it did. */
function CallDocument({ call, live, busy, onDecide }: {
  call: Call;
  live: boolean;
  busy: boolean;
  onDecide?: (decision: "approve" | "deny") => void;
}) {
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
  return (
    <div className="calls-doc" data-testid="calls-document" data-call={call.id}>
      {segments.length ? <LiveTranscript segments={segments} listening={live && !call.hold} /> : null}
      {live && call.hold ? (
        <div className="calls-hold" role="group" aria-label="HoldSpeak asks" data-testid="calls-hold">
          <span className="calls-hold-words">{call.hold.words}</span>
          <span className="calls-hold-verbs">
            <Button variant="primary" dense loading={busy} onClick={() => onDecide?.("approve")} data-testid="calls-yes">Yes</Button>
            <Button variant="secondary" dense disabled={busy} onClick={() => onDecide?.("deny")} data-testid="calls-no">No</Button>
          </span>
        </div>
      ) : null}
      {results.length || call.note_ref ? (
        <section className="calls-done" aria-label="Done on this call" data-testid="calls-done">
          <h3 className="calls-done-title">Done on this call</h3>
          {results.map((result, index) => (
            <ResultRow
              key={`${result.ref}-${index}`}
              kind={result.kind}
              label={result.label}
              word={EFFECT_WORDS[result.effect] ?? result.effect}
              onOpen={result.ref ? () => openRef(result.ref) : undefined}
              testId="calls-result"
            />
          ))}
          {call.note_ref ? (
            <ResultRow kind="note" label={noteWhen(call)} word="Transcript" onOpen={() => openRef(call.note_ref!)} testId="calls-transcript-note" />
          ) : null}
        </section>
      ) : null}
    </div>
  );
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

/** Ready for calls: Calls on and the daemon running. */
export function callsReady(settings: CallsSettings | null, status: CallsStatus): boolean {
  return Boolean(settings?.enabled && status.enabled && status.aiphone.state === "running");
}

function openCallsSettings() {
  openSurfaceOr("configure-settings", "/settings", "calls");
}

export function CallsCore(_props: CoreProps) {
  const calls = useCalls();
  const [viewing, setViewing] = useState<Call | null>(null);
  const [busy, setBusy] = useState<"" | "place" | "hangup" | "decide" | "open">("");
  const [refusal, setRefusal] = useState("");
  const [sort, setSort] = useState<ObjectListSort>({ key: "when", dir: "desc" });
  const active = calls.active;
  const shown = active ?? calls.ended ?? viewing;
  const clock = useCallClock(active);
  useWindowInterior("list");

  const ready = callsReady(calls.settings, calls.status);
  const mine = calls.settings?.allowed_numbers ?? [];
  const canCall = ready && mine.length > 0;

  const run = async (kind: typeof busy, act: () => Promise<void>) => {
    setBusy(kind);
    setRefusal("");
    try { await act(); } catch (error) { setRefusal(refusalWords(error)); } finally { setBusy(""); }
  };
  const callMe = () => run("place", async () => {
    setViewing(null);
    calls.clearEnded();
    calls.apply(withTranscript(await placeCall(), null));
  });
  const hangup = () => { if (active) void run("hangup", async () => { calls.apply(withTranscript(await hangUp(active.id), active)); }); };
  const answer = (decision: "approve" | "deny") => {
    if (active) void run("decide", async () => { calls.apply(withTranscript(await decide(active.id, decision), active)); });
  };
  const open = (id: string) => void run("open", async () => { setViewing(await readCall(id)); });
  const back = () => { setViewing(null); calls.clearEnded(); };

  const rows: ObjectListRow[] = calls.calls.filter((row) => row.state === "ended").map((call) => {
    const outcome = outcomeOf(call);
    const length = call.duration_sec && call.duration_sec > 0 ? clockWords(call.duration_sec) : "";
    return {
      id: call.id,
      kind: "meeting",
      name: call.first_words ? `“${call.first_words}”` : (call.direction === "out" ? "HoldSpeak called you" : "No words"),
      when: callWhen(call.started_at),
      whenSort: at(call.started_at) || 0,
      state: { label: outcome.word, tone: outcome.tone, testId: "calls-outcome" },
      cells: { from: remoteWords(call.remote, mine), length },
      sortValues: { from: remoteWords(call.remote, mine), length: call.duration_sec ?? 0 },
    };
  });
  const ended = rows.length;

  const statusItems: Array<StatusBarItem | null> = refusal ? [
    { key: "refusal", lamp: "warn", text: refusal, testId: "calls-refusal" },
  ] : active ? [
    { key: "live", lamp: "fail", text: "On a call", testId: "calls-status-live" },
    clock != null ? { key: "clock", text: <TickNumber value={clockWords(clock)} className="calls-clock" />, testId: "calls-clock" } : null,
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
  ] : calls.status.aiphone.state !== "running" ? [
    { key: "daemon", lamp: "warn", text: "ai-phone not running", testId: "calls-status-daemon" },
  ] : [
    { key: "ready", lamp: "ok", text: "Ready for calls", testId: "calls-status-ready" },
  ];
  if (!active) statusItems.push({ key: "count", text: countWords(ended, "call") });

  let body: ReactNode;
  if (calls.loading || calls.error) {
    body = <SurfaceState loading={calls.loading} error={calls.error} onRetry={() => void calls.reload()} />;
  } else if (shown) {
    body = <CallDocument call={shown} live={Boolean(active)} busy={busy === "decide"} onDecide={answer} />;
  } else if (!ended) {
    body = (
      <SurfaceState
        empty
        emptyKind="meeting"
        emptyImage={spriteUrl("meeting", "calls")}
        emptyLabel="No calls yet"
        emptyHint="Call me rings your number and HoldSpeak answers."
        actionLabel={canCall ? "Call me" : "Set up calls"}
        onAction={canCall ? () => void callMe() : openCallsSettings}
      />
    );
  } else {
    body = (
      <div className="calls-list" data-testid="calls-list">
        <ObjectList
          label="Past calls"
          density="dense"
          rows={rows}
          columns={[
            { key: "name", word: "First words" },
            { key: "from", word: "From", track: "96px" },
            { key: "when", word: "When", track: "136px" },
            { key: "length", word: "Length", track: "72px" },
            { key: "state", word: "Outcome", track: "120px" },
          ]}
          sort={sort}
          onSort={(key: string) => setSort((now) => ({ key, dir: now.key === key && now.dir === "desc" ? "asc" : "desc" }))}
          onOpen={open}
          rowProps={(row) => ({ "data-testid": "calls-row", "data-call": row.id })}
        />
      </div>
    );
  }

  return (
    <div className="calls-window" data-testid="calls-window" data-state={active ? "live" : shown ? "call" : "list"}>
      <Toolbar label="Calls" data-testid="calls-toolbar">
        {active ? (
          <Button variant="danger" dense loading={busy === "hangup"} onClick={hangup} data-testid="calls-hangup">
            <CallGlyph down />
            Hang up
          </Button>
        ) : (
          <>
            <Button
              variant="primary"
              dense
              loading={busy === "place"}
              disabled={!canCall}
              title={canCall ? "HoldSpeak rings your number" : "Set up calls in Settings ▸ Calls"}
              onClick={() => void callMe()}
              data-testid="calls-call-me"
            >
              <CallGlyph />
              Call me
            </Button>
            {shown?.note_ref ? (
              <Button variant="secondary" dense onClick={() => openRef(shown.note_ref!)} data-testid="calls-open-note">
                <ToolGlyph kind="note" />
                Open note
              </Button>
            ) : null}
            {shown ? (
              <Button variant="secondary" dense onClick={back} data-testid="calls-back">All calls</Button>
            ) : null}
          </>
        )}
      </Toolbar>
      <div className="calls-body">{body}</div>
      <StatusBar
        data-testid="calls-status"
        items={statusItems}
        verbs={!active && !shown && (!calls.settings || !calls.settings.enabled) ? (
          <Button variant="ghost" dense className="calls-status-link" onClick={openCallsSettings} data-testid="calls-open-settings">
            Settings ▸ Calls
          </Button>
        ) : null}
      />
    </div>
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

export default CallsCore;

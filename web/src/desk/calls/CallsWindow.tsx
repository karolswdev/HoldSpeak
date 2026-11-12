import { useEffect, useRef, useState } from "react";
import type { CoreProps } from "../../pages/cores/core-types";
import { openRef } from "../openObject";
import { spriteUrl } from "../sprites";
import {
  ActionNotice,
  PreferencePane,
  PreferenceWell,
  Elapsed,
  InspectorBody,
  InspectorFacts,
  InspectorFigures,
  InspectorQuestion,
  ListApp,
  ListPane,
  PaneNotice,
  useWindowInterior,
  ListView,
  PaneInspector,
  PaneViews,
  SurfaceState,
  countWords,
  useWindowMast,
  type ListVerb,
  type ObjectListRow,
  type StatusBarItem,
} from "../surface";
import { TranscriptWell } from "../../pages/cores/history/TranscriptWell";
import { PaneViewContext } from "../surface/patterns/PaneViews";
import { useCompactViewport } from "../useCompactViewport";
import { useGuideView } from "../walk/viewState";
import {
  decide,
  hangUp,
  lineInUse,
  placeCall,
  readCall,
  refusalWords,
  useCalls,
  withTranscript,
  writeCallsSetting,
} from "./api";
import { LineSettingsPane } from "./LineSettings";
import {
  PhonePane,
  phoneStatusItems,
  pushNotReady,
  type PhoneFailure,
} from "./PhonePane";
import { PhoneSettingsPane } from "./PhoneSettings";
import { pairedPhone, usePhone, waitsForReply } from "./phoneApi";
import { usePhoneFocus } from "./phoneFocus";
import type {
  Call,
  CallResult,
  CallSummary,
  CallsSettings,
  CallsStatus,
} from "./types";

export function clockWords(seconds: number): string {
  const whole = Math.max(0, Math.floor(seconds));
  const h = Math.floor(whole / 3600),
    m = Math.floor((whole % 3600) / 60),
    s = String(whole % 60).padStart(2, "0");
  return h ? `${h}:${String(m).padStart(2, "0")}:${s}` : `${m}:${s}`;
}
function at(value: string | null | undefined): number {
  return value ? Date.parse(value) : NaN;
}
export function callWhen(
  value: string | null | undefined,
  now = new Date(),
): string {
  const ms = at(value);
  if (!Number.isFinite(ms)) return "";
  const date = new Date(ms),
    yesterday = new Date(now);
  yesterday.setDate(now.getDate() - 1);
  const clock = date.toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
  if (date.toDateString() === now.toDateString()) return `Today ${clock}`;
  if (date.toDateString() === yesterday.toDateString())
    return `Yesterday ${clock}`;
  const day =
    now.getTime() - ms < 6 * 86_400_000 && now.getTime() > ms
      ? date.toLocaleDateString("en-US", { weekday: "short" })
      : date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `${day} ${clock}`;
}
type Tone = "ok" | "idle" | "warn" | "fail" | "info" | "ask";
const OUTCOMES: Record<string, { word: string; tone: Tone }> = {
  done: { word: "Done", tone: "ok" },
  no_answer: { word: "No answer", tone: "fail" },
  rejected: { word: "Refused", tone: "warn" },
  busy: { word: "Busy", tone: "warn" },
  failed: { word: "Failed", tone: "fail" },
  denied: { word: "Not let in", tone: "warn" },
};
export function outcomeOf(call: CallSummary): { word: string; tone: Tone } {
  if (call.state !== "ended")
    return call.hold
      ? { word: "Waits for you", tone: "ask" }
      : { word: "On the line", tone: "info" };
  const raw = String(call.outcome ?? "")
    .replace(/_/g, " ")
    .trim();
  return (
    OUTCOMES[String(call.outcome)] ?? {
      word: raw ? raw[0].toUpperCase() + raw.slice(1) : "Ended",
      tone: "idle",
    }
  );
}
function digits(value: string): string {
  return value
    .replace(/^sip:/i, "")
    .split("@", 1)[0]
    .replace(/[^\d+]/g, "");
}
function masked(number: string): string {
  return number.length > 4
    ? `${number.startsWith("+") ? number.slice(0, 2) : ""} ··· ${number.slice(-4)}`.trim()
    : number;
}
export function remoteWords(remote: string, mine: readonly string[]): string {
  const number = digits(remote);
  return number && mine.some((own) => digits(own) === number)
    ? "You"
    : masked(number) || "Unknown";
}
export function callsReady(
  settings: CallsSettings | null,
  status: CallsStatus,
): boolean {
  return Boolean(
    settings?.enabled &&
    status.enabled &&
    (lineInUse(status)
      ? status.line?.state === "ready"
      : status.aiphone.state === "running"),
  );
}
export function lineBarItem(
  status: CallsStatus,
): StatusBarItem & { text: string } {
  const state = status.line?.state;
  if (state === "ready")
    return {
      key: "ready",
      lamp: "ok",
      text: "Ready for calls",
      testId: "calls-status-ready",
    };
  if (state === "starting")
    return {
      key: "line",
      lamp: "info",
      live: true,
      text: "Line starting",
      testId: "calls-status-line",
    };
  if (state === "not_running" || state === "offline")
    return {
      key: "line",
      lamp: "warn",
      text: "Line not running",
      testId: "calls-status-line",
    };
  return {
    key: "line",
    lamp: "ask",
    text: "No line",
    testId: "calls-status-line",
  };
}
function callTitle(call: CallSummary): string {
  return (
    call.first_words ||
    (call.state !== "ended"
      ? "On the line"
      : call.direction === "out"
        ? "HoldSpeak called you"
        : "No words")
  );
}
const EFFECT_WORDS: Record<CallResult["effect"], string> = {
  wrote: "Wrote",
  prepared: "Prepared",
  sent: "Sent on your yes",
  started: "Started on your yes",
  changed: "Changed on your yes",
};

function CallDetails({
  call,
  live,
  mine,
  status,
  transcript,
  busy,
  answer,
}: {
  call: Call;
  live: boolean;
  mine: readonly string[];
  status: CallsStatus;
  transcript: boolean;
  busy: boolean;
  answer(decision: "approve" | "deny", target: Call): void;
}) {
  const [result, setResult] = useState<string | null>(null);
  const results = call.results ?? [];
  const outcome = outcomeOf(call);
  const started = at(call.answered_at) || at(call.started_at);
  const turns = call.transcript.map((line, i) => {
    const offset = (at(line.at) - started) / 1000;
    const who = line.who === "holdspeak" ? "HoldSpeak" : "You";
    return {
      id: `${call.id}-${i}`,
      label: [who, Number.isFinite(offset) ? clockWords(offset) : ""]
        .filter(Boolean)
        .join(" · "),
      text: line.text,
    };
  });
  const selected = results.find((_, i) => String(i) === result);
  const openResult: ListVerb[] = [
    {
      id: "open-result",
      label: "Open",
      enabled: () => Boolean(selected?.ref),
      run: () => {
        if (selected?.ref) openRef(selected.ref);
      },
    },
  ];
  const elapsed = <Elapsed start={call.answered_at ?? call.started_at ?? ""} />;
  const length =
    call.duration_sec == null ? undefined : clockWords(call.duration_sec);
  return (
    <PaneInspector
      label={callTitle(call)}
      subtitle={`${outcome.word} · ${callWhen(call.started_at)}`}
      object={
        <img
          src={spriteUrl("call", "calls", "rest", null, 32)}
          width={32}
          height={32}
          alt=""
        />
      }
      testId="calls-document"
      trailing={
        live
          ? countWords(results.length, "result")
          : !results.length
            ? length
            : undefined
      }
    >
      <InspectorBody>
        {results.length && !live ? (
          <InspectorFigures
            label="The call"
            figures={[
              {
                value: live ? elapsed : (length ?? "—"),
                label: live ? "on the line" : "length",
              },
              { value: results.length, label: "done on call" },
            ]}
          />
        ) : null}
        {transcript ? (
          <PreferenceWell>
            <InspectorFacts
              name="Transcript"
              header={false}
              testId="calls-transcript"
              data-feedback-redact="true"
              rows={turns.map((line) => ({
                key: line.id,
                label: line.label,
                value: line.text,
              }))}
            />
          </PreferenceWell>
        ) : live ? (
          <div role="log" aria-label="Transcript" data-feedback-redact="true">
            <TranscriptWell
              id={call.id}
              segments={turns.slice(-4).map((line, index, tail) => ({
                id: line.id,
                speaker: line.label,
                text: line.text + (index === tail.length - 1 ? " ▌" : ""),
              }))}
            />
          </div>
        ) : null}
        {live && call.hold ? (
          <InspectorQuestion
            key={`${call.id}:${JSON.stringify(call.hold)}`}
            targetId={`${call.id}:${JSON.stringify(call.hold)}`}
            actionId="answer-call"
            question={call.hold.words}
            rows={[
              {
                label: "Yes",
                control: (
                  <span
                    data-testid="calls-yes-effect"
                    data-feedback-redact="true"
                  >
                    {call.hold.words}
                  </span>
                ),
              },
            ]}
            cancelLabel="No"
            variant="brass"
            cancel={() => {
              if (!busy) answer("deny", call);
            }}
            cancelTestId="calls-no"
            testId="calls-hold"
            verb={{
              label: "Yes",
              run: () => answer("approve", call),
              busy,
              testId: "calls-yes",
            }}
          />
        ) : null}
        <InspectorFacts
          name="Call facts"
          header={false}
          data-feedback-redact="true"
          rows={[{ label: "Number", value: call.remote }]}
        />
        {!transcript && results.length ? (
          <ListPane
            listTestId="calls-results"
            label="Done on this call"
            list={
              <ListView
                label="Done on this call"
                ordered
                rows={results.map((item, i) => ({
                  id: String(i),
                  kind: item.kind,
                  name: item.label,
                  detail: EFFECT_WORDS[item.effect] ?? item.effect,
                  leadingLamp: { state: "done" as const, label: "Done" },
                }))}
                columns={[{ key: "name", word: "Done on this call" }]}
                rowProps={() => ({
                  "data-testid": "calls-result",
                  "data-feedback-redact": "true",
                })}
                selectedId={result}
                onSelect={setResult}
                verbs={openResult}
                defaultVerb="open-result"
              />
            }
          />
        ) : null}
        {live && status.engine.model ? (
          <InspectorFacts
            data-feedback-redact="true"
            header={false}
            name="Call facts"
            rows={[{ label: "Voice", value: status.engine.model }]}
          />
        ) : null}
      </InspectorBody>
    </PaneInspector>
  );
}

type Entry = { id: string; call?: CallSummary };
export function CallsCore({ scope }: CoreProps) {
  useWindowInterior("list");
  const compact = useCompactViewport();
  const calls = useCalls(),
    phoneOn = Boolean(calls.settings?.phone_on),
    phone = usePhone(phoneOn);
  const asks = usePhoneFocus.getState();
  const [phoneDraft, setPhoneDraft] = useState("");
  const [phoneBusy, setPhoneBusy] = useState("");
  const [phoneRefusal, setPhoneRefusal] = useState<PhoneFailure>(null);
  const [phoneReply, setPhoneReply] = useState<string | null>(asks.replyTo);
  const [picked, setPicked] = useState<string | null>(
    scope === "phone" || (asks.pending && !asks.callId) ? "phone" : null,
  );
  const [view, setView] = useState("all");
  const [viewing, setViewing] = useState<Call | null>(null),
    [readError, setReadError] = useState("");
  const [busy, setBusy] = useState(""),
    [refusal, setRefusal] = useState("");
  const [readRound, setReadRound] = useState(0);
  const activeId = calls.active?.id;
  const previousActive = useRef<string | undefined>(undefined);
  useEffect(() => {
    if (activeId && activeId !== previousActive.current) setPicked(activeId);
    previousActive.current = activeId;
  }, [activeId]);
  const asked = usePhoneFocus((st) => st.pending),
    askedCall = usePhoneFocus((st) => st.callId);
  useEffect(() => {
    if (asked) {
      setPicked(askedCall ?? "phone");
      setView("all");
      usePhoneFocus.getState().take();
    }
  }, [asked, askedCall]);
  useGuideView(
    () => ({ picked, view }),
    (saved) => {
      setPicked(saved.picked);
      setView(saved.view);
    },
    undefined,
    1,
  );
  const live = calls.active?.id === picked ? calls.active : null;
  const ended = calls.ended?.id === picked ? calls.ended : null;
  useEffect(() => {
    let current = true;
    setViewing(null);
    setReadError("");
    if (picked && picked !== "phone" && !live && !ended) {
      void readCall(picked).then(
        (call) => {
          if (current) setViewing(call);
        },
        (error) => {
          if (current) setReadError(refusalWords(error));
        },
      );
    }
    return () => {
      current = false;
    };
  }, [picked, live?.id, ended?.id, readRound]);
  const shown = live ?? ended ?? (viewing?.id === picked ? viewing : null);
  const mine = calls.settings?.allowed_numbers ?? [];
  const ready = callsReady(calls.settings, calls.status),
    canCall =
      ready &&
      mine.length > 0 &&
      !calls.active &&
      refusal !== "A call is on the line";
  const run = async (kind: string, action: () => Promise<void>) => {
    if (busy && (kind !== "hangup" || busy === "hangup")) return;
    setBusy(kind);
    setRefusal("");
    try {
      await action();
    } catch (error) {
      setRefusal(refusalWords(error, lineInUse(calls.status)));
    } finally {
      setBusy((current) => (current === kind ? "" : current));
    }
  };
  const callMe = () =>
    void run("place", async () => {
      const call = withTranscript(await placeCall(), null);
      calls.apply(call);
      setPicked(call.id);
      setView("all");
    });
  const answer = (decision: "approve" | "deny", target: Call) =>
    void run("decide", async () => {
      calls.apply(withTranscript(await decide(target.id, decision), target));
    });
  const items: Entry[] = [
    ...calls.calls.filter((call) => call.state !== "ended"),
    ...calls.calls
      .filter((call) => call.state === "ended")
      .sort((a, b) => (at(b.started_at) || 0) - (at(a.started_at) || 0)),
  ].map((call) => ({ id: call.id, call }));
  if (calls.active && !items.some((item) => item.id === calls.active!.id))
    items.unshift({ id: calls.active.id, call: calls.active });
  if (
    viewing &&
    viewing.id === picked &&
    !items.some((item) => item.id === viewing.id)
  )
    items.push({ id: viewing.id, call: viewing });
  items.push({ id: "phone" });
  const device = pairedPhone(phone.status);
  const waiting =
    phone.messages.some((message) => waitsForReply(message, phone.messages)) ||
    phone.calls.some((call) => call.state === "held");
  const row = (entry: Entry): ObjectListRow => {
    if (!entry.call)
      return {
        id: "phone",
        kind: "call",
        name: device?.name ?? "Your phone",
        detail: device ? "Paired" : phoneOn ? "Not paired" : "Off",
        group: 2,
        state: {
          label: !phoneOn
            ? "Off"
            : waiting
              ? "Waits on you"
              : device
                ? pushNotReady(device)
                  ? "Push not ready"
                  : "Paired"
                : "Not paired",
          tone: waiting ? "ask" : "idle",
        },
      };
    const call = entry.call,
      outcome = outcomeOf(call);
    return {
      id: call.id,
      kind: "call",
      name: callTitle(call),
      detail: callWhen(call.started_at),
      group: call.state === "ended" ? 1 : 0,
      when: callWhen(call.started_at),
      cells: {
        length:
          call.state !== "ended" ? (
            <Elapsed start={call.answered_at ?? call.started_at ?? ""} />
          ) : call.duration_sec == null ? (
            "—"
          ) : (
            clockWords(call.duration_sec)
          ),
      },
      leadingLamp: {
        state:
          outcome.tone === "ask"
            ? "waiting"
            : call.state !== "ended"
              ? "working"
              : outcome.tone === "ok"
                ? "done"
                : outcome.tone === "fail" || outcome.tone === "warn"
                  ? "failed"
                  : "off",
        label: outcome.word,
      },
      state: {
        label:
          call.state !== "ended"
            ? "On the line"
            : call.outcome === "done"
              ? "Done"
              : call.outcome === "no_answer"
                ? "No answer"
                : "Failed",
        tone: outcome.tone,
        testId: "calls-outcome",
      },
    };
  };
  const visible = items;
  const selected = visible.find((item) => item.id === picked) ?? null;
  const verbs: ListVerb[] = [
    {
      id: "call",
      label: "Call me",
      variant: "primary",
      testId: "calls-call-me",
      dispatching: busy === "place",
      enabled: () => canCall && !busy,
      title: mine[0]
        ? `Rings ${masked(digits(mine[0])) || "your phone"}`
        : "Set a number in Settings",
      run: callMe,
    },
    {
      id: "hangup",
      label: "Hang up",
      variant: "stop",
      testId: "calls-hangup",
      dispatching: busy === "hangup",
      enabled: () => Boolean(calls.active) && busy !== "hangup",
      run: () => {
        const target = calls.active;
        if (target)
          void run("hangup", async () => {
            calls.apply(withTranscript(await hangUp(target.id), target));
            setPicked(target.id);
            setView("all");
          });
      },
    },
    {
      id: "note",
      label: "Open note",
      testId: "calls-open-note",
      enabled: () => Boolean(selected && shown?.note_ref),
      run: () => {
        if (shown?.note_ref) openRef(shown.note_ref);
      },
    },
    {
      id: "transcript",
      label: "Open transcript",
      enabled: () => Boolean(selected?.call && shown),
      run: () => setView("transcript"),
    },
  ];
  const stateLine = calls.loading
    ? undefined
    : calls.error
      ? "Calls not read"
      : calls.active || refusal === "A call is on the line"
        ? `${calls.status.lines[0]?.id || "Line"} · On the line`
        : !calls.settings?.enabled
          ? "Calls are off"
          : ready
            ? "Ready for calls"
            : lineInUse(calls.status)
              ? lineBarItem(calls.status).text
              : calls.status.aiphone.words || "ai-phone not running";
  useWindowMast({
    line: stateLine,
    figures: calls.active
      ? [
          {
            value: (
              <Elapsed
                start={
                  calls.active.answered_at ?? calls.active.started_at ?? ""
                }
              />
            ),
            label: "on the line",
            tone: "stop",
          },
        ]
      : [
          {
            value: calls.calls.filter((call) => call.outcome === "no_answer")
              .length,
            label: "no answer",
            tone: "ask",
          },
        ],
  });
  const status: Array<StatusBarItem | null> = calls.loading
    ? []
    : calls.error
      ? [
          {
            key: "read",
            lamp: "fail",
            text: "Calls not read",
            notice: "Calls not read",
            priority: 100,
          },
        ]
      : refusal === "A call is on the line"
        ? [{ key: "line", text: "On the line", lamp: "info", priority: 100 }]
        : picked === "phone"
          ? phoneStatusItems(phone)
          : calls.active
            ? [
                {
                  key: "live",
                  lamp: calls.active.hold ? "ask" : "info",
                  live: true,
                  text: calls.active.hold
                    ? "Waiting for your answer"
                    : "On a call",
                  priority: 100,
                  testId: "calls-status-live",
                },
                {
                  key: "clock",
                  text: (
                    <Elapsed
                      start={
                        calls.active.answered_at ??
                        calls.active.started_at ??
                        ""
                      }
                    />
                  ),
                  testId: "calls-clock",
                },
              ]
            : [
                lineInUse(calls.status) && calls.settings?.enabled
                  ? lineBarItem(calls.status)
                  : {
                      key: "ready",
                      text: stateLine,
                      lamp: ready ? "ok" : undefined,
                      testId: ready ? "calls-status-ready" : "calls-status-off",
                    },
                {
                  key: "count",
                  text: countWords(
                    calls.calls.filter((call) => call.state === "ended").length,
                    "call",
                  ),
                },
              ];
  const lineView =
    view === "line" || view === "line-account" || view === "telnyx";
  const phoneSetupView = view === "phone-setup" || view === "phone-alerts";
  const writeLine = async (_key: "line", value: unknown) => {
    await writeCallsSetting("line", value);
    await calls.reload();
  };
  return (
    <PreferencePane label="Calls" data-feedback-redact="true">
      <PaneViews
        label="Call view"
        value={view}
        onChange={setView}
        tabs={[
          { id: "all", label: "All calls" },
          ...(selected?.call && shown
            ? [{ id: "transcript", label: "Transcript" }]
            : []),
          ...(calls.settings?.line
            ? [
                { id: "line", label: "Line setup" },
                { id: "line-account", label: "Line account" },
                ...(calls.settings.line.account.kind === "telnyx"
                  ? [{ id: "telnyx", label: "Telnyx setup" }]
                  : []),
              ]
            : []),
          { id: "phone-setup", label: "Phone setup" },
          { id: "phone-alerts", label: "Phone alerts" },
        ]}
      >
        <ListApp<Entry>
          label="Calls"
          layout={
            compact &&
            !live &&
            picked !== "phone" &&
            !lineView &&
            !phoneSetupView
              ? undefined
              : "deck"
          }
          paneOpen={Boolean(live) || lineView || phoneSetupView}
          onPaneBack={() => {
            setView("all");
            if (live) setPicked(null);
          }}
          app={{
            visible,
            selected: lineView || phoneSetupView ? null : selected,
            picked,
            setPicked: (id) => {
              setPicked(id);
              setView("all");
            },
            query: "",
            setQuery: () => {},
            loading: calls.loading,
            error: calls.error,
            reload: calls.reload,
            serverSearch: false,
            groups: [
              { id: 0, label: "On the line" },
              { id: 1, label: "Recent" },
              { id: 2, label: "Your phone" },
            ],
          }}
          ids={{
            windowTestId: "calls-window",
            listTestId: "calls-list",
            paneTestId: "calls-inspector",
            toolbarTestId: "calls-toolbar",
            statusTestId: "calls-status",
          }}
          words={{
            find: "Find a call",
            empty: "No calls yet",
            noMatch: "No calls match",
            select: calls.calls.length ? undefined : "No calls yet",
          }}
          row={row}
          list={{
            toolbar: { trailing: false },
            columns: [
              { key: "name", word: "Call", priority: 100, minWidth: 220 },
              { key: "when", word: "At", track: "70px", priority: 10 },
              { key: "length", word: "Length", track: "55px", priority: 20 },
              { key: "state", word: "State", track: "124px", priority: 100 },
            ],
            verbs,
            defaultVerb: "transcript",
            rowProps: (item) => ({
              "data-testid":
                item.id === "phone" ? "calls-rail-phone" : "calls-row",
              "data-call": item.id === "phone" ? undefined : item.id,
              "data-feedback-redact": "true",
            }),
          }}
          status={status}
          pane={() => {
            const notice = refusal ? (
              <ActionNotice
                tone="warn"
                role="alert"
                action={{
                  label: "Read again",
                  onClick: () => {
                    setRefusal("");
                    void calls.reload();
                  },
                }}
              >
                <span data-testid="calls-refusal">{refusal}</span>
              </ActionNotice>
            ) : null;
            const content =
              lineView && calls.settings ? (
                <LineSettingsPane
                  showEgress={false}
                  accountOpen={view === "line-account"}
                  telnyxOpen={view === "telnyx"}
                  settings={calls.settings}
                  onWrite={writeLine}
                  onReload={calls.reload}
                />
              ) : phoneSetupView ? (
                <PhoneSettingsPane
                  alertsOpen={view === "phone-alerts"}
                  showEgress={false}
                />
              ) : picked === "phone" ? (
                <PhonePane
                  busy={phoneBusy}
                  setBusy={setPhoneBusy}
                  refusal={phoneRefusal}
                  setRefusal={setPhoneRefusal}
                  draft={phoneDraft}
                  setDraft={setPhoneDraft}
                  replying={phoneReply}
                  setReplying={setPhoneReply}
                  phone={phoneOn ? phone : { ...phone, loading: false }}
                  onOpenCall={(id) => {
                    setPicked(id);
                    setView("all");
                  }}
                  onPair={() => setView("phone-setup")}
                />
              ) : selected?.call ? (
                readError ? (
                  <SurfaceState
                    error={readError}
                    onRetry={() => setReadRound((round) => round + 1)}
                  />
                ) : shown ? (
                  <CallDetails
                    key={shown.id}
                    call={shown}
                    live={Boolean(live)}
                    mine={mine}
                    status={calls.status}
                    transcript={view === "transcript"}
                    busy={Boolean(busy)}
                    answer={answer}
                  />
                ) : (
                  <SurfaceState loading />
                )
              ) : calls.loading || calls.error ? null : (
                <PaneInspector label="Line" testId="calls-line-summary">
                  <InspectorBody>
                    <InspectorFacts
                      name="Line"
                      header={false}
                      rows={[
                        { label: "State", value: stateLine },
                        {
                          label: "Last call",
                          value:
                            calls.calls
                              .filter((call) => call.state === "ended")
                              .sort(
                                (a, b) =>
                                  (at(b.started_at) || 0) -
                                  (at(a.started_at) || 0),
                              )[0]?.first_words || "No calls yet",
                        },
                      ]}
                    />
                    <InspectorFigures
                      label="Today"
                      figures={[
                        {
                          label: "Calls today",
                          value: calls.calls.filter(
                            (call) =>
                              call.started_at &&
                              new Date(call.started_at).toDateString() ===
                                new Date().toDateString(),
                          ).length,
                        },
                        {
                          label: "No answer",
                          value: calls.calls.filter(
                            (call) =>
                              call.outcome === "no_answer" &&
                              call.started_at &&
                              new Date(call.started_at).toDateString() ===
                                new Date().toDateString(),
                          ).length,
                        },
                      ]}
                    />
                  </InspectorBody>
                </PaneInspector>
              );
            return content ? (
              <PaneViewContext.Provider value={null}>
                {notice ? (
                  <InspectorBody>
                    {notice}
                    {content}
                  </InspectorBody>
                ) : (
                  content
                )}
              </PaneViewContext.Provider>
            ) : null;
          }}
        />
      </PaneViews>
    </PreferencePane>
  );
}
export default CallsCore;

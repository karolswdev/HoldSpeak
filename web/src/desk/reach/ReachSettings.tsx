/* Settings ▸ Reach (PG-DIRECTION DIR6; DIRECTION-2026-10-31.md §9, canvas
 * canvases/direction-2026-10-31.html "Settings ▸ Reach"; ruled 2026-10-31:
 * Notices becomes Reach, and the Reach you rows move here from Settings ▸
 * Calls ▸ Phone).
 *
 * Telegram has its own tab: the setup pane of `TelegramSetup.tsx` (2026-11-13;
 * the old Channels row with its unlabelled token field is parked beside this
 * file). `What it sends` is one tab (2026-11-13; the `When` and `Brief` tabs
 * are parked beside this file): a short list picks what the pane shows: the
 * kinds that go to Telegram, when to reach you (the ladder and quiet hours,
 * the one store, shared with the Phone), the digest and Later means, and the
 * Cadence and morning brief groups. Calls keeps the Phone app and the Reach
 * you rows. The egress fact sits in the Telegram
 * pane, where the choice is made (UX-CANON A.9). No modal. */
import { Fragment, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { hubWords, TelegramSetup, type TelegramPairing, type TelegramStatus } from "./TelegramSetup";
import { wireClock } from "../surface/format";
import { useResource } from "../../pages/pageSupport";
import { ReachYouRows } from "../calls/PhoneSettings";
import type { PhoneStatus } from "../calls/phoneTypes";
import { openSurfaceOr } from "../shell";
import { CycleGadget, GadgetGroup, GadgetRow } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { plainFail } from "../surface/plainFailure";
import { SurfaceState } from "../surface/Surface";
import { PreferencePane, PreferenceWell, SegmentedTabs, ListPane, ListView, PaneGroup } from "../surface";

export type ReachStatus = {
  channels: {
    desk: { words: string };
    phone_app: { on: boolean; paired: string | null; words: string };
    telegram: TelegramStatus;
    calls: { ready: boolean; words: string };
  };
  ladder: {
    telegram: string;
    telegram_words?: string;
    order: string[];
    kinds: Record<string, unknown>;
    /** What Telegram sends, kind by kind (the hub's words and modes). */
    sends?: SendKind[];
    cap_words?: string;
    people_words?: string;
  };
  quiet_hours: { start: number; end: number; now: boolean };
  digest: { at: string | number; hour: number; brief?: string; brief_words?: string };
  later_means: string;
  later_means_words?: string;
  open_packages: unknown[];
  later: unknown[];
};

export type Pairing = TelegramPairing;

/** One kind that can travel to Telegram: his word, the words it takes, and
 *  how it goes now under Telegram's rung. */
export type SendKind = {
  kind: string;
  label: string;
  mode: string;
  modes: { value: string; label: string }[];
  now: string;
  now_words: string;
  fact?: string;
};

export const BRIEF_MODES = [
  { value: "on", label: "On" },
  { value: "off", label: "Off" },
];

export const TELEGRAM_RUNG = [
  { value: "at_once", label: "At once" },
  { value: "after_10", label: "After 10 min" },
  { value: "digest", label: "Only the digest" },
  { value: "off", label: "Off" },
];

/** DIR7: the ladder's rungs, in the hub's order when it sends none. */
export const LADDER = ["desk", "phone_app", "telegram", "call"];

/** The Phone rung: the Phone app's push, at once or off. */
export const PHONE_RUNG = [
  { value: "on", label: "At once" },
  { value: "off", label: "Off" },
];

export const LATER_MEANS = [
  { value: "in_2h", label: "In 2 hours" },
  { value: "end_of_quiet", label: "End of quiet hours" },
  { value: "tomorrow", label: "Tomorrow" },
];

export const DIGEST_TIMES = [
  { value: "end_of_quiet", label: "End of quiet hours" },
  ...[6, 7, 8, 9, 10, 12, 18].map((hour) => ({
    value: String(hour),
    label: `${String(hour).padStart(2, "0")}:00`,
  })),
];

/** The kinds of Reach you, without the level key the hub sends beside them. */
function reachKinds(kinds: Record<string, unknown> | undefined): PhoneStatus["reach"] {
  const out: PhoneStatus["reach"] = {};
  for (const [kind, value] of Object.entries(kinds ?? {})) {
    if (kind !== "level" && value && typeof value === "object") out[kind] = value as PhoneStatus["reach"][string];
  }
  return out;
}

export function ReachSettingsPane({
  highlight,
  onSaved,
  onStatus,
  quiet,
  cadence,
  cadenceTabs,
  urgentCallsDnd = false,
}: {
  highlight?: string | null;
  onSaved?: () => void;
  /** The window's strip says Telegram's state (the host owns the strip). */
  onStatus?: (words: string | null) => void;
  /** Quiet hours: the one store (Settings' heartbeat rows). */
  quiet: ReactNode;
  /** Read-only fact from the Settings document the host already reads. */
  urgentCallsDnd?: boolean;
  /** The Cadence and morning brief groups, folded. */
  cadence?: ReactNode;
  cadenceTabs?: {
    id: string;
    label: string;
    content: ReactNode;
    form?: boolean;
  }[];
}) {
  // A deep link names a row of What it sends: the ladder and quiet hours
  // (When to reach you), the digest and Later, or a Cadence entry.
  const briefTarget = highlight === "reach.digest" || highlight === "reach.later" ? "digest"
    : highlight?.startsWith("heartbeat.") || highlight?.startsWith("reach.ladder") ? "when"
    : highlight?.startsWith("cadence.brief") ? "brief" : highlight?.startsWith("cadence.") || highlight?.startsWith("cadence_telegram.") ? "cadence" : null;
  const [tab, setTab] = useState(briefTarget ? "sends" : "telegram");
  const [briefPick, pickBrief] = useState(briefTarget ?? "kinds");
  const briefRef = useRef<HTMLDivElement>(null);
  const [focusRequest, requestFocus] = useState(0);
  useLayoutEffect(() => {
    if (focusRequest) briefRef.current?.querySelector<HTMLElement>(
      '.surface-list-pane-preview :is(input, select, textarea, button):not(:disabled)',
    )?.focus();
  }, [focusRequest]);
  useEffect(() => {
    if (briefTarget) {setTab("sends"); pickBrief(briefTarget);}
  }, [highlight, briefTarget]);
  const reach = useResource<ReachStatus | null>("/api/reach", null);
  // A hub without the Reach routes (or any other answer) draws the rows empty.
  const status = reach.data && typeof reach.data === "object" && reach.data.channels ? reach.data : null;
  const [pairing, setPairing] = useState<Pairing | null>(null);
  const [tokenRefused, setTokenRefused] = useState<string | null>(null);
  const [tokenDraft, setTokenDraft] = useState("");
  const [telegramRefusal, setTelegramRefusal] = useState<string | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{
    words: string;
    title: string;
  } | null>(null);
  const [digest, setDigest] = useState("");
  const telegram = status?.channels?.telegram;
  const paired = telegram?.paired ?? null;

  // The pane reads the hub again every 3 s while it waits for the owner's
  // press in Telegram: a code that is open, or a test that is not answered
  // yet (at most three minutes after it was sent).
  const test = telegram?.last_test ?? null;
  const testSentAt = test?.sent_at && !test.answered_at ? Date.parse(test.sent_at) : NaN;
  const testWaits = Number.isFinite(testSentAt) && now - testSentAt < 180_000;
  const waits = Boolean(pairing || telegram?.pairing) && !paired ? true : testWaits;
  useEffect(() => {
    if (!waits) return;
    const timer = window.setInterval(() => {
      setNow(Date.now());
      void reach.reload();
    }, 3_000);
    return () => window.clearInterval(timer);
  }, [waits, reach.reload]);
  // The window's strip: Telegram's state, and the test while it is new.
  const health = telegram?.health;
  const stripWords = !telegram ? null
    : test?.sent_at && !test.answered_at && testWaits ? `Test sent ${wireClock(test.sent_at)}`
    : test?.answered_at && Date.now() - Date.parse(test.answered_at) < 180_000 ? `Test answered ${wireClock(test.answered_at)}`
    : health?.state === "connected" && paired ? "Telegram connected"
    : health?.state === "token_revoked" ? "Telegram: token refused"
    : health?.state === "bot_blocked" ? "Telegram: stopped in the chat"
    : health?.state === "another_desk" ? "Telegram: two desks, one bot"
    : health?.state === "unreachable" ? `Telegram not reachable${health.since ? ` since ${wireClock(health.since)}` : ""}`
    : telegram.token !== "keystore" ? "Telegram is not set up"
    : !paired ? "Telegram waits for your chat" : null;
  useEffect(() => {
    onStatus?.(stripWords);
  }, [onStatus, stripWords]);
  useEffect(() => () => onStatus?.(null), [onStatus]);
  useEffect(() => {
    if (pairing && paired) setPairing(null);
  }, [pairing, paired]);

  const run = async (key: string, act: () => Promise<void>, failed: string, stayed: string) => {
    setBusy(key);
    setRefusal(null);
    try {
      await act();
      onSaved?.();
      return true;
    } catch (cause) {
      setRefusal(plainFail(failed, cause, stayed, "Try again"));
      return false;
    } finally {
      setBusy("");
    }
  };
  const put = (patch: Record<string, unknown>) =>
    void run(
      "put",
      async () => {
        const saved = await apiFetch<ReachStatus>("/api/reach", {
          method: "PUT",
          json: patch,
        });
        reach.setData(saved);
      },
      "Reach was not saved",
      "The last choice holds",
    );
  // Telegram's acts say the hub's own sentence when it refuses.
  const telegramAct = async (key: string, act: () => Promise<void>, failed: string, saves = false) => {
    setBusy(key);
    setTelegramRefusal(null);
    try {
      await act();
      // Only an act that changes what is saved stamps the window's receipt.
      if (saves) onSaved?.();
      return true;
    } catch (cause) {
      setTelegramRefusal(hubWords(cause) ?? plainFail(failed, cause, "Nothing changed", "Try again").words);
      return false;
    } finally {
      setBusy("");
    }
  };
  const pair = () =>
    void telegramAct("pair", async () => {
      setNow(Date.now());
      setPairing(await apiFetch<Pairing>("/api/reach/telegram/pair", { method: "POST", json: {} }));
      await reach.reload();
    }, "No link was made");
  const disconnect = () =>
    telegramAct("unpair", async () => {
      await apiFetch("/api/reach/telegram/pair", { method: "DELETE" });
      setPairing(null);
      await reach.reload();
    }, "The chat was not disconnected", true);
  const removeBot = (username: string) =>
    telegramAct("remove", async () => {
      await apiFetch("/api/reach/telegram/remove", { method: "POST", json: { username } });
      setPairing(null);
      await reach.reload();
    }, "The bot was not removed", true);
  const useHere = () =>
    void telegramAct("use-here", async () => {
      await apiFetch("/api/reach/telegram/use-here", { method: "POST", json: {} });
      await reach.reload();
    }, "This desk does not read the bot yet");
  const sendTest = () =>
    void telegramAct("test", async () => {
      await apiFetch("/api/reach/telegram/test", { method: "POST", json: {} });
      setNow(Date.now());
      await reach.reload();
    }, "The test was not sent");
  const saveToken = async (value: string) => {
    setBusy("token");
    setTokenRefused(null);
    setTelegramRefusal(null);
    try {
      await apiFetch("/api/reach/telegram/token", { method: "PUT", json: { token: value } });
      await reach.reload();
      onSaved?.();
      return true;
    } catch (cause) {
      setTokenRefused(hubWords(cause) ?? plainFail("The token was not saved", cause, "Nothing changed", "Try again").words);
      return false;
    } finally {
      setBusy("");
    }
  };
  const sendDigest = () =>
    void run(
      "digest",
      async () => {
        await apiFetch("/api/reach/digest", { method: "POST", json: {} });
        setDigest("Sent to Telegram");
      },
      "No digest was sent",
      "Nothing was sent",
    );
  const kinds = reachKinds(status?.ladder.kinds);
  const level = typeof status?.ladder.kinds?.level === "string" ? String(status.ladder.kinds.level) : undefined;

  return (
    <PreferencePane label="Reach" testId="reach-settings">
      <SegmentedTabs
        label="Reach"
        value={tab}
        onChange={(id) => {
          setTab(id);
          if (id === "sends" && tab !== "sends") pickBrief("kinds");
        }}
        tabs={[
          { id: "telegram", label: "Telegram" },
          { id: "sends", label: "What it sends" },
          { id: "calls", label: "Calls" },
        ]}
      >
        {reach.error && !status ? <SurfaceState error={`Not read · ${reach.error}`} onRetry={() => void reach.reload()} /> : null}
        {refusal ? (
          <p className="gadget-fact" role="alert" title={refusal.title} data-testid="reach-refusal">
            {refusal.words}
          </p>
        ) : null}
        {tab === "telegram" ? (
          <PreferenceWell>
            <TelegramSetup
              telegram={telegram}
              pairing={pairing}
              now={now}
              busy={busy}
              tokenDraft={tokenDraft}
              onTokenDraft={setTokenDraft}
              tokenRefused={tokenRefused}
              refusal={telegramRefusal}
              sends={TELEGRAM_RUNG.find((rung) => rung.value === status?.ladder.telegram)?.label}
              quiet={status ? `${String(status.quiet_hours.start).padStart(2, "0")}:00 to ${String(status.quiet_hours.end).padStart(2, "0")}:00` : undefined}
              acts={{ saveToken, pair, disconnect, remove: removeBot, useHere, sendTest, readAgain: () => void reach.reload() }}
            />
          </PreferenceWell>
        ) : null}
        {tab === "calls" && status ? (
          <>
            <GadgetGroup label="Phone and calls">
              <GadgetRow label="Phone app" controlWidth="full">
                <span className="surface-pane-actions">
                  <DotWord tone={status.channels.phone_app.paired ? "ok" : "idle"} data-testid="reach-phone-state">
                    {status.channels.phone_app.paired ? "Paired" : (status.channels.phone_app.words ?? "No phone is paired")}
                  </DotWord>
                  <Button dense variant="secondary" onClick={() => openSurfaceOr("configure-settings", "/settings", "calls")} data-testid="reach-phone-open">
                    Open Calls settings
                  </Button>
                </span>
              </GadgetRow>
              <GadgetRow label="Line" controlWidth="full">
                <DotWord tone={status.channels.calls.ready ? "ok" : "idle"} data-testid="reach-calls-state">
                  {status.channels.calls.words ?? "Not set in Settings ▸ Calls"}
                </DotWord>
              </GadgetRow>
            </GadgetGroup>
            <ReachYouRows reach={kinds} level={level} onChanged={() => reach.reload()} />
          </>
        ) : null}
        {tab === "sends" ? (
          <div ref={briefRef} className="surface-tab-panel">
          <ListPane
            label="What it sends details"
            list={
              <PaneGroup label="What it sends">
                <ListView
                  label="Send choices"
                  rows={[
                    { id: "kinds", kind: "preference", name: "To Telegram" },
                    { id: "when", kind: "preference", name: "When to reach you" },
                    { id: "digest", kind: "preference", name: "Digest and Later" },
                    ...(cadenceTabs ?? [{ id: "cadence", label: "Notices", content: cadence }]).map((entry) => ({
                      id: entry.id,
                      kind: "preference",
                      name: entry.label,
                    })),
                  ]}
                  headerless
                  ordered
                  columns={[{ key: "name", word: "Name" }]}
                  selectedId={briefPick}
                  onSelect={pickBrief}
                  onOpen={(id) => { pickBrief(id); requestFocus((value) => value + 1); }}
                />
              </PaneGroup>
            }
          >
            {briefPick === "kinds" ? (
              <GadgetGroup label="To Telegram">
                {/* Each kind that can travel, as the hub names it: its word,
                    the words it takes, and how it goes now under Telegram's
                    rung (When to reach you). The face types none of them. */}
                {(status?.ladder.sends ?? []).map((row) => (
                  <GadgetRow
                    key={row.kind}
                    label={row.label}
                    controlWidth="standard"
                    fact={row.now !== row.mode
                      ? <DotWord tone="idle" data-testid={`reach-send-now-${row.kind}`}>Now: {row.now_words}</DotWord>
                      : row.fact ? <span data-testid={`reach-send-fact-${row.kind}`}>{row.fact}</span> : undefined}
                  >
                    <CycleGadget
                      label={row.label}
                      value={row.mode}
                      options={row.modes}
                      disabled={busy === "put" || status?.ladder.telegram === "off"}
                      onChange={(next) => put({ kinds: { [row.kind]: next } })}
                    />
                  </GadgetRow>
                ))}
                {status?.ladder.cap_words ? (
                  <GadgetRow label="Limit" controlWidth="full">
                    <span data-testid="reach-send-cap">{status.ladder.cap_words}</span>
                  </GadgetRow>
                ) : null}
                {status?.ladder.people_words ? (
                  <GadgetRow label="People" controlWidth="full">
                    <span data-testid="reach-send-people">{status.ladder.people_words}</span>
                  </GadgetRow>
                ) : null}
              </GadgetGroup>
            ) : null}
            {briefPick === "when" ? (
              <>
              <GadgetGroup label="When to reach you">
                <div className="reach-ladder" data-testid="reach-ladder">
                  {(status?.ladder.order ?? LADDER).map((rung) => {
                    if (rung === "desk") {
                      return (
                        <GadgetRow key={rung} label="Desk" controlWidth="standard">
                          <DotWord tone="ok" data-testid="reach-rung-desk">
                            At once
                          </DotWord>
                        </GadgetRow>
                      );
                    }
                    if (rung === "phone_app") {
                      return (
                        <Fragment key={rung}>
                        <GadgetRow label="Phone" controlWidth="standard">
                          <CycleGadget
                            label="Phone"
                            value={status?.channels.phone_app.on === false ? "off" : "on"}
                            options={PHONE_RUNG}
                            disabled={!status || busy === "put"}
                            onChange={(next) => put({ phone_app: next })}
                          />
                        </GadgetRow>
                        {urgentCallsDnd ? <GadgetRow label="Urgent calls" controlWidth="standard">
                          <span>Ring through Do Not Disturb</span>
                        </GadgetRow> : null}
                        </Fragment>
                      );
                    }
                    if (rung === "telegram") {
                      return (
                        <GadgetRow key={rung} label="Telegram" highlight={highlight === "reach.ladder"} controlWidth="standard">
                          <CycleGadget
                            label="Telegram"
                            value={status?.ladder.telegram ?? "at_once"}
                            options={TELEGRAM_RUNG}
                            disabled={!status || busy === "put"}
                            onChange={(next) => put({ telegram: next })}
                          />
                        </GadgetRow>
                      );
                    }
                    if (rung === "call") {
                      return (
                        <GadgetRow
                          key={rung}
                          label="Call"
                          controlWidth="standard"
                          fact={
                            <DotWord tone={status?.channels.calls.ready ? "ok" : "idle"} data-testid="reach-rung-call">
                              {status?.channels.calls.ready ? "By your rules below" : "Not set in Settings ▸ Calls"}
                            </DotWord>
                          }
                        >
                          <span />
                        </GadgetRow>
                      );
                    }
                    return null;
                  })}
                </div>
              </GadgetGroup>
                {quiet}
              </>
            ) : null}
            {briefPick === "digest" ? (
              <GadgetGroup label="Digest and Later">
                  <GadgetRow label="Daily brief" controlWidth="standard">
                    <CycleGadget
                      label="Daily brief"
                      value={status?.digest.brief ?? "on"}
                      options={BRIEF_MODES}
                      disabled={!status || busy === "put"}
                      onChange={(next) => put({ brief: next })}
                    />
                  </GadgetRow>
                  <GadgetRow label="Digest" highlight={highlight === "reach.digest"} controlWidth="standard">
                    <CycleGadget
                      label="Digest"
                      value={String(status?.digest.at ?? "end_of_quiet")}
                      options={DIGEST_TIMES}
                      disabled={!status || busy === "put"}
                      onChange={(next) =>
                        put({
                          digest: next === "end_of_quiet" ? next : Number(next),
                        })
                      }
                    />
                  </GadgetRow>
                  <GadgetRow
                    label="By hand"
                    controlWidth="standard"
                    fact={
                      digest ? (
                        <DotWord tone="ok" data-testid="reach-digest-sent">
                          {digest}
                        </DotWord>
                      ) : undefined
                    }
                  >
                    <Button
                      dense
                      variant="secondary"
                      loading={busy === "digest"}
                      disabled={!paired}
                      title={paired ? "One message to your Telegram chat" : "Connect your chat in the Telegram tab first"}
                      onClick={sendDigest}
                      data-testid="reach-digest-now"
                    >
                      Send the digest now
                    </Button>
                  </GadgetRow>
                  <GadgetRow label="Later means" highlight={highlight === "reach.later"} controlWidth="standard">
                    <CycleGadget
                      label="Later means"
                      value={status?.later_means ?? "in_2h"}
                      options={LATER_MEANS}
                      disabled={!status || busy === "put"}
                      onChange={(next) => put({ later_means: next })}
                    />
                  </GadgetRow>
              </GadgetGroup>
            ) : null}
            {(
              cadenceTabs ?? [
                {
                  id: "cadence",
                  label: "Notices",
                  content: cadence,
                  form: false,
                },
              ]
            ).map((entry) =>
              briefPick === entry.id ? (
                entry.form ? (
                  <GadgetGroup key={entry.id} label={entry.label}>{entry.content}</GadgetGroup>
                ) : (
                  <div key={entry.id} className="surface-tab-panel">
                    {entry.content}
                  </div>
                )
              ) : null,
            )}
          </ListPane>
          </div>
        ) : null}
      </SegmentedTabs>
    </PreferencePane>
  );
}

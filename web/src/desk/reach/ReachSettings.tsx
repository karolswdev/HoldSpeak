/* Settings ▸ Reach (PG-DIRECTION DIR6; DIRECTION-2026-10-31.md §9, canvas
 * canvases/direction-2026-10-31.html "Settings ▸ Reach"; ruled 2026-10-31:
 * Notices becomes Reach, and the Reach you rows move here from Settings ▸
 * Calls ▸ Phone).
 *
 * One paper, label · state · verb: the channels (Desk, Phone app, Telegram
 * with Pair Telegram in place, the bot token in the keystore, Calls), when
 * to reach you (Telegram's rung and the Reach you rows), quiet hours (the
 * one store, shared with the Phone), the digest and Later means, and the
 * Cadence and morning brief groups folded under it. The egress fact sits
 * on the Telegram row, where the choice is made (UX-CANON A.9). No modal:
 * the pairing code opens in place under its row and its dot breathes until
 * a chat pairs. */
import { useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { apiFetch } from "../../lib/api";
import { useResource } from "../../pages/pageSupport";
import { ReachYouRows } from "../calls/PhoneSettings";
import type { PhoneStatus } from "../calls/phoneTypes";
import { openSurfaceOr } from "../shell";
import { CycleGadget, GadgetGroup, GadgetRow, StringGadget } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { plainFail } from "../surface/plainFailure";
import { SurfaceState } from "../surface/Surface";
import { PreferencePane, PreferenceWell, SegmentedTabs, PaneActions, ListPane, ListView, PaneGroup, PaneInspector, InspectorForm } from "../surface";

export type ReachStatus = {
  channels: {
    desk: { words: string };
    phone_app: { on: boolean; paired: string | null; words: string };
    telegram: {
      on: boolean;
      token: "keystore" | "missing";
      destination?: string;
      paired: { name: string; at?: string | null } | null;
      pairing: { expires_at: string } | null;
    };
    calls: { ready: boolean; words: string };
  };
  ladder: {
    telegram: string;
    telegram_words?: string;
    order: string[];
    kinds: Record<string, unknown>;
  };
  quiet_hours: { start: number; end: number; now: boolean };
  digest: { at: string | number; hour: number };
  later_means: string;
  later_means_words?: string;
  open_packages: unknown[];
  later: unknown[];
};

export type Pairing = {
  code: string;
  words: string;
  expires_at: string;
  say: string;
};

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

export const TELEGRAM_EGRESS = "Messages go through Telegram's servers";

function minutesLeft(expiresAt: string, now: number): number {
  const end = Date.parse(expiresAt);
  return Number.isFinite(end) ? Math.max(0, Math.ceil((end - now) / 60_000)) : 0;
}

/** The kinds of Reach you, without the level key the hub sends beside them. */
function reachKinds(kinds: Record<string, unknown> | undefined): PhoneStatus["reach"] {
  const out: PhoneStatus["reach"] = {};
  for (const [kind, value] of Object.entries(kinds ?? {})) {
    if (kind !== "level" && value && typeof value === "object") out[kind] = value as PhoneStatus["reach"][string];
  }
  return out;
}

function TokenRow({ present, busy, highlight, onSave }: { present: boolean; busy: boolean; highlight?: boolean; onSave(value: string): Promise<boolean> }) {
  const [draft, setDraft] = useState("");
  const [changing, setChanging] = useState(false);
  const open = !present || changing;
  const save = async () => {
    if (!draft.trim()) return;
    const value = draft;
    if (await onSave(value.trim())) {
      setDraft((current) => (current === value ? "" : current));
      setChanging(false);
    }
  };
  return (
    <div className="reach-token" data-testid="reach-token" data-present={present || undefined}>
      {present && !changing ? (
        <Button dense onClick={() => setChanging(true)} data-testid="reach-token-replace">
          Replace token
        </Button>
      ) : null}
      {open ? (
        <PaneActions>
          <StringGadget
            label="Bot token"
            value={draft}
            onChange={setDraft}
            mic={false}
            type="password"
            placeholder="Bot token"
            onKeyDown={(event) => {
              if (event.key === "Enter") save();
            }}
            inputProps={{ autoComplete: "off", spellCheck: false }}
          />
          <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid="reach-token-save">
            Save
          </Button>
          {changing ? (
            <Button
              dense
              variant="ghost"
              onClick={() => {
                setChanging(false);
                setDraft("");
              }}
            >
              Cancel
            </Button>
          ) : null}
        </PaneActions>
      ) : null}
    </div>
  );
}

function PairSheet({ pairing, now, onCopy, copied }: { pairing: Pairing; now: number; onCopy(): void; copied: boolean }) {
  const left = minutesLeft(pairing.expires_at, now);
  return (
    <div className="surface-pane-actions" data-testid="reach-pair-sheet">
      <span className="reach-pair-say">
        Send <code data-testid="reach-pair-code">/pair {pairing.words}</code> to your bot
      </span>
      <DotWord tone="info" live data-testid="reach-pair-left">
        {left > 0 ? `${left} min left` : "This code is too old"}
      </DotWord>
      <Button dense variant="secondary" onClick={onCopy} data-testid="reach-pair-copy">
        {copied ? "Copied" : "Copy"}
      </Button>
    </div>
  );
}

export function ReachSettingsPane({
  highlight,
  onSaved,
  quiet,
  cadence,
  cadenceTabs,
}: {
  highlight?: string | null;
  onSaved?: () => void;
  /** Quiet hours: the one store (Settings' heartbeat rows). */
  quiet: ReactNode;
  /** The Cadence and morning brief groups, folded. */
  cadence?: ReactNode;
  cadenceTabs?: {
    id: string;
    label: string;
    content: ReactNode;
    form?: boolean;
  }[];
}) {
  const briefTarget = highlight === "reach.digest" || highlight === "reach.later" ? "digest"
    : highlight?.startsWith("cadence.brief") ? "brief" : highlight?.startsWith("cadence.") || highlight?.startsWith("cadence_telegram.") ? "cadence" : null;
  const [tab, setTab] = useState(briefTarget ? "digest" : highlight?.startsWith("heartbeat.") || highlight?.startsWith("reach.ladder") ? "timing" : "channels");
  const [briefPick, pickBrief] = useState<string | null>(briefTarget);
  const [briefOpen, openBrief] = useState<string | null>(briefTarget);
  useEffect(() => {
    if (briefTarget) {setTab("digest"); pickBrief(briefTarget); openBrief(briefTarget);}
    else if (highlight?.startsWith("heartbeat.") || highlight?.startsWith("reach.ladder")) setTab("timing");
  }, [highlight, briefTarget]);
  const reach = useResource<ReachStatus | null>("/api/reach", null);
  // A hub without the Reach routes (or any other answer) draws the rows empty.
  const status = reach.data && typeof reach.data === "object" && reach.data.channels ? reach.data : null;
  const [pairing, setPairing] = useState<Pairing | null>(null);
  const [copied, setCopied] = useState(false);
  const [now, setNow] = useState(() => Date.now());
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{
    words: string;
    title: string;
  } | null>(null);
  const [digest, setDigest] = useState("");
  const telegram = status?.channels?.telegram;
  const paired = telegram?.paired ?? null;

  // The code breathes until a chat pairs: read the hub again every 3 s.
  useEffect(() => {
    if (!pairing) return;
    const timer = window.setInterval(() => {
      setNow(Date.now());
      void reach.reload();
    }, 3_000);
    return () => window.clearInterval(timer);
  }, [pairing, reach.reload]);
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
  const pair = () =>
    void run(
      "pair",
      async () => {
        setCopied(false);
        setNow(Date.now());
        setPairing(
          await apiFetch<Pairing>("/api/reach/telegram/pair", {
            method: "POST",
            json: {},
          }),
        );
      },
      "No pairing code",
      "Nothing changed",
    );
  const unpair = () =>
    void run(
      "unpair",
      async () => {
        await apiFetch("/api/reach/telegram/pair", { method: "DELETE" });
        setPairing(null);
        await reach.reload();
      },
      "Telegram was not unpaired",
      "It stays paired",
    );
  const saveToken = (value: string) =>
    run(
      "token",
      async () => {
        await apiFetch("/api/reach/telegram/token", {
          method: "PUT",
          json: { token: value },
        });
        await reach.reload();
      },
      "The token was not saved",
      "Nothing changed",
    );
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
  const copy = () => {
    if (!pairing) return;
    void navigator.clipboard
      ?.writeText(`/pair ${pairing.code}`)
      .then(() => setCopied(true))
      .catch(() => undefined);
  };

  const telegramWord = paired ? (
    <DotWord tone="ok" data-testid="reach-telegram-state">
      {paired.name ? `Paired · ${paired.name}` : "Paired"}
    </DotWord>
  ) : pairing ? (
    <DotWord tone="info" live data-testid="reach-telegram-state">
      Waiting for your bot
    </DotWord>
  ) : (
    <DotWord tone="idle" data-testid="reach-telegram-state">
      Not paired
    </DotWord>
  );
  const kinds = reachKinds(status?.ladder.kinds);
  const level = typeof status?.ladder.kinds?.level === "string" ? String(status.ladder.kinds.level) : undefined;

  return (
    <PreferencePane label="Reach" testId="reach-settings">
      <SegmentedTabs
        label="Reach"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "channels", label: "Channels" },
          { id: "timing", label: "When" },
          { id: "calls", label: "Calls" },
          { id: "digest", label: "Brief" },
        ]}
      >
        {reach.error && !status ? <SurfaceState error={`Not read · ${reach.error}`} onRetry={() => void reach.reload()} /> : null}
        {refusal ? (
          <p className="gadget-fact" role="alert" title={refusal.title} data-testid="reach-refusal">
            {refusal.words}
          </p>
        ) : null}
        <div className="surface-tab-panel" hidden={tab !== "channels"}>
          <GadgetGroup label="Channels">
            <GadgetRow label="Desk">
              <span />
            </GadgetRow>
            <GadgetRow
              label="Phone app"
              controlWidth="standard"
              fact={
                <DotWord tone={status?.channels.phone_app.paired ? "ok" : "idle"} data-testid="reach-phone-state">
                  {status?.channels.phone_app.paired ? "" : (status?.channels.phone_app.words ?? "No phone is paired")}
                </DotWord>
              }
            >
              <Button dense variant="secondary" onClick={() => openSurfaceOr("configure-settings", "/settings", "calls")} data-testid="reach-phone-open">
                Open Calls settings
              </Button>
            </GadgetRow>
            <div data-testid="reach-telegram">
              <GadgetRow
                label="Telegram"
                highlight={highlight === "reach.telegram"}
                controlWidth="standard"
                fact={
                  <span className="surface-pane-actions">
                    {paired ? null : telegramWord}
                    <span className="gadget-fact" data-testid="reach-egress">
                      {TELEGRAM_EGRESS}
                    </span>
                  </span>
                }
              >
                <div className="surface-pane-group">
                  {status ? (
                    <TokenRow present={telegram?.token === "keystore"} busy={busy === "token"} onSave={saveToken} highlight={highlight === "reach.token"} />
                  ) : null}
                  {paired ? (
                    <Button dense variant="secondary" loading={busy === "unpair"} onClick={unpair} data-testid="reach-unpair">
                      Unpair
                    </Button>
                  ) : (
                    <Button
                      dense
                      variant={pairing ? "secondary" : "primary"}
                      loading={busy === "pair"}
                      disabled={!status || telegram?.token !== "keystore" || !telegram?.on}
                      title={telegram?.token !== "keystore" ? "Put the bot token in first" : undefined}
                      onClick={pair}
                      data-testid="reach-pair"
                    >
                      {pairing ? "New code" : "Pair Telegram"}
                    </Button>
                  )}
                </div>
              </GadgetRow>
              {pairing && !paired ? <PairSheet pairing={pairing} now={now} onCopy={copy} copied={copied} /> : null}
            </div>
            <GadgetRow
              label="Calls"
              controlWidth="standard"
              fact={
                <DotWord tone={status?.channels.calls.ready ? "ok" : "idle"} data-testid="reach-calls-state">
                  {status?.channels.calls.words ?? "Not set in Settings ▸ Calls"}
                </DotWord>
              }
            >
              <span />
            </GadgetRow>
          </GadgetGroup>
        </div>
        {tab === "timing" ? (
          <PreferenceWell>
            {/* DIR7: the ladder, its rungs in the hub's order, each with its wait. */}
            {tab === "timing" ? (
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
                        <GadgetRow key={rung} label="Phone" controlWidth="standard">
                          <CycleGadget
                            label="Phone"
                            value={status?.channels.phone_app.on === false ? "off" : "on"}
                            options={PHONE_RUNG}
                            disabled={!status || busy === "put"}
                            onChange={(next) => put({ phone_app: next })}
                          />
                        </GadgetRow>
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
            ) : null}

            {tab === "timing" ? quiet : null}
          </PreferenceWell>
        ) : null}
            {tab === "calls" && status ? <ReachYouRows reach={kinds} level={level} onChanged={() => reach.reload()} /> : null}
        {tab === "digest" ? (
          <ListPane
            label="Brief details"
            list={
              <PaneGroup label="Brief and notices">
                <ListView
                  label="Brief choices"
                  rows={[
                    {
                      id: "digest",
                      kind: "preference",
                      name: "Digest and Later",
                    },
                    ...(cadenceTabs ?? [{ id: "cadence", label: "Notices", content: cadence }]).map((entry) => ({
                      id: entry.id,
                      kind: "preference",
                      name: entry.label,
                    })),
                  ]}
                  columns={[{ key: "name", word: "Choice" }]}
                  selectedId={briefPick}
                  onSelect={pickBrief}
                  verbs={[
                    {
                      id: "open",
                      label: "Open choice",
                      key: "Enter",
                      enabled: (row) => Boolean(row),
                      run: (row) => openBrief(row!.id),
                    },
                  ]}
                  defaultVerb="open"
                />
              </PaneGroup>
            }
          >
            {briefOpen === "digest" ? (
              <PaneInspector label="Digest and Later" onClose={() => openBrief(null)}>
                <InspectorForm>
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
                    label="Send the digest now"
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
                      title={paired ? "One message to your Telegram chat" : "Pair Telegram first"}
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
                </InspectorForm>
              </PaneInspector>
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
              briefOpen === entry.id ? (
                entry.form ? (
                  <PaneInspector key={entry.id} label={entry.label} onClose={() => openBrief(null)}>
                    <InspectorForm>{entry.content}</InspectorForm>
                  </PaneInspector>
                ) : (
                  <div key={entry.id} className="surface-tab-panel">
                    {entry.content}
                    <PaneActions>
                      <Button dense onClick={() => openBrief(null)}>
                        Done
                      </Button>
                    </PaneActions>
                  </div>
                )
              ) : null,
            )}
          </ListPane>
        ) : null}
      </SegmentedTabs>
    </PreferencePane>
  );
}

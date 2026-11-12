import { ListView, GadgetRow, PaneActions, PaneGroup, ListPane, PaneInspector, InspectorForm, ActionNotice, PaneNotice } from "../surface";
/* Settings ▸ Calls: Phone holds the paired-device list and its QR inspector.
 * Phone alerts holds write-only push keys, the app build choice and Test push.
 * Reach owns call/message choices and quiet hours; Numbers owns line numbers.
 * Pairing closes when the phone_changed device frame arrives. */
import { useEffect, useRef, useState, type DragEvent, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { plainFail } from "../surface/plainFailure";
import { openSurfaceOr } from "../shell";
import { CycleGadget, GadgetGroup, PadGadget, StringGadget } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { wireWords } from "../surface/words";
import { readPushKey, removePhoneDevice, savePushKey, startPairing, testPush, usePhone, writeReach } from "./phoneApi";
import type { PhoneDevice, PhonePairing, PhonePushKey, PhonePushTest, PhoneStatus, ReachChannel } from "./phoneTypes";
import { deviceFact, pushNotReady } from "./PhonePane";
import { PhoneQr } from "./PhoneQr";


export const PHONE_EGRESS_SENTENCE = "A message goes to your phone through Apple's push service. A call on the number goes through your line's carrier. The words of a call stay on your home engine.";

/** The kinds that may reach him (§6, `phone_rules.KINDS`), in the design's
 *  order, in his words. */
export const REACH_KINDS: ReadonlyArray<{
  kind: string;
  label: string;
  note?: string;
  short?: string;
}> = [
  {
    kind: "core_question",
    label: "A program asks you",
    short: "Program question",
    note: "a call follows after 10 min with no reply when it may call",
  },
  { kind: "step_red", label: "A program step stays red", short: "Failed step" },
  { kind: "program_done", label: "A program is done", short: "Program done" },
  {
    kind: "heartbeat_security",
    label: "A security or data-loss finding",
    short: "Security",
  },
  {
    kind: "aftercare",
    label: "A meeting's follow-up asks",
    short: "Follow-up",
  },
  {
    kind: "agent_question",
    label: "An agent asks what only you know",
    short: "Agent question",
  },
];

const CHANNELS: ReadonlyArray<{ value: ReachChannel; word: string }> = [
  { value: "message", word: "Message" },
  { value: "call", word: "Call" },
  { value: "nothing", word: "Nothing" },
];

const LEVEL_WORDS: Record<string, string> = {
  secure: "Secure",
  normal: "Normal",
  yolo: "YOLO",
  owner: "Owner",
};

export function levelWord(level: string | undefined): string {
  const key = String(level ?? "normal").toLowerCase();
  return LEVEL_WORDS[key] ?? wireWords(key);
}

/** His own words over the level's: the map Reach you writes. */
export function ownReach(status: PhoneStatus | null): Record<string, ReachChannel> {
  const out: Record<string, ReachChannel> = {};
  for (const [kind, choice] of Object.entries(status?.reach ?? {})) if (choice.own) out[kind] = choice.word;
  return out;
}

function minutesLeft(expiresAt: string, now: number): number {
  const end = Date.parse(expiresAt);
  return Number.isFinite(end) ? Math.max(0, Math.ceil((end - now) / 60_000)) : 0;
}

function Row({ name, fact, verb, testId }: { name: ReactNode; fact?: ReactNode; verb?: ReactNode; testId?: string }) {
  return (
    <div data-testid={testId}>
      <GadgetRow label={name} fact={fact}>
        {verb ?? <span />}
      </GadgetRow>
    </div>
  );
}

function PairSheet({pairing, now, busy, onNew, onCancel}: {pairing: PhonePairing; now: number; busy: boolean; onNew(): void; onCancel(): void}) {
  const left = minutesLeft(pairing.expires_at, now);
  return <InspectorForm testId="phone-pair-sheet" rows={[
    {label: "Code", control: <PhoneQr text={pairing.qr_payload} />},
  ]} notice={<PaneActions><span className="gadget-fact">Scan with HoldSpeak on your phone</span><span data-testid="phone-pair-left">{left > 0 ? `Good for ${left} more ${left === 1 ? "minute" : "minutes"}` : "This code is too old"}</span></PaneActions>} completion={{cancel: onCancel, cancelDisabled: busy, cancelTestId: "phone-pair-cancel", primary: {label: "New code", run: onNew, busy, testId: "phone-pair-new"}}} />;
}

type Tone = "ok" | "info" | "warn" | "idle" | "fail";

/** Where the app on his phone was built from: Apple's host for its token. */
export const PUSH_HOSTS: ReadonlyArray<{ value: string; label: string }> = [
  { value: "app_store", label: "App Store" },
  { value: "development", label: "Xcode" },
];

/** The Test push's answer in his words (`POST /api/phone/push/test`). */
export function pushTestWords(result: PhonePushTest): {
  word: string;
  tone: Tone;
} {
  if (result.answer === "accepted") return { word: "Apple accepted it", tone: "ok" };
  if (result.answer === "stale") {
    return {
      word: "This phone's token is stale: open the app once. If this is an Xcode build, pick Xcode under Builds from",
      tone: "warn",
    };
  }
  if (result.answer === "refused")
    return {
      word: "Apple refused the key: check the Key ID and Team ID",
      tone: "fail",
    };
  if (!result.status) return { word: "The hub could not reach Apple", tone: "fail" };
  return {
    word: `Apple answered ${result.status}${result.reason ? `: ${result.reason}` : ""}`,
    tone: "fail",
  };
}

/** A .p8 file dropped on the pad: its text. */
async function droppedText(event: DragEvent): Promise<string> {
  const file = event.dataTransfer?.files?.[0];
  return file ? (await file.text()).trim() : "";
}

/** One write-only part of the key: where it is, never its value; Change
 *  opens the field again. The .p8 is a pad that takes a paste or a drop. */
function PushSecret({label, present, pad, busy, draft, onDraft, onSave, onCancel, testId}: {
  label: string; present: boolean; pad?: boolean; busy: boolean; draft: string; onDraft(value: string): void; onSave(): void; onCancel(): void; testId: string;
}) {
  const generation = useRef(0);
  useEffect(() => { generation.current += 1; return () => { generation.current += 1; }; }, [label]);
  return <InspectorForm testId={`${testId}-editor`} rows={[
    {label, control: pad ? <span className="surface-input-well" data-testid={`${testId}-drop`} onDragOver={(event) => event.preventDefault()} onDrop={(event) => {
      event.preventDefault(); const target = generation.current; void droppedText(event).then((text) => { if (text && generation.current === target) onDraft(text); });
    }}><PadGadget label={label} value={draft} onChange={onDraft} rows={3} placeholder="Paste or drop the .p8 file" inputProps={{spellCheck: false}} /></span>
      : <StringGadget label={label} value={draft} onChange={onDraft} placeholder="Kept in your keystore" onKeyDown={(event) => {if (event.key === "Enter") onSave();}} inputProps={{autoComplete: "off", spellCheck: false}} />},
  ]} notice={present ? "Stored in your keystore" : "Missing"} completion={{cancel: onCancel, cancelDisabled: busy, primary: {label: "Save", run: onSave, busy, disabled: busy || !draft.trim(), testId: `${testId}-save`}}} />;
}

/** Settings ▸ Calls ▸ Phone ▸ Push (PHONE-APNS-KEY): his Apple push key,
 *  its Key ID and Team ID (write only, in the hub's keystore), the app's
 *  bundle id, and Test push with Apple's answer. */
function PushGroup({ devices, onChanged }: { devices: PhoneDevice[]; onChanged(): void }) {
  const [key, setKey] = useState<PhonePushKey | null>(null);
  const [busy, setBusy] = useState("");
  const [bundle, setBundle] = useState("");
  const [pickedKey, pickKey] = useState<string | null>(null);
  const [editingKey, editKey] = useState<string | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const draftsRef = useRef(drafts);
  const draft = (part: string, value: string) => { draftsRef.current = {...draftsRef.current, [part]: value}; setDrafts(draftsRef.current); };
  const [result, setResult] = useState<PhonePushTest | null>(null);
  const [refusal, setRefusal] = useState<{
    words: string;
    title: string;
  } | null>(null);
  useEffect(() => {
    let alive = true;
    readPushKey()
      .then((next) => {
        if (alive) {
          setKey(next);
          setBundle(next.bundle_id);
        }
      })
      .catch(() => undefined);
    return () => {
      alive = false;
    };
  }, []);
  if (!key) return null;
  const save = async (part: string, value: string): Promise<boolean> => {
    setBusy(part);
    setRefusal(null);
    setResult(null);
    try {
      const next = await savePushKey({ [part]: value });
      setKey(next);
      setBundle(next.bundle_id);
      onChanged();
      return true;
    } catch (cause) {
      setRefusal(plainFail("The key was not saved", cause, "Nothing changed", "Try again"));
      return false;
    } finally {
      setBusy("");
    }
  };
  const test = () => {
    setBusy("test");
    setRefusal(null);
    setResult(null);
    testPush()
      .then(setResult)
      .catch((cause) => setRefusal(plainFail("No test push", cause, "Nothing was sent", "Try again")))
      .finally(() => setBusy(""));
  };
  const secretRows = [
    {id: "p8", label: "Apple push key (.p8)", present: key.present.p8, testId: "phone-push-p8", pad: true},
    {id: "key_id", label: "Key ID", present: key.present.key_id, testId: "phone-push-key-id"},
    {id: "team_id", label: "Team ID", present: key.present.team_id, testId: "phone-push-team-id"},
  ];
  const secret = secretRows.find((row) => row.id === editingKey);
  const saveSecret = async (part: string) => {
    const value = draftsRef.current[part] ?? "";
    if (!value.trim() || busy) return;
    if (await save(part, value.trim()) && draftsRef.current[part] === value) {
      draft(part, ""); editKey((current) => current === part ? null : current);
    }
  };
  const ready = key.push_state === "ready";
  const reachable = devices.some((device) => device.has_push);
  const words = result ? pushTestWords(result) : null;
  return (
    <div className="surface-tab-panel" data-testid="phone-push">
      {refusal ? (
        <span role="alert" title={refusal.title} data-testid="phone-push-refusal">
          {refusal.words}
        </span>
      ) : null}
      <ListPane label="Push key" list={<PaneGroup label="Push keys">
        <ListView label="Push keys" rows={secretRows.map((row) => ({id: row.id, kind: "credential", name: row.label,
          cells: {stored: <span data-testid={`${row.testId}-place`}>{row.present ? "Stored in your keystore" : "Missing"}</span>},
        }))} columns={[{key: "name", word: "Key", priority: 100}, {key: "stored", word: "Storage", priority: 20}]} selectedId={pickedKey} onSelect={pickKey}
          rowProps={(item) => ({"data-testid": secretRows.find((row) => row.id === item.id)!.testId})}
          verbs={[{id: "change", label: "Change key…", key: "Enter", enabled: (row) => Boolean(row) && !busy, run: (row) => editKey(row!.id)}]} defaultVerb="change" />
      </PaneGroup>}>
        {secret ? <PaneInspector label={secret.label}><PushSecret key={secret.id} {...secret} draft={drafts[secret.id] ?? ""} onDraft={(value) => draft(secret.id, value)} busy={busy === secret.id} onSave={() => void saveSecret(secret.id)} onCancel={() => { draft(secret.id, ""); editKey(null); }} /></PaneInspector> : <>
        <InspectorForm fit="rows" rows={[
          {label: "App bundle ID", control: <div data-testid="phone-push-bundle"><PaneActions>
            <StringGadget label="App bundle ID" value={bundle} onChange={setBundle} inputProps={{autoComplete:"off",spellCheck:false}} />
            <Button dense variant="secondary" loading={busy === "bundle_id"} disabled={!bundle.trim() || bundle.trim() === key.bundle_id}
              onClick={() => save("bundle_id", bundle.trim())} data-testid="phone-push-bundle-save">Save</Button>
          </PaneActions></div>},
          {label: "Builds from", control: <div data-testid="phone-push-host"><CycleGadget label="Builds from" value={key.host ?? "app_store"} options={[...PUSH_HOSTS]} disabled={busy === "host"} onChange={(next) => save("host", next)} /></div>},
          {label: "Push", control: <div data-testid="phone-push-test"><PaneActions>
            <Button dense variant="secondary" loading={busy === "test"} disabled={!ready || !reachable} onClick={test}
              title="A silent push to your phone through Apple's push service" data-testid="phone-push-test-press">Test push</Button>
            {words ? <DotWord tone={words.tone} data-testid="phone-push-answer" title={result?.reason || undefined}>{words.word}</DotWord>
              : ready ? reachable ? null : <DotWord tone="warn">No phone sent a push token</DotWord>
              : <DotWord tone="idle">Save the key, the Key ID and the Team ID</DotWord>}
          </PaneActions></div>},
        ]} />
        </>}
      </ListPane>
    </div>
  );
}

/** Settings ▸ Reach ▸ When to reach you (PG-DIRECTION DIR6; moved from
 *  Settings ▸ Calls ▸ Phone): a table of kinds × Message · Call · Nothing,
 *  prefilled by the Control level; a choice is his own word over the
 *  level's (`calls.phone_reach`, the Phone's reach rules read it). */
export function ReachYouRows({
  reach,
  level: levelKey,
  onChanged,
}: {
  reach: PhoneStatus["reach"] | undefined;
  level: string | undefined;
  onChanged(): void | Promise<unknown>;
}) {
  const [chosen, setChosen] = useState<Record<string, ReachChannel>>({});
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{
    words: string;
    title: string;
  } | null>(null);
  const status = { reach } as PhoneStatus;
  const run = async (key: string, act: () => Promise<void>, failed: (cause: unknown) => { words: string; title: string }) => {
    setBusy(key);
    setRefusal(null);
    try {
      await act();
    } catch (error) {
      setRefusal(failed(error));
    } finally {
      setBusy("");
    }
  };
  const choose = (kind: string, channel: ReachChannel) =>
    void run(
      `reach-${kind}`,
      async () => {
        const own = { ...ownReach(status), ...chosen, [kind]: channel };
        await writeReach(own);
        setChosen(own);
        await onChanged();
      },
      (cause) => plainFail("Reach you was not saved", cause, "The last choice holds", "Try again"),
    );
  const followLevel = () =>
    void run(
      "reach-reset",
      async () => {
        await writeReach({});
        setChosen({});
        await onChanged();
      },
      (cause) => plainFail("Reach you was not saved", cause, "The last choices hold", "Try again"),
    );
  const level = levelWord(levelKey);
  const own = { ...ownReach(status), ...chosen };
  const rows = REACH_KINDS.map((entry) => {
    const sent = reach?.[entry.kind];
    return {
      ...entry,
      channel: (own[entry.kind] ?? sent?.level_word ?? sent?.word ?? "message") as ReachChannel,
      own: entry.kind in own,
    };
  });
  return (
    <>
      {refusal ? (
        <ActionNotice tone="danger" role="alert"><span title={refusal.title} data-testid="phone-settings-refusal">{refusal.words}</span></ActionNotice>
      ) : null}
      <PaneGroup label="Reach you">
        <ListView label="When to call" ordered rows={rows.map((row) => ({
          id: row.kind, kind: "preference", name: row.short ?? row.label,
          cells: {channel: <CycleGadget label={row.label} value={row.channel} disabled={Boolean(busy)}
            options={CHANNELS.map((channel) => ({value: channel.value, label: channel.word}))} onChange={(next) => choose(row.kind, next as ReachChannel)} />},
        }))} columns={[{key: "name", word: "When", priority: 100}, {key: "channel", word: "Reach", priority: 100, minWidth: 140}]}
          rowProps={(item) => {const row = rows.find((row) => row.kind === item.id)!; return {"data-testid": "phone-reach-row", "data-kind": row.kind, "data-channel": row.channel, "data-own": row.own || undefined, title: [row.label, row.note].filter(Boolean).join(" · ")};}} />
        <PaneActions>
          <span data-testid="phone-reach-level">{Object.keys(own).length ? `Your choices over Control: ${level}` : `Set by Control: ${level}`}</span>
          {Object.keys(own).length ? <Button variant="ghost" dense loading={busy === "reach-reset"} onClick={followLevel} data-testid="phone-reach-reset">Use the {level} set</Button> : null}
        </PaneActions>
      </PaneGroup>
    </>
  );
}

export function PhoneSettingsPane({ alertsOpen, showEgress = true }: { alertsOpen?: boolean; showEgress?: boolean } = {}) {
  const phone = usePhone(true, false);
  const status = phone.status;
  const [pairing, setPairing] = useState<PhonePairing | null>(null);
  const [pairedAt, setPairedAt] = useState(0);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{
    words: string;
    title: string;
  } | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const paired = (status?.devices ?? []).filter((device) => device.state === "paired");
  useEffect(() => {
    if (!pairing) return;
    const timer = window.setInterval(() => setNow(Date.now()), 15_000);
    return () => window.clearInterval(timer);
  }, [pairing]);
  // The sheet closes by itself when a phone pairs after it opened.
  useEffect(() => {
    if (pairing && paired.length > pairedAt) setPairing(null);
  }, [pairing, paired.length, pairedAt]);

  const run = async (key: string, act: () => Promise<void>, failed: (cause: unknown) => { words: string; title: string }) => {
    setBusy(key);
    setRefusal(null);
    try {
      await act();
    } catch (error) {
      setRefusal(failed(error));
    } finally {
      setBusy("");
    }
  };
  const pair = () =>
    void run(
      "pair",
      async () => {
        setPairedAt(paired.length);
        setNow(Date.now());
        setPairing(await startPairing());
      },
      (cause) => plainFail("No pairing code", cause, "Nothing changed", "Try again"),
    );
  const remove = (id: string) =>
    void run(
      `remove-${id}`,
      async () => {
        await removePhoneDevice(id);
        await phone.reload();
      },
      (cause) => plainFail("The phone was not removed", cause, "It stays paired", "Try again"),
    );

  return (
    <div className="surface-preference-pane" data-testid="phone-settings" aria-busy={phone.loading || undefined}>
      {refusal ? (
        <ActionNotice tone="danger" role="alert"><span title={refusal.title} data-testid="phone-settings-refusal">{refusal.words}</span></ActionNotice>
      ) : null}
      {!phone.loading && !status ? (
        <PaneNotice><span data-testid="phone-off">Phone is off on this desk.</span></PaneNotice>
      ) : null}
      <div className="surface-tab-panel" hidden={alertsOpen === true}>
        <ListPane label="Phone" list={<PaneGroup label="Your phone">
          <ListView label="Paired phones" rows={paired.map((device) => ({id: device.id, kind: "phone", name: device.name, cells: {
            needs: pushNotReady(device) ? <DotWord tone="warn" data-testid="phone-device-push" title={deviceFact(device)}>{pushNotReady(device)}</DotWord> : "",
          }}))} rowProps={() => ({"data-testid": "phone-device-row"})} columns={[{key: "name", word: "Phone", priority: 100}, {key: "needs", word: "Needs you", priority: 20}]}
            verbs={[
              {id: "pair", label: "Pair a phone", symbol: "+", testId: "phone-pair", enabled: () => Boolean(status) && !busy, run: pair},
              {id: "remove", label: "Remove phone", symbol: "−", enabled: (row) => Boolean(row) && !busy, run: (row) => remove(row!.id)},
            ]} />
        </PaneGroup>}>
          {pairing ? <PaneInspector label="Pair phone"><PairSheet pairing={pairing} now={now} busy={busy === "pair"} onNew={pair} onCancel={() => setPairing(null)} /></PaneInspector>
            : <GadgetGroup label="Reach you"><Row testId="phone-reach-moved" name="Reach you" verb={<Button dense variant="secondary" onClick={() => openSurfaceOr("configure-settings", "/settings", "reach")} data-testid="phone-reach-open">Open Reach</Button>} /></GadgetGroup>}
        </ListPane>
      </div>
      <div className="surface-tab-panel" hidden={alertsOpen === false}>{status ? <PushGroup devices={paired} onChanged={() => void phone.reload()} /> : null}</div>
      {showEgress ? <GadgetRow label="Phone"><span data-testid="phone-egress">Apple push · Carrier · Home engine</span></GadgetRow> : null}
    </div>
  );
}

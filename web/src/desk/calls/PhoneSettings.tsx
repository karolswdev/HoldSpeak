/* Settings ▸ Calls ▸ Phone (PHONE-DESIGN-2026-10-28 §9; canvas
 * docs/internal/betterment/phone/canvases/phone-2026-10-28.html): the
 * Accounts grammar — one paper, one grid per group (Your phone, Reach you,
 * Quiet hours, The number), name · state · verb.
 *
 * Pair a phone opens the QR sheet in place under its row (never a modal);
 * the QR is drawn here from the hub's pair payload (the hub sends no PNG).
 * The sheet closes by itself when the phone pairs (the `phone_changed`
 * device frame). Reach you is a table of kinds × Message · Call · Nothing,
 * prefilled by the Control level; a choice is his own word over the
 * level's. Quiet hours are the desk's Rhythm hours, read here and changed
 * in Rhythm. Egress is said here once (UX-CANON A.9). */
import { useEffect, useState, type DragEvent, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { plainFail } from "../surface/plainFailure";
import { openSurfaceOr } from "../shell";
import { CheckGadget, GadgetGroup, MxRadio, PadGadget, StringGadget } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { stateWords } from "../surface/words";
import { readPushKey, removePhoneDevice, savePushKey, startPairing, testPush, usePhone, writeReach } from "./phoneApi";
import type { PhoneDevice, PhonePairing, PhonePushKey, PhonePushTest, PhoneStatus, ReachChannel } from "./phoneTypes";
import { deviceFact, pushNotReady } from "./PhoneWing";
import { PhoneQr } from "./PhoneQr";
import "./phone.css";

export const PHONE_EGRESS_SENTENCE =
  "A message goes to your phone through Apple's push service. A call on the number goes through your line's carrier. The words of a call stay on your home engine.";

/** The kinds that may reach him (§6, `phone_rules.KINDS`), in the design's
 *  order, in his words. */
export const REACH_KINDS: ReadonlyArray<{ kind: string; label: string; note?: string }> = [
  { kind: "core_question", label: "A program asks you", note: "a call follows after 10 min with no reply when it may call" },
  { kind: "step_red", label: "A program step stays red" },
  { kind: "program_done", label: "A program is done" },
  { kind: "heartbeat_security", label: "A security or data-loss finding" },
  { kind: "aftercare", label: "A meeting's follow-up asks" },
  { kind: "agent_question", label: "An agent asks what only you know" },
];

const CHANNELS: ReadonlyArray<{ value: ReachChannel; word: string }> = [
  { value: "message", word: "Message" },
  { value: "call", word: "Call" },
  { value: "nothing", word: "Nothing" },
];

const LEVEL_WORDS: Record<string, string> = { secure: "Secure", normal: "Normal", yolo: "YOLO", owner: "Owner" };

export function levelWord(level: string | undefined): string {
  const key = String(level ?? "normal").toLowerCase();
  return LEVEL_WORDS[key] ?? stateWords(key.toUpperCase());
}

/** `22:00 to 08:00` from the Rhythm hours. */
export function quietWords(quiet: PhoneStatus["quiet_hours"] | undefined): string {
  if (!quiet) return "";
  const hour = (value: number) => `${String(Math.max(0, Math.min(23, Math.floor(value)))).padStart(2, "0")}:00`;
  return `${hour(quiet.start)} to ${hour(quiet.end)}`;
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
    <div className="phone-row" data-testid={testId}>
      <span className="phone-row-name">{name}</span>
      <span className="phone-row-fact">{fact}</span>
      <span className="phone-row-verb">{verb}</span>
    </div>
  );
}

function PairSheet({ pairing, now, busy, onNew }: { pairing: PhonePairing; now: number; busy: boolean; onNew(): void }) {
  const left = minutesLeft(pairing.expires_at, now);
  return (
    <div className="phone-pair" data-testid="phone-pair-sheet">
      <PhoneQr text={pairing.qr_payload} />
      <div className="phone-pair-say">
        <b>Scan this with the HoldSpeak app</b>
        <ol>
          <li>Open HoldSpeak on your phone.</li>
          <li>Tap Pair with a desk.</li>
          <li>Point the camera at this code.</li>
        </ol>
        <span>Remove the phone here at any time.</span>
        <span className="phone-pair-left" data-testid="phone-pair-left">
          {left > 0 ? `Good for ${left} more ${left === 1 ? "minute" : "minutes"}` : "This code is too old"}
          <Button variant="ghost" dense loading={busy} onClick={onNew} data-testid="phone-pair-new">New code</Button>
        </span>
      </div>
    </div>
  );
}

type Tone = "ok" | "info" | "warn" | "idle" | "fail";

/** The Test push's answer in his words (`POST /api/phone/push/test`). */
export function pushTestWords(result: PhonePushTest): { word: string; tone: Tone } {
  if (result.answer === "accepted") return { word: "Apple accepted it", tone: "ok" };
  if (result.answer === "stale") return { word: "This phone's token is stale: open the app once", tone: "warn" };
  if (result.answer === "refused") return { word: "Apple refused the key: check the Key ID and Team ID", tone: "fail" };
  if (!result.status) return { word: "The hub could not reach Apple", tone: "fail" };
  return { word: `Apple answered ${result.status}${result.reason ? `: ${result.reason}` : ""}`, tone: "fail" };
}

/** A .p8 file dropped on the pad: its text. */
async function droppedText(event: DragEvent): Promise<string> {
  const file = event.dataTransfer?.files?.[0];
  return file ? (await file.text()).trim() : "";
}

/** One write-only part of the key: where it is, never its value; Change
 *  opens the field again. The .p8 is a pad that takes a paste or a drop. */
function PushSecret({ label, present, pad = false, busy, onSave, testId }: {
  label: string; present: boolean; pad?: boolean; busy: boolean; onSave(value: string): void; testId: string;
}) {
  const [draft, setDraft] = useState("");
  const [changing, setChanging] = useState(false);
  const open = !present || changing;
  const save = () => {
    if (!draft.trim()) return;
    onSave(draft.trim());
    setDraft("");
    setChanging(false);
  };
  return (
    <div className="phone-secret" data-testid={testId} data-present={present || undefined}>
      <Row name={label}
        fact={<DotWord tone={present ? "ok" : "idle"} data-testid={`${testId}-place`}>{present ? "Stored in your keystore" : "Missing"}</DotWord>}
        verb={present && !changing
          ? <Button dense variant="secondary" onClick={() => setChanging(true)} data-testid={`${testId}-change`}>Change</Button>
          : null} />
      {open ? (
        <div className="phone-field">
          {pad ? (
            <span className="phone-drop" data-testid={`${testId}-drop`}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => { event.preventDefault(); void droppedText(event).then((text) => { if (text) setDraft(text); }); }}>
              <PadGadget label={label} value={draft} onChange={setDraft} rows={4}
                placeholder="Paste the .p8 file here, or drop it here" inputProps={{ spellCheck: false }} />
            </span>
          ) : (
            <StringGadget label={label} value={draft} onChange={setDraft} placeholder="Kept in your keystore"
              onKeyDown={(event) => { if (event.key === "Enter") save(); }} inputProps={{ autoComplete: "off", spellCheck: false }} />
          )}
          <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid={`${testId}-save`}>Save</Button>
          {changing ? <Button dense variant="ghost" onClick={() => { setChanging(false); setDraft(""); }}>Cancel</Button> : null}
        </div>
      ) : null}
    </div>
  );
}

/** Settings ▸ Calls ▸ Phone ▸ Push (PHONE-APNS-KEY): his Apple push key,
 *  its Key ID and Team ID (write only, in the hub's keystore), the app's
 *  bundle id, and Test push with Apple's answer. */
function PushGroup({ devices, onChanged }: { devices: PhoneDevice[]; onChanged(): void }) {
  const [key, setKey] = useState<PhonePushKey | null>(null);
  const [busy, setBusy] = useState("");
  const [bundle, setBundle] = useState("");
  const [result, setResult] = useState<PhonePushTest | null>(null);
  const [refusal, setRefusal] = useState<{ words: string; title: string } | null>(null);
  useEffect(() => {
    let alive = true;
    readPushKey().then((next) => { if (alive) { setKey(next); setBundle(next.bundle_id); } }).catch(() => undefined);
    return () => { alive = false; };
  }, []);
  if (!key) return null;
  const save = (part: string, value: string) => {
    setBusy(part);
    setRefusal(null);
    setResult(null);
    savePushKey({ [part]: value })
      .then((next) => { setKey(next); setBundle(next.bundle_id); onChanged(); })
      .catch((cause) => setRefusal(plainFail("The key was not saved", cause, "Nothing changed", "Try again")))
      .finally(() => setBusy(""));
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
  const ready = key.push_state === "ready";
  const reachable = devices.some((device) => device.has_push);
  const words = result ? pushTestWords(result) : null;
  return (
    <GadgetGroup material="inset" label="Push">
      <div data-testid="phone-push">
        <PushSecret label="Apple push key (.p8)" present={key.present.p8} pad busy={busy === "p8"}
          onSave={(value) => save("p8", value)} testId="phone-push-p8" />
        <PushSecret label="Key ID" present={key.present.key_id} busy={busy === "key_id"}
          onSave={(value) => save("key_id", value)} testId="phone-push-key-id" />
        <PushSecret label="Team ID" present={key.present.team_id} busy={busy === "team_id"}
          onSave={(value) => save("team_id", value)} testId="phone-push-team-id" />
        <div className="phone-secret" data-testid="phone-push-bundle">
          <Row name="App bundle ID" fact="The HoldSpeak app on your phone" />
          <div className="phone-field">
            <StringGadget label="App bundle ID" value={bundle} onChange={setBundle}
              inputProps={{ autoComplete: "off", spellCheck: false }} />
            <Button dense variant="secondary" loading={busy === "bundle_id"} disabled={!bundle.trim() || bundle.trim() === key.bundle_id}
              onClick={() => save("bundle_id", bundle.trim())} data-testid="phone-push-bundle-save">Save</Button>
          </div>
        </div>
        <Row testId="phone-push-test" name="Test push"
          fact={words ? <DotWord tone={words.tone} data-testid="phone-push-answer" title={result?.reason || undefined}>{words.word}</DotWord>
            : refusal ? <DotWord tone="fail" data-testid="phone-push-refusal" title={refusal.title}>{refusal.words}</DotWord>
              : ready ? <DotWord tone="ok">{reachable ? "Ready" : "No phone sent a push token"}</DotWord>
                : <DotWord tone="idle">Save the key, the Key ID and the Team ID</DotWord>}
          verb={<Button dense variant="secondary" loading={busy === "test"} disabled={!ready || !reachable} onClick={test}
            title="A silent push to your phone through Apple's push service" data-testid="phone-push-test-press">Test push</Button>} />
      </div>
    </GadgetGroup>
  );
}

export function PhoneSettingsPane() {
  const phone = usePhone(true, false);
  const status = phone.status;
  const [pairing, setPairing] = useState<PhonePairing | null>(null);
  const [pairedAt, setPairedAt] = useState(0);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState<{ words: string; title: string } | null>(null);
  const [now, setNow] = useState(() => Date.now());
  const [chosen, setChosen] = useState<Record<string, ReachChannel>>({});

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
    try { await act(); } catch (error) {
      setRefusal(failed(error));
    } finally { setBusy(""); }
  };
  const pair = () => void run("pair", async () => {
    setPairedAt(paired.length);
    setNow(Date.now());
    setPairing(await startPairing());
  }, (cause) => plainFail("No pairing code", cause, "Nothing changed", "Try again"));
  const remove = (id: string) => void run(`remove-${id}`, async () => {
    await removePhoneDevice(id);
    await phone.reload();
  }, (cause) => plainFail("The phone was not removed", cause, "It stays paired", "Try again"));
  const choose = (kind: string, channel: ReachChannel) => void run(`reach-${kind}`, async () => {
    const own = { ...ownReach(status), ...chosen, [kind]: channel };
    setChosen(own);
    await writeReach(own);
    await phone.reload();
  }, (cause) => plainFail("Reach you was not saved", cause, "The last choice holds", "Try again"));
  const followLevel = () => void run("reach-reset", async () => {
    setChosen({});
    await writeReach({});
    await phone.reload();
  }, (cause) => plainFail("Reach you was not saved", cause, "The last choices hold", "Try again"));

  const level = levelWord(status?.level);
  const own = { ...ownReach(status), ...chosen };
  const rows = REACH_KINDS.map((entry) => {
    const sent = status?.reach?.[entry.kind];
    return { ...entry, channel: (own[entry.kind] ?? sent?.level_word ?? sent?.word ?? "message") as ReachChannel, own: entry.kind in own };
  });

  return (
    <div className="phone-settings" data-testid="phone-settings" aria-busy={phone.loading || undefined}>
      {refusal ? <p className="phone-refusal" role="alert" title={refusal.title} data-testid="phone-settings-refusal">{refusal.words}</p> : null}
      {!phone.loading && !status ? (
        <p className="phone-egress" data-testid="phone-off">Phone is off on this desk.</p>
      ) : null}
      <GadgetGroup material="inset" label="Your phone">
        <div data-testid="phone-devices">
          {paired.map((device) => (
            <Row key={device.id} testId="phone-device-row"
              name={<><span className="phone-handset" aria-hidden="true"><i /></span>{device.name}</>}
              fact={pushNotReady(device)
                ? <DotWord tone="warn" data-testid="phone-device-push" title={deviceFact(device)}>{pushNotReady(device)}</DotWord>
                : <DotWord tone="ok">{deviceFact(device) || stateWords("PAIRED")}</DotWord>}
              verb={<Button dense variant="secondary" loading={busy === `remove-${device.id}`} onClick={() => remove(device.id)}
                data-testid="phone-device-remove">Remove</Button>} />
          ))}
          {pairing ? (
            <>
              <Row name={paired.length ? "Another phone" : "No phone paired"}
                fact={<DotWord tone="info">{stateWords("PAIRING")}</DotWord>}
                verb={<Button dense variant="secondary" onClick={() => setPairing(null)} data-testid="phone-pair-cancel">Cancel</Button>} />
              <PairSheet pairing={pairing} now={now} busy={busy === "pair"} onNew={pair} />
            </>
          ) : (
            <Row testId="phone-pair-row" name={paired.length ? "Another phone" : "No phone paired"}
              verb={<Button dense variant={paired.length ? "secondary" : "primary"} loading={busy === "pair"} disabled={!status}
                onClick={pair} data-testid="phone-pair">Pair a phone</Button>} />
          )}
        </div>
      </GadgetGroup>
      {status ? <PushGroup devices={paired} onChanged={() => void phone.reload()} /> : null}
      <GadgetGroup material="inset" label="Reach you">
        <div className="phone-reach" data-testid="phone-reach">
          <span className="phone-reach-head">When</span>
          {CHANNELS.map((channel) => <span key={channel.value} className="phone-reach-head" aria-hidden="true">{channel.word}</span>)}
          {rows.map((row) => (
            <div key={row.kind} className="phone-reach-line" data-testid="phone-reach-row" data-kind={row.kind}
              data-channel={row.channel} data-own={row.own || undefined}>
              <span className="phone-reach-kind">{row.label}{row.note ? <span>{row.note}</span> : null}</span>
              <MxRadio
                label={row.label}
                value={row.channel}
                onChange={(next) => choose(row.kind, next as ReachChannel)}
                options={CHANNELS.map((channel) => ({ value: channel.value, label: <span className="phone-reach-word">{channel.word}</span> }))}
              />
            </div>
          ))}
        </div>
        <div className="phone-reach-foot">
          <span data-testid="phone-reach-level">
            {Object.keys(own).length ? `Your choices over Control: ${level}` : `Set by Control: ${level}`}
          </span>
          {Object.keys(own).length ? (
            <Button variant="ghost" dense loading={busy === "reach-reset"} onClick={followLevel} data-testid="phone-reach-reset">
              Use the {level} set
            </Button>
          ) : null}
        </div>
      </GadgetGroup>
      <GadgetGroup material="inset" label="Quiet hours">
        <Row testId="phone-quiet"
          name={quietWords(status?.quiet_hours) || "22:00 to 08:00"}
          fact={status?.quiet_hours?.now ? "Quiet now. Messages wait. Only urgent calls ring." : "Messages wait. Only urgent calls ring."}
          verb={<Button dense variant="secondary" onClick={() => openSurfaceOr("configure-settings", "/settings", "rhythm")}
            data-testid="phone-quiet-rhythm">Change in Rhythm</Button>} />
        <Row testId="phone-urgent"
          name="Urgent calls ring through Do Not Disturb"
          fact={status?.urgent_dnd ? "A security or data-loss call rings through" : "Until Apple allows it, an urgent call rings once more after 1 min"}
          verb={<CheckGadget label={status?.urgent_dnd ? "On" : "Off"} checked={Boolean(status?.urgent_dnd)} disabled onChange={() => undefined} />} />
      </GadgetGroup>
      <GadgetGroup material="inset" label="The number">
        <Row testId="phone-number"
          name="Your number"
          fact={<DotWord tone={status?.line?.ready ? "ok" : "idle"}>{status?.line?.words || "Not set in Settings ▸ Calls"}</DotWord>}
          verb={null} />
      </GadgetGroup>
      <p className="phone-egress" data-testid="phone-egress">{PHONE_EGRESS_SENTENCE}</p>
    </div>
  );
}

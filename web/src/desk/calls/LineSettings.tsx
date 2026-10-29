/* Settings ▸ Calls ▸ Line (LINE-DESIGN-2026-10-29 §10; canvas
 * docs/internal/betterment/line/canvases/line-2026-10-29.html, direction A;
 * CANVAS-NOTES-2026-10-29.md is the kit-piece list): the Accounts grammar of
 * PhoneSettings — one inset group per part (Where it runs, The line, Test
 * call, From Calls, Adapter), rows name · fact · state · verb.
 *
 * The pane reads `GET /api/calls/line/status` (the place, its word, the
 * address, where each secret is: never a value) and writes `calls.line` of
 * /api/settings. The SIP password and the Telnyx key are write only: each
 * goes to the hub's keystore. The machine is named here (and as the hover
 * title of Test call), never on the Calls window (UX-CANON A.9). Egress is
 * said here once. */
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { readableError } from "../../lib/api";
import { CommandWell } from "../../pages/cores/connections/ConnectionsPane";
import { spriteUrl } from "../sprites";
import { GadgetGroup, MxRadio, StringGadget } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { LINE_OFF, readLineStatus, testLine } from "./api";
import type { CallsSettings, LineSettings, LineState, LineStatus, SecretPlace } from "./types";
import "./calls.css";

/** The Line runs in its own Python 3.13 (the hub's Python has no
 *  onnxruntime wheel), from this checkout. */
export const LINE_BREW_COMMAND = "brew install baresip";
export const LINE_VENV_COMMAND =
  "uv python install 3.13 && uv venv ~/.holdspeak/line/venv --python 3.13 && uv pip install --python ~/.holdspeak/line/venv -e \"<your HoldSpeak checkout>[line]\" && ~/.holdspeak/line/venv/bin/holdspeak line models";
export const LINE_RUN_COMMAND = "~/.holdspeak/line/venv/bin/holdspeak line";

export const LINE_EGRESS_SENTENCE =
  "A call on the SIP address stays on your tailnet. A call on a Telnyx number goes through Telnyx. The Line hears and speaks on its own machine; the words of a turn go to your home engine.";

/** The place words (the Engines vocabulary) and their tones. */
const PLACE: Record<LineState, { word: string; tone: "ok" | "info" | "warn" | "idle" | "fail" }> = {
  ready: { word: "Ready", tone: "ok" },
  starting: { word: "Starting", tone: "info" },
  not_running: { word: "Not running", tone: "warn" },
  not_installed: { word: "Not installed", tone: "idle" },
  not_set_up: { word: "Not set up", tone: "warn" },
  offline: { word: "Offline", tone: "warn" },
  off: { word: "Off", tone: "idle" },
};

/** The Test call result words (`POST /api/calls/line/test`). */
export const TEST_WORDS: Record<string, { word: string; tone: "ok" | "info" | "warn" | "idle" | "fail" }> = {
  ringing: { word: "Ringing", tone: "info" },
  answered: { word: "Answered", tone: "ok" },
  no_answer: { word: "No answer", tone: "idle" },
  rejected: { word: "Rejected", tone: "warn" },
  busy: { word: "Busy", tone: "warn" },
  not_running: { word: "Line not running", tone: "warn" },
  no_line: { word: "Line not running", tone: "warn" },
  no_number: { word: "No number", tone: "idle" },
  daily_limit: { word: "Daily limit reached", tone: "warn" },
  emergency: { word: "Never dialled", tone: "warn" },
};

/** The secret's place in his words. */
export const SECRET_WORDS: Record<SecretPlace, { word: string; tone: "ok" | "warn" | "idle" }> = {
  keystore: { word: "Stored in your keystore", tone: "ok" },
  environment: { word: "From the environment: move it to the keystore", tone: "warn" },
  missing: { word: "Missing", tone: "idle" },
};

/** The measured cost of a call minute on each machine (LINE design §12). */
const COST: Record<string, string> = {
  "this-mac": "About 0.13 core per call minute",
  karol: "About 0.4 core per call minute",
};

const NEVER_DIALLED = "911, 112, 999, 000 and the other emergency numbers";

function placeName(where: string): string {
  return where.startsWith("node:") ? where.slice(5) : "This Mac";
}
function nodeOf(where: string): string {
  return where.startsWith("node:") ? where.slice(5) : "this-mac";
}

function Row({ name, fact, state, verb, testId }: {
  name: ReactNode; fact?: ReactNode; state?: ReactNode; verb?: ReactNode; testId?: string;
}) {
  return (
    <div className="line-row" data-testid={testId}>
      <span className="line-row-name">{name}</span>
      <span className="line-row-fact">{fact}</span>
      <span className="line-row-state">{state}</span>
      <span className="line-row-verb">{verb}</span>
    </div>
  );
}

/** A write-only secret: the field clears after Save and the row says where
 *  the secret is, never its value. */
function SecretRow({ label, place, busy, onSave, testId }: {
  label: string; place: SecretPlace; busy: boolean; onSave(value: string): void; testId: string;
}) {
  const [draft, setDraft] = useState("");
  const [changing, setChanging] = useState(false);
  const words = SECRET_WORDS[place];
  const open = place !== "keystore" || changing;
  const save = () => {
    if (!draft.trim()) return;
    onSave(draft.trim());
    setDraft("");
    setChanging(false);
  };
  return (
    <div className="line-secret" data-testid={testId} data-place={place}>
      <Row
        name={label}
        state={<DotWord tone={words.tone} data-testid={`${testId}-place`}>{words.word}</DotWord>}
        verb={place === "keystore" && !changing ? (
          <Button dense variant="secondary" onClick={() => setChanging(true)} data-testid={`${testId}-change`}>Change</Button>
        ) : null}
      />
      {open ? (
        <div className="line-field">
          <span className="calls-field-line">
            <StringGadget
              label={label}
              type="password"
              mic={false}
              value={draft}
              onChange={setDraft}
              placeholder="Kept in your keystore"
              onKeyDown={(event) => { if (event.key === "Enter") save(); }}
              inputProps={{ autoComplete: "new-password" }}
            />
            <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid={`${testId}-save`}>Save</Button>
            {changing ? <Button dense variant="ghost" onClick={() => { setChanging(false); setDraft(""); }}>Cancel</Button> : null}
          </span>
        </div>
      ) : null}
    </div>
  );
}

function AccountField({ label, value, placeholder, busy, onSave, testId }: {
  label: string; value: string; placeholder: string; busy: boolean; onSave(next: string): void; testId: string;
}) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const changed = draft.trim() !== value;
  return (
    <div className="line-field" data-testid={testId}>
      <span className="calls-field-line">
        <StringGadget
          label={label}
          value={draft}
          onChange={setDraft}
          placeholder={placeholder}
          onKeyDown={(event) => { if (event.key === "Enter" && changed) onSave(draft.trim()); }}
        />
        <Button dense variant="secondary" loading={busy} disabled={!changed} onClick={() => onSave(draft.trim())} data-testid={`${testId}-save`}>Save</Button>
      </span>
    </div>
  );
}

function CopyAddress({ address }: { address: string }) {
  const [word, setWord] = useState<"Copy" | "Copied" | "Copy failed">("Copy");
  return (
    <Button dense variant="secondary" disabled={!address} data-testid="line-address-copy"
      onClick={() => {
        void (async () => {
          try { await navigator.clipboard.writeText(address); setWord("Copied"); } catch { setWord("Copy failed"); }
        })();
      }}>
      {word}
    </Button>
  );
}

/** The pane. `settings` is the `calls` section the Calls pane read; a write
 *  goes through `onWrite` (the Calls pane's own write) and the status is
 *  read again. */
export function LineSettingsPane({ settings, onWrite }: {
  settings: CallsSettings;
  onWrite(key: "line", value: unknown): Promise<void>;
}) {
  const [status, setStatus] = useState<LineStatus>(LINE_OFF);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  const [test, setTest] = useState<string>("");

  const load = useCallback(async () => {
    try { setStatus(await readLineStatus()); } catch (error) { setRefusal(readableError(error)); } finally { setLoaded(true); }
  }, []);
  useEffect(() => { void load(); }, [load]);

  const line = settings.line;
  const where = line?.where ?? "this_mac";
  const acct = line?.account ?? { kind: "sip", user: "holdspeak", domain: "", outbound: "", password_ref: "", codecs: [] };
  const secrets = { ...(line?.secrets ?? {}), ...status.secrets };
  const adapter = line?.adapter || (status.state === "off" ? "ai-phone" : "line");

  const write = async (key: string, patch: Record<string, unknown>) => {
    setBusy(key);
    setRefusal("");
    try {
      await onWrite("line", patch);
      await load();
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const places = Array.from(new Set(["this_mac", where]));
  const place = PLACE[status.state] ?? PLACE.off;
  const here = nodeOf(where);
  const firstNumber = settings.allowed_numbers?.[0] ?? "";
  const ringing = test === "ringing";

  const call = async () => {
    setTest("ringing");
    setRefusal("");
    try {
      const answer = await testLine();
      setTest(answer.result || "not_running");
    } catch (error) {
      setTest("");
      setRefusal(readableError(error));
    }
  };

  const testWord = test ? (TEST_WORDS[test] ?? { word: test.replace(/_/g, " "), tone: "warn" as const }) : null;
  const noNumber = !firstNumber;

  return (
    <div className="line-settings" data-testid="line-settings" aria-busy={loaded ? undefined : true} data-state={status.state}>
      {refusal ? <p className="calls-refusal" role="alert" data-testid="line-refusal">{refusal}</p> : null}
      <GadgetGroup material="inset" label="Where it runs">
        <div data-testid="line-where">
          <MxRadio
            label="Where it runs"
            value={where}
            onChange={(next) => void write("where", { where: next })}
            options={places.map((value) => ({
              value,
              label: (
                <span className="line-place" data-testid="line-place" data-where={value}>
                  <img className="line-sprite" src={spriteUrl("model", "line", "rest", null, 20)} alt="" width={20} height={20} />
                  <span className="line-place-name">{placeName(value)}</span>
                  <span className="line-row-fact">{COST[nodeOf(value)] ?? ""}</span>
                  {value === where ? (
                    <DotWord tone={place.tone} className="line-place-state" data-testid="line-place-state">{status.words || place.word}</DotWord>
                  ) : null}
                </span>
              ),
            }))}
          />
          {here === "this-mac" && status.state === "not_installed" ? (
            <div className="line-commands" data-testid="line-install">
              <p className="calls-step-say">Install baresip, then the Line in its own Python 3.13.</p>
              <CommandWell hint={LINE_BREW_COMMAND} />
              <CommandWell hint={LINE_VENV_COMMAND} />
              <CommandWell hint={LINE_RUN_COMMAND} />
            </div>
          ) : here === "this-mac" && status.state === "not_running" ? (
            <div className="line-commands" data-testid="line-install">
              <p className="calls-step-say">The Line runs in its own Python 3.13.</p>
              <CommandWell hint={LINE_VENV_COMMAND} />
              <CommandWell hint={LINE_RUN_COMMAND} />
            </div>
          ) : here !== "this-mac" && (status.state === "not_running" || status.state === "offline") ? (
            <div className="line-commands" data-testid="line-install">
              <CommandWell hint={`holdspeak line --node ${here} --hub ${window.location.origin}`} />
            </div>
          ) : null}
        </div>
      </GadgetGroup>

      <GadgetGroup material="inset" label="The line">
        <div data-testid="line-account" data-kind={acct.kind}>
          <MxRadio
            label="The line"
            value={acct.kind}
            onChange={(next) => void write("kind", { account: { kind: next } })}
            options={[
              { value: "sip", label: <span className="line-kind">A SIP address on your tailnet</span> },
              { value: "telnyx", label: <span className="line-kind">A Telnyx number</span> },
            ]}
          />
          {acct.kind === "sip" ? (
            <Row testId="line-address"
              name="Address to dial"
              fact={status.address ? <code className="line-address">{status.address}</code> : "Shows when the Line runs"}
              verb={<CopyAddress address={status.address} />} />
          ) : (
            <>
              <AccountField label="User" value={acct.user} placeholder="Your Telnyx SIP user" busy={busy === "user"}
                onSave={(next) => void write("user", { account: { user: next } })} testId="line-user" />
              <AccountField label="Domain" value={acct.domain} placeholder="sip.telnyx.com" busy={busy === "domain"}
                onSave={(next) => void write("domain", { account: { domain: next } })} testId="line-domain" />
              <SecretRow label="SIP password" place={secrets.sip_password ?? "missing"} busy={busy === "password"}
                onSave={(value) => void write("password", { account: { password: value } })} testId="line-password" />
              <SecretRow label="Telnyx API key" place={secrets.telnyx_api_key ?? "missing"} busy={busy === "telnyx_api_key"}
                onSave={(value) => void write("telnyx_api_key", { telnyx_api_key: value })} testId="line-telnyx-key" />
            </>
          )}
          {acct.codecs?.length ? <p className="line-quiet" data-testid="line-codecs">Codecs: {acct.codecs.join(", ")}</p> : null}
        </div>
      </GadgetGroup>

      <GadgetGroup material="inset" label="Test call">
        <Row testId="line-test"
          name={<><img className="line-sprite" src={spriteUrl("call", "calls", "rest", null, 20)} alt="" width={20} height={20} />{noNumber ? "No number" : `Calls ${firstNumber}`}</>}
          state={testWord ? (
            <span className={ringing ? "line-live" : undefined}>
              <DotWord tone={testWord.tone} data-testid="line-test-state">{testWord.word}</DotWord>
            </span>
          ) : null}
          verb={<Button dense variant="secondary" loading={ringing} disabled={noNumber || ringing}
            title={`From the Line on ${placeName(where)}`} onClick={() => void call()} data-testid="line-test-call">Test call</Button>} />
      </GadgetGroup>

      <GadgetGroup material="inset" label="From Calls">
        <div className="calls-may" data-testid="line-from-calls">
          <div className="calls-may-row"><span>Daily limit</span>
            <span className="calls-fact">{settings.daily_limit ? `${settings.daily_limit} placed calls a day` : "No limit"}</span></div>
          <div className="calls-may-row"><span>First words out</span>
            <span className="calls-fact">This is HoldSpeak, an AI assistant</span></div>
          <div className="calls-may-row"><span>Never dialled</span><span className="calls-fact">{NEVER_DIALLED}</span></div>
        </div>
      </GadgetGroup>

      <GadgetGroup material="inset" label="Adapter">
        <div data-testid="line-adapter">
          <MxRadio
            label="Adapter"
            value={adapter}
            onChange={(next) => void write("adapter", { adapter: next })}
            options={[
              { value: "line", label: <span className="line-kind">The Line{adapter === "line" ? <DotWord tone="ok">In use</DotWord> : null}</span> },
              { value: "ai-phone", label: (
                <span className="line-kind">ai-phone<span className="line-row-fact">Optional, AGPL, runs as a separate program</span>
                  {adapter === "ai-phone" ? <DotWord tone="ok">In use</DotWord> : null}</span>
              ) },
            ]}
          />
        </div>
      </GadgetGroup>
      <p className="calls-egress" data-testid="line-egress">{LINE_EGRESS_SENTENCE}</p>
    </div>
  );
}

import { PreferenceWell, ListView, GadgetRow, PaneActions, PaneGroup, ListPane, PaneInspector, InspectorForm, EgressChip } from "../surface";
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
import { apiFetch, readableError } from "../../lib/api";
import { CommandWell } from "../../pages/cores/connections/ConnectionsPane";
import { GadgetGroup, MxRadio, StringGadget } from "../surface/gadgets";
import { DotWord } from "../surface/kit";
import { TelnyxSetup } from "./TelnyxSetup";
import { LINE_OFF, mintLineCode, readLineNodes, readLineStatus, revokeLineNode, testLine } from "./api";
import type { CallsSettings, LineCode, LineNode, LineState, LineStatus, SecretPlace } from "./types";
import "./calls.css";

/** The Line runs in its own Python 3.13 (the hub's Python has no
 *  onnxruntime wheel), from this checkout. */
export const LINE_BREW_COMMAND = "brew install baresip";
export const LINE_VENV_COMMAND =
  'uv python install 3.13 && uv venv ~/.holdspeak/line/venv --python 3.13 && uv pip install --python ~/.holdspeak/line/venv -e "<your HoldSpeak checkout>[line]" && ~/.holdspeak/line/venv/bin/holdspeak line models';
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
  environment: {
    word: "From the environment: move it to the keystore",
    tone: "warn",
  },
  missing: { word: "Missing", tone: "idle" },
};

/** While the code sheet is open the pane reads the nodes this often: the
 *  machine's first hello closes the sheet. */
export const NODE_POLL_MS = 5000;

function placeName(where: string): string {
  return where.startsWith("node:") ? where.slice(5) : "This Mac";
}
function nodeOf(where: string): string {
  return where.startsWith("node:") ? where.slice(5) : "this-mac";
}

function minutesLeft(deadline: number, now: number): number {
  return Math.max(0, Math.ceil((deadline - now) / 60_000));
}

/** The one-time code: large, its life as a word, the whole command with
 *  Copy. It closes when the machine's first hello arrives. */
function CodeSheet({
  code,
  deadline,
  now,
  busy,
  onNew,
  onCancel,
}: {
  code: LineCode;
  deadline: number;
  now: number;
  busy: boolean;
  onNew(): void;
  onCancel(): void;
}) {
  const left = minutesLeft(deadline, now);
  return (
    <div className="line-code-sheet" data-testid="line-code-sheet" data-node={code.node}>
      <div className="line-code-head">
        <code className="line-code" data-testid="line-code">
          {code.code}
        </code>
        <span className="line-code-life" data-testid="line-code-life">
          {left > 0 ? `Good for ${left} more ${left === 1 ? "minute" : "minutes"}` : "This code is too old"}
        </span>
        <span className="line-row-verb">
          {left > 0 ? null : (
            <Button dense variant="secondary" loading={busy} onClick={onNew} data-testid="line-code-new">
              New code
            </Button>
          )}
          <Button dense variant="ghost" onClick={onCancel} data-testid="line-code-cancel">
            Cancel
          </Button>
        </span>
      </div>
      <p className="calls-step-say">Run this on {code.node}</p>
      <div className="line-commands">
        <CommandWell hint={code.command} />
      </div>
      <span className="line-code-wait">
        <DotWord tone="info" data-testid="line-code-wait">
          Waiting for {code.node}
        </DotWord>
      </span>
    </div>
  );
}

function Row({ name, fact, state, verb, testId }: { name: ReactNode; fact?: ReactNode; state?: ReactNode; verb?: ReactNode; testId?: string }) {
  return (
    <div data-testid={testId}><GadgetRow label={name} fact={fact}>
      {state}{verb}
    </GadgetRow></div>
  );
}

/** A write-only secret: the field clears after Save and the row says where
 *  the secret is, never its value. */
function SecretRow({
  label,
  place,
  busy,
  onSave,
  testId,
}: {
  label: string;
  place: SecretPlace;
  busy: boolean;
  onSave(value: string): Promise<boolean>;
  testId: string;
}) {
  const [draft, setDraft] = useState("");
  const [changing, setChanging] = useState(false);
  const words = SECRET_WORDS[place];
  const open = place !== "keystore" || changing;
  const save = async () => {
    if (!draft.trim() || busy) return;
    if (await onSave(draft.trim())) {
      setDraft("");
      setChanging(false);
    }
  };
  return (
    <div className="line-secret" data-testid={testId} data-place={place}>
      <Row
        name={label}
        state={
          <DotWord tone={words.tone} data-testid={`${testId}-place`}>
            {words.word}
          </DotWord>
        }
        verb={
          place === "keystore" && !changing ? (
            <Button dense variant="secondary" onClick={() => setChanging(true)} data-testid={`${testId}-change`}>
              Change
            </Button>
          ) : null
        }
      />
      {open ? (
        <div className="line-field">
          <span className="surface-pane-actions">
            <StringGadget
              label={label}
              type="password"
              disabled={busy}
              mic={false}
              value={draft}
              onChange={setDraft}
              placeholder="Kept in your keystore"
              onKeyDown={(event) => {
                if (event.key === "Enter") save();
              }}
              inputProps={{ autoComplete: "new-password" }}
            />
            <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid={`${testId}-save`}>
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
          </span>
        </div>
      ) : null}
    </div>
  );
}

function AccountField({
  label,
  value,
  placeholder,
  busy,
  onSave,
  testId,
}: {
  label: string;
  value: string;
  placeholder: string;
  busy: boolean;
  onSave(next: string): void;
  testId: string;
}) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const changed = draft.trim() !== value;
  return (
    <div data-testid={testId}>
      <GadgetRow label={label}>
        <span className="surface-pane-actions">
          <StringGadget
            label={label}
            value={draft}
            onChange={setDraft}
            placeholder={placeholder}
            onKeyDown={(event) => {
              if (event.key === "Enter" && changed) onSave(draft.trim());
            }}
          />
          <Button dense variant="secondary" loading={busy} disabled={!changed} onClick={() => onSave(draft.trim())} data-testid={`${testId}-save`}>
            Save
          </Button>
        </span>
      </GadgetRow>
    </div>
  );
}

function CopyAddress({ address }: { address: string }) {
  const [word, setWord] = useState<"Copy" | "Copied" | "Copy failed">("Copy");
  return (
    <Button
      dense
      variant="secondary"
      disabled={!address}
      data-testid="line-address-copy"
      onClick={() => {
        void (async () => {
          try {
            await navigator.clipboard.writeText(address);
            setWord("Copied");
          } catch {
            setWord("Copy failed");
          }
        })();
      }}
    >
      {word}
    </Button>
  );
}

/** The pane. `settings` is the `calls` section the Calls pane read; a write
 *  goes through `onWrite` (the Calls pane's own write) and the status is
 *  read again. */
export function LineSettingsPane({
  settings,
  onWrite,
  onReload,
  accountOpen,
  telnyxOpen = false,
}: {
  accountOpen?: boolean;
  telnyxOpen?: boolean;
  settings: CallsSettings;
  onWrite(key: "line", value: unknown): Promise<void>;
  /** Read the `calls` settings again (the Telnyx setup wrote the account). */
  onReload?(): Promise<void>;
}) {
  const [status, setStatus] = useState<LineStatus>(LINE_OFF);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  /** The machine the owner is asked about before its key is revoked. */
  const [askRevoke, setAskRevoke] = useState<string | null>(null);
  const [test, setTest] = useState<string>("");
  const [nodes, setNodes] = useState<LineNode[]>([]);
  const [adding, setAdding] = useState(false);
  const [machine, setMachine] = useState("");
  const [sheet, setSheet] = useState<{
    code: LineCode;
    deadline: number;
  } | null>(null);
  const [now, setNow] = useState(() => Date.now());

  const load = useCallback(async () => {
    try {
      const [read, enrolled] = await Promise.all([readLineStatus(), readLineNodes()]);
      setStatus(read);
      setNodes(enrolled);
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setLoaded(true);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);

  // The sheet is open: its life ticks, and the nodes are read again until
  // the machine's first hello (its word is no longer Not running).
  const waitingFor = sheet?.code.node ?? "";
  useEffect(() => {
    if (!waitingFor) return undefined;
    const tick = window.setInterval(() => setNow(Date.now()), 1000);
    const poll = window.setInterval(() => {
      void readLineNodes()
        .then((enrolled) => {
          setNodes(enrolled);
          const arrived = enrolled.find((row) => row.node === waitingFor);
          if (arrived && arrived.state !== "not_running") {
            setSheet(null);
            void load();
          }
        })
        .catch(() => undefined);
    }, NODE_POLL_MS);
    return () => {
      window.clearInterval(tick);
      window.clearInterval(poll);
    };
  }, [waitingFor, load]);

  const install = async (name: string) => {
    if (!name) return;
    setBusy("install");
    setRefusal("");
    try {
      const code = await mintLineCode(name);
      const at = Date.now();
      setNow(at);
      setSheet({ code, deadline: at + code.expires_in * 1000 });
      setMachine("");
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const revoke = async (node: string) => {
    setBusy(`revoke-${node}`);
    setRefusal("");
    try {
      await revokeLineNode(node);
      setAskRevoke(null);
      await load();
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const line = settings.line;
  const where = line?.where ?? "this_mac";
  const acct = line?.account ?? {
    kind: "sip",
    user: "holdspeak",
    domain: "",
    outbound: "",
    password_ref: "",
    codecs: [],
  };
  const secrets = { ...(line?.secrets ?? {}), ...status.secrets };

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

  const writeSecret = async (key: string, secretId: string, value: string | null) => {
    setBusy(key);
    setRefusal("");
    try {
      const answer = await apiFetch<{ success: boolean; error?: string }>(`/api/settings/secrets/${secretId}`, {
        method: value === null ? "DELETE" : "PUT",
        ...(value === null ? {} : { json: { value } }),
      });
      if (!answer.success) throw new Error(answer.error || "The hub did not confirm the save. Your edit is kept. Try Save again.");
      await onReload?.();
      await load();
      return true;
    } catch (error) {
      setRefusal(readableError(error));
      return false;
    } finally {
      setBusy("");
    }
  };

  const places = Array.from(new Set(["this_mac", ...nodes.map((row) => `node:${row.node}`), where]));
  const nodeRow = (value: string) => nodes.find((row) => `node:${row.node}` === value);
  const typed = machine.trim();
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

  const testWord = test
    ? (TEST_WORDS[test] ?? {
        word: test.replace(/_/g, " "),
        tone: "warn" as const,
      })
    : null;
  const noNumber = !firstNumber;

  const telnyxPanel = (
<TelnyxSetup
                  onChanged={async () => {
                    await onReload?.();
                    await load();
                  }}
                  keyRow={
                    <SecretRow
                      label="Telnyx API key"
                      place={secrets.telnyx_api_key ?? "missing"}
                      busy={busy === "telnyx_api_key"}
                      onSave={(value) => writeSecret("telnyx_api_key", "line_telnyx_api_key", value)}
                      testId="line-telnyx-key"
                    />
                  }
                />
  );
  const accountPanel = (
    <PreferenceWell>
      <div className="surface-tab-panel">
        <GadgetGroup label="The line">
          <div data-testid="line-account" data-kind={acct.kind}>
            <MxRadio
              label="The line"
              value={acct.kind}
              onChange={(next) => void write("kind", { account: { kind: next } })}
              options={[
                {
                  value: "sip",
                  label: <span className="line-kind">A SIP address on your tailnet</span>,
                },
                {
                  value: "telnyx",
                  label: <span className="line-kind">A Telnyx number</span>,
                },
              ]}
            />
            {acct.kind === "telnyx" ? (
              <>
                <AccountField
                  label="User"
                  value={acct.user}
                  placeholder="Your Telnyx SIP user"
                  busy={busy === "user"}
                  onSave={(next) => void write("user", { account: { user: next } })}
                  testId="line-user"
                />
                <AccountField
                  label="Domain"
                  value={acct.domain}
                  placeholder="sip.telnyx.com"
                  busy={busy === "domain"}
                  onSave={(next) => void write("domain", { account: { domain: next } })}
                  testId="line-domain"
                />
                <SecretRow
                  label="SIP password"
                  place={secrets.sip_password ?? "missing"}
                  busy={busy === "password"}
                  onSave={(value) => writeSecret("password", "line_sip_password", value)}
                  testId="line-password"
                />
              </>
            ) : null}
          </div>
        </GadgetGroup>
      </div>
      <GadgetGroup material="inset" label="From Calls">
        <div data-testid="line-from-calls">
          <GadgetRow label="Daily limit">
            <span className="surface-preference-value">{settings.daily_limit ? `${settings.daily_limit} placed calls a day` : "No limit"}</span>
          </GadgetRow>
        </div>
      </GadgetGroup>
    </PreferenceWell>
  );
  const closeMachine = () => { setAdding(false); setSheet(null); setAskRevoke(null); };
  return (
    <div className="surface-preference-pane" data-testid="line-settings" aria-busy={loaded ? undefined : true} data-state={status.state}>
      {refusal ? <PaneActions><span role="alert" data-testid="line-refusal">{refusal}</span><Button dense onClick={() => void load()}>Retry</Button></PaneActions> : null}
      <div className="surface-tab-panel" hidden={accountOpen === true || telnyxOpen}>
        <ListPane label="Line machine" list={<PaneGroup label="Where it runs">
          <ListView label="Line machines" ordered
            rows={places.map((value) => {
              const row = nodeRow(value);
              const own = row ? (PLACE[row.state] ?? PLACE.not_running) : null;
              return {id: value, kind: "machine", name: placeName(value), cells: {
                facts: row?.machine?.platform ?? "",
                status: value === where && status.state !== "ready" ? <DotWord tone={place.tone} data-testid="line-place-state">{status.words || place.word}</DotWord>
                  : row && own && row.state !== "ready" ? <DotWord tone={own.tone} data-testid="line-node-state">{row.words || own.word}</DotWord> : null,
              }};
            })}
            columns={[{key: "name", word: "Machine", priority: 100}, {key: "facts", word: "Details", priority: 20}, {key: "status", word: "Needs you", priority: 30}]}
            rowProps={(row) => ({"data-testid": "line-place", "data-where": row.id})}
            verbs={[
              {id: "add", label: "Add machine", symbol: "+", enabled: () => !busy, run: () => {setAskRevoke(null); setAdding(true);}},
              {id: "use", label: "Use machine", key: "Enter", enabled: (row) => Boolean(row) && !busy, run: (row) => void write("where", {where: row!.id})},
              {id: "revoke", label: "Revoke machine", symbol: "−", enabled: (row) => Boolean(row?.id.startsWith("node:")) && !busy, run: (row) => {setAdding(false); setSheet(null); setAskRevoke(nodeOf(row!.id));}},
            ]} defaultVerb="use" onSelect={() => setAskRevoke(null)} />
        </PaneGroup>}>
          {askRevoke ? <PaneInspector label={`Revoke ${askRevoke}?`}>
            <InspectorForm testId="line-revoke-ask" rows={[{label: "Machine", control: askRevoke}]} completion={{
              cancel: () => setAskRevoke(null), cancelDisabled: Boolean(busy), cancelTestId: "line-revoke-cancel",
              primary: {label: "Revoke", run: () => void revoke(askRevoke), busy: busy === `revoke-${askRevoke}`, testId: "line-node-revoke"},
            }} />
          </PaneInspector> : sheet ? <PaneInspector label="Add machine"><InspectorForm rows={[{label: "Code", control:
            <CodeSheet code={sheet.code} deadline={sheet.deadline} now={now} busy={busy === "install"} onNew={() => void install(sheet.code.node)} onCancel={() => setSheet(null)} />
          }]} /></PaneInspector> : adding ? <PaneInspector label="Add machine">
            <InspectorForm testId="line-add" rows={[{label: "Machine", control:
              <StringGadget label="Add a machine" value={machine} onChange={setMachine} placeholder="Machine name" onKeyDown={(event) => {if (event.key === "Enter") void install(typed);}} />
            }]} completion={{cancel: closeMachine, primary: {label: typed ? `Install the Line on ${typed}` : "Install the Line", run: () => void install(typed), disabled: !typed || Boolean(busy), busy: busy === "install", testId: "line-install-node"}}} />
          </PaneInspector> : <>
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

          <GadgetGroup label="Line address"><GadgetRow label="Address"><PaneActions>
            <StringGadget label="Line address" value={status.address} mic={false} onChange={() => undefined} inputProps={{readOnly: true}} /><CopyAddress address={status.address} />
          </PaneActions></GadgetRow></GadgetGroup>
          <GadgetGroup label="Test call">
            <Row
              testId="line-test"
              name="Test call"
              fact={
                <span className="surface-preference-value" title={firstNumber}>
                  {noNumber ? "No number" : `Calls ${firstNumber}`}
                </span>
              }
              state={
                testWord ? (
                  <span className={ringing ? "line-live" : undefined}>
                    <DotWord tone={testWord.tone} data-testid="line-test-state">
                      {testWord.word}
                    </DotWord>
                  </span>
                ) : null
              }
              verb={
                <Button
                  dense
                  variant="secondary"
                  loading={ringing}
                  disabled={noNumber || ringing}
                  title={`From the Line on ${placeName(where)}`}
                  onClick={() => void call()}
                  data-testid="line-test-call"
                >
                  Test call
                </Button>
              }
            />
          </GadgetGroup>

          </>}
        </ListPane>
      </div>
      <div className="surface-tab-panel" hidden={accountOpen === false || telnyxOpen}>{accountPanel}</div>
      <div className="surface-tab-panel" hidden={!telnyxOpen && accountOpen !== undefined}>{acct.kind === "telnyx" ? telnyxPanel : null}</div>
      <span data-testid="line-egress"><EgressChip label={acct.kind === "sip" ? "Audio: tailnet · Words: home engine" : "Audio: Telnyx · Words: home engine"} title={LINE_EGRESS_SENTENCE} scope={acct.kind === "sip" ? "remote" : "mixed"} /></span>
    </div>
  );
}

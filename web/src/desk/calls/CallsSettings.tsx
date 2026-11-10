/* Settings ▸ Calls (CALLS-DESIGN-2026-10-28 §6; canvas
 * docs/internal/betterment/canvases/calls-2026-10-28.html): the Accounts
 * grammar (#1503): one paper, one grid, a state is a dot and a word, one
 * verb per row.
 *
 * The checklist comes from the status `steps`, in order: Install ai-phone,
 * Start it, A line, The engine, A passphrase, the switch. An open step shows
 * its exact command with Copy. Egress is said here, once, in one plain
 * sentence (UX-CANON A.9): never as a chip on the Calls window. The fields
 * write the `calls` section of /api/settings; the passphrase is write only
 * (the read says `passphrase_set`, never the value). Line (LINE-DESIGN
 * §10) follows: Where it runs, The line, Test call, From Calls, Adapter.
 * Phone (PHONE-DESIGN §9) follows: Your phone, Reach you, Quiet hours, The
 * number. When the Line is the phone, the first three steps are the Line's
 * (its commands are in Line). */
import { useCallback, useEffect, useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import { readEditor, writeChain, type RowEditor } from "../../features/runson/api";
import { readableError } from "../../lib/api";
import { CommandWell } from "../../pages/cores/connections/ConnectionsPane";
import { CheckGadget, GadgetGroup, StringGadget } from "../surface/gadgets";
import { ABSENT_STATUS, OPEN_STEPS, lineInUse, readCallsSettings, readCallsStatus, writeCallsSetting } from "./api";
import type { CallStep, CallStepId, CallsSettings, CallsStatus } from "./types";
import { LineSettingsPane } from "./LineSettings";
import { PhoneSettingsPane } from "./PhoneSettings";
import {
  PreferencePane,
  PreferenceWell,
  SegmentedTabs,
  ListView,
  PaneActions,
  GadgetRow,
  CycleGadget,
  ListPane,
  PaneGroup,
  PaneInspector,
  InspectorForm,
  EgressChip,
} from "../surface";

export const INSTALL_COMMAND = "git clone https://github.com/oxnw/ai-phone.git ~/dev/ai-phone && cd ~/dev/ai-phone && ./scripts/install.sh && uv run ai-phone setup";
export const RUN_COMMAND = "uv run ai-phone run";
export const SIP_COMMAND = "uv run ai-phone lines add sip --id agent --user agent --host <your Mac's tailnet name> --trusted <your iPhone's tailnet IP>";
export const TELNYX_COMMAND = "uv run ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212";
export const TWILIO_COMMAND = "uv run ai-phone lines add twilio --key-env TWILIO_ACCOUNT_SID --secret-env TWILIO_AUTH_TOKEN --existing <your Twilio number>";

export const EGRESS_SENTENCE = "On a call, the audio goes through your line and its carrier, and the words go to your home engine over Tailscale.";

/** The write-only passphrase field: the value is never read back. */
function PassphraseField({ busy, onSave, onCancel }: { busy: boolean; onSave(value: string): void; onCancel?: () => void }) {
  const [draft, setDraft] = useState("");
  const save = () => {
    if (draft.trim()) onSave(draft.trim());
  };
  return (
    <span className="surface-pane-actions">
      <StringGadget
        label="Passphrase"
        type="password"
        mic={false}
        value={draft}
        onChange={setDraft}
        placeholder="New passphrase"
        onKeyDown={(event) => {
          if (event.key === "Enter") save();
        }}
        inputProps={{ autoComplete: "new-password" }}
      />
      <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid="calls-passphrase-save">
        Save
      </Button>
      {onCancel ? (
        <Button dense variant="ghost" onClick={onCancel}>
          Cancel
        </Button>
      ) : null}
    </span>
  );
}

function CheckoutField({ value, busy, onSave }: { value: string; busy: boolean; onSave(value: string): void }) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const changed = draft.trim() !== value;
  return (
    <span className="surface-pane-actions">
      <StringGadget
        label="ai-phone checkout"
        value={draft}
        onChange={setDraft}
        placeholder="~/dev/ai-phone"
        onKeyDown={(event) => {
          if (event.key === "Enter" && changed) onSave(draft.trim());
        }}
      />
      <Button dense variant="secondary" loading={busy} disabled={!changed} onClick={() => onSave(draft.trim())} data-testid="calls-checkout-save">
        Save
      </Button>
    </span>
  );
}

function NumbersField({ numbers, busy, onSave }: { numbers: string[]; busy: boolean; onSave(next: string[]): Promise<void> }) {
  const [draft, setDraft] = useState("");
  const draftRef = useRef(draft);
  const [adding, setAdding] = useState(false);
  const add = async () => {
    const next = draft.trim();
    if (!next || numbers.includes(next)) return;
    try {
      await onSave([...numbers, next]);
      if (draftRef.current.trim() === next) {
        setDraft("");
        draftRef.current = "";
        setAdding(false);
      }
    } catch {
      /* The pane keeps the refusal and this draft. */
    }
  };
  return (
    <ListPane
      label="Number"
      list={
        <PaneGroup label="Your numbers">
          <ListView
            label="Your numbers"
            rows={numbers.map((number, index) => ({
              id: number,
              kind: "number",
              name: number,
              cells: { role: index === 0 ? "Call me rings here" : "May call" },
            }))}
            columns={[
              { key: "name", word: "Number", priority: 100 },
              { key: "role", word: "Use", priority: 20 },
            ]}
            verbs={[
              {
                id: "add",
                label: "Add number",
                symbol: "+",
                testId: "calls-number-add",
                enabled: () => !busy,
                run: () => setAdding(true),
              },
              {
                id: "remove",
                label: "Remove number",
                symbol: "−",
                enabled: (row) => Boolean(row) && !busy,
                run: (row) => {
                  void onSave(numbers.filter((n) => n !== row!.id)).catch(() => undefined);
                },
              },
            ]}
          />
        </PaneGroup>
      }
    >
      {adding ? (
        <PaneInspector label="Add number">
          <InspectorForm
            completion={{
              cancel: () => setAdding(false),
              primary: {
                label: "Add",
                run: () => void add(),
                disabled: busy || !draft.trim() || numbers.includes(draft.trim()),
                testId: "calls-number-save",
              },
            }}
          >
            <GadgetRow label="Number">
              <StringGadget
                label="Add a number"
                type="tel"
                value={draft}
                onChange={(value) => {
                  draftRef.current = value;
                  setDraft(value);
                }}
                placeholder="Your mobile number"
                onKeyDown={(event) => {
                  if (event.key === "Enter") add();
                }}
              />
            </GadgetRow>
          </InspectorForm>
        </PaneInspector>
      ) : null}
    </ListPane>
  );
}

/** The pane. It reads the `calls` settings and the status itself; a hub
 *  without the Calls slice draws the checklist with every step open. */
export function CallsSettingsPane({ highlight, onSaved }: { highlight?: string; onSaved?: () => void }) {
  const [tab, setTab] = useState(
    highlight === "telnyx" || highlight === "line-account" || highlight === "phone-alerts" || highlight === "numbers" || highlight === "line" || highlight === "phone"
      ? highlight
      : "setup",
  );
  const [settings, setSettings] = useState<CallsSettings | null>(null);
  const [status, setStatus] = useState<CallsStatus>(ABSENT_STATUS);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  const [changing, setChanging] = useState(false);
  const [engine, setEngine] = useState<RowEditor | null>(null);
  const [engineError, setEngineError] = useState("");
  const engineScope = {
    kind: "capability" as const,
    capability_id: "calls.turn",
  };
  const readEngine = () => readEditor(engineScope, "calls.turn").then((next) => { setEngine(next); setEngineError(""); }).catch((error) => setEngineError(readableError(error)));
  useEffect(() => {
    void readEngine();
  }, []);
  const chooseEngine = async (id: string) => {
    if (!engine || !id) return;
    setBusy("engine");
    setEngineError("");
    try {
      await writeChain({
        scope: engineScope,
        expectedRevision: engine.baseRevision,
        entries: [{ profile_id: id }],
      });
      await readEngine();
      setStatus(await readCallsStatus());
      onSaved?.();
    } catch (error) {
      await readEngine();
      setEngineError(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const load = useCallback(async () => {
    try {
      const calls = await readCallsSettings();
      setSettings(calls);
      setStatus(calls ? await readCallsStatus() : ABSENT_STATUS);
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setLoaded(true);
    }
  }, []);
  useEffect(() => {
    void load();
  }, [load]);
  /* DELIGHT slice 4 (2026-10-28): a step's dot turns with the task tick's
     settle (kit.css `data-turns`) when a write changes it. The switch is
     set two frames after the first read, so nothing turns on load. */
  const [turns, setTurns] = useState(false);
  useEffect(() => {
    if (!loaded) return;
    let second = 0;
    const first = window.requestAnimationFrame(() => {
      second = window.requestAnimationFrame(() => setTurns(true));
    });
    return () => {
      window.cancelAnimationFrame(first);
      window.cancelAnimationFrame(second);
    };
  }, [loaded]);

  const write = async (key: keyof CallsSettings | "passphrase", value: unknown, rethrow = false) => {
    setBusy(key);
    setRefusal("");
    try {
      const next = await writeCallsSetting(key, value);
      if (key === "passphrase") setChanging(false);
      if (next) setSettings(next);
      else
        setSettings((now) =>
          now
            ? {
                ...now,
                ...(key === "passphrase" ? { passphrase_set: true } : { [key]: value }),
              }
            : now,
        );
      onSaved?.();
      setStatus(await readCallsStatus());
    } catch (error) {
      setRefusal(readableError(error));
      if (rethrow) throw error;
    } finally {
      setBusy("");
    }
  };

  const onLine = lineInUse(status);
  const steps = status.steps.length ? status.steps : OPEN_STEPS;
  const absent = settings == null;
  const passphraseSet = Boolean(settings?.passphrase_set ?? status.passphrase_set);
  const step = (id: CallStepId): CallStep => steps.find((entry) => entry.id === id) ?? { id, done: false, words: "" };

  return (
    <PreferencePane label="Calls" testId="calls-settings" aria-busy={loaded ? undefined : true} data-turns={turns || undefined}>
      {refusal ? (
        <PaneActions>
          <span role="alert">{refusal}</span>
          <Button dense onClick={() => void load()}>
            Retry
          </Button>
        </PaneActions>
      ) : null}
      <SegmentedTabs
        label="Calls"
        value={tab}
        onChange={setTab}
        tabs={[
          { id: "setup", label: "Calls" },
          { id: "numbers", label: "Numbers" },
          { id: "line", label: "Line" },
          { id: "line-account", label: "Line account" },
          ...(settings?.line?.account.kind === "telnyx" ? [{id: "telnyx", label: "Telnyx"}] : []),
          { id: "phone", label: "Phone" },
          { id: "phone-alerts", label: "Phone alerts" },
        ]}
      >
        <div className="surface-tab-panel" hidden={tab !== "setup"}>
          <PreferenceWell>
            <GadgetGroup egress={<span data-testid="calls-egress"><EgressChip label="Audio: carrier · Words: home engine" title={EGRESS_SENTENCE} scope="mixed" /></span>}>
              <GadgetRow label="Calls" controlWidth="standard">
                <CheckGadget
                  label="Calls on"
                  checked={Boolean(settings?.enabled)}
                  disabled={absent || busy === "enabled"}
                  onChange={(next) => void write("enabled", next)}
                />
              </GadgetRow>
              <GadgetRow label="Engine" controlWidth="standard">
                <div className="surface-pane-group" data-testid="calls-engine">
                  <CycleGadget
                    label="Calls engine"
                    value={engine?.effective?.profileId ?? status.engine.profile_id ?? ""}
                    disabled={!engine || busy === "engine"}
                    options={[
                      {
                        value: "",
                        label: status.engine.model || "Choose an engine",
                      },
                      ...(engine?.effective && !engine.candidates.some((candidate) => candidate.profileId === engine.effective!.profileId)
                        ? [
                            {
                              value: engine.effective.profileId,
                              label: engine.effective.label,
                            },
                          ]
                        : []),
                      ...(engine?.candidates ?? []).map((candidate) => ({
                        value: candidate.profileId,
                        label: candidate.label,
                      })),
                    ]}
                    onChange={(id) => void chooseEngine(id)}
                  />
                  {engineError ? (
                    <PaneActions>
                      <span role="alert">Engine not read</span>
                      <Button dense onClick={() => void readEngine()}>
                        Retry
                      </Button>
                    </PaneActions>
                  ) : null}
                </div>
              </GadgetRow>
              <GadgetRow label="Passphrase" controlWidth="standard" highlight={highlight === "calls-passphrase"}>
                {passphraseSet && !changing ? (
                  <Button dense onClick={() => setChanging(true)} data-testid="calls-passphrase-change">
                    Change passphrase
                  </Button>
                ) : (
                  <PassphraseField
                    busy={busy === "passphrase"}
                    onSave={(next) => void write("passphrase", next)}
                    onCancel={passphraseSet ? () => setChanging(false) : undefined}
                  />
                )}
                {!passphraseSet ? (
                  <span data-testid="calls-step-state-passphrase">Not set</span>
                ) : (
                  <span hidden data-testid="calls-passphrase-set">
                    Set
                  </span>
                )}
              </GadgetRow>
              {!onLine ? (
                <GadgetRow label="Checkout" controlWidth="standard">
                  <CheckoutField value={settings?.aiphone_dir ?? ""} busy={busy === "aiphone_dir"} onSave={(next) => void write("aiphone_dir", next)} />
                </GadgetRow>
              ) : null}
              {!onLine && !step("install").done ? (
                <GadgetRow label="Install ai-phone" controlWidth="standard">
                  <CommandWell hint={INSTALL_COMMAND} />
                </GadgetRow>
              ) : null}
              {!onLine && !step("daemon").done ? (
                <GadgetRow label="Start it" controlWidth="standard">
                  <CommandWell hint={RUN_COMMAND} />
                </GadgetRow>
              ) : null}
              {!onLine && !step("line").done ? (
                <GadgetRow label="SIP address" controlWidth="standard">
                  <CommandWell hint={SIP_COMMAND} />
                </GadgetRow>
              ) : null}
              {!onLine && !step("line").done ? (
                <GadgetRow label="Telnyx" controlWidth="standard">
                  <CommandWell hint={TELNYX_COMMAND} />
                </GadgetRow>
              ) : null}
              {!onLine && !step("line").done ? (
                <GadgetRow label="Twilio" controlWidth="standard">
                  <CommandWell hint={TWILIO_COMMAND} />
                </GadgetRow>
              ) : null}
            </GadgetGroup>

          </PreferenceWell>
        </div>
        <div className="surface-tab-panel" hidden={tab !== "numbers"}>
          <NumbersField numbers={settings?.allowed_numbers ?? []} busy={busy === "allowed_numbers"} onSave={(next) => write("allowed_numbers", next, true)} />
        </div>
        <div className="surface-tab-panel" hidden={tab !== "line" && tab !== "line-account" && tab !== "telnyx"}>
          {settings?.line ? (
            <LineSettingsPane accountOpen={tab === "line-account"} telnyxOpen={tab === "telnyx"} settings={settings} onWrite={(key, value) => write(key, value, true)} onReload={load} />
          ) : (
            <span>Line is not set up</span>
          )}
        </div>
        <div className="surface-tab-panel" hidden={tab !== "phone" && tab !== "phone-alerts"}>
          {absent ? <span>Calls is not set up</span> : <PhoneSettingsPane alertsOpen={tab === "phone-alerts"} />}
        </div>
      </SegmentedTabs>
    </PreferencePane>
  );
}

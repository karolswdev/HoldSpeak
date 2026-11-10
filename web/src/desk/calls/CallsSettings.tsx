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
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { readableError } from "../../lib/api";
import { CommandWell } from "../../pages/cores/connections/ConnectionsPane";
import { openSurfaceOr } from "../shell";
import { DotWord } from "../surface/kit";
import { CheckGadget, GadgetGroup, StringGadget } from "../surface/gadgets";
import { ABSENT_STATUS, OPEN_STEPS, lineInUse, readCallsSettings, readCallsStatus, writeCallsSetting } from "./api";
import type { CallStep, CallStepId, CallsSettings, CallsStatus } from "./types";
import { LINE_RUN_COMMAND, LineSettingsPane } from "./LineSettings";
import { PhoneSettingsPane } from "./PhoneSettings";
import { PreferencePane, SegmentedTabs, ListView, PaneInspector, PaneActions, GadgetRow, type ListVerb } from "../surface";

export const INSTALL_COMMAND = "git clone https://github.com/oxnw/ai-phone.git ~/dev/ai-phone && cd ~/dev/ai-phone && ./scripts/install.sh && uv run ai-phone setup";
export const RUN_COMMAND = "uv run ai-phone run";
export const SIP_COMMAND = "uv run ai-phone lines add sip --id agent --user agent --host <your Mac's tailnet name> --trusted <your iPhone's tailnet IP>";
export const TELNYX_COMMAND = "uv run ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212";
export const TWILIO_COMMAND = "uv run ai-phone lines add twilio --key-env TWILIO_ACCOUNT_SID --secret-env TWILIO_AUTH_TOKEN --existing <your Twilio number>";

/** The first steps when the Line is the phone (the rest are the same). */
const LINE_STEP_LABELS: Partial<Record<CallStepId, string>> = {
  install: "Install the Line",
  daemon: "Start it",
  line: "A line",
};

const STEP_LABELS: Record<CallStepId, string> = {
  install: "Install ai-phone",
  daemon: "Start it",
  line: "A line",
  engine: "The engine",
  passphrase: "A passphrase",
  enable: "Calls",
};

export const EGRESS_SENTENCE = "On a call, the audio goes through your line and its carrier, and the words go to your home engine over Tailscale.";

function StepState({ step }: { step: CallStep }) {
  return (
    <DotWord tone={step.done ? "ok" : "idle"} className="calls-step-state" data-testid={`calls-step-state-${step.id}`}>
      {step.words || (step.done ? "Done" : "Not done")}
    </DotWord>
  );
}

/** One row of the checklist: the step, its state, its one verb; an open
 *  step's command under it. */
function StepRow({ step, state, verb, children, line = false }: { step: CallStep; state?: ReactNode; verb?: ReactNode; children?: ReactNode; line?: boolean }) {
  return (
    <GadgetGroup>
      <GadgetRow label="State">
        <span data-testid={`calls-step-${step.id}`}>{state ?? <StepState step={step} />}</span>
      </GadgetRow>
      {children}
      {verb ? <PaneActions>{verb}</PaneActions> : null}
    </GadgetGroup>
  );
}

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
        placeholder="Words you say first on a call"
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

function NumbersField({ numbers, busy, onSave }: { numbers: string[]; busy: boolean; onSave(next: string[]): void }) {
  const [draft, setDraft] = useState("");
  const add = () => {
    const next = draft.trim();
    if (!next || numbers.includes(next)) return;
    onSave([...numbers, next]);
    setDraft("");
  };
  return (
    <div className="calls-numbers" data-testid="calls-numbers">
      <ListView
        label="Your numbers"
        rows={numbers.map((number, index) => ({
          id: number,
          kind: "number",
          name: number,
          cells: { role: index === 0 ? "Call me rings here" : "May call" },
        }))}
        columns={[
          { key: "name", word: "Number" },
          { key: "role", word: "Use" },
        ]}
        verbs={[
          {
            id: "remove",
            label: "Remove number",
            symbol: "−",
            enabled: (row) => Boolean(row) && !busy,
            run: (row) => onSave(numbers.filter((n) => n !== row!.id)),
          },
        ]}
      />
      <span className="surface-pane-actions">
        <StringGadget
          label="Add a number"
          type="tel"
          value={draft}
          onChange={setDraft}
          placeholder="Your mobile number"
          onKeyDown={(event) => {
            if (event.key === "Enter") add();
          }}
        />
        <Button dense variant="secondary" disabled={busy || !draft.trim()} onClick={add} data-testid="calls-number-add">
          Add
        </Button>
      </span>
    </div>
  );
}

function engineTone(state: CallsStatus["engine"]["state"]): "ok" | "warn" | "idle" {
  return state === "ready" ? "ok" : state === "no_tools" ? "warn" : "idle";
}

/** The pane. It reads the `calls` settings and the status itself; a hub
 *  without the Calls slice draws the checklist with every step open. */
export function CallsSettingsPane({ highlight, onSaved }: { highlight?: string; onSaved?: () => void }) {
  const [tab, setTab] = useState("setup");
  const [picked, pick] = useState<string | null>(null);
  const [editing, edit] = useState<string | null>(null);
  const [settings, setSettings] = useState<CallsSettings | null>(null);
  const [status, setStatus] = useState<CallsStatus>(ABSENT_STATUS);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState("");
  const [refusal, setRefusal] = useState("");
  const [changing, setChanging] = useState(false);

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
      if (rethrow) throw error;
      setRefusal(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const onLine = lineInUse(status);
  const steps = status.steps.length ? status.steps : OPEN_STEPS;
  const absent = settings == null;
  const passphraseSet = Boolean(settings?.passphrase_set ?? status.passphrase_set);
  const step = (id: CallStepId): CallStep => steps.find((entry) => entry.id === id) ?? { id, done: false, words: "" };

  const lineRows: Partial<Record<CallStepId, ReactNode>> = {
    install: <StepRow line step={step("install")} />,
    daemon: (
      <StepRow line step={step("daemon")}>
        {step("daemon").done ? null : <CommandWell hint={LINE_RUN_COMMAND} />}
      </StepRow>
    ),
    line: <StepRow line step={step("line")} />,
  };
  const rows: Record<CallStepId, ReactNode> = {
    install: (
      <StepRow step={step("install")}>
        {step("install").done ? null : <CommandWell hint={INSTALL_COMMAND} />}
        <div className="surface-preference-pane" data-highlight={highlight === "calls-checkout" || undefined}>
          <span className="calls-field-label">Checkout</span>
          <CheckoutField value={settings?.aiphone_dir ?? ""} busy={busy === "aiphone_dir"} onSave={(next) => void write("aiphone_dir", next)} />
        </div>
      </StepRow>
    ),
    daemon: <StepRow step={step("daemon")}>{step("daemon").done ? null : <CommandWell hint={RUN_COMMAND} />}</StepRow>,
    line: (
      <StepRow step={step("line")}>
        {step("line").done ? null : (
          <>
            <p className="calls-step-say">A SIP address is free and stays on your tailnet.</p>
            <CommandWell hint={SIP_COMMAND} />
          </>
        )}
        <p className="calls-step-say">A real number: Telnyx.</p>
        <CommandWell hint={TELNYX_COMMAND} />
        <p className="calls-step-say">Twilio, for a number you have.</p>
        <CommandWell hint={TWILIO_COMMAND} />
      </StepRow>
    ),
    engine: (
      <StepRow
        step={step("engine")}
        state={
          <DotWord tone={engineTone(status.engine.state)} className="calls-step-state" data-testid="calls-step-state-engine">
            {status.engine.state === "ready" ? "Ready" : status.engine.state === "no_tools" ? "No tools" : "None"}
          </DotWord>
        }
        verb={
          <Button dense variant="secondary" onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="calls-engines">
            Engines ›
          </Button>
        }
      >
        <div className="calls-engine" data-testid="calls-engine">
          <span className="calls-engine-model">{status.engine.model || "No engine for calls"}</span>
        </div>
      </StepRow>
    ),
    passphrase: (
      <StepRow
        step={step("passphrase")}
        state={
          <DotWord tone={passphraseSet ? "ok" : "idle"} className="calls-step-state" data-testid="calls-step-state-passphrase">
            <span data-testid={passphraseSet ? "calls-passphrase-set" : undefined}>{passphraseSet ? "Set" : "Not set"}</span>
          </DotWord>
        }
        verb={
          passphraseSet && !changing ? (
            <Button dense variant="secondary" onClick={() => setChanging(true)} data-testid="calls-passphrase-change">
              Change
            </Button>
          ) : null
        }
      >
        {!passphraseSet || changing ? (
          <div className="surface-preference-pane" data-highlight={highlight === "calls-passphrase" || undefined}>
            <span className="calls-field-label">Passphrase</span>
            <PassphraseField busy={busy === "passphrase"} onSave={(next) => void write("passphrase", next)} onCancel={passphraseSet ? () => setChanging(false) : undefined} />
          </div>
        ) : null}
      </StepRow>
    ),
    enable: (
      <StepRow
        step={step("enable")}
        state={
          <DotWord tone={settings?.enabled ? "ok" : "idle"} className="calls-step-state" data-testid="calls-step-state-enable">
            {settings?.enabled ? "On" : "Off"}
          </DotWord>
        }
        verb={<CheckGadget label="Calls on" checked={Boolean(settings?.enabled)} disabled={absent || busy === "enabled"} onChange={(next) => void write("enabled", next)} />}
      />
    ),
  };

  const listSteps = [
    ...steps.filter((entry) => entry.id in rows),
    {
      id: "numbers",
      done: Boolean(settings?.allowed_numbers?.length),
      words: "",
    },
  ];
  const verbs: ListVerb[] = [
    {
      id: "edit",
      label: "Set up…",
      key: "Enter",
      enabled: (row) => Boolean(row),
      run: (row) => edit(row!.id),
    },
  ];
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
          { id: "line", label: "Line" },
          { id: "phone", label: "Phone" },
        ]}
      >
        <div className="surface-tab-panel" hidden={tab !== "setup"}>
          {editing ? (
            <PaneInspector label={editing === "numbers" ? "Your numbers" : (onLine && LINE_STEP_LABELS[editing as CallStepId]) || STEP_LABELS[editing as CallStepId]} onClose={() => edit(null)}>
              {editing === "numbers" ? (
                <NumbersField numbers={settings?.allowed_numbers ?? []} busy={busy === "allowed_numbers"} onSave={(next) => void write("allowed_numbers", next)} />
              ) : (
                (onLine && lineRows[editing as CallStepId]) || rows[editing as CallStepId]
              )}
            </PaneInspector>
          ) : (
            <>
              <ListView
                label="Set up calls"
                ordered
                rows={listSteps.map((entry) => ({
                  id: entry.id,
                  kind: "setting",
                  name: entry.id === "numbers" ? "Your numbers" : (onLine && LINE_STEP_LABELS[entry.id as CallStepId]) || STEP_LABELS[entry.id as CallStepId],
                  cells: {
                    needs: entry.done ? "" : entry.words || "Set up",
                  },
                }))}
                columns={[
                  { key: "name", word: "Setting", track: "minmax(0, 2fr)" },
                  { key: "needs", word: "Needs you" },
                ]}
                selectedId={picked}
                onSelect={pick}
                verbs={verbs}
                defaultVerb="edit"
              />
              <span className="gadget-fact" data-testid="calls-egress">
                {EGRESS_SENTENCE}
              </span>
            </>
          )}
        </div>
        <div className="surface-tab-panel" hidden={tab !== "line"}>
          {settings?.line ? <LineSettingsPane settings={settings} onWrite={(key, value) => write(key, value, true)} onReload={load} /> : <span>Line is not set up</span>}
        </div>
        <div className="surface-tab-panel" hidden={tab !== "phone"}>
          {absent ? <span>Calls is not set up</span> : <PhoneSettingsPane />}
        </div>
      </SegmentedTabs>
    </PreferencePane>
  );
}

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
 * (the read says `passphrase_set`, never the value). */
import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { readableError } from "../../lib/api";
import { CommandWell } from "../../pages/cores/connections/ConnectionsPane";
import { openSurfaceOr } from "../shell";
import { DotWord } from "../surface/kit";
import { CheckGadget, GadgetGroup, StringGadget } from "../surface/gadgets";
import { ABSENT_STATUS, OPEN_STEPS, readCallsSettings, readCallsStatus, writeCallsSetting } from "./api";
import type { CallStep, CallStepId, CallsSettings, CallsStatus } from "./types";
import "./calls.css";

export const INSTALL_COMMAND =
  "git clone https://github.com/oxnw/ai-phone.git ~/dev/ai-phone && cd ~/dev/ai-phone && ./scripts/install.sh && uv run ai-phone setup";
export const RUN_COMMAND = "uv run ai-phone run";
export const SIP_COMMAND =
  "uv run ai-phone lines add sip --id agent --user agent --host <your Mac's tailnet name> --trusted <your iPhone's tailnet IP>";
export const TELNYX_COMMAND = "uv run ai-phone lines add telnyx --key-env TELNYX_API_KEY --country US --area 212";
export const TWILIO_COMMAND =
  "uv run ai-phone lines add twilio --key-env TWILIO_ACCOUNT_SID --secret-env TWILIO_AUTH_TOKEN --existing <your Twilio number>";

const STEP_LABELS: Record<CallStepId, string> = {
  install: "Install ai-phone",
  daemon: "Start it",
  line: "A line",
  engine: "The engine",
  passphrase: "A passphrase",
  enable: "Calls",
};

export const EGRESS_SENTENCE =
  "On a call, the audio goes through your line and its carrier, and the words go to your home engine over Tailscale.";

function StepState({ step }: { step: CallStep }) {
  return (
    <DotWord tone={step.done ? "ok" : "idle"} className="calls-step-state" data-testid={`calls-step-state-${step.id}`}>
      {step.words || (step.done ? "Done" : "Not done")}
    </DotWord>
  );
}

/** One row of the checklist: the step, its state, its one verb; an open
 *  step's command under it. */
function StepRow({ step, state, verb, children }: { step: CallStep; state?: ReactNode; verb?: ReactNode; children?: ReactNode }) {
  return (
    <div className="calls-step" data-step={step.id} data-done={step.done || undefined} data-testid={`calls-step-${step.id}`}>
      <div className="calls-step-line">
        <span className="calls-step-name">{STEP_LABELS[step.id]}</span>
        {state ?? <StepState step={step} />}
        <span className="calls-step-verb">{verb}</span>
      </div>
      {children ? <div className="calls-step-body">{children}</div> : null}
    </div>
  );
}

/** The write-only passphrase field: the value is never read back. */
function PassphraseField({ busy, onSave, onCancel }: { busy: boolean; onSave(value: string): void; onCancel?: () => void }) {
  const [draft, setDraft] = useState("");
  const save = () => { if (draft.trim()) onSave(draft.trim()); };
  return (
    <span className="calls-field-line">
      <StringGadget
        label="Passphrase"
        type="password"
        mic={false}
        value={draft}
        onChange={setDraft}
        placeholder="Words you say first on a call"
        onKeyDown={(event) => { if (event.key === "Enter") save(); }}
        inputProps={{ autoComplete: "new-password" }}
      />
      <Button dense variant="primary" loading={busy} disabled={!draft.trim()} onClick={save} data-testid="calls-passphrase-save">Save</Button>
      {onCancel ? <Button dense variant="ghost" onClick={onCancel}>Cancel</Button> : null}
    </span>
  );
}

function CheckoutField({ value, busy, onSave }: { value: string; busy: boolean; onSave(value: string): void }) {
  const [draft, setDraft] = useState(value);
  useEffect(() => setDraft(value), [value]);
  const changed = draft.trim() !== value;
  return (
    <span className="calls-field-line">
      <StringGadget
        label="ai-phone checkout"
        value={draft}
        onChange={setDraft}
        placeholder="~/dev/ai-phone"
        onKeyDown={(event) => { if (event.key === "Enter" && changed) onSave(draft.trim()); }}
      />
      <Button dense variant="secondary" loading={busy} disabled={!changed} onClick={() => onSave(draft.trim())} data-testid="calls-checkout-save">Save</Button>
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
      {numbers.map((number, index) => (
        <div className="calls-number" key={number} data-testid="calls-number">
          <span className="calls-number-value">{number}</span>
          <span className="calls-number-role">{index === 0 ? "Call me rings this number" : "May call"}</span>
          <Button dense variant="ghost" disabled={busy} onClick={() => onSave(numbers.filter((n) => n !== number))}>Remove</Button>
        </div>
      ))}
      <span className="calls-field-line">
        <StringGadget
          label="Add a number"
          type="tel"
          value={draft}
          onChange={setDraft}
          placeholder="Your mobile number"
          onKeyDown={(event) => { if (event.key === "Enter") add(); }}
        />
        <Button dense variant="secondary" disabled={busy || !draft.trim()} onClick={add} data-testid="calls-number-add">Add</Button>
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
  useEffect(() => { void load(); }, [load]);
  /* DELIGHT slice 4 (2026-10-28): a step's dot turns with the task tick's
     settle (kit.css `data-turns`) when a write changes it. The switch is
     set two frames after the first read, so nothing turns on load. */
  const [turns, setTurns] = useState(false);
  useEffect(() => {
    if (!loaded) return;
    let second = 0;
    const first = window.requestAnimationFrame(() => { second = window.requestAnimationFrame(() => setTurns(true)); });
    return () => { window.cancelAnimationFrame(first); window.cancelAnimationFrame(second); };
  }, [loaded]);

  const write = async (key: keyof CallsSettings | "passphrase", value: unknown) => {
    setBusy(key);
    setRefusal("");
    try {
      const next = await writeCallsSetting(key, value);
      if (key === "passphrase") setChanging(false);
      if (next) setSettings(next);
      else setSettings((now) => now ? { ...now, ...(key === "passphrase" ? { passphrase_set: true } : { [key]: value }) } : now);
      onSaved?.();
      setStatus(await readCallsStatus());
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setBusy("");
    }
  };

  const steps = status.steps.length ? status.steps : OPEN_STEPS;
  const absent = settings == null;
  const passphraseSet = Boolean(settings?.passphrase_set ?? status.passphrase_set);
  const step = (id: CallStepId): CallStep => steps.find((entry) => entry.id === id) ?? { id, done: false, words: "" };

  const rows: Record<CallStepId, ReactNode> = {
    install: (
      <StepRow step={step("install")}>
        {step("install").done ? null : <CommandWell hint={INSTALL_COMMAND} />}
        <div className="calls-field" data-highlight={highlight === "calls-checkout" || undefined}>
          <span className="calls-field-label">Checkout</span>
          <CheckoutField value={settings?.aiphone_dir ?? ""} busy={busy === "aiphone_dir"} onSave={(next) => void write("aiphone_dir", next)} />
        </div>
      </StepRow>
    ),
    daemon: (
      <StepRow step={step("daemon")}>
        {step("daemon").done ? null : <CommandWell hint={RUN_COMMAND} />}
      </StepRow>
    ),
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
        verb={<Button dense variant="secondary" onClick={() => openSurfaceOr("configure-runs-on", "/models")} data-testid="calls-engines">Engines ›</Button>}
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
        verb={passphraseSet && !changing ? (
          <Button dense variant="secondary" onClick={() => setChanging(true)} data-testid="calls-passphrase-change">Change</Button>
        ) : null}
      >
        {!passphraseSet || changing ? (
          <div className="calls-field" data-highlight={highlight === "calls-passphrase" || undefined}>
            <span className="calls-field-label">Passphrase</span>
            <PassphraseField
              busy={busy === "passphrase"}
              onSave={(next) => void write("passphrase", next)}
              onCancel={passphraseSet ? () => setChanging(false) : undefined}
            />
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
        verb={
          <CheckGadget
            label="Calls on"
            checked={Boolean(settings?.enabled)}
            disabled={absent || busy === "enabled"}
            onChange={(next) => void write("enabled", next)}
          />
        }
      />
    ),
  };

  return (
    <div className="calls-settings" data-testid="calls-settings" aria-busy={loaded ? undefined : true} data-turns={turns || undefined}>
      {refusal ? <p className="calls-refusal" role="alert">{refusal}</p> : null}
      <GadgetGroup material="inset" label="Set up calls">
        <div className="calls-steps" data-testid="calls-steps">
          {steps.filter((entry) => entry.id in rows).map((entry) => (
            <div key={entry.id} className="calls-step-slot">
              {rows[entry.id]}
              {entry.id === "passphrase" ? (
                <div className="calls-step" data-step="numbers" data-testid="calls-step-numbers">
                  <div className="calls-step-line">
                    <span className="calls-step-name">Your numbers</span>
                    <DotWord tone={settings?.allowed_numbers?.length ? "ok" : "idle"} className="calls-step-state">
                      {settings?.allowed_numbers?.length ? "Set" : "Any caller"}
                    </DotWord>
                    <span className="calls-step-verb" />
                  </div>
                  <div className="calls-step-body">
                    <NumbersField numbers={settings?.allowed_numbers ?? []} busy={busy === "allowed_numbers"} onSave={(next) => void write("allowed_numbers", next)} />
                  </div>
                </div>
              ) : null}
            </div>
          ))}
        </div>
      </GadgetGroup>
      <GadgetGroup material="inset" label="On a call, HoldSpeak may">
        <div className="calls-may" data-testid="calls-may">
          <div className="calls-may-row"><span>Read, write notes and tasks, prepare sends</span><span className="calls-fact">Yes</span></div>
          <div className="calls-may-row"><span>Send or nudge</span><span className="calls-fact">Only after you say yes</span></div>
        </div>
      </GadgetGroup>
      <p className="calls-egress" data-testid="calls-egress">{EGRESS_SENTENCE}</p>
    </div>
  );
}

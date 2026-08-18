// HS-95-07 / HS-111-01 — the Settings core, rethought as the OS's own
// Prefs program (the verified audit at .tmp/hs-111-01-audit.md §3):
// a drawer face of authored pref modules; a module swaps the WHOLE
// window body; the footer status bar carries the receipt and the
// refusals; every control is a gadget from the surface kit. The pane
// roster is a code constant — the wire never mints a pane again.
import { useEffect, useRef, useState, type ReactNode } from "react";
import type {
  CoreProps,
  SecretState,
  SettingsResponse,
  AuthorityPolicyResponse,
} from "./core-types";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError } from "../../lib/api";
import { useResource } from "../pageSupport";
import { SurfaceState } from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  PropGadget,
  SecretRow,
  StepperGadget,
  StringGadget,
  type CycleOption,
} from "../../desk/surface/gadgets";
import { HotkeyCapture } from "./settingsBespoke";
import { toggleSfx } from "../../lib/sfx";
import { ModelsModule } from "./settingsModels";
import { RuntimeDocsCore } from "./RuntimeDocsCore";
import { useCoreWings } from "./core-hooks";
// HS-139-05: activateLauncher removed (Delivery tile absorbed).
import {
  CADENCE_PRESSURE_OPTIONS,
  LANGUAGE_OPTIONS,
  DeskModule,
  MIR_PROFILE_OPTIONS,
  MODULE_ALIASES,
  PREF_MODULES,
  PrefsFace,
  PrefStatusBar,
  WAKE_ACTION_OPTIONS,
  meetingPlacement,
  placementLine,
  providerIgnoredReason,
} from "./settingsPrefs";

const SECRET_LABELS: Record<string, string> = {
  web_token: "Web pairing token",
  device_psk: "Device audio key",
  telegram_bot_token: "Telegram bot token",
  telegram_pairing_code: "Telegram pairing code",
  failure_webhook_url: "Failure alert webhook",
  failure_webhook_credential: "Failure alert credential",
  slack_webhook_url: "Slack webhook",
  companion_webhook_url: "Custom webhook",
};
const ROTATABLE_SECRETS = new Set([
  "web_token",
  "device_psk",
  "telegram_pairing_code",
]);

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}
/* HS-101 round 4 — the glass never wears wire keys: curated names
 * for the fields people actually meet, an acronym dictionary for the
 * rest. */
const FRIENDLY_FIELDS: Record<string, string> = {
  mlx_model: "MLX model",
  llama_cpp_model_path: "llama.cpp model file",
  profile_id: "Runs on",
  max_total_latency_ms: "Latency budget",
  journal_retention: "Journal retention",
  n_ctx: "Context window",
};
const ACRONYMS: Record<string, string> = {
  Mlx: "MLX",
  Openai: "OpenAI",
  Api: "API",
  Url: "URL",
  Id: "ID",
  Ui: "UI",
  Llm: "LLM",
  Cpp: "C++",
  Ms: "ms",
  Env: "env",
  Ip: "IP",
  Db: "DB",
  Vad: "VAD",
  Mir: "MIR",
};

function title(key: string) {
  const curated = FRIENDLY_FIELDS[key];
  if (curated) return curated;
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (value) => value.toUpperCase())
    .split(" ")
    .map((word) => ACRONYMS[word] ?? word)
    .join(" ");
}

const SETTINGS_WINGS = [
  { id: "settings", label: "Settings" },
  { id: "guide", label: "Guide" },
];

export function SettingsCore({ hero, scope }: CoreProps) {
  // HS-100-10 — the Runtime guide is the Guide wing (the standalone
  // doc-window died; deep links land here via the registry alias).
  const wings = useCoreWings(SETTINGS_WINGS, scope === "guide" ? "guide" : "settings");
  if (wings.view === "guide") return <RuntimeDocsCore />;
  return <SettingsFace hero={hero} scope={scope} />;
}

function SettingsFace({ hero, scope }: CoreProps) {
  const integrationSubject =
    scope && scope.startsWith("integration:")
      ? scope.slice("integration:".length)
      : null;
  // HS-139-05: resolve aliases from the retired 14-tile roster to the new 7.
  const resolvedScope = scope ? (MODULE_ALIASES[scope] ?? scope) : scope;
  const scopedModule = PREF_MODULES.some((module) => module.id === resolvedScope)
    ? (resolvedScope ?? null)
    : null;
  const resource = useResource<SettingsResponse>("/api/settings", {});
  const authority = useResource<AuthorityPolicyResponse>("/api/authority/policy", {});
  // null = the drawer face; a module id = that module owns the body.
  const [moduleId, setModuleId] = useState<string | null>(
    integrationSubject ? "integrations" : scopedModule,
  );
  const [highlight, setHighlight] = useState("");
  const [saving, setSaving] = useState(false);
  const [writtenAt, setWrittenAt] = useState("");
  const [refusal, setRefusal] = useState("");
  const [secretBusy, setSecretBusy] = useState("");
  const [authorityBusy, setAuthorityBusy] = useState(false);
  const secrets = (resource.data._secrets ?? {}) as Record<string, SecretState>;

  /* HS-101 round 3 — the configuring archetype saves ON CHANGE
     (Article VII: no ceremony): every edit lands debounced. HS-111-01:
     the receipt is the footer status bar (USING · WRITTEN hh:mm:ss);
     a refusal replaces it in the danger tone until the next edit. */
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  // HS-130-07: Settings is the canonical full-document writer. It threads the
  // FRESHEST `_revision` (via a ref, not the possibly-stale debounced draft)
  // so its own back-to-back saves never self-conflict, while a genuinely
  // concurrent write from another surface is still rejected + reconciled.
  const revisionRef = useRef<string | undefined>(undefined);
  revisionRef.current = resource.data._revision;
  const save = async (payload?: Record<string, unknown>) => {
    setSaving(true);
    setRefusal("");
    try {
      const body = payload ?? resource.data;
      const result = await apiFetch<{ settings?: Record<string, unknown> }>(
        "/api/settings",
        {
          method: "PUT",
          json: revisionRef.current
            ? { ...body, _revision: revisionRef.current }
            : body,
        },
      );
      resource.setData(result.settings ?? payload ?? resource.data);
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setSaving(false);
    }
  };
  const update = (path: string[], next: unknown) => {
    const draft = clone(resource.data);
    let cursor = draft;
    path.forEach((part, index) => {
      if (index === path.length - 1) cursor[part] = next;
      else cursor = cursor[part] as Record<string, unknown>;
    });
    resource.setData(draft);
    setRefusal("");
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => void save(draft), 700);
  };

  const changeSecret = async (
    secretId: string,
    action: "replace" | "rotate" | "delete",
    value?: string,
  ) => {
    setSecretBusy(secretId);
    setRefusal("");
    try {
      if (action === "replace") {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "PUT",
          json: { value },
        });
      } else if (action === "rotate") {
        await apiFetch(`/api/settings/secrets/${secretId}/rotate`, {
          method: "POST",
        });
      } else {
        await apiFetch(`/api/settings/secrets/${secretId}`, {
          method: "DELETE",
        });
      }
      await resource.reload();
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setSecretBusy("");
    }
  };

  const setControlMode = async (controlMode: string) => {
    setAuthorityBusy(true);
    setRefusal("");
    try {
      const result = await apiFetch<Record<string, unknown>>("/api/authority/control-mode", {
        method: "PUT",
        json: { control_mode: controlMode },
      });
      authority.setData({ ...authority.data, ...result });
      setWrittenAt(new Date().toTimeString().slice(0, 8));
    } catch (error) {
      setRefusal(readableError(error));
    } finally {
      setAuthorityBusy(false);
    }
  };

  // A scope names the focused module. Integration links retain their
  // subject alias while the palette can address every module directly.
  // HS-139-05: aliases from the retired 14-tile roster land here too.
  useEffect(() => {
    if (integrationSubject) setModuleId("integrations");
    else if (scopedModule) setModuleId(scopedModule);
  }, [integrationSubject, scopedModule]);

  // HS-139-05: deep-index and filter removed — 7 tiles all visible at once.
  const openModule = (id: string) => {
    setModuleId(id);
    setHighlight("");
  };

  /* ── gadget bindings (plain function helpers — never components
        defined in render, which would remount and drop focus) ── */
  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object"
          ? (acc as Record<string, unknown>)[part]
          : undefined,
      resource.data,
    );
  const hl = (path: string[]) => highlight === path.join(".");
  const check = (path: string[], label: string, fact?: string) => (
    <GadgetRow key={path.join(".")} label={label} fact={fact} highlight={hl(path)}>
      <CheckGadget
        label={label}
        checked={Boolean(val(path))}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const str = (
    path: string[],
    label: string,
    opts?: { placeholder?: string; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
    >
      <StringGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        placeholder={opts?.placeholder}
        onChange={(next) => update(path, next || null)}
      />
    </GadgetRow>
  );
  const num = (
    path: string[],
    label: string,
    opts?: { unit?: string; step?: number; min?: number; max?: number },
  ) => (
    <GadgetRow key={path.join(".")} label={label} highlight={hl(path)}>
      <StepperGadget
        label={label}
        value={Number(val(path) ?? 0)}
        unit={opts?.unit}
        step={opts?.step}
        min={opts?.min}
        max={opts?.max}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const cyc = (
    path: string[],
    label: string,
    options: CycleOption[],
    fact?: string,
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={fact}
      highlight={hl(path)}
    >
      <CycleGadget
        label={label}
        value={val(path) == null ? "" : String(val(path))}
        options={options}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const prop = (
    path: string[],
    label: string,
    opts?: { min?: number; max?: number; step?: number; fact?: string },
  ) => (
    <GadgetRow
      key={path.join(".")}
      label={label}
      fact={opts?.fact}
      highlight={hl(path)}
    >
      <PropGadget
        label={label}
        value={Number(val(path) ?? opts?.min ?? 0)}
        min={opts?.min}
        max={opts?.max}
        step={opts?.step}
        onChange={(next) => update(path, next)}
      />
    </GadgetRow>
  );
  const csv = (path: string[], label: string, fact = "comma-separated") => (
    <GadgetRow key={path.join(".")} label={label} fact={fact} highlight={hl(path)}>
      <StringGadget
        label={label}
        value={Array.isArray(val(path)) ? (val(path) as unknown[]).join(", ") : ""}
        onChange={(next) =>
          update(
            path,
            next
              .split(",")
              .map((part) => part.trim())
              .filter(Boolean),
          )
        }
      />
    </GadgetRow>
  );

  /* HS-132-10 — the hub's meetings-placement provenance. Meetings states
     where its intelligence runs and which dial decided; the dial itself
     lives in Models (one control, one home). */
  const placement = meetingPlacement(resource.data);
  const providerIgnored = placement ? providerIgnoredReason(placement) : "";

  /* ── the generic walker: survives ONLY inside System (§3.2) ── */
  const walkerRows = (node: Record<string, unknown>, path: string[]): ReactNode[] =>
    Object.entries(node).map(([key, item]) => {
      const nextPath = [...path, key];
      if (item !== null && typeof item === "object" && !Array.isArray(item))
        return (
          <GadgetGroup key={nextPath.join(".")} label={title(key)}>
            {walkerRows(item as Record<string, unknown>, nextPath)}
          </GadgetGroup>
        );
      if (typeof item === "boolean") return check(nextPath, title(key));
      if (typeof item === "number") return num(nextPath, title(key));
      if (Array.isArray(item)) return csv(nextPath, title(key));
      return str(nextPath, title(key));
    });

  /* ── the authored modules (HS-139-05: seven tiles) ── */
  const renderModule = (id: string): ReactNode => {
    const data = resource.data;
    switch (id) {
      /* ── Voice: hotkey + language + voice typing + wake word ── */
      case "voice": {
        const symbols = (val(["dictation", "spoken_symbols"]) ?? []) as Array<{
          spoken?: string;
          symbol?: string;
          attach?: string;
        }>;
        const symbolsPath = ["dictation", "spoken_symbols"];
        const patchSymbol = (index: number, patch: Record<string, string>) =>
          update(
            symbolsPath,
            symbols.map((entry, row) =>
              row === index ? { ...entry, ...patch } : entry,
            ),
          );
        const macroItems = (val(["dictation", "macros", "items"]) ??
          []) as unknown[];
        return (
          <>
            <HotkeyCapture
              value={(data.hotkey ?? {}) as Record<string, unknown>}
              onCommit={(next) =>
                update(["hotkey"], { ...(data.hotkey as Record<string, unknown>), ...next })
              }
              onRefuse={setRefusal}
            />
            <GadgetGroup label="Transcription">
              {cyc(["model", "language"], "Language", LANGUAGE_OPTIONS)}
            </GadgetGroup>
            <GadgetGroup label="Typing">
              {check(["dictation", "preview_before_type"], "Preview before type")}
              {check(
                ["dictation", "macros", "enabled"],
                "Voice commands",
                `${macroItems.length} configured`,
              )}
            </GadgetGroup>
            <GadgetGroup label="Spoken symbols">
              <GadgetRow
                wide
                label="Dictionary"
                highlight={hl(symbolsPath)}
              >
                <GadgetTable
                  head={["SPOKEN", "SYMBOL", "ATTACH"]}
                  deleteLabel="FORGET?"
                  onDelete={(index) =>
                    update(
                      symbolsPath,
                      symbols.filter((_, row) => row !== index),
                    )
                  }
                  onAdd={() =>
                    update(symbolsPath, [
                      ...symbols,
                      { spoken: "", symbol: "", attach: "none" },
                    ])
                  }
                  rows={symbols.map((entry, index) => [
                    <StringGadget
                      key="spoken"
                      label={`Spoken phrase ${index + 1}`}
                      value={entry.spoken ?? ""}
                      placeholder="arrow"
                      onChange={(next) => patchSymbol(index, { spoken: next })}
                    />,
                    <StringGadget
                      key="symbol"
                      label={`Symbol ${index + 1}`}
                      value={entry.symbol ?? ""}
                      placeholder="→"
                      mic={false}
                      onChange={(next) => patchSymbol(index, { symbol: next })}
                    />,
                    <CycleGadget
                      key="attach"
                      label={`Attachment ${index + 1}`}
                      value={entry.attach ?? "none"}
                      options={[
                        { value: "none" },
                        { value: "left" },
                        { value: "right" },
                        { value: "both" },
                      ]}
                      onChange={(next) => patchSymbol(index, { attach: next })}
                    />,
                  ])}
                />
              </GadgetRow>
            </GadgetGroup>
            <GadgetGroup label="Wake word">
              {check(["wake_word", "enabled"], "Enabled", "models download once")}
              {cyc(
                ["wake_word", "action"],
                "Action",
                WAKE_ACTION_OPTIONS,
                "type lands in the focused app",
              )}
            </GadgetGroup>
            {/* HS-139-04/05: all voice RAW wells merged. */}
            <FoldGadget title="RAW" token="10">
              <GadgetGroup label="Transcription">
                {num(["model", "transcribe_timeout_seconds"], "Transcribe timeout", {
                  unit: "s",
                  min: 5,
                  step: 5,
                })}
              </GadgetGroup>
              <GadgetGroup label="Pipeline">
                {csv(["dictation", "pipeline", "stages"], "Stages")}
                {num(
                  ["dictation", "pipeline", "max_total_latency_ms"],
                  "Latency budget",
                  { unit: "ms", min: 0, step: 250 },
                )}
                {str(
                  ["dictation", "pipeline", "target_profile_override"],
                  "Target profile override",
                )}
                {num(["dictation", "pipeline", "rewrite_passes"], "Rewrite passes", {
                  min: 0,
                  max: 5,
                })}
                {check(
                  ["dictation", "pipeline", "target_detect_llm_enabled"],
                  "LLM target detect",
                )}
                {prop(
                  ["dictation", "pipeline", "target_detect_llm_below"],
                  "Detect below",
                  { min: 0, max: 1, step: 0.05 },
                )}
              </GadgetGroup>
              <GadgetGroup label="Wake word">
                {str(["wake_word", "model"], "Model", {
                  placeholder: "hey_jarvis",
                })}
                {prop(["wake_word", "threshold"], "Threshold", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
                {num(["wake_word", "armed_window_seconds"], "Armed window", {
                  unit: "s",
                  min: 1,
                  step: 1,
                })}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      }
      /* ── Sounds & Presence: desk sounds + presence + mascot ── */
      case "sounds":
        return (
          <>
            <GadgetGroup label="Sounds">
              <GadgetRow label="DESK SOUNDS" highlight={hl(["ui", "desk_sounds"])}>
                <CheckGadget
                  label="DESK SOUNDS"
                  checked={Boolean(val(["ui", "desk_sounds"]) ?? true)}
                  onChange={(next) => {
                    update(["ui", "desk_sounds"], next);
                    toggleSfx(next);
                  }}
                />
              </GadgetRow>
            </GadgetGroup>
            <GadgetGroup label="Presence">
              {check(["presence", "enabled"], "Presence")}
              {check(["presence", "mascot"], "Mascot")}
            </GadgetGroup>
          </>
        );
      /* ── Meetings: pointer tile + actuators + RAW ── */
      case "meetings":
        return (
          <>
            <GadgetGroup label="Capture + export">
              <div className="prefs-elsewhere">
                <span className="prefs-elsewhere-fact">
                  CONFIG LIVES ON MEETINGS
                </span>
              </div>
            </GadgetGroup>
            <GadgetGroup label="Actuators">
              {check(["meeting", "allow_actuators"], "Allow actuators")}
            </GadgetGroup>
            <GadgetGroup label="Intelligence">
              <div className="prefs-elsewhere">
                <span className="prefs-elsewhere-fact">
                  PLACEMENT LIVES IN MODELS
                </span>
                {placement ? (
                  <span className="prefs-elsewhere-fact">
                    {placementLine(placement)}
                  </span>
                ) : null}
                {providerIgnored ? (
                  <span className="prefs-elsewhere-fact" role="status">
                    {providerIgnored}
                  </span>
                ) : null}
                <Button dense onClick={() => openModule("models")}>
                  Open Models
                </Button>
              </div>
            </GadgetGroup>
            {/* HS-139-04: all operator knobs fold behind one RAW well. */}
            <FoldGadget title="RAW" token="20">
              <GadgetGroup label="Capture">
                {check(["meeting", "diarization_enabled"], "Diarization")}
                {check(["meeting", "diarize_mic"], "Diarize mic")}
                {prop(["meeting", "similarity_threshold"], "Similarity", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
              </GadgetGroup>
              <GadgetGroup label="Intelligence">
                {str(["meeting", "intel_summary_model"], "Summary model")}
                {check(["meeting", "intel_cloud_store"], "Cloud store")}
              </GadgetGroup>
              <GadgetGroup label="Deferred queue">
                {num(["meeting", "intel_retry_base_seconds"], "Retry base", {
                  unit: "s",
                  min: 1,
                  step: 5,
                })}
                {num(["meeting", "intel_retry_max_seconds"], "Retry max", {
                  unit: "s",
                  min: 1,
                  step: 60,
                })}
                {num(["meeting", "intel_retry_max_attempts"], "Retry attempts", {
                  min: 0,
                })}
                {str(
                  ["meeting", "intel_retry_failure_webhook_header_name"],
                  "Webhook header",
                )}
              </GadgetGroup>
              <GadgetGroup label="Routing">
                {cyc(
                  ["meeting", "routing_profile"],
                  "Routing profile",
                  MIR_PROFILE_OPTIONS,
                )}
                {check(["meeting", "intent_router_enabled"], "Intent router")}
                {num(["meeting", "intent_window_seconds"], "Intent window", {
                  unit: "s",
                  min: 10,
                  step: 10,
                })}
                {num(["meeting", "intent_step_seconds"], "Intent step", {
                  unit: "s",
                  min: 5,
                  step: 5,
                })}
                {prop(["meeting", "intent_score_threshold"], "Score threshold", {
                  min: 0,
                  max: 1,
                  step: 0.05,
                })}
                {num(
                  ["meeting", "intent_hysteresis_windows"],
                  "Hysteresis windows",
                  { min: 0, max: 10 },
                )}
                {check(
                  ["meeting", "intent_segment_probe_enabled"],
                  "Segment probe",
                )}
                {csv(["meeting", "disabled_plugins"], "Disabled plugins")}
              </GadgetGroup>
              <GadgetGroup label="Actuators">
                {csv(["meeting", "allowed_actuators"], "Allowed actuators")}
                {csv(["meeting", "webhook_allowed_hosts"], "Webhook hosts")}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      /* ── Rhythm: cadence user-facing + Telegram + RAW ── */
      case "rhythm":
        return (
          <>
            <GadgetGroup label="Cadence">
              {check(["cadence", "enabled"], "Enabled")}
              {cyc(["cadence", "pressure"], "Pressure", CADENCE_PRESSURE_OPTIONS)}
              {num(["cadence", "quiet_hours_start"], "Quiet from", {
                unit: "h",
                min: 0,
                max: 23,
              })}
              {num(["cadence", "quiet_hours_end"], "Quiet until", {
                unit: "h",
                min: 0,
                max: 23,
              })}
              {num(["cadence", "max_nudges_per_day"], "Max nudges", {
                unit: "/day",
                min: 0,
              })}
            </GadgetGroup>
            <GadgetGroup label="Telegram">
              {check(["cadence_telegram", "enabled"], "Enabled")}
            </GadgetGroup>
            {/* HS-139-04: operator knobs fold behind RAW. */}
            <FoldGadget title="RAW" token="3">
              <GadgetGroup>
                {check(["cadence", "use_llm"], "Use LLM")}
                {num(["cadence", "tick_interval_seconds"], "Tick interval", {
                  unit: "s",
                  min: 30,
                  step: 30,
                })}
                {csv(["cadence_telegram", "allowed_chat_ids"], "Allowed chats")}
              </GadgetGroup>
            </FoldGadget>
          </>
        );
      /* ── Models: destinations, runs-on, engine, rails ── */
      case "models":
        return (
          <ModelsModule
            settings={data}
            update={update}
            onRefuse={setRefusal}
          />
        );
      /* ── Integrations: credentials + RAW ── */
      case "integrations": {
        const RAW_SECRETS = new Set(["failure_webhook_url", "failure_webhook_credential"]);
        const keepSecrets = Object.entries(secrets).filter(([id]) => !RAW_SECRETS.has(id));
        const rawSecrets = Object.entries(secrets).filter(([id]) => RAW_SECRETS.has(id));
        const secretRow = ([secretId, state]: [string, SecretState]) => (
          <SecretRow
            key={secretId}
            label={SECRET_LABELS[secretId] ?? title(secretId)}
            configured={Boolean(state.configured)}
            destination={state.destination}
            busy={secretBusy === secretId}
            rotatable={ROTATABLE_SECRETS.has(secretId)}
            onReplace={(value) =>
              void changeSecret(secretId, "replace", value)
            }
            onRotate={() => void changeSecret(secretId, "rotate")}
            onDelete={() => void changeSecret(secretId, "delete")}
          />
        );
        return (
          <>
            <GadgetGroup label="Credentials">
              <div className="prefs-egress-line">
                <EgressChip />
                <span className="gadget-fact">values stay on this hub</span>
              </div>
              {keepSecrets.map(secretRow)}
            </GadgetGroup>
            {/* HS-139-04: operator-wiring secrets fold behind RAW. */}
            {rawSecrets.length ? (
              <FoldGadget title="RAW" token={String(rawSecrets.length)}>
                <GadgetGroup>
                  {rawSecrets.map(secretRow)}
                </GadgetGroup>
              </FoldGadget>
            ) : null}
          </>
        );
      }
      /* ── System: device name + desk reset + devices RAW ── */
      case "system": {
        const device = (data.device ?? {}) as Record<string, unknown>;
        const deviceCount = Object.keys(device).length;
        return (
          <>
            <GadgetGroup label="Mesh">
              {str(["mesh", "device_name"], "Device name")}
            </GadgetGroup>
            <DeskModule />
            {/* HS-139-04/05: device walker knobs fold behind RAW. */}
            {deviceCount ? (
              <FoldGadget title="RAW" token={String(deviceCount)}>
                <GadgetGroup label="Device">
                  {walkerRows(device, ["device"])}
                </GadgetGroup>
              </FoldGadget>
            ) : null}
          </>
        );
      }
      default:
        return null;
    }
  };

  const module = moduleId
    ? PREF_MODULES.find((entry) => entry.id === moduleId)
    : null;
  const receipt = { saving, writtenAt, refusal };
  return (
    <>
      {hero ? hero(null) : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        {module ? (
          <div className="prefs-module">
            <h2 className="gadget-pane-title">{module.label}</h2>
            {renderModule(module.id)}
          </div>
        ) : (
          <PrefsFace
            onOpen={openModule}
            posture={String(authority.data.control_mode ?? "neutral")}
            postureBusy={authorityBusy || authority.loading}
            onPosture={(mode) => void setControlMode(mode)}
            precedence={
              Array.isArray(authority.data.precedence)
                ? (authority.data.precedence as string[])
                : []
            }
          />
        )}
      </SurfaceState>
      <PrefStatusBar
        onBack={
          module
            ? () => {
                setModuleId(null);
                setHighlight("");
              }
            : undefined
        }
        receipt={receipt}
      />
    </>
  );
}

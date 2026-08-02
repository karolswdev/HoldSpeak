// HS-95-07 / HS-111-01 — the Settings core, rethought as the OS's own
// Prefs program (the verified audit at .tmp/hs-111-01-audit.md §3):
// a drawer face of authored pref modules; a module swaps the WHOLE
// window body; the footer status bar carries the receipt and the
// refusals; every control is a gadget from the surface kit. The pane
// roster is a code constant — the wire never mints a pane again.
import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import type { CoreProps } from "./ActivityCore";
import { Button } from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { useResource } from "../pageSupport";
import { SurfaceState } from "../../desk/surface/Surface";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  PropGadget,
  SecretRow,
  StepperGadget,
  StringGadget,
  type CycleOption,
} from "../../desk/surface/gadgets";
import { HotkeyCapture, RuntimeDestination } from "./settingsBespoke";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { RuntimeDocsCore } from "./RuntimeDocsCore";
import { activateLauncher } from "../../desk/components/DeskWindow";
import {
  CADENCE_PRESSURE_OPTIONS,
  EXPORT_FORMAT_OPTIONS,
  INTEL_PROVIDER_OPTIONS,
  LANGUAGE_OPTIONS,
  MIR_PROFILE_OPTIONS,
  PREF_MODULES,
  PrefsFace,
  PrefStatusBar,
  THEME_OPTIONS,
  TRANSCRIBE_BACKEND_OPTIONS,
  WAKE_ACTION_OPTIONS,
  WHISPER_MODEL_OPTIONS,
  moduleForKey,
  type DeepHit,
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
type SecretState = { configured?: boolean; destination?: string };

function clone<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T;
}
/* HS-101 round 4 — the glass never wears wire keys: curated names
 * for the fields people actually meet, an acronym dictionary for the
 * rest. */
const FRIENDLY_FIELDS: Record<string, string> = {
  mlx_model: "MLX model",
  llama_cpp_model_path: "llama.cpp model file",
  openai_compatible_model: "Model (OpenAI-compatible)",
  openai_compatible_base_url: "Endpoint URL",
  openai_compatible_api_key_env: "API key env var",
  profile_id: "Runs on profile",
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
  const [wing, setWing] = useState(scope === "guide" ? "guide" : "settings");
  useWindowWings(
    <SurfaceWings wings={SETTINGS_WINGS} active={wing} onChange={setWing} />,
    [wing],
  );
  if (wing === "guide") return <RuntimeDocsCore />;
  return <SettingsFace hero={hero} scope={scope} />;
}

function SettingsFace({ hero, scope }: CoreProps) {
  const integrationSubject =
    scope && scope.startsWith("integration:")
      ? scope.slice("integration:".length)
      : null;
  const resource = useResource<JsonRecord>("/api/settings", {});
  const authority = useResource<JsonRecord>("/api/authority/policy", {});
  // null = the drawer face; a module id = that module owns the body.
  const [moduleId, setModuleId] = useState<string | null>(
    integrationSubject ? "integrations" : null,
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
  const save = async (payload?: JsonRecord) => {
    setSaving(true);
    setRefusal("");
    try {
      const result = await apiFetch<{ settings?: JsonRecord }>(
        "/api/settings",
        { method: "PUT", json: payload ?? resource.data },
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
      else cursor = cursor[part] as JsonRecord;
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
      const result = await apiFetch<JsonRecord>("/api/authority/control-mode", {
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

  // HS-98-05 / HS-111-01: the `integration:` scope alias opens the
  // Integrations module directly.
  useEffect(() => {
    if (integrationSubject) setModuleId("integrations");
  }, [integrationSubject]);

  /* ── the deep setting index for the drawer filter ── */
  const deepIndex = useMemo<DeepHit[]>(() => {
    const hits: DeepHit[] = [];
    const walk = (node: JsonRecord, path: string[]) => {
      for (const [key, item] of Object.entries(node)) {
        const nextPath = [...path, key];
        const owner =
          nextPath[0] === "dictation" && nextPath[1] === "runtime"
            ? "models"
            : moduleForKey(nextPath[0]);
        if (item !== null && typeof item === "object" && !Array.isArray(item)) {
          walk(item as JsonRecord, nextPath);
        } else {
          hits.push({ module: owner, label: title(key), path: nextPath });
        }
      }
    };
    for (const key of Object.keys(resource.data)) {
      if (key.startsWith("_") || key === "config_version" || key === "control_mode")
        continue;
      const value = resource.data[key];
      if (value && typeof value === "object" && !Array.isArray(value))
        walk(value as JsonRecord, [key]);
    }
    return hits;
  }, [resource.data]);

  const openModule = (id: string, highlightPath?: string) => {
    setModuleId(id);
    setHighlight(highlightPath ?? "");
  };

  /* ── gadget bindings (plain function helpers — never components
        defined in render, which would remount and drop focus) ── */
  const val = (path: string[]): unknown =>
    path.reduce<unknown>(
      (acc, part) =>
        acc && typeof acc === "object"
          ? (acc as JsonRecord)[part]
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

  /* ── the generic walker: survives ONLY inside System (§3.2) ── */
  const walkerRows = (node: JsonRecord, path: string[]): ReactNode[] =>
    Object.entries(node).map(([key, item]) => {
      const nextPath = [...path, key];
      if (item !== null && typeof item === "object" && !Array.isArray(item))
        return (
          <GadgetGroup key={nextPath.join(".")} label={title(key)}>
            {walkerRows(item as JsonRecord, nextPath)}
          </GadgetGroup>
        );
      if (typeof item === "boolean") return check(nextPath, title(key));
      if (typeof item === "number") return num(nextPath, title(key));
      if (Array.isArray(item)) return csv(nextPath, title(key));
      return str(nextPath, title(key));
    });

  /* ── the authored modules (audit §3.2): the wire never decides ── */
  const renderModule = (id: string): ReactNode => {
    const data = resource.data;
    switch (id) {
      case "appearance":
        return (
          <GadgetGroup>
            {check(["ui", "show_audio_meter"], "Show audio meter")}
            {num(["ui", "history_lines"], "History lines", {
              unit: "lines",
              min: 1,
            })}
            {cyc(["ui", "theme"], "Theme", THEME_OPTIONS)}
          </GadgetGroup>
        );
      case "hotkey":
        return (
          <HotkeyCapture
            value={(data.hotkey ?? {}) as JsonRecord}
            onCommit={(next) =>
              update(["hotkey"], { ...(data.hotkey as JsonRecord), ...next })
            }
            onRefuse={setRefusal}
          />
        );
      case "transcription":
        return (
          <GadgetGroup>
            {cyc(["model", "name"], "Model size", WHISPER_MODEL_OPTIONS)}
            {cyc(["model", "backend"], "Backend", TRANSCRIBE_BACKEND_OPTIONS)}
            {cyc(["model", "language"], "Language", LANGUAGE_OPTIONS)}
            {check(["model", "warm_on_start"], "Warm on start")}
            {num(["model", "transcribe_timeout_seconds"], "Transcribe timeout", {
              unit: "s",
              min: 5,
              step: 5,
            })}
          </GadgetGroup>
        );
      case "voice-typing": {
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
            <GadgetGroup label="Pipeline">
              {check(["dictation", "pipeline", "enabled"], "Enabled")}
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
                ["dictation", "pipeline", "corrections_enabled"],
                "Corrections",
              )}
              {check(
                ["dictation", "pipeline", "target_detect_llm_enabled"],
                "LLM target detect",
              )}
              {prop(
                ["dictation", "pipeline", "target_detect_llm_below"],
                "Detect below",
                { min: 0, max: 1, step: 0.05 },
              )}
              {check(["dictation", "pipeline", "journal_enabled"], "Journal")}
              {num(
                ["dictation", "pipeline", "journal_retention"],
                "Journal retention",
                { unit: "entries", min: 0, step: 50 },
              )}
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
          </>
        );
      }
      case "wake-word":
        return (
          <GadgetGroup>
            {/* The honest truths ride as fact tokens (no-prose canon):
                enabling fetches detection models once; the `type` action
                lands unpreviewed in whatever app holds focus. */}
            {check(["wake_word", "enabled"], "Enabled", "models download once")}
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
            {cyc(
              ["wake_word", "action"],
              "Action",
              WAKE_ACTION_OPTIONS,
              "type lands in the focused app",
            )}
          </GadgetGroup>
        );
      case "presence":
        return (
          <GadgetGroup>
            {check(["presence", "enabled"], "Presence")}
            {check(["presence", "mascot"], "Mascot")}
          </GadgetGroup>
        );
      case "meetings":
        return (
          <>
            <GadgetGroup label="Capture">
              {str(["meeting", "mic_device"], "Mic device", {
                fact: "device name",
              })}
              {str(["meeting", "system_audio_device"], "System audio device", {
                fact: "device name",
              })}
              {str(["meeting", "mic_label"], "Mic label")}
              {str(["meeting", "remote_label"], "Remote label")}
              {check(["meeting", "diarization_enabled"], "Diarization")}
              {check(["meeting", "diarize_mic"], "Diarize mic")}
              {check(
                ["meeting", "cross_meeting_recognition"],
                "Cross-meeting recognition",
              )}
              {prop(["meeting", "similarity_threshold"], "Similarity", {
                min: 0,
                max: 1,
                step: 0.05,
              })}
            </GadgetGroup>
            <GadgetGroup label="Export">
              {check(["meeting", "auto_export"], "Auto export")}
              {cyc(["meeting", "export_format"], "Format", EXPORT_FORMAT_OPTIONS)}
              {check(["meeting", "web_auto_open"], "Open on web")}
            </GadgetGroup>
            <GadgetGroup label="Intelligence">
              {check(["meeting", "intel_enabled"], "Enabled")}
              {cyc(["meeting", "intel_provider"], "Provider", INTEL_PROVIDER_OPTIONS)}
              {str(["meeting", "intel_realtime_model"], "Realtime model")}
              {str(["meeting", "intel_summary_model"], "Summary model")}
              {str(["meeting", "intel_cloud_model"], "Cloud model")}
              {str(["meeting", "intel_cloud_base_url"], "Cloud endpoint")}
              {str(["meeting", "intel_cloud_api_key_env"], "API key env var")}
              {check(["meeting", "intel_cloud_store"], "Cloud store")}
              {str(["meeting", "intel_profile_id"], "Runs on profile")}
            </GadgetGroup>
            <GadgetGroup label="Deferred queue">
              {check(["meeting", "intel_deferred_enabled"], "Enabled")}
              {num(["meeting", "intel_queue_poll_seconds"], "Poll", {
                unit: "s",
                min: 10,
                step: 10,
              })}
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
              {num(
                ["meeting", "intel_retry_failure_alert_percent"],
                "Failure alert",
                { unit: "%", min: 0, max: 100, step: 5 },
              )}
              {num(
                ["meeting", "intel_retry_failure_hysteresis_minutes"],
                "Alert hysteresis",
                { unit: "min", min: 0 },
              )}
              {str(
                ["meeting", "intel_retry_failure_webhook_header_name"],
                "Webhook header",
              )}
            </GadgetGroup>
            <GadgetGroup label="Routing">
              {check(["meeting", "mir_enabled"], "Multi-intent routing")}
              {cyc(["meeting", "mir_profile"], "MIR profile", MIR_PROFILE_OPTIONS)}
              {cyc(
                ["meeting", "plugin_profile"],
                "Plugin profile",
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
              {check(["meeting", "allow_actuators"], "Allow actuators")}
              {csv(["meeting", "allowed_actuators"], "Allowed actuators")}
              {csv(["meeting", "webhook_allowed_hosts"], "Webhook hosts")}
              {str(["meeting", "companion_github_repo"], "GitHub repo", {
                placeholder: "owner/repo",
              })}
            </GadgetGroup>
          </>
        );
      case "cadence":
        return (
          <>
            <GadgetGroup label="Cadence">
              {check(["cadence", "enabled"], "Enabled")}
              {cyc(["cadence", "pressure"], "Pressure", CADENCE_PRESSURE_OPTIONS)}
              {check(["cadence", "use_llm"], "Use LLM")}
              {num(["cadence", "tick_interval_seconds"], "Tick interval", {
                unit: "s",
                min: 30,
                step: 30,
              })}
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
              {csv(["cadence_telegram", "allowed_chat_ids"], "Allowed chats")}
            </GadgetGroup>
          </>
        );
      case "devices": {
        const device = (data.device ?? {}) as JsonRecord;
        return (
          <>
            <GadgetGroup label="Mesh">
              {str(["mesh", "device_name"], "Device name")}
            </GadgetGroup>
            {Object.keys(device).length ? (
              <GadgetGroup label="Device">
                {walkerRows(device, ["device"])}
              </GadgetGroup>
            ) : null}
          </>
        );
      }
      case "delivery":
        // No delivery keys live under /api/settings today: the module
        // states the fact and hands over to the Delivery program.
        return (
          <div className="prefs-elsewhere">
            <span className="prefs-elsewhere-fact">CONFIG LIVES IN DELIVERY</span>
            <Button dense onClick={() => activateLauncher("delivery-board")}>
              Open Delivery
            </Button>
          </div>
        );
      case "models":
        return (
          <RuntimeDestination
            value={(val(["dictation", "runtime"]) ?? {}) as JsonRecord}
            onCommit={(next) => update(["dictation", "runtime"], next)}
          />
        );
      case "integrations":
        return (
          <GadgetGroup label="Credentials">
            <div className="prefs-egress-line">
              <EgressChip />
              {/* the credential truth, as a fact token */}
              <span className="gadget-fact">values stay on this hub</span>
            </div>
            {Object.entries(secrets).map(([secretId, state]) => (
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
            ))}
          </GadgetGroup>
        );
      case "system": {
        const claimed = new Set(PREF_MODULES.flatMap((module) => module.keys));
        const systemKeys = Object.keys(data).filter(
          (key) =>
            !key.startsWith("_") &&
            key !== "config_version" &&
            key !== "control_mode" &&
            !claimed.has(key) &&
            data[key] &&
            typeof data[key] === "object" &&
            !Array.isArray(data[key]),
        );
        if (!systemKeys.length)
          return (
            <div className="prefs-elsewhere">
              <span className="prefs-elsewhere-fact">NO UNMAPPED KEYS</span>
            </div>
          );
        return systemKeys.map((key) => (
          <GadgetGroup key={key} label={title(key)}>
            {walkerRows(data[key] as JsonRecord, [key])}
          </GadgetGroup>
        ));
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
            hits={deepIndex}
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

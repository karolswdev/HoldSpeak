// HS-95-07 — the Settings core: the whole cockpit, hosted anywhere.
import { useEffect, useMemo, useRef, useState } from "react";
import type { CoreProps } from "./ActivityCore";
import {
  Button,
  Disclosure,
  Field,
  InlineMessage,
  Select,
  Switch,
  Tabs,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { CONTROL_MODES, controlModeLabel } from "../../lib/productLanguage";
import { PostureNote, useResource } from "../pageSupport";
import {
  ConfirmVerb,
  SurfaceGroup,
  SurfaceSection,
  SurfaceSettingRow,
  SurfaceState,
  SurfaceToggle,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { HotkeyCapture, RuntimeDestination } from "./settingsBespoke";
import { SurfaceWings, useWindowWings } from "../../desk/surface/wings";
import { RuntimeDocsCore } from "./RuntimeDocsCore";

const SECTION_ORDER = [
  "ui",
  "hotkey",
  "model",
  "dictation",
  "wake_word",
  "presence",
  "meeting",
  "activity",
  "cadence",
  "commands",
];
const FRIENDLY: Record<string, string> = {
  ui: "Appearance",
  hotkey: "Hotkey",
  model: "Transcription",
  dictation: "Voice typing",
  wake_word: "Wake Word",
  presence: "Presence",
  meeting: "Meetings & intelligence",
  activity: "Activity",
  cadence: "Cadence",
  commands: "Commands",
};
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
 * rest ("Mlx Model" and "Openai Compatible Api Key Env" are config
 * dump, not settings). */
const FRIENDLY_FIELDS: Record<string, string> = {
  mlx_model: "MLX model",
  llama_cpp_model_path: "llama.cpp model file",
  openai_compatible_model: "Model (OpenAI-compatible)",
  openai_compatible_base_url: "Endpoint URL",
  openai_compatible_api_key_env: "API key env var",
  profile_id: "Runs on profile",
  max_total_latency_ms: "Latency budget (ms)",
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

/** HS-100 spike — the OS settings idiom: leaves render as rows
 * (text left, compact control right) inside grouped inset lists;
 * nested objects become their own labeled groups. Never a form
 * stack. */
function SettingsFields({
  value,
  path,
  query,
  onChange,
}: {
  value: JsonRecord;
  path: string[];
  query: string;
  onChange(path: string[], value: unknown): void;
}) {
  type Leaf = { key: string; item: unknown; path: string[] };
  type Group = { label: string; leaves: Leaf[] };
  // HS-101 round 5 — bespoke components own their complex ideas.
  if (path.length === 1 && path[0] === "hotkey") {
    return (
      <HotkeyCapture
        value={value}
        onCommit={(next) => onChange(path, { ...value, ...next })}
      />
    );
  }
  const groups: Group[] = [];
  const walk = (node: JsonRecord, nodePath: string[], label: string) => {
    const leaves: Leaf[] = [];
    for (const [key, item] of Object.entries(node)) {
      const nextPath = [...nodePath, key];
      if (item !== null && typeof item === "object" && !Array.isArray(item)) {
        if (nextPath.join(".") === "dictation.runtime") {
          groups.push({
            label: "Runtime",
            leaves: [{ key: "__runtime__", item, path: nextPath }],
          });
        } else {
          walk(
            item as JsonRecord,
            nextPath,
            `${label ? label + " · " : ""}${title(key)}`,
          );
        }
      } else if (
        !query ||
        `${nextPath.join(" ")}`.toLowerCase().includes(query.toLowerCase())
      ) {
        leaves.push({ key, item, path: nextPath });
      }
    }
    if (leaves.length) groups.push({ label, leaves });
  };
  walk(value, path, "");
  return (
    <>
      {groups.map((group) => {
        const runtime = group.leaves.find((leaf) => leaf.key === "__runtime__");
        if (runtime) {
          return (
            <div key="runtime">
              <h4 className="surface-panel-title">Runtime</h4>
              <RuntimeDestination
                value={runtime.item as JsonRecord}
                onCommit={(next) => onChange(runtime.path, next)}
              />
            </div>
          );
        }
        return (
        <SurfaceGroup
          key={group.label || "general"}
          label={group.label || undefined}
        >
          {group.leaves.map(({ key, item, path: leafPath }) => {
            if (Array.isArray(item) && key === "spoken_symbols") {
              const symbols = item as Array<{
                spoken?: string;
                symbol?: string;
                attach?: string;
              }>;
              const updateSymbol = (
                index: number,
                patch: Record<string, string>,
              ) =>
                onChange(
                  leafPath,
                  symbols.map((entry, row) =>
                    row === index ? { ...entry, ...patch } : entry,
                  ),
                );
              return (
                <SurfaceSettingRow
                  key={key}
                  wide
                  label="Spoken-symbol dictionary"
                  description="Say the phrase, type the symbol."
                  control={
                    <div className="surface-symbol-editor">
                      {symbols.map((entry, index) => (
                        <div className="symbol-row" key={index}>
                          <TextInput
                            aria-label={`Spoken phrase ${index + 1}`}
                            value={entry.spoken ?? ""}
                            onChange={(event) =>
                              updateSymbol(index, {
                                spoken: event.target.value,
                              })
                            }
                            placeholder="arrow"
                          />
                          <TextInput
                            aria-label={`Symbol ${index + 1}`}
                            value={entry.symbol ?? ""}
                            onChange={(event) =>
                              updateSymbol(index, {
                                symbol: event.target.value,
                              })
                            }
                            placeholder="→"
                          />
                          <Select
                            aria-label={`Attachment ${index + 1}`}
                            value={entry.attach ?? "none"}
                            onChange={(event) =>
                              updateSymbol(index, {
                                attach: event.target.value,
                              })
                            }
                          >
                            <option value="none">No attachment</option>
                            <option value="left">Attach left</option>
                            <option value="right">Attach right</option>
                            <option value="both">Attach both</option>
                          </Select>
                          <Button
                            dense
                            variant="ghost"
                            onClick={() =>
                              onChange(
                                leafPath,
                                symbols.filter((_, row) => row !== index),
                              )
                            }
                          >
                            Remove
                          </Button>
                        </div>
                      ))}
                      <Button
                        dense
                        onClick={() =>
                          onChange(leafPath, [
                            ...symbols,
                            { spoken: "", symbol: "", attach: "none" },
                          ])
                        }
                      >
                        Add spoken symbol
                      </Button>
                    </div>
                  }
                />
              );
            }
            if (Array.isArray(item))
              return (
                <SurfaceSettingRow
                  key={key}
                  wide
                  label={title(key)}
                  description="Comma-separated list."
                  control={
                    <TextInput
                      aria-label={title(key)}
                      value={item.join(", ")}
                      onChange={(event) =>
                        onChange(
                          leafPath,
                          event.target.value
                            .split(",")
                            .map((part) => part.trim())
                            .filter(Boolean),
                        )
                      }
                    />
                  }
                />
              );
            if (typeof item === "boolean")
              return (
                <SurfaceSettingRow
                  key={key}
                  label={title(key)}
                  control={
                    <SurfaceToggle
                      label={title(key)}
                      checked={item}
                      onChange={(next) => onChange(leafPath, next)}
                    />
                  }
                />
              );
            return (
              <SurfaceSettingRow
                key={key}
                label={title(key)}
                control={
                  <TextInput
                    aria-label={title(key)}
                    type={typeof item === "number" ? "number" : "text"}
                    value={item === null ? "" : String(item)}
                    onChange={(event) =>
                      onChange(
                        leafPath,
                        typeof item === "number"
                          ? Number(event.target.value)
                          : event.target.value,
                      )
                    }
                  />
                }
              />
            );
          })}
        </SurfaceGroup>
        );
      })}
    </>
  );
}

/** HS-100 spike — a tiny drawn icon set for settings rows. */
function SettingGlyph({ name }: { name: string }) {
  const paths: Record<string, string> = {
    posture: "M8 1.8 13 3.8v3.4c0 3.2-2.1 5.6-5 6.9-2.9-1.3-5-3.7-5-6.9V3.8Z",
    secret: "M3.5 7.5h9v5.5h-9Z M5.5 7.5V5.4a2.5 2.5 0 0 1 5 0v2.1",
    ui: "M3 5h10M3 5v6h10V5M6 8h4",
    hotkey: "M2.5 4.5h11v7h-11Z M4.5 6.5h1M7.5 6.5h1M10.5 6.5h1M5 9.5h6",
    model: "M4 12V7m4 5V4m4 8V9",
    dictation: "M8 2.5a2 2 0 0 1 2 2v3a2 2 0 1 1-4 0v-3a2 2 0 0 1 2-2Z M4.5 7.5a3.5 3.5 0 0 0 7 0M8 11v2.5",
    wake_word: "M8 2l1.2 3.3L12.5 6.5 9.2 7.7 8 11 6.8 7.7 3.5 6.5 6.8 5.3Z",
    presence: "M2.5 8s2-3.5 5.5-3.5S13.5 8 13.5 8s-2 3.5-5.5 3.5S2.5 8 2.5 8Z M8 8m-1.5 0a1.5 1.5 0 1 0 3 0a1.5 1.5 0 1 0-3 0",
    meeting: "M5.5 6.5a2 2 0 1 0 0-.01M10.5 6.5a2 2 0 1 0 0-.01M2.5 12c0-1.7 1.3-3 3-3s3 1.3 3 3M8.5 12c0-1.7 1.3-3 3-3s3 1.3 3 3",
    activity: "M2.5 8h2.5l1.5-3.5 2 7L10 8h3.5",
    cadence: "M8 8V4.5M8 8l2.5 1.5M8 2.5A5.5 5.5 0 1 0 8 13.5 5.5 5.5 0 1 0 8 2.5Z",
    commands: "M3 4.5l3 3.5-3 3.5M8 11.5h5",
    device: "M4.5 2.5h7v11h-7Z M7 11.5h2",
    mesh: "M4 4.5a1.5 1.5 0 1 0 0-.01M12 4.5a1.5 1.5 0 1 0 0-.01M8 11.5a1.5 1.5 0 1 0 0-.01M5 5.5l2 4.5M11 5.5l-2 4.5M5.5 4.5h5",
  };
  return (
    <svg
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path
        d={
          paths[name] ??
          "M8 8m-2.6 0a2.6 2.6 0 1 0 5.2 0a2.6 2.6 0 1 0-5.2 0"
        }
      />
    </svg>
  );
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
  const [active, setActive] = useState("");
  const [query, setQuery] = useState("");
  const [saving, setSaving] = useState(false);
  const [secretDrafts, setSecretDrafts] = useState<Record<string, string>>({});
  const [secretBusy, setSecretBusy] = useState("");
  const [authorityBusy, setAuthorityBusy] = useState(false);
  const [message, setMessage] = useState<{
    error?: boolean;
    text: string;
  } | null>(null);
  const sections = useMemo(
    () =>
      Object.keys(resource.data)
        .filter(
          (key) =>
            !key.startsWith("_") &&
            resource.data[key] &&
            typeof resource.data[key] === "object" &&
            !Array.isArray(resource.data[key]),
        )
        .sort(
          (a, b) =>
            (SECTION_ORDER.indexOf(a) < 0 ? 99 : SECTION_ORDER.indexOf(a)) -
            (SECTION_ORDER.indexOf(b) < 0 ? 99 : SECTION_ORDER.indexOf(b)),
        ),
    [resource.data],
  );
  const selected =
    active && sections.includes(active) ? active : (sections[0] ?? "");
  const secrets = (resource.data._secrets ?? {}) as Record<string, SecretState>;

  /* HS-101 round 3 — the configuring archetype saves ON CHANGE
     (Article VII: no ceremony): every edit lands debounced; the verb
     bar whispers Saving…/Saved instead of wearing buttons. */
  const [savedTick, setSavedTick] = useState(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout>>(undefined);
  useEffect(() => () => clearTimeout(saveTimer.current), []);
  const save = async (payload?: JsonRecord) => {
    setSaving(true);
    setMessage(null);
    try {
      const result = await apiFetch<{ settings?: JsonRecord }>(
        "/api/settings",
        { method: "PUT", json: payload ?? resource.data },
      );
      resource.setData(result.settings ?? payload ?? resource.data);
      setSavedTick(true);
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
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
    setMessage(null);
    clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => void save(draft), 700);
  };

  const changeSecret = async (
    secretId: string,
    action: "replace" | "rotate" | "delete",
  ) => {
    setSecretBusy(secretId);
    setMessage(null);
    try {
      if (action === "replace") {
        const value = secretDrafts[secretId]?.trim() ?? "";
        if (!value) throw new Error("Enter a replacement value first.");
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
      setSecretDrafts((drafts) => ({ ...drafts, [secretId]: "" }));
      await resource.reload();
      setMessage({
        text: `${SECRET_LABELS[secretId] ?? title(secretId)} ${
          action === "delete"
            ? "deleted"
            : action === "rotate"
              ? "rotated"
              : "replaced"
        }. The value was not returned by the hub.`,
      });
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
    } finally {
      setSecretBusy("");
    }
  };

  const setControlMode = async (controlMode: string) => {
    setAuthorityBusy(true);
    setMessage(null);
    try {
      const result = await apiFetch<JsonRecord>("/api/authority/control-mode", {
        method: "PUT",
        json: { control_mode: controlMode },
      });
      authority.setData({ ...authority.data, ...result });
      const revoked = Number(result.revoked_grants ?? 0);
      setMessage({
        text: `Control posture is now ${controlModeLabel(controlMode)} for future operations.${revoked ? ` ${revoked} active ${revoked === 1 ? "grant was" : "grants were"} revoked.` : ""}`,
      });
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
    } finally {
      setAuthorityBusy(false);
    }
  };

  // HS-98-05: the Integrations alias lands on its section — the
  // credentials (destination) block scrolls into view when scoped.
  const credentialsRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!integrationSubject || resource.loading) return;
    credentialsRef.current?.scrollIntoView({ block: "start" });
  }, [integrationSubject, resource.loading]);

  const verbs = (
    <span
      className={"settings-save-whisper" + (saving ? " is-saving" : "")}
      role="status"
    >
      {saving ? "Saving…" : savedTick ? "Saved" : ""}
    </span>
  );
  return (
    <>
      {hero ? hero(verbs) : <SurfaceVerbs>{verbs}</SurfaceVerbs>}
      {integrationSubject ? (
        <p className="desk-scope-chip">
          <span aria-hidden="true">⇄</span> Integration destinations
        </p>
      ) : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceSection label="Control posture">
          <SurfaceGroup>
            <SurfaceSettingRow
              icon={<SettingGlyph name="posture" />}
              label="Preset"
              description={
                <PostureNote
                  mode={String(authority.data.control_mode ?? "neutral")}
                  describe
                />
              }
              control={
                <Select
                  aria-label="Control posture preset"
                  value={String(authority.data.control_mode ?? "neutral")}
                  disabled={authorityBusy || authority.loading}
                  onChange={(event) => void setControlMode(event.target.value)}
                >
                  {CONTROL_MODES.map((mode) => (
                    <option key={mode} value={mode}>
                      {controlModeLabel(mode)}
                    </option>
                  ))}
                </Select>
              }
            />
          </SurfaceGroup>
          <Disclosure title="Policy details">
            <p className="surface-boundary-note">
              Hard invariants never change: authentication, secret custody,
              destination and payload binding, pane identity, receipts.
            </p>
            <p className="surface-boundary-note">
              {String(authority.data.source ?? "config")} ·{" "}
              {String(authority.data.policy_version ?? "operation policy")} ·{" "}
              {Array.isArray(authority.data.precedence)
                ? authority.data.precedence.join(" → ")
                : "hard invariants → grants → mode → feature default"}
            </p>
          </Disclosure>
        </SurfaceSection>
        <SurfaceSection
          label="Hub configuration"
          actions={
            <TextInput
              aria-label="Find a setting"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Find a setting"
            />
          }
        >
          {message ? (
            <InlineMessage tone={message.error ? "error" : "success"}>
              {message.text}
            </InlineMessage>
          ) : null}
          {query ? (
            sections.map((section) => (
              <section key={section} className="settings-section">
                <h2>{FRIENDLY[section] ?? title(section)}</h2>
                <SettingsFields
                  value={resource.data[section] as JsonRecord}
                  path={[section]}
                  query={query}
                  onChange={update}
                />
              </section>
            ))
          ) : selected ? (
            /* HS-99-06 — the settings archetype: rail + panel at a wide
               window; the strip returns when narrow. */
            <div className="surface-railed">
              <Tabs
                label="Settings sections"
                active={selected}
                onChange={setActive}
                tabs={sections.map((id) => ({
                  id,
                  label: (
                    <>
                      <SettingGlyph name={id} />
                      {FRIENDLY[id] ?? title(id)}
                    </>
                  ),
                }))}
              />
              <div className="surface-railed-panel">
                <h2 className="surface-panel-title">
                  {FRIENDLY[selected] ?? title(selected)}
                </h2>
                <SettingsFields
                  value={resource.data[selected] as JsonRecord}
                  path={[selected]}
                  query=""
                  onChange={update}
                />
              </div>
            </div>
          ) : (
            <InlineMessage tone="warning">
              No settings were returned by the hub.
            </InlineMessage>
          )}
        </SurfaceSection>
        <div ref={credentialsRef}>
          <SurfaceSection label="Credentials">
            <p className="surface-boundary-note">
              Values stay on this hub — reads show configured or not, never
              the value.
            </p>
            <SurfaceGroup>
              {Object.entries(secrets).map(([secretId, state]) => (
                <SurfaceSettingRow
                  key={secretId}
                  icon={<SettingGlyph name="secret" />}
                  label={SECRET_LABELS[secretId] ?? title(secretId)}
                  description={
                    (state.configured ? "Configured" : "Not configured") +
                    (state.destination ? ` · ${state.destination}` : "")
                  }
                  control={
                    <span className="surface-actions">
                      <TextInput
                        aria-label={`Replacement ${SECRET_LABELS[secretId] ?? title(secretId)}`}
                        type="password"
                        autoComplete="new-password"
                        placeholder="Replace…"
                        value={secretDrafts[secretId] ?? ""}
                        onChange={(event) =>
                          setSecretDrafts((drafts) => ({
                            ...drafts,
                            [secretId]: event.target.value,
                          }))
                        }
                      />
                      <Button
                        dense
                        loading={secretBusy === secretId}
                        disabled={!secretDrafts[secretId]?.trim()}
                        onClick={() => void changeSecret(secretId, "replace")}
                      >
                        Replace
                      </Button>
                      {ROTATABLE_SECRETS.has(secretId) ? (
                        <ConfirmVerb
                          label="Rotate"
                          confirmLabel="Rotate?"
                          busy={secretBusy === secretId}
                          onConfirm={() => void changeSecret(secretId, "rotate")}
                        />
                      ) : null}
                      {state.configured ? (
                        <ConfirmVerb
                          label="Delete"
                          confirmLabel="Delete?"
                          busy={secretBusy === secretId}
                          onConfirm={() => void changeSecret(secretId, "delete")}
                        />
                      ) : null}
                    </span>
                  }
                />
              ))}
            </SurfaceGroup>
          </SurfaceSection>
        </div>
      </SurfaceState>
    </>
  );
}

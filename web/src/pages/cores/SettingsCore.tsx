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
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";

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
  meeting: "Meetings & intel",
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
function title(key: string) {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (value) => value.toUpperCase());
}

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
  const rows = Object.entries(value).filter(([key, item]) => {
    if (item !== null && typeof item === "object" && !Array.isArray(item))
      return true;
    return (
      !query ||
      `${path.join(" ")} ${key}`.toLowerCase().includes(query.toLowerCase())
    );
  });
  return (
    <div className="settings-fields">
      {rows.map(([key, item]) => {
        const nextPath = [...path, key];
        if (item !== null && typeof item === "object" && !Array.isArray(item))
          return (
            <fieldset key={key}>
              <legend>{title(key)}</legend>
              <SettingsFields
                value={item as JsonRecord}
                path={nextPath}
                query={query}
                onChange={onChange}
              />
            </fieldset>
          );
        if (Array.isArray(item) && key === "spoken_symbols") {
          const symbols = item as Array<{
            spoken?: string;
            symbol?: string;
            attach?: string;
          }>;
          const updateSymbol = (index: number, patch: Record<string, string>) =>
            onChange(
              nextPath,
              symbols.map((entry, row) =>
                row === index ? { ...entry, ...patch } : entry,
              ),
            );
          return (
            <fieldset key={key}>
              <legend>Spoken-symbol dictionary</legend>
              {symbols.map((entry, index) => (
                <div className="symbol-row" key={index}>
                  <TextInput
                    aria-label={`Spoken phrase ${index + 1}`}
                    value={entry.spoken ?? ""}
                    onChange={(event) =>
                      updateSymbol(index, { spoken: event.target.value })
                    }
                    placeholder="arrow"
                  />
                  <TextInput
                    aria-label={`Symbol ${index + 1}`}
                    value={entry.symbol ?? ""}
                    onChange={(event) =>
                      updateSymbol(index, { symbol: event.target.value })
                    }
                    placeholder="→"
                  />
                  <Select
                    aria-label={`Attachment ${index + 1}`}
                    value={entry.attach ?? "none"}
                    onChange={(event) =>
                      updateSymbol(index, { attach: event.target.value })
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
                        nextPath,
                        symbols.filter((_, row) => row !== index),
                      )
                    }
                  >
                    Remove
                  </Button>
                </div>
              ))}
              <Button
                onClick={() =>
                  onChange(nextPath, [
                    ...symbols,
                    { spoken: "", symbol: "", attach: "none" },
                  ])
                }
              >
                Add spoken symbol
              </Button>
            </fieldset>
          );
        }
        if (Array.isArray(item))
          return (
            <Field
              key={key}
              label={title(key)}
              description="Comma-separated list."
            >
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  value={item.join(", ")}
                  onChange={(event) =>
                    onChange(
                      nextPath,
                      event.target.value
                        .split(",")
                        .map((part) => part.trim())
                        .filter(Boolean),
                    )
                  }
                />
              )}
            </Field>
          );
        if (typeof item === "boolean")
          return (
            <Switch
              key={key}
              label={title(key)}
              checked={item}
              onChange={(event) => onChange(nextPath, event.target.checked)}
            />
          );
        return (
          <Field key={key} label={title(key)}>
            {({ id }) => (
              <TextInput
                id={id}
                type={typeof item === "number" ? "number" : "text"}
                value={item === null ? "" : String(item)}
                onChange={(event) =>
                  onChange(
                    nextPath,
                    typeof item === "number"
                      ? Number(event.target.value)
                      : event.target.value,
                  )
                }
              />
            )}
          </Field>
        );
      })}
    </div>
  );
}

export function SettingsCore({ hero, scope }: CoreProps) {
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

  const update = (path: string[], next: unknown) => {
    const draft = clone(resource.data);
    let cursor = draft;
    path.forEach((part, index) => {
      if (index === path.length - 1) cursor[part] = next;
      else cursor = cursor[part] as JsonRecord;
    });
    resource.setData(draft);
    setMessage(null);
  };

  const save = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const result = await apiFetch<{ settings?: JsonRecord }>(
        "/api/settings",
        { method: "PUT", json: resource.data },
      );
      resource.setData(result.settings ?? resource.data);
      setMessage({
        text: "Settings saved. The running hub has the new configuration.",
      });
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
    } finally {
      setSaving(false);
    }
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
    <Button variant="primary" dense loading={saving} onClick={save}>
      Save settings
    </Button>
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
          <Field
            label="Preset"
            description="Applies to future operations. Existing proposals keep their captured posture."
          >
            {({ id, describedBy }) => (
              <Select
                id={id}
                aria-describedby={describedBy}
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
            )}
          </Field>
          <p>
            <PostureNote
              mode={String(authority.data.control_mode ?? "neutral")}
              describe
            />
          </p>
          <Disclosure title="Policy details">
            <p>
              Authentication, secret custody, destination and payload binding,
              pane identity, receipts, configuration, and schema checks never
              change.
            </p>
            <p>
              Source: {String(authority.data.source ?? "config")} ·{" "}
              {String(authority.data.policy_version ?? "operation policy")} ·
              precedence:{" "}
              {Array.isArray(authority.data.precedence)
                ? authority.data.precedence.join(" → ")
                : "hard invariants → grants → mode → feature default"}
            </p>
          </Disclosure>
        </SurfaceSection>
        <SurfaceSection label="Hub configuration">
          <Field
            label="Find a setting"
            description="Search matches section and setting names."
          >
            {({ id, describedBy }) => (
              <TextInput
                id={id}
                aria-describedby={describedBy}
                type="search"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Try model, privacy, wake word…"
              />
            )}
          </Field>
          {query ? null : (
            <Tabs
              label="Settings sections"
              active={selected}
              onChange={setActive}
              tabs={sections.map((id) => ({
                id,
                label: FRIENDLY[id] ?? title(id),
              }))}
            />
          )}
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
            <SettingsFields
              value={resource.data[selected] as JsonRecord}
              path={[selected]}
              query=""
              onChange={update}
            />
          ) : (
            <InlineMessage tone="warning">
              No settings were returned by the hub.
            </InlineMessage>
          )}
          <div className="surface-actions">
            <Button variant="primary" loading={saving} onClick={save}>
              Save settings
            </Button>
            <Button variant="ghost" onClick={() => void resource.reload()}>
              Discard changes
            </Button>
          </div>
        </SurfaceSection>
        <div ref={credentialsRef}>
          <SurfaceSection label="Credentials">
            <p>
              Values stay on this hub. Reads show only whether each credential
              is configured; replacement, rotation, and deletion never return
              it.
            </p>
            <div className="settings-fields">
              {Object.entries(secrets).map(([secretId, state]) => (
                <fieldset key={secretId}>
                  <legend>{SECRET_LABELS[secretId] ?? title(secretId)}</legend>
                  <p>
                    {state.configured ? "Configured" : "Not configured"}
                    {state.destination ? ` · ${state.destination}` : ""}
                  </p>
                  <Field label="Replacement value">
                    {({ id }) => (
                      <TextInput
                        id={id}
                        type="password"
                        autoComplete="new-password"
                        value={secretDrafts[secretId] ?? ""}
                        onChange={(event) =>
                          setSecretDrafts((drafts) => ({
                            ...drafts,
                            [secretId]: event.target.value,
                          }))
                        }
                      />
                    )}
                  </Field>
                  <div className="surface-actions">
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
                  </div>
                </fieldset>
              ))}
            </div>
          </SurfaceSection>
        </div>
      </SurfaceState>
    </>
  );
}

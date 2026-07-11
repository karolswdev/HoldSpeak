import { useMemo, useState } from "react";
import {
  Button,
  Field,
  InlineMessage,
  Panel,
  Select,
  Switch,
  Tabs,
  TextInput,
} from "../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";
import { PageHero, ResourceState, useResource } from "./pageSupport";

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

export default function SettingsPage() {
  const resource = useResource<JsonRecord>("/api/settings", {});
  const [active, setActive] = useState("");
  const [query, setQuery] = useState("");
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{
    error?: boolean;
    text: string;
  } | null>(null);
  const sections = useMemo(
    () =>
      Object.keys(resource.data)
        .filter(
          (key) =>
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

  return (
    <div className="page-wrap">
      <PageHero
        eyebrow="Configuration"
        title="Settings"
        actions={
          <Button variant="primary" loading={saving} onClick={save}>
            Save settings
          </Button>
        }
      >
        Search the full configuration without losing the product's grouped
        mental model.
      </PageHero>
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <Panel title="Hub configuration" eyebrow="Signal editor">
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
          <div className="button-row">
            <Button variant="primary" loading={saving} onClick={save}>
              Save settings
            </Button>
            <Button variant="ghost" onClick={() => void resource.reload()}>
              Discard changes
            </Button>
          </div>
        </Panel>
      </ResourceState>
    </div>
  );
}

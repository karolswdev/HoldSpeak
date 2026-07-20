// HS-95-04 — the Commands surface's core: the flat page's whole capability
// without the flat chrome (see ActivityCore for the pattern rules).
// HS-98-07 — re-crafted native: the editor left its modal for an
// in-surface section; delete is an inline two-step. Wire calls
// unchanged.
import { useState } from "react";
import {
  Button,
  Field,
  InlineMessage,
  Select,
  Switch,
  TextInput,
} from "../../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../../lib/api";
import { useResource } from "../pageSupport";
import type { CoreProps } from "./ActivityCore";
import {
  ConfirmVerb,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";

type Macro = { keyword: string; action: { kind: string; payload: string } };
const blank = (): Macro => ({
  keyword: "",
  action: { kind: "open_url", payload: "" },
});
const preview = (macro: Macro) =>
  (({
    open_url: "opens",
    launch_app: "launches",
    shell: "runs",
    type_text: "types",
  })[macro.action.kind] ?? "uses") + ` ${macro.action.payload}`;

export function CommandsCore({ hero }: CoreProps) {
  const resource = useResource<JsonRecord>("/api/settings", {});
  const macros = ((resource.data.dictation as JsonRecord | undefined)?.macros ??
    {}) as JsonRecord;
  const items = (Array.isArray(macros.items) ? macros.items : []) as Macro[];
  const enabled = Boolean(macros.enabled);
  const [editing, setEditing] = useState<{
    index: number;
    macro: Macro;
  } | null>(null);
  const [message, setMessage] = useState<{
    error?: boolean;
    text: string;
  } | null>(null);
  const [busy, setBusy] = useState(false);

  const persist = async (next: Macro[], on = enabled) => {
    setBusy(true);
    setMessage(null);
    try {
      const value = await apiFetch<{ settings?: JsonRecord }>("/api/settings", {
        method: "PUT",
        json: { dictation: { macros: { enabled: on, items: next } } },
      });
      resource.setData(value.settings ?? resource.data);
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };
  const test = async (macro: Macro) => {
    setBusy(true);
    try {
      const value = await apiFetch<JsonRecord>("/api/commands/test", {
        method: "POST",
        json: macro.action,
      });
      setMessage({
        error: !value.ok,
        text: String(
          value.note ??
            value.error ??
            (value.tested ? "Command ran." : "Command is valid."),
        ),
      });
    } catch (error) {
      setMessage({ error: true, text: readableError(error) });
    } finally {
      setBusy(false);
    }
  };
  const save = async () => {
    if (!editing) return;
    const next = [...items];
    if (editing.index < 0) next.push(editing.macro);
    else next[editing.index] = editing.macro;
    await persist(next);
    setEditing(null);
  };

  const verbs = (
    <>
      <Button
        dense
        onClick={() => setEditing({ index: -1, macro: blank() })}
      >
        Add command
      </Button>
      <Switch
        label={enabled ? "Commands on" : "Commands off"}
        checked={enabled}
        onChange={(event) => void persist(items, event.target.checked)}
      />
    </>
  );
  return (
    <>
      {hero ? (
        hero(verbs)
      ) : (
        <SurfaceVerbs status={`${items.length} ${items.length === 1 ? "command" : "commands"}`}>{verbs}</SurfaceVerbs>
      )}
      {message ? (
        <InlineMessage tone={message.error ? "error" : "success"}>
          {message.text}
        </InlineMessage>
      ) : null}
      <SurfaceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <SurfaceSection label="Command board">
          {!items.length && !editing ? (
            <>
              <SurfaceState
                empty
                emptyLabel="No voice commands"
                emptyGlyph="❝"
              />
              <div className="surface-actions is-centered">
                <Button
                  variant="primary"
                  dense
                  onClick={() => setEditing({ index: -1, macro: blank() })}
                >
                  Add your first command
                </Button>
              </div>
            </>
          ) : (
            <SurfaceRows>
              {items.map((macro, index) => (
                <SurfaceRow
                  key={`${macro.keyword}-${index}`}
                  title={`“${macro.keyword}”`}
                  detail={
                    preview(macro) +
                    (macro.action.kind === "shell" ? " · runs code" : "")
                  }
                  verbs={
                    <>
                      <Button
                        dense
                        loading={busy}
                        onClick={() => void test(macro)}
                      >
                        Test
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        onClick={() =>
                          setEditing({ index, macro: structuredClone(macro) })
                        }
                      >
                        Edit
                      </Button>
                      <ConfirmVerb
                        label="Delete"
                        confirmLabel="Delete?"
                        busy={busy}
                        onConfirm={() =>
                          void persist(items.filter((_, row) => row !== index))
                        }
                      />
                    </>
                  }
                />
              ))}
            </SurfaceRows>
          )}
        </SurfaceSection>
        {editing ? (
          <SurfaceSection
            label={editing.index === -1 ? "New command" : "Edit command"}
            actions={
              <Button dense variant="ghost" onClick={() => setEditing(null)}>
                Close
              </Button>
            }
          >
            <Field
              label="Spoken keyword"
              description={`Matches: ${
                editing.macro.keyword
                  .trim()
                  .toLowerCase()
                  .replace(/[.!?,]+$/, "") || "—"
              }`}
            >
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  value={editing.macro.keyword}
                  onChange={(event) =>
                    setEditing({
                      ...editing,
                      macro: { ...editing.macro, keyword: event.target.value },
                    })
                  }
                />
              )}
            </Field>
            <Field label="Command behavior">
              {({ id }) => (
                <Select
                  id={id}
                  value={editing.macro.action.kind}
                  onChange={(event) =>
                    setEditing({
                      ...editing,
                      macro: {
                        ...editing.macro,
                        action: {
                          ...editing.macro.action,
                          kind: event.target.value,
                        },
                      },
                    })
                  }
                >
                  <option value="open_url">Open URL</option>
                  <option value="launch_app">Launch app</option>
                  <option value="shell">Shell command</option>
                  <option value="type_text">Type text</option>
                </Select>
              )}
            </Field>
            <Field
              label="Payload"
              description={
                editing.macro.action.payload
                  ? preview(editing.macro)
                  : "Enter exactly what this command should use."
              }
            >
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  value={editing.macro.action.payload}
                  onChange={(event) =>
                    setEditing({
                      ...editing,
                      macro: {
                        ...editing.macro,
                        action: {
                          ...editing.macro.action,
                          payload: event.target.value,
                        },
                      },
                    })
                  }
                />
              )}
            </Field>
            {editing.macro.action.kind === "shell" ? (
              <InlineMessage tone="warning">
                This command runs code on your machine after the spoken keyword
                matches.
              </InlineMessage>
            ) : null}
            <div className="surface-actions">
              <Button
                variant="primary"
                dense
                loading={busy}
                disabled={
                  !editing.macro.keyword.trim() ||
                  !editing.macro.action.payload.trim()
                }
                onClick={save}
              >
                Save command
              </Button>
              <Button dense onClick={() => void test(editing.macro)}>
                Test without saving
              </Button>
            </div>
          </SurfaceSection>
        ) : null}
      </SurfaceState>
    </>
  );
}

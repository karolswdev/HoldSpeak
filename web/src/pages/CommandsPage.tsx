import { useState } from "react";
import {
  Button,
  Dialog,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  Switch,
  TextInput,
} from "../components/signal/Signal";
import { apiFetch, readableError, type JsonRecord } from "../lib/api";
import {
  ConfirmAction,
  PageHero,
  ResourceState,
  useResource,
} from "./pageSupport";

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

export default function CommandsPage() {
  const resource = useResource<JsonRecord>("/api/settings", {});
  const macros = ((resource.data.dictation as JsonRecord | undefined)?.macros ??
    {}) as JsonRecord;
  const items = (Array.isArray(macros.items) ? macros.items : []) as Macro[];
  const enabled = Boolean(macros.enabled);
  const [editing, setEditing] = useState<{
    index: number;
    macro: Macro;
  } | null>(null);
  const [deleting, setDeleting] = useState<number | null>(null);
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
  const remove = async () => {
    if (deleting === null) return;
    await persist(items.filter((_, index) => index !== deleting));
    setDeleting(null);
  };

  return (
    <div className="page-wrap">
      <PageHero eyebrow="Voice commands" title="Commands">
        What you see is what fires. Test an action before you trust it.
      </PageHero>
      <ResourceState
        loading={resource.loading}
        error={resource.error}
        onRetry={() => void resource.reload()}
      >
        <Panel
          title="Command board"
          eyebrow={`${items.length} macros`}
          actions={
            <Switch
              label={enabled ? "Commands on" : "Commands off"}
              checked={enabled}
              onChange={(event) => void persist(items, event.target.checked)}
            />
          }
        >
          {message ? (
            <InlineMessage tone={message.error ? "error" : "success"}>
              {message.text}
            </InlineMessage>
          ) : null}
          {!items.length ? (
            <EmptyState title="No voice commands">
              <Button
                variant="primary"
                onClick={() => setEditing({ index: -1, macro: blank() })}
              >
                Add your first command
              </Button>
            </EmptyState>
          ) : (
            <ul className="data-list">
              {items.map((macro, index) => (
                <li className="data-row" key={`${macro.keyword}-${index}`}>
                  <div>
                    <strong>“{macro.keyword}”</strong>
                    <small>
                      {preview(macro)}
                      {macro.action.kind === "shell" ? " · runs code" : ""}
                    </small>
                  </div>
                  <div className="button-row">
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
                    <Button
                      dense
                      variant="ghost"
                      onClick={() => setDeleting(index)}
                    >
                      Delete
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
          <Button onClick={() => setEditing({ index: -1, macro: blank() })}>
            Add command
          </Button>
        </Panel>
      </ResourceState>
      <Dialog
        open={Boolean(editing)}
        title={editing?.index === -1 ? "New command" : "Edit command"}
        onClose={() => setEditing(null)}
      >
        {editing ? (
          <div className="dialog-form">
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
            <Field label="Action">
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
            <div className="button-row">
              <Button
                variant="primary"
                loading={busy}
                disabled={
                  !editing.macro.keyword.trim() ||
                  !editing.macro.action.payload.trim()
                }
                onClick={save}
              >
                Save command
              </Button>
              <Button onClick={() => void test(editing.macro)}>
                Test without saving
              </Button>
            </div>
          </div>
        ) : null}
      </Dialog>
      <ConfirmAction
        open={deleting !== null}
        title="Delete command?"
        detail={
          deleting === null
            ? ""
            : `“${items[deleting]?.keyword ?? "This command"}” will stop matching.`
        }
        busy={busy}
        onConfirm={remove}
        onClose={() => setDeleting(null)}
      />
    </div>
  );
}

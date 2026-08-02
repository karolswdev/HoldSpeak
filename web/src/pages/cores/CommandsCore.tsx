// HS-95-04 — the Commands surface's core: the flat page's whole capability
// without the flat chrome (see ActivityCore for the pattern rules).
// HS-98-07 — re-crafted native: the editor left its modal for an
// in-surface section; delete is an inline two-step. Wire calls
// unchanged.
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  GadgetGroup,
  GadgetRow,
  StringGadget,
} from "../../desk/surface/gadgets";
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
      <span className="gadget-checkline">
        <CheckGadget
          label="Commands enabled"
          checked={enabled}
          onChange={(next) => void persist(items, next)}
        />
        <span className="gadget-checkline-word">
          {enabled ? "Commands on" : "Commands off"}
        </span>
      </span>
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
        message.error ? (
          <SurfaceState error={message.text} />
        ) : (
          <p className="surface-receipt-line" data-tone="ok" role="status">
            ✓ {message.text}
          </p>
        )
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
              <button
                type="button"
                className="gadget-table-add"
                onClick={() => setEditing({ index: -1, macro: blank() })}
              >
                + ADD COMMAND
              </button>
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
            <GadgetGroup>
              <GadgetRow
                label="Spoken keyword"
                fact={
                  editing.macro.keyword
                    .trim()
                    .toLowerCase()
                    .replace(/[.!?,]+$/, "") || "—"
                }
              >
                <StringGadget
                  label="Spoken keyword"
                  value={editing.macro.keyword}
                  onChange={(next) =>
                    setEditing({
                      ...editing,
                      macro: { ...editing.macro, keyword: next },
                    })
                  }
                />
              </GadgetRow>
              <GadgetRow label="Command behavior">
                <CycleGadget
                  label="Command behavior"
                  value={editing.macro.action.kind}
                  options={[
                    { value: "open_url", label: "Open URL" },
                    { value: "launch_app", label: "Launch app" },
                    { value: "shell", label: "Shell command" },
                    { value: "type_text", label: "Type text" },
                  ]}
                  onChange={(kind) =>
                    setEditing({
                      ...editing,
                      macro: {
                        ...editing.macro,
                        action: { ...editing.macro.action, kind },
                      },
                    })
                  }
                />
              </GadgetRow>
              <GadgetRow
                label="Payload"
                fact={
                  editing.macro.action.payload
                    ? preview(editing.macro)
                    : undefined
                }
              >
                <StringGadget
                  label="Payload"
                  value={editing.macro.action.payload}
                  onChange={(payload) =>
                    setEditing({
                      ...editing,
                      macro: {
                        ...editing.macro,
                        action: { ...editing.macro.action, payload },
                      },
                    })
                  }
                />
              </GadgetRow>
            </GadgetGroup>
            {editing.macro.action.kind === "shell" ? (
              <p className="surface-receipt-line" data-tone="warn">
                ⚠ RUNS CODE ON THIS MACHINE WHEN THE KEYWORD MATCHES
              </p>
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

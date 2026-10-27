/** Knowledge edits its name and real membership, never an unsupported body. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../../store";
import { apiFetch } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { GadgetRow, StringGadget } from "../../surface/gadgets";
import { ToolGlyph, Toolbar } from "../../surface/kit";
// @ts-ignore — shared ESM module (see ../../sprites.d.ts)
import { refAgent, spriteUrl } from "../../sprites";
import "./kbEditor.css";
import { SurfaceState } from "../../surface/Surface";
import { Material } from "../../surface/Material";
import { allObjects, objectByRef } from "../../world";
import { qualifiedRef } from "../../api";
import { KIND_LABEL } from "../../tools";
import { kindWord } from "../../windowName";
import { writeFailureReason } from "../../hooks/useWriteReceipt";
import { useDebouncedSave, usePublishEditorWriter, type EditorWriter } from "./useDebouncedSave";
import { keptEditorPatch, keptField, updateKeptEditorFields } from "./editorDraft";
import type { KB } from "../../../lib/primitives";
import type { InlineEditorContentProps } from "./types";

export function KbEditor({ object: o, autoFocusName, onWriter, openAdd, toolbar }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("kb", o.id);
  const live = (items.kb || []).find((x) => x.id === o.id) || o.ref as KB;
  const [name, setName] = useState(() => keptField(keptEditorPatch("kb", o.id), "name", live.name || ""));
  const [refs, setRefs] = useState<string[]>(live.memberIds || []);
  const [adding, setAdding] = useState(Boolean(openAdd));
  const [query, setQuery] = useState("");
  const [readError, setReadError] = useState("");
  const [recovered, setRecovered] = useState(() => keptField(keptEditorPatch("kb", o.id), "body_markdown", ""));
  const recoveryId = useRef(keptField(keptEditorPatch("kb", o.id), "recovery_note_id", ""));
  const operation = useRef<Promise<boolean> | null>(null);
  const retryAction = useRef<(() => Promise<boolean>) | null>(null);
  const mutationFailed = useRef(false);
  const [mutation, setMutation] = useState<{ state: "idle" | "saving" | "saved" | "error"; reason: string; at: number | null }>({ state: "idle", reason: "", at: null });
  const base = "/api/kbs/" + encodeURIComponent(o.id);
  const readMembers = useCallback(async () => {
    try {
      const data = await apiFetch<{ members: Array<{ resource_ref: string }> }>(base + "/members");
      setRefs((data.members || []).map((m) => m.resource_ref));
      setReadError("");
    } catch { setReadError("Items unavailable"); }
  }, [base]);
  useEffect(() => { void readMembers(); }, [readMembers]);

  const run = useCallback((action: () => Promise<void>): Promise<boolean> => {
    if (operation.current) return operation.current;
    const retry = () => run(action);
    retryAction.current = retry;
    mutationFailed.current = false;
    setMutation((s) => ({ ...s, state: "saving", reason: "" }));
    const request = (async () => {
      try {
        await action();
        mutationFailed.current = false;
        setMutation({ state: "saved", reason: "", at: Date.now() });
        // A successful member write remains successful if only its reread fails.
        void useDesk.getState().refresh().catch(() => undefined);
        return true;
      } catch (cause) {
        mutationFailed.current = true;
        setMutation((s) => ({ ...s, state: "error", reason: writeFailureReason(cause) }));
        return false;
      } finally { operation.current = null; }
    })();
    operation.current = request;
    return request;
  }, []);
  const member = (ref: string, active: boolean) => run(async () => {
    await apiFetch(base + "/members/" + encodeURIComponent(ref), { method: active ? "DELETE" : "PUT" });
    setRefs((before) => active ? before.filter((r) => r !== ref) : [...new Set([...before, ref])]);
  });
  const recover = () => run(async () => {
    if (!recoveryId.current) {
      const made = await apiFetch<{ note: { id: string } }>("/api/notes", {
        method: "POST", json: { title: name || "Recovered Knowledge text", body_markdown: recovered, tags: [] },
      });
      recoveryId.current = made.note.id;
      updateKeptEditorFields("kb", o.id, { recovery_note_id: recoveryId.current });
    }
    const ref = qualifiedRef("note", recoveryId.current);
    await apiFetch(base + "/members/" + encodeURIComponent(ref), { method: "PUT" });
    setRefs((before) => [...new Set([...before, ref])]);
    updateKeptEditorFields("kb", o.id, {}, ["body_markdown", "recovery_note_id"]);
    setRecovered("");
  });
  const writer = useMemo<EditorWriter>(() => Object.assign((patch: Record<string, unknown>) => save(patch), {
    ...save,
    state: mutation.state === "error" || mutation.state === "saving" ? mutation.state : save.state === "idle" && mutation.state === "saved" ? "saved" as const : save.state,
    savedAt: Math.max(save.savedAt || 0, mutation.at || 0) || null,
    reason: mutation.state === "error" ? mutation.reason : save.reason,
    flush: async () => {
      if (operation.current && !(await operation.current)) return false;
      if (mutationFailed.current) return false;
      return save.flush();
    },
    retry: async () => mutationFailed.current && retryAction.current ? retryAction.current() : save.retry(),
  }), [save, mutation]);
  usePublishEditorWriter(writer, onWriter);

  const members = refs.map((ref) => ({ ref, object: objectByRef(items, ref) }));
  const choices = allObjects(items).filter((entry) => entry.kind !== "kb" && !refs.includes(qualifiedRef(entry.kind, entry.id)) && (!query || entry.title.toLocaleLowerCase().includes(query.toLocaleLowerCase())));
  const busy = mutation.state === "saving";
  // W3-B (atlas 2026-10-27): the editor on the window grammar. The toolbar
  // holds the host's verbs (Done; Retry after a refusal) and Add items; the
  // name is the Settings label/control grid; the items and the picker are
  // dense list rows (the object glyph, the name, the kind in quiet sans).
  return <>
    <Toolbar label="Knowledge editor" data-testid="knowledge-editor-toolbar">
      {toolbar}
      <Button dense variant={adding ? "secondary" : "ghost"} aria-pressed={adding} onClick={() => setAdding((value) => !value)}>
        <ToolGlyph kind="new" />{adding ? "Close items" : "Add items"}
      </Button>
    </Toolbar>
    <div className="kb-editor-page">
      <div className="kb-editor-grid">
        <GadgetRow label="Name" controlWidth="full">
          <StringGadget label="Knowledge name" value={name} autoFocus={autoFocusName} onChange={(value) => { setName(value); save({ name: value }); }} />
        </GadgetRow>
      </div>
      <section className="kb-editor-section" aria-label="Items">
        <h3 className="kb-editor-caption">Items{refs.length ? <span className="kb-editor-count">{` · ${refs.length}`}</span> : null}</h3>
        {readError ? <SurfaceState error={readError} onRetry={() => void readMembers()} /> : null}
        {members.length ? <ul className="kb-editor-list" data-testid="knowledge-editor-items">
          {members.map(({ ref, object }) => <li key={ref} className="kb-editor-row">
            {object ? <img className="kb-editor-glyph" src={spriteUrl(object.kind, object.id, "rest", refAgent(object.ref))} width={20} height={20} alt="" /> : <span className="kb-editor-glyph" aria-hidden="true" />}
            <span className="kb-editor-name" title={object?.title || ref}>{object?.title || "Item unavailable"}</span>
            <span className="kb-editor-kind">{object ? KIND_LABEL[object.kind] || kindWord(object.kind) : "Unavailable"}</span>
            <span className="kb-editor-verbs">
              {object ? <Button dense variant="ghost" disabled={busy} onClick={async () => { if (await writer.flush()) useDesk.getState().openPullout(ref); }}>Open {kindWord(object.kind).toLowerCase()}</Button> : null}
              <Button dense variant="ghost" disabled={busy} onClick={() => void member(ref, true)}>Remove</Button>
            </span>
          </li>)}
        </ul> : !readError ? <SurfaceState empty emptyLabel="No items" /> : null}
      </section>
      {adding ? <section className="kb-editor-section" aria-label="Add items" data-testid="knowledge-picker">
        <h3 className="kb-editor-caption">Add items</h3>
        <StringGadget label="Find items" value={query} autoFocus={Boolean(openAdd)} onChange={setQuery} placeholder="Find items" />
        {choices.length ? <ul className="kb-editor-list">
          {choices.map((entry) => {
            const ref = qualifiedRef(entry.kind, entry.id);
            return <li key={ref} className="kb-editor-row">
              <img className="kb-editor-glyph" src={spriteUrl(entry.kind, entry.id, "rest", refAgent(entry.ref))} width={20} height={20} alt="" />
              <span className="kb-editor-name" title={entry.title}>{entry.title}</span>
              <span className="kb-editor-kind">{KIND_LABEL[entry.kind] || kindWord(entry.kind)}</span>
              <span className="kb-editor-verbs">
                <Button dense variant="ghost" disabled={busy} onClick={() => void member(ref, false)}>Add</Button>
              </span>
            </li>;
          })}
        </ul> : <SurfaceState empty emptyLabel="No items found" />}
      </section> : null}
      {recovered ? <section className="kb-editor-section" aria-label="Recovered text">
        <h3 className="kb-editor-caption">Recovered text</h3>
        <Material>{recovered}</Material>
        <span><Button variant="primary" disabled={busy} onClick={() => void recover()}>Save as Note</Button></span>
      </section> : null}
    </div>
  </>;
}

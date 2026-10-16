/** Knowledge edits its name and real membership, never an unsupported body. */
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useDesk } from "../../store";
import { apiFetch } from "../../../lib/api";
import { Button } from "../../../components/signal/Signal";
import { StringGadget } from "../../surface/gadgets";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, SurfaceWell } from "../../surface/Surface";
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

export function KbEditor({ object: o, autoFocusName, onWriter }: InlineEditorContentProps) {
  const items = useDesk((s) => s.items);
  const save = useDebouncedSave("kb", o.id);
  const live = (items.kb || []).find((x) => x.id === o.id) || o.ref as KB;
  const [name, setName] = useState(() => keptField(keptEditorPatch("kb", o.id), "name", live.name || ""));
  const [refs, setRefs] = useState<string[]>(live.memberIds || []);
  const [adding, setAdding] = useState(false);
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
  return <>
    <StringGadget label="Knowledge name" value={name} autoFocus={autoFocusName} onChange={(value) => { setName(value); save({ name: value }); }} />
    <SurfaceSection label="Items" count={refs.length || undefined}>
      {readError ? <SurfaceState error={readError} onRetry={() => void readMembers()} /> : null}
      {members.length ? <SurfaceLedger count={null} cols="room">
        {members.map(({ ref, object }) => <SurfaceLedgerRow key={ref}
          primary={object?.title || "Item unavailable"} meta={object ? KIND_LABEL[object.kind] || kindWord(object.kind) : "Unavailable"}
          trailing={<>
            {object ? <Button dense variant="ghost" disabled={mutation.state === "saving"} onClick={async () => { if (await writer.flush()) useDesk.getState().openPullout(ref); }}>Open {kindWord(object.kind).toLowerCase()}</Button> : null}
            <Button dense variant="ghost" disabled={mutation.state === "saving"} onClick={() => void member(ref, true)}>Remove</Button>
          </>} />)}
      </SurfaceLedger> : <SurfaceState empty emptyLabel="No items" />}
      <Button dense variant="ghost" onClick={() => setAdding((value) => !value)}>{adding ? "Close items" : "Add items"}</Button>
      {adding ? <SurfaceWell>
        <StringGadget label="Find items" value={query} onChange={setQuery} />
        <SurfaceLedger count={null} cols="room">
          {choices.map((entry) => <SurfaceLedgerRow key={qualifiedRef(entry.kind, entry.id)} primary={entry.title} meta={KIND_LABEL[entry.kind] || kindWord(entry.kind)}
            trailing={<Button dense variant="ghost" disabled={mutation.state === "saving"} onClick={() => void member(qualifiedRef(entry.kind, entry.id), false)}>Add</Button>} />)}
        </SurfaceLedger>
        {!choices.length ? <SurfaceState empty emptyLabel="No items found" /> : null}
      </SurfaceWell> : null}
    </SurfaceSection>
    {recovered ? <SurfaceSection label="Recovered text">
      <Material>{recovered}</Material>
      <Button variant="primary" disabled={mutation.state === "saving"} onClick={() => void recover()}>Save as Note</Button>
    </SurfaceSection> : null}
  </>;
}

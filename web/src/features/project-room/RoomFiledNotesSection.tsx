/** The Room's filed Notes. Project membership is a fresh resource read;
 * a Note's title and availability come from its own read when needed.
 * Opening is an explicit local door into the canonical Note window. */
import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import { ApiError, apiFetch } from "../../lib/api";
import { Button } from "../../components/signal/Signal";
import { openRef } from "../../desk/openObject";
import { useRoomRead } from "./roomReads";
import { ObjectList, SurfaceSection, StateChip, type ObjectSort, type ObjectSortKey } from "../../desk/surface";
import { FoldGadget } from "../../desk/surface/gadgets";
import type { DrawerMember } from "../../desk/drawer/members";
import type { ResourcesRead, ResourcesState } from "../../desk/drawer/useDrawerData";
import { DotWord } from "../../desk/surface/kit";
import "./project-room.css";

/** W6-H words: the return receipts in sentence case, as a dot + words. A
 *  failure says what failed and what stayed; Retry stands beside it. */
const RETURN = {
  checking: "Checking files",
  filesNotRead: "Could not read the files · Nothing changed",
  notFiled: "Not filed here",
  noteUnavailable: "Note not available",
  noteNotRead: "Could not read the note · Nothing changed",
  filed: "Filed here",
} as const;
const RETURN_TONE: Record<string, "ok" | "warn" | "fail" | "idle"> = {
  [RETURN.checking]: "idle",
  [RETURN.filesNotRead]: "fail",
  [RETURN.notFiled]: "warn",
  [RETURN.noteUnavailable]: "warn",
  [RETURN.noteNotRead]: "fail",
  [RETURN.filed]: "ok",
};

type NoteRef = `note:${string}`;
export type NoteRead = { state: "loading" | "ok" | "unavailable" | "failed"; title?: string };
export type FiledNoteAdapter = {
  read: (ref: NoteRef, signal: AbortSignal) => Promise<NoteRead>;
  open: (ref: NoteRef, context: { projectReturn: { projectId: string; resourceRef: NoteRef } }) => void;
};
const productionAdapter: FiledNoteAdapter = { read: fetchFiledNote, open: openRef };
export type FiledNoteRequest = { ref: NoteRef; seq: number } | null;

export function isFiledNoteRef(ref: string): ref is NoteRef {
  return ref.startsWith("note:") && ref.length > "note:".length;
}

export function filedNoteRefs(refs: readonly string[]): NoteRef[] {
  return [...new Set(refs.filter(isFiledNoteRef))];
}

async function fetchFiledNote(ref: NoteRef, signal: AbortSignal): Promise<NoteRead> {
  try {
    const body = await apiFetch<{ note?: { title?: unknown; deleted?: boolean } }>(
      `/api/notes/${encodeURIComponent(ref.slice("note:".length))}`, { signal },
    );
    if (!body?.note || body.note.deleted) return { state: "unavailable" };
    const title = typeof body.note.title === "string" ? body.note.title.trim() : "";
    return { state: "ok", title: title || "Note" };
  } catch (cause) {
    return { state: cause instanceof ApiError && cause.status === 404 ? "unavailable" : "failed" };
  }
}

export function RoomFiledNotesSection({ projectId, resourceRefs, resourcesState, refreshResources, members,
  followCurrentResources, request, onRequestHandled, presentationReady = true, adapter = productionAdapter,
}: {
  projectId: string;
  resourceRefs: readonly string[];
  resourcesState: ResourcesState;
  refreshResources: () => Promise<ResourcesRead>;
  followCurrentResources: (result: ResourcesRead) => Promise<ResourcesRead>;
  members: readonly DrawerMember[];
  request: FiledNoteRequest;
  onRequestHandled: (seq: number) => void;
  presentationReady?: boolean;
  adapter?: FiledNoteAdapter;
}) {
  // The Room gates on the FIRST read only. A re-read (every desk change)
  // must not make Files late again: at the cap it drew a Loading line that
  // vanished a moment later and moved Sources up by 40 px (393 held read).
  const firstSettled = useRef(false);
  if (resourcesState !== "loading") firstSettled.current = true;
  useRoomRead("files", firstSettled.current);
  const [expanded, setExpanded] = useState(false);
  const [selectedRef, setSelectedRef] = useState<NoteRef | null>(null);
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [noteReads, setNoteReads] = useState<Record<string, NoteRead>>({});
  const noteReadsRef = useRef(noteReads);
  noteReadsRef.current = noteReads;
  const pendingNotes = useRef(new Map<string, AbortController>());
  const returnGeneration = useRef(0);
  const openGeneration = useRef(0);
  // The last settled read held no filed Note (see the hidden fold below).
  const lastReadEmpty = useRef(false);
  const [returnReceipt, setReturnReceipt] = useState("");
  const [returnTarget, setReturnTarget] = useState<NoteRef | null>(null);
  const [focusRequest, setFocusRequest] = useState<{ ref: NoteRef; seq: number } | null>(null);
  const focusedSeq = useRef(0);
  const host = useRef<HTMLDivElement | null>(null);
  const noteRefs = useMemo(() => filedNoteRefs(resourceRefs), [resourceRefs]);
  const cached = useMemo(() => new Map(members.filter((m) => isFiledNoteRef(m.ref)).map((m) => [m.ref, m])), [members]);

  useEffect(() => () => {
    returnGeneration.current += 1;
    openGeneration.current += 1;
    for (const controller of pendingNotes.current.values()) controller.abort();
    pendingNotes.current.clear();
  }, []);

  const readNote = useCallback(async (ref: NoteRef, force = false): Promise<NoteRead> => {
    const prior = noteReadsRef.current[ref];
    if (!force && prior && prior.state !== "loading") return prior;
    pendingNotes.current.get(ref)?.abort();
    const controller = new AbortController();
    pendingNotes.current.set(ref, controller);
    setNoteReads((current) => ({ ...current, [ref]: { state: "loading", title: current[ref]?.title } }));
    const result = await adapter.read(ref, controller.signal);
    if (controller.signal.aborted || pendingNotes.current.get(ref) !== controller) return { state: "failed" };
    pendingNotes.current.delete(ref);
    setNoteReads((current) => ({ ...current, [ref]: result }));
    return result;
  }, [adapter]);

  // Cache data is only a label hint. Every filed Note needs its own successful
  // read before Open; Files expansion is the first permitted read command.
  useEffect(() => {
    if (!expanded || resourcesState !== "ok") return;
    for (const ref of noteRefs) {
      // The explicit return owns this ref's fresh membership/read decision.
      // A prior list must never start a Note read after NOT FILED HERE.
      if (ref === returnTarget) continue;
      if (!noteReads[ref] && !pendingNotes.current.has(ref)) void readNote(ref);
    }
  }, [expanded, resourcesState, noteRefs, cached, noteReads, readNote, returnTarget]);

  const resolveReturn = useCallback(async (ref: NoteRef, seq: number) => {
    const generation = ++returnGeneration.current;
    setExpanded(true);
    setReturnTarget(ref);
    setReturnReceipt(RETURN.checking);
    setSelectedRef(null);
    const result = await followCurrentResources(await refreshResources());
    if (generation !== returnGeneration.current) return;
    if (result.state === "stale") {
      // A scope that unmounted has no current read and cannot issue a receipt.
      return;
    }
    if (result.state === "failed") {
      setReturnReceipt(RETURN.filesNotRead);
      onRequestHandled(seq);
      return;
    }
    if (!filedNoteRefs(result.refs).includes(ref)) {
      setReturnReceipt(RETURN.notFiled);
      onRequestHandled(seq);
      return;
    }
    const note = await readNote(ref, true);
    if (generation !== returnGeneration.current) return;
    if (note.state === "unavailable") setReturnReceipt(RETURN.noteUnavailable);
    else if (note.state !== "ok") setReturnReceipt(RETURN.noteNotRead);
    else {
      setReturnReceipt(RETURN.filed);
      setSelectedRef(ref);
      setFocusRequest({ ref, seq });
    }
    onRequestHandled(seq);
  }, [refreshResources, followCurrentResources, readNote, onRequestHandled]);

  useEffect(() => {
    if (request) void resolveReturn(request.ref, request.seq);
  }, [request, resolveReturn]);

  useLayoutEffect(() => {
    // The Room can mount Files while its first-read body or late slot is
    // hidden. A browser ignores focus then, so keep this return pending.
    if (!presentationReady || !focusRequest || focusedSeq.current === focusRequest.seq) return;
    const row = [...(host.current?.querySelectorAll<HTMLElement>("[data-object-id]") ?? [])]
      .find((node) => node.dataset.objectId === focusRequest.ref);
    const button = row?.querySelector<HTMLButtonElement>(".object-list-open");
    if (!button) return;
    row?.scrollIntoView?.({ block: "center" });
    button.focus({ preventScroll: true });
    if (document.activeElement === button) focusedSeq.current = focusRequest.seq;
  }, [presentationReady, focusRequest, noteReads, resourceRefs, expanded]);

  const rows = noteRefs.map((ref) => {
    const read = noteReads[ref];
    const member = cached.get(ref);
    const name = read?.state === "unavailable" ? "Note not available"
      : read?.state === "failed" ? "Note not read"
        : read?.state === "ok" ? read.title || "Note"
          : member?.name || "Reading note";
    return { id: ref, kind: "note", name };
  });
  const retainedLoading = resourcesState === "loading" && rows.length > 0;
  if (resourcesState === "ok") lastReadEmpty.current = noteRefs.length === 0;
  else if (resourcesState === "failed") lastReadEmpty.current = false;
  const selectedRead = selectedRef ? noteReads[selectedRef] : undefined;
  const failedNote = noteRefs.find((ref) => noteReads[ref]?.state === "failed");
  const canOpen = resourcesState === "ok" && selectedRef && noteRefs.includes(selectedRef) &&
    selectedRead?.state === "ok";
  const open = async (ref: string) => {
    if (!isFiledNoteRef(ref) || resourcesState !== "ok" || !noteRefs.includes(ref)) return;
    const read = noteReadsRef.current[ref];
    if (read?.state !== "ok") return;
    const generation = ++openGeneration.current;
    const context = { projectReturn: { projectId, resourceRef: ref } };
    setReturnReceipt(RETURN.checking);
    const resources = await followCurrentResources(await refreshResources());
    if (generation !== openGeneration.current || resources.state === "stale") return;
    if (resources.state === "failed") { setReturnReceipt(RETURN.filesNotRead); return; }
    if (!filedNoteRefs(resources.refs).includes(ref)) { setReturnReceipt(RETURN.notFiled); setSelectedRef(null); return; }
    const note = await readNote(ref, true);
    if (generation !== openGeneration.current) return;
    if (note.state !== "ok") {
      setReturnReceipt(note.state === "unavailable" ? RETURN.noteUnavailable : RETURN.noteNotRead);
      return;
    }
    setReturnReceipt("");
    adapter.open(ref, context);
  };
  const retry = () => {
    if ((returnReceipt === RETURN.filesNotRead || returnReceipt === RETURN.noteNotRead) && returnTarget)
      void resolveReturn(returnTarget, Date.now());
    else if (resourcesState === "failed" || returnReceipt === RETURN.filesNotRead) void refreshResources();
    else if (selectedRef && noteReads[selectedRef]?.state === "failed") void readNote(selectedRef, true);
    else if (failedNote) void readNote(failedNote, true);
  };
  const sortBy = (key: ObjectSortKey) => setSort((current) => ({ key, dir: current.key === key && current.dir === "asc" ? "desc" : "asc" }));

  // Ordinary loading moves no pointer target: a Project whose last read
  // held no filed Note keeps the fold out of the Room while it reads again,
  // so Sources and Plan below it never jump by a fold row (the 393 held-read
  // fences). A first read, a failure or a receipt still draws the fold.
  if (!noteRefs.length && !returnReceipt &&
      (resourcesState === "ok" || (resourcesState === "loading" && lastReadEmpty.current))) return null;
  return <div className="room-fold" data-testid="room-fold-files" ref={host}>
    <FoldGadget title="Files" token={resourcesState === "ok" && noteRefs.length ? noteRefs.length : undefined}
      open={expanded || undefined} onToggle={setExpanded}>
      <SurfaceSection label="Files" data-testid="room-files" actions={<>
        {retainedLoading ? <StateChip state="working" label="READING FILES · LAST READ" /> : null}
        {(resourcesState === "failed" || returnReceipt === RETURN.filesNotRead || returnReceipt === RETURN.noteNotRead || failedNote) ?
          <Button dense variant="ghost" onClick={retry} data-testid="room-files-retry">Retry</Button> : null}
        <Button dense variant="ghost" disabled={!canOpen} onClick={() => selectedRef && void open(selectedRef)} data-testid="room-files-open">Open note</Button>
      </>}>
        {resourcesState === "loading" && !retainedLoading ? <StateChip state="working" label="READING FILES" /> : null}
        {resourcesState === "failed" ? <DotWord tone="fail">Files not read</DotWord> : null}
        {returnReceipt ? <div role="status" data-testid="room-files-return"><DotWord tone={RETURN_TONE[returnReceipt] ?? "idle"}>{returnReceipt}</DotWord></div> : null}
        {resourcesState !== "ok" && noteRefs.length && !retainedLoading ? <StateChip state="warning" label="LAST READ" /> : null}
        {rows.length ? <ObjectList label="Filed notes" rows={rows} sort={sort} onSort={sortBy} visibleColumns={["name", "kind"]}
          selectedId={selectedRef} onSelect={(id) => setSelectedRef(isFiledNoteRef(id) ? id : null)} onOpen={(id) => void open(id)} /> : null}
      </SurfaceSection>
    </FoldGadget>
  </div>;
}

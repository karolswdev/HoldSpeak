import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { countToken, StringGadget, SurfaceLedger, SurfaceLedgerRow, SurfaceSection, SurfaceState, SurfaceWell } from "../surface";
import { readableError } from "../../lib/api";
import {
  attachThoughtContext,
  detachThoughtContext,
  listThoughtContext,
  replaceDefaultThoughtContext,
  type Thought,
  type ThoughtAttachment,
  type ThoughtContextCandidate,
  type ThoughtContextReceipt,
  type ThoughtDefaultContext,
  type ThoughtDefaultContextReceipt,
  type ThoughtWorkspaceProjection,
  type ThoughtWorkspaceCursor,
} from "../thoughts";

type PickerResult = { thought: Thought; receipt: ThoughtContextReceipt; workbench?: ThoughtWorkspaceProjection };

// Keep an ambiguous action's identity when this browser refuses storage. A
// cleared entry also fences a stale stored ID if removeItem was refused.
const contextRequestIds = new Map<string, string | null>();
function contextRequestId(key: string): string {
  let id = contextRequestIds.get(key);
  if (!contextRequestIds.has(key)) {
    try { id = sessionStorage.getItem(key) || id; } catch { /* Memory owns this retry. */ }
  }
  if (!id) id = crypto.randomUUID();
  contextRequestIds.set(key, id);
  try { sessionStorage.setItem(key, id); } catch { /* Memory owns this retry. */ }
  return id;
}
function clearContextRequest(key: string) {
  contextRequestIds.set(key, null);
  try { sessionStorage.removeItem(key); contextRequestIds.delete(key); } catch { /* The accepted result still applies. */ }
}

export function ThoughtContextPicker({
  thought,
  anchor,
  onApplied,
  onDefaultApplied,
  onClose,
  workspaceCursor,
}: {
  thought: Thought;
  anchor: HTMLElement | null;
  onApplied: (result: PickerResult) => void;
  onDefaultApplied: (result: { default_context: ThoughtDefaultContext; receipt: ThoughtDefaultContextReceipt }) => void;
  onClose: () => void;
  workspaceCursor?: ThoughtWorkspaceCursor;
}) {
  const [query, setQuery] = useState("");
  const [view, setView] = useState<"compact" | "browse">("compact");
  const [attachments, setAttachments] = useState<ThoughtAttachment[]>(thought.attachments || []);
  const [defaultContext, setDefaultContext] = useState<ThoughtDefaultContext | null>(null);
  const [pinned, setPinned] = useState<ThoughtContextCandidate[]>([]);
  const [recent, setRecent] = useState<ThoughtContextCandidate[]>([]);
  const [results, setResults] = useState<ThoughtContextCandidate[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const generation = useRef(0);
  const pendingAction = useRef(false);
  const retryAction = useRef<(() => Promise<void>) | null>(null);
  const dialogRef = useRef<HTMLElement | null>(null);
  const rowRefs = useRef(new Map<string, HTMLButtonElement>());
  const [desktopPosition, setDesktopPosition] = useState<{ top: number; left: number } | null>(null);

  useEffect(() => { dialogRef.current?.focus(); }, []);
  useEffect(() => {
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault(); event.stopPropagation(); onClose();
    };
    window.addEventListener("keydown", closeOnEscape, true);
    return () => window.removeEventListener("keydown", closeOnEscape, true);
  }, [onClose]);
  useLayoutEffect(() => {
    if (!anchor || window.innerWidth <= 500) { setDesktopPosition(null); return; }
    const place = () => {
      const rect = anchor.getBoundingClientRect();
      const width = Math.min(420, window.innerWidth - 24);
      const height = Math.min(570, window.innerHeight - 24);
      const safeBottom = 64;
      const beside = rect.left >= width + 20 ? rect.left - width - 8 : rect.left;
      setDesktopPosition({
        top: Math.max(12, Math.min(window.innerHeight - safeBottom - height, rect.top - 80)),
        left: Math.max(12, Math.min(window.innerWidth - width - 12, beside)),
      });
    };
    place();
    window.addEventListener("resize", place);
    return () => window.removeEventListener("resize", place);
  }, [anchor]);

  const load = async (cursor?: string) => {
    const current = ++generation.current;
    setLoading(true);
    setError("");
    try {
      const listing = await listThoughtContext(thought.id, {
        view,
        query: query.trim() || undefined,
        cursor,
        limit: 20,
      });
      if (current !== generation.current) return;
      setAttachments(listing.attachments || []);
      setDefaultContext(listing.default_context);
      setPinned(listing.pinned || []);
      setRecent(listing.recent || []);
      setResults((prior) => cursor
        ? [...prior, ...(listing.results || [])].filter((row, index, all) => all.findIndex((item) => item.ref === row.ref) === index)
        : listing.results || []);
      setNextCursor(listing.next_cursor || null);
    } catch (cause) {
      if (current === generation.current) { setError(readableError(cause)); retryAction.current = () => load(cursor); }
    } finally {
      if (current === generation.current) setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, query ? 160 : 0);
    return () => { window.clearTimeout(timer); ++generation.current; };
  // `load` deliberately follows these inputs; a generation fence drops stale responses.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [thought.id, query, view]);

  const attach = async (row: ThoughtContextCandidate) => {
    if (pendingAction.current || row.disabled || row.selected) return;
    pendingAction.current = true;
    setPending(row.ref); setError("");
    const key = `hs.thought.context.attach.${thought.id}.${row.ref}`;
    try {
      const result = await attachThoughtContext(thought, row.ref, contextRequestId(key), workspaceCursor);
      clearContextRequest(key); onApplied(result); onClose();
    } catch (cause) {
      setError(readableError(cause));
      retryAction.current = () => attach(row);
      requestAnimationFrame(() => rowRefs.current.get(row.ref)?.focus());
    } finally { pendingAction.current = false; setPending(null); }
  };

  const remove = async (attachment: ThoughtAttachment) => {
    if (pendingAction.current) return;
    pendingAction.current = true;
    setPending(attachment.ref); setError("");
    const key = `hs.thought.context.detach.${thought.id}.${attachment.ref}`;
    try {
      const result = await detachThoughtContext(thought, attachment.ref, contextRequestId(key), workspaceCursor);
      clearContextRequest(key); onApplied(result); onClose();
    } catch (cause) { setError(readableError(cause)); retryAction.current = () => remove(attachment); }
    finally { pendingAction.current = false; setPending(null); }
  };

  const replaceDefault = async (refs: string[], action: "use" | "stop") => {
    if (pendingAction.current || !defaultContext) return;
    pendingAction.current = true;
    setPending(`default:${action}`); setError("");
    const key = `hs.thought.default-context.${action}.${defaultContext.revision}`;
    try {
      const result = await replaceDefaultThoughtContext({ request_id: contextRequestId(key), expected_revision: defaultContext.revision, refs });
      clearContextRequest(key); onDefaultApplied(result); onClose();
    } catch (cause) { setError(readableError(cause)); retryAction.current = () => replaceDefault(refs, action); }
    finally { pendingAction.current = false; setPending(null); }
  };

  const candidateRows = (items: ThoughtContextCandidate[]) => (
    <SurfaceLedger cols="kit"><ul className="surface-ledger-rows">
      {items.map((row) => {
        const disabled = Boolean(row.disabled || row.selected || pending);
        const noteCount = row.kind === "knowledge" ? (countToken(row.leaf_count, "note", "notes") ?? "Note") : "Note";
        const state = row.selected ? "Attached" : row.disabled_reason || noteCount;
        return <SurfaceLedgerRow key={row.ref} wrap kind="SRC" expands={false}
          primary={row.title} meta={state} trailing={<Button
          variant="secondary" dense loading={pending === row.ref}
          ref={(node: HTMLButtonElement | null) => { if (node) rowRefs.current.set(row.ref, node); else rowRefs.current.delete(row.ref); }}
          disabled={disabled}
          aria-label={`${row.title}, ${state}`} onClick={() => void attach(row)}
        >Attach</Button>}/>;
      })}
    </ul></SurfaceLedger>
  );

  const searching = Boolean(query.trim());
  const picker = <section ref={dialogRef} className="thought-context-picker" role="region" aria-label="Attach context" tabIndex={-1} style={desktopPosition || undefined}>
    <header className="thought-context-picker-head"><strong>Attach context</strong><Button variant="ghost" dense onClick={onClose}>Close</Button></header>
    <SurfaceSection label="On this Thought">
      {!attachments.length ? <SurfaceState empty emptyLabel="None"/> : <SurfaceLedger cols="kit"><ul className="surface-ledger-rows">{attachments.map((attachment) => {
        const isDef = attachment.is_default;
        return <SurfaceLedgerRow key={attachment.ref} wrap kind="SRC" expands={false} primary={attachment.title}
          meta={isDef ? <span className="thought-context-default-marker">Default</span> : undefined}
          trailing={<Button variant="secondary" dense aria-label="Remove from this Thought" loading={pending === attachment.ref} disabled={Boolean(pending)} onClick={() => void remove(attachment)}>Remove</Button>}/>;
      })}</ul></SurfaceLedger>}
      {attachments.length ? <div className="thought-context-picker-actions"><Button variant="secondary" dense aria-label="Use these by default" loading={pending === "default:use"} disabled={Boolean(pending || !defaultContext)} onClick={() => void replaceDefault(attachments.map((item) => item.ref), "use")}>Use for new Thoughts</Button></div> : null}
    </SurfaceSection>
    <SurfaceSection label="For new Thoughts">
      {!defaultContext ? loading ? <SurfaceState loading/> : null : !defaultContext.selections.length ? <SurfaceState empty emptyLabel="None"/> : <SurfaceLedger cols="kit"><ul className="surface-ledger-rows">{defaultContext.selections.map((selection) => {
        const leafCt = selection.leaf_count;
        return <SurfaceLedgerRow key={selection.ref} wrap kind="SRC" expands={false} primary={selection.title}
          meta={selection.state === "current" ? countToken(leafCt, "note", "notes") ?? "Note" : "Unavailable"}/>;
      })}</ul></SurfaceLedger>}
      {defaultContext?.selections.length ? <div className="thought-context-picker-actions"><Button variant="secondary" dense loading={pending === "default:stop"} disabled={Boolean(pending)} onClick={() => void replaceDefault([], "stop")}>Stop using by default</Button></div> : null}
    </SurfaceSection>
    {/* HS-176-04 — the voice law: the note search is spoken or typed. */}
    <SurfaceWell><StringGadget type="search" label="Search notes" caption micLabel="Speak note search" value={query} placeholder="Find a note…" onChange={(value) => { setQuery(value); setView("compact"); }} /></SurfaceWell>
    {error ? <SurfaceState error={error} onRetry={() => { void retryAction.current?.(); }}/> : null}
    {loading && !pinned.length && !recent.length && !results.length ? <SurfaceState loading/> : null}
    {!searching && view === "compact" ? <>
      {pinned.length ? <SurfaceSection label="Pinned">{candidateRows(pinned)}</SurfaceSection> : null}
      {recent.length ? <SurfaceSection label="Recent">{candidateRows(recent)}</SurfaceSection> : null}
      {!loading && !error && !pinned.length && !recent.length ? <SurfaceState empty emptyLabel="No pinned or recent context"/> : null}
      <div className="thought-context-picker-actions"><Button variant="secondary" dense onClick={() => setView("browse")}>Browse all notes</Button></div>
    </> : <SurfaceSection label={searching ? "Search results" : "All notes"}>
      {results.length ? candidateRows(results) : !loading && !error ? <SurfaceState empty emptyLabel="No matching notes"/> : null}
      <div className="thought-context-picker-actions">
        {nextCursor ? <Button variant="secondary" dense loading={loading} onClick={() => void load(nextCursor!)}>Show more</Button> : null}
        {!searching ? <Button variant="ghost" dense onClick={() => setView("compact")}>Back</Button> : null}
      </div>
    </SurfaceSection>}
  </section>;
  return createPortal(<div className="desk-next thought-context-overlay">{picker}</div>, document.body);
}

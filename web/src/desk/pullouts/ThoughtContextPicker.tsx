import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Button } from "../../components/signal/Signal";
import { countToken } from "../surface";
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
      if (current === generation.current) setError(readableError(cause));
    } finally {
      if (current === generation.current) setLoading(false);
    }
  };

  useEffect(() => {
    const timer = window.setTimeout(() => { void load(); }, query ? 160 : 0);
    return () => window.clearTimeout(timer);
  // `load` deliberately follows these inputs; a generation fence drops stale responses.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [thought.id, query, view]);

  const attach = async (row: ThoughtContextCandidate) => {
    if (pending || row.disabled || row.selected) return;
    setPending(row.ref); setError("");
    const key = `hs.thought.context.attach.${thought.id}.${row.ref}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try {
      const result = await attachThoughtContext(thought, row.ref, requestId, workspaceCursor);
      sessionStorage.removeItem(key); onApplied(result); onClose();
    } catch (cause) {
      setError(readableError(cause));
      requestAnimationFrame(() => rowRefs.current.get(row.ref)?.focus());
    } finally { setPending(null); }
  };

  const remove = async (attachment: ThoughtAttachment) => {
    if (pending) return;
    setPending(attachment.ref); setError("");
    const key = `hs.thought.context.detach.${thought.id}.${attachment.ref}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try {
      const result = await detachThoughtContext(thought, attachment.ref, requestId, workspaceCursor);
      sessionStorage.removeItem(key); onApplied(result); onClose();
    } catch (cause) { setError(readableError(cause)); }
    finally { setPending(null); }
  };

  const replaceDefault = async (refs: string[], action: "use" | "stop") => {
    if (pending || !defaultContext) return;
    setPending(`default:${action}`); setError("");
    const key = `hs.thought.default-context.${action}.${defaultContext.revision}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try {
      const result = await replaceDefaultThoughtContext({ request_id: requestId, expected_revision: defaultContext.revision, refs });
      sessionStorage.removeItem(key); onDefaultApplied(result); onClose();
    } catch (cause) { setError(readableError(cause)); }
    finally { setPending(null); }
  };

  const candidateRows = (items: ThoughtContextCandidate[]) => (
    <ul className="thought-context-picker-list">
      {items.map((row) => {
        const disabled = Boolean(row.disabled || row.selected || pending);
        const noteCount = row.kind === "knowledge" ? (countToken(row.leaf_count, "note", "notes") ?? "Note") : "Note";
        const state = row.selected ? "Attached" : row.disabled_reason || noteCount;
        return <li key={row.ref}><button type="button"
          ref={(node: HTMLButtonElement | null) => { if (node) rowRefs.current.set(row.ref, node); else rowRefs.current.delete(row.ref); }}
          className="btn btn--ghost btn--sm thought-context-choice" disabled={disabled}
          aria-label={`${row.title}, ${state}`} onClick={() => void attach(row)}
        ><span className="thought-context-choice-title">{row.title}</span><span className="thought-context-choice-meta">{pending === row.ref ? "Attaching…" : state}</span></button></li>;
      })}
    </ul>
  );

  const searching = Boolean(query.trim());
  const picker = <section ref={dialogRef} className="thought-context-picker" role="region" aria-label="Attach context" tabIndex={-1} style={desktopPosition || undefined}>
    <header className="thought-context-picker-head"><div><strong>Attach context</strong><small>Choose what AI may use for this Thought.</small></div><Button variant="ghost" dense className="thought-context-close" aria-label="Close" title="Close" onClick={onClose}>×</Button></header>
    <div className="thought-context-picker-group thought-context-policy-group"><h3>On this Thought</h3>
      {!attachments.length ? <><p className="thought-context-empty">None</p><p className="thought-context-empty">Attach context to use it by default.</p></> : <ul className="thought-context-picker-list">{attachments.map((attachment) => {
        const isDef = attachment.is_default;
        return <li key={attachment.ref} className="thought-context-policy-row">
        <span><span className="thought-context-choice-title">{attachment.title}</span>{isDef ? <small className="thought-context-default-marker">Default</small> : null}</span>
        <Button variant="ghost" dense className="thought-context-row-action" aria-label="Remove from this Thought" disabled={Boolean(pending)} onClick={() => void remove(attachment)}>{pending === attachment.ref ? "Removing…" : "Remove"}</Button>
      </li>; })}</ul>}
      {attachments.length ? <Button variant="ghost" dense className="thought-context-policy-action" aria-label="Use these by default" disabled={Boolean(pending || !defaultContext)} onClick={() => void replaceDefault(attachments.map((item) => item.ref), "use")}>{pending === "default:use" ? "Saving…" : "Use for new Thoughts"}</Button> : null}
    </div>
    <div className="thought-context-picker-group thought-context-policy-group"><h3>For new Thoughts</h3>
      {!defaultContext?.selections.length ? <p className="thought-context-empty">None</p> : <ul className="thought-context-picker-list">{defaultContext.selections.map((selection) => {
        const leafCt = selection.leaf_count;
        return <li key={selection.ref} className="thought-context-policy-row"><span className="thought-context-choice-title">{selection.title}</span><span className="thought-context-choice-meta">{selection.state === "current" ? countToken(leafCt, "note", "notes") ?? "Note" : "Unavailable"}</span></li>;
      })}</ul>}
      {defaultContext?.selections.length ? <Button variant="ghost" dense className="thought-context-policy-action" disabled={Boolean(pending)} onClick={() => void replaceDefault([], "stop")}>{pending === "default:stop" ? "Stopping…" : "Stop using by default"}</Button> : null}
    </div>
    {/* UX-CANON: needs redesign (HS-170-04) */}
    <label className="thought-context-search"><span className="sr-only">Search notes</span><span aria-hidden="true">⌕</span><input type="search" value={query} placeholder="Find a note…" onChange={(event) => { setQuery(event.target.value); setView("compact"); }} /></label>
    {error ? <p role="alert" className="thought-context-error">{error}</p> : null}
    {loading && !pinned.length && !recent.length && !results.length ? <p role="status" className="thought-context-empty">Loading context…</p> : null}
    {!searching && view === "compact" ? <>
      {pinned.length ? <div className="thought-context-picker-group"><h3>Pinned</h3>{candidateRows(pinned)}</div> : null}
      {recent.length ? <div className="thought-context-picker-group"><h3>Recent</h3>{candidateRows(recent)}</div> : null}
      {!loading && !pinned.length && !recent.length ? <p className="thought-context-empty">No pinned or recent context yet.</p> : null}
      <Button variant="ghost" dense className="desk-chip quiet thought-context-browse" onClick={() => setView("browse")}>Browse all notes</Button>
    </> : <div className="thought-context-picker-group"><h3>{searching ? "Search results" : "All notes"}</h3>
      {results.length ? candidateRows(results) : !loading ? <p className="thought-context-empty">No matching notes.</p> : null}
      {nextCursor ? <Button variant="ghost" dense className="desk-chip quiet thought-context-more-results" disabled={loading} onClick={() => void load(nextCursor)}>{loading ? "Loading…" : "Show more"}</Button> : null}
      {!searching ? <Button variant="ghost" dense className="desk-chip quiet" onClick={() => setView("compact")}>Back</Button> : null}
    </div>}
  </section>;
  return createPortal(<div className="desk-next thought-context-overlay">{picker}</div>, document.body);
}

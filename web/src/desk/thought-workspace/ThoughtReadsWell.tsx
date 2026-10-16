import { useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import { CheckGadget, countToken, StringGadget, SurfaceState } from "../surface";
import {
  attachThoughtContext,
  detachThoughtContext,
  listThoughtContext,
  type Thought,
  type ThoughtAttachment,
  type ThoughtContextCandidate,
  type ThoughtContextReceipt,
  type ThoughtWorkspaceCursor,
  type ThoughtWorkspaceProjection,
} from "../thoughts";

export type ReadsResult = { thought: Thought; receipt: ThoughtContextReceipt; workbench?: ThoughtWorkspaceProjection };

const CANDIDATE_CAP = 6;
const readsRequestIds = new Map<string, string | null>();
function readsRequestId(key: string): string {
  let id = readsRequestIds.get(key);
  if (!readsRequestIds.has(key)) {
    try { id = sessionStorage.getItem(key) || id; } catch { /* Memory owns this retry. */ }
  }
  if (!id) id = crypto.randomUUID();
  readsRequestIds.set(key, id);
  try { sessionStorage.setItem(key, id); } catch { /* Memory owns this retry. */ }
  return id;
}
function clearReadsRequest(key: string) {
  readsRequestIds.set(key, null);
  try { sessionStorage.removeItem(key); readsRequestIds.delete(key); } catch { /* Keep the accepted receipt. */ }
}

/* HS-201-12 — band 4's `Add a note`: what the AI may read for THIS note, as an
   in-window well under the foot.  Library species only, no portal overlay,
   no prose, no raw elements (the Phase 141 picker has all three, and
   keeps them for the Note pullout, where default-context policy lives). */
export function ThoughtReadsWell({
  thought,
  cursor,
  disabled,
  onApplied,
  onClose,
}: {
  thought: Thought;
  cursor?: ThoughtWorkspaceCursor;
  disabled?: boolean;
  onApplied: (result: ReadsResult) => void;
  onClose: () => void;
}) {
  const [attachments, setAttachments] = useState<ThoughtAttachment[]>(thought.attachments || []);
  const [candidates, setCandidates] = useState<ThoughtContextCandidate[]>([]);
  const [query, setQuery] = useState("");
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [readAttempt, setReadAttempt] = useState(0);
  const wellRef = useRef<HTMLDivElement | null>(null);
  const pendingAction = useRef(false);
  const retryAction = useRef<(() => void) | null>(null);

  // The well takes focus when it opens, so Escape always lands in it and
  // the caller can send focus back to Add a note when it closes.
  useEffect(() => { wellRef.current?.focus(); }, []);

  useEffect(() => {
    const close = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      event.stopPropagation();
      onClose();
    };
    const node = wellRef.current;
    node?.addEventListener("keydown", close);
    return () => node?.removeEventListener("keydown", close);
  }, [onClose]);

  /* Astra finding 3 — six pinned/recent rows is not a chooser on a desk
     with many notes: the well searches the real listing (the same endpoint
     the picker uses), debounced, and the mic rides the field (voice law). */
  useEffect(() => {
    let live = true;
    setLoading(true);
    const run = async () => {
      try {
        const search = query.trim();
        const listing = await listThoughtContext(thought.id, {
          view: search ? "browse" : "compact",
          query: search || undefined,
          limit: CANDIDATE_CAP,
        });
        if (!live) return;
        setAttachments(listing.attachments || []);
        setError("");
        const held = new Set((listing.attachments || []).map((item) => item.ref));
        const pool = search
          ? listing.results || []
          : [...(listing.pinned || []), ...(listing.recent || [])];
        setCandidates(pool
          .filter((row, index, all) => !held.has(row.ref) && all.findIndex((item) => item.ref === row.ref) === index)
          .slice(0, CANDIDATE_CAP));
      } catch (cause) {
        if (live) { setError(readableError(cause)); retryAction.current = () => setReadAttempt((attempt) => attempt + 1); }
      } finally { if (live) setLoading(false); }
    };
    const timer = window.setTimeout(() => { void run(); }, query ? 160 : 0);
    return () => { live = false; window.clearTimeout(timer); };
  }, [thought.id, thought.attachment_revision, query, readAttempt]);

  const change = async (ref: string, next: boolean) => {
    if (pendingAction.current || disabled) return;
    pendingAction.current = true;
    setPending(ref);
    setError("");
    const key = `hs.thought.reads.${next ? "attach" : "detach"}.${thought.id}.${ref}`;
    try {
      const requestId = readsRequestId(key);
      const result = next
        ? await attachThoughtContext(thought, ref, requestId, cursor)
        : await detachThoughtContext(thought, ref, requestId, cursor);
      clearReadsRequest(key);
      onApplied(result);
    } catch (cause) {
      setError(readableError(cause));
      retryAction.current = () => { void change(ref, next); };
    } finally {
      pendingAction.current = false;
      setPending(null);
    }
  };

  const row = (ref: string, title: string, leaves: number, checked: boolean) => {
    const token = countToken(leaves, "NOTE");
    return <div key={ref} className="thought-reads-row">
      {/* The token variant DRAWS its name: a bare checkbox square would
          leave the owner a control he cannot read (the well's shot). */}
      <CheckGadget
        variant="token"
        label={title}
        checked={checked}
        disabled={Boolean(disabled || pending)}
        onChange={(next) => void change(ref, next)}
      />
      {token ? <span className="surface-token" data-chip>{token}</span> : null}
    </div>;
  };

  return <div ref={wellRef} className="thought-reads-well" role="region" aria-label="Add notes" tabIndex={-1}>
    <span className="thought-reads-find">
      <StringGadget label="Add notes" micLabel="Speak a note to add" value={query} onChange={setQuery} placeholder="Find a note…" />
    </span>
    <span className="thought-reads-rows">
      {attachments.map((item) => row(item.ref, item.title, item.leaf_count, true))}
      {candidates.map((item) => row(item.ref, item.title, item.leaf_count, false))}
      {loading && !attachments.length && !candidates.length ? <SurfaceState loading/> : null}
      {!loading && !attachments.length && !candidates.length && !error ? <span className="surface-token">{query.trim() ? "No match" : "Nothing to read yet"}</span> : null}
    </span>
    {error ? <SurfaceState error={error} onRetry={() => retryAction.current?.()}/> : null}
  </div>;
}

import { useEffect, useRef, useState } from "react";
import { readableError } from "../../lib/api";
import { CheckGadget, countToken } from "../surface";
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

/* HS-201-12 — band 4's `Change`: what the AI may read for THIS note, as an
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
  const [pending, setPending] = useState<string | null>(null);
  const [error, setError] = useState("");
  const wellRef = useRef<HTMLDivElement | null>(null);

  // The well takes focus when it opens, so Escape always lands in it and
  // the caller can send focus back to Change when it closes.
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

  useEffect(() => {
    let live = true;
    void (async () => {
      try {
        const listing = await listThoughtContext(thought.id, { view: "compact", limit: CANDIDATE_CAP });
        if (!live) return;
        setAttachments(listing.attachments || []);
        const held = new Set((listing.attachments || []).map((item) => item.ref));
        setCandidates([...(listing.pinned || []), ...(listing.recent || [])]
          .filter((row, index, all) => !held.has(row.ref) && all.findIndex((item) => item.ref === row.ref) === index)
          .slice(0, CANDIDATE_CAP));
      } catch (cause) {
        if (live) setError(readableError(cause));
      }
    })();
    return () => { live = false; };
  }, [thought.id, thought.attachment_revision]);

  const change = async (ref: string, next: boolean) => {
    if (pending || disabled) return;
    setPending(ref);
    setError("");
    const key = `hs.thought.reads.${next ? "attach" : "detach"}.${thought.id}.${ref}`;
    const requestId = sessionStorage.getItem(key) || crypto.randomUUID();
    sessionStorage.setItem(key, requestId);
    try {
      const result = next
        ? await attachThoughtContext(thought, ref, requestId, cursor)
        : await detachThoughtContext(thought, ref, requestId, cursor);
      sessionStorage.removeItem(key);
      onApplied(result);
    } catch (cause) {
      setError(readableError(cause));
    } finally {
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

  return <div ref={wellRef} className="thought-reads-well" role="region" aria-label="What the AI reads" tabIndex={-1}>
    {attachments.map((item) => row(item.ref, item.title, item.leaf_count, true))}
    {candidates.map((item) => row(item.ref, item.title, item.leaf_count, false))}
    {!attachments.length && !candidates.length && !error ? <span className="surface-token">Nothing to read yet</span> : null}
    {error ? <span className="thought-reads-error" role="alert">{error}</span> : null}
  </div>;
}

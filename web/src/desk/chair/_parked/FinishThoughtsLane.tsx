// PARKED (HS-170-04)
import { useEffect, useRef, useState } from "react";
import { useDesk } from "../store";
import { unfinishedThoughts, type UnfinishedThought } from "../thoughts";

const continuityLabels: Record<UnfinishedThought["continuity_state"], string> =
  {
    idle: "Continue",
    reserved: "Working",
    in_flight: "Working",
    awaiting_projection: "Working",
    review_ready: "Ready for you",
    stale: "Needs attention",
    named_failure: "Needs attention",
    unavailable_remote: "Needs attention",
  };

function sourceLabel(kind: UnfinishedThought["source_kind"]): string {
  if (kind === "voice") return "Voice";
  if (kind === "note") return "Note";
  return "Typed";
}

function comparable(value: string): string {
  return value.trim().replace(/\s+/g, " ").toLocaleLowerCase();
}

export function relativeUpdated(value: string, now = Date.now()): string {
  const then = new Date(value).getTime();
  if (!Number.isFinite(then)) return "Updated recently";
  const seconds = Math.max(0, Math.floor((now - then) / 1000));
  if (seconds < 60) return "Updated now";
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `Updated ${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `Updated ${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `Updated ${days}d ago`;
  const weeks = Math.floor(days / 7);
  if (weeks < 5) return `Updated ${weeks}w ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `Updated ${months}mo ago`;
  return `Updated ${Math.floor(days / 365)}y ago`;
}

export function FinishThoughtsLane() {
  const deskUpdatedAt = useDesk((state) => state.updatedAt);
  const [items, setItems] = useState<UnfinishedThought[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const loadingRef = useRef(true);

  const load = async (cursor?: string) => {
    if (loadingRef.current) return;
    loadingRef.current = true;
    setLoading(true);
    try {
      const page = await unfinishedThoughts(cursor);
      setItems((current) => {
        if (!cursor) return page.items;
        const known = new Set(current.map((item) => item.id));
        return [
          ...current,
          ...page.items.filter((item) => !known.has(item.id)),
        ];
      });
      setNextCursor(page.next_cursor);
    } catch {
      // The current rows remain useful; retry is the same explicit Show more.
    } finally {
      loadingRef.current = false;
      setLoading(false);
    }
  };

  useEffect(() => {
    let live = true;
    void unfinishedThoughts()
      .then((page) => {
        if (!live) return;
        setItems(page.items);
        setNextCursor(page.next_cursor);
      })
      .catch(() => undefined)
      .finally(() => {
        if (live) {
          loadingRef.current = false;
          setLoading(false);
        }
      });
    return () => {
      live = false;
    };
  }, [deskUpdatedAt]);

  if (!items.length) return null;

  const count = items.length > 0 ? `${items.length}${nextCursor ? "+" : ""}` : null;
  return (
    <section
      className="finish-thoughts"
      aria-labelledby="finish-thoughts-title"
    >
      <header className="finish-thoughts-head">
        <h2 id="finish-thoughts-title">Finish thoughts</h2>
        <span
          aria-label={items.length > 0 ? `${items.length}${nextCursor ? " or more" : ""} unfinished thoughts` : "unfinished thoughts"}
        >
          {count}
        </span>
      </header>
      <ul className="finish-thoughts-list">
        {items.map((thought) => {
          const title = thought.title.trim() || "Untitled thought";
          const preview = thought.body_preview.trim();
          const sourceKind = thought.source_kind;
          const updatedAt = thought.updated_at;
          const continuityState = thought.continuity_state;
          const showPreview =
            Boolean(preview) && comparable(preview) !== comparable(title);
          return (
            <li key={thought.id} className="finish-thoughts-item">
              <button
                type="button"
                className="finish-thoughts-row"
                onClick={() =>
                  useDesk
                    .getState()
                    .openPullout(`note:${thought.working_note_id}`)
                }
              >
                <span className="finish-thoughts-copy">
                  <strong>{title}</strong>
                  {showPreview ? (
                    <span className="finish-thoughts-preview">{preview}</span>
                  ) : null}
                  <span className="finish-thoughts-meta">
                    <span>{sourceLabel(sourceKind)}</span><span>{relativeUpdated(updatedAt)}</span><span>{continuityLabels[continuityState]}</span>
                    {thought.filing_status === "missing" ? (
                      <span>Not in a drawer</span>
                    ) : null}
                  </span>
                </span>
                <span className="finish-thoughts-arrow" aria-hidden="true">
                  ›
                </span>
              </button>
            </li>
          );
        })}
      </ul>
      {nextCursor ? (
        <button
          type="button"
          className="desk-chip quiet finish-thoughts-more"
          disabled={loading}
          onClick={() => void load(nextCursor)}
        >
          {loading ? "Loading…" : "Show more"}
        </button>
      ) : null}
    </section>
  );
}

import { useCallback, useEffect, useState, type ReactNode } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { useWriteReceipt } from "../../hooks/useWriteReceipt";
import { refreshIntelligenceAttention } from "../../intelligenceAttention";
import { openSurfaceOr } from "../../shell";
import { FoldGadget } from "../../surface/gadgets";
import { SurfaceLedgerRow, SurfaceState } from "../../surface/Surface";
import { SurfaceFooter } from "../../surface/SurfaceFooter";

interface BriefItem {
  id: string;
  section: BriefSection;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
}

type BriefSection = "changed" | "broke" | "waiting" | "decisions";

type ShelfState = "acknowledged" | "deferred";

type MondayBrief = {
  id: string;
  headline: string;
  sections: Partial<Record<BriefSection, BriefItem[]>>;
  is_empty: boolean;
  /** HS-132-08 — durable triage, read back with the brief itself. */
  shelf?: Record<string, ShelfState>;
};

const GROUPS: ReadonlyArray<{ id: BriefSection; label: string }> = [
  { id: "changed", label: "Changed" },
  { id: "broke", label: "Broke" },
  { id: "waiting", label: "Waiting" },
  { id: "decisions", label: "Your Decisions" },
];

function sourceLabel(sourceRef: string): string {
  return sourceRef.replace(/:/g, " · ").replace(/_/g, " ");
}

/** The desk's compact daily operating picture, sourced only from MondayBriefService facts. */
export function BriefView({ header, onOpenFollowThrough }: { header: ReactNode; onOpenFollowThrough?: (id: string) => void }) {
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [shelf, setShelf] = useState<Record<string, ShelfState>>({});
  const [shelving, setShelving] = useState(false);
  const [narrow, setNarrow] = useState(false);
  const [openGroup, setOpenGroup] = useState<BriefSection | null>("changed");
  const { attempt, receipt } = useWriteReceipt();

  useEffect(() => {
    const media = window.matchMedia("(max-width: 420px)");
    const update = () => setNarrow(media.matches);
    update();
    media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const latest = await apiFetch<MondayBrief | null>("/api/brief/latest");
      setBrief(latest);
      setShelf(latest?.shelf ?? {});
    } catch (requestError) {
      setError(readableError(requestError));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const generate = async () => {
    setGenerating(true);
    setError("");
    try {
      const generated = await apiFetch<MondayBrief>("/api/brief/generate", { method: "POST" });
      setBrief(generated);
      setShelf(generated?.shelf ?? {});
    } catch (requestError) {
      setError(readableError(requestError));
    } finally {
      setGenerating(false);
    }
  };

  const selected = GROUPS.flatMap(({ id }) => brief?.sections[id] ?? []).find(
    (item) => item.id === selectedId,
  );
  // HS-132-08 — triage is a write, not React state: it rides the durable
  // shelf so Acknowledge/Defer survive reload and the pullout closing, and it
  // reports a refusal through the one write-receipt channel.
  const setShelfState = async (state: ShelfState) => {
    const itemId = selectedId;
    if (!itemId) return;
    const next: ShelfState | null = shelf[itemId] === state ? null : state;
    setShelving(true);
    const result = await attempt(
      next === null ? "clear triage" : next,
      () =>
        apiFetch(`/api/brief/items/${encodeURIComponent(itemId)}/shelf`, {
          method: "POST",
          json: { state: next },
        }),
    );
    setShelving(false);
    if (!result.ok) return;
    setShelf((current) => {
      const updated = { ...current };
      if (next === null) delete updated[itemId];
      else updated[itemId] = next;
      return updated;
    });
    refreshIntelligenceAttention();
  };

  const body = loading ? (
    <SurfaceState loading />
  ) : error ? (
    <SurfaceState error={error} onRetry={() => void load()} />
  ) : !brief ? (
    <SurfaceState
      empty
      emptyLabel="No brief generated."
      onAction={() => void generate()}
      actionLabel={generating ? "Generating…" : "Generate"}
    />
  ) : brief.is_empty ? (
    <SurfaceState empty emptyLabel="Nothing material changed." />
  ) : (
    <>
      <div className="intelligence-brief-headline" role="heading" aria-level={2}>{brief.headline}</div>
      <div className="intelligence-brief-groups">
        {GROUPS.map(({ id, label }) => {
          const items = brief.sections[id] ?? [];
          return (
            <FoldGadget
              key={id}
              title={label}
              token={String(items.length).padStart(2, "0")}
              open={narrow ? openGroup === id : items.length > 0}
              onToggle={(open) => {
                if (narrow) setOpenGroup(open ? id : null);
              }}
              className={`intelligence-brief-group intelligence-brief-group-${id}`}
            >
              {items.length ? (
                <ul className="intelligence-brief-rows">
                  {items.map((item) => {
                    const state = shelf[item.id];
                    const isOpen = selectedId === item.id;
                    return (
                      <SurfaceLedgerRow
                        key={item.id}
                        primary={item.text}
                        open={isOpen}
                        onToggle={() => {
                          const followThroughId = item.source_ref?.match(/^(?:follow-through|action_item):(.+)$/)?.[1];
                          if (followThroughId && onOpenFollowThrough) onOpenFollowThrough(followThroughId);
                          else setSelectedId(isOpen ? null : item.id);
                        }}
                        lineLabel={`${label}: ${item.text}`}
                        cells={
                          state ? (
                            <span className="intelligence-brief-shelf-state">
                              {state}
                            </span>
                          ) : undefined
                        }
                      >
                        <div className="intelligence-brief-item-detail">
                          {item.detail ? <p>{item.detail}</p> : null}
                          {item.source_ref ? (
                            <span className="intelligence-brief-source">
                              SOURCE · {sourceLabel(item.source_ref)}
                            </span>
                          ) : null}
                        </div>
                      </SurfaceLedgerRow>
                    );
                  })}
                </ul>
              ) : (
                <p className="intelligence-brief-none">Nothing here.</p>
              )}
            </FoldGadget>
          );
        })}
      </div>
    </>
  );

  return (
    <>
      <div className="desk-pullout-body desk-surface-body intelligence-pullout">
        {header}
        <section className="intelligence-view intelligence-brief" aria-live="polite">
          {body}
        </section>
      </div>
      <SurfaceFooter
        receipt={
          receipt ??
          (selected ? `SELECTED · ${sourceLabel(selected.source_ref ?? selected.id)}` : undefined)
        }
        verbs={
          <>
            <Button
              dense
              disabled={!selected || shelving}
              aria-pressed={selectedId ? shelf[selectedId] === "acknowledged" : undefined}
              onClick={() => void setShelfState("acknowledged")}
            >
              Acknowledge
            </Button>
            <Button
              dense
              variant="ghost"
              disabled={!selected || shelving}
              aria-pressed={selectedId ? shelf[selectedId] === "deferred" : undefined}
              onClick={() => void setShelfState("deferred")}
            >
              Defer
            </Button>
            <Button
              dense
              variant="ghost"
              disabled={!selected}
              onClick={() => selected && openSurfaceOr("dictate", "/dictation", selected.source_ref ?? undefined)}
            >
              Speak
            </Button>
          </>
        }
      />
    </>
  );
}

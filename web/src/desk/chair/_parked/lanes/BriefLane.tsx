// PARKED (HS-170-04)
// HS-135-07 -- the Brief lane: the headline truth ("N things waiting"),
// Changed/Broke/Waiting/Decisions counts, top items to the maxItems
// bound. Per-item Acknowledge/Defer verbs reuse the existing shelf
// actions from BriefView.  Header-click opens Intelligence on the
// Brief wing.  The no-false-ALL-CLEAR law (Phase 132) holds: the lane
// can never read clear while commitments exist.

import { useCallback, useEffect, useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { apiFetch, readableError } from "../../../lib/api";
import { clearWriteFailure, reportWriteFailure } from "../../hooks/useWriteReceipt";
import { refreshIntelligenceAttention, untriagedBriefItems } from "../../intelligenceAttention";
import { openIntelligence } from "../../intelligenceNavigation";
import {
  SurfaceRows,
  SurfaceRow,
  SurfaceSection,
  SurfaceState,
} from "../../surface/Surface";
import { DEFAULT_MAX_ITEMS, type LaneProps } from "../laneContract";

// ---------------------------------------------------------------------------
// types -- reused from BriefView (no new endpoints)
// ---------------------------------------------------------------------------

type BriefSection = "changed" | "broke" | "waiting" | "decisions";
type ShelfState = "acknowledged" | "deferred";

interface BriefItemData {
  id: string;
  section: BriefSection;
  text: string;
  detail?: string | null;
  source_ref?: string | null;
  priority: number;
}

type MondayBrief = {
  id: string;
  headline: string;
  sections: Partial<Record<BriefSection, BriefItemData[]>>;
  is_empty: boolean;
  shelf?: Record<string, ShelfState>;
};

const SECTIONS: ReadonlyArray<{ id: BriefSection; label: string }> = [
  { id: "changed", label: "Changed" },
  { id: "broke", label: "Broke" },
  { id: "waiting", label: "Waiting" },
  { id: "decisions", label: "Decisions" },
];

// ---------------------------------------------------------------------------
// the lane
// ---------------------------------------------------------------------------

export function BriefLane({
  maxItems = DEFAULT_MAX_ITEMS,
  onOpenInWindow,
}: LaneProps) {
  const [brief, setBrief] = useState<MondayBrief | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [shelf, setShelf] = useState<Record<string, ShelfState>>({});
  const [busyItemId, setBusyItemId] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch<MondayBrief | null>("/api/brief/latest");
      setBrief(data);
      setShelf(data?.shelf ?? {});
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const generateBrief = useCallback(async () => {
    setGenerating(true);
    setError("");
    try {
      const data = await apiFetch<MondayBrief>("/api/brief/generate", { method: "POST" });
      setBrief(data);
      setShelf(data?.shelf ?? {});
    } catch (cause) {
      setError(readableError(cause));
    } finally {
      setGenerating(false);
    }
  }, []);

  // -- shelf verbs (reused from BriefView) --------------------------------

  const doShelf = async (itemId: string, state: ShelfState) => {
    const current = shelf[itemId];
    const next: ShelfState | null = current === state ? null : state;
    setBusyItemId(itemId);
    try {
      await apiFetch(`/api/brief/items/${encodeURIComponent(itemId)}/shelf`, {
        method: "POST",
        json: { state: next },
      });
      clearWriteFailure();
      setShelf((prev) => {
        const updated = { ...prev };
        if (next === null) delete updated[itemId];
        else updated[itemId] = next;
        return updated;
      });
      refreshIntelligenceAttention();
    } catch (cause) {
      reportWriteFailure(
        next === null ? "clear brief triage" : `${next} brief item`,
        cause,
        () => void doShelf(itemId, state),
      );
    } finally {
      setBusyItemId(null);
    }
  };

  // -- render -------------------------------------------------------------

  if (loading) return <SurfaceState loading />;
  if (error && !brief) {
    return <SurfaceState error={error} onRetry={() => void load()} />;
  }
  if (!brief) {
    return (
      <SurfaceSection label="BRIEF">
        <div
          className="brief-lane-act"
          role="status"
          data-testid="brief-lane-act"
        >
          <button
            type="button"
            className="brief-lane-act-generate"
            onClick={() => void generateBrief()}
            disabled={generating}
            aria-label="Generate your brief"
          >
            {generating ? "Generating..." : "Generate your brief"}
          </button>
        </div>
      </SurfaceSection>
    );
  }
  if (brief.is_empty) return null;

  // Flatten all items in section order (changed, broke, waiting, decisions).
  const allItems = SECTIONS.flatMap(({ id }) => brief.sections[id] ?? []);

  // HS-132-08 -- the no-false-ALL-CLEAR law: if there are untriaged
  // items the lane MUST render content; it can never say "clear".
  // When the brief has items (is_empty = false), we always render --
  // the null return above only fires on truly empty briefs.

  const untriaged = untriagedBriefItems(brief);
  const headline =
    untriaged === 0
      ? "Everything triaged"
      : untriaged === 1
        ? "1 thing waiting"
        : `${untriaged} things waiting`;

  // Counts per section.
  const counts = SECTIONS.map(({ id, label }) => ({
    id,
    label,
    count: (brief.sections[id] ?? []).length,
  }));

  const visible = allItems.slice(0, maxItems);
  const overflow = allItems.length - visible.length;

  const openBrief = () => {
    openIntelligence({ view: "brief" });
  };

  return (
    <>
      <SurfaceSection
        label="BRIEF"
        actions={
          <button
            type="button"
            className="chair-lane-header-verb"
            onClick={openBrief}
            aria-label="Open BRIEF"
          >
            {String(allItems.length).padStart(2, "0")}
          </button>
        }
      >
        <div className="brief-lane-headline" role="heading" aria-level={3}>
          {headline}
        </div>
        <div className="brief-lane-counts" aria-label="Brief section counts">
          {counts.map(({ id, label, count }) => (
            <span key={id} className="brief-lane-count" data-section={id}>
              {label} {String(count).padStart(2, "0")}
            </span>
          ))}
        </div>
        {visible.length > 0 ? (
          <SurfaceRows>
            {visible.map((item) => {
              const section = SECTIONS.find((s) => s.id === item.section);
              const shelfState = shelf[item.id];
              return (
                <SurfaceRow
                  key={item.id}
                  title={item.text}
                  detail={
                    shelfState
                      ? `${section?.label ?? item.section} -- ${shelfState}`
                      : section?.label ?? item.section
                  }
                  onOpen={() => onOpenInWindow(item.id)}
                  verbs={
                    <>
                      <Button
                        dense
                        variant="ghost"
                        disabled={busyItemId === item.id}
                        aria-pressed={shelfState === "acknowledged"}
                        onClick={() => void doShelf(item.id, "acknowledged")}
                        aria-label={`Acknowledge ${item.text}`}
                      >
                        Ack
                      </Button>
                      <Button
                        dense
                        variant="ghost"
                        disabled={busyItemId === item.id}
                        aria-pressed={shelfState === "deferred"}
                        onClick={() => void doShelf(item.id, "deferred")}
                        aria-label={`Defer ${item.text}`}
                      >
                        Defer
                      </Button>
                    </>
                  }
                />
              );
            })}
          </SurfaceRows>
        ) : null}
        {overflow > 0 ? (
          <button
            type="button"
            className="chair-lane-footer"
            onClick={openBrief}
          >
            {overflow} more -- Open Intelligence
          </button>
        ) : null}
      </SurfaceSection>
    </>
  );
}

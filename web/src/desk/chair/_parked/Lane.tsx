// PARKED (HS-170-04)
// HS-135-05 -- the Lane component: the composition contract's React
// shape. Each lane receives {title, maxItems, items, onOpenInWindow,
// footerVerb}. Header-click fires onOpenInWindow. Renders Surface
// primitives only.

import type { ReactNode } from "react";
import { SurfaceSection, SurfaceRows, SurfaceRow } from "../surface/Surface";
import { DEFAULT_MAX_ITEMS } from "./laneContract";

export interface LaneItem {
  id: string;
  title: ReactNode;
  detail?: ReactNode;
  meta?: ReactNode;
  glyph?: ReactNode;
}

export interface ChairLaneProps {
  /** The lane's section label (e.g. "BRIEF", "FOLLOW-THROUGH"). */
  title: string;
  /** Curated-dozen bound (default 12). */
  maxItems?: number;
  /** The items to render (capped at maxItems). */
  items: LaneItem[];
  /** Open the full surface in a DeskWindow. Fires on header click and
   *  per-item actions. */
  onOpenInWindow: (id: string) => void;
  /** Opens the full surface (header click). */
  surfaceId: string;
  /** Optional footer verb label (e.g. "Open Intelligence"). */
  footerVerb?: string;
  /** Honest in-lane treatment when this named lane has no rows. */
  emptyState?: ReactNode;
}

/** The lane component: L2's composition contract rendered as Surface
 *  primitives. No per-lane spinners, no bespoke CSS -- the Chair shows
 *  a single SurfaceState when ALL lanes are blank (counsel condition 2). */
export function ChairLane({
  title,
  maxItems = DEFAULT_MAX_ITEMS,
  items,
  onOpenInWindow,
  surfaceId,
  footerVerb,
  emptyState,
}: ChairLaneProps) {
  const visible = items.slice(0, maxItems);
  const overflow = items.length - visible.length;

  return (
    <SurfaceSection
      label={title}
      actions={
        <button
          type="button"
          className="chair-lane-header-verb"
          onClick={() => onOpenInWindow(surfaceId)}
          aria-label={`Open ${title}`}
        >
          {items.length > 0 ? String(items.length).padStart(2, "0") : null}
        </button>
      }
    >
      {visible.length > 0 ? (
        <SurfaceRows>
          {visible.map((item) => (
            <SurfaceRow
              key={item.id}
              glyph={item.glyph}
              title={item.title}
              detail={item.detail}
              meta={item.meta}
              onOpen={() => onOpenInWindow(item.id)}
            />
          ))}
        </SurfaceRows>
      ) : emptyState ?? null}
      {overflow > 0 && footerVerb ? (
        <button
          type="button"
          className="chair-lane-footer"
          onClick={() => onOpenInWindow(surfaceId)}
        >
          {overflow} more -- {footerVerb}
        </button>
      ) : null}
    </SurfaceSection>
  );
}

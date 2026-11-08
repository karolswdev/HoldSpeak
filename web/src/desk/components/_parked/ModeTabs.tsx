/** Thread mode uses the library's measured filter strip.
 * Choosing the bound recipe again removes the mode binding. */
import { useEffect, useState } from "react";
import { apiFetch } from "../../lib/api";
import type { ThreadMode } from "../threads";
import { FilterTokens } from "../surface/FilterTokens";

export interface ModeTabItem {
  id: string;
  name: string;
  avatar: string;
}

export interface ModeTabsProps {
  /** Currently active mode (resolved from the thread). */
  activeMode: ThreadMode | null;
  /** Callback when a tab is clicked. Empty string = unbind (no mode). */
  onSelect: (recipeId: string) => void;
  /** Whether tabs are disabled (e.g. while streaming). */
  disabled?: boolean;
}

/** Fetch mode recipes from GET /api/recipes?kind=mode. Cached per session. */
const SEED_ORDER = [
  "hs-seed-mode-desk",
  "hs-seed-mode-interview",
  "hs-seed-mode-chase",
  "hs-seed-mode-draft",
  "hs-seed-mode-plan",
];
let _modeCache: ModeTabItem[] | null = null;
let _modeFetching = false;

async function fetchModes(): Promise<ModeTabItem[]> {
  if (_modeCache) return _modeCache;
  if (_modeFetching) return [];
  _modeFetching = true;
  try {
    const data = await apiFetch<{ recipes?: Array<Record<string, unknown>> }>(
      "/api/recipes?kind=mode",
    );
    const recipes = data.recipes ?? [];
    const items = recipes
      .filter((r) => r.name && !r.deleted)
      .map((r) => ({
        id: String(r.id ?? ""),
        name: String(r.name ?? ""),
        avatar: String(r.avatar ?? "#6B7280"),
      }));
    // Canonical order: the four seeds first (Desk · Chase · Draft · Plan),
    // then custom modes by name -- never the route's updated_at order.
    const rank = (id: string): number => {
      const i = SEED_ORDER.indexOf(id);
      return i === -1 ? SEED_ORDER.length : i;
    };
    items.sort((a, b) => rank(a.id) - rank(b.id) || a.name.localeCompare(b.name));
    _modeCache = items;
    return _modeCache;
  } catch {
    return [];
  } finally {
    _modeFetching = false;
  }
}

/** Reset the mode cache (e.g. after creating a custom mode). */
export function resetModeCache(): void {
  _modeCache = null;
}

export function ModeTabs({ activeMode, onSelect, disabled }: ModeTabsProps) {
  const [modes, setModes] = useState<ModeTabItem[]>([]);
  useEffect(() => {
    void fetchModes().then(setModes);
  }, []);

  if (modes.length === 0) return null;

  return (
    <div className="thread-mode-tabs" data-testid="mode-tabs">
      <FilterTokens
        label="Thread mode"
        emptyLabel="Choose mode"
        options={modes.map((mode) => ({ value: mode.id, label: mode.name }))}
        value={activeMode?.id ?? ""}
        onChange={(next) => onSelect(next === activeMode?.id ? "" : next)}
        disabled={disabled}
      />
    </div>
  );
}

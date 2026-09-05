/** HS-153-01 -- Mode tabs in the composer HEAD.
 *
 * Renders: Desk . Chase . Draft . Plan . <custom modes>
 * Coloured dot from avatar, active tab marked (aria-pressed).
 * Arrow-key + Enter reachable, no horizontal overflow at 393
 * (tabs scroll inside overflow-x container). */
import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { apiFetch } from "../../lib/api";
import type { ThreadMode } from "../threads";

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
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    void fetchModes().then(setModes);
  }, []);

  const handleKey = useCallback(
    (e: KeyboardEvent<HTMLDivElement>) => {
      if (disabled) return;
      const btns = scrollRef.current?.querySelectorAll<HTMLButtonElement>(
        "[data-mode-tab]",
      );
      if (!btns || btns.length === 0) return;
      const arr = Array.from(btns);
      const idx = arr.findIndex((b) => b === document.activeElement);
      if (e.key === "ArrowRight" || e.key === "ArrowDown") {
        e.preventDefault();
        const next = idx < arr.length - 1 ? idx + 1 : 0;
        arr[next].focus();
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        const prev = idx > 0 ? idx - 1 : arr.length - 1;
        arr[prev].focus();
      } else if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        if (idx >= 0) arr[idx].click();
      }
    },
    [disabled],
  );

  if (modes.length === 0) return null;

  return (
    <div
      className="thread-mode-tabs"
      role="tablist"
      aria-label="Thread modes"
      data-testid="mode-tabs"
      onKeyDown={handleKey}
      ref={scrollRef}
    >
      {modes.map((m) => {
        const isActive = activeMode?.id === m.id;
        return (
          <button
            key={m.id}
            type="button"
            role="tab"
            data-mode-tab
            data-mode-id={m.id}
            aria-selected={isActive}
            aria-pressed={isActive}
            className={`thread-mode-tab${isActive ? " thread-mode-tab--active" : ""}`}
            tabIndex={isActive ? 0 : -1}
            disabled={disabled}
            onClick={() => onSelect(isActive ? "" : m.id)}
            data-testid={`mode-tab-${m.name.toLowerCase()}`}
          >
            <span
              className="thread-mode-dot"
              style={{ backgroundColor: m.avatar }}
            />
            <span className="thread-mode-label">{m.name}</span>
          </button>
        );
      })}
    </div>
  );
}

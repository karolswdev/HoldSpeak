/* Memory on the Desk (canvas section 2, option B "Where the work lives",
 * ratified 2026-10-05): the standing pages of one scope, where the work
 * lives.  The Room draws its project's four (What did we decide · What is
 * open and who owes it · Risks and disputes · What changed this week); the
 * Brief draws the desk's two (What I owe · What changed this week).
 *
 * One read: GET /api/memory/pages (no model call).  No page served: the
 * section is absent (the default, with no page engine assigned).  A read
 * that fails is absent too: the pages are context, never a failure of the
 * window that holds them.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";
import { openRef } from "./openObject";
import { StandingPage, SurfaceSection, countLabel, wireDate, type MemoryRefToken } from "./surface";
import { useMemoryChanges } from "./memoryChanges";

export interface StandingPageWire {
  slug: string;
  question: string;
  sentences: { text: string; refs: MemoryRefToken[] }[];
  built_at: string;
  stale: boolean;
  new_sources: number;
  model: string;
  boundary: string;
}

/** The boards' titles for the fixed page set (MEMORY-DESIGN.md §3.4). */
const TITLES: Record<string, string> = {
  "what-we-decided": "What did we decide",
  "what-is-open": "What is open and who owes it",
  "risks-and-disputes": "Risks and disputes",
  "what-changed-this-week": "What changed this week",
  "what-i-owe": "What I owe",
};

export function pageTitle(page: Pick<StandingPageWire, "slug" | "question">): string {
  return TITLES[page.slug] ?? page.question.replace(/\?$/, "");
}

const DAYS = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
const pad = (n: number) => String(n).padStart(2, "0");

/** `BUILT 09:12` today, `BUILT MON 08:02` this week, else `BUILT 09-28`. */
export function builtToken(builtAt: string, now: Date = new Date()): string {
  const d = wireDate(builtAt);
  if (!d) return "BUILT";
  const clock = `${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime();
  if (d.getTime() >= startOfToday) return `BUILT ${clock}`;
  if (startOfToday - d.getTime() < 6 * 86_400_000) return `BUILT ${DAYS[d.getDay()]} ${clock}`;
  return `BUILT ${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

const BOUNDARY: Record<string, string> = {
  local: "THIS DEVICE",
  same_device: "THIS DEVICE",
  private_network: "LAN",
  lan: "LAN",
  mesh: "MESH",
  cloud: "CLOUD",
};

/** `PAGES BY QWEN3.8-27B · LAN`: which engine wrote the pages, and where. */
export function modelToken(pages: StandingPageWire[]): string | null {
  const seen = [...new Set(pages.map((p) => {
    const model = (p.model || "").toUpperCase();
    const where = BOUNDARY[(p.boundary || "").toLowerCase()] ?? (p.boundary || "").toUpperCase();
    return [model, where].filter(Boolean).join(" · ");
  }).filter(Boolean))];
  return seen.length ? `PAGES BY ${seen.join(" / ")}` : null;
}

/** The scope key the cached pages belong to: `project:atlas` / `desk`. */
export function scopeKey(scope: "desk" | "project", projectId?: string | null): string {
  return scope === "project" ? `project:${projectId ?? ""}` : "desk";
}

/**
 * The served pages of one scope.  The cache is BOUND to its scope key: on a
 * scope change nothing of the old scope is drawn (the pages read empty until
 * the new scope's answer lands), and a late answer for another scope is
 * dropped (Astra, PR #877 P2: Atlas pages in Harbor's Room).  On a
 * `desk_changed` frame a sentence whose ref names a changed source is not
 * drawn until the re-read lands (`useMemoryChanges`).
 */
export function useStandingPages(scope: "desk" | "project", projectId?: string | null) {
  const key = scopeKey(scope, projectId);
  const [cache, setCache] = useState<{ key: string; pages: StandingPageWire[] }>({ key: "", pages: [] });
  const wanted = useRef(key);
  wanted.current = key;
  const load = useCallback(async () => {
    const asked = key;
    if (scope === "project" && !projectId) {
      setCache({ key: asked, pages: [] });
      return;
    }
    const params = scope === "project"
      ? new URLSearchParams({ project_id: String(projectId) })
      : new URLSearchParams({ scope: "desk" });
    const body = await apiFetch<{ pages?: StandingPageWire[] }>(`/api/memory/pages?${params}`);
    // An answer for a scope this face no longer shows is dropped.
    if (wanted.current !== asked) return;
    setCache({ key: asked, pages: Array.isArray(body?.pages) ? body.pages : [] });
  }, [key, scope, projectId]);
  useEffect(() => {
    // A failed first read draws nothing (never an error); the hold logic
    // needs the rejection, so only this call site swallows it.
    load().catch(() => {
      if (wanted.current === key) setCache({ key, pages: [] });
    });
  }, [load, key]);
  const held = useMemoryChanges(load);
  const pages = cache.key === key ? cache.pages : [];
  return pages
    .map((page) => ({
      ...page,
      sentences: (page.sentences ?? []).filter((s) => !held(s.refs.map((r) => r.ref))),
    }))
    .filter((page) => page.sentences.length);
}

export function StandingPagesSection({
  pages,
  onOpenRef = openRef,
  now,
}: {
  pages: StandingPageWire[];
  onOpenRef?: (ref: string) => void;
  now?: Date;
}) {
  if (!pages.length) return null;
  const by = modelToken(pages);
  return (
    <div data-testid="standing-pages">
      <SurfaceSection
        label={countLabel("STANDING PAGES", pages.length)}
        className="standing-pages-section"
        actions={by ? <span className="surface-token" data-testid="standing-pages-model">{by}</span> : undefined}
      >
        <div className="standing-pages-grid">
          {pages.map((page) => (
            <StandingPage
              key={page.slug}
              title={pageTitle(page)}
              sentences={page.sentences}
              built={builtToken(page.built_at, now)}
              stale={page.stale}
              newSources={page.new_sources}
              onOpenRef={onOpenRef}
            />
          ))}
        </div>
      </SurfaceSection>
    </div>
  );
}

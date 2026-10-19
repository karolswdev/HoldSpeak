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
import { StandingPage, SurfaceSection, wireDate, type MemoryRefToken } from "./surface";
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
  "what-they-owe-me": "What others owe me",
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

/** `Written by qwen3.8-27b · LAN`: which engine wrote the pages, and where.
 *  PHILO-17: no credit without an engine name (the word "PAGES" stood in
 *  for a missing name). */
export function modelToken(pages: StandingPageWire[]): string | null {
  const seen = [...new Set(pages.map((p) => {
    const model = (p.model || "").trim();
    if (!model) return "";
    const where = BOUNDARY[(p.boundary || "").toLowerCase()] ?? (p.boundary || "").toUpperCase();
    return [model, where].filter(Boolean).join(" · ");
  }).filter(Boolean))];
  return seen.length ? `Written by ${seen.join(" / ")}` : null;
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
  return useStandingPagesRead(scope, projectId).pages;
}

/** PHILO-17 (phonepass): the pages, and whether the first read for this
 *  scope has resolved (the Room waits for it). */
export function useStandingPagesRead(scope: "desk" | "project", projectId?: string | null) {
  const key = scopeKey(scope, projectId);
  const [cache, setCache] = useState<{ key: string; pages: StandingPageWire[] }>({ key: "", pages: [] });
  const wanted = useRef(key);
  wanted.current = key;
  const order = useRef(0);
  const load = useCallback(async (): Promise<boolean> => {
    const asked = key;
    if (scope === "project" && !projectId) {
      setCache({ key: asked, pages: [] });
      return true;
    }
    const mine = ++order.current;
    const params = scope === "project"
      ? new URLSearchParams({ project_id: String(projectId) })
      : new URLSearchParams({ scope: "desk" });
    const body = await apiFetch<{ pages?: StandingPageWire[] }>(`/api/memory/pages?${params}`);
    // An answer for a scope this face no longer shows, or one a newer read
    // of the same scope overtook, is dropped and releases no hold.
    if (wanted.current !== asked || mine !== order.current) return false;
    setCache({ key: asked, pages: Array.isArray(body?.pages) ? body.pages : [] });
    return true;
  }, [key, scope, projectId]);
  useEffect(() => {
    // A failed first read draws nothing (never an error); the hold logic
    // needs the rejection, so only this call site swallows it.
    load().catch(() => {
      if (wanted.current === key) setCache({ key, pages: [] });
    });
  }, [load, key]);
  const held = useMemoryChanges(load);
  const loaded = cache.key === key;
  const pages = loaded ? cache.pages : [];
  return {
    loaded,
    pages: pages
      .map((page) => ({
        ...page,
        sentences: (page.sentences ?? []).filter((s) => !held(s.refs.map((r) => r.ref))),
      }))
      .filter((page) => page.sentences.length),
  };
}

/* Betterment Q11 (Memory where he looks): a person's two pages, What I owe
 * her and What she owes me. They are the sentences of the desk's "What do I
 * owe?" and "What do others owe me?" that name the person (her full name or
 * her first name, as a word), so her window reads them with no Ask and no
 * People id is ever written beside a page. */
function names(displayName: string): string[] {
  const full = displayName.trim();
  const first = full.split(/\s+/, 1)[0] ?? "";
  return [...new Set([full, first].filter((n) => n.length >= 2))];
}

function mentions(text: string, who: string[]): boolean {
  return who.some((name) => new RegExp(`(^|[^\\p{L}])${name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}($|[^\\p{L}])`, "iu").test(text));
}

export function personPages(pages: StandingPageWire[], displayName: string): StandingPageWire[] {
  const who = names(displayName);
  const first = who[who.length - 1] ?? displayName;
  if (!who.length) return [];
  const pick = (slug: string, question: string): StandingPageWire[] => {
    const page = pages.find((p) => p.slug === slug);
    const sentences = (page?.sentences ?? []).filter((s) => mentions(s.text, who));
    return page && sentences.length ? [{ ...page, slug: `person:${slug}`, question, sentences }] : [];
  };
  return [...pick("what-i-owe", `What I owe ${first}`), ...pick("what-they-owe-me", `What ${first} owes me`)];
}

/** Betterment Q11: the Room leads with What is open, then What we decided. */
const ROOM_FIRST = ["what-is-open", "what-we-decided"];
export function roomPageOrder(pages: StandingPageWire[]): StandingPageWire[] {
  const rank = (slug: string) => {
    const at = ROOM_FIRST.indexOf(slug);
    return at < 0 ? ROOM_FIRST.length : at;
  };
  return [...pages].sort((a, b) => rank(a.slug) - rank(b.slug));
}

/** The person's two pages, first in her window (absent with none). */
export function PersonPages({ displayName, onOpenRef = openRef }: { displayName: string; onOpenRef?: (ref: string) => void }) {
  const pages = useStandingPages("desk");
  const mine = personPages(pages, displayName);
  if (!mine.length) return null;
  return <div data-testid="person-pages"><StandingPagesSection pages={mine} presentation="questions" onOpenRef={onOpenRef} /></div>;
}

export function StandingPagesSection({
  pages,
  onOpenRef = openRef,
  now,
  presentation = "grouped",
}: {
  pages: StandingPageWire[];
  onOpenRef?: (ref: string) => void;
  now?: Date;
  /** Brief leads with the named answers, without a second generic heading. */
  presentation?: "grouped" | "questions";
}) {
  if (!pages.length) return null;
  const by = modelToken(pages);
  return (
    <div data-testid="standing-pages" data-presentation={presentation}>
      <SurfaceSection
        label={presentation === "grouped" ? `Standing pages · ${pages.length}` : undefined}
        className="standing-pages-section"
        actions={presentation === "grouped" && by ? <span className="standing-pages-model" data-testid="standing-pages-model">{by}</span> : undefined}
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
        {presentation === "questions" && by ? <span className="standing-pages-model" data-testid="standing-pages-model">{by}</span> : null}
      </SurfaceSection>
    </div>
  );
}

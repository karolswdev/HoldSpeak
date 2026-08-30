// HS-111-07 - the ⌘K command deck (owner P0). The old shelf could not
// run ANYTHING on Enter and fed from its own parallel lists; the deck
// keeps a SELECTION INDEX (not DOM focus), Enter always runs the
// selected hit (the top hit by default), ranking is prefix(3) >
// recents(2) > substring(1), and rows are 26px mono ledger lines in
// sections VERBS / PROGRAMS / OBJECTS / SETTINGS / MEETINGS - fed from
// the ONE verb registry plus the same stores every face reads.
// Deferred riders (named, not built): Settings deep-pane search plugs
// in as more SETTINGS rows once settingsPrefs exports its module
// index; meeting CONTENT search plugs in as more MEETINGS rows via the
// History program's existing query. Both ride this same ranking.
import "./chrome-menus.css";
import { useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { openSurface } from "../shell";
import { SYSTEM } from "../systemSprites";
import { qualifiedRef } from "../api";
import { createThread } from "../threads";
import {
  contextualCapabilityActions,
  contextualCoderSessions,
  contextualIntegrationActions,
} from "../contextual";
import { useDesk } from "../store";
import { usePalette } from "../chromeState";
import { StringGadget } from "../surface/gadgets";
import { allObjects } from "../world";
import { DESK_TOOLS, KIND_LABEL } from "../tools";
import { VERBS, verbLabel, type VerbContext } from "../verbRegistry";
import { PREF_MODULES } from "../../pages/cores/settingsPrefs";
import { useLaunchers } from "./DeskWindow";

// Re-exported so existing imports keep one source (the data moved to
// desk/tools.ts so the registry never imports a component).
export { DESK_TOOLS, KIND_LABEL };

const SECTIONS = [
  "VERBS",
  "PROGRAMS",
  "OBJECTS",
  "SETTINGS",
  "MEETINGS",
] as const;
type Section = (typeof SECTIONS)[number];

interface DeckRow {
  id: string;
  section: Section;
  glyph: string;
  label: string;
  /** The mono kind token on the right of the label. */
  kind: string;
  keycap?: string;
  /** A ghosted verb stays visible with its reason and cannot run. */
  ghost?: string | null;
  /** Extra match terms beyond the label. */
  terms?: string;
  run(): void;
}

/* ── recents (localStorage, last 20 run ids) ── */
const RECENTS_KEY = "hs.desk.palette-recents";

function readRecents(): string[] {
  try {
    const raw = JSON.parse(localStorage.getItem(RECENTS_KEY) || "[]");
    return Array.isArray(raw) ? raw.filter((x) => typeof x === "string") : [];
  } catch {
    return [];
  }
}

function recordRecent(id: string): void {
  const next = [id, ...readRecents().filter((x) => x !== id)].slice(0, 20);
  try {
    localStorage.setItem(RECENTS_KEY, JSON.stringify(next));
  } catch {
    /* storage full or denied: recents just stay cold */
  }
}

export function fuzzyScore(query: string, target: string): number {
  const q = query.toLowerCase();
  const t = target.toLowerCase();
  if (t === q) return 100;
  if (t.startsWith(q)) return 80;
  const words = t.split(/[\s\-_]+/);
  if (words.some((word) => word.startsWith(q))) return 60;
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++;
  }
  if (qi === q.length) return 30;
  if (t.includes(q)) return 20;
  return 0;
}

/** Fuzzy relevance with a recency boost; 0 = no match. */
export function rankRow(
  row: { label: string; terms?: string },
  query: string,
  recent: boolean,
  recentBoostsEmpty = false,
): number {
  if (!query) return recent && recentBoostsEmpty ? 2 : 1;
  const score = Math.max(
    fuzzyScore(query, row.label),
    fuzzyScore(query, row.terms ?? ""),
  );
  return score ? score + (recent ? 10 : 0) : 0;
}

export function DeskToolShelf() {
  const open = usePalette((s) => s.open);
  const [query, setQuery] = useState("");
  const [sel, setSel] = useState(0);
  const rootRef = useRef<HTMLElement | null>(null);
  const launchRef = useRef<HTMLButtonElement | null>(null);
  const searchRef = useRef<HTMLInputElement | null>(null);
  const items = useDesk((state) => state.items);
  const projects = useDesk((state) => state.projects);
  const targets = useDesk((state) => state.inferenceTargets);
  const models = useDesk((state) => state.models);
  const setup = useDesk((state) => state.setup);
  const selectedIds = useDesk((state) => state.selectedIds);
  const openPullout = useDesk((state) => state.openPullout);
  const refresh = useDesk((state) => state.refresh);
  const openToolInspector = useDesk((state) => state.openToolInspector);
  const diveInto = useDesk((state) => state.diveInto);
  const integrations = setup?.trust?.destinations ?? [];
  const launchers = useLaunchers();

  useEffect(() => {
    // ⌘K itself lives in desk/keymap.ts (the one binder); the deck
    // keeps only its own Escape ladder: query first, then the panel.
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      event.preventDefault();
      if (searchRef.current?.value) setQuery("");
      else {
        usePalette.getState().setOpen(false);
        launchRef.current?.focus();
      }
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [open]);

  useEffect(() => {
    if (open) searchRef.current?.focus();
    setQuery("");
    setSel(0);
  }, [open]);

  // The deck's open state is shared chrome state (the keymap toggles
  // it); an unmounting shelf never leaves it stranded open.
  useEffect(() => () => usePalette.getState().setOpen(false), []);

  useEffect(() => setSel(0), [query]);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Node;
      if (
        !rootRef.current?.contains(target) &&
        !launchRef.current?.contains(target)
      ) {
        usePalette.getState().setOpen(false);
      }
    };
    document.addEventListener("pointerdown", onPointerDown);
    return () => document.removeEventListener("pointerdown", onPointerDown);
  }, [open]);

  const normalized = query.trim().toLocaleLowerCase();
  const recents = useMemo(() => readRecents(), [open]);

  const close = () => {
    usePalette.getState().setOpen(false);
    setQuery("");
  };

  const ctx: VerbContext = {
    selectedRef: selectedIds.length === 1 ? selectedIds[0] : null,
  };

  const rows: DeckRow[] = useMemo(() => {
    const out: DeckRow[] = [];
    const push = (row: DeckRow) => out.push(row);

    // ── VERBS: the registry + the contextual actions for a selection ──
    for (const action of contextualCapabilityActions(items, selectedIds))
      push({
        id: `ctx.cap:${action.id}`,
        section: "VERBS",
        glyph: "◇",
        label: action.label,
        kind: "AGENT",
        run: () => openPullout(qualifiedRef(action.kind, action.id)),
      });
    for (const action of contextualIntegrationActions(
      integrations,
      items,
      selectedIds,
    ))
      push({
        id: `ctx.int:${action.id}`,
        section: "VERBS",
        glyph: "↗",
        label: action.label,
        kind: "SEND",
        run: () => openToolInspector("integration", action.id),
      });
    for (const action of contextualCoderSessions(items, selectedIds))
      push({
        id: `ctx.coder:${action.id}`,
        section: "VERBS",
        glyph: "◉",
        label: action.label,
        kind: "CODER",
        run: () => openPullout(qualifiedRef("coder", action.id)),
      });
    for (const v of VERBS) {
      if (v.palette === false || v.scope === "go") continue;
      const label = verbLabel(v, ctx);
      const ghost = v.ghost(ctx);
      // A cold deck begins with the Desk's creation verbs; other verbs
      // appear after use. A query still reaches every verb (ghosted ones
      // say why).
      if (!normalized && v.group !== "new" && !recents.includes(v.id)) continue;
      push({
        id: v.id,
        section: "VERBS",
        glyph: "▸",
        label,
        kind: "VERB",
        keycap: v.key,
        ghost,
        terms: (v.keywords ?? []).join(" "),
        run: () => v.run(ctx),
      });
    }

    // ── PROGRAMS: the go.* registry face + open drawers ──
    for (const v of VERBS) {
      if (v.scope !== "go") continue;
      const tool = DESK_TOOLS.find((t) => `go.${t.action}` === v.id);
      push({
        id: v.id,
        section: "PROGRAMS",
        glyph: tool?.glyph ?? "▸",
        label: verbLabel(v, ctx),
        kind: "PROGRAM",
        keycap: v.key,
        terms: tool?.description.toLocaleLowerCase(),
        run: () => v.run(ctx),
      });
    }
    for (const l of launchers) {
      if (l.id === "attention") continue;
      push({
        id: `drawer:${l.id}`,
        section: "PROGRAMS",
        glyph: l.glyph,
        label: l.badge ? `${l.label} · ${l.badge} waiting` : l.label,
        kind: "DRAWER",
        run: () => l.activate(),
      });
    }

    // ── OBJECTS: zones + desk items (query) + projects ──
    if (normalized) {
      for (const zone of items.directory ?? [])
        push({
          id: `zone:${zone.id}`,
          section: "OBJECTS",
          glyph: "□",
          label: String(zone.name ?? "Zone"),
          kind: "ZONE",
          run: () => diveInto(String(zone.id)),
        });
      for (const item of allObjects(items)) {
        const kind = (KIND_LABEL[item.kind] ?? item.kind).toUpperCase();
        push({
          id: `${item.kind}:${item.id}`,
          section: item.kind === "meeting" ? "MEETINGS" : "OBJECTS",
          glyph: item.kind === "meeting" ? "▣" : "○",
          label: item.title,
          kind,
          terms: kind.toLocaleLowerCase(),
          run: () => openPullout(qualifiedRef(item.kind, item.id)),
        });
      }
    }
    for (const project of projects)
      push({
        id: `project:${project.id}`,
        section: "OBJECTS",
        glyph: "▤",
        label: project.name,
        kind: "PROJECT",
        terms: `project ${project.description}`.toLocaleLowerCase(),
        run: () => openSurface("open-project-memory", `project:${project.id}`),
      });

    // ── SETTINGS: preference modules, integrations, runtime targets, models ──
    for (const module of PREF_MODULES)
      push({
        id: `settings:${module.id}`,
        section: "SETTINGS",
        glyph: "⚙",
        label: module.label,
        kind: "SETTINGS",
        terms: `${module.id} ${module.keys.join(" ")}`,
        run: () => openSurface("configure-settings", module.id),
      });
    for (const integration of integrations) {
      if (!normalized && !integration.enabled) continue;
      push({
        id: `integration:${integration.id}`,
        section: "SETTINGS",
        glyph: "↗",
        label: integration.name,
        kind: integration.enabled ? "INTEGRATION" : "NOT CONFIGURED",
        terms:
          `integration ${integration.destination} ${integration.operation}`.toLocaleLowerCase(),
        run: () => openToolInspector("integration", integration.id),
      });
    }
    for (const target of targets)
      push({
        id: `target:${target.id}`,
        section: "SETTINGS",
        glyph: "▣",
        label: target.name,
        kind: target.readiness.available ? "RUNS ON" : "UNAVAILABLE",
        terms:
          `${target.kind} ${target.boundary} ${target.model}`.toLocaleLowerCase(),
        run: () => openToolInspector("target", target.id),
      });
    for (const model of models)
      push({
        id: `model:${model.name}`,
        section: "SETTINGS",
        glyph: "◈",
        label: model.name,
        kind: "MODEL",
        terms: "model",
        run: () => void createThread({ title: model.name, profile_override: model.name }).then((t) => { openPullout(`thread:${t.id}`); void refresh(); }),
      });

    // ── rank, cut, and settle into section bands ──
    const ranked = out
      .map((row, i) => ({
        row,
        i,
        score: rankRow(row, normalized, recents.includes(row.id), true),
      }))
      .filter((r) => r.score > 0);
    const sectionRank = (s: Section) => SECTIONS.indexOf(s);
    ranked.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      const sec = sectionRank(a.row.section) - sectionRank(b.row.section);
      if (sec !== 0) return sec;
      return a.i - b.i;
    });
    // Per-section cut: a query keeps the deck dense; the cold deck
    // shows every PROGRAM (they are the launcher truth) and a short
    // head of everything else.
    const cap = (s: Section) =>
      normalized
        ? s === "OBJECTS"
          ? 5
          : 10
        : s === "PROGRAMS"
          ? Number.POSITIVE_INFINITY
          : 6;
    const byCount = new Map<Section, number>();
    return ranked
      .filter(({ row }) => {
        const n = byCount.get(row.section) ?? 0;
        if (n >= cap(row.section)) return false;
        byCount.set(row.section, n + 1);
        return true;
      })
      .map(({ row }) => row);
  }, [
    ctx.selectedRef,
    diveInto,
    integrations,
    items,
    launchers,
    models,
    normalized,
    openPullout,
    refresh,
    openToolInspector,
    projects,
    recents,
    selectedIds,
    targets,
  ]);

  // The runnable list the selection index walks (ghosts stay visible
  // but are never selected, never run).
  const runnable = rows.filter((r) => !r.ghost);
  const selected = runnable.length
    ? runnable[Math.min(sel, runnable.length - 1)]
    : null;
  const activeId = selected ? `desk-palette-option-${selected.id}` : undefined;

  const runRow = (row: DeckRow) => {
    if (row.ghost) return;
    recordRecent(row.id);
    close();
    row.run();
  };

  const onDeckKeyDown = (event: React.KeyboardEvent<HTMLElement>) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      if (!runnable.length) return;
      setSel((now) => {
        const at = Math.min(now, runnable.length - 1);
        return event.key === "ArrowDown"
          ? Math.min(at + 1, runnable.length - 1)
          : Math.max(at - 1, 0);
      });
    } else if (event.key === "Enter") {
      // Enter ALWAYS runs the selected hit - the top hit by default.
      event.preventDefault();
      if (selected) runRow(selected);
    }
  };

  let lastSection: Section | null = null;

  return (
    <>
      <button
        ref={launchRef}
        type="button"
        className="desk-chip desk-tools-launch"
        aria-expanded={open}
        aria-controls="desk-tool-shelf"
        aria-keyshortcuts="Control+K Meta+K"
        onClick={() => usePalette.getState().toggle()}
      >
        <img
          src={SYSTEM.menuSearch}
          alt=""
          width={16}
          height={16}
          className="desk-chrome-sprite"
          draggable={false}
        />{" "}
        Search <kbd>⌘K</kbd>
      </button>
      {/* Round 9 - the deck PORTALS to the desk root: rendered inside
          the chrome bar it inherited the bar's z-30 stacking context and
          every desk window (z 42+) covered the ⌘K results - a palette
          must sit above the window band, always. */}
      {open
        ? createPortal(
            <aside
              ref={rootRef}
              id="desk-tool-shelf"
              className="desk-tool-shelf"
              role="region"
              aria-label="Tools and Desk search"
              onKeyDown={onDeckKeyDown}
            >
              <label className="desk-tool-search">
                <span className="sr-only">Search tools and Desk items</span>
                <StringGadget
                  inputRef={searchRef}
                  label="Search tools and Desk items"
                  value={query}
                  placeholder="Search tools and Desk items"
                  onChange={setQuery}
                  inputProps={{
                    role: "combobox",
                    "aria-expanded": open,
                    "aria-controls": "desk-palette-listbox",
                    "aria-activedescendant": activeId,
                  }}
                />
              </label>
              {rows.length ? (
                <ul
                  id="desk-palette-listbox"
                  className="desk-deck-list"
                  role="listbox"
                >
                  {rows.map((row) => {
                    const band =
                      row.section !== lastSection ? row.section : null;
                    lastSection = row.section;
                    const isSel = selected?.id === row.id;
                    return (
                      <li key={row.id}>
                        {band ? (
                          <span className="desk-deck-band">{band}</span>
                        ) : null}
                        <button
                          id={`desk-palette-option-${row.id}`}
                          type="button"
                          role="option"
                          aria-selected={isSel}
                          className={
                            "desk-deck-row" +
                            (isSel ? " is-selected" : "") +
                            (row.ghost ? " is-ghost" : "")
                          }
                          aria-disabled={row.ghost ? true : undefined}
                          aria-current={isSel || undefined}
                          onClick={() => runRow(row)}
                          onPointerEnter={() => {
                            if (row.ghost) return;
                            const at = runnable.findIndex(
                              (r) => r.id === row.id,
                            );
                            if (at >= 0) setSel(at);
                          }}
                        >
                          <span className="desk-deck-glyph" aria-hidden="true">
                            {row.glyph}
                          </span>
                          <span className="desk-deck-label">
                            {row.label}
                            {row.ghost ? (
                              <small className="quiet"> · {row.ghost}</small>
                            ) : null}
                          </span>
                          <span className="desk-deck-kind">{row.kind}</span>
                          {row.keycap ? <kbd>{row.keycap}</kbd> : null}
                        </button>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <p className="desk-tool-empty">
                  No matching tools or Desk items.
                </p>
              )}
            </aside>,
            launchRef.current?.closest(".desk-next") ??
              document.getElementById("desk-next") ??
              document.body,
          )
        : null}
    </>
  );
}

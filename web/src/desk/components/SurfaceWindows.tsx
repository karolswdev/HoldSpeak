// HS-95-04 — page cores hosted as desk windows. One table row per
// re-homed surface: the shell key the chrome/shelf dispatches, the window
// identity, and the (lazy) core. Stories HS-95-05..08 grow this table
// until no surface lives outside the desk (Constitution, Article I).
import {
  Suspense,
  lazy,
  useEffect,
  useState,
  type ComponentType,
  type LazyExoticComponent,
  type ReactNode,
} from "react";
import { create } from "zustand";
import { registerSurface } from "../shell";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { DeskWindowFrame } from "./DeskWindow";
import { WingSlotContext } from "../surface/wings";
import type { CoreProps } from "../../pages/cores/ActivityCore";

interface SurfaceRow {
  key: string;
  id: string;
  title: string;
  glyph: string;
  eyebrow: string;
  minW?: number;
  /** Open maximized (full stage) — the canvas-sized surfaces want it. */
  maximized?: boolean;
  Core: LazyExoticComponent<ComponentType<CoreProps & { scope?: string }>>;
}

const SURFACES: SurfaceRow[] = [
  {
    key: "dictate",
    id: "surface-dictation",
    title: "Speak",
    glyph: "⌁",
    eyebrow: "Daily cockpit",
    minW: 560,
    Core: lazy(() =>
      import("../../pages/cores/DictationCore").then((m) => ({
        default: m.DictationCore,
      })),
    ),
  },
  {
    key: "review-meetings",
    id: "surface-meetings",
    title: "Meetings",
    glyph: "▣",
    eyebrow: "Meeting memory",
    minW: 640,
    Core: lazy(() =>
      import("../../pages/cores/HistoryCore").then((m) => ({
        default: m.HistoryCore,
      })),
    ),
  },
  {
    key: "record-live",
    id: "surface-live",
    title: "Live meeting",
    glyph: "●",
    eyebrow: "Meeting room",
    minW: 560,
    Core: lazy(() =>
      import("../../pages/cores/LiveCore").then((m) => ({
        default: m.LiveCore,
      })),
    ),
  },
  {
    key: "configure-settings",
    id: "surface-settings",
    title: "Settings",
    glyph: "⚙",
    eyebrow: "Configuration",
    minW: 560,
    Core: lazy(() =>
      import("../../pages/cores/SettingsCore").then((m) => ({
        default: m.SettingsCore,
      })),
    ),
  },
  {
    key: "configure-runs-on",
    id: "surface-profiles",
    title: "Runs on",
    glyph: "⇄",
    eyebrow: "Runtime",
    minW: 520,
    Core: lazy(() =>
      import("../../pages/cores/ProfilesCore").then((m) => ({
        default: m.ProfilesCore,
      })),
    ),
  },
  {
    key: "configure-cadence",
    id: "surface-cadence",
    title: "Cadence",
    glyph: "∿",
    eyebrow: "Follow-through",
    minW: 520,
    Core: lazy(() =>
      import("../../pages/cores/CadenceCore").then((m) => ({
        default: m.CadenceCore,
      })),
    ),
  },
  {
    key: "configure-setup",
    id: "surface-setup",
    title: "Setup",
    glyph: "✓",
    eyebrow: "Arrival",
    minW: 520,
    Core: lazy(() =>
      import("../../pages/cores/SetupCore").then((m) => ({
        default: m.SetupCore,
      })),
    ),
  },
  {
    key: "build-workflow",
    id: "surface-workbench",
    title: "Workbench",
    glyph: "⧉",
    eyebrow: "Build",
    minW: 720,
    maximized: true,
    Core: lazy(() =>
      import("../../pages/cores/WorkbenchCore").then((m) => ({
        default: m.WorkbenchCore,
      })),
    ),
  },
  {
    key: "inspect-personas-and-coders",
    id: "surface-companion",
    title: "Agents",
    glyph: "🤝",
    eyebrow: "Companion",
    minW: 560,
    Core: lazy(() =>
      import("../../pages/cores/CompanionCore").then((m) => ({
        default: m.CompanionCore,
      })),
    ),
  },
  {
    key: "design-components",
    id: "surface-components",
    title: "Components",
    glyph: "▦",
    eyebrow: "Signal React",
    minW: 640,
    Core: lazy(() =>
      import("../../pages/cores/ComponentsCore").then((m) => ({
        default: m.ComponentsCore,
      })),
    ),
  },
  {
    key: "inspect-activity",
    id: "surface-activity",
    title: "Activity",
    glyph: "⊙",
    eyebrow: "This-device context",
    minW: 480,
    Core: lazy(() =>
      import("../../pages/cores/ActivityCore").then((m) => ({
        default: m.ActivityCore,
      })),
    ),
  },
  {
    key: "open-project-memory",
    id: "surface-project-memory",
    title: "Project memory",
    glyph: "▤",
    eyebrow: "Long memory",
    minW: 640,
    Core: lazy(() =>
      import("../../pages/cores/ProjectMemoryCore").then((m) => ({
        default: m.ProjectMemoryCore,
      })),
    ),
  },
  {
    key: "inspect-processes",
    id: "surface-processes",
    title: "Processes",
    glyph: "∷",
    eyebrow: "Kernel",
    minW: 520,
    Core: lazy(() =>
      import("../../pages/cores/ProcessCore").then((m) => ({
        default: m.ProcessCore,
      })),
    ),
  },
  {
    key: "configure-commands",
    id: "surface-commands",
    title: "Commands",
    glyph: "⌘",
    eyebrow: "Voice commands",
    minW: 460,
    Core: lazy(() =>
      import("../../pages/cores/CommandsCore").then((m) => ({
        default: m.CommandsCore,
      })),
    ),
  },
];

/** HS-103-01 — which surface windows were open survives a reload, the
 * same manual-localStorage shape `store.ts` already uses for positions
 * and panel rects (own key: this store is the sole writer). */
const OPEN_KEY = "hs.desk.open-windows";

function loadOpenWindows(): Record<string, string | null> {
  try {
    return JSON.parse(localStorage.getItem(OPEN_KEY) || "{}") || {};
  } catch {
    return {};
  }
}

function saveOpenWindows(open: Record<string, string | null>) {
  try {
    localStorage.setItem(OPEN_KEY, JSON.stringify(open));
  } catch {
    /* storage may be unavailable; the open set just won't persist */
  }
}

interface SurfaceState {
  open: Record<string, string | null>;
  openSurfaceWindow(key: string, scope?: string): void;
  closeSurfaceWindow(key: string): void;
}

export const useSurfaceWindows = create<SurfaceState>((set, get) => ({
  open: loadOpenWindows(),
  openSurfaceWindow(key, scope) {
    const open = { ...get().open, [key]: scope ?? null };
    set({ open });
    saveOpenWindows(open);
  },
  closeSurfaceWindow(key) {
    const { [key]: _dropped, ...rest } = get().open;
    set({ open: rest });
    saveOpenWindows(rest);
  },
}));

/** Alias keys open an existing window with a default scope (e.g. the
 * shelf's Integrations entry is the Settings window scoped to
 * integrations). */
const SURFACE_ALIASES: Record<string, { target: string; scope?: string }> = {
  "configure-integrations": {
    target: "configure-settings",
    scope: "integration:destinations",
  },
  "configure-integration": { target: "configure-settings" },
  // HS-100-10 — the Runtime guide is Settings' Guide wing; old
  // dispatches and deep links keep landing.
  "read-runtime-docs": { target: "configure-settings", scope: "guide" },
};

export function SurfaceWindows() {
  const open = useSurfaceWindows((s) => s.open);
  const items = useDesk((s) => s.items);

  useEffect(() => {
    const offs = SURFACES.map((row) =>
      registerSurface(row.key, (scope) => {
        useSurfaceWindows.getState().openSurfaceWindow(row.key, scope);
        if (row.maximized && !useDesk.getState().panelMax.includes(row.id))
          useDesk.getState().toggleMaximizePanel(row.id);
      }),
    );
    const aliasOffs = Object.entries(SURFACE_ALIASES).map(([key, alias]) =>
      registerSurface(key, (scope) =>
        useSurfaceWindows
          .getState()
          .openSurfaceWindow(alias.target, scope ?? alias.scope),
      ),
    );
    return () => {
      offs.forEach((off) => off());
      aliasOffs.forEach((off) => off());
    };
  }, []);

  return (
    <>
      {SURFACES.map((row) => {
        const isOpen = row.key in open;
        if (!isOpen) return null;
        return (
          <SurfaceWindowHost
            key={row.id}
            row={row}
            scope={open[row.key] ?? undefined}
            items={items}
          />
        );
      })}
    </>
  );
}

/** One hosted core: owns the head's wing slot so the core can publish
 * its faces into the window chrome (HS-100-07, the posture rule). */
function SurfaceWindowHost({
  row,
  scope,
  items,
}: {
  row: SurfaceRow;
  scope: string | undefined;
  items: ReturnType<typeof useDesk.getState>["items"];
}) {
  const [wings, setWings] = useState<ReactNode>(null);
  return (
    <DeskWindowFrame
      id={row.id}
      glyph={row.glyph}
      eyebrow={row.eyebrow}
      title={row.title}
      minW={row.minW}
      wings={wings}
      open
      unmountOnMinimize
      onClose={() => useSurfaceWindows.getState().closeSurfaceWindow(row.key)}
      className="desk-surface-window"
    >
      <div className="desk-surface-body">
        <WingSlotContext.Provider value={setWings}>
          <Suspense fallback={<p className="quiet">…</p>}>
            <row.Core
              scope={scope}
              scopeLabel={
                scope
                  ? (objectByRef(items, scope)?.title ?? undefined)
                  : undefined
              }
            />
          </Suspense>
        </WingSlotContext.Provider>
      </div>
    </DeskWindowFrame>
  );
}

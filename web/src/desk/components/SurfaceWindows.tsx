// HS-95-04 — page cores hosted as desk windows. One table row per
// re-homed surface: the shell key the chrome/shelf dispatches, the window
// identity, and the (lazy) core. Stories HS-95-05..08 grow this table
// until no surface lives outside the desk (Constitution, Article I).
import {
  Suspense,
  lazy,
  useEffect,
  type ComponentType,
  type LazyExoticComponent,
} from "react";
import { create } from "zustand";
import { registerSurface } from "../shell";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { DeskWindowFrame } from "./DeskWindow";
import type { CoreProps } from "../../pages/cores/ActivityCore";

interface SurfaceRow {
  key: string;
  id: string;
  title: string;
  glyph: string;
  eyebrow: string;
  minW?: number;
  Core: LazyExoticComponent<ComponentType<CoreProps & { scope?: string }>>;
}

const SURFACES: SurfaceRow[] = [
  {
    key: "dictate",
    id: "surface-dictation",
    title: "Dictation",
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

interface SurfaceState {
  open: Record<string, string | undefined | null>;
  openSurfaceWindow(key: string, scope?: string): void;
  closeSurfaceWindow(key: string): void;
}

export const useSurfaceWindows = create<SurfaceState>((set, get) => ({
  open: {},
  openSurfaceWindow(key, scope) {
    set({ open: { ...get().open, [key]: scope ?? null } });
  },
  closeSurfaceWindow(key) {
    const { [key]: _dropped, ...rest } = get().open;
    set({ open: rest });
  },
}));

export function SurfaceWindows() {
  const open = useSurfaceWindows((s) => s.open);
  const items = useDesk((s) => s.items);

  useEffect(() => {
    const offs = SURFACES.map((row) =>
      registerSurface(row.key, (scope) =>
        useSurfaceWindows.getState().openSurfaceWindow(row.key, scope),
      ),
    );
    return () => offs.forEach((off) => off());
  }, []);

  return (
    <>
      {SURFACES.map((row) => {
        const isOpen = row.key in open;
        if (!isOpen) return null;
        return (
          <DeskWindowFrame
            key={row.id}
            id={row.id}
            glyph={row.glyph}
            eyebrow={row.eyebrow}
            title={row.title}
            minW={row.minW}
            open
            unmountOnMinimize
            onClose={() =>
              useSurfaceWindows.getState().closeSurfaceWindow(row.key)
            }
            className="desk-surface-window"
          >
            <div className="desk-surface-body">
              <Suspense fallback={<p className="quiet">…</p>}>
                <row.Core
                  scope={open[row.key] ?? undefined}
                  scopeLabel={
                    open[row.key]
                      ? (objectByRef(items, open[row.key]!)?.title ?? undefined)
                      : undefined
                  }
                />
              </Suspense>
            </div>
          </DeskWindowFrame>
        );
      })}
    </>
  );
}

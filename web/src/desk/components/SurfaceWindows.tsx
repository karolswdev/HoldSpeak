// HS-95-04 — page cores hosted as desk windows. One table row per
// re-homed surface: the shell key the chrome/shelf dispatches, the window
// identity, and the (lazy) core. Stories HS-95-05..08 grow this table
// until no surface lives outside the desk (Constitution, Article I).
import {
  Suspense,
  lazy,
  useCallback,
  useEffect,
  useState,
  type ComponentType,
  type LazyExoticComponent,
  type ReactNode,
} from "react";
import {
  DESK_APPLICATION_ALIASES,
  composeApplicationScope,
  SURFACE_APPLICATIONS,
} from "../applications";
import {
  consumeStagedSurfaceOpen,
  openSurfaceWhenReady,
  registerSurface,
} from "../shell";
import { useDesk } from "../store";
import { objectByRef } from "../world";
import { DeskWindowFrame } from "./DeskWindow";
import { FootSlotContext } from "../surface/foot";
import { TitleSlotContext } from "../surface/title";
import { BackSlotContext, type WindowBack } from "../surface/back";
import { windowName } from "../windowName";
import { WingSlotContext } from "../surface/wings";
import type { CoreProps } from "../../pages/cores/core-types";
import { SurfaceState } from "../surface/Surface";
import { ApplicationBoundary } from "./ApplicationBoundary";
import { useSurfaceScrollPlace } from "../hooks/useSurfaceScrollPlace";

export interface SurfaceRow {
  key: string;
  id: string;
  title: string;
  glyph: string;
  eyebrow: string;
  minW?: number;
  minH?: number;
  /** Preferred first-open width; persisted owner arrangements still win. */
  defaultW?: number;
  /** Preferred first-open height; persisted owner arrangements still win. */
  defaultH?: number;
  /** Open maximized (full stage) — the canvas-sized surfaces want it. */
  maximized?: boolean;
  parked?: string;
  Core: LazyExoticComponent<ComponentType<CoreProps & { scope?: string }>>;
}

const SURFACES: SurfaceRow[] = SURFACE_APPLICATIONS
  .filter((application) => !application.parked)
  .map((application) => ({
  key: application.action,
  id: application.windowId,
  title: application.label,
  glyph: application.glyph,
  eyebrow: application.surface.eyebrow,
  minW: application.surface.minW,
  minH: application.surface.minH ?? 220,
  defaultW: application.surface.defaultW,
  defaultH: application.surface.defaultH,
  maximized: application.surface.maximized,
  parked: application.parked,
  Core: lazy(application.surface.load),
  }));

/** Alias keys open an existing window with a default scope (e.g. the
 * shelf's Integrations entry is the Settings window scoped to
 * integrations). */
/* HS-202-02 (Astra's counsel finding 1 on PR #595): the cold desk's
   recovery set. `Check the microphone` on the first-run card calls
   `configure-setup`; with only `project-setup` admitted here the
   dispatcher found no surface and fell back to `/`, so the one recovery
   the card offers did nothing. Both Setup doors are registered during
   first use, and nothing else is. */
/* PHILO-17 (Astra r1 on #1085): First words' recovery doors are Setup
   (the microphone) and Engines (the speech model's row): both are admitted
   here, so neither falls back to a route recovery never consumes (the
   /models fallback reloaded the page and lost the card). The canonical
   Engines surface is `configure-runs-on`; `open-concierge` remains its
   retired compatibility alias. */
const FIRST_VALUE_RECOVERY_KEYS = new Set(["project-setup", "configure-setup", "configure-settings", "configure-runs-on"]);
const FIRST_VALUE_RECOVERY_SURFACES = SURFACES.filter((row) =>
  FIRST_VALUE_RECOVERY_KEYS.has(row.key),
);

export function SurfaceWindows({
  firstValueRecoveryOnly = false,
  keepDeskWindows = false,
}: {
  /** First value registers only its explicit Setup recovery and starts with
      no persisted Desk windows competing on glass. */
  firstValueRecoveryOnly?: boolean;
  /** PHILO-17: first run opened again. Recovery-only, but his desk windows
      are NOT cleared: the ones open now wait off glass and come back when he
      leaves first run; a recovery door he presses here opens on glass. */
  keepDeskWindows?: boolean;
} = {}) {
  const windowsById = useDesk((s) => s.windowsById);
  const [waiting, setWaiting] = useState<ReadonlySet<string>>(() =>
    keepDeskWindows ? new Set(Object.keys(useDesk.getState().windowsById)) : new Set(),
  );
  const items = useDesk((s) => s.items);
  const [ready, setReady] = useState(!firstValueRecoveryOnly);
  // `ready` is first-value paint recovery. This separate fact names the
  // completed normal-surface registration that the demoted-route dispatcher
  // actually depends on; Setup-only recovery must never claim it.
  const [registryState, setRegistryState] = useState<"pending" | "registered">("pending");
  const rows = firstValueRecoveryOnly
    ? FIRST_VALUE_RECOVERY_SURFACES
    : SURFACES;

  useEffect(() => {
    // The persisted open set belongs to the normal Desk. Hide it before this
    // recovery-only mount becomes paintable; FirstWords can still open Setup
    // after the registry below is ready.
    if (firstValueRecoveryOnly && !keepDeskWindows) useDesk.getState().clearSurfaceWindows();
    setReady(true);
  }, [firstValueRecoveryOnly]);

  useEffect(() => {
    // One reveal-and-open for a row and its aliases (Astra r2 on #1085): a
    // window that waits off glass (first run opened again) comes back on
    // glass when any of its keys is pressed.
    const reveal = (row: SurfaceRow, scope?: string) => {
      setWaiting((now) => {
        if (!now.has(row.id)) return now;
        const next = new Set(now);
        next.delete(row.id);
        return next;
      });
      useDesk.getState().openSurfaceWindow(row.key, scope);
    };
    const offs = rows.map((row) => registerSurface(row.key, (scope) => reveal(row, scope)));
    const aliasOffs = Object.entries(DESK_APPLICATION_ALIASES)
      .map(([key, alias]) => [key, alias, rows.find((row) => row.key === alias.target)] as const)
      .filter(([, , row]) => Boolean(row))
      .map(([key, alias, row]) => registerSurface(key, (scope) =>
        reveal(row!, composeApplicationScope(alias.scope, scope))));
    // This runs only after every normal row and applicable alias is present in
    // the dispatcher. Consume a demoted-route intent only here, then publish
    // the fact the /meetings proof awaits; first-value recovery has no normal
    // registry and must not claim or consume either.
    if (!firstValueRecoveryOnly) {
      const staged = consumeStagedSurfaceOpen();
      if (staged) openSurfaceWhenReady(staged.key, staged.scope);
      setRegistryState("registered");
    }
    return () => {
      offs.forEach((off) => off());
      aliasOffs.forEach((off) => off());
    };
  }, [firstValueRecoveryOnly, rows]);

  if (!ready) return null;

  return (
    <div
      className="desk-surface-windows"
      data-surface-registry-state={
        firstValueRecoveryOnly ? "recovery-only" : registryState
      }
    >
      {rows.map((row) => {
        const instance = windowsById[row.id];
        if (!instance || instance.applicationKey !== row.key) return null;
        if (waiting.has(row.id)) return null;
        return (
          <SurfaceWindowHost
            key={row.id}
            row={row}
            scope={instance.scope ?? undefined}
            items={items}
          />
        );
      })}
    </div>
  );
}

/** One hosted core: owns the head's wing slot so the core can publish
 * its faces into the window chrome (HS-100-07, the posture rule), the
 * foot slot so its footer belongs to the frame (HS-129-01), and the
 * title slot so cores can override the manifest label (HS-158-05). */
export function SurfaceWindowHost({
  row,
  scope,
  items,
}: {
  row: SurfaceRow;
  scope: string | undefined;
  items: ReturnType<typeof useDesk.getState>["items"];
}) {
  const [wings, setWings] = useState<ReactNode>(null);
  const [foot, setFoot] = useState<HTMLElement | null>(null);
  const [titleOverride, setTitleOverrideState] = useState<string | null>(null);
  // Window grammar: a core's own narrow step (Settings' rail → pane) owns
  // the compact Back while it is open.
  const [coreBack, setCoreBack] = useState<WindowBack | null>(null);
  // PHILO-13-17 (C7; Astra r1 #751, condition 1): an iconified window
  // unmounts its core (unmountOnMinimize), and the core's cleanup clears
  // the title it published. The window keeps that title while iconified:
  // it is still the same open window (the Dock chip, the 393 switcher).
  const setTitleOverride = useCallback(
    (next: string | null) => {
      if (next === null && useDesk.getState().panelMin.includes(row.id)) return;
      setTitleOverrideState(next);
    },
    [row.id],
  );
  // A Project Room (Desk memory scoped to one project) is named by its
  // project; Desk memory with no project keeps its own word.
  const project =
    row.key === "open-project-memory" && scope?.startsWith("project:")
      ? objectByRef(items, scope)
      : null;
  const scopedName = project ? windowName({ kind: "project", name: project.title }, project.id) : null;
  const bodyRef = useSurfaceScrollPlace(row.id, scope);
  return (
    <DeskWindowFrame
      id={row.id}
      glyph={row.glyph}
      eyebrow={row.eyebrow}
      title={titleOverride ?? scopedName ?? row.title}
      minW={row.minW}
      minH={row.minH}
      defaultW={row.defaultW}
      defaultH={row.defaultH}
      // The creation form keeps its declared footer seat as source choices
      // arrive. Application readers fit the material on their first open.
      fitContent={row.key !== "project-setup"}
      wings={wings}
      // PHILO-16: a window scoped to a project belongs to that Room (Gather).
      room={scope?.startsWith("project:") ? scope : undefined}
      open
      unmountOnMinimize
      onClose={() => useDesk.getState().closeSurfaceWindow(row.key)}
      // Settings scopes select an anchor on its one page, not a child face.
      // Phone Back returns to the caller instead of scrolling Settings to top.
      onBack={
        coreBack?.onBack ?? (scope && row.key !== "configure-settings"
          ? () => useDesk.getState().openSurfaceWindow(row.key, undefined)
          : undefined)
      }
      backTestId={coreBack?.testId}
      className={
        row.key === "configure-settings"
          ? "desk-surface-window desk-settings-window"
          : "desk-surface-window"
      }
    >
      <FootSlotContext.Provider value={foot}>
        <div
          ref={bodyRef}
          className="desk-surface-body surface-host-body"
          data-surface-host={row.key}
        >
          <div data-aftercare-window-slot="top" />
          <BackSlotContext.Provider value={setCoreBack}>
          <TitleSlotContext.Provider value={setTitleOverride}>
            <WingSlotContext.Provider value={setWings}>
              <ApplicationBoundary label={row.title}>
                {/* PHILO-17: the face's code is still loading: busy, so the
                    window never reads as settled empty (the desk sweep's held
                    read: Memory settled here, then its face moved 30 px). */}
                <Suspense fallback={<SurfaceState loading />}>
                  <row.Core
                    scope={scope}
                    scopeLabel={
                      scope
                        ? (objectByRef(items, scope)?.title ?? undefined)
                        : undefined
                    }
                  />
                </Suspense>
              </ApplicationBoundary>
            </WingSlotContext.Provider>
          </TitleSlotContext.Provider>
          </BackSlotContext.Provider>
        </div>
        <footer
          ref={setFoot}
          className="desk-surface-foot surface-footer"
        />
      </FootSlotContext.Provider>
    </DeskWindowFrame>
  );
}

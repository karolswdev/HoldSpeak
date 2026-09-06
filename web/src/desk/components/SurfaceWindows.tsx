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
import {
  DESK_APPLICATION_ALIASES,
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
import { WingSlotContext } from "../surface/wings";
import type { CoreProps } from "../../pages/cores/core-types";
import { ApplicationBoundary } from "./ApplicationBoundary";

export interface SurfaceRow {
  key: string;
  id: string;
  title: string;
  glyph: string;
  eyebrow: string;
  minW?: number;
  /** Preferred first-open height; persisted owner arrangements still win. */
  defaultH?: number;
  /** Open maximized (full stage) — the canvas-sized surfaces want it. */
  maximized?: boolean;
  Core: LazyExoticComponent<ComponentType<CoreProps & { scope?: string }>>;
}

const SURFACES: SurfaceRow[] = SURFACE_APPLICATIONS.map((application) => ({
  key: application.action,
  id: application.windowId,
  title: application.label,
  glyph: application.glyph,
  eyebrow: application.surface.eyebrow,
  minW: application.surface.minW,
  defaultH: application.surface.defaultH,
  maximized: application.surface.maximized,
  Core: lazy(application.surface.load),
}));

/** Alias keys open an existing window with a default scope (e.g. the
 * shelf's Integrations entry is the Settings window scoped to
 * integrations). */
const FIRST_VALUE_RECOVERY_SURFACES = SURFACES.filter(
  (row) => row.key === "project-setup",
);

export function SurfaceWindows({
  firstValueRecoveryOnly = false,
}: {
  /** First value registers only its explicit Setup recovery and starts with
      no persisted Desk windows competing on glass. */
  firstValueRecoveryOnly?: boolean;
} = {}) {
  const windowsById = useDesk((s) => s.windowsById);
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
    if (firstValueRecoveryOnly) useDesk.getState().clearSurfaceWindows();
    setReady(true);
  }, [firstValueRecoveryOnly]);

  useEffect(() => {
    const offs = rows.map((row) =>
      registerSurface(row.key, (scope) => {
        useDesk.getState().openSurfaceWindow(row.key, scope);
      }),
    );
    const aliasOffs = Object.entries(DESK_APPLICATION_ALIASES)
      .filter(([, alias]) => rows.some((row) => row.key === alias.target))
      .map(([key, alias]) =>
        registerSurface(key, (scope) =>
          useDesk.getState().openSurfaceWindow(alias.target, scope ?? alias.scope),
        ),
      );
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
  const [titleOverride, setTitleOverride] = useState<string | null>(null);
  return (
    <DeskWindowFrame
      id={row.id}
      glyph={row.glyph}
      eyebrow={row.eyebrow}
      title={titleOverride ?? row.title}
      minW={row.minW}
      defaultH={row.defaultH}
      wings={wings}
      open
      unmountOnMinimize
      onClose={() => useDesk.getState().closeSurfaceWindow(row.key)}
      className={
        row.key === "configure-settings"
          ? "desk-surface-window desk-settings-window"
          : "desk-surface-window"
      }
    >
      <FootSlotContext.Provider value={foot}>
        <div className="desk-surface-body">
          <TitleSlotContext.Provider value={setTitleOverride}>
            <WingSlotContext.Provider value={setWings}>
              <ApplicationBoundary label={row.title}>
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
              </ApplicationBoundary>
            </WingSlotContext.Provider>
          </TitleSlotContext.Provider>
        </div>
        <footer
          ref={setFoot}
          className="desk-surface-foot surface-footer"
        />
      </FootSlotContext.Provider>
    </DeskWindowFrame>
  );
}

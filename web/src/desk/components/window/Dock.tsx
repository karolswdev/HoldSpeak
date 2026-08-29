// Dock — the application launcher + running window toolbar.
// Extracted from DeskWindow.tsx (HS-117-04).
import { useEffect, useState, type ReactNode } from "react";
import { useIntelligenceAttention } from "../../intelligenceAttention";
import { openIntelligence } from "../../intelligenceNavigation";
import { DOCK_SPRITES, SYSTEM } from "../../systemSprites";
import { useDesk } from "../../store";
import { useChairState } from "../../chairState";
import { useShortcutSheet } from "../../chromeState";
import { useKeymap } from "../../keymap";
import { WorkMenu } from "../DeskMenu";
import { dockChipMenuEntries } from "../../windowMenuAdapter";
import { useOpenWindows, chipEls } from "./windowRegistry";
import { useLaunchers } from "./launcherRegistry";
import { toggleExpose } from "./Expose";
import { VerbGlyph } from "./VerbGlyph";
import { ShortcutSheet } from "./ShortcutSheet";

/** HS-100-11 — the dock IS the launcher: the four applications ride it
 * always (running mark when their window is open); drawers and tools
 * moved to the menu-bar bell and the search shelf. */
const DOCK_APPS = [
  { key: "open-intelligence", id: "intelligence:desk", label: "Intelligence", glyph: "◈", fallback: "/" },
  { key: "dictate", id: "surface-dictation", label: "Speak", glyph: "⌁", fallback: "/dictation" },
  { key: "review-meetings", id: "surface-meetings", label: "Meetings", glyph: "▣", fallback: "/history" },
  { key: "inspect-personas-and-coders", id: "surface-companion", label: "Agents", glyph: "◉", fallback: "/companion" },
  { key: "configure-settings", id: "surface-settings", label: "Settings", glyph: "⚙", fallback: "/settings" },
] as const;
const DOCK_APP_IDS = new Set<string>(DOCK_APPS.map((a) => a.id));
const ACTIONABLE_LAUNCHERS = new Set(["attention", "delivery-board"]);

/** The dock (HS-95-03): every open window as a chip -- tap focuses (or
 * restores a parked one), x closes, loop resets the layout. Ctrl+` cycles
 * focus in MRU order, restoring as it lands. Shell furniture: it rides
 * above the window band, and it is invisible while nothing is open. */
export function Dock({ center }: { center?: ReactNode } = {}) {
  const panelMin = useDesk((s) => s.panelMin);
  const panelOrder = useDesk((s) => s.panelOrder);
  const windows = useOpenWindows();
  const launchers = useLaunchers();
  // HS-111-07 — the HS-101 B8 keyboard grammar (Cmd+1-Cmd+4, Cmd+W, Cmd+M, Ctrl+`,
  // Cmd+/) moved into desk/keymap.ts, driven by the registry's key
  // fields: ONE binder (refcounted -- the chrome mounts it too). The
  // sheet's open state is shared chrome state so the system.sheet
  // verb can draw it.
  useKeymap();
  const sheetOpen = useShortcutSheet((s) => s.open);
  // HS-135-06: the Chair/Floor dock toggle (counsel ruling B.Q1).
  const chairSurface = useChairState((s) => s.surface);
  const toggleSurface = useChairState((s) => s.toggle);
  const intelligenceAttention = useIntelligenceAttention();
  const intelligenceBadge = intelligenceAttention.overdue
    ? String(intelligenceAttention.overdue)
    : intelligenceAttention.briefReady ? "•" : null;
  // HS-99-04 — the dock chip menu (one menu vocabulary).
  const [chipMenu, setChipMenu] = useState<{
    id: string;
    label: string;
    x: number;
    y: number;
    minimized: boolean;
    close: () => void;
  } | null>(null);
  useEffect(() => {
    if (!chipMenu) return;
    const close = () => setChipMenu(null);
    window.addEventListener("pointerdown", close);
    return () => window.removeEventListener("pointerdown", close);
  }, [chipMenu]);

  // The front chip mirrors the shell's is-front rule: the last id in
  // the order that is open here and not minimized (HS-97-04).
  let front: string | undefined;
  for (let i = panelOrder.length - 1; i >= 0; i--) {
    const oid = panelOrder[i];
    if (panelMin.includes(oid)) continue;
    if (!windows.some((w) => w.id === oid)) continue;
    front = oid;
    break;
  }
  // A launcher whose surface is already a window folds into that chip;
  // it only renders as a launcher while its surface is closed.
  const shown = launchers.filter((l) => !windows.some((w) => w.id === l.id));
  return (
    <div
      className="desk-dock"
      role="toolbar"
      aria-label="Dock"
      /* HS-110-04: magnification swell removed -- the shelf is flat. */
    >
      {DOCK_APPS.map((a) => {
        const win = windows.find((w) => w.id === a.id);
        const minimized = win ? panelMin.includes(a.id) : false;
        const badge = a.id === "intelligence:desk" ? intelligenceBadge : null;
        const overdue = badge !== null && badge !== "•";
        return (
          <button
            key={a.id}
            type="button"
            className={
              "desk-dock-launch desk-dock-app" +
              (win ? " is-run" : "") +
              (win && a.id === front && !minimized ? " is-front" : "") +
              (overdue ? " is-attention" : "")
            }
            aria-label={badge ? `${a.label}, ${overdue ? `${badge} overdue` : "brief ready"}` : a.label}
            onClick={() => {
              const s = useDesk.getState();
              if (win && minimized) s.restorePanel(a.id);
              else if (win) s.focusPanel(a.id);
              else if (a.key === "open-intelligence") openIntelligence({ view: "brief" });
              else
                void import("../../shell").then((m) =>
                  m.openSurfaceOr(a.key, a.fallback),
                );
            }}
            onContextMenu={(e) => {
              if (!win) return;
              e.preventDefault();
              setChipMenu({
                id: a.id,
                label: a.label,
                x: e.clientX,
                y: e.clientY,
                minimized,
                close: win.close,
              });
            }}
          >
            {/* HS-111-09 — integer-true: the 32px source renders at 32
                CSS px (64 device px at DPR 2 = exact 2x); 24 was a 1.5x
                smear. */}
            {DOCK_SPRITES[a.id] ? (
              <img src={DOCK_SPRITES[a.id]} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
            ) : (
              <span aria-hidden="true">{a.glyph}</span>
            )}
            <span className="desk-dock-label">{a.label}</span>
            {badge ? (
              <span className="desk-chip desk-dock-badge" data-tone={overdue ? "warn" : undefined}>
                {badge}
              </span>
            ) : null}
          </button>
        );
      })}
      {/* HS-135-06 + HS-135-14: Floor/Chair toggle — the floor-grid
          sprite replaces the ▦ glyph character. */}
      <button
        key="chair-floor-toggle"
        type="button"
        className={
          "desk-dock-launch" +
          (chairSurface === "floor" ? " is-run" : "")
        }
        aria-label={chairSurface === "chair" ? "Floor" : "Chair"}
        aria-pressed={chairSurface === "floor"}
        onClick={toggleSurface}
        data-testid="chair-floor-toggle"
      >
        <img src={SYSTEM.floorGrid} alt="" width={32} height={32} className="desk-dock-sprite" draggable={false} />
        <span className="desk-dock-label">
          {chairSurface === "chair" ? "Floor" : "Chair"}
        </span>
      </button>
      {shown.map((launcher) => {
        const actionable = ACTIONABLE_LAUNCHERS.has(launcher.id);
        return (
          <button
            key={launcher.id}
            type="button"
            className={
              "desk-dock-launch" +
              (launcher.open ? " is-run" : "") +
              (launcher.badge && actionable ? " is-attention" : "")
            }
            aria-label={
              launcher.badge
                ? `${launcher.label}, ${launcher.badge} ${actionable ? "need attention" : "items"}`
                : launcher.label
            }
            onClick={launcher.activate}
          >
            <span aria-hidden="true">{launcher.glyph}</span>
            <span className="desk-dock-label">{launcher.label}</span>
            {launcher.badge ? (
              <span
                className="desk-chip desk-dock-badge"
                data-tone={actionable ? "warn" : undefined}
              >
                {launcher.badge}
              </span>
            ) : null}
          </button>
        );
      })}
      {center}
      {windows.some((w) => !DOCK_APP_IDS.has(w.id)) ? (
        <span className="desk-dock-sep" aria-hidden="true" />
      ) : null}
      {windows.filter((w) => !DOCK_APP_IDS.has(w.id)).map((c) => {
        const minimized = panelMin.includes(c.id);
        return (
          <span
            key={c.id}
            className={
              "desk-dock-chip" +
              (minimized ? " is-min" : "") +
              (c.id === front && !minimized ? " is-front" : "")
            }
          >
            <button
              type="button"
              className="desk-dock-main"
              ref={(el) => {
                if (el) chipEls.set(c.id, el);
                else chipEls.delete(c.id);
              }}
              aria-label={minimized ? `Restore ${c.label}` : `Focus ${c.label}`}
              onClick={() => {
                const s = useDesk.getState();
                if (minimized) s.restorePanel(c.id);
                else s.focusPanel(c.id);
              }}
              onContextMenu={(e) => {
                e.preventDefault();
                setChipMenu({
                  id: c.id,
                  label: c.label,
                  x: e.clientX,
                  y: e.clientY,
                  minimized,
                  close: c.close,
                });
              }}
            >
              <span aria-hidden="true">{c.glyph}</span>
              <span className="desk-dock-label">{c.label}</span>
            </button>
            <button
              type="button"
              className="desk-dock-x"
              aria-label={`Close ${c.label}`}
              onClick={c.close}
            >
              <VerbGlyph kind="close" />
            </button>
          </span>
        );
      })}
      {windows.length > 0 ? (
        <>
          <button
            type="button"
            className="desk-dock-reset"
            aria-label="Overview"
            title="Overview"
            onClick={() => toggleExpose(true)}
          >
            <VerbGlyph kind="overview" />
          </button>
          <button
            type="button"
            className="desk-dock-reset"
            aria-label="Reset layout"
            title="Reset layout"
            onClick={() => useDesk.getState().resetLayout()}
          >
            <VerbGlyph kind="reset" />
          </button>
        </>
      ) : null}
      {chipMenu ? (
        <WorkMenu
          className="desk-dock-menu"
          label={`${chipMenu.label} dock menu`}
          anchor="above"
          x={chipMenu.x}
          y={chipMenu.y}
          entries={dockChipMenuEntries({
            minimized: chipMenu.minimized,
            restore: () => useDesk.getState().restorePanel(chipMenu.id),
            minimize: () => useDesk.getState().minimizePanel(chipMenu.id),
            close: chipMenu.close,
          })}
          onClose={() => setChipMenu(null)}
        />
      ) : null}
      {sheetOpen ? (
        <ShortcutSheet
          onClose={() => useShortcutSheet.getState().setOpen(false)}
        />
      ) : null}
    </div>
  );
}

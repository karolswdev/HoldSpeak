// The Desk's floating system chrome. The room menu stays compact; the opposite
// cluster exposes the three daily starts, one searchable tool shelf, layout,
// and refresh. A fresh Desk renders the same starts centrally instead.
import { useEffect, useState, useRef } from "react";
import { openSurface } from "../shell";
import { useTrustWindow } from "./TrustWindow";
import { useDesk } from "../store";
import { DeskMenuList } from "./DeskMenu";
import { egressBadge } from "../setup";
import { DeskToolShelf } from "./DeskToolShelf";
import { useLaunchers } from "./DeskWindow";

const ROOMS = [
  { label: "Desk", action: "return-to-desk" },
  { label: "Speak", action: "dictate" },
  { label: "Meetings", action: "review-meetings" },
  { label: "Agents", action: "inspect-personas-and-coders" },
  { label: "Settings", action: "configure-settings" },
];

/** HS-100-11 — the attention bell: the approve-queue's badge lives in
 * the system bar, not the dock (the dock carries the applications). */
function AttentionBell() {
  const launchers = useLaunchers();
  const attention = launchers.find((l) => l.id === "attention");
  if (!attention) return null;
  return (
    <button
      type="button"
      className={`desk-bell${attention.open ? " is-open" : ""}`}
      aria-label={
        attention.badge
          ? `Desk memory: ${attention.badge} need attention`
          : "Desk memory"
      }
      title="Desk memory"
      onClick={() => attention.activate()}
    >
      <span aria-hidden="true">◎</span>
      {attention.badge ? <strong>{attention.badge}</strong> : null}
    </button>
  );
}

/** The OS clock — every desktop has one. */
function DeskClock() {
  const [now, setNow] = useState(() => new Date());
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 30_000);
    return () => clearInterval(t);
  }, []);
  const time = now.toLocaleTimeString(undefined, {
    hour: "2-digit",
    minute: "2-digit",
  });
  const day = now.toLocaleDateString(undefined, {
    weekday: "short",
    day: "numeric",
    month: "short",
  });
  return (
    <span className="desk-clock" aria-label={`${day} ${time}`}>
      <span>{day}</span>
      <strong>{time}</strong>
    </span>
  );
}

export function DeskChrome({
  showDailyStarts = true,
}: {
  showDailyStarts?: boolean;
}) {
  // HS-100-11 — the daily starts live on the arrival and the dock; the
  // bar keeps system truth only.
  void showDailyStarts;
  const status = useDesk((s) => s.status);
  const error = useDesk((s) => s.error);
  const setup = useDesk((s) => s.setup);
  const loading = useDesk((s) => s.loading);
  const positions = useDesk((s) => s.positions);
  const viewMode = useDesk((s) => s.viewMode);
  const { refresh, tidyDesk, setViewMode } = useDesk.getState();
  const [menuOpen, setMenuOpen] = useState(false);
  const markRef = useRef<HTMLButtonElement | null>(null);

  const anyLive = Object.values(status).some((v) => v === "live");
  const hubState = error ? "degraded" : anyLive ? "live" : "connecting";
  const hubTitle =
    hubState === "live"
      ? "Hub connected"
      : hubState === "degraded"
        ? error
        : "Connecting";
  const badge = egressBadge(setup);

  return (
    <div className="desk-menubar">
      <div className="desk-chrome desk-chrome-tl">
        <div className="desk-menu-wrap">
          <button
            type="button"
            ref={markRef}
            className="desk-mark"
            aria-expanded={menuOpen}
            aria-haspopup="menu"
            onClick={() => setMenuOpen((v) => !v)}
            title="HoldSpeak"
          >
            <span className="desk-mark-glyph" aria-hidden="true">
              ◍
            </span>
            HoldSpeak
          </button>
          {menuOpen && (
            <DeskMenuList
              className="desk-menu"
              label="HoldSpeak"
              anchor="below"
              onMouseLeave={() => setMenuOpen(false)}
              onClose={() => setMenuOpen(false)}
              returnFocus={() => markRef.current?.focus()}
            >
              {[
                {
                  label: viewMode === "list" ? "Spatial view" : "List view",
                  run: () =>
                    setViewMode(viewMode === "list" ? "spatial" : "list"),
                },
                ...(Object.keys(positions).length > 0
                  ? [{ label: "Arrange desk", run: tidyDesk }]
                  : []),
                { label: "Refresh from hub", run: () => void refresh() },
              ].map((v) => (
                <button
                  key={v.label}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    v.run();
                  }}
                >
                  {v.label}
                </button>
              ))}
              {ROOMS.map((r) => (
                <button
                  key={r.action}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setMenuOpen(false);
                    // Every room is a desk surface now (HS-95-08): the
                    // menu only dispatches; nothing navigates.
                    if (r.action !== "return-to-desk") openSurface(r.action);
                  }}
                >
                  {r.label}
                </button>
              ))}
            </DeskMenuList>
          )}
        </div>
        <span
          className={`desk-hub-dot is-${hubState}`}
          title={hubTitle}
          aria-label={hubTitle}
        />
        <button
          type="button"
          className={`egress-badge is-${badge.scope} egress-badge-button`}
          title={badge.title}
          aria-label={`Privacy and trust: ${badge.text}`}
          onClick={() => useTrustWindow.getState().setOpen(true)}
        >
          {badge.text}
        </button>
      </div>

      <div className="desk-chrome desk-chrome-tr">
        <AttentionBell />
        <DeskToolShelf />
        <DeskClock />
      </div>
    </div>
  );
}

// The Desk's floating system chrome. The room menu stays compact; the opposite
// cluster exposes the three daily starts, one searchable tool shelf, layout,
// and refresh. A fresh Desk renders the same starts centrally instead.
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { workroomHref } from "../../workrooms/context";
import { openSurface } from "../shell";
import { useDesk } from "../store";
import { egressBadge } from "../setup";
import { DeskStartActions } from "./DeskStartActions";
import { DeskToolShelf } from "./DeskToolShelf";

const ROOMS = [
  { label: "Desk", href: "/", action: "return-to-desk" },
  { label: "Dictation", href: "/dictation", action: "dictate" },
  { label: "Meetings", href: "/history", action: "review-meetings" },
  { label: "Studio", href: "/studio", action: "configure-tools" },
  { label: "Settings", href: "/settings", action: "configure-settings" },
];

export function DeskChrome({
  showDailyStarts = true,
}: {
  showDailyStarts?: boolean;
}) {
  const status = useDesk((s) => s.status);
  const error = useDesk((s) => s.error);
  const setup = useDesk((s) => s.setup);
  const loading = useDesk((s) => s.loading);
  const positions = useDesk((s) => s.positions);
  const viewMode = useDesk((s) => s.viewMode);
  const { refresh, tidyDesk, setViewMode } = useDesk.getState();
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();

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
    <>
      <div className="desk-chrome desk-chrome-tl">
        <div className="desk-menu-wrap">
          <button
            type="button"
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
            <nav
              className="desk-menu"
              role="menu"
              onMouseLeave={() => setMenuOpen(false)}
            >
              {ROOMS.map((r) =>
                r.href === "/" ? (
                  <Link key={r.href} role="menuitem" to="/">
                    {r.label}
                  </Link>
                ) : (
                  <button
                    key={r.href}
                    type="button"
                    role="menuitem"
                    onClick={() => {
                      setMenuOpen(false);
                      // The shell mechanism (HS-95-03): open the surface
                      // in-world; the route is only the not-yet-landed
                      // fallback (HS-95-05..08 retire it).
                      if (!openSurface(r.action))
                        navigate(workroomHref(r.href, { action: r.action }));
                    }}
                  >
                    {r.label}
                  </button>
                ),
              )}
            </nav>
          )}
        </div>
        <span
          className={`desk-hub-dot is-${hubState}`}
          title={hubTitle}
          aria-label={hubTitle}
        />
        <span className={`egress-badge is-${badge.scope}`} title={badge.title}>
          {badge.text}
        </span>
      </div>

      <div className="desk-chrome desk-chrome-tr">
        {showDailyStarts ? <DeskStartActions compact /> : null}
        <DeskToolShelf />
        <button
          type="button"
          className="desk-chip"
          aria-pressed={viewMode === "list"}
          onClick={() =>
            setViewMode(viewMode === "list" ? "spatial" : "list")
          }
          title="Show the Desk as a keyboard-first list"
        >
          List
        </button>
        {Object.keys(positions).length > 0 && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={tidyDesk}
            title="Reset the desk layout"
          >
            Arrange
          </button>
        )}
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void refresh()}
          disabled={loading}
          aria-busy={loading}
          title="Refresh Desk from hub"
          aria-label="Refresh Desk from hub"
        >
          ↻
        </button>
      </div>
      {showDailyStarts ? (
        <div className="desk-hint">Select an item for actions</div>
      ) : null}
    </>
  );
}

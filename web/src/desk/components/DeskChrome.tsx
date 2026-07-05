// The arrival chrome (HS-73-02): the world owns the viewport; chrome is a
// floating minimal cluster, iPad-style. Top-left: the mark, a compact menu
// (the rooms), the hub dot, the egress badge. Top-right: the create chips +
// Tidy/Refresh. Bottom: ONE whispered hint. No header stack, no prose.
import { useState } from "react";
import { useDesk } from "../store";
import { egressBadge } from "../setup";

const ROOMS = [
  { label: "Dictation", href: "/dictation" },
  { label: "Meetings", href: "/history" },
  { label: "Studio", href: "/studio" },
  { label: "Settings", href: "/settings" },
];

export function DeskChrome() {
  const status = useDesk((s) => s.status);
  const error = useDesk((s) => s.error);
  const setup = useDesk((s) => s.setup);
  const loading = useDesk((s) => s.loading);
  const positions = useDesk((s) => s.positions);
  const { refresh, tidyDesk, createPrimitive } = useDesk.getState();
  const [menuOpen, setMenuOpen] = useState(false);

  const anyLive = Object.values(status).some((v) => v === "live");
  const hubState = error ? "degraded" : anyLive ? "live" : "connecting";
  const hubTitle =
    hubState === "live" ? "Hub connected" : hubState === "degraded" ? error : "Connecting";
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
            <span className="desk-mark-glyph" aria-hidden="true">◍</span>
            HoldSpeak
          </button>
          {menuOpen && (
            <nav className="desk-menu" role="menu" onMouseLeave={() => setMenuOpen(false)}>
              {ROOMS.map((r) => (
                <a key={r.href} role="menuitem" href={r.href}>
                  {r.label}
                </a>
              ))}
            </nav>
          )}
        </div>
        <span className={`desk-hub-dot is-${hubState}`} title={hubTitle} aria-label={hubTitle} />
        <span className={`egress-badge is-${badge.scope}`} title={badge.title}>
          {badge.text}
        </span>
      </div>

      <div className="desk-chrome desk-chrome-tr">
        <button type="button" className="desk-chip" onClick={() => void createPrimitive("note")}>
          + Note
        </button>
        <button type="button" className="desk-chip" onClick={() => void createPrimitive("kb")}>
          + KB
        </button>
        <button type="button" className="desk-chip" onClick={() => void createPrimitive("recipe")}>
          + Recipe
        </button>
        <button type="button" className="desk-chip" onClick={() => void createPrimitive("zone")}>
          + Zone
        </button>
        <button type="button" className="desk-chip" onClick={() => void createPrimitive("workflow")}>
          + Workflow
        </button>
        {Object.keys(positions).length > 0 && (
          <button
            type="button"
            className="desk-chip quiet"
            onClick={tidyDesk}
            title="Reset the desk layout"
          >
            Tidy
          </button>
        )}
        <button
          type="button"
          className="desk-chip quiet"
          onClick={() => void refresh()}
          disabled={loading}
          aria-busy={loading}
          title="Refresh from hub"
        >
          ↻
        </button>
      </div>

      <div className="desk-hint">drag to arrange</div>
    </>
  );
}

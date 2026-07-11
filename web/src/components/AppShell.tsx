import { type ReactNode, useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { useRuntimeBus } from "../runtime/RuntimeBus";
import { Button, Dialog, StatusPill } from "./signal/Signal";
import { AmbientLayer } from "./AmbientLayer";

const DAILY = [
  ["/", "Desk"],
  ["/dictation", "Dictation"],
  ["/history", "Meetings"],
] as const;

const STUDIO = [
  ["/studio", "Studio"],
  ["/activity", "Activity"],
  ["/commands", "Commands"],
  ["/cadence", "Cadence"],
  ["/workbench", "Workbench"],
] as const;

type Trust = { egress?: { mode?: string; target?: string }; summary?: string };

export function AppShell({
  children,
  immersive = false,
}: {
  children: ReactNode;
  immersive?: boolean;
}) {
  const location = useLocation();
  const { state } = useRuntimeBus();
  const [menuOpen, setMenuOpen] = useState(false);
  const [trustOpen, setTrustOpen] = useState(false);
  const [trust, setTrust] = useState<Trust | null>(null);

  useEffect(() => {
    setMenuOpen(false);
    document.title = `HoldSpeak${location.pathname === "/" ? "" : ` — ${location.pathname.split("/").filter(Boolean).at(-1) ?? "Web"}`}`;
  }, [location.pathname]);

  useEffect(() => {
    void apiFetch<{ trust?: Trust }>("/api/setup/status")
      .then((value) => setTrust(value.trust ?? null))
      .catch(() => null);
  }, []);

  if (immersive)
    return (
      <>
        <main id="main" className="app-immersive" tabIndex={-1}>
          {children}
        </main>
        <AmbientLayer />
      </>
    );

  const egress =
    trust?.egress?.mode === "cloud"
      ? "cloud"
      : trust?.egress?.mode === "local+cloud"
        ? "local+cloud"
        : "local";
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="app-header">
        <NavLink className="app-brand" to="/">
          <span aria-hidden="true">◍</span> HoldSpeak
        </NavLink>
        <Button
          className="app-menu-button"
          variant="ghost"
          aria-expanded={menuOpen}
          aria-controls="app-navigation"
          onClick={() => setMenuOpen((value) => !value)}
        >
          Menu
        </Button>
        <nav
          id="app-navigation"
          className={menuOpen ? "is-open" : ""}
          aria-label="Primary navigation"
        >
          {DAILY.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
          <div className="app-studio-menu">
            {STUDIO.map(([to, label]) => (
              <NavLink key={to} to={to}>
                {label}
              </NavLink>
            ))}
          </div>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
        <div className="app-status">
          <StatusPill
            tone={
              state === "connected"
                ? "success"
                : state === "offline"
                  ? "error"
                  : "warning"
            }
          >
            {state}
          </StatusPill>
          <Button
            dense
            variant="ghost"
            onClick={() => setTrustOpen(true)}
            aria-label={`Privacy and trust: ${egress}`}
          >
            {egress}
          </Button>
        </div>
      </header>
      <main id="main" tabIndex={-1}>
        {children}
      </main>
      <Dialog
        open={trustOpen}
        title="Privacy & Trust"
        onClose={() => setTrustOpen(false)}
      >
        <p>
          {trust?.summary ??
            "HoldSpeak reports its current egress posture from the local hub."}
        </p>
        <dl className="signal-facts">
          <div>
            <dt>Current scope</dt>
            <dd>{egress}</dd>
          </div>
          <div>
            <dt>Target</dt>
            <dd>{trust?.egress?.target ?? "This machine"}</dd>
          </div>
        </dl>
        <p>
          <NavLink to="/settings" onClick={() => setTrustOpen(false)}>
            Review privacy settings
          </NavLink>
        </p>
      </Dialog>
      <AmbientLayer />
    </div>
  );
}

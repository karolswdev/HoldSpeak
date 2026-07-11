import { type ReactNode, useEffect, useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { apiFetch } from "../lib/api";
import { useRuntimeBus } from "../runtime/RuntimeBus";
import { Button, Dialog, StatusPill } from "./signal/Signal";
import { AmbientLayer } from "./AmbientLayer";

export const PRIMARY_NAV = [
  ["/", "Desk"],
  ["/dictation", "Dictation"],
  ["/history", "Meetings"],
  ["/studio", "Studio"],
  ["/settings", "Settings"],
] as const;

type TrustDestination = {
  id: string;
  name: string;
  operation: string;
  enabled: boolean;
  destination: string;
  boundary: string;
  data_class: string;
  authority_basis: string;
  background_ability: string;
  revoke_action: string;
  last_receipt?: string | null;
};
type Trust = {
  transcript_egress?: "none" | "configured" | "possible";
  summary?: string;
  destinations?: TrustDestination[];
};

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

  const enabledDestinations =
    trust?.destinations?.filter((item) => item.enabled) ?? [];
  const egress =
    trust?.transcript_egress === "none"
      ? "this device"
      : "this device + external";
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
          {PRIMARY_NAV.map(([to, label]) => (
            <NavLink key={to} to={to} end={to === "/"}>
              {label}
            </NavLink>
          ))}
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
            "Current data boundaries and enabled destinations."}
        </p>
        {enabledDestinations.length > 0 ? (
          <p role="alert">
            External destinations are enabled. Review each authority boundary
            and revoke action below.
          </p>
        ) : null}
        <dl className="signal-facts">
          <div>
            <dt>Current scope</dt>
            <dd>{egress}</dd>
          </div>
          <div>
            <dt>Enabled destinations</dt>
            <dd>{enabledDestinations.length}</dd>
          </div>
        </dl>
        <div className="trust-destinations">
          {(trust?.destinations ?? []).map((destination) => (
            <article key={destination.id} className="signal-card">
              <h3>{destination.name}</h3>
              <StatusPill tone={destination.enabled ? "warning" : "success"}>
                {destination.enabled ? "Enabled" : "Off"}
              </StatusPill>
              <dl className="signal-facts">
                <div>
                  <dt>Destination</dt>
                  <dd>{destination.destination}</dd>
                </div>
                <div>
                  <dt>Operation</dt>
                  <dd>{destination.operation}</dd>
                </div>
                <div>
                  <dt>Boundary</dt>
                  <dd>{destination.boundary}</dd>
                </div>
                <div>
                  <dt>Data</dt>
                  <dd>{destination.data_class}</dd>
                </div>
                <div>
                  <dt>Authority</dt>
                  <dd>{destination.authority_basis}</dd>
                </div>
                <div>
                  <dt>Background</dt>
                  <dd>{destination.background_ability}</dd>
                </div>
                <div>
                  <dt>Revoke</dt>
                  <dd>{destination.revoke_action}</dd>
                </div>
                <div>
                  <dt>Last receipt</dt>
                  <dd>{destination.last_receipt ?? "None recorded"}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
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

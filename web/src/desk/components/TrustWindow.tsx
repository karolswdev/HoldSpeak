// HS-95-10 — Privacy & Trust on the desk (Constitution, Article III). The
// flat shell's trust panel died with the header in HS-95-08; the contract
// did not: the egress badge is the one trust answer at a glance, and
// tapping it opens THIS window — the full boundary read-out (scope,
// enabled destinations, authority basis, revoke action, last receipt) from
// `/api/setup/status`, ported verbatim from the Phase 42 shell panel.
import { useEffect, useState } from "react";
import { create } from "zustand";
import { apiFetch } from "../../lib/api";
import { StatusPill } from "../../components/signal/Signal";
import { DeskWindowFrame } from "./DeskWindow";
import { openSurfaceOr } from "../shell";

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

interface TrustWindowState {
  open: boolean;
  setOpen(open: boolean): void;
}

export const useTrustWindow = create<TrustWindowState>((set) => ({
  open: false,
  setOpen: (open) => set({ open }),
}));

export function TrustWindow() {
  const open = useTrustWindow((s) => s.open);
  const [trust, setTrust] = useState<Trust | null>(null);

  useEffect(() => {
    if (!open) return;
    void apiFetch<{ trust?: Trust }>("/api/setup/status")
      .then((value) => setTrust(value.trust ?? null))
      .catch(() => null);
  }, [open]);

  const enabledDestinations =
    trust?.destinations?.filter((item) => item.enabled) ?? [];
  const egress =
    trust?.transcript_egress === "none"
      ? "this device"
      : "this device + external";

  return (
    <DeskWindowFrame
      id="trust"
      glyph="◍"
      eyebrow="Privacy & Trust"
      title="Data boundaries"
      minW={420}
      open={open}
      onClose={() => useTrustWindow.getState().setOpen(false)}
      className="desk-trust-window"
    >
      <div className="desk-surface-body">
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
          <button
            type="button"
            className="btn-link"
            onClick={() => {
              useTrustWindow.getState().setOpen(false);
              openSurfaceOr("configure-settings", "/settings");
            }}
          >
            Review privacy settings
          </button>
        </p>
      </div>
    </DeskWindowFrame>
  );
}

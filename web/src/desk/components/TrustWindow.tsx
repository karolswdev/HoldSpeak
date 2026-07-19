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
import {
  SurfaceGroup,
  SurfaceSection,
  SurfaceSettingRow,
} from "../surface/Surface";

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
        <p className="surface-lede">
          {trust?.summary ??
            "Current data boundaries and enabled destinations."}
        </p>
        {enabledDestinations.length > 0 ? (
          <p role="alert" className="surface-lede">
            External destinations are enabled. Review each authority boundary
            and revoke action below.
          </p>
        ) : null}
        <SurfaceGroup>
          <SurfaceSettingRow
            label="Current scope"
            control={<span className="surface-setting-value">{egress}</span>}
          />
          <SurfaceSettingRow
            label="Enabled destinations"
            control={
              <span className="surface-setting-value">
                {enabledDestinations.length}
              </span>
            }
          />
        </SurfaceGroup>
        {(trust?.destinations ?? []).map((destination) => (
          <SurfaceSection
            key={destination.id}
            label={destination.name}
            actions={
              <StatusPill tone={destination.enabled ? "warning" : "success"}>
                {destination.enabled ? "Enabled" : "Off"}
              </StatusPill>
            }
          >
            <SurfaceGroup>
              {(
                [
                  ["Destination", destination.destination],
                  ["Operation", destination.operation],
                  ["Boundary", destination.boundary],
                  ["Data", destination.data_class],
                  ["Authority", destination.authority_basis],
                  ["Background", destination.background_ability],
                  ["Revoke", destination.revoke_action],
                  ["Last receipt", destination.last_receipt ?? "None recorded"],
                ] as const
              ).map(([label, value]) => (
                <SurfaceSettingRow
                  key={label}
                  label={label}
                  control={
                    <span className="surface-setting-value">{value}</span>
                  }
                />
              ))}
            </SurfaceGroup>
          </SurfaceSection>
        ))}
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

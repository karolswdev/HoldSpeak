// HS-95-10 — Privacy & Trust on the desk (Constitution, Article III). The
// flat shell's trust panel died with the header in HS-95-08; the contract
// did not: the egress badge is the one trust answer at a glance, and
// tapping it opens THIS window — the full boundary read-out (scope,
// enabled destinations, authority basis, revoke action, last receipt) from
// `/api/setup/status`, ported verbatim from the Phase 42 shell panel.
// HS-201-06 — the row heads speak plain words (Constitution tenet 4).
import { useEffect, useState } from "react";
import { create } from "zustand";
import { apiFetch } from "../../lib/api";
import { LampGadget } from "../surface/gadgets";
import { DeskWindowFrame } from "./DeskWindow";
import { openSurfaceOr } from "../shell";
import { inboundLine } from "../setup";
import {
  SurfaceGroup,
  SurfaceSection,
  SurfaceSettingRow,
} from "../surface/Surface";
import { Button } from "../../components/signal/Signal";

type TrustDestination = {
  id: string;
  name: string;
  operation: string;
  /** Data can leave this device through this destination. */
  enabled: boolean;
  /** A saved Send destination (Settings, Connections). One on this device
   *  is saved and not `enabled`. */
  saved?: boolean;
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
  // HS-201-01 (counsel fix round): who may REACH this hub. Inbound is not
  // egress, so it is stated here as its own line, whatever the
  // destinations say (`holdspeak/setup_status.py:176-177`).
  web_bind?: string;
  auth_token_set?: boolean;
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

  // `enabled` = data can leave this device. A saved Send destination on
  // this device is in use and sends nothing out (inventory 2026-10-03: the
  // count said None with a saved destination).
  const enabledDestinations =
    trust?.destinations?.filter((item) => item.enabled) ?? [];
  const inUseDestinations =
    trust?.destinations?.filter((item) => item.enabled || item.saved) ?? [];
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
          {enabledDestinations.length > 0
            ? "External destinations configured"
            : "All data stays on this device"}
        </p>
        <SurfaceGroup>
          <SurfaceSettingRow
            label="Current scope"
            control={<span className="surface-setting-value">{egress}</span>}
          />
          {/* HS-201-01 (counsel fix round, Astra finding 4): the inbound
              fact, kept rather than retired. */}
          <SurfaceSettingRow
            label="Open to the network"
            control={
              <span className="surface-setting-value" data-testid="trust-inbound">
                {inboundLine(trust)}
              </span>
            }
          />
          <SurfaceSettingRow
            label="Enabled destinations"
            control={
              <span className="surface-setting-value">
                {inUseDestinations.length || "None"}
              </span>
            }
          />
        </SurfaceGroup>
        {(trust?.destinations ?? []).map((destination) => (
          <SurfaceSection
            key={destination.id}
            label={destination.name}
            actions={
              /* PHILO-13-04 (A3): Trust's fact is whether this route
                 sends data out. "OFF" beside "Meeting summary" read as "the
                 summary is off" (Settings says SET ON), and its dot was
                 green. Now the lamp is lit only when data can leave. */
              <LampGadget
                on={destination.enabled}
                tone="warn"
                label={
                  destination.enabled
                    ? "SENDS OUT"
                    : destination.saved
                      ? "THIS DEVICE"
                      : "SENDS NOTHING"
                }
              />
            }
          >
            <SurfaceGroup>
              {(
                [
                  ["Destination", destination.destination],
                  ["Operation", destination.operation],
                  // HS-201-06 (Constitution tenet 4, ASD-STE100): the
                  // heads are short common words with one meaning.
                  // "How to stop sending" names what the row stops:
                  // the transfer out of this device, not the work
                  // itself (counsel finding 5, 2026-09-19).
                  // "Receipt" stays: it is a registered product term
                  // (docs/product-language.json, terms.receipt).
                  ["Where it goes", destination.boundary],
                  ["Data", destination.data_class],
                  ["Allowed by", destination.authority_basis],
                  ["Runs without you", destination.background_ability],
                  ["How to stop sending", destination.revoke_action],
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
          <Button
            variant="chrome"
            className="desk-chip quiet"
            onClick={() => {
              useTrustWindow.getState().setOpen(false);
              openSurfaceOr("configure-settings", "/settings");
            }}
          >
            Review privacy settings
          </Button>
        </p>
      </div>
    </DeskWindowFrame>
  );
}

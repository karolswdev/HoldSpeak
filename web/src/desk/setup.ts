/** Setup/trust state for the chrome (HS-73-02): the `/api/setup/status`
 * snapshot and the canonical egress badge derived from it — the faithful
 * port of the original desk's `egressBadge()` (the ONE structured badge that
 * replaces privacy prose; POSITIONING canon). */

export interface TrustDestination {
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
  last_receipt?: Record<string, unknown> | null;
}

export interface SetupStatus {
  first_run?: boolean;
  arrival_required?: boolean;
  onboarding?: {
    disposition?: "completed" | "dismissed" | "needs_help" | null;
  };
  overall?: string;
  trust?: {
    web_bind?: string;
    auth_token_set?: boolean;
    actuators_enabled?: boolean;
    transcript_egress?: string;
    configured_endpoints?: string[];
    destinations?: TrustDestination[];
    last_egress?: { id: string; name: string; receipt: string } | null;
  };
  [key: string]: unknown;
}
import { apiFetch } from "../lib/api";

export async function loadSetup(): Promise<SetupStatus | null> {
  try {
    return await apiFetch<SetupStatus>("/api/setup/status");
  } catch {
    return null; // adapter unreachable — chrome stays quiet (honest)
  }
}

export interface EgressBadge {
  scope: "local" | "mixed" | "cloud";
  text: string;
  title: string;
}

/** Who may REACH this hub, stated as its own token (HS-201-01).
 *
 * Counsel fix round, Astra finding 4. The chip used to fold the
 * off-loopback-without-token fact into `External reach enabled`, and the
 * 201-01 destination rule then suppressed it: a hub bound to `0.0.0.0`
 * with no token and no destinations read `This device`, which is true of
 * egress and false of exposure. Inbound is not egress, so it is its own
 * token and no destination count decides it. `web_bind` and
 * `auth_token_set` come straight from the hub
 * (`holdspeak/setup_status.py:176-177`). */
export interface InboundBadge {
  text: string;
  title: string;
  /** The hub answers machines other than this one. */
  open: boolean;
  /** A token is required of them. */
  tokenSet: boolean;
}

const LOOPBACK = ["127.0.0.1", "localhost", "::1"];

/** The inbound token, or `null` when the hub is not open without a token. */
export function inboundBadge(setup: SetupStatus | null): InboundBadge | null {
  const t = setup?.trust || {};
  const bind = (t.web_bind || "").trim();
  const open = Boolean(bind) && !LOOPBACK.includes(bind);
  const tokenSet = Boolean(t.auth_token_set);
  if (!open || tokenSet) return null;
  return {
    text: "OPEN TO NETWORK",
    title: `The hub answers other machines on ${bind}. No token is set.`,
    open,
    tokenSet,
  };
}

/** The Trust window's one line for the same fact. */
export function inboundLine(
  trust: { web_bind?: string; auth_token_set?: boolean } | null | undefined,
): string {
  const bind = (trust?.web_bind || "").trim();
  const open = Boolean(bind) && !LOOPBACK.includes(bind);
  return `${open ? "yes" : "no"} \u00b7 Token: ${trust?.auth_token_set ? "set" : "not set"}`;
}

export function egressBadge(setup: SetupStatus | null): EgressBadge {
  const t = setup?.trust || {};
  if (t.last_egress?.name) {
    return {
      scope: "mixed",
      text: `→ ${t.last_egress.name}`,
      title: `Last receipted egress: ${t.last_egress.receipt}`,
    };
  }
  // HS-201-01: the chip and the Trust window state the same thing. The
  // Trust window reads the DESTINATIONS (`components/TrustWindow.tsx:59`,
  // `:79-81`), so `actuators_enabled` alone -- a permission with nothing
  // switched on to use it -- must not read as reach. Zero enabled
  // destinations = this device, on both faces.
  const enabledDestinations = (t.destinations ?? []).filter((d) => d.enabled);
  if (enabledDestinations.length > 0 && t.actuators_enabled) {
    return {
      scope: "mixed",
      text: "→ External reach enabled",
      title:
        "Configured destinations can receive data after authority is granted.",
    };
  }
  if (t.transcript_egress && t.transcript_egress !== "none") {
    const ep = (t.configured_endpoints && t.configured_endpoints[0]) || "";
    const label = ep ? `Leaves device · ${ep}` : "Configured endpoint";
    return {
      scope: "cloud",
      text: `☁ ${label}`,
      title: "A transcript can be sent to a configured endpoint.",
    };
  }
  return {
    scope: "local",
    text: "⌂ This device",
    title: "Transcript processing stays on this device.",
  };
}

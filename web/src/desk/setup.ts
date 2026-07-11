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

export function egressBadge(setup: SetupStatus | null): EgressBadge {
  const t = setup?.trust || {};
  const bind = t.web_bind;
  const offLoopback =
    bind && bind !== "127.0.0.1" && bind !== "localhost" && bind !== "::1";
  if (t.actuators_enabled || (offLoopback && !t.auth_token_set)) {
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

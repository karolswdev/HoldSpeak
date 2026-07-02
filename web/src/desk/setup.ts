/** Setup/trust state for the chrome (HS-73-02): the `/api/setup/status`
 * snapshot and the canonical egress badge derived from it — the faithful
 * port of the Alpine desk's `egressBadge()` (the ONE structured badge that
 * replaces privacy prose; POSITIONING canon). */

export interface SetupStatus {
  first_run?: boolean;
  overall?: string;
  trust?: {
    web_bind?: string;
    auth_token_set?: boolean;
    actuators_enabled?: boolean;
    transcript_egress?: string;
    configured_endpoints?: string[];
  };
  [key: string]: unknown;
}

export async function loadSetup(): Promise<SetupStatus | null> {
  try {
    const res = await fetch("/api/setup/status");
    if (!res.ok) return null;
    return await res.json();
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
  const offLoopback = bind && bind !== "127.0.0.1" && bind !== "localhost" && bind !== "::1";
  if (t.actuators_enabled || (offLoopback && !t.auth_token_set)) {
    return {
      scope: "mixed",
      text: "⌂+☁ Local + cloud",
      title: "Local plus a configured cloud reach. Writes still need your approval.",
    };
  }
  if (t.transcript_egress && t.transcript_egress !== "none") {
    const ep = (t.configured_endpoints && t.configured_endpoints[0]) || "";
    const label = ep ? `Cloud · ${ep}` : "Configured endpoint";
    return {
      scope: "cloud",
      text: `☁ ${label}`,
      title: "A transcript can be sent to a configured endpoint.",
    };
  }
  return { scope: "local", text: "⌂ Local only", title: "Everything stays on this machine." };
}

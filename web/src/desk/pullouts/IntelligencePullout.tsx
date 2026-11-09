/** Betterment daily D4: the Today window is one page (no wings). A drill
 *  to a decision opens the Decisions window (intelligenceNavigation.ts; the
 *  native app, 2026-11-08: Today keeps no second Decisions page). The
 *  Follow-through wing is parked (`views/_parked`); its rows and verbs are
 *  the Needs-you rows. */
import { useEffect, useState } from "react";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation } from "../intelligenceNavigation";
import { TodayView } from "./views/TodayView";
import type { PulloutContentProps } from "./types";
import "./intelligence.css";

export function IntelligencePullout({ object }: PulloutContentProps) {
  const [sinceRequest, setSinceRequest] = useState(0);
  useEffect(() => {
    const navigate = (event: Event) => {
      const request = (event as CustomEvent<IntelligenceNavigation>).detail;
      if (request.view === "brief") setSinceRequest(request.nonce ?? 1);
      else if (request.view === "today") setSinceRequest(0);
    };
    window.addEventListener(INTELLIGENCE_NAVIGATE, navigate);
    return () => window.removeEventListener(INTELLIGENCE_NAVIGATE, navigate);
  }, []);

  if (object.kind !== "intelligence") return null;
  return <TodayView sinceRequest={sinceRequest} />;
}

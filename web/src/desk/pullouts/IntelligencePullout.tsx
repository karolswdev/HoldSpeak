/** Today hosts one app: View picks the day, Brief, Prepared or Activity. Decisions and Needs you keep their own windows. */
import { useEffect, useState } from "react";
import { INTELLIGENCE_NAVIGATE, type IntelligenceNavigation } from "../intelligenceNavigation";
import { TodayView } from "./views/TodayView";
import type { PulloutContentProps } from "./types";

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

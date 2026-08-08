import { useDesk } from "./store";

export type IntelligenceView = "brief" | "follow-through" | "receipts";

export type IntelligenceNavigation = {
  view: IntelligenceView;
  receiptQuery?: string;
  receiptId?: string;
  receiptWorkRef?: string;
  followThroughId?: string;
  overdueOnly?: boolean;
  whyOnly?: boolean;
};

export const INTELLIGENCE_NAVIGATE = "holdspeak:intelligence-navigate";

/** Open the one Intelligence pullout and deliver its requested focus after it mounts. */
export function openIntelligence(navigation: IntelligenceNavigation): void {
  useDesk.getState().openPullout("intelligence:desk");
  window.setTimeout(() => {
    window.dispatchEvent(new CustomEvent<IntelligenceNavigation>(INTELLIGENCE_NAVIGATE, { detail: navigation }));
  }, 0);
}

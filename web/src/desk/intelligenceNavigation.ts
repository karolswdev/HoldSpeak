import { useDesk } from "./store";

/** Betterment daily D4: Today is one page. `brief` is Today with Since
 *  yesterday open; `receipts` is the Decisions page in the same window;
 *  `follow-through` (parked) opens the Needs-you window, where its rows and
 *  verbs live. */
export type IntelligenceView = "today" | "brief" | "follow-through" | "receipts";

export type IntelligenceNavigation = {
  view: IntelligenceView;
  receiptQuery?: string;
  receiptId?: string;
  /** PHILO-17: one decision of the desk (a `decisions` row), opened in place. */
  decisionId?: string;
  /** A new number per decision request: asking for the same decision again
   *  opens it again (openIntelligence sets it; other views keep none, so the
   *  dock's same-destination open adds no BACK step). */
  nonce?: number;
  receiptWorkRef?: string;
  followThroughId?: string;
  overdueOnly?: boolean;
  whyOnly?: boolean;
};

export const INTELLIGENCE_NAVIGATE = "holdspeak:intelligence-navigate";

/** Open the one Intelligence pullout and deliver its requested focus after it mounts. */
let requests = 0;

export function openIntelligence(navigation: IntelligenceNavigation): void {
  if (navigation.view === "follow-through") {
    // Loaded on use: chairWindows reaches the window registry, which must
    // not load while this module (imported by openObject) is loading.
    // The request is still announced (its listeners name the card); the
    // Today window ignores it.
    void import("./chair/chairWindows").then((m) => m.openChairWindow("chair:needs"));
    window.setTimeout(() => {
      window.dispatchEvent(new CustomEvent<IntelligenceNavigation>(INTELLIGENCE_NAVIGATE, { detail: navigation }));
    }, 0);
    return;
  }
  if (navigation.view === "brief") {
    requests += 1;
    navigation = { ...navigation, nonce: requests };
  }
  if (navigation.decisionId) {
    requests += 1;
    navigation = { ...navigation, nonce: requests };
  }
  useDesk.getState().openPullout("intelligence:desk");
  window.setTimeout(() => {
    window.dispatchEvent(new CustomEvent<IntelligenceNavigation>(INTELLIGENCE_NAVIGATE, { detail: navigation }));
  }, 0);
}

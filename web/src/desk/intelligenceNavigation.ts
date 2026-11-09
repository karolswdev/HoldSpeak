import { useDesk } from "./store";

/** Betterment daily D4: Today is one page. `brief` is Today with Since
 *  yesterday open; `receipts` opens the Decisions window (2026-10-25);
 *  `follow-through` opens the Needs-you window, where its rows and verbs
 *  live, with the named action item (`followThroughId`) in its item reader. */
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

/** 2026-11-08 (the item reader): the action item a follow-through request
 *  names. The Needs-you window can mount after the request's event fires,
 *  so the id also waits here until that window takes it. */
let pendingFollowThrough: string | null = null;

/** The action item a follow-through request named, once (null when none). */
export function takeFollowThrough(): string | null {
  const id = pendingFollowThrough;
  pendingFollowThrough = null;
  return id;
}

export function openIntelligence(navigation: IntelligenceNavigation): void {
  if (navigation.view === "follow-through") {
    // Loaded on use: chairWindows reaches the window registry, which must
    // not load while this module (imported by openObject) is loading.
    // The Needs-you window opens the named action item in its item reader
    // (the event when it is mounted, `takeFollowThrough` when it mounts
    // after). The Today window ignores the event.
    pendingFollowThrough = navigation.followThroughId?.trim() || null;
    void import("./chair/chairWindows").then((m) => m.openChairWindow("chair:needs"));
    window.setTimeout(() => {
      window.dispatchEvent(new CustomEvent<IntelligenceNavigation>(INTELLIGENCE_NAVIGATE, { detail: navigation }));
    }, 0);
    return;
  }
  // The owner, 2026-10-25: Decisions is its own window, never a page that
  // takes Today's place. Every Decisions door opens that window: the record
  // when one is named, a meeting's decision by its id, else the rail (the
  // native app, 2026-11-08: one face of a decision; Today keeps no copy).
  if (navigation.view === "receipts") {
    const record = (navigation.receiptId ?? "").trim();
    const decision = (navigation.decisionId ?? "").trim();
    // Review decisions asks for the standing ones: the rail with Current only on.
    const scope = record ? `record:${record}` : decision ? `decision:${decision}` : navigation.whyOnly ? "current" : undefined;
    useDesk.getState().openSurfaceWindow("open-decisions", scope);
    return;
  }
  if (navigation.view === "brief") {
    requests += 1;
    navigation = { ...navigation, nonce: requests };
  }
  useDesk.getState().openPullout("intelligence:desk");
  window.setTimeout(() => {
    window.dispatchEvent(new CustomEvent<IntelligenceNavigation>(INTELLIGENCE_NAVIGATE, { detail: navigation }));
  }, 0);
}

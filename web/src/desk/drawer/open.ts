/** PHILO-14 A2 — Open on a drawer member: the one open grammar
 *  (`openObject.ts`); a repository opens its own window; a pull request
 *  opens its page. */
import { openDecisionRecord, openRef, refOpener } from "../openObject";
import { openPrimitive } from "../shell";
import { useDesk } from "../store";
import type { DrawerMember } from "./members";

// PHILO-14 A2b: a decision record the Room did not list opens through its
// own route (`openDecisionRecord`: the decision it was made from).
const WINDOW_REF = /^(meeting|decision|decision_record|note|artifact|thread|repository|commitment):\S/;

/** True when Open does something for this member (UX-CANON A.11). */
export function memberOpens(member: DrawerMember): boolean {
  return Boolean(member.url) || WINDOW_REF.test(member.ref) || refOpener(member.ref) !== null;
}

export function openMember(member: DrawerMember): void {
  if (member.url) {
    window.open(member.url, "_blank", "noopener");
    return;
  }
  // A commitment with no action item opens as the Room's own row opens it.
  if (member.ref.startsWith("commitment:")) {
    openPrimitive(member.ref);
    return;
  }
  if (member.ref.startsWith("decision_record:")) {
    openDecisionRecord(member.ref.slice("decision_record:".length));
    return;
  }
  if (member.ref.startsWith("repository:")) {
    useDesk.getState().openRepositoryWindow(member.ref.slice("repository:".length));
    return;
  }
  openRef(member.ref);
}

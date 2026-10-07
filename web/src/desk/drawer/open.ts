/** PHILO-14 A2 — Open on a drawer member: the one open grammar
 *  (`openObject.ts`); a repository opens its own window; a pull request
 *  opens its page. */
import { openRef, refOpener } from "../openObject";
import { useDesk } from "../store";
import type { DrawerMember } from "./members";

const WINDOW_REF = /^(meeting|decision|note|artifact|thread|repository):\S/;

/** True when Open does something for this member (UX-CANON A.11). */
export function memberOpens(member: DrawerMember): boolean {
  return Boolean(member.url) || WINDOW_REF.test(member.ref) || refOpener(member.ref) !== null;
}

export function openMember(member: DrawerMember): void {
  if (member.url) {
    window.open(member.url, "_blank", "noopener");
    return;
  }
  if (member.ref.startsWith("repository:")) {
    useDesk.getState().openRepositoryWindow(member.ref.slice("repository:".length));
    return;
  }
  openRef(member.ref);
}

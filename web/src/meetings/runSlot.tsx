// Window grammar (2026-10-24): the meeting window's run verbs (Run summary,
// Retry, Skip, Transcribe) live in its toolbar. The record's wells keep
// their logic and render the verbs through this slot: inside the meeting
// window they are portaled into the toolbar; elsewhere (a Chair card, a
// test) they render in place.
import { createContext, useContext, type ReactNode } from "react";
import { createPortal } from "react-dom";

export const MeetingRunSlotContext = createContext<HTMLElement | null>(null);

export function MeetingRunVerb({ children }: { children: ReactNode }) {
  const slot = useContext(MeetingRunSlotContext);
  return slot ? createPortal(children, slot) : <>{children}</>;
}

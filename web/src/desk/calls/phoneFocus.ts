/* Phone (PHONE-DESIGN-2026-10-28 §9): the one-shot ask for the Calls
 * window's Phone wing. Small on purpose: Today and Needs you import it
 * without the Phone wing itself. */
import { create } from "zustand";
import { openSurfaceOr } from "../shell";

/** Answer here (Needs you) and the Today line open the Calls window on the
 *  Phone wing; Answer here also sets the composer to reply to a line. */
export const usePhoneFocus = create<{
  /** A press asked for the Phone wing and no window has taken it yet. */
  pending: boolean;
  replyTo: string | null;
  /** A Calls call to open as a document (Open transcript from elsewhere). */
  callId: string | null;
  open(replyTo?: string | null): void;
  openCall(callId: string): void;
  take(): void;
  clear(): void;
}>((set) => ({
  pending: false,
  replyTo: null,
  callId: null,
  open: (replyTo = null) => set({ pending: true, replyTo, callId: null }),
  openCall: (callId) => set({ pending: true, replyTo: null, callId }),
  take: () => set({ pending: false, callId: null }),
  clear: () => set({ replyTo: null }),
}));

/** Open the Calls window on its Phone wing (optionally replying to a line). */
export function openPhoneWing(replyTo: string | null = null): void {
  usePhoneFocus.getState().open(replyTo);
  openSurfaceOr("open-calls", "/");
}


/** Open the Calls window on one call's transcript (a desk call by number). */
export function openCallTranscript(callId: string): void {
  usePhoneFocus.getState().openCall(callId);
  openSurfaceOr("open-calls", "/");
}

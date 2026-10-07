// PHILO-14 A1 — the Chair is the screen of objects (board A-1): its four
// windows (Needs you, Brief, The week, Capture) open on demand and a fresh
// desk opens with all four closed. The specs that read a window's body open
// it first, as the owner does from the screen, the Dock or Window ▸ Chair.
import { useChairWindows } from "../../chairWindows";

/** Every Chair window open; Needs you is the phone's window (393). */
export function openChairWindows(): void {
  useChairWindows.setState({ closed: {}, phone: "chair:needs", captureInRing: false });
}

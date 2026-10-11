/* PHILO-17 U17: open first run again. Setup ("Get ready") and the old
 * /welcome address show the SAME Get ready cards the fresh desk shows.
 * The server shows them while first value is owed (`arrival_required`);
 * this flag shows them on his press. The first-run handoff closes it. */
import { create } from "zustand";

export const useFirstRunOpen = create<{ open: boolean }>(() => ({ open: false }));

export function openFirstRun(): void {
  useFirstRunOpen.setState({ open: true });
}

export function closeFirstRun(): void {
  useFirstRunOpen.setState({ open: false });
}

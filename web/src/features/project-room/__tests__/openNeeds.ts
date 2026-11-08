// R1 "the brief" (owner 2026-11-08): the Room's Needs you rows open under the
// status line from its "<n> need you" word. A test that reads those rows
// presses it first, as he does.
import { fireEvent, screen } from "@testing-library/react";

export async function openNeedsYou(): Promise<void> {
  const need = await screen.findByTestId("room-status-need");
  if (need.getAttribute("aria-expanded") !== "true") fireEvent.click(need);
}

/** Open Needs you, then find one of its parts by test id. */
export async function findInNeeds(testId: string): Promise<HTMLElement> {
  await openNeedsYou();
  return screen.findByTestId(testId);
}

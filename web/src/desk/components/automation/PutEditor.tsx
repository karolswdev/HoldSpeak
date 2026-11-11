/** Betterment A6 — the Put it in editor (DESIGN §4, RECIPE A6).
 *
 * Where each result goes: My Inbox (a note, the default), Needs you (a row
 * due today), Today (Betterment daily D9: the newest result is Today's
 * Prepared block), or a saved destination: a file in a folder, GitHub, Jira,
 * Confluence, email, Slack. A destination only PREPARES the send; he presses
 * Send on the result (the egress rule). One press on a choice saves it; the
 * line folds its value in place. Each destination row says where it goes. */
import { useDestinations } from "../../surface/send";
import { putWords } from "./model";

const DESTINATION = "destination:";

/** The Put it in line's value: the destination by its saved name. */
export function PutValue({ target }: { target: string | null | undefined }) {
  const value = String(target ?? "inbox");
  if (!value.startsWith(DESTINATION)) return <>{putWords(value)}</>;
  return <DestinationValue id={value.slice(DESTINATION.length)} />;
}

function DestinationValue({ id }: { id: string }) {
  const destinations = useDestinations();
  const found = (destinations.data ?? []).find((d) => d.id === id);
  return <>{putWords(`${DESTINATION}${id}`, found?.name)}</>;
}

/* Betterment D6: a People read that failed is one line in place, in People,
 * Today and Needs you: "People could not be read" with Try again. The rest of
 * the face stays; nothing else breaks. */
import { Button } from "../../components/signal/Signal";
import "./peopleReadFailed.css";

/** The People store states that mean "it exists, but it could not be read". */
const UNREAD = new Set(["locked", "key_unavailable", "corrupt", "unavailable"]);

/** True when a hub answer's People store state is a failed read. */
export function peopleUnread(state: unknown): boolean {
  return UNREAD.has(String(state ?? ""));
}

/** Betterment daily D8: this Mac has no key store People can use (a HOME with
 * no login keychain). Not a failed read: no Try again, never a loop. */
export function peopleNotHere(state: unknown): boolean {
  return String(state ?? "") === "no_key_store";
}

export function PeopleNotHere({ testId = "people-not-here" }: { testId?: string }) {
  return <div className="people-read-failed" role="status" data-testid={testId}>
    <span className="people-read-failed-line">People is not set up on this Mac.</span>
  </div>;
}

export function PeopleReadFailed({ onRetry, detail = "", testId = "people-read-failed" }: { onRetry(): void; detail?: string; testId?: string }) {
  return <div className="people-read-failed" role="status" data-testid={testId}>
    <span className="people-read-failed-line">People could not be read. Nothing changed. Press Try again.</span>
    <Button dense variant="ghost" onClick={onRetry}>Try again</Button>
    {detail ? <span className="sr-only">{detail}</span> : null}
  </div>;
}

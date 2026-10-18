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

export function PeopleReadFailed({ onRetry, detail = "", testId = "people-read-failed" }: { onRetry(): void; detail?: string; testId?: string }) {
  return <div className="people-read-failed" role="status" data-testid={testId}>
    <span className="people-read-failed-line">People could not be read. Nothing changed. Press Try again.</span>
    <Button dense variant="ghost" onClick={onRetry}>Try again</Button>
    {detail ? <span className="sr-only">{detail}</span> : null}
  </div>;
}

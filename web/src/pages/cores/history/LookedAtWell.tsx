// betterment/capture C2 — what the summary read from memory.
// A fold under the transcript: "Looked at · N", each source a link with its
// date. It reads the run receipt's `looked_at`; none read, no fold.
import { Button } from "../../../components/signal/Signal";
import { Disclosure } from "../../../desk/surface/patterns";
import { SurfaceWell } from "../../../desk/surface/Surface";
import { openRef } from "../../../desk/openObject";
import type { LookedAt } from "../../../meetings/summaryRoute";

/** "Thu 15 Oct" from the source's date. The date is read as a calendar day
 *  (never through UTC), so it is the day the hub wrote. */
export function lookedAtDay(at: string): string {
  const match = /^(\d{4})-(\d{2})-(\d{2})/.exec(at);
  if (!match) return "";
  const day = new Date(Number(match[1]), Number(match[2]) - 1, Number(match[3]));
  const weekday = day.toLocaleDateString(undefined, { weekday: "short" });
  const month = day.toLocaleDateString(undefined, { month: "short" });
  return `${weekday} ${day.getDate()} ${month}`;
}

export function LookedAtWell({
  items,
  onOpen = openRef,
}: {
  items: LookedAt[] | undefined;
  onOpen?: (ref: string) => void;
}) {
  if (!items?.length) return null;
  const count = items.length; // never zero: an empty list draws no fold
  return (
    // C5b: the default fold (the dense one drew its body beside the trigger).
    <div className="meetings-looked-at-fold">
    <Disclosure label={`Looked at · ${count}`}>
      <SurfaceWell>
        <ul className="meetings-looked-at" data-testid="meeting-looked-at">
          {items.map((item) => (
            <li key={item.ref}>
              <Button variant="ghost" dense title={item.ref} onClick={() => onOpen(item.ref)}>
                {item.title || item.ref}
              </Button>
              {item.at ? <time dateTime={item.at.slice(0, 10)}>{lookedAtDay(item.at)}</time> : null}
            </li>
          ))}
        </ul>
      </SurfaceWell>
    </Disclosure>
    </div>
  );
}

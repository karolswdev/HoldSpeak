/** Betterment A4 — the When editor (DESIGN §4, RECIPE A4).
 *
 * Three choices, in place under the When line: a schedule (every day, every
 * weekday, a day of the week, every hour, at a time), something that happens
 * (only the events the hub can deliver: `when_events`), or only a press of
 * Run now. Looking never changes the saved choice; pressing a choice saves it
 * at once (one press, no Save). The cron the hub stores is never shown. */
import { useState } from "react";
import { Button } from "../../../components/signal/Signal";
import { CycleGadget, StringGadget } from "../../surface";
import type { AutomationWhenChoice } from "../../api";
import { schedulePick, type AutomationDetail } from "./model";

const DAYS: Array<[number, string, string]> = [
  [1, "Mon", "Monday"], [2, "Tue", "Tuesday"], [3, "Wed", "Wednesday"], [4, "Thu", "Thursday"],
  [5, "Fri", "Friday"], [6, "Sat", "Saturday"], [0, "Sun", "Sunday"],
];

/** Every half hour; a stored time off this list stays selectable. */
const TIMES = Array.from({ length: 48 }, (_, i) => {
  const value = `${String(Math.floor(i / 2)).padStart(2, "0")}:${i % 2 ? "30" : "00"}`;
  return { value, label: value };
});

const REPOSITORY = /^[\w.-]+\/[\w.-]+$/;

export function WhenEditor({
  detail,
  saving,
  onChoose,
}: {
  detail: AutomationDetail;
  /** The choice being saved (its key), while the hub answers. */
  saving: string | null;
  onChoose: (choice: AutomationWhenChoice, key: string) => void;
}) {
  const pick = schedulePick(detail.schedule);
  const scheduled = Boolean(detail.schedule && detail.schedule_enabled);
  const activeEvents = (detail.event_starts ?? []).filter((e) => e.enabled);
  const manual = !scheduled && !activeEvents.length;
  const [time, setTime] = useState(pick && pick.every !== "hour" ? pick.time : "09:00");
  const [repository, setRepository] = useState("");
  const events = detail.when_events ?? [];
  const repoReady = REPOSITORY.test(repository.trim());

  const schedule = (every: "day" | "weekday" | "week" | "hour", day?: number, at = time) => {
    const choice: AutomationWhenChoice = every === "hour"
      ? { kind: "schedule", every }
      : every === "week" ? { kind: "schedule", every, time: at, day } : { kind: "schedule", every, time: at };
    onChoose(choice, every === "week" ? `week-${day}` : every);
  };

  const on = (every: string, day?: number) =>
    scheduled && pick?.every === every && (every !== "week" || pick.day === day);

  // A new time saves the shown schedule at that time (one press).
  const changeTime = (next: string) => {
    setTime(next);
    if (scheduled && pick && pick.every !== "hour") schedule(pick.every, pick.day ?? undefined, next);
  };

  const chosen = (yes: boolean) => (yes ? "secondary" : "ghost");

  return (
    <div className="automation-when-editor" data-testid="automation-when-editor">
      <section className="automation-when-group" aria-label="On a schedule">
        <span className="automation-editor-head">On a schedule</span>
        <div className="automation-picks" role="group" aria-label="How often">
          {(["day", "weekday"] as const).map((every) => (
            <Button key={every} dense variant={chosen(on(every))} aria-pressed={on(every)}
              loading={saving === every} onClick={() => schedule(every)}>
              {every === "day" ? "Every day" : "Every weekday"}
            </Button>
          ))}
          <Button dense variant={chosen(on("hour"))} aria-pressed={on("hour")}
            loading={saving === "hour"} onClick={() => schedule("hour")}>
            Every hour
          </Button>
        </div>
        <div className="automation-picks" role="group" aria-label="Every week on">
          {DAYS.map(([day, short, long]) => (
            <Button key={day} dense variant={chosen(on("week", day))} aria-pressed={on("week", day)}
              aria-label={`Every ${long}`} loading={saving === `week-${day}`}
              onClick={() => schedule("week", day)}>
              {short}
            </Button>
          ))}
        </div>
        <div className="automation-when-time">
          <span className="automation-editor-caption">At</span>
          <CycleGadget label="At" value={time} options={TIMES} onChange={changeTime} />
        </div>
      </section>

      {events.length ? (
        <section className="automation-when-group" aria-label="When something happens">
          <span className="automation-editor-head">When something happens</span>
          <StringGadget
            label="GitHub repository"
            caption
            value={repository}
            onChange={setRepository}
            placeholder="owner/name"
            mic={false}
          />
          <div className="automation-picks" role="group" aria-label="Events">
            {events.map((event) => {
              const active = activeEvents.some((e) => e.event_pattern === event.event_pattern);
              return (
                <Button key={event.id} dense variant={chosen(active)} aria-pressed={active}
                  disabled={!repoReady} loading={saving === event.id}
                  onClick={() => onChoose({ kind: "event", event_id: event.id, repository: repository.trim() }, event.id)}>
                  {event.words}
                </Button>
              );
            })}
          </div>
        </section>
      ) : null}

      <section className="automation-when-group" aria-label="Only when I press Run now">
        <div className="automation-picks">
          <Button dense variant={chosen(manual)} aria-pressed={manual} loading={saving === "manual"}
            onClick={() => onChoose({ kind: "manual" }, "manual")}>
            Only when I press Run now
          </Button>
        </div>
      </section>
    </div>
  );
}

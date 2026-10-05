/* First run, option A "One screen" — Ready (owner ratified 2026-10-05,
 * canvas YDTpkaJqFs3hyrZ4g581Mx §1, artboard onb-A-ready). When every
 * step is done: "Ready, <his name>", one success chip per step, and three
 * verbs from his own data. "Record <next meeting> · <time>" arms the
 * recording of the next meeting on his calendar; with no meeting there is
 * no such verb (no dead verbs). Each verb hands off to the Desk. */
import { useState } from "react";
import { ReadyStrip, StartVerb, StartVerbs, StateChip, heardWordCount, countToken, type ReadyStripItem } from "../surface";
import { readDurableDraft, writeDurableDraft } from "../../lib/durableDraft";
import { openSurfaceOr } from "../shell";
import { useDesk } from "../store";
import { DESK_APPLICATIONS } from "../applications";
import { meetingClock, type CalendarStep } from "./calendarStep";
import { PROVIDER_NAME, type ConnectionsStep } from "./connectionsStep";

/** The Ask composer's draft scope (AskPanel `useDurableDraft("desk-ask")`). */
const ASK_SCOPE = "desk-ask";
export const ASK_THIS_WEEK = "What is on my calendar this week?";
/** The Ask application's own glyph (the manifest is the one source). */
const ASK_GLYPH = DESK_APPLICATIONS.find((app) => app.action === "ask")?.glyph ?? "";

/** "Karol Sane" -> "Karol". */
export function firstName(name: string): string {
  return name.trim().split(/\s+/)[0] ?? "";
}

export function readyItems({
  heardText,
  calendar,
  connections,
}: {
  heardText: string;
  calendar: Pick<CalendarStep, "week">;
  connections: Pick<ConnectionsStep, "providers">;
}): ReadyStripItem[] {
  const words = countToken(heardWordCount(heardText), "WORD");
  const sendTo = connections.providers.map((p) => PROVIDER_NAME[p].toUpperCase());
  return [
    { key: "local-ai", label: "LOCAL AI · ON DEVICE" },
    { key: "heard", label: words ? `HEARD · ${words}` : "HEARD" },
    { key: "calendar", label: calendar.week > 0 ? `CALENDAR · ${calendar.week} THIS WEEK` : "CALENDAR · IN USE" },
    ...(sendTo.length ? [{ key: "send-to", label: `SEND TO · ${sendTo.join(" · ")}` }] : []),
  ];
}

export function Ready({
  name,
  heardText,
  calendar,
  connections,
  finish,
  busy,
}: {
  name: string;
  heardText: string;
  calendar: CalendarStep;
  connections: ConnectionsStep;
  finish: (then?: () => void | Promise<unknown>) => Promise<boolean>;
  busy: boolean;
}) {
  const [pressed, setPressed] = useState<"" | "record" | "dictate" | "ask">("");
  const [notArmed, setNotArmed] = useState(false);
  const next = calendar.next;
  const short = firstName(name);

  const record = async () => {
    if (!next) return;
    setPressed("record");
    setNotArmed(false);
    // Arm first: a refusal stays on this face, named.
    const armed = next.armed_schedule_id ? true : await useDesk.getState().armEventRecording(next.id);
    if (!armed) {
      setNotArmed(true);
      setPressed("");
      return;
    }
    await finish();
    setPressed("");
  };
  const dictate = async () => {
    setPressed("dictate");
    await finish(() => openSurfaceOr("dictate", "/dictation"));
    setPressed("");
  };
  const ask = async () => {
    setPressed("ask");
    await finish(() => {
      if (!readDurableDraft(ASK_SCOPE)?.text.trim()) writeDurableDraft(ASK_SCOPE, ASK_THIS_WEEK);
      useDesk.getState().openAsk();
    });
    setPressed("");
  };

  return (
    <div className="firstrun-ready" data-testid="firstrun-ready">
      <h1 className="surface-display firstrun-heading">{short ? `Ready, ${short}` : "Ready"}</h1>
      <ReadyStrip items={readyItems({ heardText, calendar, connections })} />
      <StartVerbs ariaLabel="Start">
        {next ? (
          <StartVerb
            glyph="◉"
            variant="primary"
            loading={pressed === "record"}
            disabled={busy}
            onClick={() => void record()}
          >
            {`Record ${next.title} · ${meetingClock(next.starts_at)}`}
          </StartVerb>
        ) : null}
        <StartVerb
          glyph="◖"
          variant={next ? "secondary" : "primary"}
          loading={pressed === "dictate"}
          disabled={busy}
          onClick={() => void dictate()}
        >
          Dictate
        </StartVerb>
        <StartVerb glyph={ASK_GLYPH} loading={pressed === "ask"} disabled={busy} onClick={() => void ask()}>
          Ask about this week
        </StartVerb>
      </StartVerbs>
      {notArmed ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT ARMED" />
          <span className="surface-token" data-tone="danger">
            {next ? next.title.toUpperCase() : ""}
          </span>
        </div>
      ) : null}
    </div>
  );
}

/* First run, option A "One screen" — the Calendar card (owner ratified
 * 2026-10-05, canvas YDTpkaJqFs3hyrZ4g581Mx §1). The calendars macOS
 * already has, one "Use it" each (THIS DEVICE); or one calendar link
 * (its host named once typed). The macOS prompt shows only on his press. */
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import { EgressChip, Receipt, StateChip, StringGadget, SurfaceLedgerRow, countToken } from "../surface";
import { egressFor } from "../surface/egress";
import { Card } from "./Card";
import { hostOf, meetingClock, stateCount, type CalendarCandidate, type CalendarStep } from "./calendarStep";

function rowEgress(row: CalendarCandidate): { label: string; scope: "local" | "cloud" } {
  if (row.kind === "macos" || !row.egress_host) return { label: "THIS DEVICE", scope: "local" };
  return { label: row.egress_host.toUpperCase(), scope: row.lamp === "cloud" ? "cloud" : "local" };
}

/** `14 EVENTS · NEXT ATLAS WEEKLY 10:30`, each part only when known. */
export function calendarReceipt(week: number, next: { title: string; starts_at: string } | null): string {
  return [
    countToken(week, "EVENT"),
    next ? `NEXT ${next.title.toUpperCase()} ${meetingClock(next.starts_at)}`.trim() : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

export function CalendarCard({ step, lit }: { step: CalendarStep; lit: boolean }) {
  const [url, setUrl] = useState("");
  const host = hostOf(url);
  const typed = egressFor(host);
  const { macos, rows, inUse, busy, failure } = step;
  const receipt = inUse ? calendarReceipt(step.week, step.next) : "";
  const found = stateCount("FOUND", rows.length);
  const add = async () => {
    if (!host || busy) return;
    if (await step.addUrl(url.trim())) setUrl("");
  };
  return (
    <Card
      title="Calendar"
      testId="firstrun-calendar"
      lit={lit}
      selected={inUse}
      state={
        inUse ? (
          <StateChip state="success" label="IN USE" icon="●" />
        ) : found ? (
          <StateChip state="success" label={found} icon="●" />
        ) : null
      }
    >
      {step.unread ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="unreachable" label="CAN'T CHECK" />
          <span className="firstrun-reason">{step.unread}</span>
          <Button dense variant="secondary" onClick={() => void step.read()}>
            Try again
          </Button>
        </div>
      ) : null}
      {macos?.can_request && !inUse ? (
        <div className="firstrun-fail" data-testid="firstrun-calendar-ask">
          <Button
            variant="primary"
            loading={busy === "access"}
            disabled={busy !== null}
            onClick={() => void step.requestAccess()}
          >
            Allow calendar access
          </Button>
          <EgressChip label="THIS DEVICE" scope="local" />
        </div>
      ) : null}
      {step.notAllowed && !inUse ? (
        <div className="firstrun-fail" role="alert" data-testid="firstrun-calendar-denied">
          <StateChip state="failure" label="CALENDAR · NOT ALLOWED" />
          {macos?.state === "write_only" ? <span className="surface-token">WRITE ONLY</span> : null}
          {/* No verb: the desk cannot open System Settings (the no-exit
              law; no hub route opens the Calendars pane). Withheld, never dead. */}
        </div>
      ) : null}
      {rows.length ? (
        <ul className="concierge-found-list firstrun-ledger" aria-label="Found calendars">
          {rows.map((row) => {
            const egress = rowEgress(row);
            return (
              <SurfaceLedgerRow
                key={row.id}
                lead={<span className="concierge-group-glyph">▦</span>}
                primary={<span className="concierge-group-name">{row.label}</span>}
                cells={
                  <span className="concierge-found-cells" data-testid="firstrun-calendar-row">
                    {row.account && row.account !== row.egress_host ? (
                      <span className="concierge-token">{row.account}</span>
                    ) : null}
                    <span className="concierge-cloud-actions">
                      {row.in_use ? (
                        <StateChip state="success" label="IN USE" icon="●" />
                      ) : row.off ? (
                        /* Configured but turned off: "Use it" would add
                           nothing (the source is there), so no verb here. */
                        <span className="surface-token">OFF IN SETTINGS</span>
                      ) : row.verb ? (
                        <Button
                          dense
                          variant="primary"
                          loading={busy === row.id}
                          disabled={busy !== null}
                          aria-label={`Use ${row.label}`}
                          onClick={() => void step.use(row)}
                        >
                          Use it
                        </Button>
                      ) : null}
                    </span>
                    <span className="concierge-found-line2">
                      <EgressChip label={egress.label} scope={egress.scope} />
                    </span>
                  </span>
                }
                expands={false}
                wrap
              />
            );
          })}
        </ul>
      ) : null}
      {receipt ? <Receipt status="ok" label={receipt} /> : null}
      {!inUse ? (
        <label className="firstrun-field firstrun-stretch">
          <span className="firstrun-caption">OR A CALENDAR URL</span>
          <span className="firstrun-urlrow">
            <StringGadget
              label="Calendar URL"
              value={url}
              onChange={setUrl}
              placeholder="https://…/calendar.ics"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  void add();
                }
              }}
            />
            <Button
              dense
              variant="secondary"
              loading={busy === "add"}
              disabled={!host || busy !== null}
              onClick={() => void add()}
            >
              Add
            </Button>
          </span>
          {host ? <EgressChip label={typed.label.toUpperCase()} scope={typed.scope} /> : null}
        </label>
      ) : null}
      {failure?.kind === "cant_read" ? (
        <div className="firstrun-fail" role="alert" data-testid="firstrun-calendar-cant-read">
          <StateChip state="failure" label="CAN'T READ" />
          <span className="surface-token" data-tone="danger">
            {failure.reason}
          </span>
        </div>
      ) : failure?.kind === "refused" ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT IN USE" />
          <span className="firstrun-reason">{failure.reason}</span>
        </div>
      ) : null}
    </Card>
  );
}

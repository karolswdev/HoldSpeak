/* First run, option A "One screen" — the Calendar card (owner ratified
 * 2026-10-05, canvas YDTpkaJqFs3hyrZ4g581Mx §1). The calendars macOS
 * already has, one "Use it" each (THIS DEVICE); or one calendar link
 * (its host named once typed). The macOS prompt shows only on his press. */
import { useState, type ReactNode } from "react";
import { Button } from "../../components/signal/Signal";
import { DotWord, EgressChip, GadgetGroup, Receipt, StateChip, StringGadget, SurfaceLedgerRow, countToken } from "../surface";
import { egressFor } from "../surface/egress";
import { Card } from "./Card";
import { hostOf, meetingClock, stateCount, type CalendarCandidate, type CalendarStep } from "./calendarStep";
import { Token } from "../surface/Token";

function rowEgress(row: CalendarCandidate): { label: string; scope: "local" | "cloud" } {
  if (row.kind === "macos" || !row.egress_host) return { label: "This device", scope: "local" };
  return { label: row.egress_host, scope: row.lamp === "cloud" ? "cloud" : "local" };
}

/** `14 EVENTS · NEXT ATLAS WEEKLY 10:30`, each part only when known. */
export function calendarReceipt(week: number, next: { title: string; starts_at: string } | null): string {
  return [
    countToken(week, "EVENT"),
    next ? `NEXT ${next.title} ${meetingClock(next.starts_at)}`.trim() : null,
  ]
    .filter(Boolean)
    .join(" · ");
}

/** Settings uses the same chooser without the first-use card and explanation. */
function CalendarFrame({ compact, children, ...card }: { compact: boolean; children: ReactNode; title: string; line: string; testId: string; lit: boolean; selected: boolean; state: ReactNode }) {
  return compact ? (
    <div data-testid={card.testId}>
      <GadgetGroup label="Choose calendar" material="inset">
        <div className="connections-calendar-chooser">
          {card.state ? <div className="firstrun-fail">{card.state}</div> : null}
          {children}
        </div>
      </GadgetGroup>
    </div>
  ) : <Card {...card}>{children}</Card>;
}

export function CalendarCard({ step, lit, reselectNative = false, onUsed, beforeUse }: {
  step: CalendarStep;
  lit: boolean;
  reselectNative?: boolean;
  onUsed?: () => Promise<void>;
  beforeUse?: () => Promise<boolean>;
}) {
  const [url, setUrl] = useState("");
  const host = hostOf(url);
  const typed = egressFor(host);
  const { macos, rows, inUse, busy, failure } = step;
  const receipt = inUse ? calendarReceipt(step.week, step.next) : "";
  const found = stateCount("FOUND", rows.length);
  // PHILO-17: "OR" only when another choice is on the card above the link.
  const nativeAccessVisible = !inUse || reselectNative;
  const asking = Boolean(macos?.can_request && nativeAccessVisible);
  const another = rows.length > 0 || asking;
  const nativeLoading = reselectNative && !step.loaded;
  const nativeEmpty = reselectNative && step.loaded && !step.unread && !rows.length && !asking && !step.notAllowed;
  const nativeUnavailable = macos?.state === "unavailable";
  const add = async () => {
    if (!host || busy) return;
    if (beforeUse && !(await beforeUse())) return;
    if (await step.addUrl(url.trim())) {
      setUrl("");
      await onUsed?.();
    }
  };
  return (
    <CalendarFrame
      compact={reselectNative}
      title="Calendar"
      line="Reads your meetings, so HoldSpeak can record the next one."
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
          <Button dense variant="secondary"
            loading={reselectNative && busy === "check"}
            disabled={reselectNative && busy !== null}
            onClick={() => void (reselectNative ? step.checkAgain() : step.read())}>
            {reselectNative ? "Retry" : "Try again"}
          </Button>
        </div>
      ) : null}
      {nativeLoading || nativeEmpty ? (
        <div className="firstrun-fail">
          <StateChip
            state={nativeEmpty && nativeUnavailable ? "unreachable" : "idle"}
            label={nativeLoading ? "CHECKING CALENDARS" : nativeUnavailable ? "CALENDARS UNAVAILABLE" : "NO CALENDARS FOUND"}
          />
          {nativeEmpty ? (
            <Button dense variant="secondary" loading={busy === "check"} disabled={busy !== null}
              onClick={() => void step.checkAgain()}>
              Check again
            </Button>
          ) : null}
        </div>
      ) : null}
      {macos?.can_request && nativeAccessVisible ? (
        <div className="firstrun-fail" data-testid="firstrun-calendar-ask">
          <Button
            variant="primary"
            loading={busy === "access"}
            disabled={busy !== null}
            onClick={() => void step.requestAccess()}
          >
            Allow calendar access
          </Button>
          <EgressChip label="This device" scope="local" />
        </div>
      ) : null}
      {step.notAllowed && nativeAccessVisible ? (
        <div className="firstrun-fail" role="alert" data-testid="firstrun-calendar-denied">
          <StateChip state="failure" label="Calendar not allowed" />
          {macos?.state === "write_only" ? <DotWord tone="warn">Write only</DotWord> : null}
          {/* PHILO-15 04 (gap 12): the way forward. His press opens System
              Settings > Privacy & Security > Calendars; Check again reads
              the access state after he changes it there. */}
          <Button
            variant="primary"
            loading={busy === "settings"}
            disabled={busy !== null}
            onClick={() => void step.openSettings()}
            data-testid="firstrun-calendar-settings"
          >
            Open System Settings
          </Button>
          <Button
            variant="secondary"
            loading={busy === "check"}
            disabled={busy !== null}
            onClick={() => void step.checkAgain()}
            data-testid="firstrun-calendar-check"
          >
            Check again
          </Button>
          <EgressChip label="This device" scope="local" />
          {step.settingsFailed ? <DotWord tone="fail" data-testid="firstrun-calendar-settings-failed">Could not open System Settings · Nothing changed · Open it yourself, then press Check again</DotWord> : null}
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
                      {reselectNative && row.kind === "macos" && (row.in_use || row.off) ? (
                        <Button dense variant="secondary" loading={busy === row.id} disabled={busy !== null}
                          aria-label={`Refresh ${row.label} name`}
                          onClick={() => void (async () => {
                            if (beforeUse && !(await beforeUse())) return;
                            if (await step.use(row)) await onUsed?.();
                          })()}>Refresh name</Button>
                      ) : row.in_use ? (
                        <StateChip state="success" label="IN USE" icon="●" />
                      ) : row.off ? (
                        /* Configured but turned off: "Use it" would add
                           nothing (the source is there), so no verb here. */
                        <Token className="surface-token">OFF IN SETTINGS</Token>
                      ) : row.verb ? (
                        <Button
                          dense
                          variant="primary"
                          loading={busy === row.id}
                          disabled={busy !== null}
                          aria-label={`Use ${row.label}`}
                          onClick={() => void (async () => {
                            if (beforeUse && !(await beforeUse())) return;
                            if (await step.use(row)) await onUsed?.();
                          })()}
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
      {!inUse || reselectNative ? (
        <label className="firstrun-field firstrun-stretch">
          <span className="firstrun-caption">{another ? "OR A CALENDAR URL" : "CALENDAR URL"}</span>
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
          {host ? <EgressChip label={typed.label} scope={typed.scope} /> : null}
        </label>
      ) : null}
      {failure?.kind === "cant_read" ? (
        <div className="firstrun-fail" role="alert" data-testid="firstrun-calendar-cant-read">
          <StateChip state="failure" label="CAN'T READ" />
          <Token className="surface-token" data-tone="danger">
            {failure.reason}
          </Token>
        </div>
      ) : failure?.kind === "refused" ? (
        <div className="firstrun-fail" role="alert">
          <StateChip state="failure" label="NOT IN USE" />
          <span className="firstrun-reason">{failure.reason}</span>
        </div>
      ) : null}
    </CalendarFrame>
  );
}

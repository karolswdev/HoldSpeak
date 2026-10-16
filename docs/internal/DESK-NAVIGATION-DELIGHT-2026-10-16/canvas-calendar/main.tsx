// Direction only: production library, declared synthetic extraction payload.
import { useState } from "react";
import { createRoot } from "react-dom/client";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";
import { DeskWindowFrame } from "@w/desk/components/DeskWindow";
import { Button } from "@w/components/signal/Signal";
import { CycleGadget, StringGadget } from "@w/desk/surface/gadgets";
import {
  ConfirmVerb,
  SurfaceSection,
  SurfaceLedger,
  SurfaceLedgerRow,
} from "@w/desk/surface/Surface";
import { StateChip } from "@w/desk/surface";
import { SurfaceFooter } from "@w/desk/surface/SurfaceFooter";
import "./canvas.css";

const noop = () => {};
const face = new URLSearchParams(location.search).get("face") || "review";
const pending = face === "pending";
const failed = face === "failure";
const weekdays = [
  "monday",
  "tuesday",
  "wednesday",
  "thursday",
  "friday",
  "saturday",
  "sunday",
];
const sample = [
  {
    id: "sample-release",
    title: "Release review",
    weekday: "monday",
    start_time: "09:00",
    end_time: "09:30",
    location: "Room 1",
  },
  {
    id: "sample-architecture",
    title: "Architecture sync",
    weekday: "friday",
    start_time: "14:00",
    end_time: "15:00",
    location: "",
  },
];
function CalendarDirection() {
  const [events, setEvents] = useState(sample);
  const [anchor, setAnchor] = useState("2026-10-19");
  const patch = (id: string, change: Partial<(typeof sample)[number]>) =>
    setEvents(
      events.map((event) =>
        event.id === id ? { ...event, ...change } : event,
      ),
    );
  return (
    <div className="calendar-snapshot-review">
      <fieldset className="calendar-snapshot-fields" disabled={pending}>
        <SurfaceSection label="Week anchor">
          <div className="calendar-snapshot-anchor">
            <StringGadget
              label="Week of"
              caption
              value={anchor}
              onChange={setAnchor}
              disabled={pending}
            />
          </div>
        </SurfaceSection>
        <SurfaceSection label={`${events.length} events`}>
          <div className="calendar-snapshot-events">
            <SurfaceLedger label="Events">
              <ul className="surface-ledger-rows">
                {events.map((event, index) => (
                  <SurfaceLedgerRow
                    key={event.id}
                    primary={`Event ${index + 1}`}
                    open
                    expands={false}
                    trailing={
                      <ConfirmVerb
                        label="Remove"
                        confirmLabel="Remove?"
                        ariaLabel={`Remove event ${index + 1}`}
                        disabled={pending}
                        onConfirm={() =>
                          setEvents(events.filter((row) => row.id !== event.id))
                        }
                      />
                    }
                  >
                    <div className="calendar-snapshot-editor">
                      <StringGadget
                        label={`Event ${index + 1} title`}
                        caption
                        value={event.title}
                        onChange={(title) => patch(event.id, { title })}
                        disabled={pending}
                      />
                      <div className="calendar-snapshot-schedule">
                        <div className="calendar-snapshot-day">
                          <span>Day</span>
                          <CycleGadget
                            label={`Event ${index + 1} weekday`}
                            value={event.weekday}
                            onChange={(weekday) => patch(event.id, { weekday })}
                            disabled={pending}
                            options={weekdays.map((value) => ({
                              value,
                              label:
                                value.charAt(0).toUpperCase() + value.slice(1),
                            }))}
                          />
                        </div>
                        <StringGadget
                          label={`Event ${index + 1} start`}
                          caption
                          value={event.start_time}
                          mic={false}
                          onChange={(start_time) =>
                            patch(event.id, { start_time })
                          }
                          disabled={pending}
                        />
                        <StringGadget
                          label={`Event ${index + 1} end`}
                          caption
                          value={event.end_time}
                          mic={false}
                          onChange={(end_time) => patch(event.id, { end_time })}
                          disabled={pending}
                        />
                      </div>
                      <StringGadget
                        label={`Event ${index + 1} location`}
                        caption
                        value={event.location}
                        onChange={(location) => patch(event.id, { location })}
                        disabled={pending}
                      />
                    </div>
                  </SurfaceLedgerRow>
                ))}
              </ul>
            </SurfaceLedger>
          </div>
        </SurfaceSection>
      </fieldset>
      <SurfaceFooter
        receipt={
          pending ? (
            <StateChip state="idle" label="Saving" />
          ) : failed ? (
            <span
              className="surface-footer-receipt-line"
              data-wrap=""
              data-tone="danger"
              role="alert"
            >
              <StateChip state="failure" label="CAN'T SAVE" />{" "}
              <span className="surface-token" data-chip="" data-wrap="">
                Calendar unavailable
              </span>
            </span>
          ) : undefined
        }
        verbs={
          <Button dense variant="primary" loading={pending} onClick={noop}>
            {failed ? "Retry" : "Confirm"}
          </Button>
        }
      />
    </div>
  );
}
createRoot(document.getElementById("root")!).render(
  <RuntimeBusProvider>
    <main className="desk-next direction-floor">
      <DeskWindowFrame
        id={`calendar-direction-${face}`}
        title="Calendar snapshot"
        label="Calendar snapshot"
        glyph="▦"
        minW={320}
        defaultW={660}
        defaultH={800}
        open
        entrance={false}
        onClose={noop}
        className="desk-surface-window"
      >
        <div className="desk-surface-body direction-body">
          <CalendarDirection />
        </div>
      </DeskWindowFrame>
    </main>
  </RuntimeBusProvider>,
);

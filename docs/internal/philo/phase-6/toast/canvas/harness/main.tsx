/* PHILO-6-03 placement canvas — composition only.
 *
 * The Arrival shell, summary well, ledger row, capture bar controls, and
 * aftercare card are the production species. The proposal puts the card in a
 * normal-flow slot immediately before CaptureBar; the today board preserves
 * the current fixed position for comparison. No product file is changed by
 * this harness.
 */
import { createRoot } from "react-dom/client";
import { useLayoutEffect } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import "@w/desk/chair/chair.css";
import "./main.css";
import { Button } from "@w/components/signal/Signal";
import { MicButton } from "@w/desk/components/MicButton";
import { SYSTEM } from "@w/desk/systemSprites";
import { MeetingSummarySlab } from "@w/meetings/MeetingSummarySlab";
import { Chair } from "@w/desk/chair/Chair";
import { SurfaceLedger, SurfaceLedgerRow, SurfaceSection } from "@w/desk/surface";
import { BriefEgress } from "@w/desk/chair/briefEgress";
import { DeskChrome } from "@w/desk/components/DeskChrome";
import { Dock } from "@w/desk/components/DeskWindow";
import { RuntimeBusProvider } from "@w/runtime/RuntimeBus";

/* Keep shell-only reads local to this canvas. The product walk owns real hub
 * traffic; this placement board only needs the shell to mount its species. */
const nativeFetch = window.fetch.bind(window);
window.fetch = async (input, init) => {
  const url = typeof input === "string" ? input : input.url;
  if (url.startsWith("/api/")) {
    return new Response("{}", {
      status: 200,
      headers: { "content-type": "application/json" },
    });
  }
  return nativeFetch(input, init);
};

const SUMMARY =
  "The Synthetic Architect Meeting established three decisions: using SQLite for the local meeting ledger, keeping summary retrieval on the local desk after a hub restart, and using recorded provider replies for isolated rig tests. Action items were assigned to Mayyachan, Leo Martinez, and Priya Shah with specific deadlines or tasks.";
const LONG_SUMMARY = `${SUMMARY} The owner also recorded the migration boundary, the recovery check, and the follow-up review window so the summary remains a deliberately longer readable region for placement fencing.`;

function MeetingSummary({ open, long }: { open: boolean; long: boolean }) {
  return (
    <SurfaceSection label="MEETINGS · 1">
      <SurfaceLedger count={null} cols="room">
        <SurfaceLedgerRow
          primary="Architecture review"
          trailing={<Button variant="ghost" dense>Open</Button>}
          open={open}
          expands={false}
          wrap
          data-testid="arrival-meeting-row"
        >
          {open ? (
            <div data-testid="arrival-summary">
              <MeetingSummarySlab
                intel={{ summary: long ? LONG_SUMMARY : SUMMARY, topics: [] }}
                receipt={null}
              />
            </div>
          ) : null}
        </SurfaceLedgerRow>
      </SurfaceLedger>
    </SurfaceSection>
  );
}

function ArrivalPreamble() {
  return (
    <>
      <SurfaceSection label="NO CALENDAR" actions={<Button variant="ghost" dense>Connect calendar</Button>} />
      <SurfaceSection
        label="BRIEF"
        actions={
          <>
            <BriefEgress />
            <Button variant="ghost" dense>Generate</Button>
          </>
        }
      >
        <span className="arrival-brief-empty">No brief yet</span>
      </SurfaceSection>
    </>
  );
}

function CanvasPressedMic() {
  // Canvas fixture only: this is the existing pressed MicButton visual
  // rendered from the production Button and listening sprite. It never calls
  // the microphone or backend; the capture board needs a distinct state.
  return (
    <Button
      variant="chrome"
      className="desk-mic gadget-transport-key is-listening"
      aria-label="Stop listening"
      aria-pressed="true"
      data-testid="canvas-pressed-mic"
      onClick={() => undefined}
    >
      <span className="gadget-transport-glyph" aria-hidden="true">
        <img
          src={SYSTEM.micListening}
          alt=""
          width={16}
          height={16}
          className="desk-chrome-sprite"
          draggable={false}
        />
      </span>
      <span className="gadget-transport-word">Talk</span>
    </Button>
  );
}

function CaptureBar({ pressed }: { pressed: boolean }) {
  return (
    <footer className="arrival-capture-bar" data-testid="arrival-capture-bar">
      <span className="arrival-capture-talk">
        {pressed ? (
          <CanvasPressedMic />
        ) : (
          <MicButton onText={() => undefined} label="Talk" variant="transport" />
        )}
      </span>
      <Button variant="ghost">Write a thought</Button>
      <Button variant="ghost">Record meeting</Button>
      <Button variant="ghost">Schedule</Button>
    </footer>
  );
}

function AftercareCard({ flow }: { flow: boolean }) {
  return (
    <aside
      className={`ambient-preview ambient-aftercare ${flow ? "toast-canvas-flow-card" : "toast-canvas-today"}`}
      aria-label="Meeting aftercare"
      data-testid="toast-card"
    >
      <span className="signal-eyebrow">Meeting ready</span>
      <strong>Architecture review</strong>
      <p>3 open</p>
      <div className="button-row">
        <Button dense variant="primary">Open proposals</Button>
        <Button dense variant="ghost">Dismiss</Button>
      </div>
    </aside>
  );
}

function Canvas() {
  const params = new URLSearchParams(location.search);
  const board = params.get("board") ?? "today";
  const longSummary = params.get("summary") === "long";
  const pressedCapture = board === "capture";
  const flow = board !== "today";
  const summaryOpen = board !== "proposed";
  const measuredScroll = longSummary
    ? 330
    : board === "proposed"
      ? 100
    : board === "summary-open" || board === "capture"
      ? 266
      : 0;
  useLayoutEffect(() => {
    if (!measuredScroll) return;
    const chair = document.querySelector<HTMLElement>('[data-testid="chair"]');
    chair?.scrollTo({ top: measuredScroll, behavior: "instant" as ScrollBehavior });
  }, [measuredScroll]);
  return (
    <RuntimeBusProvider>
      <div className="toast-canvas desk-next" data-testid="toast-canvas">
        <DeskChrome showDailyStarts={false} />
        <Chair>
          <h1 className="toast-canvas-headline">Nothing needs you</h1>
          <ArrivalPreamble />
          <MeetingSummary open={summaryOpen} long={longSummary} />
          {flow ? <div className="toast-canvas-flow-slot"><AftercareCard flow /></div> : null}
          <CaptureBar pressed={pressedCapture} />
        </Chair>
        <Dock />
        {!flow ? <AftercareCard flow={false} /> : null}
      </div>
    </RuntimeBusProvider>
  );
}

createRoot(document.getElementById("root")!).render(<Canvas />);

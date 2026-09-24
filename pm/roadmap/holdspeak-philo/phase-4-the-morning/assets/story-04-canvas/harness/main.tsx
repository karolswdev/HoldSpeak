/* PHILO-4-04 canvas harness — design proposal only.
 *
 * The quiet branch is composed from the actual desk species: Chair, the
 * library SurfaceSection, Signal Button, BriefEgress, and the production CSS.
 * There is no product implementation here. The six rows below are the
 * round-five `_compose` acceptance fixture, not a full generate. In the full
 * producer c1 is filed in THIS WEEK; it remains in this fixture only because
 * this story preserves the accepted six-row headline exactly.
 *
 * The shelf exposes a state, not a durable handled timestamp. The proposal
 * therefore says ALL 6 HANDLED and uses only the server-provided generated
 * date. It does not invent a triage time.
 */
import { createRoot } from "react-dom/client";
import type { ReactNode } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { Chair } from "@w/desk/chair/Chair";
import { BriefEgress, briefReceipt } from "@w/desk/chair/briefEgress";
import { SurfaceSection } from "@w/desk/surface";
import { Button } from "@w/components/signal/Signal";

type FixtureItem = { id: string; text: string; section: string };

/* Source: story-01-canvas round-five producer fixture. Keep this list next to
 * the exact stored headline so a canvas reviewer can see what ALL 6 names. */
const FIXTURE_ITEMS: FixtureItem[] = [
  { id: "m1", section: "changed", text: "Meeting recorded: Platform sync" },
  { id: "o1", section: "waiting", text: "Overdue: Send the vendor review notes" },
  { id: "u1", section: "waiting", text: "Unassigned: Draft the migration runbook" },
  { id: "l1", section: "waiting", text: "Open loop: Rate limits for the partner API" },
  { id: "d2", section: "decisions", text: "Review decision: Adopt the one desk bus" },
  { id: "c1", section: "decisions", text: "Commitment due 2026-09-25: Send the Q4 plan to Dana" },
];

const STORED_HEADLINE = "1 thing changed, 3 things waiting, 2 decisions waiting.";
const PERIOD_LABEL = "SEP 21 – 23";
const GENERATED_LABEL = "GENERATED SEP 23 17:40";
const GENERATED_SNAPSHOT = `SNAPSHOT · ${PERIOD_LABEL} · ${GENERATED_LABEL}`;
const HANDLED_LINE = `ALL ${FIXTURE_ITEMS.length} HANDLED`;
const GENERATION_RECEIPT = briefReceipt({
  sections: {
    changed: [FIXTURE_ITEMS[0]],
    waiting: FIXTURE_ITEMS.slice(1, 4),
    decisions: FIXTURE_ITEMS.slice(4),
  },
  generated_at: "2026-09-23T17:40:00",
});

function HeadVerbs({ busy = false }: { busy?: boolean }) {
  return (
    <>
      <BriefEgress />
      <Button
        variant="ghost"
        dense
        disabled={busy}
        data-testid="arrival-brief-generate"
      >
        Generate
      </Button>
    </>
  );
}

function DateLine() {
  /* This is the same output as ChairHome's BriefDate: both labels come from
   * the monday-brief route and are derived from durable generated_at. */
  return (
    <span className="surface-receipt-line" data-testid="arrival-brief-date">
      {`${PERIOD_LABEL} · ${GENERATED_LABEL}`}
    </span>
  );
}

function SnapshotMarker() {
  return (
    <span
      className="surface-receipt-line"
      data-testid="arrival-brief-date"
      data-canvas-snapshot="true"
    >
      {GENERATED_SNAPSHOT}
    </span>
  );
}

function HandledReceipt() {
  return (
    <span
      className="surface-receipt-line"
      data-testid="arrival-brief-handled"
    >
      {HANDLED_LINE}
    </span>
  );
}

function GestureReceipt() {
  /* Same-day idempotent POST receipt from the real briefReceipt species. Its
   * time is the original generated_at, not a triage timestamp; this tests
   * coexistence of the durable state line and the existing receipt. */
  return (
    <span
      className="surface-receipt-line"
      role="status"
      data-testid="arrival-brief-receipt"
    >
      {GENERATION_RECEIPT}
    </span>
  );
}

function Generating() {
  return (
    <span
      className="surface-receipt-line"
      role="status"
      data-testid="arrival-brief-generating"
    >
      GENERATING…
    </span>
  );
}

function Failed() {
  return (
    <span className="arrival-brief-failed">
      <span
        className="surface-receipt-line"
        role="status"
        data-tone="danger"
        data-testid="arrival-brief-generate-failed"
      >
        BRIEF DID NOT GENERATE · HTTP 500
      </span>
    </span>
  );
}

function OriginalQuiet() {
  return (
    <SurfaceSection label="BRIEF" actions={<HeadVerbs />}>
      <span
        className="arrival-brief-headline"
        data-testid="arrival-brief-headline"
      >
        {STORED_HEADLINE}
      </span>
      <DateLine />
    </SurfaceSection>
  );
}

function OneLineProposed() {
  return (
    <SurfaceSection label="BRIEF" actions={<HeadVerbs />}>
      <span
        className="arrival-brief-headline"
        data-testid="arrival-brief-headline"
      >
        {STORED_HEADLINE}
      </span>
      <DateLine />
      <HandledReceipt />
    </SurfaceSection>
  );
}

function ProposedQuiet({ state }: { state: "ready" | "generating" | "failed" }) {
  return (
    <SurfaceSection label="BRIEF" actions={<HeadVerbs busy={state === "generating"} />}>
      <SnapshotMarker />
      <span
        className="arrival-brief-headline"
        data-testid="arrival-brief-headline"
      >
        {STORED_HEADLINE}
      </span>
      <HandledReceipt />
      {state === "generating" ? <Generating /> : null}
      {state === "failed" ? <Failed /> : null}
    </SurfaceSection>
  );
}

function OriginalEmpty() {
  return (
    <SurfaceSection label="BRIEF" actions={<HeadVerbs />}>
      <span className="arrival-brief-headline" data-testid="arrival-brief-headline">
        No changes
      </span>
      <DateLine />
    </SurfaceSection>
  );
}

const boards: Record<string, ReactNode> = {
  "7a-empty-original": <OriginalEmpty />,
  "7b-fully-triaged-original": <OriginalQuiet />,
  "7c-one-line-proposed": <OneLineProposed />,
  "7b-fully-triaged-proposed": <ProposedQuiet state="ready" />,
  "8a-quiet-generating-proposed": <ProposedQuiet state="generating" />,
  "8b-quiet-failed-proposed": <ProposedQuiet state="failed" />,
  "9-same-day-success-proposed": (
    <SurfaceSection label="BRIEF" actions={<HeadVerbs />}>
      <SnapshotMarker />
      <span className="arrival-brief-headline" data-testid="arrival-brief-headline">
        {STORED_HEADLINE}
      </span>
      <HandledReceipt />
      <GestureReceipt />
    </SurfaceSection>
  ),
};

const key = new URLSearchParams(location.search).get("board") ?? "7b-fully-triaged-proposed";
createRoot(document.getElementById("root")!).render(
  <div className="desk-next" id="desk-next">
    <Chair>
      <div data-testid="arrival-brief">{boards[key] ?? boards["7b-fully-triaged-proposed"]}</div>
    </Chair>
  </div>,
);

/* PHILO-4-01 canvas harness: the REAL library species (SurfaceSection,
 * SurfaceLedger, SurfaceLedgerRow, Button, BriefEgress) composed in the
 * BRIEF section's own markup (ChairHome.tsx:1196-1330, 1978-2040).
 * Scratch only; never shipped. */
import { createRoot } from "react-dom/client";
import type { ReactNode } from "react";
import "@w/styles/global.css";
import "@w/styles/react-app.css";
import "@w/desk/desk.css";
import { Chair } from "@w/desk/chair/Chair";
import { SurfaceSection, SurfaceLedger, SurfaceLedgerRow, countToken } from "@w/desk/surface";
import { Button } from "@w/components/signal/Signal";
import { BriefEgress } from "@w/desk/chair/briefEgress";

type Item = { id: string; text: string };
const BRIEF_CAP = 3;

const D1 = { id: "d1", text: "Review decision: Use SQLite for the local store" }; // created SEP 21 09:05
const D2 = { id: "d2", text: "Review decision: Adopt the one desk bus" };         // created SEP 22 11:30
const D3 = { id: "d3", text: "Review decision: Keep one hub per desk" };          // created SEP 23 16:10
const NEW = { id: "dn", text: "Review decision: Ship the ingest API behind a flag" }; // created SEP 24 07:58
const M1 = { id: "m1", text: "Meeting recorded: Platform sync" };
const M2 = { id: "m2", text: "Meeting recorded: Architecture review" };
const L1 = { id: "l1", text: "Open loop: Rate limits for the partner API" };
const C1 = { id: "c1", text: "Commitment due 2026-09-25: Send the Q4 plan to Dana" };

const DAY1 = "SEP 21 – 23 · GENERATED SEP 23 17:40";
const DAY2 = "SEP 21 – 24 · GENERATED SEP 24 08:02";

function Verbs({ busy }: { busy?: boolean }) {
  return (
    <>
      <BriefEgress />
      <Button variant="ghost" dense disabled={busy} data-testid="arrival-brief-generate">
        Generate
      </Button>
    </>
  );
}

function Rows({ items, actions }: { items: Item[]; actions?: ReactNode }) {
  const visible = items.slice(0, BRIEF_CAP);
  const overflow = items.length - visible.length;
  return (
    <SurfaceSection
      label={`BRIEF · ${countToken(items.length, "THING WAITING", "THINGS WAITING") ?? ""}`}
      actions={actions}
    >
      <SurfaceLedger count={null} cols="room">
        {visible.map((item) => (
          <SurfaceLedgerRow
            key={item.id}
            primary={item.text}
            trailing={
              <>
                <Button variant="ghost" dense>Ack</Button>
                <Button variant="ghost" dense>Defer</Button>
              </>
            }
            expands={false}
            wrap
            data-testid="arrival-brief-row"
          />
        ))}
      </SurfaceLedger>
      {overflow > 0 ? (
        <Button variant="ghost" dense data-testid="arrival-brief-more">
          {overflow} more
        </Button>
      ) : null}
    </SurfaceSection>
  );
}

const Caption = ({ text }: { text: string }) => (
  <span className="surface-receipt-line" data-testid="arrival-brief-date">{text}</span>
);
const Receipt = ({ text }: { text: string }) => (
  <span className="surface-receipt-line" role="status" data-testid="arrival-brief-receipt">{text}</span>
);
const Failed = ({ text, testid }: { text: string; testid: string }) => (
  <span className="arrival-brief-failed">
    <span className="surface-receipt-line" role="status" data-tone="danger" data-testid={testid}>{text}</span>
    <Button variant="ghost" dense data-testid="arrival-brief-retry">Retry</Button>
  </span>
);

const DAY1_TODAY_ORDER = [M1, L1, C1, D2]; // today: changed, waiting, decisions LAST
const DAY1_ORDER = [D2, M1, L1, C1];       // proposed: decisions lead, newest first
const DAY2_ONE = [NEW, D2, M2, M1, L1, C1];
const DAY2_SEVERAL = [NEW, D3, D2, D1, M2, L1, C1];

const boards: Record<string, ReactNode> = {
  "0-today": (<><Rows items={DAY1_TODAY_ORDER} /><Caption text={DAY1} /></>),
  "1-generate-reachable": (<><Rows items={DAY1_ORDER} actions={<Verbs />} /><Caption text={DAY1} /></>),
  "2a-generating": (<><Rows items={DAY1_ORDER} actions={<Verbs busy />} /><Caption text={DAY1} />
    <span className="surface-receipt-line" role="status" data-testid="arrival-brief-generating">GENERATING…</span></>),
  "2b-reading": (
    <SurfaceSection label="BRIEF" actions={<Verbs busy />}>
      <span className="surface-receipt-line" role="status" data-testid="arrival-brief-loading">READING…</span>
    </SurfaceSection>),
  "3a-did-not-generate": (<><Rows items={DAY1_ORDER} actions={<Verbs />} /><Caption text={DAY1} />
    <Failed text="BRIEF DID NOT GENERATE · HTTP 500" testid="arrival-brief-generate-failed" /></>),
  "3b-did-not-load": (
    <SurfaceSection label="BRIEF" actions={<Verbs />}>
      <Failed text="BRIEF DID NOT LOAD · HTTP 500" testid="arrival-brief-load-failed" />
    </SurfaceSection>),
  "4-next-day-one-decision": (<><Rows items={DAY2_ONE} actions={<Verbs />} /><Caption text={DAY2} />
    <Receipt text="Brief ready · 6 items · 8:02 AM" /></>),
  "5-next-day-several-decisions": (<><Rows items={DAY2_SEVERAL} actions={<Verbs />} /><Caption text={DAY2} />
    <Receipt text="Brief ready · 7 items · 8:02 AM" /></>),
};

const key = new URLSearchParams(location.search).get("board") ?? "1-generate-reachable";
createRoot(document.getElementById("root")!).render(
  <div className="desk-next" id="desk-next">
    <Chair>
      <div data-testid="arrival-brief">{boards[key]}</div>
    </Chair>
  </div>,
);

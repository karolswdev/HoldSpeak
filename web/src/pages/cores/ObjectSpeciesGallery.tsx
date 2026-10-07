// PHILO-14 B1 — the object species in the component gallery (the
// "Components" window, /design/components). Every species drawn with the
// A boards' data (docs/internal/philo/phase-14/canvas): the face lanes
// (A1, A2, A5, C2, C3) read their props here. Nothing here is wired to the
// hub; the verbs do nothing but move the gallery's own state.
import { useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  AskWell,
  ConfirmLine,
  DeskIcon,
  DragGhost,
  DropTarget,
  EgressChip,
  FilesChanged,
  GetInfo,
  IconGrid,
  NeedsList,
  NeedsRow,
  ObjectList,
  PRCard,
  StationTrack,
  SurfaceSection,
  TimelineRail,
  iconsInRect,
  objectSprite,
  type GridRect,
  type ObjectListRow,
  type ObjectSort,
} from "../../desk/surface";
import "./object-gallery.css";

const LEDGER = "Payments ledger cutover";

const DRAWER: ObjectListRow[] = [
  { id: "m-standup", kind: "meeting", name: "Ledger cutover sync", when: "TODAY", whenSort: 9 },
  { id: "d-freeze", kind: "decision", name: "Freeze the old ledger on Nov 5", when: "TODAY", whenSort: 9 },
  { id: "m-standup-a1", kind: "action", name: "Write the rollback runbook", when: "TODAY", whenSort: 9, state: { label: "CLAUDE CODE ASKS", tone: "ask" } },
  { id: "m-standup-a2", kind: "action", name: "Shard the reconciliation job", when: "TODAY", whenSort: 9, state: { label: "CODEX WORKS", tone: "info" } },
  { id: "m-standup-a3", kind: "action", name: "Add the ledger freeze flag", when: "TODAY", whenSort: 9, state: { label: "PR #412", tone: "ok" } },
  { id: "act-cutover-comms", kind: "action", name: "Write the cutover comms", when: "TODAY", whenSort: 9 },
  { id: "claude:c1a0de00-runbook", kind: "agent", name: "Claude Code: rollback runbook", when: "42 MIN", whenSort: 10, state: { label: "ASKS", tone: "ask" } },
  { id: "codex:c0dex000-recon", kind: "agent", name: "Codex: reconciliation", when: "30 MIN", whenSort: 11, state: { label: "WORKS", tone: "info" } },
  { id: "n-1", kind: "note", name: "Ledger cutover risks", when: "OCT 5", whenSort: 5 },
  { id: "art-cutover-reqs", kind: "artifact", name: "Cutover requirements", when: "TODAY", whenSort: 9 },
  { id: "repo-payments-ledger", kind: "repository", name: "payments-ledger", when: "OCT 4", whenSort: 4 },
  { id: "p-jordan", kind: "person", name: "Jordan Patel", when: "WEEKLY", whenSort: 1 },
];

const ICON_LAMP: Record<string, { tone: "ok" | "warn" | "fail" | "info" | "ask"; label: string }> = {
  "m-standup-a1": { tone: "ask", label: "Claude Code asks" },
  "m-standup-a2": { tone: "info", label: "Codex works" },
  "m-standup-a3": { tone: "ok", label: "PR #412" },
  "claude:c1a0de00-runbook": { tone: "ask", label: "asks" },
  "codex:c0dex000-recon": { tone: "info", label: "works" },
};

function IconsSpecimen() {
  const [sel, setSel] = useState<string[]>(["m-standup-a1"]);
  const [band, setBand] = useState<GridRect | null>(null);
  return (
    <SurfaceSection label="DeskIcon · IconLamp · IconGrid">
      <div className="object-gallery-floor">
        <DeskIcon
          id="p-ledger"
          kind="project"
          name={LEDGER}
          lamp={{ tone: "ask", count: 3, label: "3 need you" }}
          selected
        />
        <DeskIcon
          id="conductor"
          kind="conductor"
          name="Conductor"
          lamp={{ tone: "ask", count: 3, label: "3 need you" }}
          badge={objectSprite("agent", "conductor-badge")}
        />
        <DeskIcon id="needs-you" kind="smart" name="Needs you" lamp={{ tone: "ask", count: 6, label: "6 need you" }} />
        <DeskIcon id="parked" kind="parked" name="Parked" />
        <DeskIcon id="m-bare" kind="meeting" name="Vendor call" lamp={{ tone: "warn", label: "due" }} />
      </div>
      <IconGrid
        label={LEDGER}
        marquee={band}
        onClear={() => setSel([])}
        onMarquee={(rect, grid) => {
          setBand(rect);
          if (rect) setSel(iconsInRect(grid, rect));
        }}
      >
        {DRAWER.map((o) => (
          <DeskIcon
            key={o.id}
            id={o.id}
            kind={o.kind}
            name={o.name}
            lamp={ICON_LAMP[o.id]}
            selected={sel.includes(o.id)}
            ghost={o.id === "act-cutover-comms"}
            onSelect={() => setSel([o.id])}
          />
        ))}
      </IconGrid>
    </SurfaceSection>
  );
}

function ListSpecimen() {
  const [sort, setSort] = useState<ObjectSort>({ key: "name", dir: "asc" });
  const [sel, setSel] = useState<string | null>("m-standup-a1");
  return (
    <SurfaceSection label="ObjectList">
      <ObjectList
        label={LEDGER}
        rows={DRAWER}
        sort={sort}
        onSort={(key) => setSort((s) => ({ key, dir: s.key === key && s.dir === "asc" ? "desc" : "asc" }))}
        selectedId={sel}
        onSelect={setSel}
      />
    </SurfaceSection>
  );
}

function LaneSpecimen() {
  const [answer, setAnswer] = useState("");
  return (
    <>
      <SurfaceSection label="StationTrack">
        <StationTrack
          label="Lane stations"
          stations={[
            { word: "BRIEF", sub: "09:42", state: "reached" },
            { word: "WORK", sub: "14 calls", state: "reached" },
            { word: "COMMIT", sub: "1", state: "reached" },
            { word: "PR", sub: "#413", state: "reached", tone: "info" },
            { word: "HELD", sub: "1 call", state: "reached", tone: "warn" },
            { word: "ASKS", sub: "now", state: "current", tone: "ask" },
            { word: "MERGE", sub: "yours", state: "ahead" },
          ]}
        />
      </SurfaceSection>
      <SurfaceSection label="AskWell">
        <AskWell
          agent="Claude Code"
          age="6 min"
          question="The runbook needs a rollback owner. Jordan or Avery?"
          value={answer}
          onChange={setAnswer}
          onAnswer={() => setAnswer("")}
          draft="Jordan owns it. Avery reviews."
          onUseDraft={setAnswer}
          draftEgress={{ label: "API.ANTHROPIC.COM", scope: "cloud" }}
        />
      </SurfaceSection>
      <SurfaceSection label="PRCard · FilesChanged">
        <PRCard
          number={413}
          title="Draft the ledger rollback runbook"
          checks={{ passed: 6, total: 7, running: 1 }}
          review="none yet"
          branch="hs/write-the-rollback-runbook"
          base="main"
        />
        <FilesChanged
          files={[
            { path: "docs/runbooks/ledger-rollback.md", added: 84 },
            { path: "ledger/freeze.py", added: 3, removed: 1 },
            { path: "tests/runbooks/test_rollback.py", added: 22 },
          ]}
        />
      </SurfaceSection>
      <SurfaceSection label="TimelineRail">
        <TimelineRail
          label="Lane"
          entries={[
            { time: "09:42", word: "BRIEF", text: "6 sources · 4.2 KB · 3 checks", verbs: <Button dense variant="ghost">Brief</Button> },
            { time: "09:43", word: "READ", code: "ledger/freeze.py · docs/runbooks/README.md · +2" },
            { time: "09:45", word: "SAYS", quote: "I will draft the runbook from the freeze decision and the Nov 12 rollback window." },
            { time: "09:47", word: "WRITE", code: "docs/runbooks/ledger-rollback.md +84" },
            { time: "09:48", word: "RUN", tone: "ok", code: "pytest tests/runbooks -q · 6 passed" },
            { time: "09:51", word: "COMMIT", code: "a1c9e02 Draft the ledger rollback runbook" },
            { time: "09:53", word: "PR", tone: "info", text: "#413 opened · checks 6 of 7 · review none yet" },
            {
              time: "09:55",
              word: "HELD",
              tone: "warn",
              code: "psql -h staging-ledger -c 'select count(*) from entries'",
              verbs: (
                <>
                  <Button dense variant="ghost">Deny</Button>
                  <Button dense variant="secondary">Approve</Button>
                </>
              ),
            },
            { time: "09:56", word: "ASKS", tone: "ask", text: "The runbook needs a rollback owner. Jordan or Avery?" },
            { word: "MERGE", text: "Your press in GitHub", pending: true },
          ]}
        />
      </SurfaceSection>
    </>
  );
}

export function ObjectSpeciesGallery() {
  const [briefOpen, setBriefOpen] = useState(false);
  return (
    <div className="object-gallery" data-testid="object-species-gallery">
      <IconsSpecimen />
      <ListSpecimen />
      <SurfaceSection label="GetInfo">
        <GetInfo
          id="m-standup-a1"
          kind="action"
          name="Write the rollback runbook"
          facts={{
            where: LEDGER,
            from: "Ledger cutover sync",
            made: "TODAY 08:40",
            owner: "Claude Code (agent)",
            state: { label: "CLAUDE CODE ASKS", tone: "ask" },
            branch: "hs/write-the-rollback-runbook",
          }}
        />
      </SurfaceSection>
      <SurfaceSection label="ConfirmLine · DropTarget · DragGhost">
        <ConfirmLine
          from={{ kind: "action", id: "act-cutover-comms" }}
          to={{ kind: "agent", id: "claude:launcher" }}
          title="Write the cutover comms"
          fact="CLAUDE CODE · YOLO · hs/write-the-cutover-comms"
          onBrief={() => setBriefOpen((o) => !o)}
          briefOpen={briefOpen}
          onCancel={() => setBriefOpen(false)}
          onHand={() => setBriefOpen(false)}
        />
        <div className="object-gallery-drop">
          <DropTarget lit>
            <DeskIcon
              id="conductor"
              kind="conductor"
              name="Conductor"
              drop
              lamp={{ tone: "ask", count: 3, label: "3 need you" }}
              badge={objectSprite("agent", "conductor-badge")}
            />
          </DropTarget>
          <span className="object-gallery-ghost-slot" aria-hidden="true">
            <DragGhost kind="action" id="act-cutover-comms" x={0} y={0} />
          </span>
        </div>
      </SurfaceSection>
      <LaneSpecimen />
      <SurfaceSection label="NeedsRow">
        <NeedsList label="Needs you">
          <NeedsRow
            id="claude:c1a0de00-runbook"
            kind="agent"
            name="Claude Code: rollback runbook"
            fact="The runbook needs a rollback owner. Jordan or Avery?"
            lamp={{ label: "ASKS · 6 MIN", tone: "ask" }}
            verbs={
              <>
                <Button dense variant="ghost">Open</Button>
                <Button dense variant="primary">Answer</Button>
              </>
            }
          />
          <NeedsRow
            id="codex:c0dex000-recon"
            kind="agent"
            name="Codex: reconciliation"
            fact="psql -h staging-ledger -c 'select count(*) from entries'"
            lamp={{ label: "HELD CALL", tone: "warn" }}
            verbs={
              <>
                <Button dense variant="ghost">Deny</Button>
                <Button dense variant="secondary">Approve</Button>
              </>
            }
          />
          <NeedsRow
            id="pr-412"
            kind="pr"
            name="#412 Add the ledger freeze flag"
            fact="Approved · 7 of 7 checks · your merge"
            lamp={{ label: "CHECKS PASS", tone: "ok" }}
            verbs={
              <>
                <EgressChip label="GITHUB.COM" scope="cloud" />
                <Button dense variant="secondary">Open PR</Button>
              </>
            }
          />
          <NeedsRow
            id="m-bare"
            kind="meeting"
            name="Vendor call"
            fact="20 min · no summary"
            lamp={{ label: "NO SUMMARY", tone: "warn" }}
            verbs={<Button dense variant="secondary">Summarize</Button>}
          />
        </NeedsList>
      </SurfaceSection>
    </div>
  );
}

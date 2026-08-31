import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-95-08 — the component grammar gallery, hosted anywhere.
// HS-111-08 — the gallery shows the KIT (audit §3.5): the gadget
// species on the surface idiom are the living style guide now — the
// legacy Signal dialect (Switch/Tabs/StatusPill/InlineMessage/
// Disclosure/ChoiceCard/Toolbar) retired with this story.
// HS-156-03 — extended with the v1 library patterns gallery.
import type { CoreProps } from "./core-types";
import { useRef, useState } from "react";
import { Button } from "../../components/signal/Signal";
import {
  CheckGadget,
  CycleGadget,
  EgressChip,
  FoldGadget,
  GadgetGroup,
  GadgetRow,
  GadgetTable,
  LampGadget,
  LedMeter,
  PadGadget,
  PropGadget,
  StepperGadget,
  StringGadget,
  TransportKey,
  TransportRow,
} from "../../desk/surface/gadgets";
import {
  ConfirmVerb,
  MetricStrip,
  SurfaceLedger,
  SurfaceLedgerRow,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";
import { SurfaceWings } from "../../desk/surface/wings";
import {
  StateChip,
  ActionNotice,
  Disclosure,
  ProgressPlan,
  ChoiceCardGroup,
  ChoiceCard,
  Popover,
  ProvenanceChip,
  Receipt,
  type ChipState,
  type PlanStep,
} from "../../desk/surface/patterns";

const ALL_CHIP_STATES: ChipState[] = [
  "idle", "active", "working", "success", "warning", "failure", "unreachable",
];

const GALLERY_PLAN_STEPS: PlanStep[] = [
  { id: "fetch", label: "Fetch manifest", status: "done" },
  { id: "download", label: "Download weights", status: "running", progress: 0.42, rate: "18 MB/s" },
  { id: "verify", label: "Verify checksums", status: "queued" },
  { id: "register", label: "Register model", status: "queued" },
];

const GALLERY_PLAN_MIXED: PlanStep[] = [
  { id: "connect", label: "Connect to host", status: "done" },
  { id: "auth", label: "Authenticate", status: "failed", detail: "Token expired" },
  { id: "sync", label: "Sync state", status: "queued" },
];

export function ComponentsCore({ hero }: CoreProps) {
  const [checked, setChecked] = useState(true);
  const [cycle, setCycle] = useState("auto");
  const [text, setText] = useState("");
  const [pad, setPad] = useState("");
  const [steps, setSteps] = useState(16384);
  const [prop, setProp] = useState(0.6);
  const [wing, setWing] = useState("one");
  const [tableRows, setTableRows] = useState([
    ["say the word", "types the phrase"],
    ["open board", "opens the board"],
  ]);
  const [confirmed, setConfirmed] = useState(0);
  const [choiceValue, setChoiceValue] = useState<string | null>(null);
  const [disclosureOpen, setDisclosureOpen] = useState(false);
  const [popoverOpen, setPopoverOpen] = useState(false);
  const popoverAnchorRef = useRef<HTMLButtonElement>(null);
  return (
    <>
      {hero ? (
        hero(null)
      ) : (
        <SurfaceVerbs status="The gadget kit on the surface idiom">
          <Button dense variant="primary">
            Primary verb
          </Button>
        </SurfaceVerbs>
      )}
      <SurfaceSection label="Buttons and verbs">
        <div className="surface-actions">
          <Button variant="primary">Primary</Button>
          <Button>Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Destructive</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button dense>Dense action</Button>
        </div>
        <TransportRow>
          <TransportKey label="TALK" glyph="●" />
          <TransportKey label="STOP" glyph="■" active />
          <TransportKey label="KILL" glyph="✕" tone="danger" />
          <TransportKey label="SEND" glyph="↵" compact />
        </TransportRow>
      </SurfaceSection>
      <SurfaceSection label="The gadget sheet">
        <GadgetGroup label="EVERY CONTROL IS A GADGET">
          <GadgetRow label="Boolean" fact="CheckGadget">
            <CheckGadget
              label="Gallery boolean"
              checked={checked}
              onChange={setChecked}
            />
          </GadgetRow>
          <GadgetRow label="Pick" fact="CycleGadget">
            <CycleGadget
              label="Gallery pick"
              value={cycle}
              options={[
                { value: "auto", label: "Automatic" },
                { value: "device", label: "On device" },
                { value: "held", label: "Held", disabled: true },
              ]}
              onChange={setCycle}
            />
          </GadgetRow>
          <GadgetRow label="Text" fact="StringGadget · mic">
            <StringGadget
              label="Gallery text"
              value={text}
              placeholder="TYPE OR SPEAK"
              onChange={setText}
            />
          </GadgetRow>
          <GadgetRow label="Long text" fact="PadGadget · mic" wide>
            <PadGadget
              label="Gallery long text"
              value={pad}
              placeholder="THE MULTILINE WELL"
              onChange={setPad}
            />
          </GadgetRow>
          <GadgetRow label="Number" fact="StepperGadget">
            <StepperGadget
              label="Gallery number"
              value={steps}
              min={1024}
              step={1024}
              unit="tok"
              onChange={setSteps}
            />
          </GadgetRow>
          <GadgetRow label="Scalar" fact="PropGadget">
            <PropGadget label="Gallery scalar" value={prop} onChange={setProp} />
          </GadgetRow>
          <GadgetRow label="Level" fact="LedMeter" wide>
            <LedMeter label="CTX" value={prop} />
          </GadgetRow>
        </GadgetGroup>
      </SurfaceSection>
      <SurfaceSection label="Lamps and chips">
        <div className="surface-actions">
          <LampGadget on tone="ok" label="ready" />
          <LampGadget on tone="warn" label="review" />
          <LampGadget on tone="fail" label="blocked" />
          <LampGadget on={false} label="off" />
          <span className="gadget-chip">ctx 16k</span>
          <span className="gadget-chip" data-set="">
            SET
          </span>
          <EgressChip />
        </div>
        <MetricStrip
          items={[
            { label: "figures", value: 12 },
            { label: "omitted when empty", value: "" },
          ]}
        />
      </SurfaceSection>
      <SurfaceSection label="Wings and the fold">
        {/* HS-100-12: a gallery SPECIMEN, not window IA — the geometry
            walk exempts data-specimen. */}
        <div data-specimen="true">
          <SurfaceWings
            wings={[
              { id: "one", label: "Outcomes" },
              { id: "two", label: "Record" },
            ]}
            active={wing}
            onChange={setWing}
            door="Configure"
          />
        </div>
        <FoldGadget title="RAW · SPECIMEN" token="2 LINES">
          <p>The fold is the ONE disclosure species: quiet row, caret,</p>
          <p>trailing token slot; details semantics keep keyboard free.</p>
        </FoldGadget>
      </SurfaceSection>
      <SurfaceSection label="The table and the armed delete">
        <GadgetTable
          head={["KEYWORD", "DOES"]}
          rows={tableRows}
          deleteLabel="DELETE?"
          onDelete={(index) =>
            setTableRows((rows) => rows.filter((_, row) => row !== index))
          }
          onAdd={() =>
            setTableRows((rows) => [...rows, ["new word", "does the thing"]])
          }
        />
      </SurfaceSection>
      <SurfaceSection label="The ledger walks">
        <SurfaceLedger count="SPECIMEN 3 · ARROWS WALK">
          <ul className="surface-ledger-rows">
            <SurfaceLedgerRow time="09:38" primary="one Tab stop for the composite" expands={false} />
            <SurfaceLedgerRow time="09:41" primary="arrows ride the accent band" expands={false} />
            <SurfaceLedgerRow time="09:44" primary="Home and End jump; letters seek" expands={false} />
          </ul>
        </SurfaceLedger>
      </SurfaceSection>
      <SurfaceSection label="Rows, states, and the two-step">
        <SurfaceRows>
          <SurfaceRow
            glyph="◈"
            title="An honest row"
            detail="title + meaningful detail; unknowns omitted"
            meta="just now"
            verbs={
              <ConfirmVerb
                label="Delete"
                confirmLabel="Delete?"
                onConfirm={() => setConfirmed((count) => count + 1)}
              />
            }
          />
          <SurfaceRow
            title="A press-target row"
            detail="the row body is one press target"
            onOpen={() => setConfirmed((count) => count + 1)}
          />
        </SurfaceRows>
        {confirmed ? (
          <p className="surface-receipt-line" data-tone="ok" role="status">
            ✓ TWO-STEP FIRED ×{confirmed} · NO MODAL
          </p>
        ) : null}
        <SurfaceState empty emptyLabel="A quiet empty state" emptyGlyph="○" />
        <SurfaceState error="The error leg renders in the flow" />
      </SurfaceSection>
      {/* ── HS-156-03: v1 library patterns gallery ── */}
      <SurfaceSection label="StateChip — all seven states">
        <div className="surface-actions">
          {ALL_CHIP_STATES.map((state) => (
            <StateChip key={state} state={state} />
          ))}
        </div>
        <div className="surface-actions">
          <StateChip state="active" label="Custom label" icon="*" />
        </div>
      </SurfaceSection>
      <SurfaceSection label="ActionNotice — tone variants">
        <ActionNotice tone="info" icon="i">
          Models are downloading in the background.
        </ActionNotice>
        <ActionNotice tone="ok" icon={"✓"}>
          All checks passed.
        </ActionNotice>
        <ActionNotice
          tone="warn"
          icon={"⚠"}
          action={{ label: "Review", onClick: () => {} }}
        >
          One model needs attention.
        </ActionNotice>
        <ActionNotice tone="danger" icon={"✗"}>
          Connection lost to the host.
        </ActionNotice>
        <ActionNotice action={{ label: "Retry", onClick: () => {} }}>
          Default tone (no explicit tone set).
        </ActionNotice>
      </SurfaceSection>
      <SurfaceSection label="Disclosure — controlled and uncontrolled">
        <Disclosure label="Uncontrolled fold (default closed)">
          <p>Content pushed into the layout flow. Escape closes.</p>
        </Disclosure>
        <Disclosure label="Uncontrolled fold (default open)" defaultOpen>
          <p>Started open. The caret rotates with the state.</p>
        </Disclosure>
        <Disclosure
          label="Controlled fold"
          open={disclosureOpen}
          onOpenChange={setDisclosureOpen}
          token="CTRL"
        >
          <p>This fold is externally controlled. Token slot visible.</p>
        </Disclosure>
        <Disclosure label="RAW variant" variant="raw" token="DEBUG">
          <p>The RAW variant for advanced/debug panels.</p>
        </Disclosure>
      </SurfaceSection>
      <SurfaceSection label="ProgressPlan — detailed and compact">
        <ProgressPlan
          steps={GALLERY_PLAN_STEPS}
          receipt={<Receipt status="ok" label="Started" timestamp="09:41" />}
          action={{ label: "Retry", onClick: () => {} }}
        />
        <ProgressPlan
          steps={GALLERY_PLAN_MIXED}
          compact
          egress={<ProvenanceChip source="Local" boundary="LAN" />}
          action={{ label: "Resume", onClick: () => {} }}
        />
      </SurfaceSection>
      <SurfaceSection label="ChoiceCardGroup — radio semantics">
        <ChoiceCardGroup
          name="gallery-model"
          value={choiceValue}
          onChange={setChoiceValue}
          confirmLabel="Apply"
          onConfirm={() => {}}
          ariaLabel="Model selection"
        >
          <ChoiceCard
            value="local"
            label="On-device"
            description="Runs entirely on your machine"
            recommended
            facts={[
              { label: "Size", value: "4.2 GB" },
              { label: "Speed", value: "32 tok/s" },
            ]}
            cost="Free"
            name="gallery-model"
            selectedValue={choiceValue}
            onChange={setChoiceValue}
          />
          <ChoiceCard
            value="cloud"
            label="Cloud"
            description="Runs on a remote endpoint"
            facts={[
              { label: "Latency", value: "~200 ms" },
              { label: "Limit", value: "1000 req/day" },
            ]}
            cost="$0.002 / 1k tok"
            name="gallery-model"
            selectedValue={choiceValue}
            onChange={setChoiceValue}
          />
          <ChoiceCard
            value="held"
            label="Held"
            description="Temporarily unavailable"
            disabled
            name="gallery-model"
            selectedValue={choiceValue}
            onChange={setChoiceValue}
          />
        </ChoiceCardGroup>
      </SurfaceSection>
      <SurfaceSection label="Popover — in-flow anchored">
        <button
          ref={popoverAnchorRef}
          type="button"
          className="signal-btn"
          onClick={() => setPopoverOpen(!popoverOpen)}
        >
          {popoverOpen ? "Close popover" : "Open popover"}
        </button>
        <Popover
          anchor={popoverAnchorRef}
          open={popoverOpen}
          onClose={() => setPopoverOpen(false)}
          ariaLabel="Gallery popover"
        >
          <p style={{ margin: 0, padding: "8px" }}>
            Popover content. Escape dismisses. Focus is trapped.
          </p>
        </Popover>
      </SurfaceSection>
      <SurfaceSection label="ProvenanceChip and Receipt — footer slots">
        <div className="surface-actions">
          <ProvenanceChip source="Whisper" />
          <ProvenanceChip source="Local LLM" boundary="LAN" />
          <ProvenanceChip source="Cloud API" boundary="egress" onInspect={() => {}} />
        </div>
        <div className="surface-actions">
          <Receipt status="ok" label="Transcribed" timestamp="09:38" />
          <Receipt status="warn" label="Partial" timestamp="09:41" />
          <Receipt status="danger" label="Failed" onInspect={() => {}} />
        </div>
      </SurfaceSection>
      <SurfaceFooter
        receipt={<Receipt status="ok" label="Gallery loaded" timestamp="now" />}
        egress={<ProvenanceChip source="Local" />}
      />
    </>
  );
}

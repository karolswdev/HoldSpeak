import { SurfaceFooter } from "../../desk/surface/SurfaceFooter";
// HS-95-08 — the component grammar gallery, hosted anywhere.
// HS-111-08 — the gallery shows the KIT (audit §3.5): the gadget
// species on the surface idiom are the living style guide now — the
// legacy Signal dialect (Switch/Tabs/StatusPill/InlineMessage/
// Disclosure/ChoiceCard/Toolbar) retired with this story.
import type { CoreProps } from "./core-types";
import { useState } from "react";
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
      <SurfaceFooter />
    </>
  );
}

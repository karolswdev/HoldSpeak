// HS-95-08 — the component grammar gallery, hosted anywhere.
// HS-98-06 — the gallery shows the CURRENT canon: Signal controls on
// the surface idiom (sections, rows, states, the inline two-step) —
// the page grammar and the modal demo are gone with the grammar.
import type { CoreProps } from "./ActivityCore";
import { useState } from "react";
import {
  Button,
  Checkbox,
  ChoiceCard,
  Disclosure,
  Field,
  InlineMessage,
  Select,
  StatusPill,
  Switch,
  Tabs,
  TextArea,
  TextInput,
  Toolbar,
} from "../../components/signal/Signal";
import {
  ConfirmVerb,
  MetricStrip,
  SurfaceColumns,
  SurfaceRow,
  SurfaceRows,
  SurfaceSection,
  SurfaceState,
  SurfaceVerbs,
} from "../../desk/surface/Surface";

export function ComponentsCore({ hero }: CoreProps) {
  const [tab, setTab] = useState("one");
  const [checked, setChecked] = useState(true);
  const [confirmed, setConfirmed] = useState(0);
  return (
    <>
      {hero ? (
        hero(null)
      ) : (
        <SurfaceVerbs status="The Signal grammar on the surface idiom">
          <Button dense variant="primary">
            Primary verb
          </Button>
        </SurfaceVerbs>
      )}
      <SurfaceSection label="Buttons">
        <div className="surface-actions">
          <Button variant="primary">Primary</Button>
          <Button>Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Destructive</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button dense>Dense action</Button>
        </div>
      </SurfaceSection>
      <SurfaceColumns
        main={
          <SurfaceSection label="Fields">
            <Field
              label="Text input"
              description="A persistent, associated description."
            >
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  placeholder="Default state"
                />
              )}
            </Field>
            <Field label="Invalid input" error="Use a complete server address.">
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  aria-invalid="true"
                  defaultValue="localhost"
                />
              )}
            </Field>
            <Field label="Select">
              {({ id }) => (
                <Select id={id}>
                  <option>Automatic</option>
                  <option>On device</option>
                </Select>
              )}
            </Field>
            <Field label="Long text">
              {({ id }) => (
                <TextArea
                  id={id}
                  defaultValue="A composed area for longer source material."
                />
              )}
            </Field>
            <Field label="Date" description="The picker indicator wears the skin.">
              {({ id }) => <TextInput id={id} type="date" />}
            </Field>
            <Field label="Search" description="The cancel glyph is drawn, not native.">
              {({ id }) => (
                <TextInput id={id} type="search" defaultValue="clearable" />
              )}
            </Field>
            <Field label="Number">
              {({ id }) => <TextInput id={id} type="number" defaultValue={16384} />}
            </Field>
            <Field label="File" description="The selector button is a Signal face.">
              {({ id }) => <input id={id} className="hs-control" type="file" />}
            </Field>
            <Field
              label="Disabled field"
              description="Editing is restricted by policy."
            >
              {({ id, describedBy }) => (
                <TextInput
                  id={id}
                  aria-describedby={describedBy}
                  value="Read-only state"
                  disabled
                  readOnly
                />
              )}
            </Field>
          </SurfaceSection>
        }
        side={
          <SurfaceSection label="Choice">
            <Checkbox
              label="Checked option"
              description="A native checkbox with Signal presentation."
              checked={checked}
              onChange={(event) => setChecked(event.target.checked)}
            />
            <Switch
              label="Runtime enabled"
              description="A native checkbox with switch semantics."
              checked={checked}
              onChange={(event) => setChecked(event.target.checked)}
            />
            <ChoiceCard
              name="gallery-choice"
              label="On this Mac"
              description="Runs with a local model."
              defaultChecked
            />
            <ChoiceCard
              name="gallery-choice"
              label="Model server"
              description="May cross a configured boundary."
            />
          </SurfaceSection>
        }
      />
      <SurfaceSection label="Status and feedback">
        <div className="surface-actions">
          <StatusPill>neutral</StatusPill>
          <StatusPill tone="live">live</StatusPill>
          <StatusPill tone="success">success</StatusPill>
          <StatusPill tone="warning">warning</StatusPill>
          <StatusPill tone="error">error</StatusPill>
        </div>
        <InlineMessage>Informational context.</InlineMessage>
        <InlineMessage tone="success">The save completed.</InlineMessage>
        <InlineMessage tone="warning">
          Review this before continuing.
        </InlineMessage>
        <InlineMessage tone="error">
          Sync failed on the private endpoint. The draft is kept here. Retry
          sync.
        </InlineMessage>
        <MetricStrip
          items={[
            { label: "figures", value: 12 },
            { label: "omitted when empty", value: "" },
          ]}
        />
      </SurfaceSection>
      <SurfaceSection label="Navigation and disclosure">
        <Tabs
          label="Gallery tabs"
          tabs={[
            { id: "one", label: "Selected" },
            { id: "two", label: "Available" },
            { id: "three", label: "Disabled", disabled: true },
          ]}
          active={tab}
          onChange={setTab}
        />
        <Disclosure title="Reveal advanced controls">
          <p>
            Disclosure keeps advanced depth available without flattening the
            route.
          </p>
        </Disclosure>
        <Toolbar label="Example toolbar">
          <Field label="Filter">
            {({ id }) => <TextInput id={id} type="search" />}
          </Field>
          <Button>Apply filter</Button>
          <Button variant="ghost">Reset</Button>
        </Toolbar>
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
          <InlineMessage tone="success">
            {`Two-step fired ${confirmed} ${confirmed === 1 ? "time" : "times"} — no modal was involved.`}
          </InlineMessage>
        ) : null}
        <SurfaceState empty emptyLabel="A quiet empty state" emptyGlyph="○" />
      </SurfaceSection>
    </>
  );
}

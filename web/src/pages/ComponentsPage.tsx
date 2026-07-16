import { useState } from "react";
import {
  Button,
  Checkbox,
  ChoiceCard,
  Dialog,
  Disclosure,
  EmptyState,
  Field,
  InlineMessage,
  Panel,
  Select,
  StatusPill,
  Switch,
  Tabs,
  TextArea,
  TextInput,
  Toolbar,
} from "../components/signal/Signal";
import { PageHero } from "./pageSupport";

export default function ComponentsPage() {
  const [tab, setTab] = useState("one");
  const [dialog, setDialog] = useState(false);
  const [checked, setChecked] = useState(true);
  return (
    <div className="page-wrap components-page">
      <PageHero eyebrow="Signal React" title="Component grammar">
        One review surface for semantics, focus, motion, density, validation,
        and every interaction state.
      </PageHero>
      <Panel title="Buttons" eyebrow="44 px primary · 36 px dense">
        <div className="gallery-row">
          <Button variant="primary">Primary</Button>
          <Button>Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="danger">Destructive</Button>
          <Button loading>Loading</Button>
          <Button disabled>Disabled</Button>
          <Button dense>Dense action</Button>
        </div>
      </Panel>
      <div className="page-grid">
        <Panel title="Fields" eyebrow="Labels and help">
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
          <Field label="Disabled field" description="Editing is restricted by policy.">
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
        </Panel>
        <Panel title="Choice" eyebrow="Native semantics">
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
        </Panel>
      </div>
      <Panel title="Status and feedback" eyebrow="Never color alone">
        <div className="gallery-row">
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
          Sync failed on the private endpoint. The draft is kept here. Retry sync.
        </InlineMessage>
      </Panel>
      <Panel title="Navigation and disclosure" eyebrow="Keyboard-first">
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
      </Panel>
      <Panel title="Empty and dialog" eyebrow="Focus returns">
        <EmptyState
          title="A quiet empty state"
          action={<Button onClick={() => setDialog(true)}>Open dialog</Button>}
        >
          Explain what belongs here and offer one useful next move.
        </EmptyState>
      </Panel>
      <Dialog
        open={dialog}
        title="Dialog with focus return"
        onClose={() => setDialog(false)}
      >
        <p>
          Escape closes this native modal. Focus returns to the button that
          opened it.
        </p>
        <Button variant="primary" onClick={() => setDialog(false)}>
          Close dialog
        </Button>
      </Dialog>
    </div>
  );
}

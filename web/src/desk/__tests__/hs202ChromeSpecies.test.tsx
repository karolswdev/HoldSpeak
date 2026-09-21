// HS-202-03 — the shared controls on the first-use path are library species.
//
// UX-CANON A.1: "Every verb is the library Button. A raw `<button>` in a face
// is a bounce." The surface inventory of 2026-09-20 (§3.3) found the worst
// sites were the SHARED species themselves — every menu item, every wing tab,
// the dock, the editor's rail — so a stranger's first five minutes met raw
// HTML at every turn.
//
// This fence reads the source of the shared controls the five first-use jobs
// touch and refuses a raw `<button` in any of them. It is a SOURCE fence on
// purpose: the rendered DOM is a `<button>` either way (the species renders
// one), so only the source can say which species drew it.
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import deskMenuSrc from "../components/DeskMenu.tsx?raw";
import wingsSrc from "../surface/wings.tsx?raw";
import dockSrc from "../components/window/Dock.tsx?raw";
import deskEditorSrc from "../components/DeskEditor.tsx?raw";
import toolShelfSrc from "../components/DeskToolShelf.tsx?raw";
import trustWindowSrc from "../components/TrustWindow.tsx?raw";
import firstWordsSrc from "../components/FirstWords.tsx?raw";
import micButtonSrc from "../components/MicButton.tsx?raw";
import recordOrbSrc from "../components/RecordOrb.tsx?raw";
import deskWindowSrc from "../components/DeskWindow.tsx?raw";
import deskChromeSrc from "../components/DeskChrome.tsx?raw";
import deskMenuBarSrc from "../components/DeskMenuBar.tsx?raw";
import deskCreateMenuSrc from "../components/DeskCreateMenu.tsx?raw";
import pulloutSrc from "../components/Pullout.tsx?raw";
import exposeSrc from "../components/window/Expose.tsx?raw";
import noteEditorSrc from "../pullouts/editors/NoteEditor.tsx?raw";
import meetingPulloutSrc from "../pullouts/MeetingPullout.tsx?raw";
import thoughtContextSrc from "../pullouts/ThoughtContextPicker.tsx?raw";

import { Button } from "../../components/signal/Signal";
import { SurfaceWings } from "../surface/wings";

// Every stylesheet the desk ships, read as text: the ink proof below.
const CSS_MODULES = import.meta.glob("../../**/*.css", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

/** The A1 matcher the source ratchet uses (scripts/ux_canon_scan.py:460). */
const RAW_BUTTON = /<button(?=[\s>/])/g;

/** The shared controls, in the order the story migrates them. */
const MIGRATED: Array<[string, string]> = [
  ["desk/components/DeskMenu.tsx", deskMenuSrc],
  ["desk/surface/wings.tsx", wingsSrc],
  ["desk/components/window/Dock.tsx", dockSrc],
  ["desk/components/DeskEditor.tsx", deskEditorSrc],
  ["desk/components/DeskToolShelf.tsx", toolShelfSrc],
  ["desk/components/TrustWindow.tsx", trustWindowSrc],
  ["desk/components/FirstWords.tsx", firstWordsSrc],
  ["desk/components/MicButton.tsx", micButtonSrc],
  ["desk/components/RecordOrb.tsx", recordOrbSrc],
  ["desk/components/DeskWindow.tsx", deskWindowSrc],
  ["desk/components/DeskChrome.tsx", deskChromeSrc],
  ["desk/components/DeskMenuBar.tsx", deskMenuBarSrc],
  ["desk/components/DeskCreateMenu.tsx", deskCreateMenuSrc],
  ["desk/components/Pullout.tsx", pulloutSrc],
  ["desk/components/window/Expose.tsx", exposeSrc],
  ["desk/pullouts/editors/NoteEditor.tsx", noteEditorSrc],
  ["desk/pullouts/MeetingPullout.tsx", meetingPulloutSrc],
  ["desk/pullouts/ThoughtContextPicker.tsx", thoughtContextSrc],
];

describe("HS-202-03 — no raw control on the five jobs' shared screens", () => {
  it.each(MIGRATED)("%s draws every verb with the library Button", (_name, src) => {
    expect(src.match(RAW_BUTTON) ?? []).toEqual([]);
  });
});

describe("the chrome variant carries the species, not the plate", () => {
  it("withholds the .btn plate so the strip keeps its own material", () => {
    render(
      <Button variant="chrome" dense className="desk-wing">
        Record
      </Button>,
    );
    const verb = screen.getByRole("button", { name: "Record" });
    const classes = verb.className.split(/\s+/);
    expect(classes).toContain("btn--chrome");
    expect(classes).toContain("desk-wing");
    // The plate would repaint a menu row / wing tab / dock chip: 28px
    // min-height, a bevel and a centred label over a strip that draws its
    // own. Never stamped for a chrome verb -- not even `dense`.
    expect(classes).not.toContain("btn");
    expect(classes).not.toContain("btn--sm");
  });

  // THE INK PROOF. `btn--chrome` is a marker, not a look: no stylesheet in
  // the product defines it, so stamping it on a menu row, a wing tab or a
  // dock chip cannot move one pixel. The strip keeps drawing its own
  // material exactly as it did when the element was a raw `<button>`.
  it("no stylesheet defines .btn--chrome, so the marker paints nothing", () => {
    const files = Object.keys(CSS_MODULES);
    expect(files.length).toBeGreaterThan(20);
    const offenders = files.filter((file) =>
      /\.btn--chrome\b/.test(CSS_MODULES[file]),
    );
    expect(offenders).toEqual([]);
  });

  it("a plated variant still wears its plate", () => {
    render(<Button variant="primary">Save</Button>);
    const classes = screen
      .getByRole("button", { name: "Save" })
      .className.split(/\s+/);
    expect(classes).toContain("btn");
    expect(classes).toContain("btn--primary");
  });

  it("the species never submits a form unless asked", () => {
    render(
      <>
        <Button>Default</Button>
        <Button type="submit">Send</Button>
      </>,
    );
    expect(screen.getByRole("button", { name: "Default" })).toHaveAttribute(
      "type",
      "button",
    );
    expect(screen.getByRole("button", { name: "Send" })).toHaveAttribute(
      "type",
      "submit",
    );
  });
});

describe("the wing strip keeps its keyboard grammar as a library species", () => {
  const WINGS = [
    { id: "outcomes", label: "Outcomes" },
    { id: "record", label: "Record" },
  ];

  it("the tabs are tabs, and the roving Tab stop is unchanged", () => {
    render(<SurfaceWings wings={WINGS} active="record" onChange={() => {}} />);
    const tabs = screen.getAllByRole("tab");
    expect(tabs.map((tab) => tab.tabIndex)).toEqual([-1, 0]);
    expect(tabs[1].className).toContain("is-on");
  });
});

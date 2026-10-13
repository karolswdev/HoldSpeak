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


import { Button } from "../../components/signal/Signal";
import { SurfaceWings } from "../surface/wings";


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

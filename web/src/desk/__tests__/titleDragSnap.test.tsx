/** PHILO-17 snapjump: a title press and drag never tiles a window unless
 * the pointer is released inside a snap region.
 *
 * The glass red (test_philo13_12_gadgets_glass, the restored-window case):
 * after the FIRST step of a title drag the window sat in the top-left
 * quarter. The drag's end event was a lost pointer capture whose clientX
 * and clientY are 0, 0 in Chrome; the handler read that as the top-left
 * corner and tiled the window. */
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { DeskWindowFrame, snapForPointer } from "../components/DeskWindow";
import { handSourceProps } from "../hand/drag";
import { useDropHand } from "../hand/store";
import { DeskIcon } from "../surface/objects";
import { useDesk } from "../store";

const VW = 1440;
const VH = 900;

// jsdom has no pointer events and no pointer capture. The gesture library
// reads its device once, at import: the shim goes in before every import.
vi.hoisted(() => {
  class PointerEventShim extends MouseEvent {
    pointerId: number;
    pointerType: string;
    constructor(type: string, init: PointerEventInit = {}) {
      super(type, init);
      this.pointerId = init.pointerId ?? 1;
      this.pointerType = init.pointerType ?? "mouse";
    }
  }
  const w = window as unknown as Record<string, unknown>;
  w.PointerEvent = PointerEventShim;
  w.onpointerdown = null;
  const proto = Element.prototype as unknown as Record<string, unknown>;
  proto.setPointerCapture ??= () => {};
  proto.releasePointerCapture ??= () => {};
  proto.hasPointerCapture ??= () => true;
});

beforeEach(() => {
  localStorage.clear();
  Object.defineProperty(window, "innerWidth", { configurable: true, value: VW });
  Object.defineProperty(window, "innerHeight", { configurable: true, value: VH });
  useDesk.setState({
    panelRects: { wm: { x: 144, y: 72, w: 920, h: 720 } },
    panelSaved: ["wm"],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    windowsById: {},
    zoneWindows: [],
    zoneViewPrefs: {},
  });
});

afterEach(() => {
  cleanup();
  // A test that leaves the pointer held: the next one starts clean.
  fireEvent.pointerUp(document.body, at(0, 0));
  useDropHand.getState().endDrag();
});

const at = (x: number, y: number) => ({
  pointerId: 1,
  pointerType: "mouse",
  button: 0,
  buttons: 1,
  clientX: x,
  clientY: y,
});

/** The real Floor icon a drag-to-send starts from (Screen.tsx). */
function NoteIcon() {
  return (
    <DeskIcon
      id="note-1"
      kind="note"
      name="Plan"
      {...handSourceProps({
        origin: { kind: "note", id: "note-1", title: "Plan" },
        source: { kind: "note", id: "note-1" },
        host: "screen",
      })}
    />
  );
}

function Desk({ frame = true }: { frame?: boolean }) {
  return (
    <>
      {frame ? (
        <DeskWindowFrame id="wm" title="Meetings" open onClose={() => {}}>
          <p>body</p>
        </DeskWindowFrame>
      ) : null}
      <NoteIcon />
    </>
  );
}

const icon = () => screen.getByRole("button", { name: /^Plan/ });

/** An icon drag starts the app's hand, and its end clears it. */
function iconDragWorks() {
  let started = false;
  act(() => {
    // fireEvent answers false when a listener cancelled the native drag.
    started = fireEvent.dragStart(icon());
  });
  expect(started).toBe(true);
  expect(useDropHand.getState().drag).not.toBeNull();
  act(() => {
    fireEvent.dragEnd(icon());
  });
  expect(useDropHand.getState().drag).toBeNull();
}

function pressTitle(x: number, y: number, pointerType = "mouse") {
  const view = render(<Desk />);
  const shell = screen.getByRole("region", { name: "Meetings" });
  const head = shell.querySelector(".desk-window-handle") as HTMLElement;
  expect(head).toBeTruthy();
  act(() => {
    fireEvent.pointerDown(head, { ...at(x, y), pointerType });
  });
  return Object.assign(head, { view });
}

const rect = () => useDesk.getState().panelRects.wm;

describe("a title drag (PHILO-17 snapjump)", () => {
  it("a lost pointer capture on the first step parks the window; it never tiles", () => {
    const quarter = snapForPointer(0, 0, VW, VH);
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(554, 120));
    });
    // Chrome's lostpointercapture carries clientX 0, clientY 0.
    act(() => {
      fireEvent.lostPointerCapture(head, at(0, 0));
    });
    // The window stays where the first step put it (moved by -50, +30).
    expect(rect()).not.toEqual(quarter);
    expect(rect()).toEqual({ x: 94, y: 102, w: 920, h: 720 });
  });

  it("a cancelled drag inside a snap region does not tile", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(5, 450));
    });
    act(() => {
      fireEvent.pointerCancel(head, at(5, 450));
    });
    expect(rect()).not.toEqual(snapForPointer(5, 450, VW, VH));
    expect(rect().w).toBe(920);
    expect(rect().h).toBe(720);
  });

  it("a release inside a snap region tiles the window there", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(1, 460));
    });
    act(() => {
      fireEvent.pointerUp(head, at(1, 460));
    });
    expect(rect()).toEqual(snapForPointer(1, 460, VW, VH));
  });

  it("a release in the open middle parks the dragged rect", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(654, 140));
    });
    act(() => {
      fireEvent.pointerUp(head, at(654, 140));
    });
    expect(snapForPointer(654, 140, VW, VH)).toBeNull();
    expect(rect()).toEqual({ x: 194, y: 122, w: 920, h: 720 });
  });

  it("while the title drag holds the pointer, no native drag starts (a desk icon under the press point)", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(554, 120));
    });
    const icon = document.createElement("button");
    icon.draggable = true;
    document.body.appendChild(icon);
    const during = new Event("dragstart", { bubbles: true, cancelable: true });
    icon.dispatchEvent(during);
    expect(during.defaultPrevented).toBe(true);
    act(() => {
      fireEvent.pointerUp(head, at(554, 120));
    });
    const after = new Event("dragstart", { bubbles: true, cancelable: true });
    icon.dispatchEvent(after);
    expect(after.defaultPrevented).toBe(false);
    icon.remove();
  });

  it("the real desk icon: a title drag starts no hand, leaves no dim; the next icon drag works", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(554, 120));
    });
    act(() => {
      fireEvent.dragStart(icon());
    });
    expect(useDropHand.getState().drag).toBeNull();
    act(() => {
      fireEvent.pointerUp(head, at(554, 120));
    });
    expect(useDropHand.getState().drag).toBeNull();
    iconDragWorks();
  });

  it("the window goes away mid-drag: the hold is released; the next icon drag works", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(554, 120));
    });
    head.view.rerender(<Desk frame={false} />);
    expect(screen.queryByRole("region", { name: "Meetings" })).toBeNull();
    iconDragWorks();
  });

  it("a pointer cancel elsewhere releases the hold", () => {
    const head = pressTitle(604, 90);
    act(() => {
      fireEvent.pointerMove(head, at(554, 120));
    });
    act(() => {
      fireEvent.pointerCancel(document.body, at(554, 120));
    });
    iconDragWorks();
  });

  it("a mouse or touch ending elsewhere releases the hold", () => {
    for (const end of ["mouseUp", "touchEnd"] as const) {
      const head = pressTitle(604, 90);
      act(() => {
        fireEvent.pointerMove(head, at(554, 120));
      });
      act(() => {
        fireEvent[end](document.body);
      });
      iconDragWorks();
      cleanup();
    }
  });

  it("a touch drag above the compact breakpoint moves the window", () => {
    const head = pressTitle(604, 90, "touch");
    act(() => {
      fireEvent.pointerMove(head, { ...at(654, 140), pointerType: "touch" });
    });
    act(() => {
      fireEvent.pointerUp(head, { ...at(654, 140), pointerType: "touch" });
    });
    expect(rect()).toEqual({ x: 194, y: 122, w: 920, h: 720 });
  });
});

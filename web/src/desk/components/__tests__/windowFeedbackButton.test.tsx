import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDesk } from "../../store";

const feedback = vi.hoisted(() => ({
  enabled: false,
  request: vi.fn(),
}));

vi.mock("../../feedback/runtime", () => ({
  requestUiFeedback: feedback.request,
  useUiFeedbackState: () => ({ enabled: feedback.enabled, loading: false }),
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
}));

import { DeskWindowFrame } from "../DeskWindow";

const realMatchMedia = window.matchMedia;

function setCompact(on: boolean) {
  window.matchMedia = ((query: string) => ({
    matches: on && query.includes("max-width: 720px"),
    media: query,
    onchange: null,
    addEventListener: () => undefined,
    removeEventListener: () => undefined,
    addListener: () => undefined,
    removeListener: () => undefined,
    dispatchEvent: () => false,
  })) as unknown as typeof window.matchMedia;
}

function frame() {
  return (
    <div className="desk-next">
      <DeskWindowFrame id="feedback-window" title="Platform" open onClose={() => {}}>
        <textarea aria-label="Draft" defaultValue="unsaved draft" />
      </DeskWindowFrame>
    </div>
  );
}

beforeEach(() => {
  feedback.enabled = false;
  feedback.request.mockReset();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
    windowsById: {},
    zoneWindows: [],
    zoneViewPrefs: {},
  });
});

afterEach(() => {
  window.matchMedia = realMatchMedia;
});

describe("DeskWindowFrame feedback button", () => {
  it("is absent when the runtime capability is off", () => {
    setCompact(false);
    render(frame());
    expect(screen.queryByRole("button", { name: "Give feedback on Platform" })).toBeNull();
  });

  it.each([false, true])("captures this frame root directly at %s viewport", (compact) => {
    feedback.enabled = true;
    setCompact(compact);
    render(frame());
    const root = screen.getByRole("region", { name: "Platform" });
    const button = screen.getByRole("button", { name: "Give feedback on Platform" });
    expect(button).toHaveTextContent("Feedback");
    fireEvent.click(button);
    expect(feedback.request).toHaveBeenCalledWith(root);
  });
});

// HS-95-04 — one core, two hosts. The same component renders the flat
// route (with page chrome) and a desk window (without any); the guard in
// tests/unit/test_page_cores_guard.py pins host-agnosticism statically,
// these pin it behaviorally.
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it } from "vitest";
import { DeskWindowFrame } from "../../../desk/components/DeskWindow";
import { useDesk } from "../../../desk/store";
import { DEMOTED_ROUTES } from "../../../routes";
import { ActivityCore } from "../ActivityCore";
import { CommandsCore } from "../CommandsCore";

beforeEach(() => {
  localStorage.clear();
  useDesk.setState({
    panelRects: {},
    panelSaved: [],
    panelOrder: [],
    panelMin: [],
    panelMax: [],
  });
});

function inWindow(children: React.ReactNode) {
  return render(
    <DeskWindowFrame id="host" title="Host" open onClose={() => {}}>
      <div className="desk-surface-body">{children}</div>
    </DeskWindowFrame>,
  );
}

describe("cores render chrome-free inside a desk window", () => {
  it("ActivityCore: content without page chrome; verbs in the surface bar", () => {
    const { container } = inWindow(<ActivityCore />);
    expect(container.querySelector(".page-wrap")).toBeNull();
    expect(container.querySelector(".page-hero")).toBeNull();
    expect(container.querySelector(".workroom-bar")).toBeNull();
    expect(container.querySelector(".surface-verbs")).toBeTruthy();
    expect(screen.getByText("Activity intelligence")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Refresh now" })).toBeTruthy();
  });

  it("CommandsCore: content without page chrome", () => {
    const { container } = inWindow(<CommandsCore />);
    expect(container.querySelector(".page-wrap")).toBeNull();
    expect(container.querySelector(".page-hero")).toBeNull();
    expect(container.querySelector(".workroom-bar")).toBeNull();
  });
});

describe("route demotion (HS-95-08): every former page is a deep link", () => {
  const table = Object.fromEntries(DEMOTED_ROUTES.map((r) => [r.path, r]));

  it("maps every former flat route to its desk surface", () => {
    expect(table["/dictation"].surface).toBe("dictate");
    expect(table["/live"].surface).toBe("record-live");
    expect(table["/history"].surface).toBe("review-meetings");
    expect(table["/meetings"].surface).toBe("review-meetings");
    expect(table["/settings"].surface).toBe("configure-settings");
    expect(table["/activity"].surface).toBe("inspect-activity");
    expect(table["/commands"].surface).toBe("configure-commands");
    expect(table["/cadence"].surface).toBe("configure-cadence");
    expect(table["/studio"].surface).toBe("configure-tools");
    expect(table["/workbench"].surface).toBe("build-workflow");
    expect(table["/profiles"].surface).toBe("configure-runs-on");
    expect(table["/companion"].surface).toBe("inspect-personas-and-coders");
    expect(table["/setup"].surface).toBe("configure-setup");
    expect(table["/docs/dictation-runtime"].surface).toBe("read-runtime-docs");
    expect(table["/design/components"].surface).toBe("design-components");
  });

  it("carries subject decoding where deep links need scope", () => {
    expect(table["/history"].subjectKind).toBe("meeting");
    expect(table["/workbench"].subjectKind).toBe("workflow");
    expect(table["/settings"].subjectKind).toBe("integration");
  });
});

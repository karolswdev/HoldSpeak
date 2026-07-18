// HS-95-04 — one core, two hosts. The same component renders the flat
// route (with page chrome) and a desk window (without any); the guard in
// tests/unit/test_page_cores_guard.py pins host-agnosticism statically,
// these pin it behaviorally.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it } from "vitest";
import { DeskWindowFrame } from "../../../desk/components/DeskWindow";
import { useDesk } from "../../../desk/store";
import ActivityPage from "../../ActivityPage";
import CommandsPage from "../../CommandsPage";
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
  it("ActivityCore: content without page chrome; verbs in the quiet row", () => {
    const { container } = inWindow(<ActivityCore />);
    expect(container.querySelector(".page-wrap")).toBeNull();
    expect(container.querySelector(".page-hero")).toBeNull();
    expect(container.querySelector(".workroom-bar")).toBeNull();
    expect(container.querySelector(".desk-core-verbs")).toBeTruthy();
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

describe("the flat wrappers keep the page chrome", () => {
  it("ActivityPage: hero + wrap around the same core", () => {
    const { container } = render(
      <MemoryRouter>
        <ActivityPage />
      </MemoryRouter>,
    );
    expect(container.querySelector(".page-wrap")).toBeTruthy();
    expect(container.querySelector(".page-hero")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Activity" }),
    ).toBeInTheDocument();
    expect(screen.getByText("Activity intelligence")).toBeInTheDocument();
  });

  it("CommandsPage: hero + wrap around the same core", () => {
    const { container } = render(
      <MemoryRouter>
        <CommandsPage />
      </MemoryRouter>,
    );
    expect(container.querySelector(".page-wrap")).toBeTruthy();
    expect(container.querySelector(".page-hero")).toBeTruthy();
    expect(
      screen.getByRole("heading", { name: "Commands" }),
    ).toBeInTheDocument();
  });
});

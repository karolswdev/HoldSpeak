import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { decodeWorkroomContext } from "../../workrooms/context";
import { DeskToolShelf, DESK_TOOLS } from "./DeskToolShelf";
import { EmptyDesk } from "./EmptyDesk";

describe("Phase 93 Desk arrival", () => {
  beforeEach(() => {
    useDesk.setState({
      items: { ...EMPTY_ITEMS },
      projects: [],
      inferenceTargets: [],
      models: [],
      setup: null,
      selectedIds: [],
      createPrimitive: vi.fn().mockResolvedValue(undefined),
      openPullout: vi.fn(),
      openToolInspector: vi.fn(),
      diveInto: vi.fn(),
      recording: "idle",
      startRecording: vi.fn().mockResolvedValue(undefined),
      stopRecording: vi.fn().mockResolvedValue(undefined),
    });
  });

  it("presents Dictate, Record, and one progressive Create entry", () => {
    render(
      <MemoryRouter>
        <EmptyDesk />
      </MemoryRouter>,
    );

    const starts = screen.getByRole("group", { name: "Daily starts" });
    expect(starts).toBeInTheDocument();
    const dictate = new URL(
      screen.getByRole("link", { name: "Dictate" }).getAttribute("href")!,
      "https://holdspeak.test",
    );
    expect(dictate.pathname).toBe("/dictation");
    expect(decodeWorkroomContext(dictate.search)?.action).toBe("dictate");
    // Record is one verb: the chip starts the hub recorder in place (the
    // orb's exact behavior) instead of leaving the Desk for /live.
    const record = screen.getByRole("button", { name: "Record" });
    expect(record).toHaveAttribute("aria-pressed", "false");
    fireEvent.click(record);
    expect(useDesk.getState().startRecording).toHaveBeenCalled();
    expect(screen.getByRole("button", { name: "Create" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Create" }));
    const menu = screen.getByRole("menu", { name: "Create a Desk item" });
    expect(menu).toBeInTheDocument();
    for (const label of ["Note", "Zone", "Knowledge", "Persona", "Workflow"]) {
      expect(
        screen.getByRole("menuitem", { name: `Create ${label}` }),
      ).toBeInTheDocument();
    }

    fireEvent.click(screen.getByRole("menuitem", { name: "Create Persona" }));
    expect(useDesk.getState().createPrimitive).toHaveBeenCalledWith("recipe");
  });

  it("keeps every moved advanced route in the Desk tool shelf", () => {
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Tools/ }));

    // HS-95-04: the shelf is a dispatcher now — every advanced tool is a
    // button that opens its surface in-world (or falls back to the legacy
    // route until its story lands). Every tool remains reachable.
    for (const tool of DESK_TOOLS) {
      expect(
        screen.getByRole("button", { name: new RegExp(tool.label) }),
      ).toBeTruthy();
    }
  });

  it("finds a Desk object and opens its existing inspector", () => {
    const openPullout = vi.fn();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "Release checklist" }],
      },
      openPullout,
    });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Tools/ }));
    fireEvent.change(
      screen.getByRole("searchbox", { name: "Search tools and Desk items" }),
      { target: { value: "release" } },
    );
    fireEvent.click(screen.getByRole("button", { name: /Release checklist/ }));
    expect(openPullout).toHaveBeenCalledWith("note:n1");
  });

  it("discovers Project, Integration, and Runs on resources without Studio", () => {
    const openToolInspector = vi.fn();
    useDesk.setState({
      projects: [
        {
          id: "orion",
          name: "Project Orion",
          description: "Launch work",
          keywords: [],
          team_members: [],
          is_archived: false,
          meeting_count: 2,
          updated_at: "2026-07-11T00:00:00Z",
        },
      ],
      inferenceTargets: [
        {
          version: 1,
          id: "this_machine",
          profile_id: null,
          name: "This device",
          kind: "this_device",
          boundary: "same_device",
          owner: "you",
          transport: "in_process",
          data_scope: { sent: ["instruction"], returned: ["result"] },
          engine: "local",
          model: "",
          context_limit: 16_384,
          readiness: { state: "ready", available: true, reason: "" },
          secret: { required: false, present: false },
        },
      ],
      models: [
        {
          name: "Qwen local",
          source: "hub",
          profile_id: null,
        },
      ],
      setup: {
        trust: {
          destinations: [
            {
              id: "slack",
              name: "Slack",
              operation: "Send approved text",
              enabled: true,
              destination: "Launch workspace",
              boundary: "External service",
              data_class: "Selected text",
              authority_basis: "Per-action approval",
              background_ability: "No",
              revoke_action: "Clear the credential",
            },
          ],
        },
      },
      openToolInspector,
    });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Tools/ }));

    expect(
      screen.getByRole("button", { name: /Project Orion/ }),
    ).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Slack/ })).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /This device/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /Qwen local/ }),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /Project Orion/ }));
    expect(openToolInspector).toHaveBeenCalledWith("project", "orion");
  });

  it("reveals only ready actions that accept selected material", () => {
    const openPullout = vi.fn();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [
          {
            kind: "note",
            id: "release",
            title: "Release checklist",
            bodyMarkdown: "Ship after checks pass.",
          },
        ],
        recipe: [
          {
            kind: "recipe",
            id: "scout",
            name: "Scout",
            capability: {
              readiness: { state: "ready" },
              input_schema: { required: ["input"] },
              effect_classes: ["creates_artifact"],
            },
          },
          {
            kind: "recipe",
            id: "offline",
            name: "Offline",
            capability: {
              readiness: { state: "unavailable" },
              input_schema: { required: ["input"] },
              effect_classes: ["creates_artifact"],
            },
          },
        ],
      },
      selectedIds: ["note:release"],
      openPullout,
    });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Tools/ }));

    const action = screen.getByRole("button", {
      name: /Ask Scout about Release checklist/,
    });
    expect(action).toBeInTheDocument();
    expect(screen.queryByText(/Ask Offline/)).not.toBeInTheDocument();
    fireEvent.click(action);
    expect(openPullout).toHaveBeenCalledWith("persona:scout");
  });
});

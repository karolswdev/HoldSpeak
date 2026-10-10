import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { Note, Persona } from "../../lib/primitives";
import { EMPTY_ITEMS } from "../api";
import { registerSurface } from "../shell";
import { useDesk } from "../store";
import { DeskToolShelf, DESK_TOOLS } from "./DeskToolShelf";
import { useDrawers } from "../drawer/store";

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

  // PHILO-17: the empty Floor (EmptyDesk) is parked with the Floor.
  it("keeps every moved advanced route in the Desk tool shelf", () => {
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    expect(
      screen.getByRole("option", { name: /^New Note\b/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /^New Decision\b/ }),
    ).toBeInTheDocument();

    // HS-95-04: the shelf is a dispatcher now — every advanced tool is a
    // button that opens its surface in-world (or falls back to the legacy
    // route until its story lands). Every tool remains reachable.
    for (const tool of DESK_TOOLS) {
      // HS-111-10: the query well's speak-to-fill mic is also a button
      // ("Speak …") — the dispatcher row is the non-mic hit.
      const hits = screen.getAllByRole("option", {
        name: new RegExp(tool.label),
      });
      expect(hits.some((el) => !el.className.includes("desk-mic"))).toBe(true);
    }
  });

  it("finds a Desk object and opens its existing inspector", () => {
    const openPullout = vi.fn();
    useDesk.setState({
      items: {
        ...EMPTY_ITEMS,
        note: [{ kind: "note", id: "n1", title: "Release checklist" } as Note],
      },
      openPullout,
    });
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    fireEvent.change(
      screen.getByRole("combobox", { name: "Search tools and Desk items" }),
      { target: { value: "release" } },
    );
    fireEvent.click(screen.getByRole("option", { name: /Release checklist/ }));
    expect(openPullout).toHaveBeenCalledWith("note:n1");
  });

  it("discovers Project, Integration, and Runs on resources without Studio", () => {
    const openToolInspector = vi.fn();
    useDrawers.setState({ drawers: [], infos: [] });
    const openRoom = vi.fn();
    const unregisterProject = registerSurface(
      "open-project-memory",
      openRoom,
    );
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
          id: "this_machine",
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
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));

    // The cold deck keeps SETTINGS intentionally dense; every resource remains
    // discoverable through its own combobox query.
    expect(
      screen.getByRole("combobox", { name: "Search tools and Desk items" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("option", { name: /Project Orion/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: /Project Orion/ }));
    // PHILO-14 A2: the palette opens a Project as its drawer, never the Room.
    expect(useDrawers.getState().drawers.map((d) => d.projectId)).toEqual(["orion"]);
    expect(openRoom).not.toHaveBeenCalled();
    expect(openToolInspector).not.toHaveBeenCalledWith("project", "orion");

    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    const reopenedSearch = screen.getByRole("combobox", {
      name: "Search tools and Desk items",
    });
    fireEvent.change(reopenedSearch, { target: { value: "Slack" } });
    expect(screen.getByRole("option", { name: /Slack/ })).toBeInTheDocument();
    fireEvent.change(reopenedSearch, { target: { value: "This device" } });
    expect(screen.getByRole("option", { name: /This device/ })).toBeInTheDocument();
    fireEvent.change(reopenedSearch, { target: { value: "Qwen local" } });
    expect(screen.getByRole("option", { name: /Qwen local/ })).toBeInTheDocument();
    unregisterProject();
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
          } as Note,
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
          } as Persona,
          {
            kind: "recipe",
            id: "offline",
            name: "Offline",
            capability: {
              readiness: { state: "unavailable" },
              input_schema: { required: ["input"] },
              effect_classes: ["creates_artifact"],
            },
          } as Persona,
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
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));

    const action = screen.getByRole("option", {
      name: /Ask Scout about Release checklist/,
    });
    expect(action).toBeInTheDocument();
    expect(screen.queryByText(/Ask Offline/)).not.toBeInTheDocument();
    fireEvent.click(action);
    expect(openPullout).toHaveBeenCalledWith("persona:scout");
  });
});

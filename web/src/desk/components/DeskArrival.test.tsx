import { BUILDER_APPLICATION_ACTIONS } from "../applications";
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
      recentOpened: [],
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
  it("keeps every moved advanced route in the Desk tool shelf", async () => {
    render(
      <MemoryRouter>
        <DeskToolShelf />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    // PHILO-17 (palette-rank): the list draws once its ranking reads resolve.
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "new" } });
    expect(
      screen.getByRole("option", { name: /^New Note\b/ }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("option", { name: /^New Decision\b/ }),
    ).toBeInTheDocument();

    // HS-95-04: the shelf is a dispatcher now — every advanced tool is a
    // button that opens its surface in-world (or falls back to the legacy
    // route until its story lands). Every tool remains reachable.
    // Betterment shell S1: builder tools are listed only when Builder tools is on.
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "" } });
    for (const tool of DESK_TOOLS.filter((t) => !BUILDER_APPLICATION_ACTIONS.has(t.action))) {
      // HS-111-10: the query well's speak-to-fill mic is also a button
      // ("Speak …") — the dispatcher row is the non-mic hit.
      const hits = screen.getAllByRole("option", {
        name: new RegExp(tool.label),
      });
      expect(hits.some((el) => !el.className.includes("desk-mic"))).toBe(true);
    }
  });

  it("finds a Desk object and opens its existing inspector", async () => {
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
    // PHILO-17 (palette-rank): the list draws once its ranking reads resolve.
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    fireEvent.change(
      screen.getByRole("combobox", { name: "Find, open or ask" }),
      { target: { value: "release" } },
    );
    fireEvent.click(screen.getByRole("option", { name: /Release checklist/ }));
    expect(openPullout).toHaveBeenCalledWith("note:n1");
  });

  it("discovers Project, Integration, and Runs on resources without Studio", async () => {
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
    // PHILO-17 (palette-rank): the list draws once its ranking reads resolve.
    await screen.findByRole("listbox", {}, { timeout: 2000 });

    // The cold deck lists apps and recent opens; each resource is found by name.
    expect(
      screen.getByRole("combobox", { name: "Find, open or ask" }),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "Orion" } });
    expect(screen.getByRole("option", { name: /^Open Project Orion\b/ })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("option", { name: /^Open Project Orion\b/ }));
    // PHILO-17 U30: the palette opens a Project's Room (one home), never a drawer.
    expect(openRoom).toHaveBeenCalled();
    expect(openRoom.mock.calls[0][0]).toBe("project:orion");
    expect(useDrawers.getState().drawers).toEqual([]);
    expect(openToolInspector).not.toHaveBeenCalledWith("project", "orion");

    fireEvent.click(screen.getByRole("button", { name: /Search/ }));
    // PHILO-17 (palette-rank): the list draws once its ranking reads resolve.
    await screen.findByRole("listbox", {}, { timeout: 2000 });
    const reopenedSearch = screen.getByRole("combobox", {
      name: "Find, open or ask",
    });
    fireEvent.change(reopenedSearch, { target: { value: "Slack" } });
    // Betterment Q3: the Ask "…" row also names the text; the object row is the other one.
    expect(screen.getByRole("option", { name: (n) => /Slack/.test(n) && !n.includes("Ask \"") })).toBeInTheDocument();
    fireEvent.change(reopenedSearch, { target: { value: "This device" } });
    expect(screen.getByRole("option", { name: (n) => /This device/.test(n) && !n.includes("Ask \"") })).toBeInTheDocument();
    fireEvent.change(reopenedSearch, { target: { value: "Qwen local" } });
    expect(screen.getByRole("option", { name: (n) => /Qwen local/.test(n) && !n.includes("Ask \"") })).toBeInTheDocument();
    unregisterProject();
  });

  it("reveals only ready actions that accept selected material", async () => {
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
    // PHILO-17 (palette-rank): the list draws once its ranking reads resolve.
    await screen.findByRole("listbox", {}, { timeout: 2000 });

    fireEvent.change(screen.getByRole("combobox", { name: "Find, open or ask" }), { target: { value: "Scout" } });
    const action = screen.getByRole("option", {
      name: /Ask Scout about Release checklist/,
    });
    expect(action).toBeInTheDocument();
    expect(screen.queryByText(/Ask Offline/)).not.toBeInTheDocument();
    fireEvent.click(action);
    expect(openPullout).toHaveBeenCalledWith("persona:scout");
  });
});

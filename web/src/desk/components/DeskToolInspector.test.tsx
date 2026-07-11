import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { DeskToolInspector } from "./DeskToolInspector";

const slack = {
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
};

function json(body: unknown) {
  return new Response(JSON.stringify(body), {
    status: 200,
    headers: { "content-type": "application/json" },
  });
}

describe("HS-93-04 Desk tool inspector", () => {
  beforeEach(() => {
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
      },
      projects: [],
      inferenceTargets: [],
      models: [],
      setup: { trust: { destinations: [slack] } },
      selectedIds: ["note:release"],
      toolInspector: null,
      closeToolInspector: vi.fn(),
      openPullout: vi.fn(),
      openChat: vi.fn(),
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it("binds an Integration proposal and Receipt to the exact selected source", async () => {
    const fetcher = vi.fn(async (input: string, init?: RequestInit) => {
      const url = String(input);
      if (url.endsWith("/api/desk/actuators/slack/propose")) {
        return json({
          proposal: {
            id: "p1",
            status: "proposed",
            target: "slack",
            preview: "Send Release checklist to Launch workspace",
            commitment: { approve: "Approve and send to Slack" },
            payload: {
              _source: {
                ref: "note:release",
                label: "Release checklist",
              },
            },
          },
        });
      }
      if (url.includes("/api/desk/actuators/slack/p1/decision")) {
        expect(JSON.parse(String(init?.body))).toEqual({
          decision: "approved",
          decided_by: "web-desk",
        });
        return json({
          proposal: {
            id: "p1",
            status: "executed",
            target: "slack",
            preview: "Send Release checklist to Launch workspace",
            payload: {
              _source: {
                ref: "note:release",
                label: "Release checklist",
              },
            },
          },
        });
      }
      if (url.startsWith("/api/desk/projections?")) {
        return json({
          projections: [],
          counts: {},
          subject_counts: {},
          page: { offset: 0, limit: 50, total: 0, has_more: false },
        });
      }
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetcher);
    useDesk.setState({
      toolInspector: { kind: "integration", id: "slack" },
    });

    render(
      <MemoryRouter>
        <DeskToolInspector />
      </MemoryRouter>,
    );

    expect(screen.getByText("Launch workspace")).toBeInTheDocument();
    expect(screen.getByText("Ship after checks pass.")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Send Release checklist to Slack",
      }),
    );

    expect(
      await screen.findByRole("button", { name: "Approve and send to Slack" }),
    ).toBeInTheDocument();
    const proposed = JSON.parse(
      String((fetcher.mock.calls[0][1] as RequestInit).body),
    );
    expect(proposed).toMatchObject({
      text: "Ship after checks pass.",
      source_ref: "note:release",
      source_label: "Release checklist",
    });

    useDesk.setState({ selectedIds: [] });
    fireEvent.click(
      screen.getByRole("button", { name: "Approve and send to Slack" }),
    );
    expect(await screen.findByText("Receipt · executed")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", { name: "Return to Release checklist" }),
    );
    expect(useDesk.getState().openPullout).toHaveBeenCalledWith("note:release");
  });

  it("opens related Project material with its qualified identity", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () =>
        json({
          resources: [{ resource_ref: "note:release", relationship: "member" }],
        }),
      ),
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
      toolInspector: { kind: "project", id: "orion" },
    });

    render(
      <MemoryRouter>
        <DeskToolInspector />
      </MemoryRouter>,
    );

    const material = await screen.findByRole("button", {
      name: /Release checklist/,
    });
    fireEvent.click(material);
    await waitFor(() =>
      expect(useDesk.getState().openPullout).toHaveBeenCalledWith(
        "note:release",
      ),
    );
  });
});

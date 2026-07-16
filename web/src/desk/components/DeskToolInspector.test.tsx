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
      if (url.endsWith("/api/authority/policy")) {
        return json({
          control_mode: "neutral",
          control_mode_label: "Normal",
          control_mode_description:
            "Runs routine configured work and asks at consequential boundaries.",
          policy_version: "operation-policy/v2",
          source: "config",
        });
      }
      if (url.endsWith("/api/desk/actuators/slack/propose")) {
        return json({
          proposal: {
            id: "p1",
            status: "proposed",
            target: "slack",
            preview: "Send Release checklist to Launch workspace",
            commitment: { approve: "Approve and send to Slack" },
            operation: {
              effect_class: "slack/post_message",
              destination: "slack:sha256:fixed",
              consequence: "execute_now",
            },
            policy_snapshot: {
              mode: "neutral",
              policy_version: "operation-policy/v2",
              outcome: "authorization_required",
              reason_code: "per_action_authorization_required",
              authority_basis: "per_action_required",
              next_state: "awaiting_authorization",
            },
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
    const proposeCall = fetcher.mock.calls.find(([url]) =>
      String(url).endsWith("/api/desk/actuators/slack/propose"),
    );
    const proposed = JSON.parse(String((proposeCall?.[1] as RequestInit).body));
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

  it("renders YOLO posture authority and the immediate Receipt without an approval prompt", async () => {
    const fetcher = vi.fn(async (input: string) => {
      const url = String(input);
      if (url.endsWith("/api/authority/policy")) {
        return json({
          control_mode: "yolo",
          control_mode_label: "YOLO",
          control_mode_description:
            "Runs eligible configured work without HoldSpeak approval prompts.",
          policy_version: "operation-policy/v2",
          source: "config",
        });
      }
      if (url.endsWith("/api/desk/actuators/slack/propose")) {
        return json({
          proposal: {
            id: "p-yolo",
            status: "executed",
            target: "slack",
            preview: "Send Release checklist to Launch workspace",
            operation: {
              effect_class: "slack/post_message",
              destination: "slack:sha256:fixed",
              consequence: "execute_now",
            },
            policy_snapshot: {
              mode: "yolo",
              policy_version: "operation-policy/v2",
              outcome: "allowed",
              reason_code: "configured_destination_posture_allowed",
              authority_basis: "control_posture",
              next_state: "execute_now",
            },
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

    expect(await screen.findByText("YOLO")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Send Release checklist to Slack",
      }),
    );
    expect(await screen.findByText("Receipt · executed")).toBeInTheDocument();
    // The wire's control_posture authority renders as its product label —
    // present both as the fact label and as the authority value.
    expect(screen.getAllByText("Control posture").length).toBeGreaterThan(1);
    expect(screen.queryByText("control_posture")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Approve and send to Slack" }),
    ).not.toBeInTheDocument();
    expect(
      fetcher.mock.calls.some(([url]) => String(url).includes("/decision")),
    ).toBe(false);
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

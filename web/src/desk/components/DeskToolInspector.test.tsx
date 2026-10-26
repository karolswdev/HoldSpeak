import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { Note } from "../../lib/primitives";
import { EMPTY_ITEMS } from "../api";
import { useDesk } from "../store";
import { DeskToolInspector } from "./DeskToolInspector";
import inspectorChrome from "./chrome-menus.css?raw";

// PHILO-11-05: the free-text desk Slack send is parked (design section 6, D1); the
// inspector's integration flow is fenced on the Custom webhook, which keeps it.
const webhook = {
  id: "companion_webhook",
  name: "Custom webhook",
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
          } as Note,
        ],
      },
      projects: [],
      inferenceTargets: [],
      models: [],
      setup: { trust: { destinations: [webhook] } },
      selectedIds: ["note:release"],
      toolInspector: null,
      closeToolInspector: vi.fn(),
      openPullout: vi.fn(),
      openChat: vi.fn(),
    });
  });

  afterEach(() => vi.unstubAllGlobals());

  it("keeps the Inspector in the desk plane while the shared frame owns geometry and material", () => {
    const host = inspectorChrome.match(/\.desk-next \.desk-tool-inspector\s*\{([^}]+)\}/)?.[1] ?? "";
    expect(host).toMatch(/position:\s*fixed/);
    expect(host).toMatch(/display:\s*flex/);
    expect(host).toMatch(/flex-direction:\s*column/);
    expect(host).toMatch(/overflow:\s*hidden/);
    expect(host).not.toMatch(/(?:^|;)\s*(?:top|right|bottom|left|width|height|z-index|border|background|box-shadow)\s*:/);
  });

  it.each([
    ["executed", undefined, "success", "Executed"],
    ["failed", undefined, "failure", "Failed"],
    ["rejected", undefined, "idle", "Rejected"],
    ["proposed", "refused", "warning", "Refused"],
  ] as const)("keeps %s %s receipts honest in the library footer", async (status, outcome, tone, label) => {
    const fetcher = vi.fn(async (input: string) => {
      const url = String(input);
      if (url.endsWith("/api/authority/policy")) return json({ control_mode: "neutral", control_mode_label: "Normal" });
      if (url.endsWith("/propose")) return json({ proposal: {
        id: "outcome-1", target: "webhook", status, preview: "Send the selected release checklist",
        policy_snapshot: { outcome }, error: status === "failed" ? "Endpoint unavailable" : undefined,
        payload: { _source: { ref: "note:release", label: "Release checklist" } },
      } });
      if (url.endsWith("/api/desk/actuators/webhook/outcome-1/decision")) return json({ proposal: {
        id: "outcome-1", target: "webhook", status: "executed", preview: "Send the selected release checklist",
        payload: { _source: { ref: "note:release", label: "Release checklist" } },
      } });
      if (url.startsWith("/api/desk/projections?")) return json({ projections: [], counts: {}, subject_counts: {}, page: { total: 0, has_more: false } });
      throw new Error(`Unexpected request: ${url}`);
    });
    vi.stubGlobal("fetch", fetcher);
    useDesk.setState({ toolInspector: { kind: "integration", id: "companion_webhook" } });
    const { container } = render(<MemoryRouter><DeskToolInspector /></MemoryRouter>);
    const post = screen.getByRole("button", { name: "Post Release checklist to Custom webhook" });
    expect(post).toHaveClass("btn");
    expect(post).toHaveAttribute("title", "Goes to Launch workspace");
    fireEvent.click(post);
    const receipt = await screen.findByRole("status", { name: label });
    expect(receipt).toHaveAttribute("data-state", tone);
    expect(receipt.closest(".surface-footer-receipt")).not.toBeNull();
    expect(screen.getByRole("button", { name: "Return to Release checklist" })).toHaveClass("btn");
    expect(container.querySelector(".desk-integration-receipt")).toBeNull();
    // Owner ruling 2026-10-25 (UX-CANON A.9): no egress chip in the status bar; the verb names the route.
    expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeNull();
    if (status === "failed") {
      expect(screen.getByRole("button", { name: /Retry/ })).toHaveClass("btn");
      expect(screen.getByRole("alert")).toHaveTextContent("Endpoint unavailable");
      fireEvent.click(screen.getByRole("button", { name: /Retry/ }));
      expect(await screen.findByRole("status", { name: "Executed" })).toHaveAttribute("data-state", "success");
      const retryCall = fetcher.mock.calls.find(([url]) => String(url).endsWith("/webhook/outcome-1/decision"));
      expect(retryCall).toBeTruthy();
    }
    if (outcome === "refused") expect(screen.queryByRole("button", { name: /Approve/ })).not.toBeInTheDocument();
  });

  it("names a known endpoint host at the action without exposing its path", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => json({ control_mode: "neutral" })));
    useDesk.setState({
      setup: { trust: { destinations: [{ ...webhook, destination: "https://hooks.example.invalid/private-path" }] } },
      toolInspector: { kind: "integration", id: "companion_webhook" },
    });
    const { container } = render(<MemoryRouter><DeskToolInspector /></MemoryRouter>);
    expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeNull();
    const verb = screen.getByRole("button", { name: "Post Release checklist to Custom webhook" });
    expect(verb).toHaveAttribute("title", "Goes to hooks.example.invalid");
  });

  it("keeps the exact GitHub repository visible before creating an issue and its host on the verb", () => {
    vi.stubGlobal("fetch", vi.fn(async () => json({ control_mode: "neutral" })));
    useDesk.setState({
      setup: { trust: { destinations: [{ ...webhook, id: "github", name: "GitHub", destination: "owner/architecture-reports" }] } },
      toolInspector: { kind: "integration", id: "github" },
    });
    const { container } = render(<MemoryRouter><DeskToolInspector /></MemoryRouter>);
    expect(container.querySelector(".desk-tool-status .surface-primary")).toHaveTextContent("owner/architecture-reports");
    const create = screen.getByRole("button", { name: "Create GitHub issue from Release checklist" });
    expect(create).toBeVisible();
    expect(create).toHaveAttribute("title", "Goes to github.com");
    expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeNull();
  });

  it("names an unconfigured integration once without repeating a placeholder destination", () => {
    vi.stubGlobal("fetch", vi.fn(async () => json({ control_mode: "neutral" })));
    useDesk.setState({
      setup: { trust: { destinations: [{ ...webhook, enabled: false, destination: "Not configured" }] } },
      toolInspector: { kind: "integration", id: "companion_webhook" },
    });
    const { container } = render(<MemoryRouter><DeskToolInspector /></MemoryRouter>);
    expect(screen.getAllByText("Not configured")).toHaveLength(1);
    expect(container.querySelector(".desk-tool-status .surface-primary")).toBeNull();
    expect(container.querySelector(".surface-footer-egress .gadget-chip-egress")).toBeNull();
    expect(screen.getByRole("button", { name: "Configure Custom webhook" })).toHaveClass("btn");
  });

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
      if (url.endsWith("/api/desk/actuators/webhook/propose")) {
        return json({
          proposal: {
            id: "p1",
            status: "proposed",
            target: "webhook",
            preview: "Send Release checklist to Launch workspace",
            commitment: { approve: "Approve and post to webhook" },
            operation: {
              effect_class: "webhook/post",
              destination: "webhook:sha256:fixed",
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
      if (url.includes("/api/desk/actuators/webhook/p1/decision")) {
        expect(JSON.parse(String(init?.body))).toEqual({
          decision: "approved",
          decided_by: "web-desk",
        });
        return json({
          proposal: {
            id: "p1",
            status: "executed",
            target: "webhook",
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
      toolInspector: { kind: "integration", id: "companion_webhook" },
    });

    render(
      <MemoryRouter>
        <DeskToolInspector />
      </MemoryRouter>,
    );

    expect(document.querySelector(".desk-tool-status")).toHaveTextContent("Launch workspace");
    expect(screen.getByText("Ship after checks pass.")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Post Release checklist to Custom webhook",
      }),
    );

    expect(
      await screen.findByRole("button", { name: "Approve and post to webhook" }),
    ).toBeInTheDocument();
    const proposeCall = fetcher.mock.calls.find(([url]) =>
      String(url).endsWith("/api/desk/actuators/webhook/propose"),
    );
    const proposed = JSON.parse(String((proposeCall?.[1] as RequestInit).body));
    expect(proposed).toMatchObject({
      text: "Ship after checks pass.",
      source_ref: "note:release",
      source_label: "Release checklist",
    });

    useDesk.setState({ selectedIds: [] });
    fireEvent.click(
      screen.getByRole("button", { name: "Approve and post to webhook" }),
    );
    expect(await screen.findByRole("status", { name: "Executed" })).toHaveAttribute("data-state", "success");
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
      if (url.endsWith("/api/desk/actuators/webhook/propose")) {
        return json({
          proposal: {
            id: "p-yolo",
            status: "executed",
            target: "webhook",
            preview: "Send Release checklist to Launch workspace",
            operation: {
              effect_class: "webhook/post",
              destination: "webhook:sha256:fixed",
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
      toolInspector: { kind: "integration", id: "companion_webhook" },
    });

    render(
      <MemoryRouter>
        <DeskToolInspector />
      </MemoryRouter>,
    );

    expect(await screen.findByText("YOLO")).toBeInTheDocument();
    fireEvent.click(
      screen.getByRole("button", {
        name: "Post Release checklist to Custom webhook",
      }),
    );
    expect(await screen.findByRole("status", { name: "Executed" })).toHaveAttribute("data-state", "success");
    // The wire's control_posture authority renders as its product label —
    // present both as the fact label and as the authority value.
    expect(screen.getAllByText("Control posture").length).toBeGreaterThan(1);
    expect(screen.queryByText("control_posture")).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: "Approve and post to webhook" }),
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

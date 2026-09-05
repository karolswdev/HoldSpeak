import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { WorkbenchWindow } from "../WorkbenchWindow";

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
}));

const ITEM = {
  id: "item-1", title: "Review the plan", body: "", priority: 3, status: "pending",
  grounding: {}, result: null, result_egress: null, result_artifact_id: null,
  mint_attempted: false, tokens_consumed: 0, created_at: "2026-08-16T00:00:00Z", completed_at: null,
};

const DETAIL = {
  id: "wb1", name: "Review desk", recipe_id: "agent-1", profile_id: null,
  resolver_profile_id: null, schedule: null, schedule_enabled: false,
  items: [ITEM], item_count: 1, pending_count: 1, last_run: null,
};

function automation(enabled = false) {
  return {
    id: "auto-1", name: "GitHub · Review requested", provider: "github",
    event_kind: "github.review_requested", enabled,
    status: enabled ? "active" : "paused", adapter_status: "ready",
    last_good_at: "2026-08-16T08:00:00Z",
  };
}

function mockHub(initialAutomations: Record<string, unknown>[] = []) {
  let automations = initialAutomations;
  let resourceful = {
    workbench_id: "wb1", enabled: false, idle_after_minutes: 30,
    cooldown_hours: 6, nightly_target: 2, night_only: true,
    night_start_hour: 22, night_end_hour: 7,
    routines: ["loose_ideas", "failed_work"], nightly_count: 0,
  };
  const calls = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = (init?.method || "GET").toUpperCase();
    const json = (body: unknown) => new Response(JSON.stringify(body), { headers: { "content-type": "application/json" } });
    if (/\/resourceful$/.test(url) && method === "GET") return json({ policy: resourceful });
    if (/\/resourceful$/.test(url) && method === "PUT") {
      resourceful = { ...resourceful, ...JSON.parse(String(init?.body || "{}")) };
      return json({ policy: resourceful });
    }
    if (/\/automations\/auto-1\/history$/.test(url)) return json({ history: [] });
    if (/\/automations$/.test(url) && method === "GET") return json({ automations });
    if (/\/automations$/.test(url) && method === "POST") {
      const body = JSON.parse(String(init?.body || "{}"));
      automations = [{ ...automation(false), name: "GitHub · Review requested", repository: body.repository }];
      return json({ automation: automations[0] });
    }
    if (/\/automations\/auto-1\/test$/.test(url)) {
      return json({ entity_count: 1, changes: [], would_project: 0 });
    }
    if (/\/automations\/auto-1$/.test(url) && method === "PATCH") {
      const body = JSON.parse(String(init?.body || "{}"));
      automations = [{ ...automation(Boolean(body.enabled)) }];
      return json({ automation: automations[0] });
    }
    if (/\/runs$/.test(url)) return json({ runs: [] });
    if (/\/memory$/.test(url)) return json({ entries: [] });
    if (/\/api\/skills/.test(url)) return json({ skills: [] });
    if (/\/api\/workbenches\/wb1$/.test(url)) return json({ workbench: DETAIL });
    return json({});
  });
  vi.stubGlobal("fetch", calls);
  return calls;
}

async function open(automations: Record<string, unknown>[] = []) {
  useDesk.setState({
    items: { ...EMPTY_ITEMS, workbench: [{ kind: "workbench", id: "wb1", name: "Review desk" } as never] },
    inferenceTargets: [], profiles: [],
  });
  const calls = mockHub(automations);
  render(<WorkbenchWindow workbenchId="wb1" />);
  await screen.findByText("Review the plan");
  await userEvent.setup().click(screen.getByRole("button", { name: "Expand configuration" }));
  return calls;
}

describe("Workbench STARTS WHEN automations", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it("reveals one start mode at a time and requires a repository for Event", async () => {
    await open();
    expect(screen.getByText("Starts only when you press Run.")).toBeInTheDocument();
    expect(screen.queryByLabelText("GitHub repository")).not.toBeInTheDocument();

    await userEvent.setup().click(screen.getByRole("radio", { name: "Schedule" }));
    expect(screen.getByRole("button", { name: "7 AM daily" })).toBeInTheDocument();
    expect(screen.queryByLabelText("GitHub repository")).not.toBeInTheDocument();

    await userEvent.setup().click(screen.getByRole("radio", { name: "Event" }));
    expect(screen.getByLabelText("GitHub repository")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "7 AM daily" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /GitHub · Review requested/i })).toBeDisabled();
    expect(screen.getByText("REPOSITORY REQUIRED")).toBeInTheDocument();
  });

  it("creates the GitHub review-requested preset with an explicit repository", async () => {
    const calls = await open();
    const user = userEvent.setup();
    await user.click(screen.getByRole("radio", { name: "Event" }));
    await user.type(screen.getByLabelText("GitHub repository"), "karolswdev/HoldSpeak");
    await user.click(screen.getByRole("button", { name: /GitHub · Review requested/i }));

    await waitFor(() => expect(calls.mock.calls.some(([url, init]) =>
      String(url).endsWith("/api/workbenches/wb1/automations") &&
      (init as RequestInit).method === "POST",
    )).toBe(true));
    const [, init] = calls.mock.calls.find(([url, request]) =>
      String(url).endsWith("/api/workbenches/wb1/automations") &&
      (request as RequestInit).method === "POST",
    )!;
    expect(JSON.parse(String((init as RequestInit).body))).toEqual({
      preset_id: "github-review-requested",
      repository: "karolswdev/HoldSpeak",
    });
  });

  it("tests without delivering work, then enables and pauses the trigger", async () => {
    const calls = await open([automation(false)]);
    const user = userEvent.setup();
    await user.click(screen.getByRole("radio", { name: "Event" }));
    await screen.findByText("GitHub · Review requested");
    const automationButton = screen
      .getAllByRole("button", { name: /GitHub · Review requested/ })
      .find((button) => !button.hasAttribute("disabled"));
    expect(automationButton).toBeDefined();
    await user.click(automationButton!);
    expect(screen.getByText(/SILENT BASELINE/)).toBeInTheDocument();
    expect(screen.queryByText(/auto-run/i)).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Test match" }));
    await waitFor(() => expect(calls.mock.calls.some(([url]) => String(url).endsWith("/automations/auto-1/test"))).toBe(true));
    expect(calls.mock.calls.some(([url]) => /\/items(?:\/|$)/.test(String(url)))).toBe(false);
    expect(screen.getByText(/TEST ·/)).toBeVisible();

    await user.click(screen.getByRole("button", { name: "Enable" }));
    await waitFor(() => expect(calls.mock.calls.some(([url, init]) =>
      String(url).endsWith("/automations/auto-1") && (init as RequestInit).method === "PATCH",
    )).toBe(true));
    expect(screen.getByText("BASELINE ESTABLISHED")).toBeInTheDocument();
    await screen.findByRole("button", { name: "Pause" });
    await user.click(screen.getByRole("button", { name: "Pause" }));
    await waitFor(() => expect(calls.mock.calls.filter(([url, init]) =>
      String(url).endsWith("/automations/auto-1") && (init as RequestInit).method === "PATCH",
    )).toHaveLength(2));
  });

  it("pauses an active event automation when Manual is selected", async () => {
    const calls = await open([automation(true)]);
    const user = userEvent.setup();
    expect(screen.getByRole("radio", { name: "Event" })).toHaveAttribute("aria-checked", "true");

    await user.click(screen.getByRole("radio", { name: "Manual" }));

    await waitFor(() => expect(calls.mock.calls.some(([url, init]) => {
      if (!String(url).endsWith("/automations/auto-1") || (init as RequestInit).method !== "PATCH") {
        return false;
      }
      return JSON.parse(String((init as RequestInit).body)).enabled === false;
    })).toBe(true));
  });

  it("starts from the six-hour nightly preset but persists per-Workbench policy changes", async () => {
    const calls = await open();
    const user = userEvent.setup();

    await user.click(screen.getByRole("radio", { name: "Idle" }));

    expect(screen.getByText("6H COOLDOWN")).toBeInTheDocument();
    expect(screen.getByText("TARGET 2 / NIGHT")).toBeInTheDocument();
    expect(screen.getByText(/ONLY THE SELECTED MAINTENANCE ITEM RUNS/)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Decrease Cooldown hours" }));
    await user.click(screen.getByRole("button", { name: "Decrease Cooldown hours" }));
    await user.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    expect(screen.getByText("4H COOLDOWN")).toBeInTheDocument();
    expect(screen.getByText("TARGET 3 / NIGHT")).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Enable overnight resourcefulness" }));
    await user.click(screen.getByRole("button", { name: "RUN AS OWNER?" }));

    await waitFor(() => expect(calls.mock.calls.some(([url, init]) => {
      if (!String(url).endsWith("/resourceful") || (init as RequestInit).method !== "PUT") return false;
      const body = JSON.parse(String((init as RequestInit).body));
      return body.enabled === true && body.cooldown_hours === 4 && body.nightly_target === 3;
    })).toBe(true));
  });
});

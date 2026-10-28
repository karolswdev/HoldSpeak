import { fireEvent, render, screen, waitFor } from "@testing-library/react";
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

function mockHub(initialAutomations: Record<string, unknown>[] = [], detailOverrides: Record<string, unknown> = {}, resourcefulOverrides: Record<string, unknown> = {}) {
  let automations = initialAutomations;
  let detail = { ...DETAIL, ...detailOverrides };
  let resourceful = {
    workbench_id: "wb1", enabled: false, idle_after_minutes: 30,
    cooldown_hours: 6, nightly_target: 2, night_only: true,
    night_start_hour: 22, night_end_hour: 7,
    routines: ["loose_ideas", "failed_work"], nightly_count: 0,
    ...resourcefulOverrides,
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
    if (/\/api\/workbenches\/wb1$/.test(url)) {
      if (method === "PUT") detail = { ...detail, ...JSON.parse(String(init?.body || "{}")) };
      return json({ workbench: detail });
    }
    return json({});
  });
  vi.stubGlobal("fetch", calls);
  return calls;
}

async function open(automations: Record<string, unknown>[] = [], detailOverrides: Record<string, unknown> = {}, resourcefulOverrides: Record<string, unknown> = {}) {
  useDesk.setState({
    items: { ...EMPTY_ITEMS, workbench: [{ kind: "workbench", id: "wb1", name: "Review desk" } as never] },
    inferenceTargets: [], profiles: [],
  });
  const calls = mockHub(automations, detailOverrides, resourcefulOverrides);
  render(<WorkbenchWindow workbenchId="wb1" />);
  await screen.findByText("Review the plan");
  await userEvent.setup().click(screen.getByRole("button", { name: "Configure" }));
  return calls;
}

describe("Workbench STARTS WHEN automations", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => { vi.unstubAllGlobals(); vi.restoreAllMocks(); });

  it("keeps a custom cron visible and persists Schedule and Enabled through the original writer", async () => {
    const calls = await open([], { schedule: "15 9 * * 2", schedule_enabled: true });
    const schedule = screen.getByRole("combobox", { name: "Schedule" });
    expect(schedule).toHaveValue("15 9 * * 2");
    expect(screen.getByRole("option", { name: "15 9 * * 2" })).toBeInTheDocument();
    fireEvent.change(schedule, { target: { value: "0 * * * *" } });
    await waitFor(() => expect(calls.mock.calls.some(([url, init]) =>
      String(url).endsWith("/api/workbenches/wb1") && init?.method === "PUT" &&
      JSON.stringify(JSON.parse(String(init.body))) === JSON.stringify({ schedule: "0 * * * *", schedule_enabled: true }),
    )).toBe(true));
    await waitFor(() => expect(schedule).toHaveValue("0 * * * *"));
    fireEvent.click(screen.getByRole("checkbox", { name: "Schedule enabled" }));
    await waitFor(() => expect(calls.mock.calls.some(([url, init]) =>
      String(url).endsWith("/api/workbenches/wb1") && init?.method === "PUT" &&
      JSON.parse(String(init.body)).schedule_enabled === false,
    )).toBe(true));
  });

  it("a look at Event and Idle never turns the schedule off (recon step 19)", async () => {
    const calls = await open([], { schedule: "0 2 * * *", schedule_enabled: true });
    const mode = screen.getByRole("combobox", { name: "Automation start condition" });
    expect(mode).toHaveValue("schedule");
    expect(screen.getByRole("checkbox", { name: "Schedule enabled" })).toBeChecked();

    fireEvent.change(mode, { target: { value: "event" } });
    fireEvent.change(mode, { target: { value: "idle" } });
    fireEvent.change(mode, { target: { value: "manual" } });
    fireEvent.change(mode, { target: { value: "schedule" } });

    expect(screen.getByRole("checkbox", { name: "Schedule enabled" })).toBeChecked();
    const scheduleWrites = calls.mock.calls.filter(([url, init]) =>
      String(url).endsWith("/api/workbenches/wb1") && init?.method === "PUT" &&
      "schedule_enabled" in JSON.parse(String(init.body)),
    );
    expect(scheduleWrites).toHaveLength(0);
  });

  it("reveals one start mode at a time and requires a repository for Event", async () => {
    await open();
    expect(screen.getByRole("region", { name: "Starts when" })).toHaveAttribute("data-material", "inset");
    expect(screen.getByRole("combobox", { name: "Automation start condition" })).toHaveValue("manual");
    expect(screen.queryByText("Starts only when you press Run.")).toBeNull();
    expect(screen.queryByLabelText("GitHub repository")).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "schedule" } });
    expect(screen.getByRole("combobox", { name: "Schedule" })).toBeInTheDocument();
    expect(screen.queryByLabelText("GitHub repository")).not.toBeInTheDocument();

    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "event" } });
    expect(screen.getByLabelText("GitHub repository")).toBeInTheDocument();
    expect(screen.queryByRole("combobox", { name: "Schedule" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /GitHub · Review requested/i })).toBeDisabled();
    expect(screen.getByText("REPOSITORY REQUIRED")).toBeInTheDocument();
  });

  it("creates the GitHub review-requested preset with an explicit repository", async () => {
    const calls = await open();
    const user = userEvent.setup();
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "event" } });
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
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "event" } });
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

  it("looking at Manual never pauses an active event automation (Betterment A4)", async () => {
    const calls = await open([automation(true)]);
    expect(screen.getByRole("combobox", { name: "Automation start condition" })).toHaveValue("event");

    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "manual" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "idle" } });

    // Looking at another start mode writes nothing: no PATCH, no PUT (the
    // engine editors' POSTs are reads of their projection).
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(calls.mock.calls.filter(([url, init]) => {
      const method = String((init as RequestInit | undefined)?.method ?? "GET").toUpperCase();
      return method !== "GET" && !String(url).endsWith("/assignments/editor");
    })).toEqual([]);
  });

  it("starts from the six-hour nightly preset but persists per-Workbench policy changes", async () => {
    const calls = await open();
    const user = userEvent.setup();

    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "idle" } });

    expect(screen.getByText("6H COOLDOWN")).toBeInTheDocument();
    expect(screen.getByText("TARGET 2 / NIGHT")).toBeInTheDocument();
    const selectedOnly = screen.getByText("SELECTED MAINTENANCE ONLY");
    expect(selectedOnly.closest(".wb-resourceful-routines")).not.toBeNull();
    expect(screen.getByText("PENDING WORK UNTOUCHED")).toBeInTheDocument();
    expect(screen.getByText("SOURCE DATA · REVIEW-ONLY")).toBeInTheDocument();
    expect(screen.getByText("RUNS AS OWNER").closest(".wb-automation-verbs")).not.toBeNull();
    expect(screen.getByText("PAUSED")).toBeInTheDocument();
    expect(screen.queryByText(/0\/\d+ THIS NIGHT/)).toBeNull();
    await user.click(screen.getByRole("button", { name: "Decrease Cooldown hours" }));
    await user.click(screen.getByRole("button", { name: "Decrease Cooldown hours" }));
    await user.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    expect(screen.getByText("4H COOLDOWN")).toBeInTheDocument();
    expect(screen.getByText("TARGET 3 / NIGHT")).toBeInTheDocument();
    await user.click(screen.getByRole("checkbox", { name: "Prepare recovery plans" }).closest("label")!);
    await user.click(screen.getByRole("button", { name: "Enable overnight resourcefulness" }));
    expect(calls.mock.calls.some(([url, init]) => String(url).endsWith("/resourceful") && init?.method === "PUT")).toBe(false);
    await user.click(screen.getByRole("button", { name: "RUN AS OWNER?" }));

    await waitFor(() => expect(calls.mock.calls.some(([url, init]) => {
      if (!String(url).endsWith("/resourceful") || (init as RequestInit).method !== "PUT") return false;
      const body = JSON.parse(String((init as RequestInit).body));
      return JSON.stringify(body) === JSON.stringify({
        enabled: true, idle_after_minutes: 30, cooldown_hours: 4, nightly_target: 3,
        night_only: true, night_start_hour: 22, night_end_hour: 7, routines: ["loose_ideas"],
      });
    })).toBe(true));
  });

  it.each([0, 1])("enabled policy with %s completed items keeps stored progress honest while editing", async (nightlyCount) => {
    await open([], {}, { enabled: true, nightly_count: nightlyCount });
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "idle" } });
    expect(screen.getByText("READY WHEN IDLE")).toBeInTheDocument();
    expect(screen.getByText("LOCAL DATA")).toBeInTheDocument();
    expect(screen.getByText("ONE ITEM / RUN")).toBeInTheDocument();
    if (nightlyCount) expect(screen.getByText("1/2 THIS NIGHT")).toBeInTheDocument();
    else expect(screen.queryByText(/THIS NIGHT/)).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    expect(screen.getByText("TARGET 3 / NIGHT")).toBeInTheDocument();
    if (nightlyCount) expect(screen.getByText("1/2 THIS NIGHT")).toBeInTheDocument();
    expect(screen.queryByText(/0\/\d+ THIS NIGHT/)).toBeNull();
  });

  it("resourcefulness Retry owns the pending guard and replays the original policy write", async () => {
    const calls = await open();
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "idle" } });
    fireEvent.click(screen.getByRole("button", { name: "Decrease Cooldown hours" }));
    const writes: RequestInit[] = [];
    let resolveWrite!: (response: Response) => void;
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/resourceful") && init?.method === "PUT") {
        writes.push(init);
        return new Promise<Response>((resolve) => { resolveWrite = resolve; });
      }
      return calls(input, init);
    }));
    fireEvent.click(screen.getByRole("button", { name: "Enable overnight resourcefulness" }));
    fireEvent.click(screen.getByRole("button", { name: "RUN AS OWNER?" }));
    await waitFor(() => expect(writes).toHaveLength(1));
    expect(screen.getByRole("button", { name: "Enable overnight resourcefulness" })).toBeDisabled();
    resolveWrite(new Response("{}", { status: 503, headers: { "content-type": "application/json" } }));
    const retry = await screen.findByRole("button", { name: "Try again" });
    expect(screen.getByText("Could not turn on resourcefulness")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    fireEvent.click(retry);
    await waitFor(() => expect(writes).toHaveLength(2));
    expect(screen.getByRole("button", { name: "Enable overnight resourcefulness" })).toBeDisabled();
    fireEvent.click(retry);
    expect(writes).toHaveLength(2);
    expect(writes[1].body).toEqual(writes[0].body);
    expect(JSON.parse(String(writes[1].body))).toEqual({
      enabled: true, idle_after_minutes: 30, cooldown_hours: 5, nightly_target: 2,
      night_only: true, night_start_hour: 22, night_end_hour: 7, routines: ["loose_ideas", "failed_work"],
    });
    resolveWrite(new Response("{}", { status: 503, headers: { "content-type": "application/json" } }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Enable overnight resourcefulness" })).toBeEnabled());
  });

  it("Save policy names its failure and Retry replays that same save", async () => {
    const calls = await open([], {}, { enabled: true });
    fireEvent.change(screen.getByRole("combobox", { name: "Automation start condition" }), { target: { value: "idle" } });
    fireEvent.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    const writes: RequestInit[] = [];
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).endsWith("/resourceful") && init?.method === "PUT") {
        writes.push(init);
        return Promise.resolve(new Response("{}", { status: 503, headers: { "content-type": "application/json" } }));
      }
      return calls(input, init);
    }));
    fireEvent.click(screen.getByRole("button", { name: "Save policy" }));
    await screen.findByText("Could not save the policy");
    expect(screen.queryByText("Could not turn on resourcefulness")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Increase Nightly target" }));
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(writes).toHaveLength(2));
    expect(writes[1].body).toEqual(writes[0].body);
    expect(JSON.parse(String(writes[1].body))).toMatchObject({ enabled: true, nightly_target: 3 });
    expect(await screen.findByText("Could not save the policy")).toBeInTheDocument();
  });
});

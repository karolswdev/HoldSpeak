/** HS-130-09 — each picker exit persists EXACTLY ONE Workbench.
 *
 * The picker is the pre-persistence chooser: Template instantiates one record,
 * Blank creates one record. Neither exit may create more than one, and each
 * opens exactly that record's window.
 */
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, vi } from "vitest";

import { apiFetch } from "../../../lib/api";
import { useDesk } from "../../store";
import { WorkbenchTemplatePicker } from "../WorkbenchTemplatePicker";

vi.mock("../../../lib/api", () => ({
  apiFetch: vi.fn(),
  readableError: (error: unknown) => error instanceof Error ? error.message : "Failed",
}));

const TEMPLATE = {
  id: "tmpl-1",
  name: "Daily Brief",
  description: "A starter",
  icon: "📋",
  recipe: { name: "Analyst", role: "assistant" },
  workbench: { schedule: null },
  starter_items: [{ title: "one" }],
  skill_names: [],
};

const openWorkbenchWindow = vi.fn();
const refresh = vi.fn().mockResolvedValue(undefined);

function mockApi() {
  (apiFetch as unknown as ReturnType<typeof vi.fn>).mockImplementation(
    (url: string, opts?: { method?: string }) => {
      if (url === "/api/workbench-templates")
        return Promise.resolve({ templates: [TEMPLATE] });
      if (url.endsWith("/instantiate"))
        return Promise.resolve({ workbench: { id: "wb-from-template" } });
      if (url === "/api/workbenches" && opts?.method === "POST")
        return Promise.resolve({ workbench: { id: "wb-blank" } });
      return Promise.resolve({});
    },
  );
}

/** POSTs the picker made to a create endpoint. */
function createCalls() {
  return (apiFetch as unknown as ReturnType<typeof vi.fn>).mock.calls.filter(
    (call: unknown[]) => {
      const url = call[0] as string;
      const opts = call[1] as { method?: string } | undefined;
      return (
        opts?.method === "POST" &&
        (url === "/api/workbenches" || url.endsWith("/instantiate"))
      );
    },
  );
}

describe("WorkbenchTemplatePicker — one record per exit", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    refresh.mockReset().mockResolvedValue(undefined);
    mockApi();
    useDesk.setState({
      inferenceTargets: [
        {
          id: "this_machine",
          name: "This device",
          kind: "this_device",
          boundary: "on_device",
          readiness: { available: true, reason: "" },
          data_scope: { sent: [] },
        } as never,
      ],
      openWorkbenchWindow,
      refresh,
      error: "",
    });
  });

  it("Template exit instantiates exactly one Workbench and opens it", async () => {
    const onCreated = vi.fn();
    render(<WorkbenchTemplatePicker onCreated={onCreated} />);
    const card = await screen.findByText("Daily Brief");
    fireEvent.click(card);
    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));

    expect(createCalls()).toHaveLength(1);
    expect(createCalls()[0][0]).toBe("/api/workbench-templates/tmpl-1/instantiate");
    expect(openWorkbenchWindow).toHaveBeenCalledTimes(1);
    expect(openWorkbenchWindow).toHaveBeenCalledWith("wb-from-template");
    expect(onCreated).toHaveBeenCalledWith("wb-from-template");
  });

  it("Blank exit creates exactly one Workbench and opens it", async () => {
    const onCreated = vi.fn();
    render(<WorkbenchTemplatePicker onCreated={onCreated} />);
    const blank = await screen.findByText("Blank");
    fireEvent.click(blank);
    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));

    expect(createCalls()).toHaveLength(1);
    expect(createCalls()[0][0]).toBe("/api/workbenches");
    expect(openWorkbenchWindow).toHaveBeenCalledTimes(1);
    expect(openWorkbenchWindow).toHaveBeenCalledWith("wb-blank");
  });

  it("distinguishes a pending template read from a loaded empty list and permits Blank", async () => {
    const api = apiFetch as unknown as ReturnType<typeof vi.fn>;
    let release!: (value: unknown) => void;
    const base = api.getMockImplementation() as (url: string, opts?: { method?: string }) => Promise<unknown>;
    api.mockImplementation((url, opts) => url === "/api/workbench-templates"
      ? new Promise((resolve) => { release = resolve; }) : base(url, opts));
    render(<WorkbenchTemplatePicker />);
    expect(screen.getByRole("status")).toHaveAttribute("aria-busy", "true");
    expect(screen.queryByText("No templates · Start Blank")).toBeNull();
    release({ templates: [] });
    expect(await screen.findByText("No templates · Start Blank")).toBeVisible();
    expect(screen.queryByText("Loading")).toBeNull();
    fireEvent.click(screen.getByText("Blank"));
    await waitFor(() => expect(openWorkbenchWindow).toHaveBeenCalledWith("wb-blank"));
    expect(createCalls()).toHaveLength(1);
  });

  it.each(["Daily Brief", "Blank"])("keeps %s selected on POST failure and retries that choice", async (name) => {
    const api = apiFetch as unknown as ReturnType<typeof vi.fn>;
    let failed = false;
    api.mockImplementation((url: string, opts?: { method?: string }) => {
      if (url === "/api/workbench-templates") return Promise.resolve({ templates: [TEMPLATE] });
      if (opts?.method === "POST" && !failed) {
        failed = true;
        return Promise.reject(new Error("Hub unavailable"));
      }
      return Promise.resolve({ workbench: { id: "wb-retry" } });
    });
    const onCreated = vi.fn();
    render(<WorkbenchTemplatePicker onCreated={onCreated} />);
    const card = (await screen.findByText(name)).closest("button")!;
    fireEvent.click(card);
    expect(await screen.findByRole("alert")).toHaveTextContent(`${name} not created · Hub unavailable`);
    expect(card).toHaveAttribute("aria-pressed", "true");
    expect(card).toBeEnabled();
    expect(openWorkbenchWindow).not.toHaveBeenCalled();
    expect(refresh).not.toHaveBeenCalled();
    fireEvent.click(card);
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith("wb-retry"));
    expect(createCalls()).toHaveLength(2);
    expect(createCalls()[1][0]).toBe(createCalls()[0][0]);
  });

  it.each(["Daily Brief", "Blank"])("opens the saved %s before a failed refresh and Retry only reads", async (name) => {
    refresh.mockRejectedValueOnce(new Error("Read unavailable")).mockResolvedValue(undefined);
    const onCreated = vi.fn();
    render(<WorkbenchTemplatePicker onCreated={onCreated} />);
    const card = (await screen.findByText(name)).closest("button")!;
    fireEvent.click(card);
    expect(await screen.findByRole("alert")).toHaveTextContent(`${name} created · Desk read failed · Read unavailable`);
    const id = name === "Blank" ? "wb-blank" : "wb-from-template";
    expect(openWorkbenchWindow).toHaveBeenCalledWith(id);
    expect(card).toHaveAttribute("aria-pressed", "true");
    expect(card).toBeDisabled();
    expect(onCreated).not.toHaveBeenCalled();
    fireEvent.click(card);
    fireEvent.click(screen.getByRole("button", { name: "Open workbench" }));
    expect(openWorkbenchWindow).toHaveBeenLastCalledWith(id);
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith(id));
    expect(createCalls()).toHaveLength(1);
    expect(refresh).toHaveBeenCalledTimes(2);
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("treats a resolved refresh with a desk read error as a read failure", async () => {
    refresh.mockImplementationOnce(async () => { useDesk.setState({ error: "Workbenches unavailable" }); });
    render(<WorkbenchTemplatePicker />);
    fireEvent.click(await screen.findByText("Blank"));
    expect(await screen.findByRole("alert")).toHaveTextContent("Blank created · Desk read failed · Workbenches unavailable");
    expect(createCalls()).toHaveLength(1);
    expect(openWorkbenchWindow).toHaveBeenCalledWith("wb-blank");
  });

  it("keeps template cards in the library and the existing keyboard rover", async () => {
    render(<WorkbenchTemplatePicker />);
    const card = (await screen.findByText("Daily Brief")).closest("button")!;
    const blank = screen.getByText("Blank").closest("button")!;
    await waitFor(() => expect(card).toHaveAttribute("tabindex", "0"));
    expect(card).toHaveClass("btn--chrome");
    expect(blank).toHaveAttribute("tabindex", "-1");
    card.focus();
    fireEvent.keyDown(card, { key: "ArrowDown" });
    expect(blank).toHaveFocus();
    expect(blank).toHaveAttribute("tabindex", "0");
  });
});

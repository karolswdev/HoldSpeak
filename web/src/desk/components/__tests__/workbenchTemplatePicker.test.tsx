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
});

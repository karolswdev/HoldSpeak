/* HS-202-02 — rendered receipt transition with retained producer payloads.
 *
 * This fence starts with one real `/api/brief/latest` response, then presses
 * Generate and checks the different real `/api/brief/generate` response. The
 * exact count and time on each receipt come from `briefReceipt`, so a stale
 * receipt cannot satisfy the transition.
 */
import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch } from "../../../lib/api";
import { ChairHome } from "../ChairHome";
import { briefReceipt, type GeneratedBrief } from "../briefEgress";
import latestPayload from "./fixtures/philo504/latest-run4.json";
import generatedPayload from "./fixtures/philo504/generate-run5.json";
import emptyPayload from "./fixtures/philo504/empty-s3.json";

vi.mock("../../../lib/api", async (original) => ({
  ...(await original<typeof import("../../../lib/api")>()),
  apiFetch: vi.fn(),
}));
vi.mock("../../thoughts", () => ({ unfinishedThoughts: async () => ({ items: [] }) }));
vi.mock("../../components/MicButton", () => ({ MicButton: () => null }));
vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({ state: "connected", lastFrame: null, subscribe: () => () => undefined }),
  useRuntimeFrame: () => null,
}));

let latest: Record<string, unknown> | null = latestPayload;
let generated: Record<string, unknown> = generatedPayload;

function wire() {
  vi.mocked(apiFetch).mockImplementation(async (path: string, init?: unknown) => {
    const url = String(path);
    if (url === "/api/inference/assignments") {
      return { schema: "InferenceAssignmentSummary@1", rows: [], task_overrides: [], issue_count: 0 } as never;
    }
    if (url.startsWith("/api/desk/needs-you")) {
      return { count: 0, items: [], projects: [], next: null, coverage: [], complete: true } as never;
    }
    if (url.startsWith("/api/brief/latest")) return latest as never;
    if (url === "/api/brief/generate" && (init as { method?: string })?.method === "POST") {
      return generated as never;
    }
    return null as never;
  });
}

const LATEST_RECEIPT = "Brief ready · 5 items · SEP 25 18:08";
const GENERATED_RECEIPT = "Brief ready · 6 items · SEP 25 18:19";
const receiptFor = (payload: Record<string, unknown>) =>
  briefReceipt(payload as unknown as GeneratedBrief);

describe("Generate receipt transition (PHILO-5-04 / HS-202-02)", () => {
  beforeEach(() => {
    vi.mocked(apiFetch).mockReset();
    latest = latestPayload;
    generated = generatedPayload;
    wire();
  });

  it("shows the latest receipt before Generate and replaces it with the new receipt", async () => {
    render(<ChairHome />);

    const initialReceipt = await screen.findByTestId("arrival-brief-receipt");
    expect(receiptFor(latestPayload)).toBe(LATEST_RECEIPT);
    expect(initialReceipt.textContent).toBe(LATEST_RECEIPT);
    expect(screen.getByTestId("arrival-brief-generate")).toBeEnabled();
    expect(
      vi.mocked(apiFetch).mock.calls.some(
        ([path, init]) => path === "/api/brief/generate" && (init as { method?: string })?.method === "POST",
      ),
    ).toBe(false);

    await act(async () => {
      screen.getByTestId("arrival-brief-generate").click();
    });

    expect(receiptFor(generatedPayload)).toBe(GENERATED_RECEIPT);
    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-receipt").textContent).toBe(GENERATED_RECEIPT),
    );
    expect(GENERATED_RECEIPT).not.toBe(LATEST_RECEIPT);
    expect(vi.mocked(apiFetch)).toHaveBeenCalledWith(
      "/api/brief/generate",
      expect.objectContaining({ method: "POST" }),
    );
    expect(screen.queryByText("No brief yet")).toBeNull();
  });

  it("names the destination on the row before the press", async () => {
    render(<ChairHome />);
    const section = await screen.findByTestId("arrival-brief");
    expect(section.querySelector(".gadget-chip-egress")?.textContent).toBe("THIS DEVICE");
  });

  it("keeps the receipt when the generated response has no countable rows", async () => {
    generated = emptyPayload;
    render(<ChairHome />);
    await screen.findByTestId("arrival-brief-generate");
    await waitFor(() => expect(screen.getByTestId("arrival-brief-generate")).toBeEnabled());

    await act(async () => {
      screen.getByTestId("arrival-brief-generate").click();
    });

    await waitFor(() =>
      expect(screen.getByTestId("arrival-brief-receipt").textContent).toBe(
        "Brief ready · SEP 24 16:42",
      ),
    );
  });
});

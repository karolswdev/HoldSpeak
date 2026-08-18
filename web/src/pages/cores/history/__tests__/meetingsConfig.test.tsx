// HS-139-03 -- vitest for the Meetings capture + export config section.
import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn(async () => ({
  _revision: "rev-1",
  meeting: {
    mic_device: "Built-in Microphone",
    system_audio_device: "BlackHole 2ch",
    auto_export: true,
    export_format: "markdown",
  },
}));

vi.mock("../../../../lib/api", async (importOriginal) => {
  const mod = (await importOriginal()) as Record<string, unknown>;
  return {
    ...mod,
    apiFetch: (...args: unknown[]) => apiFetch(...(args as [string])),
  };
});

import { MeetingsConfig } from "../MeetingsConfig";

describe("MeetingsConfig (HS-139-03)", () => {
  it("renders capture + export controls from /api/settings", async () => {
    render(<MeetingsConfig />);
    expect(
      await screen.findByDisplayValue("Built-in Microphone"),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("BlackHole 2ch")).toBeInTheDocument();
    // Auto export checkbox
    const autoExport = screen.getByLabelText("Auto export") as HTMLInputElement;
    expect(autoExport.checked).toBe(true);
    // Export format cycle
    expect(screen.getByLabelText("Export format")).toBeInTheDocument();
  });

  it("does NOT render intel or companion controls (those moved elsewhere)", async () => {
    render(<MeetingsConfig />);
    await screen.findByDisplayValue("Built-in Microphone");
    // No intel_realtime_model (lives in Models)
    expect(screen.queryByLabelText("Realtime model")).toBeNull();
    // No companion_github_repo (lives in Delivery)
    expect(screen.queryByLabelText("GitHub repo")).toBeNull();
  });

  it("fetches settings on mount", async () => {
    render(<MeetingsConfig />);
    await waitFor(() =>
      expect(apiFetch).toHaveBeenCalledWith("/api/settings"),
    );
  });
});

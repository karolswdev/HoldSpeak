// HS-112-01 — the one dial: the Prefs `models` module owns the target
// list and the per-feature RUNS ON pickers. Writes go ONLY to
// /api/inference-targets; the three pointers write through the Prefs
// settings updater with the one sentinel (null = hub default).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ModelsModule } from "../settingsModels";

const apiFetch = vi.fn(async (url: string, init?: { method?: string }) => {
  if (url === "/api/inference-targets" && !init?.method) {
    return {
      targets: [
        {
          id: "this_machine",
          profile_id: null,
          name: "This device",
          kind: "this_device",
          model: "",
          readiness: { state: "ready", reason: "" },
          secret: { required: false, present: false },
        },
        {
          id: "p-43",
          profile_id: "p-43",
          name: "LAN llama",
          kind: "private_endpoint",
          model: "Qwen3.5-9B-Q6_K",
          context_limit: 16384,
          readiness: { state: "ready", reason: "" },
          secret: { required: false, present: false },
        },
        {
          id: "p-key",
          profile_id: "p-key",
          name: "Paid API",
          kind: "external_service",
          model: "gpt-5-mini",
          context_limit: 16384,
          readiness: {
            state: "needs_key",
            reason: "Destination 'Paid API' needs a key",
          },
          secret: { required: true, present: false },
        },
      ],
    };
  }
  if (url === "/api/profiles")
    return {
      profiles: [
        {
          id: "p-43",
          kind: "openAICompatible",
          base_url: "http://192.168.1.43:8080/v1",
          node: "",
        },
        {
          id: "p-key",
          kind: "openAICompatible",
          base_url: "https://api.example.com/v1",
          node: "",
        },
      ],
    };
  return {};
});

vi.mock("../../../lib/api", async (importOriginal) => {
  const mod = (await importOriginal()) as Record<string, unknown>;
  return { ...mod, apiFetch: (...args: unknown[]) => apiFetch(...(args as [string])) };
});

const settings = {
  meeting: { intel_profile_id: null },
  dictation: { runtime: { backend: "auto", profile_id: "p-43", n_ctx: 2048 } },
  rails_observer: { enabled: false, profile_id: null, poll_seconds: 30, tail: 20 },
};

describe("ModelsModule (HS-112-01)", () => {
  it("lists the profile-backed targets with key + readiness lamps", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    expect(await screen.findByDisplayValue("LAN llama")).toBeInTheDocument();
    expect(
      screen.getByDisplayValue("http://192.168.1.43:8080/v1"),
    ).toBeInTheDocument();
    // The unset key on a keyed destination shows honestly.
    expect(screen.getByText("UNSET")).toBeInTheDocument();
    expect(screen.getByText("NEEDS_KEY")).toBeInTheDocument();
    // The built-in this_machine row never renders as an editable target.
    expect(screen.queryByDisplayValue("This device")).toBeNull();
  });

  it("offers HUB DEFAULT plus every target on all three RUNS ON rows", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    for (const label of ["Dictation runs on", "Meetings runs on", "Rails runs on"]) {
      const picker = screen.getByLabelText(label) as HTMLSelectElement;
      const options = Array.from(picker.options).map((o) => o.textContent);
      expect(options).toContain("HUB DEFAULT");
      expect(options).toContain("LAN LLAMA");
      expect(options).toContain("PAID API");
    }
  });

  it("writes a pointer pick through the settings updater with the one sentinel", async () => {
    const update = vi.fn();
    render(
      <ModelsModule settings={settings} update={update} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    fireEvent.change(screen.getByLabelText("Meetings runs on"), {
      target: { value: "p-43" },
    });
    expect(update).toHaveBeenCalledWith(["meeting", "intel_profile_id"], "p-43");
    fireEvent.change(screen.getByLabelText("Dictation runs on"), {
      target: { value: "" },
    });
    // Clearing writes null — the one sentinel, never "".
    expect(update).toHaveBeenCalledWith(
      ["dictation", "runtime", "profile_id"],
      null,
    );
  });

  it("edits a target through the one write path (/api/inference-targets)", async () => {
    vi.useFakeTimers();
    try {
      render(
        <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
      );
      await vi.waitFor(() =>
        expect(screen.getByDisplayValue("LAN llama")).toBeInTheDocument(),
      );
      fireEvent.change(screen.getByDisplayValue("LAN llama"), {
        target: { value: "LAN llama 2" },
      });
      await vi.advanceTimersByTimeAsync(800);
      const put = apiFetch.mock.calls.find(
        (call) => (call[1] as { method?: string } | undefined)?.method === "PUT",
      );
      expect(put?.[0]).toBe("/api/inference-targets/p-43");
    } finally {
      vi.useRealTimers();
    }
  });

  it("never touches a legacy endpoint field", async () => {
    const update = vi.fn();
    render(
      <ModelsModule settings={settings} update={update} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    const paths = update.mock.calls.map((call) => (call[0] as string[]).join("."));
    for (const path of paths) {
      expect(path).not.toMatch(/intel_cloud|openai_compatible/);
    }
  });
});

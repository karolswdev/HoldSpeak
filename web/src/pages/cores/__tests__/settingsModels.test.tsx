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
  if (url === "/api/inference-targets/p-43/probe" && init?.method === "POST") {
    return {
      reachable: true,
      latency_ms: 12,
      models: ["Qwen3.5-9B-Q6_K", "Llama-3.2"],
      error: null,
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
      expect(options.some((o) => o?.startsWith("HUB DEFAULT"))).toBe(true);
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

  it("tests each destination and offers its discovered models", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");

    fireEvent.click(screen.getAllByRole("button", { name: "TEST" })[0]);

    expect(await screen.findByText("READY 12ms")).toBeInTheDocument();
    const model = screen.getByLabelText("Target p-43 model") as HTMLSelectElement;
    expect(model.value).toBe("Qwen3.5-9B-Q6_K");
    expect(Array.from(model.options).map((option) => option.value)).toEqual([
      "Qwen3.5-9B-Q6_K",
      "Llama-3.2",
    ]);
    expect(apiFetch).toHaveBeenCalledWith(
      "/api/inference-targets/p-43/probe",
      { method: "POST" },
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

  it("renders the meetings placement rule where the placement is set", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText("DESTINATION WINS · PROVIDER DECIDES WHEN NO DESTINATION"),
    ).toBeInTheDocument();
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

/* ── HS-132-10 — ONE meetings placement dial ─────────────────────────────
   The Provider cycle used to live in the Meetings prefs module as a SECOND,
   independent placement dial with no precedence signal: with a destination
   adopted, picking LOCAL there did nothing and said nothing. It is now
   subordinate to the destination pointer, in the pointer's own home, and it
   names its override state from the hub's provenance. */

const placed = (placement: Record<string, unknown>, meeting = {}) => ({
  ...settings,
  meeting: { intel_profile_id: null, intel_provider: "local", ...meeting },
  _placement: { meeting: placement },
});

const LOCAL = {
  placement_source: "provider",
  placement_reason: "",
  provider_intent: "local",
  provider_honored: true,
  boundary: "local",
  target_id: "",
  target_name: "",
  engine: "local",
  model: "qwen3-4b",
  node: "",
  runnable: true,
  runnable_reason: "",
};

describe("meetings placement dial (HS-132-10)", () => {
  it("names the local placement and leaves the provider fallback live", async () => {
    render(
      <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText("RUNS ON · HUB DEFAULT · LOCAL · QWEN3-4B"),
    ).toBeInTheDocument();
    const provider = screen.getByLabelText("Meetings provider") as HTMLSelectElement;
    expect(provider.disabled).toBe(false);
    expect(provider.value).toBe("local");
    expect(screen.queryByText(/PROVIDER SELECTION IGNORED/)).toBeNull();
  });

  it("names the cloud placement", async () => {
    render(
      <ModelsModule
        settings={placed(
          { ...LOCAL, provider_intent: "cloud", boundary: "cloud", engine: "cloud", model: "gpt-5-mini" },
          { intel_provider: "cloud" },
        )}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText("RUNS ON · HUB DEFAULT · CLOUD · GPT-5-MINI"),
    ).toBeInTheDocument();
    expect((screen.getByLabelText("Meetings provider") as HTMLSelectElement).value).toBe(
      "cloud",
    );
  });

  it("disables the provider fallback and names the override when a destination is adopted", async () => {
    render(
      <ModelsModule
        settings={placed(
          {
            ...LOCAL,
            placement_source: "destination",
            provider_honored: false,
            boundary: "private_network",
            target_id: "p-43",
            target_name: "LAN llama",
            engine: "cloud",
            model: "Qwen3.5-9B-Q6_K",
          },
          { intel_profile_id: "p-43" },
        )}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    // The destination decides — and the subordinate dial SAYS SO instead of
    // accepting a silent no-op click.
    expect(
      screen.getByText("PROVIDER SELECTION IGNORED · DESTINATION LAN LLAMA DECIDES"),
    ).toBeInTheDocument();
    expect(
      (screen.getByLabelText("Meetings provider") as HTMLSelectElement).disabled,
    ).toBe(true);
    expect(
      screen.getByText("RUNS ON · LAN LLAMA · PRIVATE_NETWORK · QWEN3.5-9B-Q6_K"),
    ).toBeInTheDocument();
  });

  it("names a dropped destination pointer and keeps the provider live", async () => {
    render(
      <ModelsModule
        settings={placed(
          {
            ...LOCAL,
            placement_source: "provider-selection-ignored",
            placement_reason: "assigned profile missing: gone",
          },
          { intel_profile_id: "gone" },
        )}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText("DESTINATION SELECTION IGNORED · ASSIGNED PROFILE MISSING: GONE"),
    ).toBeInTheDocument();
    expect(
      (screen.getByLabelText("Meetings provider") as HTMLSelectElement).disabled,
    ).toBe(false);
  });

  it("names a placement that cannot run", async () => {
    render(
      <ModelsModule
        settings={placed({
          ...LOCAL,
          runnable: false,
          runnable_reason: "model file not found",
        })}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText(/NOT RUNNABLE · MODEL FILE NOT FOUND/),
    ).toBeInTheDocument();
  });

  it("marks exactly one row as the deciding control, in every state", async () => {
    const { unmount } = render(
      <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(screen.getAllByText("DECIDES PLACEMENT")).toHaveLength(1);
    expect(screen.getByText("NONE · PROVIDER DECIDES")).toBeInTheDocument();
    unmount();

    render(
      <ModelsModule
        settings={placed({
          ...LOCAL,
          placement_source: "destination",
          provider_honored: false,
          target_name: "LAN llama",
        })}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(screen.getAllByText("DECIDES PLACEMENT")).toHaveLength(1);
    expect(screen.getByText("OVERRIDDEN")).toBeInTheDocument();
  });

  it("writes the provider fallback through the settings updater", async () => {
    const update = vi.fn();
    render(
      <ModelsModule settings={placed(LOCAL)} update={update} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    fireEvent.change(screen.getByLabelText("Meetings provider"), {
      target: { value: "cloud" },
    });
    expect(update).toHaveBeenCalledWith(["meeting", "intel_provider"], "cloud");
  });
});

// HS-112-01 — the one dial: the Prefs `models` module owns the target
// list and the per-feature RUNS ON pickers. Writes go ONLY to
// /api/inference-targets; the three pointers write through the Prefs
// settings updater with the one sentinel (null = hub default).
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ModelsModule } from "../settingsModels";
import surfaceCss from "../../../desk/surface/surface.css?raw";
import gadgetsCss from "../../../desk/surface/gadgets.css?raw";

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
          endpoint: "http://192.168.1.43:8080/v1",
          node: "",
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
          endpoint: "https://api.example.com/v1",
          node: "",
        },
        {
          id: "p-unavailable",
          profile_id: "p-unavailable",
          name: "Unavailable endpoint",
          kind: "private_endpoint",
          model: "",
          context_limit: 16384,
          readiness: { state: "unsupported", reason: "No valid endpoint" },
          secret: { required: false, present: false },
          endpoint: "",
          node: "",
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
  if (url === "/api/setup/hub-default-summary") {
    return { engine: "mlx", model: "Qwen local", available: true };
  }
  if (url === "/api/setup/runtime-options") {
    return {
      platform: { system: "darwin", machine: "arm64", apple_silicon: true },
      mlx: [{ label: "Qwen local", value: "/Users/test/Models/mlx/Qwen-local" }],
      gguf: [{ label: "Pocket GGUF", value: "/Users/test/Models/gguf/pocket.gguf" }],
    };
  }
  if (url === "/api/models") {
    return { models: [{ id: "this_machine", name: "Qwen local", ready: true }] };
  }
  // HS-134-02: /api/profiles read routes retired.
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
    expect(screen.getAllByText("KEY NEEDED").length).toBeGreaterThan(0);
    expect(screen.getByText("NOT AVAILABLE")).toBeInTheDocument();
    expect(screen.queryByText("NEEDS_KEY")).toBeNull();
    expect(screen.queryByText("UNSUPPORTED")).toBeNull();
    // The built-in this_machine row never renders as an editable target.
    expect(screen.queryByDisplayValue("This device")).toBeNull();
  });

  it("offers the device default plus every connection for each AI job", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    for (const label of ["Writing & dictation AI", "Meetings AI", "Background assistance AI"]) {
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
    fireEvent.change(screen.getByLabelText("Meetings AI"), {
      target: { value: "p-43" },
    });
    expect(update).toHaveBeenCalledWith(["meeting", "intel_profile_id"], "p-43");
    fireEvent.change(screen.getByLabelText("Writing & dictation AI"), {
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

  it("writes a masked destination key through the secret subresource and clears it", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    fireEvent.click(screen.getByRole("button", { name: "Paid API key needed" }));
    const key = screen.getByLabelText("Destination p-key API key") as HTMLInputElement;
    expect(key.type).toBe("password");
    fireEvent.change(key, { target: { value: "not-a-real-key" } });
    fireEvent.click(screen.getByRole("button", { name: "SET KEY" }));
    await waitFor(() => expect(apiFetch).toHaveBeenCalledWith(
      "/api/inference-targets/p-key/secret",
      { method: "PUT", json: { value: "not-a-real-key" } },
    ));
    await waitFor(() => expect(screen.queryByTestId("target-key-editor-p-key")).toBeNull());
    expect(screen.queryByDisplayValue("not-a-real-key")).toBeNull();
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
        (call) => call[0] === "/api/inference-targets/p-43"
          && (call[1] as { method?: string } | undefined)?.method === "PUT",
      );
      expect(put?.[0]).toBe("/api/inference-targets/p-43");
    } finally {
      vi.useRealTimers();
    }
  });

  it("states the meetings consequence in owner language", async () => {
    render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(screen.getByText("Meetings uses this device")).toBeInTheDocument();
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

describe("Models destination workbench (HS-139 beauty pass)", () => {
  it("leads with a plain setup path and keeps connection administration disclosed", async () => {
    const { container } = render(
      <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");

    expect(screen.getByRole("heading", { name: "Choose your AI" })).toBeInTheDocument();
    expect(screen.getByText("This device")).toBeInTheDocument();
    expect(screen.getByText("Choose AI for each job")).toBeInTheDocument();
    expect(screen.queryByText("Runs on")).toBeNull();
    const connections = screen.getByText("AI connections").closest("details");
    expect(connections).not.toHaveAttribute("open");
    expect(container.querySelector(".models-destinations")).toHaveAttribute("data-layout", "matrix");
    expect(container.querySelector(".models-destination-matrix")).toBeInTheDocument();
    expect(container.querySelector(".dest-card")).toBeNull();
    expect(container.querySelector(".models-setup-intro")).toBeInTheDocument();
    expect(container.querySelector(".models-local-setup")).toBeInTheDocument();
    expect(container.querySelector(".models-job-routing")).toBeInTheDocument();
  });

  it("tests the selected local AI and reports readiness in place", async () => {
    render(<ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />);
    await screen.findByDisplayValue("LAN llama");
    fireEvent.click(screen.getByRole("button", { name: "CHECK THIS AI" }));
    expect(await screen.findByText("Ready · Qwen local can answer on this device.")).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith("/api/models");
  });

  it("turns discovered local models into one owner choice", async () => {
    const update = vi.fn();
    render(<ModelsModule settings={settings} update={update} onRefuse={vi.fn()} />);
    const chooser = await screen.findByLabelText("Model on this device") as HTMLSelectElement;
    expect(Array.from(chooser.options).map((option) => option.textContent)).toEqual([
      "CHOOSE A MODEL…",
      "APPLE MLX · Qwen local",
      "GGUF · Pocket GGUF",
      "OTHER MODEL LOCATION…",
    ]);
    fireEvent.change(chooser, { target: { value: "mlx:/Users/test/Models/mlx/Qwen-local" } });
    expect(update).toHaveBeenCalledWith(["dictation", "runtime", "backend"], "mlx");
    expect(update).toHaveBeenCalledWith(
      ["dictation", "runtime", "mlx_model"],
      "/Users/test/Models/mlx/Qwen-local",
    );
    expect(screen.queryByLabelText("Apple MLX model folder")).toBeNull();
    expect(screen.queryByLabelText("GGUF model file")).toBeNull();
  });

  it("keeps a manual model-location escape hatch after discovery", async () => {
    render(<ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />);
    const chooser = await screen.findByLabelText("Model on this device");
    fireEvent.change(chooser, { target: { value: "__manual__" } });
    expect(screen.getByLabelText("Apple MLX model folder")).toBeInTheDocument();
    expect(screen.queryByLabelText("GGUF model file")).toBeNull();
  });

  it("uses collapsed target summaries below the readable matrix width", async () => {
    const rect = vi
      .spyOn(HTMLElement.prototype, "getBoundingClientRect")
      .mockReturnValue({ width: 620 } as DOMRect);
    try {
      const { container } = render(
        <ModelsModule settings={settings} update={vi.fn()} onRefuse={vi.fn()} />,
      );
      const card = await screen.findByTestId("dest-card-p-43");

      expect(container.querySelector(".models-destinations")).toHaveAttribute(
        "data-layout",
        "cards",
      );
      expect(container.querySelector(".models-destination-matrix")).toBeNull();
      expect(card).not.toHaveAttribute("data-expanded");
      expect(screen.queryByLabelText("Target p-43 endpoint")).toBeNull();

      fireEvent.click(screen.getByRole("button", { name: /LAN llama/i }));
      expect(card).toHaveAttribute("data-expanded");
      expect(screen.getByLabelText("Target p-43 endpoint")).toBeInTheDocument();
      expect(card.querySelector(".dest-card-verbs")).toBeInTheDocument();
      fireEvent.click(screen.getByRole("button", { name: /Paid API/i }));
      expect(screen.getByTestId("target-key-editor-p-key")).toBeInTheDocument();
    } finally {
      rect.mockRestore();
    }
  });

  it("pins the wide host, proportioned ledger, and container-driven collapse", () => {
    expect(surfaceCss).toContain(".desk-settings-window");
    expect(surfaceCss).toContain("width: calc(100vw - 48px);");
    expect(surfaceCss).toContain("minmax(210px, 35fr)");
    expect(surfaceCss).toContain("grid-template-columns: minmax(0, 58fr) minmax(0, 42fr);");
    expect(surfaceCss).toContain("@container surface (max-width: 839.9px)");
    expect(surfaceCss).toContain("flex-direction: row;");
    expect(surfaceCss).toContain("white-space: nowrap;");
    expect(gadgetsCss).toContain("place-items: center;");
    expect(gadgetsCss).toContain(".gadget-string .desk-mic > span");
  });
});

/* ── HS-132-10 — one Meetings placement choice ─────────────────────────── */

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

function openMeetingRouting() {
  const routing = screen.getByText("Meeting routing options").closest("details") as HTMLDetailsElement | null;
  expect(routing).not.toBeNull();
  if (!routing?.open) fireEvent.click(routing.querySelector("summary")!);
  return routing!;
}

describe("meetings placement dial (HS-132-10)", () => {
  it("keeps secondary routing closed until the owner asks for it", async () => {
    render(
      <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(screen.getByText("Meetings uses this device")).toBeInTheDocument();
    const routing = screen.getByText("Meeting routing options").closest("details");
    expect(routing).not.toHaveAttribute("open");
    openMeetingRouting();
    expect(routing).toHaveAttribute("open");
    expect(screen.getByText("If no destination")).toBeInTheDocument();
  });

  it("leaves the provider fallback live when routing options are open", async () => {
    render(
      <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    openMeetingRouting();
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
    expect(screen.getByText("Meetings uses the cloud")).toBeInTheDocument();
    openMeetingRouting();
    expect((screen.getByLabelText("Meetings provider") as HTMLSelectElement).value).toBe(
      "cloud",
    );
  });

  it("uses a selected destination without leaking precedence jargon", async () => {
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
    expect(screen.getByText("Meetings uses LAN llama")).toBeInTheDocument();
    openMeetingRouting();
    expect(
      (screen.getByLabelText("Meetings provider") as HTMLSelectElement).disabled,
    ).toBe(true);
    for (const jargon of [
      /DESTINATION SELECTION IGNORED/i,
      /PROVIDER SELECTION IGNORED/i,
      /DECIDES PLACEMENT/i,
      /DESTINATION WINS/i,
      /PRIVATE_NETWORK/i,
      /ASSIGNED PROFILE IS OPEN.?AI COMPATIBLE KIND/i,
    ]) expect(screen.queryByText(jargon)).toBeNull();
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
    expect(screen.getByText("Selected destination isn’t compatible")).toBeInTheDocument();
    expect(screen.queryByText(/assigned profile missing/i)).toBeNull();
    openMeetingRouting();
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
    expect(screen.getByText("Meetings can’t run: Model file not found")).toBeInTheDocument();
  });

  it("gives an incompatible selected destination one concise next step", async () => {
    render(
      <ModelsModule
        settings={placed({
          ...LOCAL,
          runnable: false,
          placement_reason: "selected profile incompatible",
          runnable_reason: "no language model on this hub",
        })}
        update={vi.fn()}
        onRefuse={vi.fn()}
      />,
    );
    await screen.findByDisplayValue("LAN llama");
    expect(
      screen.getByText("Meetings can’t use the selected destination. Choose a local model in Intelligence."),
    ).toBeInTheDocument();
    expect(screen.queryByText(/selected profile incompatible/i)).toBeNull();
  });

  it("keeps the fallback live only while Meetings uses this device", async () => {
    const { unmount } = render(
      <ModelsModule settings={placed(LOCAL)} update={vi.fn()} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    openMeetingRouting();
    expect((screen.getByLabelText("Meetings provider") as HTMLSelectElement).disabled).toBe(false);
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
    openMeetingRouting();
    expect((screen.getByLabelText("Meetings provider") as HTMLSelectElement).disabled).toBe(true);
  });

  it("writes the provider fallback through the settings updater", async () => {
    const update = vi.fn();
    render(
      <ModelsModule settings={placed(LOCAL)} update={update} onRefuse={vi.fn()} />,
    );
    await screen.findByDisplayValue("LAN llama");
    openMeetingRouting();
    fireEvent.change(screen.getByLabelText("Meetings provider"), {
      target: { value: "cloud" },
    });
    expect(update).toHaveBeenCalledWith(["meeting", "intel_provider"], "cloud");
  });
});

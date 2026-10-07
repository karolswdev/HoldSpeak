// PHILO-15 05, ruling 3 (inventory gap 5, honesty): there is no Anthropic
// execution adapter, so the Model Library must not take an Anthropic key as if
// it worked. Picking Anthropic shows the NOT SUPPORTED YET token, disables the
// key field and Connect, and offers the two routes that run (OpenRouter,
// OpenAI-compatible). A stored Anthropic row reads the state, not a verb.
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModelLibraryCore } from "../ModelLibraryCore";
import { connectHostedModel, getModelLibrary, type ModelLibraryProjection } from "../modelLibrary";

vi.mock("../modelLibrary", async (importOriginal) => {
  const original = await importOriginal<typeof import("../modelLibrary")>();
  return {
    ...original,
    getModelLibrary: vi.fn(),
    downloadModel: vi.fn(),
    addDetectedModel: vi.fn(),
    connectHostedModel: vi.fn(),
    defineEndpoint: vi.fn(),
    useModelFile: vi.fn(),
  };
});

function projection(rows: ModelLibraryProjection["rows"]): ModelLibraryProjection {
  return {
    schema: "ModelLibraryProjection@1",
    catalog_revision: 7,
    artifact_detection: { state: "complete" },
    summary: { state: "ready", label: "Ready", ready_count: 1, attention_count: 0 },
    rows,
  };
}

const ready = {
  id: "profile:openrouter-main", source: "provider", label: "OpenRouter Qwen", status: "ready",
  detail: { provider_family: "openrouter" }, repair: null, selected_action: "Ready",
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(getModelLibrary).mockResolvedValue(projection([ready]));
});

describe("the Anthropic provider row", () => {
  it("reads NOT SUPPORTED YET, disables its key and Connect, and offers the routes that run", async () => {
    render(<ModelLibraryCore />);
    fireEvent.click(await screen.findByRole("button", { name: "+ Add model" }));
    fireEvent.click(screen.getByRole("button", { name: "Connect hosted model" }));
    // OpenRouter (the default) takes a key.
    expect(screen.queryByTestId("model-library-anthropic-not-supported")).toBeNull();
    expect(screen.getByLabelText("Provider key")).not.toBeDisabled();

    fireEvent.change(screen.getByLabelText("Hosted provider"), { target: { value: "anthropic" } });
    const row = screen.getByTestId("model-library-anthropic-not-supported");
    expect(row.querySelector(".surface-token")?.textContent).toBe("NOT SUPPORTED YET");
    expect(screen.getByLabelText("Provider key")).toBeDisabled();
    expect(screen.getByRole("button", { name: "Connect" })).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: "Connect" }));
    expect(connectHostedModel).not.toHaveBeenCalled();

    // Route 1: OpenRouter, in place.
    fireEvent.click(screen.getByRole("button", { name: "Use OpenRouter" }));
    expect(screen.queryByTestId("model-library-anthropic-not-supported")).toBeNull();
    expect(screen.getByLabelText("Provider key")).not.toBeDisabled();

    // Route 2: an OpenAI-compatible endpoint.
    fireEvent.change(screen.getByLabelText("Hosted provider"), { target: { value: "anthropic" } });
    fireEvent.click(screen.getByRole("button", { name: "Use OpenAI-compatible" }));
    expect(screen.getByRole("region", { name: "Define endpoint" })).toBeInTheDocument();
    expect((screen.getByLabelText("Endpoint provider") as HTMLSelectElement).value).toBe("openai_compatible");
  });

  it("a stored Anthropic row shows the state, never a verb", async () => {
    vi.mocked(getModelLibrary).mockResolvedValue(projection([{
      id: "profile:anthropic-main", source: "provider", label: "Claude", status: "not_supported",
      detail: { provider_family: "anthropic" }, repair: null, selected_action: "NOT SUPPORTED YET",
    }]));
    render(<ModelLibraryCore />);
    const radio = await screen.findByRole("radio");
    fireEvent.click(radio);
    expect(screen.queryByRole("button", { name: "NOT SUPPORTED YET" })).toBeNull();
    expect(screen.getAllByText("NOT SUPPORTED YET").length).toBeGreaterThan(0);
    expect(screen.getByText(/provider · not supported/)).toBeInTheDocument();
  });
});

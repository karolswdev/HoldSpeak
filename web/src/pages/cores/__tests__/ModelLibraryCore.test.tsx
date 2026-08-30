import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ModelLibraryCore } from "../ModelLibraryCore";
import {
  addDetectedModel,
  connectHostedModel,
  downloadModel,
  getModelLibrary,
  type ModelLibraryProjection,
  type ModelLibraryRow,
} from "../modelLibrary";

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

const receipt = {
  receipt: {
    kind: "model_library_add",
    message: "Added to the Model Library. Assignments are unchanged.",
    assignments_unchanged: true as const,
  },
};

const actions = [
  "Download",
  "Add to library",
  "Connect",
  "Add model",
  "Ready",
  "Checking",
  "Try again",
];

function projection(rows: ModelLibraryRow[] = actions.map((selected_action, index) => ({
  id: index === 0 ? "catalog:quick" : index === 1 ? "detected:quick" : `profile:model-${index}`,
  source: index < 2 ? (index === 0 ? "catalog" : "detected") : "provider",
  label: `Model ${index + 1}`,
  status: selected_action === "Ready" ? "ready" : "available",
  detail: { format: "gguf", catalog_revision: 1 },
  repair: null,
  selected_action,
}))) : ModelLibraryProjection {
  return {
    schema: "ModelLibraryProjection@1",
    catalog_revision: 7,
    artifact_detection: { state: "complete" },
    summary: rows.length
      ? { state: "ready", label: "Ready", ready_count: rows.filter((row) => row.status === "ready").length, attention_count: 0 }
      : { state: "empty", label: "Add model", ready_count: 0, attention_count: 0 },
    rows,
  };
}

const getLibrary = vi.mocked(getModelLibrary);
const download = vi.mocked(downloadModel);
const addDetected = vi.mocked(addDetectedModel);
const connectHosted = vi.mocked(connectHostedModel);

beforeEach(() => {
  vi.clearAllMocks();
  getLibrary.mockResolvedValue(projection());
  download.mockResolvedValue(receipt);
  addDetected.mockResolvedValue(receipt);
  connectHosted.mockResolvedValue({
    ...receipt,
    provider: {
      profile_id: "library-provider",
      profile_revision: 1,
      binding_id: "binding-provider",
      binding_revision: 1,
      provider_family: "openrouter",
      secret: { required: true, present: true },
    },
  });
});

describe("ModelLibraryCore", () => {
  it("renders only the server action table and one selected action seat", async () => {
    getLibrary.mockResolvedValue(projection());
    render(<ModelLibraryCore />);
    await screen.findAllByText("Model 1");

    for (const action of actions) expect(screen.getAllByText(action).length).toBeGreaterThan(0);
    expect(screen.getByRole("button", { name: "Download" })).toBeInTheDocument();
    expect(screen.getByText("Runs on", { exact: true })).toBeInTheDocument();
    expect(screen.queryByText(/assignment/i)).toBeNull();
  });

  it("opens all four add entries in-world without a modal", async () => {
    render(<ModelLibraryCore />);
    const add = await screen.findByRole("button", { name: "+ Add model" });
    add.focus();
    fireEvent.click(add);

    for (const label of [
      "Download from catalog",
      "Connect hosted model",
      "Define endpoint",
      "Use model file",
    ]) expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    expect(screen.queryByRole("dialog")).toBeNull();

    fireEvent.keyDown(screen.getByLabelText("Add model"), { key: "Escape" });
    await waitFor(() => expect(document.activeElement).toBe(screen.getByRole("button", { name: "+ Add model" })));
  });

  it("shows the exact no-assignment receipt after an add", async () => {
    render(<ModelLibraryCore />);
    await screen.findAllByText("Model 1");
    fireEvent.click(screen.getByRole("button", { name: "Download" }));
    await screen.findByText("Added to the Model Library. Assignments are unchanged.");
    expect(download).toHaveBeenCalledWith("quick", 7);
  });

  it("routes a hosted catalog Connect seat directly into provider setup", async () => {
    getLibrary.mockResolvedValue(projection([{
      id: "catalog:hosted-quick",
      source: "catalog",
      label: "Hosted Quick",
      status: "available",
      detail: { format: "api", catalog_revision: 7 },
      repair: null,
      selected_action: "Connect",
    }]));
    render(<ModelLibraryCore />);
    fireEvent.click(await screen.findByRole("button", { name: "Connect" }));
    expect(await screen.findByRole("region", { name: "Connect hosted model" })).toBeInTheDocument();
  });

  it("keeps radio selection inert, restores Add focus, and maps Mod+Enter to the sole action", async () => {
    render(<ModelLibraryCore />);
    const group = await screen.findByRole("radiogroup", { name: "Model Library" });
    const radios = screen.getAllByRole("radio");
    radios[0].focus();
    fireEvent.keyDown(radios[0], { key: "ArrowDown" });
    expect(radios[1]).toBeChecked();
    expect(addDetected).not.toHaveBeenCalled();

    fireEvent.keyDown(group, { key: "Enter", metaKey: true });
    await waitFor(() => expect(addDetected).toHaveBeenCalledWith("quick"));
  });

  it("keeps one compact wrapping radio list at one hundred rows", async () => {
    getLibrary.mockResolvedValue(projection(Array.from({ length: 100 }, (_, index) => ({
      id: `catalog:very-long-model-name-${index}-that-wraps-without-a-card-grid`,
      source: "catalog",
      label: `Very long model name ${index} that wraps without a card grid`,
      status: "available",
      detail: { format: "gguf" },
      repair: null,
      selected_action: "Download",
    }))));
    const { container } = render(<ModelLibraryCore />);
    await screen.findByText(/Very long model name 99/);
    expect(screen.getAllByRole("radio")).toHaveLength(100);
    expect(container.querySelectorAll(".model-library-row")).toHaveLength(100);
    expect(container.querySelector(".models-capability-card")).toBeNull();
  });

  it("renders inviting empty, in-flow error, one repair, and one egress badge", async () => {
    getLibrary.mockResolvedValueOnce(projection([]));
    const empty = render(<ModelLibraryCore />);
    await screen.findByRole("heading", { name: "Add model" });
    expect(screen.getAllByText("Add model")).toHaveLength(3);
    for (const label of [
      "Download from catalog",
      "Connect hosted model",
      "Define endpoint",
      "Use model file",
    ]) expect(screen.getByRole("button", { name: label })).toBeInTheDocument();
    expect(screen.queryByText("Ready")).toBeNull();
    empty.unmount();

    getLibrary.mockRejectedValueOnce(new Error("Library unavailable"));
    const failed = render(<ModelLibraryCore />);
    expect(await screen.findByRole("alert")).toHaveTextContent("Library unavailable");
    failed.unmount();

    getLibrary.mockResolvedValueOnce(projection([{
      id: "profile:broken",
      source: "provider",
      label: "Broken provider",
      status: "broken",
      detail: { provider_family: "openrouter" },
      repair: { code: "credential_unavailable", label: "Provider key is missing" },
      selected_action: "Provider key is missing",
    }]));
    render(<ModelLibraryCore />);
    await screen.findAllByText("Broken provider");
    expect(screen.getAllByText("Provider key is missing")).toHaveLength(2);
    expect(screen.getByText("Egress")).toBeInTheDocument();
  });

  it("keeps a write-only secret out of serialized markup, retains failure, and clears after custody", async () => {
    const sentinel = "hs143-secret-sentinel";
    connectHosted.mockRejectedValueOnce(new Error("Custody unavailable"));
    const { container } = render(<ModelLibraryCore />);
    fireEvent.click(await screen.findByRole("button", { name: "+ Add model" }));
    fireEvent.click(screen.getByRole("button", { name: "Connect hosted model" }));
    fireEvent.change(screen.getByLabelText("Provider name"), { target: { value: "OpenRouter" } });
    fireEvent.change(screen.getByLabelText("Model"), { target: { value: "qwen/test" } });
    const key = screen.getByLabelText("Provider key") as HTMLInputElement;
    fireEvent.change(key, { target: { value: sentinel } });
    expect(container.innerHTML).not.toContain(sentinel);

    fireEvent.click(screen.getByRole("button", { name: "Connect" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Custody unavailable");
    expect(key).toHaveValue(sentinel);
    expect(container.innerHTML).not.toContain(sentinel);

    fireEvent.click(screen.getByRole("button", { name: "Connect" }));
    await screen.findByText("Added to the Model Library. Assignments are unchanged.");
    expect(key.value).toBe("");
    expect(connectHosted).toHaveBeenCalledWith(expect.any(Object), sentinel);
  });
});

// Atlas pass 3 (defect 9): the Mode window (a recipe, e.g. Chase) shows ONE
// engine line, the one its Ask runs on, with one Change; never a second
// line that can disagree ("Studio engine" vs "No default model").
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("../../../pages/cores/ContextualAssignment", () => ({
  ContextualAssignment: ({ label, capabilityId }: { label: string; capabilityId: string }) => (
    <div data-testid="engine-line" data-capability={capabilityId}>{label}<button type="button">Change</button></div>
  ),
}));
vi.mock("../../../lib/api", async (importOriginal) => ({
  ...(await importOriginal<typeof import("../../../lib/api")>()),
  apiRequest: vi.fn(async () => new Response(JSON.stringify({ invocations: [] }))),
}));

import { RecipePullout } from "../RecipePullout";

const chase = {
  id: "recipe-chase",
  kind: "recipe",
  title: "Chase",
  ref: {
    id: "recipe-chase", kind: "recipe", role: "", systemPrompt: "Chase the open items.",
    capability: { readiness: { state: "ready" }, input_schema: { required: ["input"] }, effect_classes: ["creates_artifact"] },
  },
} as any;

describe("Mode window", () => {
  it("has one engine line, the Ask's (recipe.run), with one Change", () => {
    render(<RecipePullout object={chase} onClose={vi.fn()} />);
    const lines = screen.getAllByTestId("engine-line");
    expect(lines).toHaveLength(1);
    expect(lines[0].getAttribute("data-capability")).toBe("recipe.run");
    expect(lines[0].textContent).toContain("Which engine runs it");
    expect(screen.getAllByRole("button", { name: "Change" })).toHaveLength(1);
    expect(screen.queryByText("Which engine answers in a thread")).toBeNull();
  });
});

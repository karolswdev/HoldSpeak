import { render } from "@testing-library/react";
import axe from "axe-core";
import { describe, expect, it } from "vitest";
import ComponentsPage from "./ComponentsPage";

describe("Signal component gallery", () => {
  it("has no automatically detectable accessibility violations", async () => {
    const { container } = render(<ComponentsPage />);
    const result = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(result.violations).toEqual([]);
  });
});

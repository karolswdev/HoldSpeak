import { render } from "@testing-library/react";
import axe from "axe-core";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { ComponentsCore } from "./cores/ComponentsCore";

describe("Signal component gallery", () => {
  it("has no automatically detectable accessibility violations", async () => {
    const { container } = render(
      <MemoryRouter initialEntries={["/design/components"]}>
        <ComponentsCore />
      </MemoryRouter>,
    );
    const result = await axe.run(container, {
      rules: { "color-contrast": { enabled: false } },
    });
    expect(result.violations).toEqual([]);
  });
});

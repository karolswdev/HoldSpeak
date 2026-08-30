import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ApplicationBoundary } from "./ApplicationBoundary";

describe("ApplicationBoundary", () => {
  it("contains a failed application and lets it retry", async () => {
    const reported = vi.spyOn(console, "error").mockImplementation(() => undefined);
    let failing = true;
    function RecoveringApplication() {
      if (failing) throw new Error("renderer unavailable");
      return <p>Application restored</p>;
    }

    render(
      <ApplicationBoundary label="Workbench" onRetry={() => { failing = false; }}>
        <RecoveringApplication />
      </ApplicationBoundary>,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Workbench stopped");
    await userEvent.click(
      screen.getByRole("button", { name: "Reload application" }),
    );
    expect(screen.getByText("Application restored")).toBeInTheDocument();
    expect(reported).toHaveBeenCalled();
    reported.mockRestore();
  });
});

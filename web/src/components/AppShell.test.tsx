// HS-95-08 — the one shell: every real route renders the immersive frame;
// the flat header/nav world is gone (Constitution, Article I).
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";
import { AppShell } from "./AppShell";

vi.mock("./AmbientLayer", () => ({ AmbientLayer: () => null }));

describe("the one shell", () => {
  it("renders the immersive frame with no flat header or nav", () => {
    render(
      <MemoryRouter>
        <AppShell>
          <p>surface</p>
        </AppShell>
      </MemoryRouter>,
    );
    expect(screen.getByText("surface")).toBeInTheDocument();
    expect(screen.getByRole("main")).toHaveClass("app-immersive");
    expect(screen.queryByRole("banner")).toBeNull();
    expect(
      screen.queryByRole("navigation", { name: "Primary navigation" }),
    ).toBeNull();
  });
});

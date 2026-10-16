import { fireEvent, render, screen, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AtmospherePreview } from "./AtmospherePreview";
import { SCENIC_ATMOSPHERES } from "../desk/gl/atmosphereRegistry";

const firstWorld = SCENIC_ATMOSPHERES[0];
const lastWorld = SCENIC_ATMOSPHERES[SCENIC_ATMOSPHERES.length - 1];
const collectionSize = String(SCENIC_ATMOSPHERES.length).padStart(2, "0");

const select = vi.hoisted(() => vi.fn());
vi.mock("../desk/gl/Atmosphere", () => ({
  Atmosphere: ({ id }: { id: string }) => <div data-testid="scene">{id}</div>,
}));
vi.mock("../desk/gl/atmospherePreference", () => ({
  useAtmospherePreference: () => ["radio-station", select],
}));
vi.mock("../desk/gl/atmosphereControls", () => ({
  useAtmosphereControls: () => ({
    sound: false,
    motion: true,
    setSound: vi.fn(),
    setMotion: vi.fn(),
  }),
}));

beforeEach(() => {
  history.replaceState(null, "", "/");
  select.mockClear();
});

describe("the complete night collection", () => {
  it("opens at the first scenic world and exposes the complete collection", () => {
    render(<AtmospherePreview />);
    expect(
      screen.getByRole("heading", { name: firstWorld.name }),
    ).toBeInTheDocument();
    expect(
      within(screen.getByRole("navigation"))
        .getAllByRole("button")
        .map((button) => button.getAttribute("data-scene")),
    ).toEqual(SCENIC_ATMOSPHERES.map(({ id }) => id));
    expect(
      within(screen.getByRole("navigation")).getByRole("button", {
        name: /In Jupiter's orbit/,
      }),
    ).toHaveAttribute("data-scene", "jupiter-orbit");
    expect(screen.getByText(`01 / ${collectionSize}`)).toBeInTheDocument();
  });
  it("wraps from the first scenic world to the last and back", () => {
    render(<AtmospherePreview />);
    fireEvent.click(
      screen.getByRole("button", { name: "Previous environment" }),
    );
    expect(
      screen.getByRole("heading", { name: lastWorld.name }),
    ).toBeInTheDocument();
    expect(screen.getByTestId("scene")).toHaveTextContent(lastWorld.id);
    expect(screen.getByText(`${collectionSize} / ${collectionSize}`)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next environment" }));
    expect(screen.getByTestId("scene")).toHaveTextContent(firstWorld.id);
    expect(screen.getByText(`01 / ${collectionSize}`)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Next environment" }));
    expect(
      screen.getByRole("heading", { name: SCENIC_ATMOSPHERES[1].name }),
    ).toBeInTheDocument();
    expect(select).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Use on my Floor" }));
    expect(select).toHaveBeenCalledWith(SCENIC_ATMOSPHERES[1].id);
  });
  it.each(SCENIC_ATMOSPHERES.map(({ id }) => id))(
    "honors a direct link to %s",
    (id) => {
      history.replaceState(null, "", `/#${id}`);
      render(<AtmospherePreview />);
      expect(screen.getByTestId("scene")).toHaveTextContent(id);
      expect(
        within(screen.getByRole("navigation")).getByRole("button", {
          pressed: true,
        }),
      ).toHaveAttribute("data-scene", id);
    },
  );
  it.each(["quiet-desk", "missing"])(
    "falls back to the first scenic world for #%s",
    (id) => {
      history.replaceState(null, "", `/#${id}`);
      render(<AtmospherePreview />);
      expect(screen.getByText(`01 / ${collectionSize}`)).toBeInTheDocument();
      expect(screen.getByTestId("scene")).toHaveTextContent(firstWorld.id);
    },
  );
});

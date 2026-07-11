import { describe, expect, it } from "vitest";
import { PRODUCT_ROUTES } from "./routes";

describe("product route inventory", () => {
  it("names every Phase-91 canonical route in one browser router", () => {
    const paths = PRODUCT_ROUTES.map((route) => route.path);
    expect(paths).toEqual(
      expect.arrayContaining([
        "/",
        "/welcome",
        "/setup",
        "/dictation",
        "/live",
        "/history",
        "/meetings",
        "/settings",
        "/activity",
        "/commands",
        "/cadence",
        "/studio",
        "/workbench",
        "/profiles",
        "/companion",
        "/presence",
        "/docs/dictation-runtime",
        "/design/components",
      ]),
    );
    expect(new Set(paths).size).toBe(paths.length);
  });

  it("lazy-loads each route component", () => {
    for (const route of PRODUCT_ROUTES) {
      expect(
        (route.component as unknown as { $$typeof: symbol }).$$typeof,
      ).toBe(Symbol.for("react.lazy"));
    }
  });
});

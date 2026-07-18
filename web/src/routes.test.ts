// HS-95-08 — the routing truth: three real routes render surfaces; every
// former product path is a demoted deep link into the desk.
import { describe, expect, it } from "vitest";
import { DEMOTED_ROUTES, PRODUCT_ROUTES } from "./routes";

describe("the Desk OS route inventory", () => {
  it("renders exactly three surfaces", () => {
    expect(PRODUCT_ROUTES.map((route) => route.path)).toEqual([
      "/",
      "/welcome",
      "/presence",
    ]);
    for (const route of PRODUCT_ROUTES) expect(route.immersive).toBe(true);
  });

  it("demotes every legacy product path to a desk deep link", () => {
    const paths = DEMOTED_ROUTES.map((route) => route.path);
    expect(paths).toEqual(
      expect.arrayContaining([
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
        "/docs/dictation-runtime",
        "/design/components",
      ]),
    );
    expect(new Set(paths).size).toBe(paths.length);
    for (const route of DEMOTED_ROUTES) expect(route.surface).toBeTruthy();
  });

  it("lazy-loads each rendered surface", () => {
    for (const route of PRODUCT_ROUTES) {
      expect(
        (route.component as unknown as { $$typeof: symbol }).$$typeof,
      ).toBe(Symbol.for("react.lazy"));
    }
  });
});

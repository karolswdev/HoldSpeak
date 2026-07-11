import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  CONTROL_MODES,
  DECISION_KINDS,
  DESTINATION_CLASSES,
  LEGACY_PRODUCT_ALIASES,
  LIFECYCLE_AXES,
  MEETING_PROJECTIONS,
  PRODUCT_LANGUAGE_VERSION,
  PRODUCT_TERMS,
  canonicalProductTerm,
  productLabel,
  requireCanonicalValue,
} from "./productLanguage";

const registry = JSON.parse(
  readFileSync(resolve(process.cwd(), "../docs/product-language.json"), "utf8"),
);

describe("product language contract", () => {
  it("matches the versioned registry exactly", () => {
    expect(PRODUCT_LANGUAGE_VERSION).toBe(registry.registry_version);
    expect(
      Object.fromEntries(
        Object.entries(PRODUCT_TERMS).map(([id, labels]) => [
          id,
          {
            singular: labels[0],
            plural: labels[1],
          },
        ]),
      ),
    ).toEqual(
      Object.fromEntries(
        Object.entries(registry.terms).map(([id, term]: [string, any]) => [
          id,
          {
            singular: term.singular,
            plural: term.plural,
          },
        ]),
      ),
    );
    expect(LEGACY_PRODUCT_ALIASES).toEqual(registry.legacy_aliases);
    expect(DESTINATION_CLASSES).toEqual(registry.destination_classes);
    expect(DECISION_KINDS).toEqual(registry.decision_kinds);
    expect(CONTROL_MODES).toEqual(registry.control_modes);
    expect(LIFECYCLE_AXES).toEqual(registry.lifecycle_axes);
    expect(MEETING_PROJECTIONS).toEqual(registry.meeting_projections);
  });

  it("adapts legacy wires without exposing their label", () => {
    expect(canonicalProductTerm("recipe")).toBe("persona");
    expect(productLabel("recipe")).toBe("Persona");
    expect(productLabel("directory", true)).toBe("Zones");
    expect(productLabel("profile")).toBe("Runs on");
  });

  it("rejects unknown values rather than inventing a generic label", () => {
    expect(() => canonicalProductTerm("thing")).toThrow(
      /Unknown HoldSpeak product term/,
    );
    expect(() =>
      requireCanonicalValue(
        "somewhere",
        DESTINATION_CLASSES,
        "destination class",
      ),
    ).toThrow(/Unknown HoldSpeak destination class/);
  });
});

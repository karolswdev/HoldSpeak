import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import {
  CONTROL_MODES,
  CONTROL_MODE_DESCRIPTIONS,
  CONTROL_MODE_LABELS,
  DECISION_KINDS,
  DESTINATION_CLASSES,
  DESTINATION_CLASS_LABELS,
  LEGACY_PRODUCT_ALIASES,
  LIFECYCLE_AXES,
  LIFECYCLE_LABELS,
  MEETING_PROJECTIONS,
  PRODUCT_LANGUAGE_VERSION,
  PRODUCT_TERMS,
  canonicalProductTerm,
  controlModeDescription,
  controlModeLabel,
  controlModeWire,
  destinationClassLabel,
  lifecycleLabel,
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
    expect(CONTROL_MODE_LABELS).toEqual(registry.control_mode_labels);
    expect(CONTROL_MODE_DESCRIPTIONS).toEqual(
      registry.control_mode_descriptions,
    );
    expect(DESTINATION_CLASS_LABELS).toEqual(
      registry.destination_class_labels,
    );
    expect(LIFECYCLE_AXES).toEqual(registry.lifecycle_axes);
    expect(LIFECYCLE_LABELS).toEqual(registry.lifecycle_labels);
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

  it("renders product labels while preserving versioned wires", () => {
    expect(controlModeWire("Secure")).toBe("safe");
    expect(controlModeWire("Normal")).toBe("neutral");
    expect(controlModeLabel("neutral")).toBe("Normal");
    expect(controlModeDescription("yolo")).toMatch(/without HoldSpeak approval/);
    expect(destinationClassLabel("paired_device")).toBe("Paired device");
    expect(lifecycleLabel("authority", "proposed")).toBe("Needs approval");
    expect(() => controlModeWire("reckless")).toThrow(/control mode/);
  });
});

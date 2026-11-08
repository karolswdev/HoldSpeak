/* HS-202-04 — the saved Sequence uses the canonical name (F08).
 *
 * `surface-inventory-2026-09-20/02-coherence-astra.md:120`: "The saved
 * Sequence object's own edit verb calls it a chain." The kind registry
 * already draws the canonical name (`lib/primitives.ts:531` is
 * `productLabel("sequence")`), and the registry records `chain` as a
 * LEGACY ALIAS (`docs/product-language.json` legacy_aliases), so the
 * window titled Sequence offered a verb for a thing with another name.
 * The surface repair parks unsupported Edit until a Sequence editor exists;
 * the supported Dictate verb keeps this object as its source. Assignment
 * model fallback chains remain outside this fence.
 */
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Chain } from "../../../lib/primitives";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import { openSurfaceOr } from "../../shell";
import type { WorldObject } from "../../world";
import { ChainPullout } from "../ChainPullout";

vi.mock("../../shell", async (original) => ({
  ...(await original<typeof import("../../shell")>()),
  openSurfaceOr: vi.fn(),
}));

vi.mock("../../../runtime/RuntimeBus", () => ({
  useRuntimeBus: () => ({
    state: "connected",
    lastFrame: null,
    subscribe: () => () => undefined,
  }),
}));

const emptySequence: Chain = {
  kind: "chain",
  id: "c1",
  name: "Release readiness",
  steps: [],
};

function world(): WorldObject {
  return {
    kind: "chain",
    id: "c1",
    title: "Release readiness",
    ref: emptySequence,
  } as unknown as WorldObject;
}

describe("the Sequence pullout names its own object (F08)", () => {
  it("withholds unsupported Edit and keeps Dictate about this", () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, chain: [emptySequence] } });
    render(<ChainPullout object={world()} onClose={() => undefined} />);
    expect(screen.getByText(/^No steps yet/)).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Edit Sequence|Edit chain/ })).toBeNull();
    const dictate = screen.getByRole("button", { name: "Dictate about this" });
    expect(dictate.classList.contains("btn")).toBe(true);
    fireEvent.click(dictate);
    expect(openSurfaceOr).toHaveBeenCalledWith("dictate", "/dictation", "sequence:c1");
  });
});

/* HS-202-04 — the saved Sequence's own verb says Sequence (F08).
 *
 * `surface-inventory-2026-09-20/02-coherence-astra.md:120`: "The saved
 * Sequence object's own edit verb calls it a chain." The kind registry
 * already draws the canonical name (`lib/primitives.ts:531` is
 * `productLabel("sequence")`), and the registry records `chain` as a
 * LEGACY ALIAS (`docs/product-language.json` legacy_aliases), so the
 * window titled Sequence offered a verb for a thing with another name.
 * Assignment model fallback chains are a different concept and are out of
 * this fence (Astra's noun map, same file).
 */
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Chain } from "../../../lib/primitives";
import { EMPTY_ITEMS } from "../../api";
import { useDesk } from "../../store";
import type { WorldObject } from "../../world";
import { ChainPullout } from "../ChainPullout";

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
  it("offers Edit Sequence, never Edit chain", () => {
    useDesk.setState({ items: { ...EMPTY_ITEMS, chain: [emptySequence] } });
    render(<ChainPullout object={world()} onClose={() => undefined} />);
    expect(
      screen.getByRole("button", { name: "Edit Sequence" }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Edit chain")).toBeNull();
  });
});

/* Conductor R1: a held tool call of a launched agent is a Needs you row
 * (`gate:<proposal_id>`, holdspeak/services/needs_you_membership.py
 * gate_items). Its Open opens the system shade, where the held call is
 * listed; a bare `gate:` opens nothing. */
import { describe, expect, it, vi } from "vitest";
import { OPEN_SYSTEM_SHADE_EVENT, openRef, refOpener } from "../openObject";

describe("gate refs", () => {
  it("open the system shade", () => {
    const heard = vi.fn();
    window.addEventListener(OPEN_SYSTEM_SHADE_EVENT, heard);
    const open = refOpener("gate:toolu_01abc");
    expect(open).not.toBeNull();
    open?.();
    expect(heard).toHaveBeenCalledTimes(1);
    openRef("gate:toolu_01abc");
    expect(heard).toHaveBeenCalledTimes(2);
    window.removeEventListener(OPEN_SYSTEM_SHADE_EVENT, heard);
  });

  it("need a proposal id", () => {
    expect(refOpener("gate:")).toBeNull();
  });
});

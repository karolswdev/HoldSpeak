/* Conductor R1: a held tool call of a launched agent is a Needs you row
 * (`gate:<proposal_id>`, holdspeak/services/needs_you_membership.py
 * gate_items). Its Open opens the Needs you window, where the held call is
 * listed with Approve and Deny (the system shade it opened before is parked:
 * no Desk mounted it). A bare `gate:` opens nothing. */
import { describe, expect, it, vi } from "vitest";
import { closeChairWindow, isChairWindowOpen } from "../chair/chairWindows";
import { openRef, refOpener } from "../openObject";

describe("gate refs", () => {
  it("open the Needs you window", async () => {
    closeChairWindow("chair:needs");
    expect(isChairWindowOpen("chair:needs")).toBe(false);
    const open = refOpener("gate:toolu_01abc");
    expect(open).not.toBeNull();
    open?.();
    await vi.waitFor(() => expect(isChairWindowOpen("chair:needs")).toBe(true));
    closeChairWindow("chair:needs");
    openRef("gate:toolu_01abc");
    await vi.waitFor(() => expect(isChairWindowOpen("chair:needs")).toBe(true));
  });

  it("need a proposal id", () => {
    expect(refOpener("gate:")).toBeNull();
  });
});

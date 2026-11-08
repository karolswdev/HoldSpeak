/* HS-202-02 job 2 — the badges on the meeting path state what was read.
 *
 * 03-interaction-walk.md Appendix B.2, two of the four false-badge sites:
 *
 *  - `LiveCore.tsx:450` — `label={"⌂ " + egressLabel}`: the home glyph is
 *    hardcoded in front of whatever host comes back, and no `scope` is
 *    passed, so a cloud host renders in the local tone. Worse, the value it
 *    reads (`intel_egress.label`) is not a key the hub publishes
 *    (`holdspeak/runtime/activity.py:209-234` publishes `enabled`,
 *    `provider`, `can_transmit_offmachine`, `egress`), so the chip fell to
 *    its "This device" default on every desk.
 *  - `DictationCore.tsx:154` — a hardcoded `<EgressChip label="THIS DEVICE" />`
 *    in the footer of a face whose own engine row can read a LAN IP or CLOUD.
 */
import { describe, expect, it } from "vitest";
import DictationCoreSource from "../DictationCore.tsx?raw";

describe("the dictation footer no longer hardcodes a placement", () => {
  it("has no `THIS DEVICE` literal", () => {
    expect(DictationCoreSource).not.toMatch(/EgressChip label="THIS DEVICE"/);
  });
});

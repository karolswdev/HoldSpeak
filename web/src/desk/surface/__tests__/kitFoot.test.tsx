// Phase 16 — the interior kit: Foot (SurfaceFooter restyled: the Steel foot,
// inset top lines, the egress chip a paper plate, the verbs right; egress
// exactly where egress happens, UX-CANON A.9).
import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { EgressChip, SurfaceFooter } from "..";
import { Button } from "../../../components/signal/Signal";

describe("Foot (Phase 16 kit)", () => {
  it("egress, receipt, verbs in that order", () => {
    const { container } = render(
      <SurfaceFooter
        egress={<EgressChip label="api.anthropic.com" scope="cloud" />}
        receipt={<span>5 OBJECTS</span>}
        verbs={<><Button dense variant="ghost">Get Info</Button><Button dense variant="primary">Answer</Button></>}
      />,
    );
    const layout = container.querySelector(".surface-footer-layout") as HTMLElement;
    expect([...layout.children].map((c) => c.className)).toEqual([
      "surface-footer-egress", "surface-footer-receipt", "surface-footer-verbs",
    ]);
    expect(layout.querySelector(".surface-footer-egress .gadget-chip-egress")?.textContent).toContain("api.anthropic.com");
  });

  it("the foot is Steel with the inset ink line and shine; the egress chip a paper plate", () => {
    const css = readFileSync(resolve(__dirname, "../surface-footer.css"), "utf8");
    expect(css).toMatch(/\.desk-next \.surface-footer \{[^}]*background: var\(--wb-steel\);[^}]*box-shadow: inset 0 1px 0 var\(--wb-ink\), inset 0 2px 0 var\(--wb-hi\);/);
    expect(css).toMatch(/\.desk-next \.surface-footer \.gadget-chip-egress \{[^}]*border: 1px solid var\(--wb-ink\);[^}]*background: var\(--wb-paper\);/);
  });
});

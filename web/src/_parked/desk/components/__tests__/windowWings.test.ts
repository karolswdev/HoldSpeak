// HS-168-05 — CSS contract guard: the wings stay inside the window head.
//
// The has-wings title must shrink (no flex: none) and carry min-width: 0
// so the ellipsis fires before pushing wings off-screen.  The wings
// container and actions wrapper must not shrink (flex-shrink: 0).

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const pulloutCss = readFileSync(
  resolve(process.cwd(), "src/desk/components/pullout.css"),
  "utf8",
);

const windowChromeCss = readFileSync(
  resolve(process.cwd(), "src/desk/components/window-chrome.css"),
  "utf8",
);

describe("HS-168-05 window wings CSS contract", () => {
  it("has-wings title carries min-width: 0 and no flex: none", () => {
    const rule = pulloutCss.match(
      /\.desk-next\s+\.desk-pullout-head\.has-wings\s+\.desk-pullout-title\s*\{([^}]+)\}/s,
    );
    expect(rule).not.toBeNull();
    const body = rule![1];
    expect(body).toMatch(/min-width:\s*0/);
    expect(body).not.toMatch(/flex:\s*none/);
  });

  it("base title carries min-width: 0", () => {
    // Match the base rule (no .has-wings qualifier)
    const rule = pulloutCss.match(
      /\.desk-next\s+\.desk-pullout-title\s*\{([^}]+)\}/s,
    );
    expect(rule).not.toBeNull();
    expect(rule![1]).toMatch(/min-width:\s*0/);
  });

  it("desk-wings has flex-shrink: 0", () => {
    const rule = pulloutCss.match(
      /\.desk-next\s+\.desk-wings\s*\{([^}]+)\}/s,
    );
    expect(rule).not.toBeNull();
    expect(rule![1]).toMatch(/flex-shrink:\s*0/);
  });

  it("desk-window-actions has flex-shrink: 0", () => {
    const rule = windowChromeCss.match(
      /\.desk-next\s+\.desk-window-actions\s*\{([^}]+)\}/s,
    );
    expect(rule).not.toBeNull();
    expect(rule![1]).toMatch(/flex-shrink:\s*0/);
  });
});
